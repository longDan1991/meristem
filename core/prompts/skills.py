"""<skills> 清单节：已注册技能的 name + description，恒在。

清单来自 `tools.skills.discovered()`（扫描结果，非手写）。全文按需经 read_skill 读
`skill://<名字>/...` —— 不整节注入正文（skill 会随版本换代漂移，注入 = 每个节点
白背无关内容）。
"""

from tools import skills as _tskills


def skills_section():
    """<skills>：已注册技能的清单（恒在）。

    对齐 oh-my-pi：清单只放 name + description（检索面），正文按需经 read_skill 读
    `skill://<名字>/...`。"""
    items = _tskills.discovered()
    lines = []
    if not items:
        lines.append("暂无已注册技能。")
    for name, desc in items:
        lines.append("  · %s —— %s" % (name, desc))
    return "\n".join(lines)
