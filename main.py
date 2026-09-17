#!/usr/bin/env python3
"""最小载体：一棵递归工作的 LLM 树。

    python3 main.py "帮我做一个能赚大钱的A股量化系统" \
        -c "账户权益在2026-12-31收盘 >= 本金 x 2" --workers 6

路径全部来自配置文件（.env）：工作区在哪、能力库在哪、索引扫哪里。
跑出来的东西**一律落在工作区**（包括这次的 trace），项目目录里只有代码。
"""

import argparse
import glob
import hashlib
import os
import sys
import threading
import time

from tree import config as cfg
from tree.caps import Caps
from tree.index import TreeIndex
from tree.llm import LLM, MockLLM
from tree.node import Budget, Node, Trace
from tree.run import render_tree, run


def main():
    cfg.load_env()
    ws = cfg.workspace()
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default="给我一个能赚大钱的A股量化系统")
    ap.add_argument("--criteria", "-c", default="期末账户权益 >= 本金 x 2",
                    help="根任务的验收标准（必须可被观测）")
    ap.add_argument("--workers", type=int, default=6, help="并发节点数")
    ap.add_argument("--max-nodes", type=int, default=0, help="0=不限")
    ap.add_argument("--max-tokens", type=int, default=0, help="0=不限")
    ap.add_argument("--max-hours", type=float, default=0, help="0=不限")
    ap.add_argument("--trace", default=None,
                    help="默认 <工作区>/runs/<时间>-<任务>/trace.jsonl")
    ap.add_argument("--caps", default=cfg.caps_path(),
                    help="能力库（TREE_CAPS）。放工作区里，所以跨 session 复用")
    ap.add_argument("--workspace", "-w", default=ws,
                    help="持久工作目录（TREE_WORKSPACE）。同一个任务族共用它"
                         "，上次写的代码和数据就还在")
    ap.add_argument("--index", default=cfg.index_glob(),
                    help="要索引的老树（TREE_INDEX）。执行树就是成果树")
    ap.add_argument("--progress", type=int, default=60, help="每多少秒打一行进度，0=关闭")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-depth", type=int, default=2)
    a = ap.parse_args()
    if not a.trace:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"),
                          hashlib.sha1(a.task.encode("utf-8")).hexdigest()[:6])
        a.trace = os.path.join(a.workspace, "runs", slug, "trace.jsonl")

    if a.mock or not os.environ.get("TREE_API_KEY"):
        llm = MockLLM(max_depth=a.mock_depth)
        print("[mock 模式] 未检测到 TREE_API_KEY\n", flush=True)
    else:
        llm = LLM()
        print("[模型] %s @ %s" % (llm.model, llm.base_url), flush=True)

    trace = Trace(a.trace)
    root = Node(name=a.task, accept=a.criteria, kind="dispatch")
    registry = {}
    budget = Budget(max_nodes=a.max_nodes or None, max_tokens=a.max_tokens or None,
                    max_hours=a.max_hours or None)

    print("[验收标准] %s" % a.criteria, flush=True)
    print("[限制] 无。轮次/深度/节点/token/时间 全部不限，停止交给 API 自己", flush=True)
    print("[并发] %d" % a.workers, flush=True)
    # 持久工作目录：同一个任务族共用，上次写的代码和数据就还在
    ws = os.path.abspath(a.workspace)
    os.makedirs(ws, exist_ok=True)
    os.chdir(ws)
    print("[工作目录] %s  (TREE_WORKSPACE)" % ws, flush=True)

    # 老树索引：把所有历史 trace 当成成果树
    traces = sorted(glob.glob(a.index))
    index = TreeIndex(traces, exclude=[os.path.abspath(a.trace)])
    print("[索引] %d 棵老树，%d 个节点 %s"
          % (len(index.trees), index.stats["节点"],
             dict((k, v) for k, v in index.stats.items() if k != "节点")), flush=True)

    print("[trace] %s\n" % os.path.abspath(a.trace), flush=True)
    caps = Caps(a.caps)
    print("[能力库] %s  %s" % (a.caps, caps.stats()), flush=True)

    stop = threading.Event()

    def beat():
        while not stop.wait(a.progress):
            s = budget.stats()
            st = {}
            for n in registry.values():
                st[n.status] = st.get(n.status, 0) + 1
            print("[%s] 节点 %d (%.2f 分钟, %d tokens) 状态 %s"
                  % (time.strftime("%H:%M:%S"), s["nodes"], s["minutes"],
                     s["tokens"], st), flush=True)

    if a.progress > 0:
        threading.Thread(target=beat, daemon=True).start()

    t0 = time.time()
    run(root, llm, trace, registry=registry, budget=budget,
        workers=a.workers, caps=caps, index=index)
    stop.set()

    print("\n" + "=" * 78)
    print("结束: %.1f 分钟   %s" % ((time.time() - t0) / 60,
                                  __import__("json").dumps(budget.stats())))
    print("=" * 78)
    pass
    print("\n".join(render_tree(root, registry)))
    print("节点数: %d   trace: %s" % (len(registry), a.trace))
    return 0 if root.status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
