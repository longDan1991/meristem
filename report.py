#!/usr/bin/env python3
"""从 trace.jsonl 重建整棵树。进程挂了、被 kill 了、跑了一夜，都能重建。

    python3 report.py $TREE_WORKSPACE/runs/night_quant/trace.jsonl
    python3 report.py $TREE_WORKSPACE/runs/night_quant/trace.jsonl --leaves 40
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree.node import Node                       # noqa: E402
from tree.run import render_tree                 # noqa: E402


def rebuild(path):
    nodes, order = {}, []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue          # 最后一行可能是被 kill 时的半行
        k, p, nid = r["kind"], r["payload"], r["node"]
        if k == "open":
            nodes[nid] = Node(name=p.get("name") or p.get("任务名", ""),
                              accept=p.get("accept") or p.get("验收标准", ""),
                              detail=p.get("detail") or p.get("任务详情", ""),
                              notes=p.get("notes") or p.get("注意事项", ""),
                              kind=p.get("kind") or p.get("类型", "dispatch"),
                              gate=bool(p.get("gate") or p.get("门槛")), id=nid,
                              parent=p.get("parent"),
                              depth=p.get("depth", p.get("深度", 0)))
            order.append(nid)
        elif k == "concluded" and nid in nodes:
            nodes[nid].verdict = p.get("verdict") or p.get("判定", "")
            nodes[nid].conclusion = p.get("text") or p.get("内容", "")
            nodes[nid].evidence = p.get("evidence") or p.get("证据") or []
            nodes[nid].status = "done"
        elif k in ("failed", "budget_exhausted", "crashed") and nid in nodes:
            nodes[nid].status = "failed"
            if not nodes[nid].conclusion:
                nodes[nid].conclusion = str(p)
        elif k == "children" and nid in nodes:
            pass
    # 父子关系靠 parent 字段，不靠执行顺序
    for nid, n in nodes.items():
        if n.parent and n.parent in nodes:
            nodes[n.parent].children.append(nid)
    for n in nodes.values():
        if n.status == "running" and n.children:
            n.status = "running"
    return nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--leaves", type=int, default=25)
    ap.add_argument("--max-lines", type=int, default=300)
    a = ap.parse_args()

    nodes = rebuild(a.trace)
    if not nodes:
        print("trace 里没有节点")
        return 1
    roots = [n for n in nodes.values() if not n.parent or n.parent not in nodes]
    recs = [json.loads(l) for l in open(a.trace) if l.strip()]

    m = Counter()
    tokens = Counter()
    for r in recs:
        m[r["kind"]] += 1
        if r["kind"] == "usage":
            tokens["total"] += r["payload"].get("total", 0)
            tokens["reasoning"] += r["payload"].get("reasoning", 0)
            tokens["cached"] += r["payload"].get("cached", 0)

    depths = Counter(n.depth for n in nodes.values())
    kinds = Counter(n.kind for n in nodes.values())
    status = Counter(n.status for n in nodes.values())
    verdicts = Counter(n.verdict or "(未出结论)" for n in nodes.values())
    t0, t1 = recs[0]["t"], recs[-1]["t"]

    print("=" * 78)
    print("trace: %s" % a.trace)
    print("时长: %.1f 分钟   节点: %d   最长分支深度: %d"
          % ((t1 - t0) / 60, len(nodes), max(depths) if depths else 0))
    print("LLM 调用: %d   tokens: %d（推理 %d，缓存命中 %d）"
          % (m["decide_out"] + m["leaf_out"], tokens["total"],
             tokens["reasoning"], tokens["cached"]))
    print("状态: %s" % dict(status))
    print("结论: %s" % dict(verdicts))
    print("类型: %s" % dict(kinds))
    print("判据漂移: %d   字段超长(未切): %d   降级判定: %d   门槛不成立: %d   预算耗尽: %d   崩溃: %d"
          % (m["criterion_drift"], m["field_over"], m["verdict_downgraded"],
             m["gate_failed"], m["budget_exhausted"], m["crashed"]))
    print("契约: %d   缺契约被拦: %d   effects: %d   need 调用: %d（命中 %d）"
          "   学到能力: %d   复用记账: %d"
          % (m["contract"], m["contract_missing"], m["effects"], m["cap_need"],
             m["cap_outcome"], m["cap_learned"], m["cap_outcome"]))
    print("各层节点数: %s" % dict(sorted(depths.items())))
    print("=" * 78)

    for root in roots:
        print("\n".join(render_tree(root, nodes)[:a.max_lines]))

    # 叶子/结论清单：明早最想看的是它自己给出的判据
    print("\n" + "=" * 78)
    print("最深的一批节点（%d 个）—— 它把任务切到了哪里：" % a.leaves)
    deep = sorted(nodes.values(), key=lambda n: -n.depth)[:a.leaves]
    for n in deep:
        mark = {"done": "✓", "failed": "✗"}.get(n.status, "·")
        print("  %s d%-2d [%-6s] %s" % (mark, n.depth, n.kind, n.name))
        print("        验收标准: %s" % n.accept)
        if n.conclusion:
            print("        %s: %s" % (n.verdict or "-", str(n.conclusion)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
