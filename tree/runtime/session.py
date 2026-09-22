"""会话的恢复：把 trace（统一会话记录）读回**一棵树**接着跑。

`trace.jsonl` 是一场会话的**完整记录**，几类事件按时间顺序混排在同一份
append-only 文件里：

  - 节点生命周期（open / concluded / …）—— 给人看的；
  - `state` 检查点 —— 调度器每次状态一变写一笔（`scheduler._checkpoint`），
    恢复时每个节点取**最后一笔**。检查点就是全部状态：Node 全字段 + 平铺对话
    （`msgs`），没有编排字段 —— 编排由 `runtime/reconcile.py` 从这两样推导。

**一场会话 = 一棵树**：入口节点（kind="intake"）是根，谈成的任务都是它的
孩子。`load` 读回来的就是这棵树（root / registry / state / pending），
直接丢给 `scheduler.run(..., resume=tree)` 就能接着跑。

恢复只认 `state`：节点生命周期那些事件是给别的消费者看的，重建运行状态不靠
它们（靠展示物猜事实会猜错）。历史旧格式会话没有 state 检查点，由
`migrate_sessions.py` 一次性迁移成新格式 —— 运行时不再有第二种格式。

`load` 只做反序列化 + 树分组；补投递（崩溃窗口）与重排队列（该不该调 LLM）
由调度器 resume 时用 `reconcile` 做 —— 不在这里重写一遍编排。
"""

import os
import time
from collections import deque

from ..protocol.fields import Node
from ..prompts.messages import result_ids
from . import reconcile
from .trace import iter_trace_lines


def session_label(path):
    """一场会话的一行摘要（时间 + 最新任务 + 判定）。给 `-r` 的列表用。

    根的 open 是入口节点（kind="intake"，没有任务名）；任务 = 入口的孩子。
    旧格式 / 迁移来的会话可能没有入口的 open（任务根还挂着 parent=None），
    那种也照样当任务认。只读记录里本来就有的 open / concluded / done 事件，不编造。
    """
    opens, intake_ids = {}, set()
    tasks = {}
    for r in iter_trace_lines(path):
        p = r.get("payload") or {}
        nid = r.get("node")
        k = r.get("kind")
        if k == "open" and nid:
            opens[nid] = p
            if p.get("kind") == "intake":
                intake_ids.add(nid)
        elif k == "concluded" and nid in tasks:
            tasks[nid]["verdict"] = p.get("verdict") or p.get("判定") or ""
        elif k == "done" and nid in tasks:                # 旧格式
            tasks[nid]["verdict"] = tasks[nid]["verdict"] or "满足"
        elif k in ("failed", "crashed", "budget_exhausted") and nid in tasks:
            tasks[nid]["verdict"] = tasks[nid]["verdict"] or "阻塞"
    # 任务 = kind 不是 intake、且父为空或父是入口的 open
    for nid, p in opens.items():
        if p.get("kind") == "intake":
            continue
        if not p.get("parent") or p.get("parent") in intake_ids:
            tasks[nid] = {"name": p.get("name") or p.get("任务名") or p.get("task") or "",
                          "verdict": tasks.get(nid, {}).get("verdict", ""),
                          "t": None}
    mtime = os.path.getmtime(path)
    if not tasks:
        return "%s （还没跑过任务）" % time.strftime(
            "%m-%d %H:%M", time.localtime(mtime))
    latest = max(tasks.values(), key=lambda x: x["t"] or mtime)
    name = (latest["name"] or "(无任务名)")[:40]
    verdict = latest["verdict"] or "运行中"
    extra = "" if len(tasks) == 1 else "（共 %d 个任务）" % len(tasks)
    return "%s %s [%s]%s" % (time.strftime(
        "%m-%d %H:%M", time.localtime(latest["t"] or mtime)),
        name, verdict, extra)


def load(path):
    """读一场会话的记录，返回**一棵树**：{"root", "registry", "state", "pending"}。

    拿它直接进 `scheduler.run(tree["root"], ..., resume=tree)` 就能接着跑。

    state[nid] = {"node": Node, "msgs": [...]} —— 检查点原样，无编排字段。
    pending 只是 `reconcile.actionable` 的最佳猜测（调度器 resume 会重排）。
    还没迁移的老会话（没有 state 检查点、或没有唯一的入口根）当场报错 ——
    让错误带着上下文炸出来，不静默给一棵半成品树。
    """
    states = {}                 # nid -> 最后一笔 state（dict 保留注册顺序）
    for r in iter_trace_lines(path):
        if r.get("kind") == "state":
            states[r.get("node")] = r.get("payload") or {}

    if not states:
        raise ValueError("这份会话没有 state 检查点（老格式？先跑迁移："
                         "uv run python migrate_sessions.py）")
    registry = {nid: Node.from_dict(p["node"]) for nid, p in states.items()}
    roots = [registry[nid] for nid in states if registry[nid].parent is None]
    if len(roots) != 1:
        raise ValueError("这份会话有 %d 个根（老格式？先跑迁移把它收成一棵"
                         "入口为根的树）：uv run python migrate_sessions.py"
                         % len(roots))
    root = roots[0]

    # 已投递账本：从各节点对话里的（id:…）标记重建（和调度器同一个来源）
    delivered = {nid: result_ids(p.get("msgs", []))
                 for nid, p in states.items()}
    state = {nid: {"node": registry[nid], "msgs": p.get("msgs", [])}
             for nid, p in states.items()}
    pending = deque(nid for nid in states
                    if reconcile.actionable(registry[nid], state[nid]["msgs"],
                                            delivered.get(nid, set())))
    return {"root": root, "registry": registry, "state": state, "pending": pending}
