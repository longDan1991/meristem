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
`loop.py`；"节点数据放哪、怎么落盘、记录怎么写"在 `store.py`（调度器只看见
Node 和它的结论，不碰账本/检查点/记录文件）。调度器不认识模型、不认识工具，
只认识 Outcome 的三种 kind：continue 在 Loop 内部消化，调度器只处理
suspend（等孩子）和 stop（完工）。

事件：调度器发节点级的 `loop_start` / `loop_end`（出生 / 完工是编排时点的事实），
其余（turn_* / message_* / tool_*）由 `loop.py` 和 `turn.py` 的钩子发。
"""

import asyncio
from collections import deque

from ..llm import ChatPool
from ..events import EventSink
from .hands import Hands
from .loop import Loop
from . import reconcile
from .store import TreeStore
from .turn import node_hooks, node_spec, node_tools
from .. import config as cfg


async def run(tree, llm, *, workers=cfg.WORKERS, subscribe=None,
              ask=None, say=None):
    """跑一棵树（一场会话 = 一棵树：新会话与恢复是同一件事的两个入口）。

    tree = {"root", "state", "registry", "trace", "seed"} —— 会话的全部数据，
    由 `session.new_session(root)`（新）或 `session.load(path)`（恢复）建好。
    registry 就地登记每个节点 —— 调用方拿着 tree 就能看整棵树长出来 / 接着长。
    tree["trace"] 是记录文件的路径：存储（TreeStore）构造时按它打开记录 ——
    底层文件不成为 run 的入参，也没有第二个"写哪"的入口。
    llm 是模型本身（外部依赖，测试换假模型）。

    编排之外的东西都归 `TreeStore`（会话的存储）：账本（transcript/registry/
    已投递）、检查点落盘、运行事件记录 —— 这里只回答"谁该跑、谁先谁后、
    并行几个"。新会话（state 空）登记根开跑，seed 是入口的第一句话；恢复
    （state 非空）按检查点重建账本 + 补投递（崩溃窗口）+ 按同一个谓词重排队列。

    真异步（P4）：一个节点的一整个 Loop = 一个 asyncio task。**workers 限的是
    同时在飞的 `llm.chat`**（`ChatPool`，默认取配置），不是节点 Loop —— 入口
    在等用户、节点卡在慢工具，都不占聊天名额。谁先完成谁先被回收
    （`FIRST_COMPLETED`）。节点挂起（等孩子）时它的 task 就结束了，等孩子全
    settle 再起一个新 task 续跑 —— 挂起/恢复是调度器的事，循环本身不知道"等孩子"。

    subscribe / ask / say 是外界的接线：
      · subscribe 事件消费者（consumer(type, payload)）—— 调度器发节点出生/
        完工的 loop_start/loop_end，并把同一个 consumer 订阅到每个 Loop 内建的
        sink（更细的事件由 loop/turn 的钩子发）；没给就静默（EventSink 零
        消费者时 emit 是 no-op，测试直连时如此）；
      · ask(text) 拿用户的话、say(text) 是旁白出口 —— 只有入口节点用。

    返回 tree（同一棵，registry 已长全）。
    """
    store = TreeStore(tree)       # 存储：新会话空账本 / 恢复按检查点重建 + 记录文件
    hands = Hands()
    pool = ChatPool(llm, workers)      # workers = 在飞的 llm.chat 数
    # 调度器自己的事件出口：loop_start / loop_end 是编排时点的事实，发生在
    # 任何 Loop 之前/之后，只能由这里发。每个 Loop 的事件经 loop.subscribe
    # 把同一个 consumer 订阅过去（见 run_node）。
    sink = EventSink()
    if subscribe is not None:
        sink.subscribe(subscribe)
    pending = deque()

    def emit(nid, kind, payload):
        sink.emit(kind, {"scope": nid, **payload})

    def born(node):
        """节点出生 = 建账本（store）+ 进队（调度）—— 出生时点两件事合一。"""
        store.register(node)
        pending.append(node.id)
        return node

    def spawn_specs(parent, specs):
        """把子任务规格变成孩子节点（派第一波 / 门槛续跑共用）。"""
        for s in specs:
            born(reconcile.make_child(parent, s))

    def spawn_task(spec):
        """入口的 `submit_root` 落点：把任务根挂成入口节点的孩子。

        任务根是**顶层任务**（不带入口的意图链），它的 accept 已过 `validate_root`。
        """
        task = reconcile.make_child(tree["root"], spec)
        task.lineage = []              # 入口不是"上层意图"，任务是顶层
        return born(task)

    def settle_child(pid, child):
        """把孩子的结论结算进父节点；返回 (该不该重新排队, 父节点)。"""
        parent = store.state[pid]["node"]
        return store.settle(pid, child,
                            spawn=lambda specs: spawn_specs(parent, specs))

    if not store.state:
        # 新会话：登记根开跑。
        born(tree["root"])
        if tree["seed"] is not None:
            store.seed(tree["root"].id, tree["seed"])
    else:
        # 恢复：补投递（崩溃窗口：孩子有结论但没结算进父节点）—— 和运行时同一个 settle。
        for nid, st in list(store.state.items()):
            for cid in list(st["node"].children):
                cst = store.state.get(cid)
                if cst and cst["node"].verdict and cid not in store.delivered[nid]:
                    settle_child(nid, cst["node"])

    # 重排队列：新会话的根 / 补投递新生孩子已由 born 排过，清掉按同一个谓词重排
    # （不清会排两遍、孩子跑两次 —— 实测）。
    pending.clear()
    for nid, st in store.state.items():
        if reconcile.actionable(st["node"], st["transcript"].to_list(),
                                store.delivered[nid]):
            pending.append(nid)

    def on_child_settled(nid):
        """孩子完工（stop）：先落它自己的最后一笔，再结算进父节点，
        父节点全回话就重新排队。"""
        st = store.state[nid]
        child = st["node"]
        emit(child.id, "loop_end", {"node": child})
        store.checkpoint(nid, st)
        pid = child.parent
        if not pid or pid not in store.state:
            return
        may_run, parent = settle_child(pid, child)
        if may_run and not parent.verdict:
            pending.append(pid)

    # 工具与钩子共用的运行时现场（入口节点从 ask/say/spawn_task 拿外部接线）。
    runtime = {"state": store.state, "llm": llm, "store": store,
               "hands": hands, "ask": ask, "say": say, "spawn_task": spawn_task}

    def dispatch(nid, out):
        """把 Loop 的产物翻译成编排动作。

        suspend：分配节点挂起了 —— 起第一波孩子、暂缓计划落在节点上（deferred）；
        入口节点挂起 = 任务已挂好（submit_root 干的），等它 settle。
        stop：节点完工（出结论 / 预算耗尽 / 原地打转）—— 结算进父节点。
        continue 永远不会冒到这里（由 Loop 内部消化）。
        """
        st = store.state[nid]
        if out.kind == "suspend":
            pn = st["node"]
            payload = out.payload or {}
            spawn_specs(pn, payload.get("first") or [])
            pn.deferred = payload.get("rest") or []
            store.checkpoint(nid, st)
        else:
            on_child_settled(nid)

    async def run_node(nid):
        st = store.state[nid]
        loop = Loop(pool, st["transcript"], await node_spec(nid, runtime),
                    await node_tools(nid, runtime), node_hooks(nid, runtime))
        if subscribe is not None:
            # Loop 不认识 scope：订阅的那一刻打上 —— 这是谁的 Loop 由这里定
            loop.subscribe(lambda t, p: subscribe(t, {"scope": nid, **p}))
        # 每轮结束落一笔检查点：中断时在飞的那一步作废，节点带着完整历史重问。
        # suspend / stop 由 dispatch 在起完孩子 / 结算后再落，这里只管 continue。
        def checkpoint_turn(out):
            if out.kind == "continue":
                store.checkpoint(nid, st)
        return await loop.run(on_turn=checkpoint_turn)

    inflight = {}
    try:
        while pending or inflight:
            while pending:
                nid = pending.popleft()
                st = store.state[nid]
                if not reconcile.actionable(st["node"], st["transcript"].to_list(),
                                            store.delivered.get(nid, set())):
                    continue
                # loop_start = "这个节点的 Loop 真的要跑了"（不是在登记时）——
                # 恢复时重新开跑的节点也发得到，终端才能在恢复时点亮任务视图。
                emit(nid, "loop_start", {"node": st["node"]})
                inflight[asyncio.ensure_future(run_node(nid))] = nid
            if not inflight:
                break                 # asyncio.wait([]) 直接 ValueError，不能空等
            done, _ = await asyncio.wait(list(inflight),
                                         return_when=asyncio.FIRST_COMPLETED)
            for fut in done:
                nid = inflight.pop(fut)
                dispatch(nid, fut.result())
    finally:
        try:
            await pool.close()
            await hands.close()
        finally:
            store.drain()     # 任何退出路（含取消）最后几笔都必须落盘
    return tree
