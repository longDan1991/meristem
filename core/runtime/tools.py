"""工具：模型与程序之间唯一的通道，实现就是 `@mcp.tool` 函数（schema 与实现一体）。

  · alloc    create_children / conclude
  · leaf     bash / read / write / conclude
  · intake   submit_root

每次调用由 Loop 用 `run_tool` 驱动：先把 `(loop, nid)` 写进 ContextVar，工具函数
经 `Depends(get_binding)` 拿到自己的运行时现场（store / 节点 / 手）。每个 asyncio
task 的 contextvars 独立，所以并行调用的工具各拿各的现场，不串（AGENTS §9 无锁）。

工具返回 `{"text": <给模型看的回话>}`：`None` = 结构类工具成功、不写 tool 回话
（等待由数据表达）；字符串 = 观测 / 拒绝理由，写成一条 tool 回话。
"""

import contextvars
import os
from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from ..compression import RETRIEVE_NAME, retrieve_original
from ..effects import effects_of
from ..protocol.gate import anchors, clean_conclusion, clean_spec, inherits, validate_root
from ..protocol.tool_specs import ChildSpec, mcp
from ..prompts import feedback
from ..prompts.feedback import gate_failed
from ..prompts.messages import base_user, child_result, result_ids
from ..tools import bash as _bash, read as _read, write as _write
from .plan import make_child

# Loop 调用工具前写入 (loop, nid)；工具函数用 Depends 注入。
_binding = contextvars.ContextVar("tool_binding", default=None)


def get_binding():
    return _binding.get()


def _current(binding):
    loop, nid = binding
    return loop, loop.store, nid, loop.store.registry[nid]


def _root_anchors(node, registry):
    """任务根（入口节点的孩子 / 无父节点）的可测物理量。"""
    cur = node
    while cur.parent:
        p = registry.get(cur.parent)
        if p is None or p.kind == "intake":
            break
        cur = p
    return anchors(cur.accept)


def _record_effects(store, nid, tool, args, eff, pre, created, modified):
    store.record(nid, "effects", {"tool": tool, "args": args,
                                  "wrote": created + modified,
                                  "effects": eff, "前置条件": pre})


def _action_result(store, nid, tool, args, obs):
    """一次动作的收尾：把事实记进 trace，返回给模型看的观测文本。"""
    store.record(nid, "tool", {"tool": tool, "args": args, "obs": str(obs)})
    return obs


# ---------------------------------------------------------------- 结论的语义
# conclude 工具自己在 Store 上做的事：落 verdict → 门槛续跑/作废 →
# 扫父节点：孩子都出结论了就把结果逐条拼回父节点对话（不需要任何额外结构）。
def _deferred(store, parent):
    """父节点上还没启动的孩子：对话为空（任务还没拼进来）、又没有结论。"""
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
    if node.verdict == "满足":
        for c in deferred:
            store.append_user(c.id, base_user(c))
        store.record(parent.id, "gate_passed",
                     {"gate": node.name, "started": [c.name for c in deferred]})
    else:
        for c in deferred:
            store.set_verdict(c.id, "未启动", gate_failed(node.conclusion), [], [])
        store.record(parent.id, "gate_failed",
                     {"gate": node.name, "reason": node.conclusion,
                      "skipped": [c.name for c in deferred]})


def _push_results(store, pid):
    """父节点的孩子都出结论了 → 逐条拼回父节点对话（幂等）。"""
    parent = store.registry.get(pid)
    if parent is None or not parent.children:
        return
    kids = [store.registry.get(c) for c in parent.children]
    if any(k is None or not k.verdict for k in kids):
        return                                     # 还有孩子没结论 → 等
    seen = result_ids(store.dialogue(pid).to_list())
    for k in kids:
        if k.id not in seen:
            store.append_user(pid, child_result(k.record()))


# ---------------------------------------------------------------- 结构类工具
@mcp.tool
async def create_children(children: list[ChildSpec],
                          _b=Depends(get_binding)) -> dict:
    """把任务拆成更小的子任务交给下层节点。调它 = 再拆一层。

    有门槛时只有门槛孩子拿到任务（其余对话为空 = 暂缓）；门槛通过时它们才被
    拼上任务。成功不写 tool 回话（父节点停在 assistant，等孩子结论回来）。
    """
    _loop, store, nid, node = _current(_b)
    specs, reject = [], None
    for raw in [c.model_dump() for c in children]:
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        ra = _root_anchors(node, store.registry)
        if not (inherits(node.accept, s["accept"])
                and ((not ra) or any(x in s["accept"] for x in ra))):
            reject = feedback.criterion_drift(ra or anchors(node.accept))
            store.record(nid, "criterion_drift",
                         {"child": s["name"], "accept": s["accept"],
                          "root_anchors": sorted(ra)})
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
        verdict: Annotated[str, "满足 | 未满足 | 阻塞"],
        text: Annotated[str, "结论正文，落在上层给的 conc_range 区间里。"],
        evidence: Annotated[list[str] | None,
                            "判定「满足」时必填：第几次观测 / 产物路径 / 子任务 name。"] = None,
        external: Annotated[str, "判定「阻塞」时：需要人到场 / 需要真实账户 / "
                                 "需要真实资金 / 需要现实设备。"] = "",
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
                                "或 nohup <cmd> > run.log 2>&1 & 起后台再轮询。"] = 120,
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
    existed = {p: os.path.exists(p) for p in declared}
    doomed = eff["fs"]["delete"]
    doomed_existed = {p: os.path.exists(p) for p in doomed}
    obs = str(await _bash(cmd, timeout=timeout))
    created = [p for p in declared if not existed[p] and os.path.exists(p)]
    modified = [p for p in declared if existed[p] and os.path.exists(p)]
    deleted = [p for p in doomed if doomed_existed[p] and not os.path.exists(p)]
    eff["fs"] = {"create": created, "modify": modified, "delete": deleted}
    _record_effects(store, nid, "bash", {"cmd": cmd}, eff, pre, created, modified)
    return {"text": _action_result(store, nid, "bash",
                                   {"cmd": cmd, "timeout": timeout}, obs)}


@mcp.tool
async def read(path: Annotated[str, "要读的文件路径（相对工作区）。"],
               offset: Annotated[int, "从第几个字开始读。"] = 0,
               limit: Annotated[int, "最多读多少字。"] = 2000,
               _b=Depends(get_binding)) -> dict:
    """读文件的一段，并明说这段在哪、还有多少。"""
    _loop, store, nid, _node = _current(_b)
    obs = str(_read(path, offset=offset, limit=limit))
    eff, pre = effects_of("read", {"path": path}, cwd=os.getcwd())
    store.record(nid, "effects", {"tool": "read", "args": {"path": path},
                                  "effects": eff, "前置条件": pre})
    return {"text": _action_result(store, nid, "read",
                                   {"path": path, "offset": offset, "limit": limit}, obs)}


@mcp.tool
async def write(path: Annotated[str, "要写的文件路径（相对工作区）。写文件是产出 —— "
                                    "结论里必须交代它。"],
                content: Annotated[str, "文件内容。"] = "",
                _b=Depends(get_binding)) -> dict:
    """写一个文件。产出会记进账本，conclude 时必须逐个交代。"""
    _loop, store, nid, _node = _current(_b)
    cwd = os.getcwd()
    ap = path if path.startswith("/") else os.path.normpath(os.path.join(cwd, path))
    existed = os.path.exists(ap)
    obs = str(_write(path, content))
    eff, pre = effects_of("write", {"path": path}, cwd=cwd, existed_before=existed)
    created = [ap] if (not existed and os.path.exists(ap)) else []
    modified = [ap] if (existed and os.path.exists(ap)) else []
    _record_effects(store, nid, "write", {"path": path}, eff, pre, created, modified)
    return {"text": _action_result(store, nid, "write",
                                   {"path": path, "content": content}, obs)}


# ---------------------------------------------------------------- 驱动
_TOOLS = {}


async def run_tool(loop, nid, name, args):
    """Loop 驱动一次工具调用：绑定现场 → 跑 → 返回要写回对话的文本（None = 不写）。

    headroom_retrieve 不是 mcp.tool（它是压缩库的取回入口），在这里特判。
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
