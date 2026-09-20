#!/usr/bin/env python3
"""最小载体：一棵递归工作的 LLM 树。入口默认就是 intake（一次对话）。

    python3 main.py                              # 入口先问你要做什么
    python3 main.py "帮我做一个能赚大钱的A股量化系统" -c "..." --workers 6
    python3 main.py -r                           # 选一个老会话加载成当前会话

路径全部来自配置文件（.env）：工作区在哪、能力库在哪、索引扫哪里。
跑出来的东西**一律落在工作区**（包括这次的 trace），项目目录里只有代码。

会话是可续跑的：`-r` 挑一个老会话加载成当前会话 —— 对话接着谈，
没跑完的树接着跑（中断时在飞的那一步作废，节点带着完整历史重新问模型）。
"""

import argparse
import asyncio
import glob
import hashlib
import os
import sys
import time

from tree import config as cfg
from tree.llm import LLM
from tree.memory.caps import Caps
from tree.memory.index import TreeIndex, session_label
from tree.runtime.budget import Budget
from tree.runtime.session import load, session_context
from tree.runtime.trace import Trace
from terminal.chat import converse, opening
from terminal.picker import pick_session


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?",
                    help="要做的这件事（一句话）。不给就让入口问")
    ap.add_argument("--criteria", "-c",
                    help="根任务的验收标准（必须可被观测）。"
                         "不给就让入口从你的话里提一条，让你点头或改")
    ap.add_argument("-r", "--resume", action="store_true",
                    help="选一个老会话加载成当前会话：对话接着谈，"
                         "没跑完的树接着跑")
    ap.add_argument("--workers", type=int, default=6, help="并发节点数")
    ap.add_argument("--max-nodes", type=int, default=0, help="0=不限")
    ap.add_argument("--max-tokens", type=int, default=0, help="0=不限")
    ap.add_argument("--max-hours", type=float, default=0, help="0=不限")
    ap.add_argument("--trace", default=None,
                    help="默认 <工作区>/runs/<时间>-<任务>/trace.jsonl")
    ap.add_argument("--caps", default=cfg.CAPS_PATH,
                    help="能力库（TREE_CAPS）。放工作区里，所以跨 session 复用")
    ap.add_argument("--index", default=cfg.INDEX_GLOB,
                    help="要索引的老树（TREE_INDEX）。执行树就是成果树")
    ap.add_argument("--progress", type=int, default=60,
                    help="每多少秒打一行进度，0=关闭")
    a = ap.parse_args()

    # 入口是一次对话：要真模型。没有 API key 就不开工 —— 拿假模型去聊，
    # 只会换来一句"你要做什么？"，那一圈是白烧的。
    if not os.environ.get("TREE_API_KEY"):
        ap.error("入口是一次对话：要真模型。在 .env / 环境变量里给 TREE_API_KEY")

    # 工作目录只有一个来源：TREE_WORKSPACE。没有默认值、没有先例可改、没有参数可绕。
    ws = cfg.WORKSPACE

    resume = None
    if a.resume:
        # `-r`：列出老会话（最近的在前），挑一个加载成当前会话
        traces = sorted(glob.glob(a.index or cfg.INDEX_GLOB),
                        key=os.path.getmtime, reverse=True)
        if not traces:
            print("没有可加载的老会话：工作区里还没有跑过任何树。", flush=True)
            return 1
        picked = await pick_session([(t, session_label(t)) for t in traces])
        if picked is None:
            print("取消。", flush=True)
            return 0
        a.trace = picked
        try:
            resume = load(picked)
        except ValueError:
            # 中间坏行 = 真损坏：带着是哪个会话的上下文炸出来，不静默跳过
            print("读不了这个会话（记录损坏）：%s" % picked, flush=True)
            raise
    elif not a.trace:
        slug = "%s-%s" % (time.strftime("%m%d-%H%M%S"),
                          hashlib.sha1((a.task or "intake").encode("utf-8"))
                          .hexdigest()[:6])
        a.trace = os.path.join(ws, "runs", slug, "trace.jsonl")

    # 索引：老树当先例。恢复时把当前会话也索引进去 —— 它的旧内容在恢复前
    # 已完整落盘，快照干净；新会话的 trace 还不存在，glob 碰不到它。
    index = TreeIndex(sorted(glob.glob(a.index or cfg.INDEX_GLOB)),
                      exclude=[] if resume else ([a.trace] if a.trace else []))

    llm = LLM()
    print("[模型] %s @ %s" % (llm.model, llm.base_url), flush=True)

    trace = Trace(a.trace)
    registry = {}
    if resume is not None and resume["in_flight"] is not None:
        # 恢复出的节点要能画进终端、能被后续 run() 当 registry 用
        registry.update(resume["in_flight"]["registry"])
    budget = Budget(max_nodes=a.max_nodes or None, max_tokens=a.max_tokens or None,
                    max_hours=a.max_hours or None)
    caps = Caps(a.caps)

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
    print("[能力库] %s  %s" % (a.caps, caps.stats()), flush=True)

    def beat():
        # 只在调度线程里被调 —— 它就是唯一改 budget / registry 的线程，
        # 所以读它们不需要锁（AGENTS §9）。
        s = budget.stats()
        st = {}
        for n in registry.values():
            st[n.status] = st.get(n.status, 0) + 1
        print("[%s] 节点 %d (%.2f 分钟, %d tokens) 状态 %s"
              % (time.strftime("%H:%M:%S"), s["nodes"], s["minutes"],
                 s["tokens"], st), flush=True)

    env = {"trace": trace, "caps": caps, "index": index, "budget": budget,
           "workers": a.workers, "registry": registry,
           "on_beat": beat if a.progress > 0 else None,
           "beat": a.progress or 60}

    if resume is not None:
        # 恢复：对话和树都从会话记录里回来，入口接着谈 —— 不是"继续老会话"，
        # 加载出来就是当前会话。
        # 旧格式会话没有对话记录（chat_msgs 空）：用树的轮廓开局，
        # 模型才知道这场会话做过什么，而不是像新会话一样两眼一抹黑。
        msgs = resume["chat_msgs"] or None
        seed = None if msgs is not None else session_context(resume["trees"])
        r = await converse(llm, seed, env, resume=dict(resume, path=a.trace))
        trace.drain()          # 对话最后几笔必须落盘，进程才退出
        return r

    # 入口（默认就是它）：用户的一句话谈成一个根任务，**当场跑掉，结论带回来接着谈**。
    # 入口不退场 —— 谈和跑交替，直到用户在终端上中止（DESIGN §2.8）。
    # 它也是这个程序**唯一的入口**：跑树这件事在 tree/intake.py 里，不在 main。
    # 种子只写**用户真的说了什么**：没给的就是没给（入口该去问），
    # 不许拿默认值充数。
    # 用户没在命令行交底 → 先在终端上等他把话说完，再让入口开口。
    # 种子是空的时候调模型，只会换来一句"你要做什么？" —— 那一次调用
    # 是白花的，而且看起来像程序没等他说话就自作主张（实测）。
    task = a.task or await opening()
    seed = "用户的任务: %s" % task
    seed += ("\n用户顺口提了一个验收标准: %s（可以参考，但最后写成什么由你形式化）"
             % a.criteria if a.criteria else
             "\n验收标准: 用户没给 —— 正常，真用户都不会给。"
             "那是你的活：从他的话里提一条具体的写法，让他点头或改一个数。")
    r = await converse(llm, seed, env)
    trace.drain()          # 对话最后几笔必须落盘，进程才退出
    return r


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
