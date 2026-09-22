"""调度器：广度优先、并行扇出、门槛 —— 次数不限。

每个节点（入口 / 分配节点 / 叶子一样）都是**完整的 Loop**：读自己的形式字段 +
平铺对话（累积的 assistant/tool/user 消息）→ 做一个动作或出结论。

节点没有状态字段（没有 finished / waiting / ready / gate_id / rest）：
它是一棵带对话的 Node，"该不该调 LLM"由共享谓词 `reconcile.actionable` 回答
（没出结论 + 孩子都回话了 + 最后一条不是模型自己说的），孩子出结论由
`reconcile.settle` 结算（结果投进父节点对话 + 门槛续跑/作废）——
调度器与恢复（`session.load` 的补投递）用同一份，不各自写一遍。

**一场会话 = 一棵树**：入口节点（kind="intake"）是根，谈成的任务都是它的孩子。
`run` 跑整棵树 —— 入口在等用户（`ask`）时不占聊天名额，任务在跑时入口挂起等孩子。

**workers = 同时在飞的 `llm.chat` 数**（`ChatPool`，消息传递无锁）：限的是最贵的
那个资源，不是节点 Loop —— 节点卡在慢工具、或入口在等用户，都不占名额。

原则：
  · 形式化的是字段，次数不限，判断只看已经发生的事实
  · 分配节点**没有 execute 分支** ——"不拆"就是派一个叶子
  · 完成与否由上层看证据复核，节点只能说判定，不能自己算数
  · 所以这里没有任何计数器（max_rounds / self_exec / nudged / rejects 全部删除）

这个文件只管**编排**：谁先谁后、门槛过没过、并行几个。
"一个节点的一回合怎么走"在 `turn.py`（钩子）；"一轮消息往返的生命周期"在
`loop.py`。调度器不认识模型、不认识工具，只认识 Outcome 的三种 kind：
continue 在 Loop 内部消化，调度器只处理 suspend（等孩子）和 stop（完工）。

事件：调度器发节点级的 `loop_start` / `loop_end`（出生 / 完工是编排时点的事实），
其余（turn_* / message_* / tool_*）由 `loop.py` 和 `turn.py` 的钩子发。
"""

import asyncio
import os
from collections import deque

from ..llm import ChatPool
from ..prompts import render_turn
from ..prompts.messages import result_ids
from .hands import Hands
from .loop import Loop, Transcript, emit_for
from . import reconcile
from .trace import Trace
from .turn import node_hooks, node_spec, node_tools, which_of


def _checkpoint(nid, st, trace, ckpt_base):
    """把节点状态写进会话记录（trace 的 `state` 事件），恢复时据此重建。

    检查点就是全部状态：Node 全字段 + 平铺对话。没有编排字段 ——
    编排由 `reconcile` 从这两样推导。每次状态一变就落一笔。

    对话**增量落盘**（§11）：每节点第一笔写全量 msgs，其余只写「自上次检查点
    以来新增的消息」（delta + base），恢复端（session.load）按序拼回全量；
    node 字段小，每笔全量。恢复重开时 ckpt_base 从空起，第一笔自然全量。
    """
    msgs, is_delta, base = st["transcript"].checkpoint(ckpt_base.get(nid, 0))
    ckpt_base[nid] = base + len(msgs)
    payload = {"node": st["node"].to_dict(), "msgs": msgs}
    if is_delta:
        payload["delta"] = True
        payload["base"] = base
    trace.add(nid, "state", payload)


async def run(root, llm, trace, registry=None, workers=6,
              sink=None, resume=None, seed=None, ask=None, say=None):
    """跑一整棵树（新会话跑入口根，恢复跑读回来的树）。次数不限。

    真异步（P4）：一个节点的一整个 Loop = 一个 asyncio task。**workers 限的是
    同时在飞的 `llm.chat`**（`ChatPool`），不是节点 Loop —— 入口在等用户、
    节点卡在慢工具，都不占聊天名额。谁先完成谁先被回收（`FIRST_COMPLETED`）。
    节点挂起（等孩子）时它的 task 就结束了，等孩子全 settle 再起一个新 task
    续跑 —— 挂起/恢复是调度器的事，循环本身不知道"等孩子"。

    sink 是事件出口（`tree/events.py`）：节点出生/完工发 loop_start/loop_end，
    更细的事件由 loop/turn 的钩子发。没给 sink 就静默（测试直连调度器时如此）。

    ask / say 是入口节点的外部接线：`ask(text)` 拿用户的话（终端那次读，
    测试里换成脚本），`say(text)` 是旁白出口。只有入口节点用它们。

    resume：可选 tree（`session.load` 的返回）{"root", "state", "registry"}
    —— 一整棵树**接着跑**。恢复时：
      ① 按检查点重建 transcript（msgs）；
      ② 补投递：孩子有结论但父节点对话里没有（崩溃窗口）→ 用 `reconcile.settle`
         补结算，门槛该续跑就续跑；
      ③ 重排队列：`reconcile.actionable` 逐个问"该不该调 LLM"。
    中断那一刻在飞的那一步作废，节点带着完整的对话重新问模型 ——
    恢复的语义就是"接着上次停下来的那一步重来"，不是把整棵树重跑一遍。
    """
    registry = {} if registry is None else registry
    trace = trace if isinstance(trace, Trace) else Trace(trace)
    hands = Hands()
    pool = ChatPool(llm, workers)      # workers = 在飞的 llm.chat 数
    session_root = root                # 入口节点（新会话）/ 树根（恢复）
    state = {}                 # nid -> {"node", "transcript", "seen_actions"}
    delivered = {}             # nid -> 已投递结果的孩子 id 集合（运行时账本）
    ckpt_base = {}             # nid -> 上次检查点的消息起点（增量检查点的 base）
    pending = deque()

    def register(node):
        """节点出生：建账本、进登记册、发事件、进队列。"""
        st = {"node": node,
              "transcript": Transcript(system=render_turn(which_of(node), node)),
              "seen_actions": {}}
        state[node.id] = st
        delivered.setdefault(node.id, set())
        registry[node.id] = node
        trace.add(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "conc_range": node.conc_range,
            "workspace": os.path.abspath(os.getcwd())})
        pending.append(node.id)
        _checkpoint(node.id, st, trace, ckpt_base)

    def spawn_specs(parent, specs):
        """把子任务规格变成孩子节点并注册（派第一波 / 门槛通过续跑共用）。"""
        kids = []
        for s in specs:
            kid = reconcile.make_child(parent, s)
            register(kid)
            kids.append(kid)
        return kids

    def spawn_task(spec):
        """入口的 `submit_root` 落点：把任务根挂成入口节点的孩子。

        任务根是**顶层任务**（不带入口的意图链），它的 accept 已过 `validate_root`。
        """
        task = reconcile.make_child(session_root, spec)
        task.lineage = []              # 入口不是"上层意图"，任务是顶层
        register(task)
        return task

    if resume is not None:
        # registry 只有一个来源：恢复就取 resume 里那份（与终端展示、新节点登记同一份）
        raw, root, registry = resume["state"], resume["root"], resume["registry"]
        for nid, p in raw.items():
            node = p["node"]
            state[nid] = {"node": node,
                          "transcript": Transcript(system=render_turn(which_of(node), node),
                                                   msgs=p.get("msgs", [])),
                          "seen_actions": {}}
            registry[nid] = node
        # ① 已投递账本：从对话里的（id:…）标记重建
        for nid, st in state.items():
            delivered[nid] = result_ids(st["transcript"].to_list())
        # ② 补投递：孩子有结论但没结算进父节点（崩溃窗口）—— 和运行时同一个 settle
        for nid, st in list(state.items()):
            node = st["node"]
            dset = delivered[nid]
            for cid in list(node.children):
                cst = state.get(cid)
                if cst is None:
                    continue
                if cst["node"].verdict and cid not in dset:
                    reconcile.settle(
                        node, cst["node"], dset, registry,
                        inject=lambda text, s=st: s["transcript"].add_user_merged(text),
                        trace_add=lambda n, k, pl: trace.add(n, k, pl),
                        spawn=lambda specs, p=node: spawn_specs(p, specs))
                    _checkpoint(nid, st, trace, ckpt_base)
        # ③ 重排队列：同一个谓词，调度和恢复没有第二套规则。
        # 先清空 —— ② 补投递可能新生了孩子（门槛续跑），register 已经把它们
        # 排过队，不清会排两遍、孩子跑两次（实测）。
        pending.clear()
        for nid, st in state.items():
            if reconcile.actionable(st["node"], st["transcript"].to_list(),
                                    delivered[nid]):
                pending.append(nid)
    else:
        register(root)
        if seed is not None:
            state[root.id]["transcript"].add_user(seed)
            _checkpoint(root.id, state[root.id], trace, ckpt_base)

    def on_child_settled(nid):
        """孩子完工（stop）：先落它自己的最后一笔（判定 + 完整对话），
        再结算进父节点（投递 + 门槛），父节点全回话就重新排队。"""
        st = state[nid]
        child = st["node"]
        emit_for(sink, child.id)("loop_end", {"node": child})
        _checkpoint(nid, st, trace, ckpt_base)
        pid = child.parent
        if not pid or pid not in state:
            return
        pst = state[pid]
        parent = pst["node"]
        dset = delivered.setdefault(pid, set())
        may_run = reconcile.settle(
            parent, child, dset, registry,
            inject=lambda text: pst["transcript"].add_user_merged(text),
            trace_add=lambda n, k, pl: trace.add(n, k, pl),
            spawn=lambda specs: spawn_specs(parent, specs))
        _checkpoint(pid, pst, trace, ckpt_base)
        if may_run and not parent.verdict:
            pending.append(pid)

    # 工具与钩子共用的运行时现场（入口节点从 ask/say/spawn_task 拿外部接线）。
    runtime = {"state": state, "llm": llm, "trace": trace,
               "hands": hands, "ask": ask, "say": say, "spawn_task": spawn_task,
               "stream": bool(sink is not None and sink.streaming)}

    def dispatch(nid, out):
        """把 Loop 的产物翻译成编排动作。

        suspend：分配节点挂起了 —— 起第一波孩子、暂缓计划落在节点上（deferred）；
        入口节点挂起 = 任务已挂好（submit_root 干的），等它 settle。
        stop：节点完工（出结论 / 预算耗尽 / 原地打转）—— 结算进父节点。
        continue 永远不会冒到这里（由 Loop 内部消化）。
        """
        st = state[nid]
        if out.kind == "suspend":
            pn = st["node"]
            payload = out.payload or {}
            spawn_specs(pn, payload.get("first") or [])
            pn.deferred = payload.get("rest") or []
            _checkpoint(nid, st, trace, ckpt_base)
        else:
            on_child_settled(nid)

    def on_turn(nid, out):
        # 每轮结束落一笔检查点：中断时在飞的那一步作废，节点带着完整历史重问。
        # suspend / stop 由 dispatch 在起完孩子 / 结算后再落，这里只管 continue。
        if out.kind == "continue":
            _checkpoint(nid, state[nid], trace, ckpt_base)

    async def run_node(nid):
        st = state[nid]
        node = st["node"]
        # 入口节点的话有 sink 就流式（终端一直要）；节点级吐字只在真终端上流式
        stream = sink is not None if node.kind == "intake" else runtime["stream"]
        loop = Loop(pool, st["transcript"], await node_spec(nid, runtime),
                    await node_tools(nid, runtime), node_hooks(nid, runtime),
                    scope=nid, sink=sink, stream=stream,
                    temperature=0.3 if node.kind == "intake" else 0.2)
        return await loop.run(on_turn=lambda out: on_turn(nid, out))

    inflight = {}
    try:
        while pending or inflight:
            while pending:
                nid = pending.popleft()
                st = state[nid]
                if not reconcile.actionable(st["node"], st["transcript"].to_list(),
                                            delivered.get(nid, set())):
                    continue
                # loop_start = "这个节点的 Loop 真的要跑了"（不是在登记时）——
                # 恢复时重新开跑的节点也发得到，终端才能在恢复时点亮任务视图。
                emit_for(sink, nid)("loop_start", {"node": st["node"]})
                inflight[asyncio.ensure_future(run_node(nid))] = nid
            if not inflight:
                break
            done, _ = await asyncio.wait(list(inflight),
                                         return_when=asyncio.FIRST_COMPLETED)
            for fut in done:
                nid = inflight.pop(fut)
                dispatch(nid, fut.result())
    finally:
        await pool.close()
        await hands.close()
        trace.drain()
    return root
