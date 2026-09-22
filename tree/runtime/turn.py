"""一个节点的一回合：问模型（带工具）→ 按工具调用做一个动作 / 出结论。

模型与程序之间唯一的通道是**每个节点类型的工具**（schema 在
`protocol/tool_specs.py`，实现在这里）：
  · alloc    create_children（再拆一层）/ conclude
  · leaf     bash / read / write（叶子的三只手）/ conclude
  · intake   submit_root（实现在 intake.py）

每次回复必须调用且只能调用其中一个；没调用 / 调错 / 调多个 = 协议违规（balk）。
参数形状由 pydantic schema 强制；**语义校验仍走 gate**（clean_spec /
clean_conclusion）—— schema 只管形状，拒绝信息保持 gate 的中文原文。

叶子是**直接工具**模型：bash / read / write 是它自己的工具，各住各的 schema
description（签名 / 超时 / 翻页语义的唯一来源），不再有「一段代码」这个中间载体。
产出的记账从子进程自报改成工具自己报：write 写谁、bash 命令里声明会写的目标，
跑前后各 stat 一次分 create / modify（工作区是共享的，只认它自己动过的路径，
不去 diff 整个工作区）。

**每个节点都是完整的 Loop**：分配节点和叶子一样，维护一段平铺对话
（st["msgs"]：基础 user + 累积的 assistant / tool / user 消息）。分配节点的
"观测"是它每次分配的记录（create_children 的 tool 结果）+ 下层节点的结论
（调度器注入），不再单发 render 整个历史。

工具实现要拿到**每个节点自己的运行时上下文**（节点是并发的）：`_step_binding`
是 ContextVar，ask() 开头写入 (ctx, nid)，工具函数用 `Depends(get_step_binding)`
注入 —— 每个 asyncio task 的 context 是独立的，并发节点互不串（AGENTS §9 无锁）。

代码只做四件事（都在形式字段上，不是计数器）：
  ① 规范化字段（**不切长度** —— 上限由提示词承诺，代码不再偷偷砍）
  ② 子任务的验收标准必须携带父/根的可测物理量，否则这次分配当场被拒并记进尝试
  ③ 一次最多一个门槛；门槛不成立，其余子任务不启动
  ④ 判定"满足"却指不出证据 → 降级为"未满足"
"""

import contextvars
import hashlib
import os
from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from ..effects import effects_of
from ..intake import intake_hooks, intake_spec, intake_tools
from ..protocol.gate import anchors, clean_conclusion, clean_spec, inherits
from ..protocol.tool_specs import ChildSpec, NODE_TOOLS, mcp, openai_tools
from ..prompts.messages import base_user, spec_line
from .. import config as cfg
from ..compression import RETRIEVE_NAME, compress_messages, retrieve_original
from .loop import Hooks, Outcome, ToolResult


# ---------------------------------------------------------------- 工具接线
# 每个节点类型的工具清单（OpenAI 格式，litellm 用）。schema 是静态的，
# 由 openai_tools() 缓存；这里只记名字，供 step 校验"这次调的是不是本层该调的"。
# 清单的单一事实是 tool_specs.NODE_TOOLS（docs/PROMPTS.md §4.2）；
# headroom_retrieve 只在 COMPRESS 开时挂（openai_tools 追加）。
_TOOL_NAMES = {"alloc": NODE_TOOLS["alloc"],
               "leaf": NODE_TOOLS["leaf"] + (RETRIEVE_NAME,)}

# ask 开头写入 (ctx, nid)；工具函数用 Depends 注入它。每个 asyncio task
# 的 contextvars 是独立的，所以并发节点拿到的各是各的 ctx。
_step_binding: contextvars.ContextVar = contextvars.ContextVar(
    "step_binding", default=None)


def get_step_binding():
    return _step_binding.get()


def _root_anchors(node, state):
    """任务根（入口节点的孩子 / 无父节点）的可测物理量。

    一场会话的根是入口节点（它没有形式字段）；一个**任务**的根是入口的孩子。
    沿 parent 链走到最上层那个非入口节点，拿它的 accept 算锚点。
    """
    cur = node
    while cur.parent:
        p = state.get(cur.parent, {}).get("node")
        if p is None or p.kind == "intake":
            break
        cur = p
    return anchors(cur.accept)


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


# ---------------------------------------------------------------- 节点的语义
# 骨架（问模型 / 跑工具 / 写对话 / 发事件）在 loop.py；这里只填"节点怎么做"：
# 拼要发的消息、给工具表、看回复和结果定下一拍。
def node_hooks(nid, runtime):
    """一个节点的三处语义（loop.Hooks）。

    每个节点（分配节点和叶子一样）都是完整的 Loop：系统提示词（render_turn，
    含字节稳定的 base_user）+ 累积的平铺对话（账本在 st["transcript"]）。
    压缩只发生在发送边界（before_chat），只压 role=tool 的工具输出。
    """
    st = runtime["state"][nid]
    node = st["node"]
    if node.kind == "intake":
        return intake_hooks(nid, runtime)
    which = "leaf" if node.kind == "leaf" else "alloc"
    llm, trace, budget = runtime["llm"], runtime["trace"], runtime["budget"]

    async def before_chat(transcript):
        if budget.exhausted():
            node.close("阻塞", "预算耗尽: " + budget.why(), [])
            trace.add(node.id, "budget_exhausted", node.conclusion)
            return Outcome("stop", reason="budget")
        trace.add(node.id, "%s_in" % which, base_user(node))
        wire = transcript.wire()
        if which == "leaf" and cfg.COMPRESS and any(
                m.get("role") == "tool" for m in wire):
            result = await compress_messages(wire, getattr(llm, "model", ""))
            wire = result.messages
            if result.tokens_saved > 0:
                trace.add(node.id, "wire_compressed", {
                    "before": result.tokens_before, "after": result.tokens_after,
                    "saved": result.tokens_saved,
                    "ratio": (round(result.tokens_saved / result.tokens_before, 3)
                              if result.tokens_before else 0.0),
                    "transforms": result.transforms_applied})
        return wire

    async def after_chat(transcript, assistant):
        _log_usage(llm, trace, node.id, which, budget)
        trace.add(node.id, "%s_out" % which,
                  {"text": assistant.text,
                   "tool_calls": [{"name": tc.name, "arguments": tc.arguments}
                                  for tc in assistant.tool_calls]})
        if not assistant.tool_calls:
            hint = ("（你只回了一段文字，开头：%s）" % assistant.text[:60]
                    ) if assistant.text else ""
            why = ("这次回复没有调用任何工具%s。你必须调用一个：%s。"
                   % (hint, " / ".join(_TOOL_NAMES[which])))
            transcript.add_feedback(why)
            return _to_outcome(balk(node, why, trace, st))
        if len(assistant.tool_calls) > 1:
            why = "一次只能调用一个工具（你调了 %d 个）" % len(assistant.tool_calls)
            transcript.add_feedback(why)
            return _to_outcome(balk(node, why, trace, st))
        tc = assistant.tool_calls[0]
        if tc.name not in _TOOL_NAMES[which]:
            why = ("你调用的 %s 不在这一层的工具里（你能用：%s）"
                   % (tc.name, " / ".join(_TOOL_NAMES[which])))
            transcript.add_feedback(why)
            return _to_outcome(balk(node, why, trace, st))
        return None

    async def after_tool(transcript, assistant, results):
        rej = next((r.reject for r in results if r.reject), "")
        if rej:
            return _to_outcome(balk(node, rej, trace, st))
        for r in results:
            if r.effect == "stop":
                return Outcome("stop")
            if r.effect == "suspend":
                return Outcome("suspend", payload=r.payload)
        return Outcome("continue")

    return Hooks(before_chat=before_chat, after_chat=after_chat,
                 after_tool=after_tool)


async def node_spec(nid, runtime):
    """这个节点喂给模型的工具声明（OpenAI 格式）。"""
    node = runtime["state"][nid]["node"]
    if node.kind == "intake":
        return await intake_spec(nid, runtime)
    which = "leaf" if node.kind == "leaf" else "alloc"
    return (await openai_tools())[which]


def node_tools(nid, runtime):
    """这个节点可调用的工具：名字 → async(args) -> ToolResult。"""
    node = runtime["state"][nid]["node"]
    if node.kind == "intake":
        return intake_tools(nid, runtime)
    which = "leaf" if node.kind == "leaf" else "alloc"

    def make(name):
        async def call(args):
            _step_binding.set((runtime, nid))
            # 取回工具：把被压过的工具输出原文写回对话（作为 tool 结果）
            if name == RETRIEVE_NAME:
                return ToolResult(text=retrieve_original(args))
            tool = await mcp.get_tool(name)
            try:
                res = await tool.run(args)
            except ToolValidationError as e:
                # schema 拒的参数（缺必填 / 类型错）：一条可见的事实，让模型改
                why = "工具参数不合形状，被退回：%s" % e
                return ToolResult(text=why, reject=why)
            d = res.structured_content
            if not isinstance(d, dict):
                raise TypeError("工具 %s 必须返回 dict（拿到 %r）" % (name, d))
            text = d["obs"] if d.get("obs") is not None else (d.get("feedback") or "")
            return ToolResult(text=text, effect=_effect(d), payload=_payload(d))
        return call

    return {name: make(name) for name in _TOOL_NAMES[which]}


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

    不是轮次上限：换一个动作、或者世界回话变了，指纹就不同。
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


def balk(node, why, trace, st):
    """把"这次给的东西用不了"变成一条可见的事实，并且**按重复次数处理**。

    四个地方都要走它：没调工具 / 参数不合形状 / 被代码拒的分配 / 不合规的结论。
    没有它，模型一直给同样的东西，这一回合就原地无限重复 ——
    实测撞过两次（旧协议的键；总缺 accept 的子任务）。那两种情况下
    根本没有动作，所以"重复动作"那个信号永远不会触发：这里必须自己数。

    这不是轮次上限：换一种拆法、换一个错，指纹就不同。
    """
    n, note = bump(st.setdefault("seen_actions", {}),
                   sig("(balk)", why), trace, node, "(用不了的输出)")
    if n >= 5:
        node.close("未满足", "同一份用不了的东西连续 %d 次，没有新信息：%s"
                   % (n, why), [])
        return {"kind": "finished"}
    # feedback：step 会把打回理由写回本节点的平铺对话（配对成 tool/user 消息），
    # 不然模型下一回合看不到自己为什么被拒。分配节点和叶子同构。
    return {"kind": "again", "feedback": why + note}


# ---------------------------------------------------------------- 动手
def _obs_label(tool, args):
    """观测历史里给这一次工具调用的标题：够短。"""
    if tool == "bash":
        for ln in str(args.get("cmd") or "").splitlines():
            if ln.strip():
                s = ln.strip()
                return "bash(%s)" % (s if len(s) <= 120 else s[:120] + "…")
        return "bash()"
    return "%s(%s)" % (tool, str(args.get("path") or "?"))


def _record_effects(st, trace, node_id, tool, args, eff, pre, created, modified):
    """把一次工具动作的产出落成 trace 的 effects 事件（给人看的过程记录）。

    created / modified 是这次动作之后确实存在、属于它的产物路径。
    历史只活在一处（节点对话）；这里只发事件，不存任何节点状态。
    """
    trace.add(node_id, "effects", {"tool": tool, "args": args,
                                   "wrote": created + modified,
                                   "effects": eff, "前置条件": pre})


def _action_result(st, trace, node, tool, args, obs):
    """一次工具动作的收尾：trace + 无进展检测。返回 step 的下一拍。

    同一件事重复 ≥3 次显式告警、≥5 次自己停下（指纹 = 动作 + 观测，
    换动作或世界回话变了指纹就不同）。历史进对话（工具结果消息），
    这里只发事件、记账指纹。
    """
    what = _obs_label(tool, args)
    n, note = bump(st.setdefault("seen_actions", {}),
                   sig(what, obs), trace, node, what)
    if note:
        obs = str(obs) + note
    trace.add(node.id, "tool", {"tool": tool, "args": args, "obs": str(obs)})
    if n >= 5:
        msg = "同一件事重复 %d 次、输出完全一样，没有新信息：%s" % (n, what)
        trace.add(node.id, "stalled", msg)
        node.close("未满足", msg, [])
        return {"kind": "finished"}
    return {"kind": "again", "obs": obs}


# ---------------------------------------------------------------- 工具
@mcp.tool
async def create_children(children: list[ChildSpec],
                          _b=Depends(get_step_binding)) -> dict:
    """把任务拆成更小的子任务交给下层节点。调它 = 再拆一层。

    除 notes / gate 外全部必填：缺了或形状不对，这次分配会被代码当场退回，
    原因写回本层对话。一次最多一个 gate。
    """
    st, node, trace, budget, rctx = _current(_b)
    kids_spec, reject = [], None
    for raw in (c.model_dump() for c in children):
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        # ② 子任务的验收标准必须携带父/根的可测物理量
        ra = _root_anchors(node, rctx["state"])
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
        return balk(node, reject, trace, st)

    gates = [s for s in kids_spec if s["gate"]]
    if len(gates) > 1:
        return balk(node, "一次分配最多一个门槛", trace, st)
    gate = gates[0] if gates else None
    if gate:
        first = [gate]
        rest = [s for s in kids_spec if s is not gate]
    else:
        first, rest = kids_spec, []          # 没有门槛就没有"暂缓"，不能把全部当成暂缓

    if not budget.take_nodes(len(kids_spec)):
        return balk(node, "节点预算不足", trace, st)
    gate = gates[0] if gates else None
    if gate:
        first = [gate]
        rest = [s for s in kids_spec if s is not gate]
    else:
        first, rest = kids_spec, []          # 没有门槛就没有"暂缓"，不能把全部当成暂缓
    node.deferred = rest                     # 暂缓计划存节点上：孩子还没出生，无处可推
    trace.add(node.id, "allocated",
              {"gate": gate["name"] if gate else None,
               "deferred": [s["name"] for s in rest] if gate else []})
    # obs = 这次分配的平铺记录，step 会把它写回本节点的对话（分配节点的历史
    # 也走对话消息累积，和叶子同构 —— 完整 Loop）。
    alloc_lines = ["这次分配了 %d 个子任务（除 notes / gate 外全部必填）："
                   % len(kids_spec)]
    for s in kids_spec:
        alloc_lines.append("  - %s" % spec_line(s))
    if gate:
        alloc_lines.append("门槛：%s —— 它先做，不成立则其余不启动。" % gate["name"])
    return {"kind": "children", "first": first, "rest": rest,
            "gate_name": gate["name"] if gate else None,
            "obs": "\n".join(alloc_lines)}


@mcp.tool
async def bash(cmd: Annotated[str,
    "要跑的一条命令，如 bash sum.sh 或 python3 main.py --flag x。"
    "跑在一个真的进程里（当前工作目录），输出与退出码就是观测。"],
               timeout: Annotated[int,
    "超时秒数。默认 120 秒，上限 3600 秒；超了会连同它起的子进程一起被杀，"
    "并**明说是超时**、把已经产生的输出交给你。真要跑很久（下载 / 训练 / 编译）："
    "把 timeout 调大，或 `nohup <cmd> > run.log 2>&1 &` 起在后台，"
    "再轮询 run.log 和产物。"] = 120,
               _b=Depends(get_step_binding)) -> dict:
    """跑一条命令。命令是唯一能改变世界的东西，一次一条，次数不限。

    print 打出来的、报错（异常）、exit 码，**都是观测**。
    出错是常事，也是信息：异常原样给你。别重复跑同一段命令 ——
    换个做法，或者把出错当成事实，用结论「未满足/阻塞」说清楚。
    """
    st, node, trace, budget, rctx = _current(_b)
    cmd = str(cmd or "")
    if not cmd.strip():
        return balk(node, "cmd 是空的：要么写一条命令，要么用 conclude 出结论",
                    trace, st)
    cwd = os.getcwd()
    # 产出记账：命令里声明会写的目标，跑前后各 stat 一次分 create / modify。
    # 工作区是共享的、节点是并发的 —— 只认它自己声明过的路径，不去 diff
    # 整个工作区（全局 diff 会把别的节点此刻写的文件算到它头上）。
    eff, pre = effects_of("bash", {"cmd": cmd}, cwd=cwd)
    declared = eff["fs"]["create"] + eff["fs"]["modify"]
    existed = {p: os.path.exists(p) for p in declared}
    obs = str(await rctx["hands"].run("bash", {"cmd": cmd, "timeout": timeout}))
    created = [p for p in declared if not existed[p] and os.path.exists(p)]
    modified = [p for p in declared if existed[p] and os.path.exists(p)]
    eff["fs"] = {"create": created, "modify": modified, "delete": []}
    _record_effects(st, trace, node.id, "bash", {"cmd": cmd}, eff, pre,
                    created, modified)
    return _action_result(st, trace, node, "bash", {"cmd": cmd, "timeout": timeout}, obs)


@mcp.tool
async def read(path: Annotated[str, "要读的文件路径（相对工作区）。"],
               offset: Annotated[int, "从第几个字开始读。返回里会写清「本段在哪、还有多少字」；"
                                      "要下一段就照它给的下标再调一次。"] = 0,
               limit: Annotated[int, "最多读多少字。"] = 2000,
               _b=Depends(get_step_binding)) -> dict:
    """读文件的一段，并明说这段在哪、还有多少。"""
    st, node, trace, budget, rctx = _current(_b)
    obs = str(await rctx["hands"].run("read", {"path": path, "offset": offset,
                                               "limit": limit}))
    eff, pre = effects_of("read", {"path": path}, cwd=os.getcwd())
    trace.add(node.id, "effects", {"tool": "read", "args": {"path": path},
                                   "effects": eff, "前置条件": pre})
    return _action_result(st, trace, node, "read", {"path": path, "offset": offset,
                                                    "limit": limit}, obs)


@mcp.tool
async def write(path: Annotated[str, "要写的文件路径（相对工作区）。写文件是产出 —— "
                                     "结论里必须交代它。"],
                content: Annotated[str, "文件内容。"] = "",
                _b=Depends(get_step_binding)) -> dict:
    """写一个文件。产出会记进你的账本，conclude 时必须逐个交代。"""
    st, node, trace, budget, rctx = _current(_b)
    cwd = os.getcwd()
    ap = path if path.startswith("/") else os.path.normpath(os.path.join(cwd, path))
    existed = os.path.exists(ap)
    obs = str(await rctx["hands"].run("write", {"path": path, "content": content}))
    eff, pre = effects_of("write", {"path": path}, cwd=cwd, existed_before=existed)
    created = [ap] if (not existed and os.path.exists(ap)) else []
    modified = [ap] if (existed and os.path.exists(ap)) else []
    _record_effects(st, trace, node.id, "write", {"path": path}, eff, pre,
                    created, modified)
    return _action_result(st, trace, node, "write", {"path": path, "content": content},
                          obs)


@mcp.tool
async def conclude(verdict: str, text: str,
                   evidence: list[str] | None = None,
                   external: str = "",
                   _b=Depends(get_step_binding)) -> dict:
    """出结论：判定这件事做没做完。分配节点和叶子共用。

    判定「满足」必须指得出真证据（叶子：第几次观测 / 产物路径；分配节点：
    子任务 name / 产物路径），指不出来会被降级为未满足。
    """
    st, node, trace, budget, rctx = _current(_b)
    concl = {"verdict": verdict, "text": text, "evidence": evidence or [],
             "external": external}
    got, err = clean_conclusion(concl, trace, node,
                                msgs=st["transcript"].to_list())
    if err:
        trace.add(node.id, "bad_conclusion", err)
        return balk(node, err, trace, st)
    node.close(got["verdict"], got["content"], got["evidence"], got["external"])
    trace.add(node.id, "concluded",
              {"verdict": got["verdict"], "text": got["content"],
               "evidence": got["evidence"], "external": got["external"]})
    return {"kind": "finished"}


# ---------------------------------------------------------------- 下一拍
def _effect(d):
    """工具结果 dict 的 kind → 循环的下一拍。"""
    kind = d.get("kind")
    if kind == "finished":
        return "stop"
    if kind == "children":
        return "suspend"
    return "continue"                           # again


def _payload(d):
    """suspend 时带上孩子 / 门槛信息（分配节点挂起用）。"""
    if d.get("kind") != "children":
        return None
    return {"first": d["first"], "rest": d.get("rest") or [],
            "gate_name": d.get("gate_name")}


def _to_outcome(d):
    """打回 / 停 的 dict → Outcome（balk 返回的就是这两个 kind）。"""
    return Outcome(_effect(d))
