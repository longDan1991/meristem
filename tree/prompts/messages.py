"""节点消息：把 Node 状态渲成模型收到的 user 消息。

所有消息拼接都在这里，`class Node`（fields.py）只装数据与协议逻辑，不碰字符串。

  · `base_user(node)` —— 模型每次收到的**基础 user 消息**（字节稳定，节点出生后
    不变）：形式字段 + 意图链。历史不在这里 —— 它走**平铺对话**（`turn.node_hooks`
    它和累积的 assistant / tool 消息拼一起），每个节点（分配节点和叶子一样）都是
    完整的 Loop，观测 / 尝试 / 下层结论以对话消息的形式逐条累积。

历史不渲染成视图：trace 里每条工具动作都有 `tool` 事件原文，节点每回合发出去
的基础消息记 `%s_in` 事件 —— 线上模型看的是平铺对话里的 tool 消息。

`child_result(rec)` 是调度器把"一个下层节点的结论"注入父节点对话时用的那一条
（分配节点自己不看观测，它的观测 = 下层回话）。注入的文本带 `（id:…）` 标记 ——
恢复时（`runtime/reconcile.py` 的 `result_ids`）靠它判断"哪个孩子的结论已经投递"。
"""

import json
import re

# child_result 注入文本里的孩子 id 标记。8 位 hex，和 Node.id 同源。
_RESULT_ID = re.compile(r"（id:([0-9a-f]{6,16})）")
# 下层结论行的开头（名字在「｜」之前）。
_CHILD_NAME = re.compile(r"下层结论：([^｜]+)｜")


def result_ids(msgs):
    """一份对话里已经回填过的下层结论 id（投递判断用）。

    多个孩子并行完工时结论会并进同一条 user 消息，所以要扫全部消息、
    每条里找所有标记。"""
    out = set()
    for m in msgs:
        if m.get("role") == "user":
            out |= set(_RESULT_ID.findall(str(m.get("content") or "")))
    return out


def result_names(msgs):
    """对话里出现过的下层结论名字（结论审计的证据校验用）。"""
    out = set()
    for m in msgs:
        if m.get("role") == "user":
            out |= set(_CHILD_NAME.findall(str(m.get("content") or "")))
    return out


def as_json(v):
    """值按 JSON 形状渲染（数组就是数组，假就是 false），空写 (无)。

    收到的行和模型要写出去的 JSON 必须是同一套值形状 —— 否则它得先猜
    "逗号分隔的一串算不算数组"，而这正是漂移的开始。
    """
    if v is None or v == "" or v == []:
        return "(无)"
    return json.dumps(v, ensure_ascii=False)


def spec_line(c):
    """一次分配里的一个子任务 —— 按**它自己输出的那套键**列出来。

    历史里看到的是自己写过的形式，不是另一套中文标签：同一个词在"收到的"
    和"写回去的"两边指同一个东西，模型不用做翻译。
    """
    return " | ".join([
        "name: %s" % (c.get("name") or "(无)"),
        "kind: %s" % (c.get("kind") or "(无)"),
        "gate: %s" % as_json(bool(c.get("gate"))),
        "conc_range: %s" % as_json(c.get("conc_range")),
        "accept: %s" % (c.get("accept") or "(无)")])


def header(node):
    """形式字段 —— **行首就是字段名**，和模型自己写给孩子的键一模一样。

    这是"收到的东西与要交出去的东西同构"：同一个词既在收到的行首，
    也在它输出的 JSON 里，中间没有"中文标签 → 键"的翻译层可漂移。
    哪一行是谁给的（上层给的 / 程序查出来的）由 `tree/prompts/prose.py` 的
    input 节说，不放进行内 —— 行内只留键和值。
    """
    return "\n".join([
        "name: %s" % (node.name or "(无)"),
        "detail: %s" % (node.detail or "(无)"),
        "notes: %s" % (node.notes or "(无)"),
        "accept: %s" % (node.accept or "(无)"),
        "kind: %s" % (node.kind or "(无)"),
        "gate: %s" % as_json(bool(node.gate)),
        "conc_range: %s" % as_json(node.conc_range)])


def lineage(node):
    """从根到自己的上层的意图链（程序物化的，不是上层下发的字段）。

    没有它，节点只知道"我要干什么"，不知道"这件事为什么值得做" ——
    拆到第三层就没人记得最初的验收标准是给谁用的了。**两种节点都渲染**。
    """
    if not node.lineage:
        return ""
    lines = ["上层意图链（从根到你上层，只读）:"]
    for i, (name, detail) in enumerate(node.lineage, start=1):
        lines.append("  %d. %s: %s" % (i, name, detail or "(无)"))
    return "\n\n" + "\n".join(lines)


def base_user(node):
    """模型每次收到的基础 user 消息：出生后永不变（字节稳定）。

    形式字段 + 意图链。观测 / 尝试 / 下层结论不在基础里 —— 它们走平铺对话
    （assistant/tool/user 消息逐条累积，`turn.node_hooks` 拼接发送）。字节稳定 ⇒
    provider KV 缓存前缀命中，分配节点和叶子同构。
    """
    return "%s%s" % (header(node), lineage(node))


def child_result(rec):
    """一个下层节点的结论，注入父节点对话时的那一条（分配节点的"观测"）。

    末尾带 `（id:…）` 标记：恢复时据此判断这个孩子的结论投递过没有
    （`result_ids`）。崩溃窗口（孩子出了结论、投递给父节点前崩了）靠它补齐。"""
    line = "下层结论：%s｜%s｜%s" % (rec.get("name", ""), rec.get("outcome", ""),
                                  rec.get("text", ""))
    if rec.get("evidence"):
        line += "（证据：%s）" % "; ".join(str(x) for x in rec["evidence"])
    if rec.get("external"):
        line += "（外部需求：%s）" % "、".join(str(x) for x in rec["external"])
    return "%s（id:%s）" % (line, rec.get("id", ""))
