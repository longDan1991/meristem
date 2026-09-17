"""叶子的手。叶子只能通过这些工具接触世界，所以事实必须从这里产生。

一条硬纪律：**截断必须可见。**

静默截断等于对模型撒谎 —— 它会以为"这就是全部输出"，然后反复重读同一个
东西。这不是假设：实测一个叶子把同一个文件读了 25 次，只因为提示词里
每条观测只给它看前 200 字，而它不知道那是截断。模型不傻，是我们没给它信息。
"""

import subprocess

BASH_CAP = 4000
READ_CAP = 2000


def bash(cmd, timeout=120):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    n = len(out)
    if n > BASH_CAP:
        out = (out[:BASH_CAP] + "\n…[截断：输出共 %d 字，这里只显示了前 %d 字。"
               "要精确取用 head/tail/grep/sed -n]" % (n, BASH_CAP))
    return out + ("\n[exit=%d]" % p.returncode if p.returncode else "")


def read(path, offset=0, limit=READ_CAP):
    """读文件的一段，并**明说**这段在哪、还有多少。

    报出行号区间，模型才能自己翻页；不报，它就只能反复重读同一段。
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        s = f.read()
    n = len(s)
    offset = max(0, int(offset or 0))
    limit = max(1, int(limit or READ_CAP))
    seg = s[offset:offset + limit]
    end = offset + len(seg)
    head = "[%s 共 %d 字，本段 %d-%d]" % (path, n, offset, end)
    if end < n:
        head += " 还有 %d 字未显示 —— read(offset=%d) 取下一段" % (n - end, end)
    return head + "\n" + seg


def write(path, content):
    with open(path, "w") as f:
        f.write(content)
    return "written: %s (%d bytes)" % (path, len(content))


TOOLS = {"bash": bash, "read": read, "write": write}
