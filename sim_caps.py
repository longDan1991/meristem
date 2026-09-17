#!/usr/bin/env python3
"""量化"回路闭合"到底值多少钱 —— 在昨晚的真实 trace 上离线重演。

问题：caps 原本是手动灌的，正在跑的树学不到任何东西。
如果在线增量学习当时就生效，同一次运行里后面的节点能复用前面学到的吗？值多少？

做法：按时间顺序重演整份 trace。
  - 每遇到一个完工的节点，就把它成功执行过的命令学成 cap（和线上一样）
  - 每遇到一个 leaf_start，就拿该节点的任务当查询去检索（代理：真实查询是模型自己写的）
  - 命中就计一笔"本可复用"

零成本，不调模型。查询用节点任务当代理，所以结果是**下界或量级估计**，不是精确值。
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree.caps import Caps                            # noqa: E402
from tree.mine import caps_from_node                  # noqa: E402


def main():
    from tree import config as cfg
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        cfg.workspace(), "runs", "night_quant", "trace.jsonl")
    caps = Caps("/tmp/_sim.jsonl")                    # 空库起演
    status, tasks, calls = {}, {}, {}
    stats = Counter()
    first_hit_at = None

    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        k, nid = r["kind"], r["node"]
        p = r["payload"]

        if k == "open":
            tasks[nid] = p.get("task", "")
        elif k == "done":
            status[nid] = "done"
        elif k in ("failed", "budget_exhausted") and nid not in status:
            status[nid] = "failed"
        elif k == "leaf_tool":
            calls.setdefault(nid, []).append(
                (p.get("tool"), p.get("args") or {}, str(p.get("obs", ""))))
        elif k == "leaf_start":
            stats["叶子启动"] += 1
            q = tasks.get(nid, "")
            picked, _ = caps.search(q) if q else ([], "")
            if picked:
                stats["本可命中"] += 1
                stats["命中条目累计"] += len(picked)
                if first_hit_at is None:
                    first_hit_at = stats["叶子启动"]
        # 完工 → 立刻学（这就是线上闭环的那一步）
        if k == "done" and calls.get(nid):
            for e in caps_from_node(nid, tasks.get(nid, ""), calls[nid],
                                    os.path.basename(path)):
                caps.record(e)
                stats["学到能力"] += 1
            calls[nid] = []

    print("=" * 74)
    print("在 %s 上空转一遍在线闭环" % path)
    print("=" * 74)
    print("  叶子启动: %d" % stats["叶子启动"])
    print("  学到能力: %d 条（库最终 %d 条）" % (stats["学到能力"], len(caps.entries)))
    print("  本可命中: %d 次（%.1f%%）"
          % (stats["本可命中"], 100 * stats["本可命中"] / max(stats["叶子启动"], 1)))
    if first_hit_at:
        print("  第一次命中出现在第 %d 个叶子" % first_hit_at)
    print()
    print("  参照：库里最终只有 %d 条，而昨晚的叶子启动了 %d 次 ——"
          % (len(caps.entries), stats["叶子启动"]))
    print("  说明昨晚反复从头做同一件事的空间有多大。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
