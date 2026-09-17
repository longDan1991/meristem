#!/usr/bin/env python3
"""CLI 参数契约的定向测试。零成本、确定性 —— 参数不对在联网之前就退出了。

  A. 给了任务没给验收标准 → 报错（不是悄悄用一个默认值）
  B. 什么都没给 → 报错：**没有默认任务，也没有默认验收标准**
  C. `--intake` 和 `--mock` 一起用 → 报错（入口就是一次真对话）
  D. 守门：伪造的"用户的话"不许回来 —— 源码里不许再有硬编码的默认任务/标准
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def run(args):
    """跑 CLI。**不给 API key**：参数不对必须在联网之前就退出。"""
    env = dict(os.environ, TREE_API_KEY="")
    p = subprocess.run([sys.executable, "main.py"] + args, cwd=ROOT,
                       capture_output=True, text=True, timeout=120, env=env)
    return p.returncode, (p.stderr or "") + (p.stdout or "")


def main():
    print("=" * 80)
    print("A. 给了任务、没给验收标准 → 当场报错")
    code, out = run(["帮我自动做视频赚钱"])
    print("  exit=%s  %s" % (code, out.strip().splitlines()[-1] if out else ""))
    line("退出码 = 2（argparse 的用法错）", code == 2)
    line("说清缺的是验收标准", "验收标准" in out)
    line("没偷偷用一个默认值开工", "[模型]" not in out and "[mock" not in out)

    print("=" * 80)
    print("B. 什么都没给 → 报错（不再有量化默认）")
    code, out = run([])
    print("  exit=%s  %s" % (code, out.strip().splitlines()[-1] if out else ""))
    line("退出码 = 2", code == 2)
    line("说清必须给任务", "必须给任务" in out)
    line("提示了 --intake 这条替代路", "--intake" in out)

    print("=" * 80)
    print("C. --intake 和 --mock 一起用 → 报错")
    code, out = run(["做视频", "-c", "有一条成片", "--intake", "--mock"])
    line("退出码 = 2", code == 2)
    line("说清入口要真模型", "mock" in out and "真模型" in out)

    print("=" * 80)
    print("D. 守门：伪造的「用户的话」不许回来")
    src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    line("没有默认任务", "给我一个能赚大钱的A股量化系统" not in src)
    line("没有默认验收标准", "期末账户权益" not in src)
    line("种子只写用户真说了什么", "用户没给" in src and "a.criteria if a.criteria" in src)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
