"""叶子的手在运行时那一侧的壳：bash / write 串行执行。

`tools.py` 里的函数是无状态的（谁调都一样）；"同时只能有一个在动"是**运行时**
的纪律，不是工具的语义，所以壳在这里。

串行靠**单消费者队列**（AGENTS §9 的官方解法）：bash / write 走队列，
一个消费者 task 挨个执行；`read` 只读，不经过它，直接跑。
`bash` 是真异步（`asyncio.create_subprocess_shell`），`read`/`write` 是同步的
文件操作（几十微秒，不值得为它开协程）—— 消费者要认得出这两种，
否则同步返回值会被当成协程去 schedule，消费者当场死掉、后面排队的人永远等不到。

工具的异常用 **done-callback** 原样搬到调用方的 future 上：
不吞、也不让消费者的任务死掉（消费者死了，后面排队的就永远等不到）。
"""

import asyncio
import inspect

from ..tools import TOOLS

SERIAL = ("bash", "write")


def _deliver(fut, task):
    if fut.done():
        return                 # 调用方已经等不及走了
    if task.cancelled():
        fut.cancel()
    elif task.exception() is not None:
        fut.set_exception(task.exception())
    else:
        fut.set_result(task.result())


class Hands:
    def __init__(self):
        self._q = asyncio.Queue()
        self._worker = asyncio.ensure_future(self._serve())

    async def _serve(self):
        while True:
            tool, args, fut = await self._q.get()
            call = TOOLS[tool](**args)
            if not inspect.isawaitable(call):
                if not fut.done():           # 同步工具：直接交付
                    fut.set_result(call)
                continue
            task = asyncio.ensure_future(call)
            task.add_done_callback(
                lambda t, fut=fut: _deliver(fut, t))

    async def run(self, tool, args):
        if tool not in SERIAL:
            out = TOOLS[tool](**args)
            return await out if inspect.isawaitable(out) else out
        fut = asyncio.get_running_loop().create_future()
        await self._q.put((tool, args, fut))
        return await fut

    async def close(self):
        self._worker.cancel()
