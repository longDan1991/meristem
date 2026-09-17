#!/usr/bin/env python3
"""工具层的纪律测试：**截断必须可见**。

这个文件是修一个真 bug 换来的：一个叶子把同一个文件读了 25 次。
原因不是模型傻，而是——
  · read 只返回前 4000 字，不说被截了
  · 提示词里每条观测只给模型看前 200 字，也不说被截了
模型看到的是断在半句的文件，以为没读全，于是反复重读。

静默截断 = 对模型撒谎（"这就是全部输出"）。所以：
  A. read 报出总量、本段区间、下一段怎么取
  B. read 能翻页，翻到的是不同的内容
  C. bash 输出过长时明说被截了
  D. 观测历史过长时明说被截了，且**新观测优先拿额度**
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.tools import bash, read                # noqa: E402
from tree.node import Node, LIMITS               # noqa: E402

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
    print("C. bash 输出过长 → 明说被截了")
    big = bash("python3 -c \"print('x' * 9000)\"")
    line("有截断标记", "截断" in big and "共" in big)
    line("给了替代手段", "head" in big or "grep" in big)

    print("=" * 78)
    print("D. 观测历史截断可见 + 新观测优先")
    n = Node(name="x", accept="y", kind="leaf")
    n.observations = [{"动作": "read %d" % i, "观测": str(i) * 4000}
                      for i in range(1, 9)]
    r = n.render_observations()
    # 只比观测正文，不比前缀/标题行（那是测试写法的伪差异）
    bodies = [row.split("→ ", 1)[-1] for row in r.split("\n  [") if "→ " in row]
    sizes = [len(b) for b in bodies]
    total = sum(4000 for _ in range(8))
    print("  限额 %d，%d 份原始共 %d 字，实际给了 %s"
          % (LIMITS["max_obs_chars"], len(n.observations), total, sizes))
    line("明说被截断", "截断" in r)
    nums = [int(x) for x in re.findall(r"截断：这一次共 (\d+) 字", r)]
    line("说清原始长度", bool(nums) and max(nums) >= 4000, "标明 %s 字" % nums)
    # 总额度 = 限额 + 每条最低 200 的保护线
    line("总额度受控",
         sum(sizes) <= LIMITS["max_obs_chars"] + 200 * LIMITS["max_obs_shown"])
    line("越新的观测拿到越多额度",
         len(sizes) == len(n.observations) and sizes == sorted(sizes),
         "旧→新 %s" % sizes)
    line("最新那次没有被压短", sizes and sizes[-1] >= LIMITS["obs_entry"],
         "最新 %d 字（上限 %d）" % (sizes[-1], LIMITS["obs_entry"]))

    print("=" * 78)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
