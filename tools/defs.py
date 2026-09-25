"""工具：模型与程序之间唯一的通道，实现就是 `@mcp.tool` 函数（schema 与实现一体）。

每个工具在声明处用 fastmcp 的 `tags` 说自己属于哪些作用域（`scope_tag(...)` 给的是
`scope:<层>` 标签，清单由 `tools.specs` 让库的可见性过滤算出来）—— 本文不再另列一份工具清单。
`action` 标签的是动手工具（证据审计里的"观测"）。

结构类工具（create_children / conclude / submit_root）的语义住 `core/runtime/ops.py`
（协议操作层，与 gate.py 同一变因），这里只留注册壳与参数适配；read / write 的实现在
本文，bash 独立在 `tools/bash.py`（schema 照抄 oh-my-pi），import 即注册。
共享的工具现场（ContextVar / 记 trace）在 `tools/context.py`；每次调用由 Loop 用
`run_tool` 驱动，`(loop, nid)` 经 ContextVar 注入，各 asyncio task 独立所以并行调用不串。

返回 `{"text": ...}`：None = 结构类工具成功、不写 tool 回话；字符串 = 观测 / 拒绝理由。
"""

from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from core.protocol import feedback
from core.protocol.fields import ALLOC, INTAKE, LEAF
from core.runtime import ops
from tools import bash as _bash  # noqa: F401  # import 即把 bash 工具注册进 mcp（实现在 tools/bash.py）
from tools import skills as _skills  # noqa: F401  # import 即挂载 SkillProvider + 注册 read_skill（实现在 tools/skills.py）
from tools.context import _action_result, _binding, _current, get_binding
from tools.specs import ACTION_TAG, ChildSpec, action_names, mcp, scope_tag

READ_CAP = 2000


# ---------------------------------------------------------------- 结构类工具（注册壳）
@mcp.tool(tags={scope_tag(ALLOC)})
async def create_children(children: list[ChildSpec],
                          _b=Depends(get_binding)) -> dict:
    """把任务拆成更小的子任务交给下层节点（调它 = 再拆一层）。

    有门槛时只有门槛孩子拿到任务，其余对话为空 = 暂缓；成功不写 tool 回话。
    """
    _loop, store, nid, _node = _current(_b)
    return {"text": ops.create_children(store, nid,
                                        [c.model_dump() for c in children])}


@mcp.tool(tags={scope_tag(ALLOC), scope_tag(LEAF)})
async def conclude(
        verdict: Annotated[str, feedback.VERDICT_HINT],
        text: Annotated[str, "结论正文，落在上层给的 conc_range 区间里。"],
        evidence: Annotated[list[str] | None,
                            "判定「满足」时必填：第几次观测 / 产物路径 / 子任务 name。"] = None,
        external: Annotated[str, "判定「阻塞」时：" + feedback.EXTERNAL_HINT + "。"] = "",
        _b=Depends(get_binding)) -> dict:
    """出结论：判定这件事做没做完。判定「满足」必须指得出真证据。"""
    _loop, store, nid, _node = _current(_b)
    return {"text": ops.conclude(store, nid, verdict, text, evidence or [],
                                 external, action_tools=action_names())}


@mcp.tool(tags={scope_tag(INTAKE)})
async def submit_root(root: ChildSpec, _b=Depends(get_binding)) -> dict:
    """把谈成的任务交出去当场跑。返回后任务树开始长，跑完结论回到对话。"""
    loop, store, nid, _node = _current(_b)
    return {"text": ops.submit_root(loop, store, nid, root.model_dump())}


# ---------------------------------------------------------------- 三只手
# bash 独立在 tools/bash.py（schema 照抄 oh-my-pi），import 即注册；这里只剩 read / write。
@mcp.tool(tags={scope_tag(LEAF), ACTION_TAG})
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
    return {"text": _action_result(store, nid, "read",
                                   {"path": path, "offset": offset, "limit": limit},
                                   obs)}


@mcp.tool(tags={scope_tag(LEAF), ACTION_TAG})
async def write(path: Annotated[str, "要写的文件路径（相对工作区）。写文件是产出 —— "
                                    "结论里必须交代它。"],
                content: Annotated[str, "文件内容。"] = "",
                _b=Depends(get_binding)) -> dict:
    """写一个文件。写文件是产出，conclude 时必须逐个交代。"""
    _loop, store, nid, _node = _current(_b)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        obs = feedback.tool_error(e)
    else:
        obs = "written: %s (%d bytes)" % (path, len(content))
    return {"text": _action_result(store, nid, "write",
                                   {"path": path, "content": content}, obs)}


# ---------------------------------------------------------------- 驱动
_TOOLS = {}


async def run_tool(loop, nid, name, args):
    """Loop 驱动一次工具调用：绑定现场 → 跑 → 返回要写回对话的文本（None = 不写）。"""
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
