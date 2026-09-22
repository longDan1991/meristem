#!/usr/bin/env python3
"""CLI 参数契约的定向测试。零成本、确定性 —— **不跑 subprocess（测试不走 CLI）**，
直接在进程内调 `terminal.chat.run_session` / `main.parse_args`。

  A. 入口默认就是 intake，而且要真模型：没有 API key，新会话和 -r 都当场报错
     （不许拿假模型去和用户聊，也不许悄悄用一个默认任务开工）
  B. -r 没有可加载的老会话 → 当场说清并退出
  C. 守门：伪造的「用户的话」不许回来；老路已删；main.py 只剩 -r 一个参数
"""

import argparse
import asyncio
import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import main as main_mod                                     # noqa: E402
import terminal.chat as chat                                # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def run_session(resume, api_key="", traces=None):
    """进程内跑 `run_session`（不走 CLI）。api_key="" = 没给。

    traces：`-r` 时老会话列表的替身（测试不碰真工作区的树），不给默认空。
    返回 (退出码/返回值, 标准输出 + 标准错误)。
    """
    os.environ["TREE_API_KEY"] = api_key
    if traces is not None:
        chat.Store.roots = staticmethod(lambda: traces)
    a = argparse.Namespace(resume=resume)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = asyncio.run(chat.run_session(a))
        return code, out.getvalue()
    except SystemExit as e:
        return e.code, out.getvalue()


def main():
    print("=" * 80)
    print("A. 入口默认就是 intake，而且要真模型（没有 API key 一律当场报错）")
    for resume, tag in ((False, "什么都不给"), (True, "-r 恢复老会话")):
        code, out = run_session(resume=resume, api_key="")
        print("  %-18s exit=%s %s" % (
            tag, code, out.strip().splitlines()[-1] if out else ""))
        line("%s → 退出码 2" % tag, code == 2)
        line("%s → 说清要真模型" % tag, "真模型" in out)

    print("=" * 80)
    print("B. -r 没有可加载的老会话 → 当场说清并退出")
    code, out = run_session(resume=True, api_key="dummy", traces=[])
    print("  exit=%s  %s" % (code, out.strip().splitlines()[-1] if out else ""))
    line("返回值 = 1", code == 1)
    line("说清没有老会话", "没有可加载的老会话" in out)

    print("=" * 80)
    print("C. 守门：伪造的「用户的话」不许回来；老路已删")
    src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    chat_src = open(os.path.join(ROOT, "terminal", "chat.py"), encoding="utf-8").read()
    line("main.py 只剩 -r 一个参数", '"-r"' in src and "--resume" in src
         and "--workers" not in src and "--criteria" not in src
         and "--max-nodes" not in src and "--max-tokens" not in src
         and "--max-hours" not in src and "--trace" not in src
         and "--progress" not in src and '"task"' not in src)
    line("main.py 是薄分派（不碰终端 / 不碰运行现场）",
         "from terminal.chat import" in src and "Trace(" not in src
         and "converse(" not in src and "opening()" not in src and "LLM(" not in src)
    a = main_mod.parse_args(["-r"])
    line("-r 真的解析成一个参数", a.resume is True
         and main_mod.parse_args([]).resume is False)
    line("没有默认任务", "给我一个能赚大钱的A股量化系统" not in src + chat_src)
    line("没有默认验收标准", "期末账户权益" not in src + chat_src)
    line("种子只写用户真说了什么", "用户没给" in chat_src)
    line("--intake 老路已删（入口默认就是 intake）", "--intake" not in src)
    line("MockLLM 已删（不再有假模型去聊天的路）",
         "MockLLM" not in open(os.path.join(ROOT, "tree", "llm.py"),
                               encoding="utf-8").read())

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
