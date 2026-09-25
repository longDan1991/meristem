"""入口函数：初始化（工作区 / API key / 记录根）后把参数派发给终端会话。

`cli` 是唯一可执行入口，它只 import 这里；本模块只做初始化与真正的启动。
"""

import asyncio
import os
import sys

from core import config as cfg

from terminal.chat import run_session


def init():
    """程序开始时的初始化：所有需要在跑之前定下来的东西都在这。"""
    if not os.environ.get("TREE_API_KEY"):
        print("入口是一次对话：要真模型。在 .env / 环境变量里给 TREE_API_KEY",
              file=sys.stderr)
        raise SystemExit(2)
    ws = cfg.WORKSPACE            # 记录根 = 工作区；store 模块默认就用它，不再另调 init
    os.makedirs(ws, exist_ok=True)
    os.chdir(ws)


def main(args):
    """入口函数：asyncio 事件循环里把已解析的参数派发给终端会话。"""
    return asyncio.run(run_session(args))
