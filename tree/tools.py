"""叶子的手。叶子只能通过这些工具接触世界，所以事实必须从这里产生。

一条硬纪律：**截断必须可见。**

静默截断等于对模型撒谎 —— 它会以为"这就是全部输出"，然后反复重读同一个
东西。这不是假设：实测一个叶子把同一个文件读了 25 次，只因为提示词里
每条观测只给它看前 200 字，而它不知道那是截断。模型不傻，是我们没给它信息。
"""

import os
import signal
import subprocess

BASH_CAP = 4000
READ_CAP = 2000

# bash 必须带超时：没有它，一条卡住的命令会把整棵树钉死在那里。
# 但"超时"本身也是**一条事实**，必须当面说清楚（§2.5）：
#   默认多少、你能不能改、改的上限、超了之后已经跑出来的输出还在不在。
# 不说清楚，模型会把超时当成"工具坏了"，于是原样重试。
BASH_TIMEOUT = 120        # 默认：一条命令最多跑这么久
BASH_TIMEOUT_MAX = 3600   # 上限：更久的事请改成后台 + 轮询（提示词里写明了）


def bash(cmd, timeout=None):
    """跑一条命令。**总是有超时**，但超时是可见的、可调的、会连子进程一起杀。

    两个细节不能省：
      · `start_new_session=True` + `killpg` —— 只杀 shell 不杀子进程的话，
        被杀掉的 `python train.py` 还在后台跑，把机器占住。
      · 超时时把**已经产生的输出**交回去 —— 一个跑了两分钟才被杀的
        回测，它前面打印的东西正是模型最需要的。丢掉它们就是再一次静默截断。
    """
    try:
        t = int(timeout) if timeout not in (None, "") else BASH_TIMEOUT
    except Exception:
        t = BASH_TIMEOUT
    if t <= 0:
        t = BASH_TIMEOUT
    asked = t
    if t > BASH_TIMEOUT_MAX:
        t = BASH_TIMEOUT_MAX
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True,
                         start_new_session=True)
    timed_out = False
    try:
        out, _ = p.communicate(timeout=t)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            p.kill()
        out, _ = p.communicate()          # 收尸，顺手把已产生的输出拿回来
    out = (out or "").strip()
    n = len(out)
    if n > BASH_CAP:
        out = (out[:BASH_CAP] + "\n…[截断：输出共 %d 字，这里只显示了前 %d 字。"
               "要精确取用 head/tail/grep/sed -n]" % (n, BASH_CAP))
    if timed_out:
        note = ("\n[超时] 这条命令跑了 %d 秒还没结束，已经被连同它起的子进程一起杀掉。"
                % t)
        if asked > BASH_TIMEOUT_MAX:
            note += "（你写的是 %d 秒，被夹到上限 %d 秒）" % (asked, BASH_TIMEOUT_MAX)
        if out:
            note += "\n已经产生的输出在上面（不是全部）。"
        else:
            note += "\n它一点输出都没来得及给。"
        note += ("\n要跑更久：把 args.timeout 调大（上限 %d 秒），"
                 "或者把长任务改成后台：`nohup <cmd> > run.log 2>&1 &`，"
                 "然后轮询 run.log 和产物（轮询时观测会变，不会被当成原地打转）。"
                 % BASH_TIMEOUT_MAX)
        return (out + note).strip()
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
