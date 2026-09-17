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
from terminal.chat import converse


def main():
    cfg.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?",
                    help="要做的这件事（一句话）。不给就得靠 --intake 谈出来")
    ap.add_argument("--criteria", "-c",
                    help="根任务的验收标准（必须可被观测）。"
                         "这是唯一能判定整棵树做没做完的东西：不给就得靠 --intake 谈出来")
    ap.add_argument("--workers", type=int, default=6, help="并发节点数")
    ap.add_argument("--max-nodes", type=int, default=0, help="0=不限")
    ap.add_argument("--max-tokens", type=int, default=0, help="0=不限")
    ap.add_argument("--max-hours", type=float, default=0, help="0=不限")
    ap.add_argument("--trace", default=None,
                    help="默认 <工作区>/runs/<时间>-<任务>/trace.jsonl")
    ap.add_argument("--caps", default=cfg.caps_path(),
                    help="能力库（TREE_CAPS）。放工作区里，所以跨 session 复用")
    ap.add_argument("--index", default=cfg.index_glob(),
                    help="要索引的老树（TREE_INDEX）。执行树就是成果树")
    ap.add_argument("--progress", type=int, default=60, help="每多少秒打一行进度，0=关闭")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-depth", type=int, default=2)
    ap.add_argument("--intake", action="store_true",
                    help="先过一遍入口：和用户把预期谈定，再交给根节点（用一次就退场）")
    a = ap.parse_args()
    if a.intake and a.mock:
        ap.error("--intake 要真模型（入口就是一次对话），和 --mock 不能一起用")
    # 没有默认任务、也没有默认验收标准。默认值就是**伪造用户的话**：
    # 入口拿到一条用户从没提过的验收标准，就只能围着它编 ——
    # 实测一句“帮我自动做视频赚钱”被谈成了 A 股回测 / 模拟盘。
    # 想要默认值，就显式写出来；不想写，就让入口向用户问。
    if not a.intake:
        if not a.task:
            ap.error('必须给任务：python3 main.py "..." -c "..."'
                     '（或者用 --intake 让入口问你）')
        if not a.criteria:
            ap.error("必须给验收标准 -c：没有它，这棵树判不了自己做没做完")
    # 工作目录只有一个来源：TREE_WORKSPACE。没有默认值、没有先例可改、没有参数可绕。
    # 先例只提供“那里有什么”，不提供“你该在哪干活”。
    ws = os.path.abspath(cfg.workspace())
    if not a.trace:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"),
                          hashlib.sha1((a.task or "intake").encode("utf-8"))
                          .hexdigest()[:6])
        a.trace = os.path.join(ws, "runs", slug, "trace.jsonl")
    # exclude 只对显式 --trace 有意义 —— 那时它可能指向一棵已经存在的树。
    index = TreeIndex(sorted(glob.glob(a.index)),
                      exclude=[a.trace] if a.trace else [])

    if a.mock or not os.environ.get("TREE_API_KEY"):
        llm = MockLLM(max_depth=a.mock_depth)
        print("[mock 模式] 未检测到 TREE_API_KEY\n", flush=True)
    else:
        llm = LLM()
        print("[模型] %s @ %s" % (llm.model, llm.base_url), flush=True)

    trace = Trace(a.trace)

    # 入口（可选）：根节点的"上层"只被用一次 —— 把用户的一句话谈成
    # 一个能过同一台闸门的根任务形式，然后退场。它的对话不用留：
    # 结论已经落成根节点的形式字段了，而树就是记忆（DESIGN §2.1、§2.8）。
    # 种子只写**用户真的说了什么**：没给的就是没给（入口该去问），
    # 不许拿默认值充数。
    if a.intake:
        seed = "用户的任务: %s" % (a.task or "（他没说任务）")
        seed += ("\n用户顺口提了一个验收标准: %s（可以参考，但最后写成什么由你形式化）"
                 % a.criteria if a.criteria else
                 "\n验收标准: 用户没给 —— 正常，真用户都不会给。"
                 "那是你的活：从他的话里提一条具体的写法，让他点头或改一个数。")
        r = converse(llm, seed)
        if r is None:                 # 用户中止了：没开工，也没有结论
            return 1
        s = r["root"]
        root = Node(name=s["name"], detail=s["detail"], notes=s["notes"],
                    accept=s["accept"], kind=s["kind"],
                    keywords=s["keywords"], conc_range=s["conc_range"])
    else:
        root = Node(name=a.task, accept=a.criteria, kind="dispatch")
    registry = {}
    budget = Budget(max_nodes=a.max_nodes or None, max_tokens=a.max_tokens or None,
                    max_hours=a.max_hours or None)

    print("[验收标准] %s" % root.accept, flush=True)
    print("[限制] 无。轮次/深度/节点/token/时间 全部不限，停止交给 API 自己", flush=True)
    print("[并发] %d" % a.workers, flush=True)
    # 持久工作目录：TREE_WORKSPACE，agent 的 cwd。上次写的代码和数据就还在。
    os.makedirs(ws, exist_ok=True)
    os.chdir(ws)
    print("[工作目录] %s" % ws, flush=True)

    # 老树索引：把所有历史 trace 当成成果树
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
