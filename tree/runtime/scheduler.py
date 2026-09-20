"""调度器：广度优先、并行扇出、门槛、学能力 —— 次数不限。

    分配节点：读自己的形式字段 + 本层已有尝试 → 「再做一次分配」或「出结论」
    叶子：  读自己的形式字段 + 观测历史   → 「写一段代码」或「出结论」

原则：
  · 形式化的是字段，次数不限，判断只看已经发生的事实
  · 分配节点**没有 execute 分支** ——"不拆"就是派一个叶子
  · 完成与否由上层看证据复核，节点只能说判定，不能自己算数
  · 所以这里没有任何计数器（max_rounds / self_exec / nudged / rejects 全部删除）

这个文件只管**编排**：谁先谁后、门槛过没过、并行几个、什么时候学能力。
"一回合怎么走"在 `turn.py`；协议校验在 `protocol/gate.py`。
"""

import asyncio
import os
from collections import deque

from ..memory.mine import caps_from_node
from ..protocol.fields import Node
from ..protocol.gate import anchors
from .box import Box
from .budget import Budget
from .hands import Hands
from .trace import Trace
from .turn import step


def _checkpoint(nid, st, trace):
    """把节点状态写进会话记录（trace 的 `state` 事件），恢复时据此重建。

    每次状态一变就落一笔：节点全字段 + 调度器的编排字段。恢复只认这个 ——
    不再从 open/concluded 那些展示事件里猜（那些是给人看的，这里是事实本身）。
    calls 是 (工具, 参数, 观测) 元组，转成列表才好序列化；加载后解包不碍事。
    """
    trace.add(nid, "state", {
        "node": st["node"].to_dict(),
        "ready": st["ready"], "finished": st["finished"],
        "waiting": st["waiting"], "rest": st["rest"],
        "gate_id": st["gate_id"], "gate_name": st["gate_name"],
        "calls": [list(c) for c in st["calls"]],
        "contracts": st["contracts"],
        "artifacts": sorted(st["artifacts"]),
        "art_effects": st["art_effects"],
        "msgs": st.get("msgs", [])})


async def run(root, llm, trace, registry=None, budget=None, workers=6, caps=None,
              index=None, on_beat=None, beat=60, on_event=None,
              on_delta=None, on_reasoning=None, resume=None):
    """广度优先、并行扇出的调度器。次数不限——没有 max_depth/max_rounds。

    真异步（P4）：一个节点的一回合 = 一个 asyncio task，`workers` 是同时在飞
    的任务数。谁先完成谁先被回收（`FIRST_COMPLETED`），慢节点不拖整批。

    on_event(node) 是可选的事件回调：每个节点**出生**和**出结论**各调一次
    （节点状态当时分别是 running 和 done/failed）。它是给实时展示用的
    （终端据此重画任务树）—— 调度器只管发事实，怎么显示是消费方的事。

    on_delta(node_id, text) / on_reasoning(node_id, text) 是可选的**节点级
    实时吐字**回调：每个节点问模型时，把它吐的每一口（content / 思考）按
    node_id 送出来，给终端画进树里。没给就不开流式（入口那一路默认要）。

    resume：可选 dict {"state", "pending", "root"} —— 一棵跑了一半的树**接着跑**
    （会话记录里恢复出来的，见 `session.load`；registry 走参数传入，调用方负责
    把恢复出的节点合进来）。恢复时：已完工的节点不再碰，waiting>0 的继续等下层，
    其余重新排队（中断时刻在飞的那步作废，节点带着完整的观测/尝试历史重新问模型）。
    """
    registry = {} if registry is None else registry
    budget = Budget() if budget is None else budget
    trace = trace if isinstance(trace, Trace) else Trace(trace)
    hands = Hands()
    box = Box(caps, hands)

    def rebuild_msgs(node):
        """旧 trace（没有 msgs 检查点）恢复的叶子：把观测历史重建成对话。

        只写 user 消息（不带悬空 tool_call_id —— provider 会拒）。压缩只在
        发送边界做，存储（observations）永远是原文，所以重建不丢信息。
        """
        out = []
        for i, o in enumerate(node.observations, 1):
            out.append({"role": "user",
                        "content": "（你第 %d 次做了：%s）" % (i, o.get("action", ""))})
            out.append({"role": "user", "content": o.get("obs", "")})
        return out

    if resume is not None:
        state, pending, root = resume["state"], resume["pending"], resume["root"]
        # 恢复的节点没有出生时的运行时工具绑定（box.search 的结果不落盘），
        # 按同一组检索键重查一次补回来；先例/现成做法的**文字**已在节点里。
        for nid, st in state.items():
            if st["finished"]:
                continue
            node = st["node"]
            q = " ".join(str(x) for x in (node.keywords or [node.name, node.accept]))
            tools, _text, _hits = box.search(q)
            st["tools"] = tools
            # 旧 trace 没有 msgs 检查点：把观测历史重建成对话，别让恢复的叶子失忆
            if node.kind == "leaf" and not st.get("msgs") and node.observations:
                st["msgs"] = rebuild_msgs(node)
    else:
        state, pending = {}, deque()

    def register(node):
        state[node.id] = {"node": node, "ready": True, "finished": False,
                          "waiting": 0, "rest": [], "gate_id": None,
                          "gate_name": None, "calls": [], "tools": [],
                          "contracts": [], "artifacts": set(), "art_effects": {},
                          "seen_actions": {}}
        registry[node.id] = node
        trace.add(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "keywords": node.keywords, "conc_range": node.conc_range,
            "workspace": os.path.abspath(os.getcwd())})
        # 出生即检索：键是**上层给的**（根没有上层，就用它自己的名字+验收标准）。
        # 检索不花 LLM 调用，也不问模型要不要查 —— 实测它没有理由去查，
        # 而真正贵的恰恰是大事（DESIGN §5.4）。
        # **老树只给分配节点查**：先例回答的是"这件事该怎么拆、当年卡在哪"，
        # 而拆是分配节点的事；叶子要的是工具，老树对它只是噪音。
        if index is not None and node.kind == "dispatch":
            qs = node.keywords or ["%s %s" % (node.name, node.accept)]
            picked, text = index.search(qs, workspace=os.getcwd())
            if text:
                node.precedents.append(text)
            trace.add(node.id, "precedent",
                      {"queries": qs, "auto": True,
                       "hits": [p.id for p in picked], "chars": len(text)})
        # 现成做法也在出生时塞进来（**所有节点**：叶子就是要动手的那个）：
        # 模型没有动机去主动找工具（它觉得自己都会，§4.3），
        # 所以没有 need 这个动作 —— 程序按同一组检索键查能力库，直接给它。
        # 命中的工具同时存成 **绑定**：它们会在子进程里以同名函数出现，
        # 模型写代码就能直接调（见 runtime/sandbox.py）。
        q = " ".join(str(x) for x in (node.keywords or [node.name, node.accept]))
        tools, text, hits = box.search(q)
        if text:
            node.caps.append(text)
        state[node.id]["tools"] = tools
        trace.add(node.id, "caps_injected",
                  {"queries": node.keywords or [node.name],
                   "hits": hits, "chars": len(text),
                   "bindings": [t["name"] for t in tools]})
        pending.append(node.id)
        _checkpoint(node.id, state[node.id], trace)
        if on_event:
            on_event(node)

    def learn(node, calls, contracts=None):
        skipped = []
        for e in caps_from_node(node.id, node.name, calls,
                                os.path.basename(getattr(trace, "path", "")),
                                contracts, skipped):
            box.register(e)
            trace.add(node.id, "cap_learned",
                      {"does": e["does"], "keys": e["keys"],
                       "scope": e.get("scope"),
                       "可调用": bool((e.get("契约") or {}).get("func"))})
        # 不收的能力也要说得出来：理由 + 原命令，不悄悄丢
        for s in skipped:
            trace.add(node.id, "cap_skipped", s)

    def settle(nid, res):
        st = state[nid]
        if res["kind"] == "finished":
            st["finished"] = True
            node = st["node"]
            if on_event:
                on_event(node)
            if node.verdict in ("满足", "未满足") and caps is not None and st["calls"]:
                learn(node, st["calls"], st.get("contracts"))
            _checkpoint(nid, st, trace)
            parent = node.parent
            if parent and parent in state:
                pst = state[parent]
                pn = pst["node"]
                if pn.attempts:
                    pn.attempts[-1].setdefault("results", []).append(node.record())
                # 门槛不成立 → 整个分支作废，其余子任务永不启动
                if pst.get("gate_id") == nid and node.verdict != "满足":
                    skipped = [s["name"] for s in pst.get("rest") or []]
                    pst["rest"], pst["gate_id"] = [], None
                    if pn.attempts:
                        pn.attempts[-1]["outcome"] = "门槛不成立（%s）: %s" % (
                            node.name, node.conclusion)
                        if skipped:
                            pn.attempts[-1]["results"].append(
                                {"name": "（以下子任务被跳过）", "outcome": "未启动",
                                 "text": ", ".join(skipped), "evidence": []})
                    trace.add(parent, "gate_failed",
                              {"gate": node.name, "reason": node.conclusion,
                               "skipped": skipped})
                    if not pst["finished"]:
                        pst["ready"] = True
                        pending.append(parent)
                    _checkpoint(parent, pst, trace)
                    return
                pst["waiting"] -= 1
                _checkpoint(parent, pst, trace)
                if pst["waiting"] <= 0 and not pst["finished"]:
                    if pn.attempts:
                        pn.attempts[-1]["outcome"] = "下层已全部返回"
                    if pst.get("rest"):
                        rest, pst["rest"], pst["gate_id"] = pst["rest"], [], None
                        trace.add(parent, "gate_passed",
                                  {"started": [s["name"] for s in rest]})
                        kids = _spawn(pn, rest)
                        for k in kids:
                            register(k)
                        pst["waiting"] = len(kids)
                        _checkpoint(parent, pst, trace)
                    else:
                        pst["ready"] = True
                        pending.append(parent)
                        _checkpoint(parent, pst, trace)
        elif res["kind"] == "children":
            for k in res["kids"]:
                register(k)
            st["waiting"] = len(res["kids"])
            st["rest"] = res.get("rest") or []
            st["gate_id"] = res.get("gate_id")
            _checkpoint(nid, st, trace)
        else:                                      # again：接着再来一回合
            if not st["finished"]:
                st["ready"] = True
                pending.append(nid)
                _checkpoint(nid, st, trace)

    def _spawn(parent, specs):
        kids = []
        for s in specs:
            kids.append(Node(name=s["name"], detail=s["detail"], notes=s["notes"],
                             accept=s["accept"], kind=s["kind"], gate=s["gate"],
                             keywords=s["keywords"], conc_range=s["conc_range"],
                             parent=parent.id, depth=parent.depth + 1,
                             # 意图链只加一层，孩子不重新把祖先走一遍（§11）
                             lineage=parent.lineage + [[parent.name, parent.detail]]))
        parent.children += [k.id for k in kids]
        return kids

    ctx = {"state": state, "llm": llm, "trace": trace, "budget": budget,
           "root_anchors": anchors(root.accept),
           "caps": caps, "index": index, "hands": hands, "box": box,
           "on_delta": on_delta, "on_reasoning": on_reasoning}

    def dispatch(nid, res):
        """把 step 的抽象结果翻译成真实的节点/子节点。"""
        if res["kind"] != "children":
            settle(nid, res)
            return
        st = state[nid]
        pn = st["node"]
        first = _spawn(pn, res["first"])
        rest = res["rest"]
        gate_kid = first[0] if res["gate_name"] else None
        settle(nid, {"kind": "children", "kids": first,
                     "rest": rest,
                     "gate_id": gate_kid.id if gate_kid else None})

    inflight = {}
    try:
        if resume is None:
            register(root)
        while pending or inflight:
            while pending and len(inflight) < workers:
                nid = pending.popleft()
                st = state[nid]
                if st["finished"] or not st["ready"]:
                    continue
                st["ready"] = False
                inflight[asyncio.ensure_future(step(nid, ctx))] = nid
            if not inflight:
                break
            done, _ = await asyncio.wait(list(inflight),
                                         return_when=asyncio.FIRST_COMPLETED,
                                         timeout=beat if on_beat else None)
            if not done:
                on_beat()
                continue
            for fut in done:
                nid = inflight.pop(fut)
                dispatch(nid, fut.result())
    finally:
        await hands.close()
        trace.drain()
    return root
