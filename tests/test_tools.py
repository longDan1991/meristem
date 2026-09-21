#!/usr/bin/env python3
"""工具层的纪律测试。

这个文件是修一个真 bug 换来的：一个叶子把同一个文件读了 25 次。
原因不是模型傻，而是 read 静默截断 —— 模型以为读全了，其实没有。

教训落成两条：
  · read 是**翻页不是截断**：报出总量、本段区间、怎么取下一段（A/B）
  · bash 输出**不截断**：跑出多少就是多少（C）—— 压缩在发送边界处理它，
    截断会毁掉压缩救不回来的数据。
  · bash 必须带超时，超时是可见的事实（D）
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tree.tools as T                        # noqa: E402
from tree.tools import read                  # noqa: E402


def bash(*a, **k):
    """bash 现在是真异步（P4），测试里用同步壳调它。"""
    return asyncio.run(T.bash(*a, **k))

OK = []


def line(tag, cond, detail=""):
    print("  %s %-46s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def main():
    p = "/tmp/_t_tools.txt"
    with open(p, "w") as f:
        f.write("\n".join("第%d行" % i for i in range(1, 1201)))   # ~ 9000 字

    print("=" * 78)
    print("A. read 报出总量 / 本段区间 / 怎么取下一段")
    head = read(p)
    print("  %s" % head.split("\n")[0])
    line("有总量", "共" in head and "字" in head)
    line("有本段区间", "本段" in head)
    line("说清还有多少字", "还有" in head and "未显示" in head)
    line("给出翻页办法", "offset=" in head)

    print("=" * 78)
    print("B. read 能翻页，翻到的是不同的内容")
    tail = read(p, offset=4000)
    print("  第二段开头: %s" % tail.split("\n")[1])
    line("两段内容不同", tail.split("\n")[1] != head.split("\n")[1])
    line("翻到末尾时明说已到末尾", "未显示" not in read(p, offset=20000))

    print("=" * 78)
    print("C. bash 输出不截断：跑出多少就是多少")
    big = bash("python3 -c \"print('x' * 70000)\"")
    line("70000 字完整返回（没有截断标记）", len(big) >= 70000 and "截断" not in big,
         "%d 字" % len(big))

    print("=" * 78)
    print("D. bash 必须带超时，而且超时是可见的 / 可调的 / 会连子进程一起杀")
    out = bash("echo 先打一行; sleep 30", timeout=2)
    print("  超时观测（末两行）: %s" % " / ".join(out.strip().splitlines()[-2:]))
    line("明说是超时，不是「工具出错」", "[超时]" in out and "工具出错" not in out)
    line("已经产生的输出被带回来了", "先打一行" in out)
    line("说了上限和怎么跑更久", "上限" in out and "nohup" in out)

    # 留不留孤儿：子进程 3 秒后去碰一个文件，若没被一起杀就会看到它
    orphan = "/tmp/_t_orphan_%d" % os.getpid()
    if os.path.exists(orphan):
        os.remove(orphan)
    bash("sh -c 'sleep 3; touch %s' & echo 起了个子进程; sleep 30" % orphan,
           timeout=1)
    time.sleep(4)
    line("超时把子进程也一起杀了（没留孤儿）", not os.path.exists(orphan))

    # 夹上限：把上限改小，否则要等一小时才能验这一条
    _saved = (T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX)
    T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX = 1, 2
    try:
        o1 = bash("sleep 30", timeout=99999)
        line("超上限会被夹住并明说", "被夹到上限" in o1 and "99999" in o1)
        o2 = bash("sleep 30")          # 不给 timeout → 用默认
        line("不给 timeout 也一定有超时（走默认）", "[超时]" in o2 and "上限" in o2)
    finally:
        T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX = _saved

    print("=" * 78)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
