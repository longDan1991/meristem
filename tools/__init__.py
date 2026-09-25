"""工具包：模型与程序之间唯一的通道。

- `specs`  工具注册表（`mcp` 实例 + fastmcp 的 tags 声明作用域）/ `ChildSpec` 形状 /
  作用域视图（`load` / `scope_names` / `action_names`）/ OpenAI 适配
- `defs`   `@mcp.tool` 工具注册壳（结构工具语义住 `core/runtime/ops.py`；read / write
  底层在本文，bash 在 `tools/bash.py`）+ `run_tool` 驱动

`defs` 在 import 时把工具注册进 `specs.mcp`，所以拿清单 / schema 前要先 `import tools.defs`
（loop 会做）；清单由 `specs.load()` 从注册表读出来（`openai_tools()` 会先加载）。
"""

from .specs import (ACTION_TAG, ChildSpec, action_names, load, mcp, openai_tools,
                    scope_names, scope_tag, scopes)

__all__ = ["ACTION_TAG", "ChildSpec", "action_names", "load", "mcp", "openai_tools",
           "scope_names", "scope_tag", "scopes"]
