"""会话的恢复：把 trace（统一会话记录）读回能继续跑的状态。

`trace.jsonl` 是一场会话的**完整记录**，几类事件按时间顺序混排在同一份
append-only 文件里：

  - 节点生命周期（open / concluded / code / …）—— 给人看、给索引搜的；
  - `state` 检查点 —— 调度器每次状态一变写一笔（`scheduler._checkpoint`），
    恢复时每个节点取**最后一笔**；
  - `chat_*` —— intake 对话的每一条消息（用户说的、模型回的、工具回填的）。

**恢复只认 state 和 chat_***：节点生命周期那些事件是给别的消费者看的，重建运行
状态不靠它们（靠展示物猜事实会猜错）。历史旧格式会话没有 state 检查点，
由 `migrate_sessions.py` 一次性迁移成新格式 —— 运行时不再有第二种格式。

恢复时的重排规则（和调度器自己的编排同一套逻辑）：
  - finished 的节点不动（已完工，不再碰）；
  - waiting>0 的节点继续等下层（孩子还没回来）；
  - 其余一律重新排队（ready=True）—— 中断那一刻在飞的那一步作废，
    节点带着完整的观测 / 尝试历史重新问模型。恢复的语义就是
    "接着上次停下来的那一步重来"，不是把整棵树重跑一遍。
"""

from collections import deque

from ..memory.index import iter_trace_lines
from ..protocol.fields import Node


def session_context(trees):
    """把一场会话的树变成给模型的上下文。

    会话没有对话记录（chat_msgs 为空，比如迁移来的旧会话）时用它开局 ——
    不然模型不知道这场会话做过什么，像新会话一样两眼一抹黑。只写**记录里的
    事实**（任务/验收/判定/结论），不添"继续老会话"这类话术：加载出来就是
    当前会话。
    """
    if not trees:
        return None
    lines = ["这场会话已经做过这些事（从会话记录恢复）:"]
    for i, t in enumerate(trees, 1):
        r = t["root"]
        lines.append("%d. 任务: %s" % (i, r.name or "(无任务名)"))
        if r.accept:
            lines.append("   验收标准: %s" % r.accept)
        lines.append("   判定: %s" % (r.verdict or "（没出结论）"))
        if r.conclusion:
            lines.append("   结论: %s" % r.conclusion)
    return "\n".join(lines)


def load(path):
    """读一场会话的记录，返回可继续跑的现场。

    chat_msgs  -> intake 对话（含开头那条 seed，不含 system；恢复后回填）
    trees      -> 每棵根树 {"root", "registry", "state", "pending"}（提交顺序）
    in_flight  -> 中断时正在跑的那棵树（有没完工的节点），没有则 None
    """
    states = {}                 # nid -> 最后一笔 state（dict 保留注册顺序）
    chat = []
    for r in iter_trace_lines(path):
        k, p = r.get("kind"), r.get("payload") or {}
        if k == "state":
            states[r.get("node")] = p
        elif k == "chat_user":
            chat.append({"role": "user", "content": p.get("text")})
        elif k == "chat_model":
            m = {"role": "assistant", "content": p.get("text") or ""}
            if p.get("tool_calls"):
                m["tool_calls"] = p["tool_calls"]
            chat.append(m)
        elif k == "chat_tool":
            chat.append({"role": "tool", "tool_call_id": p.get("tool_call_id"),
                         "content": p.get("content")})

    registry, state = {}, {}
    for nid, p in states.items():
        node = Node.from_dict(p["node"])
        registry[nid] = node
        state[nid] = {"node": node,
                      "ready": p["ready"], "finished": p["finished"],
                      "waiting": p["waiting"], "rest": p["rest"],
                      "gate_id": p["gate_id"], "gate_name": p["gate_name"],
                      "calls": p["calls"], "contracts": p["contracts"],
                      "artifacts": set(p["artifacts"]),
                      "art_effects": p["art_effects"],
                      "tools": [], "seen_actions": {}}

    pending = deque()
    for nid, st in state.items():
        if st["finished"]:
            continue
        node = st["node"]
        # waiting 不信任存的值：中断可能发生在"孩子完工 → 父节点结算"之间
        # （结算在 settle 里是同步几步，但确有一个窗口）。以孩子状态为准重算 ——
        # 孩子引用按 state 里的 parent 链接数，不按 node.children（可能旧）。
        kids = [c for c in state if state[c]["node"].parent == nid]
        unfinished = [c for c in kids if not state[c]["finished"]]
        if unfinished:
            st["waiting"] = len(unfinished)
            continue                       # 还在等下层，不排队
        # 门槛：gate 孩子已出结论而父节点还没结算时，按结论处理暂缓分支
        gid = st["gate_id"]
        if gid and gid in state and state[gid]["finished"]:
            if state[gid]["node"].verdict != "满足":
                st["rest"], st["gate_id"] = [], None   # 门槛不成立 → 分支作废
        st["waiting"] = 0
        st["ready"] = True
        pending.append(nid)

    def subtree_ids(root_id):
        ids, stack = [], [root_id]
        while stack:
            nid = stack.pop()
            n = registry.get(nid)
            if n is None:
                continue     # 孩子引用了没写完 state 的节点：那一步从没"出生"
            ids.append(nid)
            stack.extend(c for c in n.children if c in registry)
        return ids

    trees, in_flight = [], None
    for r in [registry[nid] for nid in state if registry[nid].parent is None]:
        ids = subtree_ids(r.id)
        reg = {nid: registry[nid] for nid in ids}
        st = {nid: state[nid] for nid in ids}
        t = {"root": r, "registry": reg, "state": st,
             "pending": deque(nid for nid in pending if nid in ids)}
        trees.append(t)
        if any(not st[nid]["finished"] for nid in ids):
            in_flight = t
    return {"chat_msgs": chat, "trees": trees, "in_flight": in_flight}
