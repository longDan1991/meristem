"""一个节点的一回合：问模型（带工具）→ 按工具调用做一个动作 / 出结论。

模型与程序之间唯一的通道是**三个工具**（schema 在 `protocol/tool_specs.py`，
实现在这里）：
  · create_children —— 分配节点再拆一层（它唯一的动作）
  · run_code        —— 叶子写一段代码（它唯一的动作）
  · conclude        —— 出结论（两个节点共用）

每次回复必须调用且只能调用其中一个；没调用 / 调错 / 调多个 = 协议违规（balk）。
参数形状由 pydantic schema 强制；**语义校验仍走 gate**（clean_spec /
clean_conclusion）—— schema 只管形状，拒绝信息保持 gate 的中文原文。

工具实现要拿到**每个节点自己的运行时上下文**（节点是并发的）：`_step_binding`
是 ContextVar，step() 开头写入 (ctx, nid)，工具函数用 `Depends(get_step_binding)`
注入 —— 每个 asyncio task 的 context 是独立的，并发节点互不串（AGENTS §9 无锁）。

代码只做四件事（都在形式字段上，不是计数器）：
  ① 规范化字段（**不切长度** —— 上限由提示词承诺，代码不再偷偷砍）
  ② 子任务的验收标准必须携带父/根的可测物理量，否则这次分配当场被拒并记进尝试
  ③ 一次最多一个门槛；门槛不成立，其余子任务不启动
  ④ 判定"满足"却指不出证据 → 降级为"未满足"
"""

import contextvars
import hashlib
import json
import os

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from ..effects import (ARTIFACT_EXT, accept_artifacts, classify_paths,
                       effects_of, snapshot_workspace)
from ..protocol.gate import anchors, clean_conclusion, clean_spec, inherits
from ..protocol.tool_specs import Artifact, ChildSpec, mcp, openai_tools
from ..prompts import PROMPT
from .. import config as cfg
from ..compression import RETRIEVE_NAME, compress_messages, retrieve_original
from . import sandbox


# ---------------------------------------------------------------- 工具接线
# 每个节点类型的工具清单（OpenAI 格式，litellm 用）。schema 是静态的，
# 由 openai_tools() 缓存；这里只记名字，供 step 校验"这次调的是不是本层该调的"。
_TOOL_NAMES = {"alloc": ("create_children", "conclude"),
               "leaf": ("run_code", "conclude", RETRIEVE_NAME)}

# step 开头写入 (ctx, nid)；工具函数用 Depends 注入它。每个 asyncio task
# 的 contextvars 是独立的，所以并发节点拿到的各是各的 ctx。
_step_binding: contextvars.ContextVar = contextvars.ContextVar(
    "step_binding", default=None)


def get_step_binding():
    return _step_binding.get()


def _current(binding):
    rctx, nid = binding
    st = rctx["state"][nid]
    return st, st["node"], rctx["trace"], rctx["budget"], rctx


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


async def ask(llm, trace, node, which, budget, ctx=None, st=None):
    """问模型。节点级的实时吐字从这里接出去：调度器把终端给的
    `on_delta` / `on_reasoning` 放进 ctx，这里按节点包一层再传给 llm.chat ——
    节点是并发的，回调不带 node.id 就分不清是谁在说话（§11 不建共享计数器，
    只是给回调做标记）。没给就不开流式：入口那一路默认开，节点级没有实时展示
    不背 SSE 的开销。

    叶子（选项 B）走**真对话**：基础 user 消息（render_wire，字节稳定）
    + 累积的 asst/tool 消息，发送前交给 headroom 路由压缩 —— 只压 role=tool
    的工具输出，user/system 一字不动。压缩统计写进 trace（wire_compressed），
    预算计的是 API 真实用量，节省自动反映。分配节点照旧单发 render。
    """
    trace.add(node.id, "%s_in" % which, node.render())
    tools = (await openai_tools())[which]
    stream_kw = {}
    if ctx:
        if ctx.get("on_delta"):
            stream_kw["on_delta"] = lambda t: ctx["on_delta"](node.id, t)
        if ctx.get("on_reasoning"):
            stream_kw["on_reasoning"] = lambda t: ctx["on_reasoning"](node.id, t)
    if which == "leaf" and st is not None:
        msgs = st.setdefault("msgs", [])
        wire = [{"role": "system", "content": PROMPT["leaf"]},
                {"role": "user", "content": node.render_wire()}] + msgs
        if cfg.COMPRESS and any(m.get("role") == "tool" for m in msgs):
            result = await compress_messages(wire, getattr(llm, "model", ""))
            wire = result.messages
            if result.tokens_saved > 0:
                trace.add(node.id, "wire_compressed", {
                    "before": result.tokens_before, "after": result.tokens_after,
                    "saved": result.tokens_saved,
                    "ratio": (round(result.tokens_saved / result.tokens_before, 3)
                               if result.tokens_before else 0.0),
                    "transforms": result.transforms_applied})
    else:
        wire = [{"role": "system", "content": PROMPT[which]},
                {"role": "user", "content": node.render()}]
    msg = await llm.chat(wire, tools=tools, **stream_kw)
    _log_usage(llm, trace, node.id, which, budget)
    trace.add(node.id, "%s_out" % which,
              {"text": msg.text,
               "tool_calls": [{"name": tc.name, "arguments": tc.arguments}
                              for tc in msg.tool_calls]})
    return msg


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

    四个地方都要走它：没调工具 / 参数不合形状 / 被代码拒的分配 / 不合规的结论。
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
    # feedback：叶子的对话要把它写回（step 会配对成 tool/user 消息），
    # 不然模型下一回合看不到自己为什么被拒。分配节点不用（单发 render 自带历史）。
    return {"kind": "again", "feedback": why + note}


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
    契约的「前置条件」靠它。
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


async def do_code(node, code, trace, st, hands):
    """跑一段代码。它是唯一能改变世界的东西，也是这一回合的观测来源。

    产出记账不再靠解析工具参数（代码模式下没有参数可解析）：候选 = 子进程自己
    报的写入 ∪ 真跑过的命令里解析出的目标，再逐个 stat 和跑之前的快照对比。
    这样**并发节点写的东西不会被算到它头上**（全局 diff 会 —— 见 `effects.classify_paths`）。
    """
    cwd = os.getcwd()
    # 自己的账本（trace）每回合都在改，不能算成模型的产出
    skip = [getattr(trace, "path", None)]
    before = snapshot_workspace(cwd, skip)
    obs, calls, wrote = await sandbox.run(
        code, hands, trace=trace, node_id=node.id, cwd=cwd)
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
        # dict 形状（不是元组）：会话状态检查点要序列化，元组不是 JSON。
        st.setdefault("art_effects", {})[os.path.realpath(p)] = {
            "effects": eff, "preconditions": pre}
        if p in created:
            made.append(os.path.basename(p))
    st.setdefault("calls", []).extend(calls)
    # 过程中只给一个中性事实，不下指令 —— 不分散注意力
    note = "\n（本次产出：%s）" % ", ".join(made) if made else ""
    return str(obs) + note


# ---------------------------------------------------------------- 三个工具
@mcp.tool
async def create_children(children: list[ChildSpec],
                          _b=Depends(get_step_binding)) -> dict:
    """把任务拆成更小的子任务交给下层节点。调它 = 再拆一层。

    除 notes / gate 外全部必填：缺了或形状不对，这次分配会被代码当场退回，
    原因写进「本层已有尝试」。一次最多一个 gate。
    """
    st, node, trace, budget, rctx = _current(_b)
    kids_spec, reject = [], None
    for raw in (c.model_dump() for c in children):
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        # ② 子任务的验收标准必须携带父/根的可测物理量
        ra = rctx["root_anchors"]
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


@mcp.tool
async def run_code(code: str, _b=Depends(get_step_binding)) -> dict:
    """写一段代码。代码是唯一能改变世界的东西，一次一段，次数不限。

    跑在一个真的 Python 进程里（当前工作目录）：bash / read / write 永远都在。
    print 和异常都是观测。
    """
    st, node, trace, budget, rctx = _current(_b)
    if not code.strip():
        return balk(node, "code 是空的：要么写一段代码，要么用 conclude 出结论",
                    trace, st)
    obs = await do_code(node, code, trace, st, rctx["hands"])
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
    # obs 随结果带回：选项 B 的 step 要把它写成 role=tool 消息（观测在对话里）。
    return {"kind": "again", "obs": obs}


@mcp.tool
async def conclude(verdict: str, text: str,
                   evidence: list[str] | None = None,
                   external: str = "",
                   artifacts: list[Artifact] | None = None,
                   _b=Depends(get_step_binding)) -> dict:
    """出结论：判定这件事做没做完。分配节点和叶子共用。

    判定「满足」必须指得出真证据（叶子：第几次观测 / 产物路径；分配节点：
    子任务 name / 产物路径），指不出来会被降级为未满足。
    叶子的每个产出文件都要在 artifacts 里交代（type=内部 只给自己用的）。
    """
    st, node, trace, budget, rctx = _current(_b)
    concl = {"verdict": verdict, "text": text, "evidence": evidence or [],
             "external": external,
             "artifacts": [a.model_dump(by_alias=True) for a in (artifacts or [])]}
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


# ---------------------------------------------------------------- 一回合
async def step(nid, ctx):
    """一个节点的一回合。不递归，只返回下一步该干什么。

    叶子（选项 B）维护一段真对话（st["msgs"]）：assistant 消息每回合先入账，
    之后工具结果 / 打回理由按 OpenAI 协议配对成 tool 消息 —— 每个 tool_call id
    都必须有一条 tool 回话，悬空的 id 会让 provider 报错。run_code 的观测就是
    tool 消息；没调工具时的打回理由没有 id 可配对，就写 user 消息
    （对话不能断在两个 assistant 之间）。分配节点照旧单发 render，不记账。
    """
    st = ctx["state"][nid]
    node = st["node"]
    llm, trace, budget = ctx["llm"], ctx["trace"], ctx["budget"]

    if budget.exhausted():
        node.close("阻塞", "预算耗尽: " + budget.why(), [])
        node.status = "failed"
        trace.add(node.id, "budget_exhausted", node.conclusion)
        return {"kind": "finished"}

    which = "leaf" if node.kind == "leaf" else "alloc"
    _step_binding.set((ctx, nid))
    msg = await ask(llm, trace, node, which, budget, ctx, st)

    # ── 选项 B：叶子对话。assistant 消息先入账（无论回什么）──
    wire = st.get("msgs") if node.kind == "leaf" else None
    if wire is not None:
        # id 用模型给的；没有（mock/个别 provider）就按对话长度回退 ——
        # 每回合都从 0 数会让同一条对话里出现重复的 call_0（provider 会拒或串）。
        ids = [tc.id or "call_%d" % (len(wire) + i)
               for i, tc in enumerate(msg.tool_calls)]
        wire.append({"role": "assistant", "content": msg.text or None,
                     "tool_calls": [
                         {"id": i, "type": "function",
                          "function": {"name": tc.name,
                                        "arguments": json.dumps(
                                            tc.arguments, ensure_ascii=False)}}
                         for i, tc in zip(ids, msg.tool_calls)] or None})

        def feedback(text, ids=ids):
            # 有 tool_call 就用 tool 回话配对；纯文本回复没有 id，写 user 消息
            if ids:
                for i in ids:
                    wire.append({"role": "tool", "tool_call_id": i,
                                 "content": text})
            else:
                wire.append({"role": "user", "content": text})
    else:
        feedback = None

    if not msg.tool_calls:
        hint = ("（你只回了一段文字，开头：%s）" % msg.text[:60]) if msg.text else ""
        why = ("这次回复没有调用任何工具%s。你必须调用一个：%s。"
               % (hint, " / ".join(_TOOL_NAMES[which])))
        if feedback:
            feedback(why)
        return balk(node, why, trace, st)
    if len(msg.tool_calls) > 1:
        why = "一次只能调用一个工具（你调了 %d 个）" % len(msg.tool_calls)
        if feedback:
            feedback(why)
        return balk(node, why, trace, st)
    tc = msg.tool_calls[0]
    if tc.name not in _TOOL_NAMES[which]:
        why = ("你调用的 %s 不在这一层的工具里（你能用：%s）"
               % (tc.name, " / ".join(_TOOL_NAMES[which])))
        if feedback:
            feedback(why)
        return balk(node, why, trace, st)

    # 取回工具：把被压过的工具输出原文写回对话（作为 tool 结果）
    if tc.name == RETRIEVE_NAME:
        if wire is not None:
            wire.append({"role": "tool", "tool_call_id": ids[0],
                         "content": retrieve_original(tc.arguments)})
        return {"kind": "again"}

    tool = await mcp.get_tool(tc.name)
    try:
        res = await tool.run(tc.arguments)
    except ToolValidationError as e:
        # schema 拒的参数（缺必填 / 类型错）：一条可见的事实，让模型改
        why = "工具参数不合形状，被退回：%s" % e
        if feedback:
            feedback(why)
        return balk(node, why, trace, st)
    d = res.structured_content
    if not isinstance(d, dict):
        raise TypeError("工具 %s 必须返回 dict（拿到 %r）" % (tc.name, d))
    if wire is not None:
        if d.get("obs") is not None:
            wire.append({"role": "tool", "tool_call_id": ids[0],
                         "content": d["obs"]})
        elif d.get("feedback"):
            wire.append({"role": "tool", "tool_call_id": ids[0],
                         "content": d["feedback"]})
    return d
