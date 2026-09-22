"""一棵树的运行时存储：内存账本 + 它自己的记录文件。

调度器只看见 Node：该不该跑由 `reconcile.actionable` 回答、孩子结论由
`reconcile.settle` 结算 —— 这里管"节点账本建在哪、怎么落盘"（transcript /
registry / 已投递 / 检查点），不碰谁先谁后、并行几个。

会话的记录只有一份：checkpoint、出生 open、运行事件（usage / tool / effects…）
都写进同一份 append-only 文件（tree["trace"] 指向的路径）。`Trace` 是这份
存储的磁盘 IO 实现（写线程 + 文件），不是另一个"会话存储"概念 —— 要写记录
一律走 `TreeStore.record`，外面不另拿一个 trace 句柄。

检查点就是全部状态：Node 全字段 + 平铺对话。没有编排字段 —— 编排由
`reconcile` 从这两样推导。对话**增量落盘**（§11）：每节点第一笔写全量 msgs，
其余只写「自上次检查点以来新增的消息」（delta + base），恢复端（session.load）
按序拼回全量；node 字段小，每笔全量。恢复重开时 ckpt_base 从空起，第一笔自然全量。
"""

import os

from ..prompts import render_turn
from ..prompts.messages import result_ids
from .loop import Transcript
from .trace import Trace
from . import reconcile
from .turn import which_of


class TreeStore:
    """一棵树（会话）的运行时存储：内存账本 + 记录文件。

    state[nid] = {"node", "transcript", "seen_actions"}；registry 是 tree 的那份
    （就地登记，调用方拿着 tree 看得见整棵树长出来）；delivered 是已投递结果的
    孩子 id 集合（运行时维护；恢复时从对话里的（id:…）标记重建）。
    记录文件在构造时按 tree["trace"] 打开 —— 全会话共用一份。

    新会话：构造后账本为空，根由 `register` 建。
    恢复：构造时按 `tree["state"]` 重建（检查点已拼回全量 + delivered 重建）。
    """

    def __init__(self, tree):
        self.registry = tree["registry"]
        self.trace = Trace(tree["trace"])   # 会话的记录文件（磁盘 IO）
        self.state = {}          # nid -> {"node", "transcript", "seen_actions"}
        self.delivered = {}      # nid -> 已投递结果的孩子 id 集合
        self.ckpt_base = {}      # nid -> 上次检查点的消息起点（增量检查点的 base）
        self._workspace = os.path.abspath(os.getcwd())
        for nid, p in tree["state"].items():
            node = p["node"]
            self.state[nid] = self._state_for(node, p.get("msgs", []))
            self.registry[nid] = node
        for nid, st in self.state.items():
            self.delivered[nid] = result_ids(st["transcript"].to_list())

    def record(self, nid, kind, payload):
        """往会话记录里追加一笔事实（运行事件：usage / tool / effects…）。"""
        self.trace.add(nid, kind, payload)

    def drain(self):
        """等这一刻之前进队的记录全部落盘（任何退出路都要调）。"""
        self.trace.drain()

    def _state_for(self, node, msgs=None):
        return {"node": node,
                "transcript": Transcript(system=render_turn(which_of(node), node),
                                         msgs=msgs if msgs is not None else []),
                "seen_actions": {}}

    def register(self, node):
        """节点出生：建账本、进登记册、发 open 事件、落一笔检查点。"""
        st = self._state_for(node)
        self.state[node.id] = st
        self.delivered.setdefault(node.id, set())
        self.registry[node.id] = node
        self.record(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "conc_range": node.conc_range, "workspace": self._workspace})
        self.checkpoint(node.id, st)
        return node

    def seed(self, nid, text):
        """给节点的对话注一条 user 消息并落一笔检查点（新会话入口的第一句话）。"""
        st = self.state[nid]
        st["transcript"].add_user(text)
        self.checkpoint(nid, st)

    def checkpoint(self, nid, st):
        """把节点状态写进会话记录（增量，§11）。"""
        msgs, is_delta, base = st["transcript"].checkpoint(self.ckpt_base.get(nid, 0))
        self.ckpt_base[nid] = base + len(msgs)
        payload = {"node": st["node"].to_dict(), "msgs": msgs}
        if is_delta:
            payload["delta"] = True
            payload["base"] = base
        self.record(nid, "state", payload)

    def settle(self, pid, child, spawn):
        """把孩子的结论结算进父节点（投递 + 门槛），落一笔父检查点。

        spawn(specs) 由调度器给：门槛通过后把暂缓规格变成孩子（出生 + 排队）。
        返回 (父节点是否该重新排队, 父节点)。
        """
        pst = self.state[pid]
        parent = pst["node"]
        may_run = reconcile.settle(
            parent, child, self.delivered.setdefault(pid, set()), self.registry,
            inject=lambda text: pst["transcript"].add_user_merged(text),
            trace_add=self.record,
            spawn=spawn)
        self.checkpoint(pid, pst)
        return may_run, parent
