"""一场会话的存储：一棵树 + 一份 append-only 记录，写入即账。

会话 = 一棵树（入口节点为根，谈成的任务都是它的孩子）。存储把这场会话的全部
数据收在一个对象里，并且是**树与记录的唯一写者** —— 工具、Loop 都只经它改树。

接口：
  · `Store.roots()`          加载树根列表（-r：会话 id + 一行摘要）
  · `Store.load(session)`    加载一棵树（session = roots() 给的会话 id）
  · `Store.new(root, seed)`  建一棵只含入口根的新树
  · `store.node(nid)`        按 id 取一个节点
  · `store.dialogue(nid)`    某节点的平铺对话
  · `store.put(nodes, on_id)` 新增 / 更新一组节点（自动落盘 + 标脏）
  · 那一组写入方法（append_* / set_verdict / put）是树的所有变更入口

结论的完整语义（扫父节点、回填结果、门槛续跑/作废）是 `conclude` 工具的职责，
Store 只提供它用的基本写入口。

落盘：写入先进内存缓冲，`pydash.throttle` 按节奏懒写磁盘；读记录前和进程退出时
自动补齐。检查点就是全部状态：Node 全字段 + 平铺对话；对话**增量落盘**（第一笔
全量，之后只写自上次以来新增的消息），恢复端按序拼回全量。

`dirty` 是 Loop 的活跃集来源：任何写都标脏，Loop 每轮 `take_dirty()` 取走 ——
它是易失的调度状态，不进检查点。
"""

import atexit
import hashlib
import json
import os
import time
from glob import glob

import pydash

from core import config as cfg

from ..protocol.fields import Node
from ..prompts.messages import base_user
from .dialogue import Dialogue

# 新会话目录的任务名恒为 intake（入口会话），哈希是常量。
_INTAKE_SLUG = hashlib.sha1(b"intake").hexdigest()[:6]

# 记录根：所有会话的记录都落它下面。程序开始时 init() 定（默认取配置里的工作区）。
_ROOT = cfg.WORKSPACE

# 懒写节奏：记录最多每这么久落一次盘（毫秒）。
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


# 还开着的记录文件：读记录前 / 进程退出时统一把缓冲落盘。
_LIVE = []


def _flush_live():
    for rf in list(_LIVE):
        rf.flush()


atexit.register(_flush_live)


class _RecordFile:
    """会话记录的磁盘 IO：内存缓冲 + 节流懒写（pydash.throttle）。"""

    def __init__(self, path):
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self._buf = []
        self._flush_now = pydash.throttle(self.flush, _THROTTLE_MS)
        _LIVE.append(self)

    def add(self, node_id, kind, payload):
        rec = {"t": round(time.time(), 3), "node": node_id,
               "kind": kind, "payload": payload}
        self._buf.append(json.dumps(rec, ensure_ascii=False) + "\n")
        self._flush_now()

    def flush(self):
        if not self._buf:
            return
        lines, self._buf = self._buf, []
        with open(self.path, "a", encoding="utf-8") as f:
            f.writelines(lines)


class Store:
    """一场会话的存储。写入自动落盘；`dirty` 是 Loop 的活跃集来源。"""

    # ─────────────────────────────────────────── 1. 树根列表
    @staticmethod
    def roots():
        """加载树根列表：[(会话 id, 一行摘要), ...]，最近的在前。"""
        _flush_live()
        out = []
        for path in Store._paths():
            registry = Store._registry_of(Store._read(path))
            root = Store._root(registry)
            if root is not None:
                out.append((root.id, Store._label(registry, path)))
        return out

    # ─────────────────────────────────────────── 2. 加载 / 新建
    @classmethod
    def load(cls, session):
        """加载一棵树：`session` 是 `Store.roots()` 给的会话 id（根节点 id）。

        没有该会话、没有 state 检查点、或根不唯一 → 当场报错，不静默给半成品树。
        """
        _flush_live()
        for path in cls._paths():
            states = cls._read(path)
            registry = cls._registry_of(states)
            root = cls._root(registry)
            if root is not None and root.id == session:
                return cls._build(path, states, registry)
        raise ValueError("找不到会话 %r（记录根下没有这场会话）" % session)

    @classmethod
    def new(cls, root, seed=None):
        """建一棵只含入口根的新树。

        入口根的首条是 `seed`（用户说的话）；一个直接建的任务根（非 intake）
        首条是它的任务（`base_user`）—— 任务就在对话里，创建即拼进来。
        """
        store = cls(_new_path(), root=root)
        store.put([root])
        if seed is not None:
            store.append_user(root.id, seed)
        elif root.kind != "intake":
            store.append_user(root.id, base_user(root))
        return store

    def __init__(self, path, root=None):
        self.path = path
        self.root = root
        self.registry = {}       # nid -> Node（就地）
        self.state = {}          # nid -> {"dialogue"}
        self.dirty = set()       # 易失：有变更、可能需要动作的节点
        self._file = _RecordFile(path)
        self._base = {}          # nid -> 上次检查点的消息起点（增量）

    # ─────────────────────────────────────────── 3. 读
    def node(self, nid):
        return self.registry.get(nid)

    def dialogue(self, nid):
        return self.state[nid]["dialogue"]

    def take_dirty(self):
        got, self.dirty = self.dirty, set()
        return got

    def record(self, nid, kind, payload):
        """往会话记录里追加一笔事实（运行事件：usage / tool / effects…）。"""
        self._file.add(nid, kind, payload)

    # ─────────────────────────────────────────── 4. 写（树的所有变更入口）
    def put(self, nodes, on_id=None):
        """新增 / 更新一组完整 Node：登记、标脏、自动落盘。

        新增（id 没登记过）：建空对话、进登记册、发 open 事件。
        on_id 给了且在本会话里 → 它一起落（它的 children 刚变过）。
        """
        for node in nodes:
            if node.id not in self.state:
                self._register(node)
            else:
                self.registry[node.id] = node
            self._checkpoint(node.id)
            self.dirty.add(node.id)
        if on_id is not None and on_id in self.state:
            self._checkpoint(on_id)
            self.dirty.add(on_id)
        return nodes

    def append_assistant(self, nid, text, tool_calls):
        ids = self.dialogue(nid).assistant(text, tool_calls)
        self._after(nid)
        return ids

    def append_tool(self, nid, call_id, text):
        self.dialogue(nid).tool(call_id, text)
        self._after(nid)

    def append_user(self, nid, text):
        self.dialogue(nid).user(text)
        self._after(nid)

    def append_feedback(self, nid, text):
        self.dialogue(nid).feedback(text)
        self._after(nid)

    def set_verdict(self, nid, verdict, text, evidence, external=None):
        """落 verdict。结论的完整含义（扫父节点 / 回填结果 / 门槛）在 conclude 工具里。"""
        self.registry[nid].close(verdict, text, evidence, external)
        self._after(nid)

    def _after(self, nid):
        self._checkpoint(nid)
        self.dirty.add(nid)

    # ─────────────────────────────────────────── 读记录的辅助
    @staticmethod
    def iter_lines(path, kinds=None):
        """逐行**流式**读一份记录。最后一行若是被截断的半笔，跳过 —— 一次崩溃
        不该把整棵树的成果埋掉；其它位置坏行照样炸（那是真损坏）。

        流式读不知道 EOF 在哪：用「后一行到达才解析前一行」的 lookahead。
        """
        _flush_live()
        want = tuple('"kind": "%s"' % k for k in kinds) if kinds else ()
        with open(path, encoding="utf-8") as f:
            prev = None
            for raw in f:
                if prev is not None:
                    if not want or any(w in prev for w in want):
                        line = prev.strip()
                        if line:
                            yield json.loads(line)
                prev = raw
            if prev is not None:
                if not want or any(w in prev for w in want):
                    line = prev.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except ValueError:
                            return

    @staticmethod
    def label(path):
        return Store._label(Store._registry_of(Store._read(path)), path)

    @staticmethod
    def _paths():
        return sorted(glob(os.path.join(_runs_dir(), "*", "trace.jsonl")),
                      key=os.path.getmtime, reverse=True)

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
                cur["msgs"] = p.get("msgs") or []
        return states

    @staticmethod
    def _registry_of(states):
        return {nid: Node.from_dict(st["node"]) for nid, st in states.items()}

    @staticmethod
    def _root(registry):
        roots = [n for n in registry.values() if n.parent is None]
        return roots[0] if len(roots) == 1 else None

    @classmethod
    def _build(cls, path, states, registry):
        if not states:
            raise ValueError("这份会话没有 state 检查点（数据损坏，或不是当前格式）")
        root = cls._root(registry)
        if root is None:
            raise ValueError("这份会话的根不唯一（数据损坏，或不是入口为根的一棵树）")
        store = cls(path, root=root)
        store.registry = registry
        for nid, st in states.items():
            store.state[nid] = store._state_for(store.registry[nid], st["msgs"])
        return store

    @staticmethod
    def _label(registry, path):
        mtime = os.path.getmtime(path)
        stamp = time.strftime("%m-%d %H:%M", time.localtime(mtime))
        if not registry:
            return "%s （没有 state 检查点）" % stamp
        intake = next((n for n in registry.values() if n.kind == "intake"), None)
        if intake is not None:
            tasks = [registry[c] for c in intake.children if c in registry]
        else:
            tasks = [n for n in registry.values() if n.parent is None]
        if not tasks:
            return "%s （还没跑过任务）" % stamp
        latest = tasks[0]
        name = latest.name or "(无任务名)"
        verdict = latest.verdict or "运行中"
        extra = "" if len(tasks) == 1 else "（共 %d 个任务）" % len(tasks)
        return "%s %s [%s]%s" % (stamp, name, verdict, extra)

    # ─────────────────────────────────────────── 内部：写
    def _state_for(self, node, msgs=None):
        return {"dialogue": Dialogue(msgs if msgs is not None else [])}

    def _register(self, node):
        self.state[node.id] = self._state_for(node)
        self.registry[node.id] = node
        self.record(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "conc_range": node.conc_range,
            "workspace": os.path.abspath(os.getcwd())})

    def _checkpoint(self, nid):
        """把节点状态写进会话记录（对话增量，§11）。"""
        msgs = self.state[nid]["dialogue"].to_list()
        base = self._base.get(nid, 0)
        if base == 0 or len(msgs) < base:
            # 第一笔 / 恢复重开：全量
            self._base[nid] = len(msgs)
            self.record(nid, "state",
                        {"node": self.registry[nid].to_dict(), "msgs": msgs})
            return
        delta = msgs[base:]
        self._base[nid] = base + len(delta)
        self.record(nid, "state", {"node": self.registry[nid].to_dict(),
                                    "msgs": delta, "delta": True, "base": base})
