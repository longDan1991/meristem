#!/usr/bin/env python3
"""拿昨晚的真实 trace 离线回归：新规则如果当时生效，会拦掉多少。

不需要调模型，不用花钱。读 trace.jsonl 就行。
    python3 regress.py $TREE_WORKSPACE/runs/night_quant/trace.jsonl
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree.run import anchors, inherits          # noqa: E402


def load(path):
    nodes, done, misc = {}, set(), Counter()
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        k, p, nid = r["kind"], r["payload"], r["node"]
        if k == "open":
            nodes[nid] = {"crit": p.get("criteria", ""), "parent": p.get("parent"),
                          "depth": p.get("depth", 0), "kind": p.get("kind", "evidence"),
                          "task": p.get("task", "")}
        elif k == "done":
            done.add(nid)
        elif k == "leaf_result":
            if "回合上限" in str(p) or "未产出事实" in str(p):
                misc["叶子超时却被当成结果"] += 1
    return nodes, done, misc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--show", type=int, default=6)
    a = ap.parse_args()

    nodes, done, misc = load(a.trace)
    kids = defaultdict(list)
    for nid, n in nodes.items():
        if n["parent"]:
            kids[n["parent"]].append(nid)

    print("=" * 78)
    print("回归对象: %s   节点 %d" % (a.trace, len(nodes)))
    print("=" * 78)

    # ── 规则 ①：子判据必须继承父/根判据的可测物理量（kind 现在由代码推导，不再自报）
    claimed = checked_fail = 0
    samples = []
    for pid, cs in kids.items():
        for cid in cs:
            c = nodes[cid]
            claimed += 1
            if not inherits(nodes[pid]["crit"], c["crit"]):
                checked_fail += 1
                if len(samples) < a.show:
                    samples.append((nodes[pid]["crit"], c["crit"],
                                    sorted(anchors(nodes[pid]["crit"]))))

    print("\n① 子判据带不上锚点、会被判为 infra（不算证据）: %d / %d (%.1f%%)"
          % (checked_fail, claimed, 100 * checked_fail / max(claimed, 1)))
    print("   —— 这就是昨晚\"标成 evidence 就能绕过约束\"的实际规模：")
    for p, c, an in samples:
        print("      父判据锚点 %-28s 子判据: %s" % (an, c))

    # ── 规则 ②：降级之后，有多少父节点的拆分变成"全是 infra"从而会被拒
    reject_root = reject_second = 0
    for pid, cs in kids.items():
        ok = any(nodes[c]["kind"] == "evidence" and inherits(nodes[pid]["crit"], nodes[c]["crit"])
                 for c in cs)
        if ok:
            continue
        if nodes[pid]["depth"] == 0:
            reject_root += 1
        else:
            reject_second += 1
    print("\n② 降级后变成\"纯基础设施\"的拆分: %d 个" % (reject_root + reject_second))
    print("   根节点上会被直接拒掉（改为自己执行）: %d" % reject_root)
    print("   其它层第一次允许、第二次会被拒: %d" % reject_second)

    # ── 规则 ③：账本撒谎 —— 标签说 evidence，但子节点根本没完工
    lied = sum(1 for nid, n in nodes.items()
               if n["parent"] and n["kind"] == "evidence" and nid not in done)
    print("\n③ 账本撒谎: 被标成 [证据] 上传、实际从未完工的子节点: %d 个 (%.1f%%)"
          % (lied, 100 * lied / max(claimed, 1)))
    for k, v in misc.items():
        print("   %s: %d 次" % (k, v))

    # ── 结论：新规则下这棵树会长成什么样
    print("\n" + "=" * 78)
    print("昨晚实际: %d 个节点, 完工 %d, 最深 %d 层"
          % (len(nodes), len(done), max(n["depth"] for n in nodes.values())))
    if reject_root:
        print("新规则下: 根节点的那次拆分会被拒 → 根自己去执行 → 叶子无工具可做 →")
        print("          整个任务在 1 个节点内结论为 **阻塞/失败并带原因**，而不是 2433 个节点。")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
