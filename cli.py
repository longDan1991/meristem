"""命令行：解析参数 → 交给终端会话。

`main.py` 只负责初始化（工作区 / API key / 记录根），参数与派发在这里。
"""

import argparse
import asyncio

from terminal.chat import run_session


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--resume", action="store_true",
                    help="选一个老会话加载成当前会话：对话接着谈，没跑完的树接着跑")
    return ap.parse_args(argv)


async def run(argv=None):
    return await run_session(parse_args(argv))


def main(argv=None):
    return asyncio.run(run(argv))
