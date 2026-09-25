"""命令行入口：解析参数 → 交给 `main` 的入口函数，是唯一可执行入口。

`main` 只做初始化与入口函数；这里只负责参数解析与启动调用，除 `main` 外不 import 任何项目模块。
"""

import argparse
import sys

import main


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--resume", action="store_true",
                    help="选一个老会话加载成当前会话：对话接着谈，没跑完的树接着跑")
    return ap.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    main.init()
    sys.exit(main.main(args))
