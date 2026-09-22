"""提示词：命名分节结构 —— system = `Record<节名, 内容>`，每节一个同名 XML 标签。

对齐 pi 的 `buildSystemPromptSections` / `renderSystem`（`system-prompt.ts`，
成熟宿主范式，见 `docs/PROMPTS.md`）：

  · system 不是拼好的字符串，是**命名分节的数据结构**。每节渲染成
    `<节名>\n内容\n</节名>`；`preamble` 无标签、放在最前。
  · 节名机器校验：必须匹配 `[a-z][a-z0-9_-]*`，违反当场报错（AGENTS §2 不掩盖）。
    设计文档表里的 `skill:gate` / `skill:compression` 带冒号通不过校验，
    条件节用下划线：`skill_gate` / `skill_compression`。
  · 节组成 = f(节点出生时静态属性)：恒在的 preamble / process / tools / rules / input
    + 条件节 `skill_gate`（`node.gate`）/ `skill_compression`（`cfg.COMPRESS` 且叶子）。
    节点生命周期内不变 → system 字节稳定 → provider KV 缓存按节命中。
  · 节内容**直接写在代码里**（没有 .md 文件）：散文节在 `prose.py`、条件节在
    `skills.py`、tools / rules 两节从 `tool_specs.NODE_TOOLS` 的工具清单推导
    （工具清单变，操作纪律跟着变，docs/PROMPTS.md §4.2）。

**system 不走 @mcp.prompt，也不和 user 消息混装**：`render_turn` 直接把
[system, 基础 user] 两条分开返回（分配节点和叶子同构）；节点的累积历史
（观测 / 尝试 / 下层结论）是**平铺对话**，由 `turn.node_hooks` 在基础消息后面拼接
（每个节点都是完整的 Loop，`turn.py` 里所有节点统一维护 st["msgs"]）。

本文件只做三件事：按在场规则组装节（`build_system_sections`）、把节渲染成
system 文本（`render_system`）、产出线上 wire（`render_turn`）。节点消息的
拼接在 `messages.py`（class Node 不碰字符串）。

每条硬性要求都对应 `tree/protocol/gate.py` 里的一处代码检查 —— 改一边就得看另一边：

    "除 notes 外全部必填"        →  clean_spec：缺一个当场拒
    "必须携带父的可测物理量"      →  inherits + 根锚点，当场拒绝
    "最多一个门槛"                →  门槛先做，不成立则分支作废
    "判定满足必须指得出证据"      →  指不出来就降级为未满足
    kind                          →  clean_spec：只能是 dispatch / leaf，不给兜底
    外部需求四类                  →  EXTERNAL_CLASSES（tree/protocol/fields.py）
    字段的"本质"                  →  tool_specs.py 的 schema description（provider 原样喂模型）

入口（`prompts/prose.py` 的 intake 三节）是同一个协议的第一环：它交出来的
`root` 要过 `clean_spec` 加"验收标准必须有可测物理量"，所以它不可能塞进树
检查不了的东西。

设计与不变量的完整版在 `docs/PROMPTS.md`；进度与交接在 `docs/HANDOVER.md`。
"""

import re

from .. import config as cfg
from ..protocol.tool_specs import NODE_TOOLS
from .messages import base_user
from .prose import prose
from .rules import rules_section
from .skills import skill_compression, skill_gate
from .tools import tools_section

__all__ = ["render_turn", "build_system_sections", "render_system"]

# 节名机器校验（pi 的 SYSTEM_PROMPT_SECTION_NAME，见 docs/PROMPTS.md §3.3）。
SECTION_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def build_system_sections(which, node=None):
    """返回 Record<节名, 内容>（pi 的 SystemPromptSections）。

    `which` = alloc / leaf / intake；`node` = 该节点（intake 没有）。节组成
    只看节点出生时已知的静态属性（kind / gate / cfg.COMPRESS），生命周期内不变。
    返回的 dict 按固定顺序插入（docs/PROMPTS.md §3.1 表自上而下：preamble /
    process / tools / rules / input / skill_gate / skill_compression），
    render_system 照 dict 顺序渲染，KV 缓存按节命中稳定。
    """
    if which not in NODE_TOOLS:
        raise ValueError("未知节点类型: %r（可用：%s）"
                         % (which, " / ".join(NODE_TOOLS)))
    s = {"preamble": prose(which, "preamble"),
         "process": prose(which, "process"),
         "tools": tools_section(which),
         "rules": rules_section(which),
         "input": prose(which, "input")}
    if node is not None and getattr(node, "gate", False):
        s["skill_gate"] = skill_gate()
    if which == "leaf" and cfg.COMPRESS:
        s["skill_compression"] = skill_compression()
    return s


def render_system(sections):
    """Record<节名, 内容> → system 文本：每节包 `<节名>` 标签，preamble 无标签最前。

    节名违反 `[a-z][a-z0-9_-]*` 当场报错（不掩盖）。顺序按 dict 插入顺序
    （build_system_sections 已按固定顺序排好）。
    """
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


def render_turn(which, node=None):
    """一个节点回合的线上消息（dict 列表，直接喂 litellm）。

    **system 与 user 分开**：第一条是 system（分节文本，经 render_system），
    第二条是基础 user 消息（形式字段 + 意图链，字节稳定，见 messages.base_user）。
    不注册 FastMCP prompt、不混装 —— 节点的累积历史由 `turn.node_hooks` 在基础消息
    后面拼平铺对话（每个节点都是完整的 Loop）。
    intake 没有节点消息（它的 user 是用户说的话，在对话里），只给 system。
    """
    wire = [{"role": "system",
             "content": render_system(build_system_sections(which, node))}]
    if which != "intake":
        wire.append({"role": "user", "content": base_user(node)})
    return wire
