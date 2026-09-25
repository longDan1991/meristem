"""条件节：`node.gate` 在场时的 skill 全文。

在场与否只在 `__init__.py` 的 `build_system_sections` 里判一次（看 Node 字段）。
`<skills>` 清单节恒在：内容来自 tools.skills.discovered()（扫描结果）。
"""

from tools import skills as _tskills


def skill_gate():
    """<skill_gate>：你是门槛（node.gate 时在场）。"""
    lines = []
    lines.append("你是门槛：这件事不先做，其余全是白做 —— 你不成立，"
                 "整个分支作废（兄弟全不启动）。")
    lines.append("所以更要给准话：拿不到就说拿不到，不要先报个满足。")
    return "\n".join(lines)


def skills_section():
    """<skills>：已注册技能的清单（恒在）。

    对齐 oh-my-pi：清单只放 name + description（检索面），正文按需经 read_skill 读
    `skill://<名字>/...` —— 不整节注入正文（skill 会随版本换代漂移，注入 = 每个节点
    白背无关内容）。清单来自 tools.skills.discovered()（扫描结果，非手写）。
    """
    items = _tskills.discovered()
    lines = []
    if not items:
        lines.append("暂无已注册技能。")
    for name, desc in items:
        lines.append("  · %s —— %s" % (name, desc))
    return "\n".join(lines)
