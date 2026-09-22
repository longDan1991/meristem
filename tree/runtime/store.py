"""一场会话 = 一棵树 + 它自己的记录：全部数据与存储都在这一个文件。

树的形状 {"root", "state", "registry", "trace", "seed"} 由两头构造：
`new_session(root)` 建一棵只含入口根的新树，`load(path)` 从记录读回一棵，
`session_label(path)` 给 `-r` 列表一行摘要 —— 都直接丢给 `scheduler.run(tree)` 跑。

`tree["trace"]` 是记录文件的路径；记录只有一份（checkpoint / 出生 open /
运行事件 usage、tool、effects…），`TreeStore` 是运行时存储（内存账本 + 记录入口），
`Trace` 是记录文件的磁盘 IO（append-only 的 jsonl，一个写线程），
`iter_trace_lines` / `trace_path` / `get_traces` 是这份记录的读 / 路径 / 列表。

调度器只看见 Node：该不该跑由 `reconcile.actionable` 回答、孩子结论由
`reconcile.settle` 结算 —— 节点账本建在哪、怎么落盘，都是这里的事，不碰谁先谁后。

`Trace` 由**一个写线程**独占文件，调用方只往队列里投一行的字符串（无锁，
AGENTS §9）。序列化在**调用方**做：不能序列化的东西当场炸，不拖进写线程里丢。
写线程只碰文件 IO，失败会记下来，下一次 `drain()` 原样抛回去 —— 不静默吞掉
（AGENTS §2）。

检查点就是全部状态：Node 全字段 + 平铺对话。没有编排字段 —— 编排由
`reconcile` 从这两样推导。对话**增量落盘**（§11）：每节点第一笔写全量 msgs，
其余只写「自上次检查点以来新增的消息」（delta + base），恢复端（load）按序
拼回全量；node 字段小，每笔全量。恢复重开时 ckpt_base 从空起，第一笔自然全量。
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
from . import reconcile
from .turn import which_of


# ---------------------------------------------------------------- 会话的两头构造
def new_session(root, seed=None, trace=None):
    """建一棵只含入口根的新树 —— `scheduler.run` 的新会话输入。

    与 `load` 同一个形状 {"root", "state", "registry", "trace", "seed"}：
    树自己知道记录落在哪（trace = 路径），新会话不传 trace 就从工作区生成；
    seed 是新会话入口的第一句话（恢复的树没有）。
    """
    return {"root": root, "state": {}, "registry": {},
            "trace": trace_path(trace), "seed": seed}


def load(path):
    """读一场会话的记录，返回**一棵树**：{"root", "registry", "state"}。

    拿它直接进 `scheduler.run(tree)` 就能接着跑。

    state[nid] = {"node": Node, "msgs": [...]} —— 检查点原样，无编排字段；
    该不该调 LLM 由调度器恢复时按共享谓词 `reconcile.actionable` 重排。
    没有 state 检查点、或没有唯一的入口根 → 当场报错（数据损坏 / 不是当前格式），
    让错误带着上下文炸出来，不静默给一棵半成品树。

    检查点是**增量**的（`store.checkpoint`：delta 事件只带自上次以来新增的
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
    return {"root": root, "registry": registry, "state": state,
            "trace": path, "seed": None}


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


# ---------------------------------------------------------------- 记录文件
def iter_trace_lines(path, kinds=None):
    """逐行**流式**读一份记录（不整文件驻留，大文件也只占一行内存）。最后
    一行若是被截断的半笔（崩溃时写了一半），跳过 —— 一次崩溃不该把整棵树的
    成果埋掉。其它位置坏行照样炸（那是真损坏）。

    流式读不知道 EOF 在哪：用「后一行到达才解析前一行」的 lookahead 拿
    「哪一行是最后一行」，最后一行解析失败当半笔跳过，其余坏行当场炸。

    kinds：只要某种 kind（如 ("state",)）时传它 —— 行内先做子串预过滤，
    不是目标 kind 的行连 json.loads 都省掉。大档案里大头是非 state 行（tool
    观测 / 分配记录），这个预过滤把解析量降到只剩需要的检查点（§11）。
    预过滤只看 kind 标记，被滤掉的行（含坏行）不参与解析，也就不报错 ——
    「坏行照样炸」的承诺只对目标 kind 的行生效（读取方本来就只认它们）。
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


class Trace:
    """记录文件的磁盘 IO：append-only 的 jsonl，按 node id 索引，一个写线程。"""

    def __init__(self, path="trace.jsonl"):
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


# 新会话目录的任务名恒为 intake（入口会话），哈希是常量 —— 没有 task 参数。
_INTAKE_SLUG = hashlib.sha1(b"intake").hexdigest()[:6]


def trace_path(path=None):
    """一场会话的记录路径：给了就是它（恢复 / 测试钉住），不给自己生成（新会话）。

    路径是"这棵树（会话）的记录在哪"——树带着它（{"trace"} 字段），
    存储构造时按它打开记录，路径本身不是 run 的入参。
    新会话路径：<工作区>/runs/<时间>-<任务哈希>/trace.jsonl。
    """
    if not path:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"), _INTAKE_SLUG)
        path = os.path.join(cfg.WORKSPACE, "runs", slug, "trace.jsonl")
    return path


def get_traces():
    """历史会话的记录文件（最近的在前）。`-r` 从这里列老会话。"""
    return sorted(glob(os.path.join(cfg.WORKSPACE, "runs", "*", "trace.jsonl")),
                  key=os.path.getmtime, reverse=True)


# ---------------------------------------------------------------- 运行时存储
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
