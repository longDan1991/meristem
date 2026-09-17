#!/usr/bin/env python3
"""离线批量挖能力。提取逻辑在 tree/mine.py，在线增量也用它。

线上回路是闭合的（节点一完工就学），这个 CLI 是给两种情况用的：
  1. 崩溃 / 被 kill 之后补挖（昨晚就是这样，进程被 kill，没走到收尾）
  2. 想拿旧 trace 回填，或想看挖出了什么

    python3 mine.py $TREE_WORKSPACE/runs/night_quant/trace.jsonl --dry --show 8
    python3 mine.py $TREE_WORKSPACE/runs/night_quant/trace.jsonl --query "起一个本地服务"
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import config as cfg                        # noqa: E402
from tree.caps import Caps                            # noqa: E402
from tree.mine import mine_trace                      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--caps", default=cfg.caps_path(),
                    help="能力库（TREE_CAPS）。在工作区里，跨 session 复用")
    ap.add_argument("--dry", action="store_true", help="只看挖出什么，不写")
    ap.add_argument("--show", type=int, default=10)
    ap.add_argument("--query", help="挖完后拿一个查询试检索")
    a = ap.parse_args()

    entries = mine_trace(a.trace)
    print("从 %s 挖出 %d 条能力" % (a.trace, len(entries)))
    for e in entries[:a.show]:
        print("  - %s%s" % (e["does"], "  [本项目]" if e.get("scope") == "project" else ""))
        print("      做法: %s" % e["how"]["cmd"])
        print("      键: %s" % ", ".join(e["keys"]))

    caps = Caps("/tmp/_mine_dry.jsonl" if a.dry else a.caps)
    before = len(caps.entries)
    for e in entries:
        caps.record(e)
    if a.dry:
        print("\n（--dry，未写入 %s）" % a.caps)
    else:
        print("\n已写入 %s（%d -> %d 条）" % (a.caps, before, len(caps.entries)))
        print("库状态: %s" % caps.stats())

    if a.query:
        picked, text = caps.search(a.query)
        print("\n查询 %r 命中 %d 条（%d 字符）:" % (a.query, len(picked), len(text)))
        print(text or "  （没有命中）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
