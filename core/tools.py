"""叶子的手。叶子只能通过这些工具接触世界，所以事实必须从这里产生。

工具输出**不截断**：跑出多少就是多少，完整流到压缩层（core/compression.py）——
日志/JSON 在发送边界被无损折叠，模型收到的永远是被压过的完整内容。
截断会毁掉压缩救不回来的数据（尾部 FATAL 行、超出部分的 JSON），所以没有。

read 是**翻页**不是截断：它按 offset/limit 给一段，并明说"本段在哪、还有多少、
下一段怎么取"—— 那是工具契约，不是静默丢弃。

另一条：**环境失败是观测，不是异常。** 文件不存在、命令跑不动，是"世界说不行",
要让模型看见并据此换路；所以工具在这里就地把它变成观测文本返回。
真正的编程错误（不该发生的）照旧往上炸，不被糊掉（AGENTS §2、§6）。
"""

import asyncio
import os
import signal
import subprocess
import time

READ_CAP = 2000

# bash 必须带超时：没有它，一条卡住的命令会把整棵树钉死在那里。
# 但"超时"本身也是**一条事实**，必须当面说清楚：
#   默认多少、你能不能改、改的上限、超了之后已经跑出来的输出还在不在。
# 不说清楚，模型会把超时当成"工具坏了"，于是原样重试。
BASH_TIMEOUT = 120        # 默认：一条命令最多跑这么久
BASH_TIMEOUT_MAX = 3600   # 上限：更久的事请改成后台 + 轮询（提示词里写明了）


async def bash(cmd, timeout=None):
    """跑一条命令。**总是有超时**，但超时是可见的、可调的、会连子进程一起杀。

    真异步（P4）：`asyncio.create_subprocess_shell` + `wait_for`，不占线程。
    语义和以前逐字一致：`start_new_session=True` + `killpg` 连子进程一起杀；
    超时时把**已经产生的输出**交回去 —— 一个跑了两分钟才被杀的
    回测，它前面打印的东西正是模型最需要的。丢掉它们就是再一次静默截断。
    """
    try:
        t = int(timeout) if timeout not in (None, "") else BASH_TIMEOUT
    except (TypeError, ValueError):
        t = BASH_TIMEOUT
    if t <= 0:
        t = BASH_TIMEOUT
    asked = t
    if t > BASH_TIMEOUT_MAX:
        t = BASH_TIMEOUT_MAX
    try:
        p = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            start_new_session=True)
    except OSError as e:
        return "工具出错: %r" % e
    # 增量读，超时时**保住已经读到的部分**：`wait_for(p.communicate(), t)`
    # 取消的那一瞬会把已读进缓冲的数据一起丢掉 —— 那正是"把已产生的输出
    # 交回去"要交的东西（实测：`echo 先打一行; sleep 30` 超时后 out 是空的）。
    chunks, timed_out = [], False
    deadline = time.monotonic() + t
    while True:
        left = deadline - time.monotonic()
        if left <= 0:
            timed_out = True
            break
        try:
            chunk = await asyncio.wait_for(p.stdout.read(65536), left)
        except asyncio.TimeoutError:
            timed_out = True
            break
        if not chunk:
            break
        chunks.append(chunk)
    if timed_out:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except OSError:
            p.kill()
    out = b"".join(chunks).decode("utf-8", "replace").strip()
    rc = await p.wait()
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
                 "然后轮询 run.log 和产物。"
                 % BASH_TIMEOUT_MAX)
        return (out + note).strip()
    return out + ("\n[exit=%d]" % rc if rc else "")


def read(path, offset=0, limit=READ_CAP):
    """读文件的一段，并**明说**这段在哪、还有多少。

    报出行号区间，模型才能自己翻页；不报，它就只能反复重读同一段。
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            s = f.read()
    except OSError as e:
        return "工具出错: %r" % e
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
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return "工具出错: %r" % e
    return "written: %s (%d bytes)" % (path, len(content))
