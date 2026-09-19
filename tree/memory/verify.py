"""主动重验：把库里的 cap 重新跑一遍，坏了的记进 fails，喂给现有的自动退休。

为什么需要：`uses`/`fails` 是**被动**的 —— 只有被用到才记账。一条没人再用的
cap 可能早就烂了（脚本被删、依赖没了、数据 schema 变了），直到某次被检索出来
才害人。主动重验是扫一遍，把已经烂的先记上账（`fails > uses` 就会退休）。

保守三原则（宁可漏查，不可误杀）：
  · 只在临时目录里跑 —— 副作用不污染工作区；
  · 只重验**不依赖项目目录**的（scope=general 且没标"依赖当前目录"、没有 cwd）——
    project 的配方必须站在原项目里才成立，在空目录里跑必败，那是在冤枉它；
  · 超时给短一点 —— 重验不是干活，是体检。

跑法：`python -m tree.memory.verify <caps.jsonl>`。
"""

import asyncio
import os
import sys
import tempfile

from ..tools import bash
from .caps import Caps

# 一条命令重验最多跑多久。体检要快，真要跑很久的配方不该被主动重验拖住。
VERIFY_TIMEOUT = 30


def eligible(e):
    """值得重验的：general、不依赖当前目录、没有绑定 cwd。"""
    if (e.get("scope") or "") != "general":
        return False
    how = e.get("how") or {}
    if how.get("cwd"):
        return False
    pre = e.get("前置条件") or {}
    return not pre.get("依赖当前目录")


def verify_one(e):
    cmd = (e.get("how") or {}).get("cmd") or ""
    if not cmd:
        return None
    try:
        obs = asyncio.run(bash(cmd, timeout=VERIFY_TIMEOUT))
    except (OSError, ValueError):
        return False                        # 命令本身炸了 = 没跑成
    # 编程错误不在上面（TypeError 之类照旧往上炸，§2）：那是 bug，不是坏配方
    return "工具出错" not in obs and ("[exit=" not in obs or "[exit=0]" in obs)


def verify(caps, report=None):
    """重跑一遍，坏的记 fails。返回 (checked, broken)。

    cwd 切进临时目录：重验的副作用不污染工作区（bash 不带 cwd，
    得靠 chdir，跑完恢复）。"""
    checked = broken = 0
    saved = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            for e in list(caps.entries.values()):
                if e.get("retired") or not eligible(e):
                    continue
                ok = verify_one(e)
                if ok is None:
                    continue
                checked += 1
                if not ok:
                    broken += 1
                    caps.note_outcome(e["id"], False)
                    if report:
                        report.append((e["id"], (e.get("how") or {}).get("cmd", "")))
        finally:
            os.chdir(saved)
    return checked, broken


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("用法: python -m tree.memory.verify <caps.jsonl>\n")
        return 2
    caps = Caps(argv[1])
    report = []
    checked, broken = verify(caps, report)
    print("重验 %d 条，烂了 %d 条（已记进 fails，失败多于成功会自动退休）"
          % (checked, broken))
    for eid, cmd in report[:20]:
        print("  ✗ %s  %s" % (eid, cmd[:90]))
    if len(report) > 20:
        print("  …还有 %d 条" % (len(report) - 20))
    print("可调用 %s / 不可调用 %s / 总数 %s"
          % (caps.stats().get("可调用"), caps.stats().get("不可调用"),
             caps.stats().get("总数")))
    return 0 if broken == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
