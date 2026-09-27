"""一场会话的存储：一棵树 + 一份 append-only 记录，写入即账。

会话 = 一棵树（入口节点为根，谈成的任务都是它的孩子）；存储是树与记录的唯一写者，
工具、Loop 都只经它改树。写入方法是树的所有变更入口（`append_*` / `put`）。

落盘：先写内存缓冲、`pydash.throttle` 懒写磁盘；检查点 = Node 全字段 + 平铺对话，
对话增量落盘（第一笔全量，之后只写新增），恢复端按序拼回全量。

`dirty` 是 Loop 的活跃集来源，是易失的调度状态，不进检查点。
"""

import atexit
import json
import os
import time
import uuid
from glob import glob

import pydash

from core import config as cfg

from ..protocol.fields import INTAKE, is_task_root, node_from_dict, node_to_dict
from ..protocol.messages import base_user
from .dialogue import Dialogue

_ROOT = cfg.WORKSPACE

# 懒写节奏：记录最多每这么久落一次盘（毫秒）
_THROTTLE_MS = 200

# 流式读遇到末行 JSON 坏掉时的哨兵：说明是被截断的半行，停在这里。
_TRUNCATED = object()


def _sent_comm(msgs):
    """一份对话里有没有向对方发过 communicate（会话摘要的"已回报/运行中"判据）。"""
    return any(m.get("role") == "assistant" and m.get("tool_calls")
               and any((tc.get("function") or {}).get("name") == "communicate"
                       for tc in m["tool_calls"])
               for m in msgs)


def init(root=None):
    """记录根改到这（默认配置里的工作区）；测试用它把记录根指到临时目录。"""
    global _ROOT
    _ROOT = root or cfg.WORKSPACE


def _runs_dir():
    return os.path.join(_ROOT, "runs")


def _new_path():
    """新会话的记录路径：<记录根>/runs/<时间>-<随机>/trace.jsonl。

    新会话时还没有任务名（谈成什么要入口谈完才知道），所以目录名只带时间 + 一小段随机：
    同一秒里连开两场也不会撞进同一条记录。
    """
    slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"), uuid.uuid4().hex[:6])
    return os.path.join(_runs_dir(), slug, "trace.jsonl")


# 读记录前 / 进程退出时统一把缓冲落盘
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
            _states, registry, root = Store._open(path)
            if root is not None:
                out.append((root.id, Store._label(registry, _states, path)))
        return out

    # ─────────────────────────────────────────── 2. 加载 / 新建
    @classmethod
    def load(cls, session):
        """加载一棵树；找不到 / 没有 state 检查点 / 根不唯一都当场报错，不给半成品树。"""
        _flush_live()
        for path in cls._paths():
            states, registry, root = cls._open(path)
            if root is not None and root.id == session:
                return cls._build(path, states, registry)
        raise ValueError("找不到会话 %r（记录根下没有这场会话）" % session)

    @classmethod
    def new(cls, root, seed=None):
        """建一棵只含入口根的新树；入口根首条是 `seed`，非 intake 根首条是它的任务（`base_user`）。"""
        store = cls(_new_path(), root=root)
        store.put([root])
        if seed is not None:
            store.append_user(root.id, seed)
        elif root.kind != INTAKE:
            store.append_user(root.id, base_user(root))
        return store

    def __init__(self, path, root=None):
        self.path = path
        self.root = root
        self.registry = {}       # nid -> Node（就地）
        self.state = {}          # nid -> Dialogue（一个节点的全部历史）
        self.dirty = set()       # 易失：有变更、可能需要动作的节点
        self._file = _RecordFile(path)
        self._base = {}          # nid -> 上次检查点的消息起点（增量）

    # ─────────────────────────────────────────── 3. 读
    def dialogue(self, nid):
        return self.state[nid]

    def take_dirty(self):
        got, self.dirty = self.dirty, set()
        return got

    def record(self, nid, kind, payload):
        """往会话记录里追加一笔事实（运行事件：usage / tool…）。"""
        self._file.add(nid, kind, payload)

    # ─────────────────────────────────────────── 4. 写（树的所有变更入口）
    def put(self, nodes, on_id=None):
        """新增 / 更新一组完整 Node：登记、标脏、自动落盘；on_id 给了就一起落（它的 children 刚变过）。"""
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

    def append_assistant(self, nid, text, tool_calls, reasoning=""):
        ids = self.dialogue(nid).assistant(text, tool_calls, reasoning)
        self._after(nid)
        return ids

    def append_tool(self, nid, call_id, text):
        self.dialogue(nid).tool(call_id, text)
        self._after(nid)

    def append_user(self, nid, text, sender=None):
        """给节点追加一条 user 消息；`sender` = 发送者节点 id（沟通消息带，账本里才有的键）。"""
        m = {"role": "user", "content": text}
        if sender:
            m["from"] = sender
        self.dialogue(nid).msgs.append(m)
        self._after(nid)

    def append_feedback(self, nid, text):
        self.dialogue(nid).feedback(text)
        self._after(nid)

    def _after(self, nid):
        self._checkpoint(nid)
        self.dirty.add(nid)

    # ─────────────────────────────────────────── 读记录的辅助
    @staticmethod
    def iter_lines(path, kinds=None):
        """逐行流式读一份记录：跳过被截断的最后一行（崩溃不埋成果），其它位置坏行照样炸。

        流式读不知 EOF 在哪，用「后一行到达才解析前一行」的 lookahead。
        `kinds` 按**解析出来**的 kind 过滤：不在原始行上做字符串匹配 —— 那既会跟 json 的
        分隔符写法隐式耦合，也会把 payload 里恰好一样的键值当成记录类型。
        """
        _flush_live()
        want = frozenset(kinds) if kinds else None

        def parse(raw, tolerate_truncated):
            line = raw.strip()
            if not line:
                return None
            try:
                rec = json.loads(line)
            except ValueError:
                if tolerate_truncated:
                    return _TRUNCATED
                raise
            if want is not None and rec.get("kind") not in want:
                return None
            return rec

        with open(path, encoding="utf-8") as f:
            prev = None
            for raw in f:
                if prev is not None:
                    rec = parse(prev, False)
                    if rec is not None:
                        yield rec
                prev = raw
            if prev is not None:
                rec = parse(prev, True)
                if rec is not _TRUNCATED and rec is not None:
                    yield rec

    @staticmethod
    def _open(path):
        """一条记录 → (states, registry, 唯一根)；没有 / 根不唯一时 root=None。"""
        states = Store._read(path)
        registry = Store._registry_of(states)
        return states, registry, Store._root(registry)

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
        return {nid: node_from_dict(st["node"]) for nid, st in states.items()}

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
            store.state[nid] = Dialogue(st["msgs"])
        return store

    @staticmethod
    def _label(registry, states, path):
        mtime = os.path.getmtime(path)
        stamp = time.strftime("%m-%d %H:%M", time.localtime(mtime))
        if not registry:
            return "%s （没有 state 检查点）" % stamp
        tasks = [n for n in registry.values() if is_task_root(n, registry)]
        if not tasks:
            return "%s （还没跑过任务）" % stamp
        newest = tasks[-1]      # registry 按记录出现顺序 = 节点出生顺序，最后一个是最新谈成的任务
        name = newest.name or "(无任务名)"
        msgs = (states.get(newest.id) or {}).get("msgs") or []
        state = "已回报" if _sent_comm(msgs) else "运行中"
        extra = "" if len(tasks) == 1 else "（共 %d 个任务）" % len(tasks)
        return "%s %s [%s]%s" % (stamp, name, state, extra)

    # ─────────────────────────────────────────── 内部：写
    def _register(self, node):
        # 节点出生与首笔 state 检查点同一次 put 完成，出生事件不另立记录（state 已含全字段）。
        self.state[node.id] = Dialogue()
        self.registry[node.id] = node

    def _checkpoint(self, nid):
        """把节点状态写进会话记录（对话增量）。"""
        msgs = self.state[nid].to_list()
        base = self._base.get(nid, 0)
        if base == 0 or len(msgs) < base:
            # 第一笔 / 恢复重开：全量
            self._base[nid] = len(msgs)
            self.record(nid, "state",
                        {"node": node_to_dict(self.registry[nid]), "msgs": msgs})
            return
        delta = msgs[base:]
        self._base[nid] = base + len(delta)
        self.record(nid, "state", {"node": node_to_dict(self.registry[nid]),
                                    "msgs": delta, "delta": True, "base": base})
