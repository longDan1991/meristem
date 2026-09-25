"""一次工具调用的现场：Loop 在 `run_tool` 里把 `(loop, nid)` 写进 ContextVar，工具函数经
`Depends(get_binding)` 注入。各 asyncio task 的 ContextVar 独立，所以并行调用不串。

`_action_result` 是动作的收尾：把 tool 调用 + 观测记进 trace，返回给模型看的观测文本。
所有 `@mcp.tool` 实现（bash / read / write / 结构类工具）共用这一份现场。
"""

import contextvars

# Loop 调用工具前写入 (loop, nid)；工具函数用 Depends 注入。
_binding = contextvars.ContextVar("tool_binding", default=None)


def get_binding():
    return _binding.get()


def _current(binding):
    loop, nid = binding
    return loop, loop.store, nid, loop.store.registry[nid]


def _action_result(store, nid, tool, args, obs):
    """一次动作的收尾：把事实记进 trace，返回给模型看的观测文本。"""
    store.record(nid, "tool", {"tool": tool, "args": args, "obs": str(obs)})
    return obs
