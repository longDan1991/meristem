"""trace：append-only 的 jsonl，按 node id 索引。

这是"过程下沉"的落点，不是记忆机制。它由**一个写线程**独占文件，
调用方只往队列里投一行的字符串（无锁，AGENTS §9）。

序列化在**调用方**做：不能序列化的东西当场炸，不拖进写线程里丢。
写线程只碰文件 IO，失败会记下来，下一次 `drain()` 原样抛回去 ——
不静默吞掉（AGENTS §2）。
"""

import json
import os
import queue
import threading
import time


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
        rec = {"t": round(time.time(), 3), "node": node_id, "kind": kind,
               "payload": payload}
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
