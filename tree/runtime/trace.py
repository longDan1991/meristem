"""trace：append-only 的 jsonl，按 node id 索引。

这是"过程下沉"的落点，不是记忆机制。它由**一个写线程**独占文件，
调用方只往队列里投一行的字符串（无锁，AGENTS §9）。

序列化在**调用方**做：不能序列化的东西当场炸，不拖进写线程里丢。
写线程只碰文件 IO，失败会记下来，下一次 `drain()` 原样抛回去 ——
不静默吞掉（AGENTS §2）。
"""

import hashlib
import json
import os
import queue
import threading
import time
from glob import glob

from tree import config as cfg


def iter_trace_lines(path, kinds=None):
    """逐行**流式**读一份 trace（不整文件驻留，大文件也只占一行内存）。最后
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
            raise RuntimeError("trace 写线程已死（%s）：记录不再落盘" % self.path)
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


def get_trace(path=None):
    """新会话的 trace 路径：<工作区>/runs/<时间>-<任务哈希>/trace.jsonl。"""
    if not path:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"), _INTAKE_SLUG)
        path = os.path.join(cfg.WORKSPACE, "runs", slug, "trace.jsonl")
    return Trace(path)


def get_traces():
    """历史会话（最近的在前）。`-r` 从这里列老会话。"""
    return sorted(glob(os.path.join(cfg.WORKSPACE, "runs", "*", "trace.jsonl")),
                  key=os.path.getmtime, reverse=True)
