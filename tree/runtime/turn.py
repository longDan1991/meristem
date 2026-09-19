"""一个节点的一回合：问模型 → 过闸门 → 做一个动作 / 再拆一层。

这一层因**"回合怎么走"**而变：提示词里模型能说什么、代码要核什么、
动作怎么记账、原地打转怎么显式化。调度（谁先谁后、门槛、并行）在 scheduler。

代码只做四件事（都在形式字段上，不是计数器）：
  ① 规范化字段（**不切长度** —— 上限由提示词承诺，代码不再偷偷砍）
  ② 子任务的验收标准必须携带父/根的可测物理量，否则这次分配当场被拒并记进尝试
  ③ 一次最多一个门槛；门槛不成立，其余子任务不启动
  ④ 判定"满足"却指不出证据 → 降级为"未满足"
"""

import hashlib
import os

from ..effects import (ARTIFACT_EXT, accept_artifacts, classify_paths,
                       effects_of, snapshot_workspace)
from ..llm import parse_json
from ..prompts import PROMPT
from ..protocol.gate import anchors, clean_conclusion, clean_spec, inherits
from . import sandbox


# ---------------------------------------------------------------- 问模型
def _log_usage(llm, trace, node_id, phase, budget):
    u = getattr(llm, "last_usage", None)
    if not u:
        return
    total = u.get("total_tokens", 0)
    trace.add(node_id, "usage", {
        "phase": phase, "prompt": u.get("prompt_tokens", 0),
        "completion": u.get("completion_tokens", 0),
        "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        "cached": (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
        "total": total})
    budget.add_tokens(total)


async def ask(llm, trace, node, which, budget):
    trace.add(node.id, "%s_in" % which, node.render())
    text = await llm.chat([{"role": "system", "content": PROMPT[which]},
                           {"role": "user", "content": node.render()}])
    _log_usage(llm, trace, node.id, which, budget)
    trace.add(node.id, "%s_out" % which, text)
    try:
        d = parse_json(text)
    except ValueError as e:
        return {"_bad": "输出不是合法 JSON：%s" % e}
    if not isinstance(d, dict):
        return {"_bad": "输出必须是一个 JSON 对象"}
    return d


# ---------------------------------------------------------------- 原地打转
def sig(what, obs=""):
    """这次做了什么 + 世界回了什么的指纹。用于检测"重复同一件事、没有新信息"。

    这不是轮次上限：只要观测变了（比如轮询一个正在启动的服务），指纹
    就不同，永远不会触发。它检测的是**没有新信息**，不是"做得太多"。
    观测**整段参与哈希**：截掉尾巴会让"只在 400 字之后不一样"的两次观测
    看起来一样，于是真的进展被当成原地打转。哈希再长的字符串也不贵。
    """
    return hashlib.sha1((str(what) + "\x00" + str(obs)).encode()).hexdigest()


def bump(seen, fingerprint, trace, node, what):
    """同一份东西重复出现 ≥3 次就显式告警，≥5 次就自己停下。

    不是轮次上限：换一个动作、或者世界回话变了，指纹就不同（§2.4）。
    它检测的是**没有新信息**。这里既用于"重复同一个动作"，也用于
    "重复同一份看不懂的输出" —— 后者根本没有动作，所以更隐蔽
    （实测撞过一次：mock 还在说旧协议的键，同一回合无限重复）。
    """
    seen[fingerprint] = seen.get(fingerprint, 0) + 1
    n = seen[fingerprint]
    if n < 3:
        return n, ""
    trace.add(node.id, "no_progress", {"times": n, "action": what})
    return n, ("\n[停止] 已经有 %d 次是同样的东西了：%s —— 再重复不会带来新信息。\n"
               "换一个动作，或者出结论（阻塞就写清为什么）。" % (n, what))


def balk(node, why, trace, st, kids=None):
    """把"这次给的东西用不了"变成一条可见的事实，并且**按重复次数处理**。

    四个地方都要走它：看不懂的输出、被代码拒的分配、不合规的结论。
    没有它，模型一直给同样的东西，这一回合就原地无限重复 ——
    实测撞过两次（旧协议的键；总缺 accept 的子任务）。那两种情况下
    根本没有动作，所以"重复动作"那个信号永远不会触发：这里必须自己数。

    这不是轮次上限：换一种拆法、换一个错，指纹就不同（§2.4）。
    """
    if node.kind == "leaf":
        node.observations.append({"action": "(用不了)", "obs": why})
    else:
        node.attempts.append({"children": kids or [], "rejected": why})
    n, note = bump(st.setdefault("seen_actions", {}),
                   sig("(balk)", why), trace, node, "(用不了的输出)")
    if n >= 5:
        node.close("未满足", "同一份用不了的东西连续 %d 次，没有新信息：%s"
                   % (n, why), [])
        return {"kind": "finished"}
    if note:
        if node.kind == "leaf":
            node.observations[-1]["obs"] += note
        else:
            node.attempts[-1]["rejected"] += note
    return {"kind": "again"}


# ---------------------------------------------------------------- 动手
def code_label(code):
    """观测历史里给这一段代码的标题：第一行，够短。
    完整代码进 trace（那里不占模型的上下文）。"""
    for ln in str(code).splitlines():
        if ln.strip():
            s = ln.strip()
            return s if len(s) <= 200 else s[:200] + "…"
    return "(空代码)"


def _merged_effects(calls):
    """把这一段代码里**真跑过的每一条命令**的 effects 合起来。

    这里来的是文件清单看不见的那一半：装了什么包、连了哪个网、起了常驻进程 ——
    能力库的「前置条件」靠它，而复用失败最常见的原因就是前提不成立。
    create/modify 先按命令里写的收下来，真正的认定（是否真发生）由
    `effects.classify_paths` 对比快照做。"""
    eff = {"fs": {"create": [], "modify": [], "delete": []},
           "pkg": [], "proc": [], "net": [], "data": [], "cwd": os.getcwd()}
    pre = {}
    for tool, args, _ in calls:
        e, p = effects_of(tool, args, cwd=os.getcwd())
        for k in ("pkg", "proc", "net", "data"):
            for x in e[k]:
                if x not in eff[k]:
                    eff[k].append(x)
        for k in ("create", "modify", "delete"):
            for x in e["fs"][k]:
                if x not in eff["fs"][k]:
                    eff["fs"][k].append(x)
        pre.update(p)
    return eff, pre


async def do_code(node, code, trace, box, st, hands):
    """跑一段代码。它是唯一能改变世界的东西，也是这一回合的观测来源。

    产出记账不再靠解析工具参数（代码模式下没有参数可解析）：候选 = 子进程自己
    报的写入 ∪ 真跑过的命令里解析出的目标，再逐个 stat 和跑之前的快照对比。
    这样**并发节点写的东西不会被算到它头上**（全局 diff 会 —— 见 `effects.classify_paths`）。
    这一段代码真发生过的调用（走协议回调宿主的那几次）同时是能力库的原料。
    """
    cwd = os.getcwd()
    # 自己的账本（trace / caps）每回合都在改，不能算成模型的产出
    skip = [getattr(trace, "path", None)]
    if getattr(box, "caps", None) is not None:
        skip.append(getattr(box.caps, "path", None))
    before = snapshot_workspace(cwd, skip)
    obs, calls, wrote = await sandbox.run(
        code, st.get("tools") or [], box, hands, trace=trace,
        node_id=node.id, cwd=cwd)
    eff, pre = _merged_effects(calls)
    candidates = list(wrote)
    for p in eff["fs"]["create"] + eff["fs"]["modify"]:
        candidates.append(p)
    created, modified = classify_paths(candidates, before, cwd)
    eff["fs"] = {"create": created, "modify": modified, "delete": []}
    trace.add(node.id, "effects", {"calls": [c[0] for c in calls],
                                    "wrote": wrote, "effects": eff,
                                    "前置条件": pre})
    # 要交代的是**该给契约的那几类**（和以前同一个词表）；数据/日志不用管。
    made = []
    for p in created + modified:
        if not str(p).lower().endswith(ARTIFACT_EXT):
            continue
        st.setdefault("artifacts", set()).add(os.path.realpath(p))
        st.setdefault("art_effects", {})[os.path.realpath(p)] = (eff, pre)
        if p in created:
            made.append(os.path.basename(p))
    st.setdefault("calls", []).extend(calls)
    # 过程中只给一个中性事实，不下指令 —— 不分散注意力
    note = "\n（本次产出：%s）" % ", ".join(made) if made else ""
    return str(obs) + note


# ---------------------------------------------------------------- 一回合
async def step(nid, ctx):
    """一个节点的一回合。不递归，只返回下一步该干什么。"""
    st = ctx["state"][nid]
    node = st["node"]
    llm, trace, budget = ctx["llm"], ctx["trace"], ctx["budget"]
    hands = ctx["hands"]

    if budget.exhausted():
        node.close("阻塞", "预算耗尽: " + budget.why(), [])
        node.status = "failed"
        trace.add(node.id, "budget_exhausted", node.conclusion)
        return {"kind": "finished"}

    which = "leaf" if node.kind == "leaf" else "alloc"
    d = await ask(llm, trace, node, which, budget)

    if d.get("_bad"):
        # 把非法输出当成一条事实喂回去，让它自己纠正（不加计数器）
        trace.add(node.id, "bad_output", d["_bad"])
        return balk(node, d["_bad"], trace, st)

    concl = d.get("conclusion")
    if isinstance(concl, dict):
        got, err = clean_conclusion(concl, trace, node, st)
        if err:
            trace.add(node.id, "bad_conclusion", err)
            return balk(node, err, trace, st)
        accept_artifacts(node, got["artifacts"], trace, st)
        node.close(got["verdict"], got["content"], got["evidence"], got["external"])
        trace.add(node.id, "concluded",
                  {"verdict": got["verdict"], "text": got["content"],
                   "evidence": got["evidence"], "external": got["external"]})
        return {"kind": "finished"}

    if node.kind == "leaf":
        code = d.get("code")
        if not isinstance(code, str) or not code.strip():
            return balk(
                node,
                "输出里没有能识别的顶层键（你只能给 code 或 conclusion）。"
                "你给的键是: %s" % (", ".join(sorted(d)) or "(空)"),
                trace, st)
        obs = await do_code(node, code, trace, ctx["box"], st, hands)
        label = code_label(code)
        # 每一回合的代码只在这一处计数：跑成没成、报不报错，都得过这里，
        # 所以"同一段代码 + 同一结果 ≥3 告警 / ≥5 停下"没有漏网的路。
        n, note = bump(st.setdefault("seen_actions", {}),
                       sig(code, obs), trace, node, label)
        if n >= 5:
            st["stalled"] = ("同一段代码重复 %d 次、输出完全一样，没有新信息" % n)
        if note:
            obs = str(obs) + note
        node.observations.append({"action": label, "obs": obs})
        trace.add(node.id, "code", {"code": code, "obs": obs})
        stalled = st.pop("stalled", None)
        if stalled:
            trace.add(node.id, "stalled", stalled)
            node.close("未满足", stalled, [])
            return {"kind": "finished"}
        return {"kind": "again"}

    # ── 分配节点：再拆一层 ──
    specs = d.get("children")
    if not isinstance(specs, list) or not specs:
        return balk(
            node,
            "输出里没有能识别的顶层键（你只能给 children 或 conclusion）。"
            "你给的键是: %s" % (", ".join(sorted(d)) or "(空)"),
            trace, st)

    kids_spec, reject = [], None
    for raw in specs:                         # 不砍：拆几个是模型的决定
        s, why = clean_spec(raw if isinstance(raw, dict) else {})
        if why:
            reject = why
            break
        # ② 子任务的验收标准必须携带父/根的可测物理量
        ra = ctx["root_anchors"]
        ok_parent = inherits(node.accept, s["accept"])
        ok_root = (not ra) or any(x in s["accept"] for x in ra)
        if not (ok_parent and ok_root):
            reject = ("子任务的 accept 丢了可测物理量（缺 %s）—— 这是把任务换成了别的东西"
                      % ", ".join(sorted(ra or anchors(node.accept))))
            trace.add(node.id, "criterion_drift",
                      {"child": s["name"], "accept": s["accept"],
                       "parent_anchors": sorted(anchors(node.accept)),
                       "root_anchors": sorted(ra)})
            break
        kids_spec.append(s)

    if reject:
        # 把被拒这件事变成一条可见的事实（而不是丢弃或加计数器）
        return balk(node, reject, trace, st, kids=kids_spec)

    gates = [s for s in kids_spec if s["gate"]]
    if len(gates) > 1:
        return balk(node, "一次分配最多一个门槛", trace, st, kids=kids_spec)
    gate = gates[0] if gates else None
    if gate:
        first = [gate]
        rest = [s for s in kids_spec if s is not gate]
    else:
        first, rest = kids_spec, []          # 没有门槛就没有"暂缓"，不能把全部当成暂缓

    if not budget.take_nodes(len(kids_spec)):
        return balk(node, "节点预算不足", trace, st, kids=kids_spec)
    node.attempts.append({"children": kids_spec, "results": [], "outcome": "等下层"})
    trace.add(node.id, "allocated",
              {"round": len(node.attempts), "gate": gate["name"] if gate else None,
               "deferred": [s["name"] for s in rest] if gate else []})
    return {"kind": "children", "first": first, "rest": rest,
            "gate_name": gate["name"] if gate else None}
