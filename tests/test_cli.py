#!/usr/bin/env python3
"""CLI 参数契约的定向测试。零成本、确定性 —— 参数不对在联网之前就退出了。

  A. 入口默认就是 intake，而且要真模型：没有 API key，任何入口都当场报错
     （不许拿 MockLLM 去和用户聊，也不许悄悄用一个默认任务开工）
  B. `-r` 没有可加载的老会话 → 当场说清并退出
  C. 守门：伪造的"用户的话"不许回来；--intake 那条老路已经删了
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def run(args, api_key="", workspace=None):
    """跑 CLI。默认不给 API key：参数不对必须在联网之前就退出。

    workspace：给一个空的临时目录（测试不碰真工作区）。"""
    env = dict(os.environ, TREE_API_KEY=api_key)
    if workspace is not None:
        env["TREE_WORKSPACE"] = workspace
        env["TREE_INDEX"] = ""     # 让它从临时工作区推导，不碰真工作区的老树
    p = subprocess.run([sys.executable, "main.py"] + args, cwd=ROOT,
                       capture_output=True, text=True, timeout=120, env=env)
    return p.returncode, (p.stderr or "") + (p.stdout or "")


def main():
    print("=" * 80)
    print("A. 入口默认就是 intake，而且要真模型（没有 API key 一律当场报错）")
    for args, tag in (
            ([], "什么都不给"),
            (["帮我自动做视频赚钱"], "只给任务"),
            (["帮我自动做视频赚钱", "-c", "有一条成片"], "任务 + 验收标准都给"),
            (["-r"], "要恢复老会话")):
        code, out = run(args)
        print("  %-22s exit=%s %s" % (
            tag, code, out.strip().splitlines()[-1] if out else ""))
        line("%s → 退出码 2" % tag, code == 2)
        line("%s → 说清要真模型" % tag, "真模型" in out)

    print("=" * 80)
    print("B. -r 没有可加载的老会话 → 当场说清并退出")
    with tempfile.TemporaryDirectory() as ws:
        code, out = run(["-r"], api_key="dummy", workspace=ws)
    print("  exit=%s  %s" % (code, out.strip().splitlines()[-1] if out else ""))
    line("退出码 = 1", code == 1)
    line("说清没有老会话", "没有可加载的老会话" in out)

    print("=" * 80)
    print("C. 守门：伪造的「用户的话」不许回来；老路已删")
    src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    line("没有默认任务", "给我一个能赚大钱的A股量化系统" not in src)
    line("没有默认验收标准", "期末账户权益" not in src)
    line("种子只写用户真说了什么", "用户没给" in src and "a.criteria if a.criteria" in src)
    line("--intake 老路已删（入口默认就是 intake）", "--intake" not in src)
    line("-r 在（加载老会话）", '"--resume"' in src or "'--resume'" in src)
    line("MockLLM 已删（不再有假模型去聊天的路）",
         "MockLLM" not in open(os.path.join(ROOT, "tree", "llm.py"),
                               encoding="utf-8").read())

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
