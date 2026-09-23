"""tools 节：从 `tools.specs.NODE_TOOLS` 生成，一行一个工具 + 何时用哪个。

不重复工具描述 —— 签名 / 超时 / 语义住各自工具的 schema description；工具清单变这节跟着变。
"""

from ..protocol.fields import INTAKE
from tools import NODE_TOOLS

# 每个工具的一行决策指导（“何时用哪个”）；工具“是什么”住各自 @mcp.tool 的 docstring，不在这重复。
_TOOL_GUIDE = {
    "create_children": "任务能再拆、自己不该硬做时",
    "conclude": "做完了 / 判定做不了时",
    "bash": "要改变世界（装包 / 起进程 / 跑脚本）时",
    "read": "要看已有内容时",
    "write": "要产出文件时",
    "submit_root": "和用户谈拢了预期时（交形式 ≠ 退场）",
}


def tools_section(which):
    """tools 节：`which` 节点类型这次能调的工具清单。"""
    lines = []
    if which == INTAKE:
        lines.append("你每次回复二选一：")
    else:
        lines.append("你可以调用的工具（可以一次调用多个，它们并行执行）：")
    lines.append("")
    for name in NODE_TOOLS[which]:
        lines.append("  · %s —— %s" % (name, _TOOL_GUIDE[name]))
    return "\n".join(lines)
