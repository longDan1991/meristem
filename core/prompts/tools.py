"""tools 节：一行一个工具 + 何时用哪个；清单从工具的作用域声明派生（`scope_names`）。

不重复工具描述 —— 签名 / 超时 / 语义住各自工具的 schema description；工具清单变这节跟着变。
每个工具都必须在这里有一行"何时用哪个"，缺了当场报错（清单是工具的，指导是提示词的，
两边的对齐靠这条检查，不靠记性）。
"""

from core.protocol.fields import INTAKE
from tools import scope_names

# 每个工具的一行决策指导（“何时用哪个”）；工具“是什么”住各自 `@mcp.tool` 的 docstring，不在这重复。
# 表必须覆盖每个作用域里的每个工具（测试核对），缺了 `tools_section` 当场报错。
TOOL_GUIDE = {
    "create_children": "任务能再拆、自己不该硬做时",
    "conclude": "做完了 / 判定做不了时",
    "bash": "要改变世界（装包 / 起进程 / 跑脚本）时",
    "read_skill": "要读已注册 skill 的全文 / 子文件（清单节列出的技能）时",
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
    for name in scope_names(which):
        if name not in TOOL_GUIDE:
            raise ValueError("工具 %r 没有给模型的决策指导：在 TOOL_GUIDE 里补一行" % name)
        lines.append("  · %s —— %s" % (name, TOOL_GUIDE[name]))
    return "\n".join(lines)
