"""tools 节：从 `tool_specs.NODE_TOOLS` 生成，一行一个工具 + 何时用哪个。

不重复工具描述 —— 签名 / 超时 / 语义住各自工具的 schema description；工具清单变这节跟着变。
"""

from ..protocol.tool_specs import NODE_TOOLS

# 每个工具的一行决策指导（"何时用哪个"），不是工具描述
_TOOL_GUIDE = {
    "create_children": "再拆一层：把任务拆成更小的子任务交给下层节点",
    "conclude": "出结论：判定这件事做没做完",
    "bash": "跑一条命令：要改变世界（装包 / 起进程 / 跑脚本）时用它",
    "read": "读文件的一段：要看已有内容时用它",
    "write": "写一个文件：要产出文件时用它",
    "submit_root": "把谈成的任务交出去当场跑（交形式 ≠ 退场）",
}


def tools_section(which):
    """tools 节：`which` 节点类型这次能调的工具清单。"""
    lines = []
    if which == "intake":
        lines.append("你每次回复二选一：")
    else:
        lines.append("你可以调用的工具（可以一次调用多个，它们并行执行）：")
    lines.append("")
    for name in NODE_TOOLS[which]:
        lines.append("  · %s —— %s" % (name, _TOOL_GUIDE[name]))
    return "\n".join(lines)
