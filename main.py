#!/usr/bin/env python3
import argparse
import asyncio
import sys

from terminal.chat import run_session


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--resume", action="store_true",
                    help="选一个老会话加载成当前会话：对话接着谈，没跑完的树接着跑")
    return ap.parse_args(argv)


async def main(argv=None):
    a = parse_args(argv)
    return await run_session(a)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
