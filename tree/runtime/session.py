"""会话的恢复：把 trace（统一会话记录）读回**一棵树**接着跑。

`trace.jsonl` 是一场会话的**完整记录**，几类事件按时间顺序混排在同一份
append-only 文件里：

  - 节点生命周期（open / concluded / …）—— 给人看的；
  - `state` 检查点 —— 调度器每次状态一变写一笔（`scheduler._checkpoint`），
    恢复时每个节点按序把**增量检查点**拼回全量（第一笔全量，之后只带新增消息）。
    检查点就是全部状态：Node 全字段 + 平铺对话（`msgs`），没有编排字段 ——
    编排由 `runtime/reconcile.py` 从这两样推导。

**一场会话 = 一棵树**：入口节点（kind="intake"）是根，谈成的任务都是它的
孩子。`load` 读回来的就是这棵树（root / registry / state），
直接丢给 `scheduler.run(..., resume=tree)` 就能接着跑。

恢复只认 `state`：节点生命周期那些事件是给别的消费者看的，重建运行状态不靠
它们（靠展示物猜事实会猜错）。

`load` 只做反序列化 + 树分组；补投递（崩溃窗口）与重排队列（该不该调 LLM）
由调度器 resume 时用 `reconcile` 做 —— 不在这里重写一遍编排。
"""

import os
import time

from ..protocol.fields import Node
from .trace import iter_trace_lines


def session_label(path):
    """一场会话的一行摘要（时间 + 最新任务 + 判定）。给 `-r` 的列表用。

    从 state 检查点推导（和 `load` 同一个来源，不认生命周期事件词表）：
      · 当前格式：入口节点（kind="intake"）是根，任务 = 入口的孩子；
      · 档案会话（入口并入根之前的数据，工作区里还留着当只读档案）：
        没有入口，根本身就是任务 —— 只能当任务树续跑，没有对话。
    两种情况都从检查点里的 Node 字段读判定；事件词（open / concluded / done…）
    因版本而异，不参与摘要。

    标签只要 node 字段（找入口和它的孩子）—— `msgs` 是检查点里的大头，一行
    摘要不碰它（大 trace 只扫 node，不整份反序列化，AGENTS §11）。
    """
    nodes = {}                  # nid -> 最后一笔 state 的 node 字段
    for r in iter_trace_lines(path, kinds=("state",)):
        if r.get("kind") == "state":
            p = r.get("payload") or {}
            if p.get("node"):
                nodes[r.get("node")] = p["node"]
    mtime = os.path.getmtime(path)
    stamp = time.strftime("%m-%d %H:%M", time.localtime(mtime))
    if not nodes:
        return "%s （没有 state 检查点）" % stamp
    registry = {nid: Node.from_dict(d) for nid, d in nodes.items()}
    intake = next((n for n in registry.values() if n.kind == "intake"), None)
    if intake is not None:
        tasks = [registry[c] for c in intake.children if c in registry]
    else:
        # 档案：没有入口，单根就是任务
        tasks = [n for n in registry.values() if n.parent is None]
    if not tasks:
        return "%s （还没跑过任务）" % stamp
    latest = tasks[0]                    # 出生顺序第一个（和原实现一致）
    name = (latest.name or "(无任务名)")[:40]
    verdict = latest.verdict or "运行中"
    extra = "" if len(tasks) == 1 else "（共 %d 个任务）" % len(tasks)
    return "%s %s [%s]%s" % (stamp, name, verdict, extra)


def load(path):
    """读一场会话的记录，返回**一棵树**：{"root", "registry", "state"}。

    拿它直接进 `scheduler.run(tree["root"], ..., resume=tree)` 就能接着跑。

    state[nid] = {"node": Node, "msgs": [...]} —— 检查点原样，无编排字段；
    该不该调 LLM 由调度器 resume 时按共享谓词 `reconcile.actionable` 重排。
    没有 state 检查点、或没有唯一的入口根 → 当场报错（数据损坏 / 不是当前格式），
    让错误带着上下文炸出来，不静默给一棵半成品树。

    检查点是**增量**的（`scheduler._checkpoint`：delta 事件只带自上次以来新增的
    消息），这里按节点、按文件顺序把增量拼回全量；老格式（没有 delta 字段）
    是整份快照，直接当全量采纳 —— 老档案照常只读，不写兼容层。
    """
    states = {}                 # nid -> {node dict, msgs}（按文件顺序合并增量）
    for r in iter_trace_lines(path, kinds=("state",)):
        if r.get("kind") == "state":
            nid = r.get("node")
            p = r.get("payload") or {}
            cur = states.setdefault(nid, {"node": None, "msgs": []})
            if p.get("node"):
                cur["node"] = p["node"]
            if p.get("delta"):
                cur["msgs"] = cur["msgs"][: p.get("base", 0)] + (p.get("msgs") or [])
            else:
                cur["msgs"] = p.get("msgs") or []      # 全量 / 老格式

    if not states:
        raise ValueError("这份会话没有 state 检查点（数据损坏，或不是当前格式）")
    registry = {nid: Node.from_dict(st["node"]) for nid, st in states.items()}
    roots = [registry[nid] for nid in states if registry[nid].parent is None]
    if len(roots) != 1:
        raise ValueError("这份会话有 %d 个根 —— 当前格式一场会话必须是一棵"
                         "入口为根的树" % len(roots))
    root = roots[0]
    state = {nid: {"node": registry[nid], "msgs": st["msgs"]}
             for nid, st in states.items()}
    return {"root": root, "registry": registry, "state": state}
