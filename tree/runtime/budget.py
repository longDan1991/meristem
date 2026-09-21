"""预算：只记用掉了多少，给报告看；人给的上限在这里生效。

计数器由**一个账本线程**独占，调用方通过队列收发 —— 没有锁（AGENTS §9）。
默认全不限：默认跑的时候它是纯计数，不参与任何判断。
"""

import queue
import threading
import time


class Budget:
    def __init__(self, max_nodes=None, max_tokens=None, max_hours=None):
        self._max_nodes = max_nodes
        self._max_tokens = max_tokens
        self._max_seconds = max_hours * 3600 if max_hours else None
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        nodes = tokens = 0
        t0 = time.time()
        while True:
            op, arg, reply = self._q.get()
            if op == "take_nodes":
                ok = not (self._max_nodes is not None
                          and nodes + arg > self._max_nodes)
                if ok:
                    nodes += arg
                reply.put(ok)
            elif op == "add_tokens":
                tokens += arg
                reply.put(None)
            else:                                   # snapshot
                reply.put((nodes, tokens, time.time() - t0))

    def _call(self, op, arg=None):
        if not self._thread.is_alive():
            raise RuntimeError("预算线程已死：后续预算操作不再安全")
        reply = queue.Queue()
        self._q.put((op, arg, reply))
        try:
            return reply.get(timeout=60)
        except queue.Empty:
            raise RuntimeError("预算线程没有响应")

    def take_nodes(self, n):
        return self._call("take_nodes", n)

    def add_tokens(self, n):
        self._call("add_tokens", n)

    def exhausted(self):
        nodes, tokens, secs = self._call("snapshot")
        return ((self._max_nodes is not None and nodes >= self._max_nodes)
                or (self._max_tokens is not None and tokens >= self._max_tokens)
                or (self._max_seconds is not None and secs >= self._max_seconds))

    def why(self):
        nodes, tokens, secs = self._call("snapshot")
        return "节点 %d, token %d, %.1f 分钟" % (nodes, tokens, secs / 60)

    def stats(self):
        nodes, tokens, secs = self._call("snapshot")
        return {"nodes": nodes, "tokens": tokens,
                "minutes": round(secs / 60, 1)}
