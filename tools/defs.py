"""工具：模型与程序之间唯一的通道，实现就是 `@mcp.tool` 函数（schema 与实现一体）。

工具按节点类型分（alloc: create_children / conclude，leaf: bash / read / write / conclude，
intake: submit_root）。每次调用由 Loop 用 `run_tool` 驱动，`(loop, nid)` 经 ContextVar
注入，各 asyncio task 独立所以并行调用不串。

返回 `{"text": ...}`：None = 结构类工具成功、不写 tool 回话；字符串 = 观测 / 拒绝理由。
"""

import asyncio
import contextvars
import os
import signal
import subprocess
import time
from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from core.compression import RETRIEVE_NAME, retrieve_original
from core.effects import abs_path, effects_of
from core.protocol.fields import EXTERNAL_CLASSES, NOT_STARTED, SATISFIED, VERDICTS, task_root
from core.protocol.gate import anchors, clean_conclusion, clean_spec, covers, validate_root
from core.prompts import feedback
from core.prompts.messages import base_user, child_result, result_marks
from core.runtime.plan import make_child
from tools.specs import ChildSpec, mcp

READ_CAP = 2000

# bash 必须带超时，否则一条卡住的命令会钉死整棵树；超时也是一条必须当面说清的事实，
# 否则模型会当成"工具坏了"原样重试。
BASH_TIMEOUT = 120        # 默认：一条命令最多跑这么久
BASH_TIMEOUT_MAX = 3600   # 上限：更久的事请改成后台 + 轮询

# Loop 调用工具前写入 (loop, nid)；工具函数用 Depends 注入。
_binding = contextvars.ContextVar("tool_binding", default=None)


def get_binding():
    return _binding.get()


def _current(binding):
    loop, nid = binding
    return loop, loop.store, nid, loop.store.registry[nid]


def _root_anchors(node, registry):
    """任务根的 accept 里的可测物理量（任务根 = 入口节点的孩子 / 无父节点）。"""
    return anchors(task_root(node, registry).accept)


def _record_effects(store, nid, tool, args, eff, pre, created, modified):
    store.record(nid, "effects", {"tool": tool, "args": args,
                                  "wrote": created + modified,
                                  "effects": eff, "前置条件": pre})


def _action_result(store, nid, tool, args, obs):
    """一次动作的收尾：把事实记进 trace，返回给模型看的观测文本。"""
    store.record(nid, "tool", {"tool": tool, "args": args, "obs": str(obs)})
    return obs


def _fs_actual(declared, doomed, before):
    """声明的路径对账成实际发生的 create/modify/delete（动作之后跑）。

    `before` 是动作**之前**的存在性，调用方必须动作前捕获（动作后再查就是"已经发生"）。
    """
    created = [p for p in declared if not before[p] and os.path.exists(p)]
    modified = [p for p in declared if before[p] and os.path.exists(p)]
    deleted = [p for p in doomed if before[p] and not os.path.exists(p)]
    return created, modified, deleted


def _finish(store, nid, tool, obs, eff, pre, *, effects_args, tool_args,
            created=(), modified=()):
    """一次动作的收尾：effects 预测与 tool 观测两笔事实进 trace，返回给模型看的文本。"""
    _record_effects(store, nid, tool, effects_args, eff, pre, created, modified)
    return {"text": _action_result(store, nid, tool, tool_args, obs)}


# ---------------------------------------------------------------- 结论的语义
def _deferred(store, parent):
    """父节点上还没启动的孩子：没结论、对话也为空。"""
    out = []
    for cid in parent.children:
        c = store.registry.get(cid)
        if c is not None and not c.verdict and not store.dialogue(cid).to_list():
            out.append(c)
    return out


def _resolve_gate(store, nid):
    """门槛孩子出了结论 → 续跑 / 作废它的暂缓兄弟（幂等）。"""
    node = store.registry.get(nid)
    if node is None or not node.gate or not node.verdict or not node.parent:
        return
    parent = store.registry.get(node.parent)
    if parent is None:
        return
    deferred = [c for c in _deferred(store, parent) if c.id != nid]
    if not deferred:
        return
    if node.verdict == SATISFIED:
        for c in deferred:
            store.append_user(c.id, base_user(c))
        store.record(parent.id, "gate_passed",
                     {"gate": node.name, "started": [c.name for c in deferred]})
    else:
        for c in deferred:
            store.set_verdict(c.id, NOT_STARTED, feedback.gate_failed(node.conclusion), [], [])
        store.record(parent.id, "gate_failed",
                     {"gate": node.name, "reason": node.conclusion,
                      "skipped": [c.name for c in deferred]})


def _push_results(store, pid):
    """父节点的孩子都出结论了就把结果逐条拼回父对话（幂等）。"""
    parent = store.registry.get(pid)
    if parent is None or not parent.children:
        return
    kids = [store.registry.get(c) for c in parent.children]
    if any(k is None or not k.verdict for k in kids):
        return
    seen, _ = result_marks(store.dialogue(pid).to_list())
    for k in kids:
        if k.id not in seen:
            store.append_user(pid, child_result(k))


# ---------------------------------------------------------------- 结构类工具
@mcp.tool
async def create_children(children: list[ChildSpec],
                          _b=Depends(get_binding)) -> dict:
    """把任务拆成更小的子任务交给下层节点（调它 = 再拆一层）。

    有门槛时只有门槛孩子拿到任务，其余对话为空 = 暂缓；成功不写 tool 回话。
    """
    _loop, store, nid, node = _current(_b)
    parent_anchors = anchors(node.accept)
    root_anchors = _root_anchors(node, store.registry)
    specs, reject = [], None
    for raw in [c.model_dump() for c in children]:
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        if not (covers(parent_anchors, s["accept"])
                and covers(root_anchors, s["accept"])):
            reject = feedback.criterion_drift(root_anchors or parent_anchors)
            store.record(nid, "criterion_drift",
                         {"child": s["name"], "accept": s["accept"],
                          "root_anchors": sorted(root_anchors)})
            break
        specs.append(s)
    if reject:
        return {"text": reject}
    gates = [s for s in specs if s["gate"]]
    if len(gates) > 1:
        return {"text": feedback.too_many_gates()}
    gate = gates[0] if gates else None
    kids = [make_child(node, s) for s in specs]
    store.put(kids, on_id=nid)
    active = [k for k in kids if gate is None or k.gate]
    for k in active:
        store.append_user(k.id, base_user(k))
    store.record(nid, "allocated",
                 {"gate": gate["name"] if gate else None,
                  "deferred": [k.name for k in kids if k.id not in {a.id for a in active}]})
    return {"text": None}


@mcp.tool
async def conclude(
        verdict: Annotated[str, " | ".join(VERDICTS)],
        text: Annotated[str, "结论正文，落在上层给的 conc_range 区间里。"],
        evidence: Annotated[list[str] | None,
                            "判定「满足」时必填：第几次观测 / 产物路径 / 子任务 name。"] = None,
        external: Annotated[str, "判定「阻塞」时：" + " / ".join(EXTERNAL_CLASSES) + "。"] = "",
        _b=Depends(get_binding)) -> dict:
    """出结论：判定这件事做没做完。判定「满足」必须指得出真证据。"""
    _loop, store, nid, node = _current(_b)
    got, err = clean_conclusion(
        {"verdict": verdict, "text": text, "evidence": evidence or [],
         "external": external}, store, node, msgs=store.dialogue(nid).to_list())
    if err:
        store.record(nid, "bad_conclusion", err)
        return {"text": err}
    store.set_verdict(nid, got["verdict"], got["content"],
                      got["evidence"], got["external"])
    store.record(nid, "concluded",
                 {"verdict": got["verdict"], "text": got["content"],
                  "evidence": got["evidence"], "external": got["external"]})
    _resolve_gate(store, nid)
    if node.parent:
        _push_results(store, node.parent)
    return {"text": None}


@mcp.tool
async def submit_root(root: ChildSpec, _b=Depends(get_binding)) -> dict:
    """把谈成的任务交出去当场跑。返回后任务树开始长，跑完结论回到对话。"""
    loop, store, nid, node = _current(_b)
    got, why = validate_root(root.model_dump())
    if got is None:
        if loop.say:
            loop.say("（入口交的东西用不了：%s）" % why)
        return {"text": feedback.bad_root(why)}
    if loop.say:
        loop.say("（接到任务：%s）" % got["name"])
    task = make_child(node, got)
    store.put([task], on_id=nid)
    store.append_user(task.id, base_user(task))
    store.record(nid, "submitted", {"task": task.id, "name": task.name})
    return {"text": None}


# ---------------------------------------------------------------- 三只手
@mcp.tool
async def bash(
        cmd: Annotated[str, "要跑的一条命令，如 bash sum.sh 或 python3 main.py。"
                            "命令是唯一能改变世界的东西。"],
        timeout: Annotated[int, "超时秒数。默认 120，上限 3600；超了连同子进程一起被杀，"
                                "并明说是超时、把已产生的输出交给你。跑很久就调大，"
                                "或 nohup <cmd> > run.log 2>&1 & 起后台再轮询。"] = BASH_TIMEOUT,
        _b=Depends(get_binding)) -> dict:
    """跑一条命令。命令是唯一能改变世界的东西，一次一条，次数不限。"""
    _loop, store, nid, _node = _current(_b)
    cwd = os.getcwd()
    cmd = str(cmd or "")
    if not cmd.strip():
        return {"text": _action_result(store, nid, "bash", {"cmd": cmd},
                                       feedback.empty_cmd())}
    eff, pre = effects_of("bash", {"cmd": cmd}, cwd=cwd)
    declared = eff["fs"]["create"] + eff["fs"]["modify"]
    doomed = eff["fs"]["delete"]
    before = {p: os.path.exists(p) for p in declared + doomed}
    obs = str(await _run_bash(cmd, timeout=timeout))
    created, modified, deleted = _fs_actual(declared, doomed, before)
    eff["fs"] = {"create": created, "modify": modified, "delete": deleted}
    return _finish(store, nid, "bash", obs, eff, pre,
                   effects_args={"cmd": cmd},
                   tool_args={"cmd": cmd, "timeout": timeout},
                   created=created, modified=modified)


async def _run_bash(cmd, timeout=None):
    """跑一条命令：总是有超时，但超时可见、可调、会连子进程一起杀。真异步，不占线程。"""
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
        return feedback.tool_error(e)
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


@mcp.tool
async def read(path: Annotated[str, "要读的文件路径（相对工作区）。"],
               offset: Annotated[int, "从第几个字开始读。"] = 0,
               limit: Annotated[int, "最多读多少字。"] = READ_CAP,
               _b=Depends(get_binding)) -> dict:
    """读文件的一段，并明说这段在哪、还有多少。"""
    _loop, store, nid, _node = _current(_b)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            s = f.read()
    except OSError as e:
        obs = feedback.tool_error(e)
    else:
        n = len(s)
        start = max(0, int(offset or 0))
        cap = max(1, int(limit or READ_CAP))
        seg = s[start:start + cap]
        end = start + len(seg)
        head = "[%s 共 %d 字，本段 %d-%d]" % (path, n, start, end)
        if end < n:
            head += " 还有 %d 字未显示 —— read(offset=%d) 取下一段" % (n - end, end)
        obs = head + "\n" + seg
    eff, pre = effects_of("read", {"path": path}, cwd=os.getcwd())
    return _finish(store, nid, "read", obs, eff, pre,
                   effects_args={"path": path},
                   tool_args={"path": path, "offset": offset, "limit": limit})


@mcp.tool
async def write(path: Annotated[str, "要写的文件路径（相对工作区）。写文件是产出 —— "
                                    "结论里必须交代它。"],
                content: Annotated[str, "文件内容。"] = "",
                _b=Depends(get_binding)) -> dict:
    """写一个文件。产出会记进账本，conclude 时必须逐个交代。"""
    _loop, store, nid, _node = _current(_b)
    cwd = os.getcwd()
    ap = abs_path(path, cwd)
    existed = bool(ap) and os.path.exists(ap)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        obs = feedback.tool_error(e)
    else:
        obs = "written: %s (%d bytes)" % (path, len(content))
    eff, pre = effects_of("write", {"path": path}, cwd=cwd, existed_before=existed)
    created, modified, _ = _fs_actual([ap] if ap else [], [],
                                      before={ap: existed} if ap else {})
    return _finish(store, nid, "write", obs, eff, pre,
                   effects_args={"path": path},
                   tool_args={"path": path, "content": content},
                   created=created, modified=modified)


# ---------------------------------------------------------------- 驱动
_TOOLS = {}


async def run_tool(loop, nid, name, args):
    """Loop 驱动一次工具调用：绑定现场 → 跑 → 返回要写回对话的文本（None = 不写）。

    headroom_retrieve 不是 mcp.tool，在这里特判。
    """
    if name == RETRIEVE_NAME:
        return retrieve_original(args)
    tool = _TOOLS.get(name)
    if tool is None:
        tool = await mcp.get_tool(name)
        _TOOLS[name] = tool
    _binding.set((loop, nid))
    try:
        res = await tool.run(args)
    except ToolValidationError as e:
        return feedback.bad_shape(e)
    d = res.structured_content
    return d.get("text") if isinstance(d, dict) else None
