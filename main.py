"""程序入口：初始化（工作区 / API key / 记录根）后交给 `cli`。

跑之前要定下来的东西全在 `init()` 里：记录根（会话记录落哪，给 `store`）、
工作目录（agent 的 cwd，工具在这跑）、有没有真模型。这里是唯一初始化点。
"""

import os
import sys

from tree import config as cfg
from tree.runtime import store

import cli


def init():
    """程序开始时的初始化：所有需要在跑之前定下来的东西都在这。"""
    if not os.environ.get("TREE_API_KEY"):
        print("入口是一次对话：要真模型。在 .env / 环境变量里给 TREE_API_KEY",
              file=sys.stderr)
        raise SystemExit(2)
    ws = cfg.WORKSPACE
    os.makedirs(ws, exist_ok=True)
    os.chdir(ws)
    store.init(ws)


if __name__ == "__main__":
    init()
    sys.exit(cli.main())
