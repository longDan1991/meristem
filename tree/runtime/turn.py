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
import json
import os

from ..effects import ARTIFACT_EXT, accept_artifacts, effects_of
from ..llm import parse_json
from ..prompts import PROMPT
from ..protocol.gate import anchors, clean_conclusion, clean_spec, inherits
from ..tools import TOOLS


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


def ask(llm, trace, node, which, budget):
    trace.add(node.id, "%s_in" % which, node.render())
    text = llm.chat([{"role": "system", "content": PROMPT[which]},
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
def sig(tool, args, obs):
    """动作 + 观测的指纹。用于检测"重复同一件事、没有新信息"。

    这不是轮次上限：只要观测变了（比如轮询一个正在启动的服务），
    指纹就不同，永远不会触发。它检测的是**没有新信息**，不是"做得太多"。

    观测**整段参与哈希**：截掉尾巴会让"只在 400 字之后不一样"的两次观测
    看起来一样，于是真的进展被当成原地打转。哈希再长的字符串也不贵。
    """
    a = json.dumps({"tool": tool, "args": args}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1((a + "\x00" + str(obs)).encode()).hexdigest()


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
                   sig("(balk)", why, ""), trace, node, "(用不了的输出)")
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


# ---------------------------------------------------------------- 动作
def do_action(node, act, trace, caps, st, hands):
    """执行一个形式化动作。返回观测文本。动作是唯一能改变世界的东西。"""
    tool = str(act.get("tool", ""))
    args = act.get("args") or {}
    if not isinstance(args, dict):
        return "参数必须是一个 JSON 对象"
    if tool not in TOOLS:
        return ("没有这个工具：%s（只有 bash / read / write）\n"
                "现成做法已经在上面的「现成做法」里了，直接用 bash 跑。" % tool)
    # offset/limit 必须传下去 —— read 的返回里就写着
    # "read(offset=2000) 取下一段"，不传的话模型照做了也拿不到下一段，
    # 它就只能反复重读（这正是当年读了 25 次的那个坑）。
    call_args = {k: args[k] for k in ("path", "content", "cmd", "timeout",
                                      "offset", "limit") if k in args}
    # write 必须在动作**之前**记下文件存不存在，否则 create 永远被记成 modify
    existed = None
    if tool == "write":
        existed = os.path.exists(str(args.get("path")))
    # 工具层把环境错误变成观测（世界说"不行"），编程错误照旧往上炸（§2）。
    # 观测不能提前 return —— 提前 return 会让它绕过调用方的重复计数，
    # 于是同一个报错无限重试。
    obs = hands.run(tool, call_args)

    # 动作之后统一记账：effects 由代码抽，不给模型自报的机会。
    # bash 和 write 共用这一套 —— 它们本来就是同一件事的两个壳。
    eff, pre = effects_of(tool, args, cwd=os.getcwd(), existed_before=existed)
    # effects / 前置条件 是 effects.py 自己的词表（能力库、sidecar 也用它），
    # 跟形式字段不是一套；这里只把协议那个键写成英文。
    trace.add(node.id, "effects", {"tool": tool, "effects": eff, "前置条件": pre})
    # 产出物由代码记账（模型只管干活）。effects 留着，结论时给契约用。
    made = []
    for p in eff["fs"]["create"] + eff["fs"]["modify"]:
        if str(p).lower().endswith(ARTIFACT_EXT):
            rp = os.path.realpath(p)
            st.setdefault("artifacts", set()).add(rp)
            st.setdefault("art_effects", {})[rp] = (eff, pre)
            if p in eff["fs"]["create"]:
                made.append(os.path.basename(p))
    # 过程中只给一个中性事实，不下指令 —— 不分散注意力
    note = "\n（本次产出：%s）" % ", ".join(made) if made else ""

    # 复用反馈：刚检索出来的做法，用它成没成
    if caps is not None and tool == "bash" and st.get("_caps"):
        cmd = str(args.get("cmd", ""))
        for e in list(st["_caps"]):
            c = (e.get("how") or {}).get("cmd") or ""
            if c and (c in cmd or cmd in c):
                ok = ("工具出错" not in str(obs)
                      and ("[exit=" not in str(obs) or "[exit=0]" in str(obs)))
                caps.note_outcome(e["id"], ok)
                trace.add(node.id, "cap_outcome", {"cap": e["id"], "ok": ok})
                break
        st["_caps"] = []
    # 无进展检测：同一动作 + 同一结果重复多次 = 再重复不会带来新信息。
    # 实测：一个叶子把同一个文件读了 25 次，光摆着历史它停不下来。
    # 所以把"重复"这个事实显式化（内容信号，不是轮次预算）。
    # 计数**不在这里做** —— 这里有好几个 return，漏掉一个就是死循环。
    # 收口在 step：每一回合的动作都在那里计数，一条路也漏不了。
    return str(obs) + note


# ---------------------------------------------------------------- 一回合
def step(nid, ctx):
    """一个节点的一回合。不递归，只返回下一步该干什么。"""
    st = ctx["state"][nid]
    node = st["node"]
    llm, trace, budget = ctx["llm"], ctx["trace"], ctx["budget"]
    caps, hands = ctx["caps"], ctx["hands"]

    if budget.exhausted():
        node.close("阻塞", "预算耗尽: " + budget.why(), [])
        node.status = "failed"
        trace.add(node.id, "budget_exhausted", node.conclusion)
        return {"kind": "finished"}

    which = "leaf" if node.kind == "leaf" else "alloc"
    d = ask(llm, trace, node, which, budget)

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
        act = d.get("action")
        if not isinstance(act, dict):
            return balk(
                node,
                "输出里没有能识别的顶层键（你只能给 action 或 conclusion）。"
                "你给的键是: %s" % (", ".join(sorted(d)) or "(空)"),
                trace, st)
        obs = do_action(node, act, trace, caps, st, hands)
        label = "%s %s" % (act.get("tool", ""),
                           json.dumps(act.get("args") or {}, ensure_ascii=False))
        # 每一回合的动作只在这一处计数：动作成没成、工具报不报错，都得过这里，
        # 所以"同一动作 + 同一结果 ≥3 告警 / ≥5 停下"没有漏网的路。
        n, note = bump(st.setdefault("seen_actions", {}),
                       sig(act.get("tool"), act.get("args") or {}, obs),
                       trace, node, str(act.get("tool")))
        if n >= 5:
            st["stalled"] = ("同一动作重复 %d 次、结果完全一样，没有新信息" % n)
        if note:
            obs = str(obs) + note
        node.observations.append({"action": label, "obs": obs})
        st["calls"].append((act.get("tool"), act.get("args") or {}, obs))
        # 存结构化参数：挖掘器要能直接读，不该去反解一个拼出来的字符串
        trace.add(node.id, "action", {"tool": act.get("tool"),
                                      "args": act.get("args") or {},
                                      "obs": obs})
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
            reject = ("子任务的验收标准丢了可测物理量（缺 %s）—— 这是把任务换成了别的东西"
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
