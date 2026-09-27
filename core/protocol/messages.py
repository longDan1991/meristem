"""节点消息：把 Node 状态渲成模型收到的 user 消息；所有消息拼接都在这里，class Node 不碰字符串。

`base_user(node)` 是节点每次收到的任务消息（形式字段 + 意图链），出生时拼进 `msgs[0]`，
之后 assistant / tool / user 逐条累积。`intake_seed(task)` 是入口根的第一条（用户原话 +
"验收标准由你提"），也在出生时拼进 `msgs[0]`。

`comm_content(...)` 是 communicate 消息的正文：来源 + 内容 + 可选的回复长度要求。
消息进对方对话时带 `from` 键（发送者 id）—— 终端渲染与恢复靠它，发射时由
`dialogue.pair()` 剥掉（OpenAI 不认识这个键，账本里才有）。

变因：协议字段与消息格式 —— FORM_FIELDS 变了 / 消息格式改了，只动这里。
"""

import json

from .fields import FORM_FIELDS

# 空值的统一写法：字段渲染与 as_json 共用。
EMPTY = "(无)"


def as_json(v):
    """值按 JSON 形状渲染（数组就是数组，假就是 false），空写 (无) —— 收到的与要写出去的必须同套形状。"""
    if v is None or v == "" or v == []:
        return EMPTY
    return json.dumps(v, ensure_ascii=False)


def _text(v):
    """文本字段：空写 (无)。"""
    return v or EMPTY


# 每个键怎么渲染：形状特殊的在这里（布尔按 JSON 的 true/false、区间按数组），其余当文本。
_RENDER = {"gate": lambda v: as_json(bool(v)), "conc_range": as_json}


def header(node):
    """形式字段：行首就是字段名，和模型写给孩子的键一模一样（收到与交出去的同构）。

    键清单来自 `FORM_FIELDS`（协议层的形式字段）—— 加一个字段这里跟着走，不另抄一份；
    哪一行是谁给的由 `prose.py` 的 input 节说，行内只留键和值。
    """
    return "\n".join("%s: %s" % (k, _RENDER.get(k, _text)(getattr(node, k)))
                     for k in FORM_FIELDS)


def lineage(node):
    """从根到自己的上层的意图链（程序物化）：没有它，拆到第三层就没人记得最初的意图。"""
    if not node.lineage:
        return ""
    lines = ["上层意图链（从根到你上层，只读）:"]
    for i, (name, detail) in enumerate(node.lineage, start=1):
        lines.append("  %d. %s: %s" % (i, name, detail or EMPTY))
    return "\n\n" + "\n".join(lines)


def base_user(node):
    """模型每次收到的基础 user 消息（形式字段 + 意图链），出生后字节稳定，能命中 provider KV 缓存。

    观测 / 尝试 / 沟通消息不在基础里，它们走平铺对话。
    """
    return "%s%s" % (header(node), lineage(node))


def intake_seed(task):
    """入口根的第一条用户消息：只写用户真的说了什么，验收标准永远要入口自己提。"""
    return ("用户的任务: %s\n"
            "验收标准: 用户没给 —— 正常，真用户都不会给。"
            "那是你的活：从他的话里提一条具体的写法，让他点头或改一个数。" % task)


def comm_content(sender_name, text, conc_range=None):
    """一条沟通消息的正文：来源 + 内容 + 可选的回复长度要求（进对方的对话）。"""
    lines = ["来自「%s」的消息：" % (sender_name or "?"), str(text or "")]
    if conc_range:
        lines.append("（要求回复长度：%d-%d 字）" % tuple(conc_range))
    return "\n".join(lines)
