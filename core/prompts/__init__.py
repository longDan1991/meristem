"""提示词：命名分节结构 —— system = `Record<节名, 内容>`，每节一个同名 XML 标签。

system 是分节的数据结构而不是拼好的字符串：每节渲染成 `<节名>\n内容\n</节名>`，
preamble 无标签放最前；节名必须匹配 `[a-z][a-z0-9_-]*`，违反当场报错。

节组成 = f(节点出生时静态属性)：恒在的 preamble / process / tools / rules / input ——
生命周期内不变 ⇒ system 字节稳定 ⇒ provider KV 缓存按节命中。内容写在代码里，
散文在 `prose.py`、skills 清单在 `skills.py`、tools / rules 从工具的作用域声明派生。

`render_turn` 只返回 system；节点的任务（`base_user`）在平铺对话 msgs[0] 里，
发模型前由 `runtime/loop._build_wire` 拼成 wire（没回话的 tool_call 补占位）。
"""

import re

from tools import scope_names
from .prose import prose
from .rules import rules_section
from .skills import skills_section
from .tools import tools_section

__all__ = ["render_turn", "build_system_sections", "render_system"]

# 节名机器校验（pi 的 SYSTEM_PROMPT_SECTION_NAME）
SECTION_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def build_system_sections(which):
    """返回 Record<节名, 内容>；`which` = alloc / leaf / intake。

    节组成只看出生时已知的静态属性（kind），dict 按固定顺序插入，
    render_system 照顺序渲染，KV 缓存按节命中稳定。
    """
    scope_names(which)      # 未知作用域当场报 ValueError（prose 只会给 KeyError，不是给调用方的契约）
    return {"preamble": prose(which, "preamble"),
            "process": prose(which, "process"),
            "tools": tools_section(which),
            "rules": rules_section(which),
            "skills": skills_section(),
            "input": prose(which, "input")}


def render_system(sections):
    """Record<节名, 内容> → system 文本：每节包 `<节名>` 标签，preamble 无标签最前；节名不合法当场报错。"""
    out = []
    for name, content in sections.items():
        text = str(content).strip()
        if name == "preamble":
            out.append(text)
            continue
        if not SECTION_NAME_RE.match(name):
            raise ValueError("节名 %r 不合法（必须是 [a-z][a-z0-9_-]*）" % name)
        out.append("<%s>\n%s\n</%s>" % (name, text, name))
    return "\n\n".join(out)


def render_turn(which):
    """一个节点发给模型的 system 消息，只给 system；任务消息与历史都在它自己的平铺对话里。"""
    return [{"role": "system",
             "content": render_system(build_system_sections(which))}]
