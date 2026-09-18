"""叶子的手在运行时那一侧的壳：bash / write 串行执行。

`tools.py` 里的函数是无状态的（谁调都一样）；"同时只能有一个在动"是**运行时**
的纪律，不是工具的语义，所以壳在这里。

串行靠 `ThreadPoolExecutor(max_workers=1)` —— 一个消费者线程，消息传递，
没有锁（AGENTS §9）。`read` 只读，不经过它，直接跑。
异常由 future 原样带回调用方，不被吞掉。
"""

from concurrent.futures import ThreadPoolExecutor

from ..tools import TOOLS

SERIAL = ("bash", "write")


class Hands:
    def __init__(self):
        self._pool = ThreadPoolExecutor(max_workers=1)

    def run(self, tool, args):
        if tool not in SERIAL:
            return TOOLS[tool](**args)
        return self._pool.submit(TOOLS[tool], **args).result()

    def close(self):
        self._pool.shutdown()
