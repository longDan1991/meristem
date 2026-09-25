"""bash 工具：命令跑在 llmbash 进程内 shell 上。

schema 与给模型的文字描述**照抄 oh-my-pi 的 BashTool**（`packages/coding-agent/src/prompts/tools/bash.md`
的渲染版 + `BASH_TIMEOUT_DESCRIPTION`；llmbash 就是 oh-my-pi 的 pi-shell 的 Python 封装）。
执行走 llmbash：进程内命令（常见命令不 fork/exec）、超时走 CancelToken。
会话管理照 oh-my-pi 的 bash-executor：持久 shell 按 cwd 复用、并发重叠降级 one-shot 真并行、
坏会话弃用重建。
"""

import os
from typing import Annotated

import llm_sh

from fastmcp.dependencies import Depends

from core.protocol import feedback
from core.protocol.fields import LEAF
from tools.context import _action_result, _current, get_binding
from tools.specs import ACTION_TAG, mcp, scope_tag

# bash 必须带超时，否则一条卡住的命令会钉死整棵树；超时也是一条必须当面说清的事实，
# 否则模型会当成"工具坏了"原样重试。
BASH_TIMEOUT = 120        # 默认：一条命令最多跑这么久（秒）
BASH_TIMEOUT_MAX = 3600   # 上限；`timeout=0` 禁用 deadline

# 持久 shell 池（key = 工作目录）：export / 函数跨调用保留；同一 key 同一时间只跑一条，
# 并发重叠的调用降级为一次性 one-shot shell（真并行不排队）；run 抛错说明 shell 坏了，弃用重建。
_sessions: dict[str, llm_sh.Session] = {}
_sessions_busy: set[str] = set()


def _acquire_shell(key):
    """取一个 shell：key 空闲 → 复用持久 shell 并标记占用；被占用 → 一次性 shell（真并行）。"""
    if key in _sessions_busy:
        return llm_sh.Session(minimize=False), False
    s = _sessions.get(key)
    if s is None:
        s = llm_sh.Session(minimize=False)
        _sessions[key] = s
    _sessions_busy.add(key)
    return s, True


def _release_shell(key):
    _sessions_busy.discard(key)


# 参数描述照抄 oh-my-pi（BashTool schema / BASH_TIMEOUT_DESCRIPTION）。
_CMD_DESC = "command to execute"
_CWD_DESC = "working directory"
_TIMEOUT_DESC = ("timeout in seconds; 0 disables the command deadline; "
                 "nonzero values are clamped to 1-%d" % BASH_TIMEOUT_MAX)


@mcp.tool(tags={scope_tag(LEAF), ACTION_TAG})
async def bash(
        command: Annotated[str, _CMD_DESC],
        timeout: Annotated[int, _TIMEOUT_DESC] = BASH_TIMEOUT,
        cwd: Annotated[str, _CWD_DESC] = "",
        _b=Depends(get_binding)) -> dict:
    """Runs commands in a persistent shell.

    Use ONLY for one binary or a short pipeline that computes a fact (`wc -l`, `sort | uniq -c`, `diff`).
    Inline scripts, heredocs, `$(…)`, and complex control flow → a purpose-built tool or checked-in script.

    <instruction>
    - Set `cwd` instead of `cd`.
    - Order-dependent commands use `&&` in one call; independent calls may run concurrently.
    - aux utils available: mkdir, wc, sort, comm, diff, uniq, base64, cmp, md5sum, sha*sum, b2sum, basename, dirname, readlink, realpath, touch, stat, date, mktemp, seq, yes, printenv, truncate, tac, nproc, uname, whoami, hostname, which, ps, pgrep, pkill, pidwait, top, cut, tee, tr, paste, sed, xargs, jq, rm, mv, ln, ts, sponge, ifne, isutf8, combine, errno
    </instruction>
    """
    _loop, store, nid, _node = _current(_b)
    command = str(command or "")
    if not command.strip():
        return {"text": _action_result(store, nid, "bash", {"command": command},
                                       feedback.empty_command())}
    obs = str(await _run_bash(command, timeout=timeout, cwd=cwd or None))
    return {"text": _action_result(store, nid, "bash",
                                   {"command": command, "timeout": timeout, "cwd": cwd},
                                   obs)}


async def _run_bash(command, timeout=None, cwd=None):
    """跑一条命令：总是有超时，但超时可见、可调、会连子进程一起杀。

    timeout 是秒：0 = 不限时（对齐 oh-my-pi：timeout 0 禁用 deadline），负值 = 走默认。
    llmbash 超时走 CancelToken：返回 timed_out=True 而非异常，已产生的输出保留，进程树被杀；
    命令自己的非零退出是 exit_code，不是错误。
    """
    try:
        t = int(timeout) if timeout not in (None, "") else BASH_TIMEOUT
    except (TypeError, ValueError):
        t = BASH_TIMEOUT
    asked = t
    if t < 0:
        t = BASH_TIMEOUT
    timeout_ms = None if t == 0 else min(t, BASH_TIMEOUT_MAX) * 1000
    key = cwd or os.getcwd()
    shell, pooled = _acquire_shell(key)
    try:
        try:
            r = await shell.run(command, cwd=key, timeout_ms=timeout_ms)
        except RuntimeError as e:
            # pyo3 把 shell 内部错误（起不来等）转成 RuntimeError；命令自己的非零退出不是错误。
            # 持久 shell 抛错说明它坏了 —— 弃用，下次重建（对齐 oh-my-pi 的坏会话隔离）。
            if pooled:
                _sessions.pop(key, None)
            return feedback.tool_error(e)
    finally:
        if pooled:
            _release_shell(key)
    out = r.output.strip()
    if r.timed_out:
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
    return out + ("\n[exit=%d]" % r.exit_code if r.exit_code else "")
