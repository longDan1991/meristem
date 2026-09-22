"""一场会话的存储：一个对象，一组接口，写入自动落盘。

会话 = 一棵树（入口节点为根，谈成的任务都是它的孩子）。存储把这场会话的
全部数据收在一个对象里：

  1. roots()                加载树根列表（-r：每场会话的 id + 一行摘要）
  2. load(session)/new(...) 加载 / 新建一棵树 → Store
  3. node(nid)              根据 id 搜索一个节点
  4. put(nodes, on_id)      外界传一组完整 Node 挂到 on_id 下：
                            自动新增 / 更新内存并落盘（open + 状态检查点）

记录根（记录落哪）在**程序开始时初始化**（`init`，main.py 调）—— 外面拿不到
也不需要传路径。落盘是自动的：write 先进内存缓冲，`pydash.throttle` 按节奏
（最多每 `_THROTTLE_MS` 毫秒一次）懒写磁盘；读记录前和进程退出时自动补齐
（`_flush_live`）—— 调用方只管 record / put，不碰句柄、不手动 flush。

检查点就是全部状态：Node 全字段 + 平铺对话。没有编排字段 —— 编排由
`reconcile` 从这两样推导。对话**增量落盘**（§11）：每节点第一笔写全量 msgs，
其余只写「自上次检查点以来新增的消息」（delta + base），恢复端按序拼回全量；
node 字段小，每笔全量。
"""

import atexit
import hashlib
import json
import os
import time
from glob import glob

import pydash

from tree import config as cfg

from ..prompts import render_turn
from ..prompts.messages import result_ids
from ..protocol.fields import Node
from .loop import Transcript
from .turn import which_of

# 新会话目录的任务名恒为 intake（入口会话），哈希是常量 —— 没有 task 参数。
_INTAKE_SLUG = hashlib.sha1(b"intake").hexdigest()[:6]

# 记录根：所有会话的记录都落它下面。程序开始时 init() 定（默认取配置里的工作区）。
_ROOT = cfg.WORKSPACE

# 懒写节奏：记录最多每这么久落一次盘（毫秒）。write 先进缓冲，节流触发才写磁盘。
_THROTTLE_MS = 200


def init(root=None):
    """程序开始时的初始化：记录根定在这（默认配置里的工作区）。"""
    global _ROOT
    _ROOT = root or cfg.WORKSPACE


def _runs_dir():
    return os.path.join(_ROOT, "runs")


def _new_path():
    """新会话的记录路径：<记录根>/runs/<时间>-<任务哈希>/trace.jsonl。"""
    slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"), _INTAKE_SLUG)
    return os.path.join(_runs_dir(), slug, "trace.jsonl")


# 还开着的记录文件：读记录前 / 进程退出时统一把缓冲落盘（保证读到全量、退出不丢）。
_LIVE = []


def _flush_live():
    for rf in list(_LIVE):
        rf.flush()


atexit.register(_flush_live)


class _RecordFile:
    """会话记录的磁盘 IO：内存缓冲 + 节流懒写（pydash.throttle，成熟的节流实现）。

    外界只管 add()：记录先进缓冲，节流（最多每 `_THROTTLE_MS` 毫秒一次）把缓冲
    落盘。读记录前（`_flush_live`）和进程退出时补齐 —— 调用方不需要自己 flush。
    """

    def __init__(self, path):
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self._buf = []
        self._flush_now = pydash.throttle(self.flush, _THROTTLE_MS)
        _LIVE.append(self)

    def add(self, node_id, kind, payload):
        rec = {"t": round(time.time(), 3), "node": node_id, "kind": kind, "payload": payload}
        self._buf.append(json.dumps(rec, ensure_ascii=False) + "\n")
        self._flush_now()          # 节流：到了节奏点就把缓冲落盘

    def flush(self):
        """把缓冲落盘（节流到点 / 读记录前 / 退出时都会调；空缓冲是 no-op）。"""
        if not self._buf:
            return
        lines, self._buf = self._buf, []
        with open(self.path, "a", encoding="utf-8") as f:
            f.writelines(lines)


class Store:
    """一场会话的存储：一个对象。外界只走这几个接口（写入自动落盘）：

      · Store.roots()          加载树根列表（-r：会话 id + 一行摘要）
      · Store.load(session)    加载一棵树（session = roots() 给的会话 id）
      · Store.new(root, seed)  建一棵只含入口根的新树
      · store.node(nid)        根据 id 搜索一个节点（没登记过 → None）
      · store.put(nodes, on_id) 传一组完整 Node 挂到 on_id 下：
                               自动新增 / 更新内存并落盘
      · store.record(...)      运行事件（钩子发；落盘同上，自动）

    属性：root（入口）、registry（nid → Node，就地）、state（运行时账本，
    nid → {"node", "transcript", "seen_actions"}）、delivered（nid → 已投递
    结果的孩子 id 集合）、seed（新会话入口的第一句话）、path（记录落在哪）。
    """

    # ─────────────────────────────────────────── 1. 树根列表
    @staticmethod
    def roots():
        """加载树根列表：[(会话 id, 一行摘要), ...]，最近的在前（`-r` 用）。

        会话 id 是那棵树的根节点 id —— 加载时用 `load(id)`。
        """
        _flush_live()
        out = []
        for path in Store._paths():
            states = Store._read(path)
            root = Store._root(states)
            if root is not None and root.parent is None:
                out.append((root.id, Store._label(states, path)))
        return out

    # ─────────────────────────────────────────── 2. 加载 / 新建一棵树
    @classmethod
    def load(cls, session):
        """加载一棵树：`session` 是 `Store.roots()` 给的会话 id（根节点 id）。

        没有该会话、没有 state 检查点、或没有唯一的入口根 → 当场报错（数据
        损坏 / 不是当前格式），让错误带着上下文炸出来，不静默给半成品树。
        """
        _flush_live()
        for path in cls._paths():
            states = cls._read(path)
            if cls._root_id(states) == session:
                return cls._build(path, states)
        raise ValueError("找不到会话 %r（记录根下没有这场会话）" % session)

    @classmethod
    def new(cls, root, seed=None):
        """建一棵只含入口根的新树：登记根（+ seed）→ Store。"""
        store = cls(_new_path(), root=root, seed=seed)
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

    # ─────────────────────────────────────────── 记录（运行事件）
    def record(self, nid, kind, payload):
        """往会话记录里追加一笔事实（运行事件：usage / tool / effects…）。"""
        self._file.add(nid, kind, payload)

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
        _flush_live()      # 读记录前先把还开着的缓冲落盘（保证读到全量）
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
        """一场会话的一行摘要（时间 + 最新任务 + 判定）。给 `-r` 的列表用。"""
        return Store._label(Store._read(path), path)

    @staticmethod
    def _paths():
        """记录根下全部会话的记录路径（最近的在前）。"""
        return sorted(glob(os.path.join(_runs_dir(), "*", "trace.jsonl")),
                      key=os.path.getmtime, reverse=True)

    # ─────────────────────────────────────────── 内部：读
    @staticmethod
    def _read(path):
        """一份记录 → {nid: {"node": dict, "msgs": [...]}}（增量按序拼回全量）。"""
        states = {}
        for r in Store.iter_lines(path, kinds=("state",)):
            nid = r.get("node")
            p = r.get("payload") or {}
            cur = states.setdefault(nid, {"node": None, "msgs": []})
            if p.get("node"):
                cur["node"] = p["node"]
            if p.get("delta"):
                cur["msgs"] = cur["msgs"][: p.get("base", 0)] + (p.get("msgs") or [])
            else:
                cur["msgs"] = p.get("msgs") or []      # 全量 / 老格式
        return states

    @staticmethod
    def _registry_of(states):
        return {nid: Node.from_dict(st["node"]) for nid, st in states.items()}

    @staticmethod
    def _root(states):
        """记录里唯一的根（parent 为空）。多根 / 无根 → None（调用方报错）。"""
        registry = Store._registry_of(states)
        roots = [n for n in registry.values() if n.parent is None]
        return roots[0] if len(roots) == 1 else None

    @staticmethod
    def _root_id(states):
        root = Store._root(states)
        return root.id if root is not None else None

    @classmethod
    def _build(cls, path, states):
        """检查点 → Store（增量拼全、registry、delivered 都建好）。"""
        if not states:
            raise ValueError("这份会话没有 state 检查点（数据损坏，或不是当前格式）")
        registry = cls._registry_of(states)
        roots = [n for n in registry.values() if n.parent is None]
        if len(roots) != 1:
            raise ValueError("这份会话的根不唯一（数据损坏，或不是入口为根的一棵树）")
        store = cls(path, root=roots[0])
        store.registry = registry
        for nid, st in states.items():
            store.state[nid] = store._state_for(store.registry[nid], st["msgs"])
        for nid, st in store.state.items():
            store.delivered[nid] = result_ids(st["transcript"].to_list())
        return store

    @staticmethod
    def _label(states, path):
        """从检查点的 node 字段算一行摘要（只扫 node，不碰 msgs 大头，§11）。"""
        mtime = os.path.getmtime(path)
        stamp = time.strftime("%m-%d %H:%M", time.localtime(mtime))
        registry = Store._registry_of(states)
        if not registry:
            return "%s （没有 state 检查点）" % stamp
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

    # ─────────────────────────────────────────── 内部：写
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
            "conc_range": node.conc_range,
            "workspace": os.path.abspath(os.getcwd())})

    def _checkpoint(self, nid, st):
        """把节点状态写进会话记录（增量，§11）。"""
        msgs, is_delta, base = st["transcript"].checkpoint(self._base.get(nid, 0))
        self._base[nid] = base + len(msgs)
        payload = {"node": st["node"].to_dict(), "msgs": msgs}
        if is_delta:
            payload["delta"] = True
            payload["base"] = base
        self.record(nid, "state", payload)
