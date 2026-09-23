"""工具包：模型与程序之间唯一的通道。

- `specs`  工具清单 / `ChildSpec` 形状 / `mcp` 实例 / OpenAI 适配（唯一事实 `NODE_TOOLS`）
- `defs`   `@mcp.tool` 工具实现（schema 与实现一体，含 bash / read / write 的底层逻辑）+ `run_tool` 驱动

`defs` 在 import 时把工具注册进 `specs.mcp`，所以拿 schema 前要先 `import tools.defs`。
"""

from .specs import ACTION_TOOLS, NODE_TOOLS, ChildSpec, allowed_names, openai_tools

__all__ = ["ACTION_TOOLS", "NODE_TOOLS", "ChildSpec", "allowed_names", "openai_tools"]
