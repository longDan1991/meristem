"""叶子的手：叶子只能通过这些工具接触世界，事实必须从这里产生。

工具输出不截断，跑出多少就是多少，完整流到压缩层；read 是翻页不是截断，会明说本段在哪、还有多少。

环境失败（文件不存在、命令跑不动）是观测不是异常，就地变成文本让模型换路；
真正的编程错误照旧往上炸。
"""

import asyncio
import os
import signal
import subprocess
import time

READ_CAP = 2000

# bash 必须带超时，否则一条卡住的命令会钉死整棵树；超时也是一条必须当面说清的事实，
# 否则模型会当成"工具坏了"原样重试。
BASH_TIMEOUT = 120        # 默认：一条命令最多跑这么久
BASH_TIMEOUT_MAX = 3600   # 上限：更久的事请改成后台 + 轮询


async def bash(cmd, timeout=None):
    """跑一条命令：总是有超时，但超时可见、可调、会连子进程一起杀。

    真异步，不占线程；超时时把已经产生的输出交回去（丢掉就是静默截断）。
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
    # 增量读：`wait_for(p.communicate(), t)` 取消时会把已读数据一起丢掉，那样超时就交不回输出
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
    """读文件的一段，并明说这段在哪、还有多少；报出区间模型才能自己翻页。"""
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
