"""一场会话的存储：一个对象，一组接口，写入自动落盘。

会话 = 一棵树（入口节点为根，谈成的任务都是它的孩子）。存储把这场会话的
全部数据收在一个对象里：

  1. roots()                加载树根列表（-r：每场会话的路径 + 一行摘要）
  2. load(path) / new(...)  加载 / 新建一棵树 → Store
  3. node(nid)              根据 id 搜索一个节点
  4. put(nodes, on_id)      外界传一组完整 Node 挂到 on_id 下：
                            自动新增 / 更新内存并落盘（open + 状态检查点）

记录文件（append-only jsonl + 一个写线程）、内存索引、增量检查点都是这个
对象自己的事 —— 外面不拿文件句柄、不手动落盘。record / drain 是写记录与
保证落盘的运行出口（钩子发运行事件、调度器收尾时用）。

检查点就是全部状态：Node 全字段 + 平铺对话。没有编排字段 —— 编排由
`reconcile` 从这两样推导。对话**增量落盘**（§11）：每节点第一笔写全量 msgs，
其余只写「自上次检查点以来新增的消息」（delta + base），恢复端按序拼回全量；
node 字段小，每笔全量。
"""

import hashlib
import json
import os
import queue
import threading
import time
from glob import glob

from tree import config as cfg

from ..prompts import render_turn
from ..prompts.messages import result_ids
from ..protocol.fields import Node
from .loop import Transcript
from .turn import which_of


# 新会话目录的任务名恒为 intake（入口会话），哈希是常量 —— 没有 task 参数。
_INTAKE_SLUG = hashlib.sha1(b"intake").hexdigest()[:6]


def _trace_path(path=None):
    """一场会话的记录路径：给了就是它（恢复 / 测试钉住），不给自己生成（新会话）。

    路径是"这棵树（会话）的记录在哪"——树带着它，存储构造时按它打开记录。
    新会话路径：<工作区>/runs/<时间>-<任务哈希>/trace.jsonl。
    """
    if not path:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"), _INTAKE_SLUG)
        path = os.path.join(cfg.WORKSPACE, "runs", slug, "trace.jsonl")
    return path


class _RecordFile:
    """记录文件的磁盘 IO：append-only 的 jsonl，按 node id 索引，一个写线程。

    调用方只往队列里投一行的字符串（无锁，AGENTS §9）。序列化在**调用方**
    做（Store.record）：不能序列化的东西当场炸，不拖进写线程里丢。写线程只碰
    文件 IO，失败会记下来，下一次 `drain()` 原样抛回去 —— 不静默吞掉（AGENTS §2）。
    """

    def __init__(self, path):
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self._q = queue.Queue()
        self._error = None
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def add(self, node_id, kind, payload):
        if not self._thread.is_alive():
            raise RuntimeError("记录写线程已死（%s）：不再落盘" % self.path)
        rec = {"t": round(time.time(), 3), "node": node_id, "kind": kind, "payload": payload}
        self._q.put(json.dumps(rec, ensure_ascii=False) + "\n")

    def _serve(self):
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                while True:
                    line = self._q.get()
                    try:
                        f.write(line)
                        f.flush()
                    except OSError as e:
                        if self._error is None:
                            self._error = e
                    finally:
                        self._q.task_done()
        except OSError as e:
            # 文件打不开：把队列排空，让 drain() 不挂死，然后把错误抛回去
            if self._error is None:
                self._error = e
            while True:
                self._q.get()
                self._q.task_done()

    def drain(self):
        """等这一刻之前进队的记录全部处理完（不是关掉它：入口会反复跑树）。"""
        self._q.join()
        if self._error is not None:
            raise self._error


class Store:
    """一场会话的存储：一个对象。外界只走这几个接口（写入自动落盘）：

      · Store.roots()          加载树根列表（-r：路径 + 一行摘要）
      · Store.load(path)       加载一棵树（记录 → 内存账本）
      · Store.new(root, seed)  建一棵只含入口根的新树
      · store.node(nid)        根据 id 搜索一个节点（没登记过 → None）
      · store.put(nodes, on_id) 传一组完整 Node 挂到 on_id 下：
                               自动新增 / 更新内存并落盘
      · store.record / drain   运行事件 / 保证落盘

    属性：root（入口）、registry（nid → Node，就地）、state（运行时账本，
    nid → {"node", "transcript", "seen_actions"}）、delivered（nid → 已投递
    结果的孩子 id 集合）、seed（新会话入口的第一句话）。
    """

    # ─────────────────────────────────────────── 1. 树根列表
    @staticmethod
    def roots():
        """加载树根列表：每场会话（记录路径 + 一行摘要），最近的在前（`-r` 用）。"""
        return [(p, Store.label(p)) for p in Store._paths()]

    # ─────────────────────────────────────────── 2. 加载 / 新建一棵树
    @classmethod
    def load(cls, path):
        """加载一棵树：记录（增量检查点按序拼回全量）→ Store。

        没有 state 检查点、或没有唯一的入口根 → 当场报错（数据损坏 / 不是当前
        格式），让错误带着上下文炸出来，不静默给一棵半成品树。
        """
        states = {}                 # nid -> {node dict, msgs}（按文件顺序合并增量）
        for r in cls.iter_lines(path, kinds=("state",)):
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
        store = cls(path, root=roots[0])
        store.registry = registry
        for nid, st in states.items():
            node = registry[nid]
            store.state[nid] = store._state_for(node, st["msgs"])
        for nid, st in store.state.items():
            store.delivered[nid] = result_ids(st["transcript"].to_list())
        return store

    @classmethod
    def new(cls, root, seed=None, trace=None):
        """建一棵只含入口根的新树：登记根（+ seed）→ Store。"""
        store = cls(_trace_path(trace), root=root, seed=seed)
        store._register(root)
        if seed is not None:
            store.state[root.id]["transcript"].add_user(seed)
        store._checkpoint(root.id, store.state[root.id])
        return store

    def __init__(self, path, root=None, seed=None):
        self.path = path
        self.root = root
        self.seed = seed
        self.registry = {}       # nid -> Node（就地，渲染 / 查找都看它）
        self.state = {}          # nid -> {"node", "transcript", "seen_actions"}
        self.delivered = {}      # nid -> 已投递结果的孩子 id 集合
        self._file = _RecordFile(path)
        self._base = {}          # nid -> 上次检查点的消息起点（增量）
        self._workspace = os.path.abspath(os.getcwd())

    # ─────────────────────────────────────────── 3. 按 id 搜索节点
    def node(self, nid):
        """根据 id 搜索一个节点（没登记过 → None）。"""
        return self.registry.get(nid)

    # ─────────────────────────────────────────── 4. 传一组完整 Node + 挂 ID
    def put(self, nodes, on_id=None):
        """外界传一组完整 Node 挂到 on_id 下：新增 / 更新内存并自动落盘。

        新增（id 没登记过）：建账本、进登记册、发 open 事件；
        更新（id 已登记）：节点字段以传入的为准。
        两者都自动落一笔检查点（node 全字段 + 对话自上次以来的增量）。
        on_id 给了且在本会话里 → 它一起落（它的 children 刚变过）。
        """
        for node in nodes:
            st = self.state.get(node.id)
            if st is None:
                self._register(node)
            else:
                st["node"] = node
                self.registry[node.id] = node
            self._checkpoint(node.id, self.state[node.id])
        if on_id is not None and on_id in self.state:
            self._checkpoint(on_id, self.state[on_id])
        return nodes

    # ─────────────────────────────────────────── 记录 / 落盘
    def record(self, nid, kind, payload):
        """往会话记录里追加一笔事实（运行事件：usage / tool / effects…）。"""
        self._file.add(nid, kind, payload)

    def drain(self):
        """等这一刻之前进队的记录全部落盘（任何退出路都要调）。"""
        self._file.drain()

    # ─────────────────────────────────────────── 读记录的辅助（roots / 测试）
    @staticmethod
    def iter_lines(path, kinds=None):
        """逐行**流式**读一份记录（不整文件驻留，大文件也只占一行内存）。最后
        一行若是被截断的半笔（崩溃时写了一半），跳过 —— 一次崩溃不该把整棵树
        的成果埋掉。其它位置坏行照样炸（那是真损坏）。

        流式读不知道 EOF 在哪：用「后一行到达才解析前一行」的 lookahead 拿
        「哪一行是最后一行」，最后一行解析失败当半笔跳过，其余坏行当场炸。

        kinds：只要某种 kind（如 ("state",)）时传它 —— 行内先做子串预过滤，
        不是目标 kind 的行连 json.loads 都省掉（大档案里大头是非 state 行）。
        """
        want = tuple('"kind": "%s"' % k for k in kinds) if kinds else ()
        with open(path, encoding="utf-8") as f:
            prev = None
            for raw in f:
                if prev is not None:
                    if not want or any(w in prev for w in want):
                        line = prev.strip()
                        if line:
                            yield json.loads(line)      # 非最后一行：坏行直接炸
                prev = raw
            if prev is not None:
                if not want or any(w in prev for w in want):
                    line = prev.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except ValueError:
                            return                      # 最后一行：崩溃残笔，跳过

    @staticmethod
    def label(path):
        """一场会话的一行摘要（时间 + 最新任务 + 判定）。给 `-r` 的列表用。

        从 state 检查点推导（和 `load` 同一个来源，不认生命周期事件词表）：
          · 当前格式：入口节点（kind="intake"）是根，任务 = 入口的孩子；
          · 档案会话（入口并入根之前的数据）：没有入口，根本身就是任务。
        标签只要 node 字段（找入口和它的孩子）—— msgs 是检查点里的大头，
        一行摘要不碰它（大 trace 只扫 node，AGENTS §11）。
        """
        nodes = {}                  # nid -> 最后一笔 state 的 node 字段
        for r in Store.iter_lines(path, kinds=("state",)):
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

    @staticmethod
    def _paths():
        """工作区里全部会话的记录路径（最近的在前）。"""
        return sorted(glob(os.path.join(cfg.WORKSPACE, "runs", "*", "trace.jsonl")),
                      key=os.path.getmtime, reverse=True)

    # ─────────────────────────────────────────── 内部
    def _state_for(self, node, msgs=None):
        return {"node": node,
                "transcript": Transcript(system=render_turn(which_of(node), node),
                                         msgs=msgs if msgs is not None else []),
                "seen_actions": {}}

    def _register(self, node):
        """节点出生：建账本、进登记册、发 open 事件（落盘由 put 统一做）。"""
        st = self._state_for(node)
        self.state[node.id] = st
        self.delivered[node.id] = set()
        self.registry[node.id] = node
        self.record(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "conc_range": node.conc_range, "workspace": self._workspace})

    def _checkpoint(self, nid, st):
        """把节点状态写进会话记录（增量，§11）。"""
        msgs, is_delta, base = st["transcript"].checkpoint(self._base.get(nid, 0))
        self._base[nid] = base + len(msgs)
        payload = {"node": st["node"].to_dict(), "msgs": msgs}
        if is_delta:
            payload["delta"] = True
            payload["base"] = base
        self.record(nid, "state", payload)
