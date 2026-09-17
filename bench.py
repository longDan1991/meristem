#!/usr/bin/env python3
"""跑一个任务，把可观测量写进 result.json。

这是自优化的眼睛：没有 trace 里的这些量，自优化就是瞎的。
它自己不判定"做对了没有" —— 那是 evolve.py 的 checker 干的，属于外部。
"""

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree.llm import LLM, MockLLM          # noqa: E402
from tree.node import Node, Trace          # noqa: E402
from tree.run import run                   # noqa: E402


def metrics(trace_path):
    m = {"calls": 0, "tokens": 0, "reasoning": 0, "nodes": 0,
         "violations": 0, "depth_caps": 0, "done_rejected": 0}
    if not os.path.exists(trace_path):
        return m
    for line in open(trace_path):
        r = json.loads(line)
        k, p = r["kind"], r["payload"]
        if k in ("decide_out", "leaf_out"):
            m["calls"] += 1
        elif k == "usage":
            m["tokens"] += p.get("total", 0)
            m["reasoning"] += p.get("reasoning", 0)
        elif k == "open":
            m["nodes"] += 1
        elif k == "invariant_violation":
            m["violations"] += 1
        elif k == "depth_cap":
            m["depth_caps"] += 1
        elif k == "done_rejected":
            m["done_rejected"] += 1
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--criteria", required=True)
    ap.add_argument("--trace", default="trace.jsonl")
    ap.add_argument("--out", default="result.json")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    rec = {"task": a.task, "criteria": a.criteria}
    try:
        llm = MockLLM() if a.mock else LLM()
        trace = Trace(a.trace)
        root = Node(name=a.task, accept=a.criteria, kind="dispatch")
        registry = {}
        run(root, llm, trace, registry=registry)
        rec.update({"status": root.status, "claimed": root.conclusion,
                    "verdict": root.verdict, "reason": ""})
    except Exception:
        rec.update({"status": "error", "claimed": None,
                    "reason": traceback.format_exc()})

    rec["seconds"] = round(time.time() - t0, 1)
    rec.update(metrics(a.trace))

    with open(a.out, "w") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
