"""节点消息：把 Node 状态渲成模型看到的 user 消息 / trace 视图。

所有消息拼接都在这里，`class Node`（fields.py）只装数据与协议逻辑，不碰字符串。

两种视图（区分"给模型看"和"给人看"）：

  · `base_user(node)` —— 模型每次收到的**基础 user 消息**（字节稳定，节点出生后
    不变）：形式字段 + 意图链。历史不在这里 —— 它走**平铺对话**（`turn.ask` 把
    它和累积的 assistant / tool 消息拼一起），每个节点（分配节点和叶子一样）都是
    完整的 Loop，观测 / 尝试 / 下层结论以对话消息的形式逐条累积。
  · `full_view(node)` —— trace 里给人看的完整快照：基础消息 + 观测历史 / 本层
    已有尝试。模型不收到这份，只做记录。

`child_result(rec)` 是调度器把"一个下层节点的结论"注入父节点对话时用的那一条
（分配节点自己不看观测，它的观测 = 下层回话）。
"""

import json

# VIEW 是"一次给模型看多少历史"的**视图**预算，不是"限制模型写多少"。
# 它只影响 full_view（trace 给人看的快照）；线上走平铺对话 + 压缩，不截断。
VIEW = {"max_attempts_shown": 4, "max_obs_shown": 10,
        "max_obs_chars": 6000, "obs_entry": 1500}


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


def attempts(node):
    """分配节点的"本层已有尝试"视图（给 full_view / trace 用）。"""
    if not node.attempts:
        return "本层已有尝试: (还没有)"
    # 注：只列最近几次尝试（这是**条数**上的截断，会明说）；
    # 但每条里的判据和结论全文给出 —— 字数是模型自己的决定，代码不管。
    lim = VIEW["max_attempts_shown"]
    shown = node.attempts[-lim:]
    head = "本层已有尝试: 共 %d 次" % len(node.attempts)
    if len(node.attempts) > lim:
        head += "（下面只列最近 %d 次）" % lim
    lines = [head]
    for i, a in enumerate(shown, start=len(node.attempts) - len(shown) + 1):
        lines.append("  第 %d 次分配:" % i)
        for c in a.get("children", []):
            lines.append("    - %s" % spec_line(c))
        if a.get("rejected"):
            lines.append("    → 这次分配被代码拒了: %s" % a["rejected"])
            continue
        for r in a.get("results", []):
            lines.append("    ← %s｜%s｜%s"
                         % (r.get("name", ""), r.get("outcome", ""),
                            r.get("text", "")))
            if r.get("evidence"):
                lines.append("       证据: %s"
                             % "; ".join(str(x) for x in r["evidence"]))
        if a.get("outcome"):
            lines.append("    → %s" % a["outcome"])
    return "\n".join(lines)


def observations(node):
    """把观测历史讲给人看（full_view / trace）。

    两条纪律（都是修一个真 bug 换来的）：
      ① **截断必须可见** —— 静默截断会让模型以为"那就是全部输出"，
         实测它因此把同一个文件反复读了 25 次。
      ② 额度从最新往回给 —— 越近越完整。旧观测被压短是安全的
         （结论已经在别处），新观测被压短是致命的（它正要用）。
    线上模型不看这份（平铺对话 + 压缩代替）；这里只服务 trace。
    """
    if not node.observations:
        return "观测历史: (还没有)"
    shown = node.observations[-VIEW["max_obs_shown"]:]
    first = len(node.observations) - len(shown) + 1
    budget = VIEW["max_obs_chars"]
    rows = []
    for i in range(len(shown) - 1, -1, -1):
        o = shown[i]
        cap = max(200, min(VIEW["obs_entry"], budget))
        budget -= cap
        # 动作和观测一起算额度：否则一个很长的 write 参数会把观测挤没
        row = "%s → %s" % (str(o.get("action", "")), str(o.get("obs", "")))
        if len(row) > cap:
            row = row[:cap] + "…[截断：这一次共 %d 字]" % len(row)
        rows.append("  [%d] %s" % (first + i, row))
    rows.reverse()
    head = "观测历史: 共 %d 次" % len(node.observations)
    if first > 1:
        head += "（下面只列最近 %d 次）" % len(shown)
    return "\n".join([head] + rows)


def base_user(node):
    """模型每次收到的基础 user 消息：出生后永不变（字节稳定）。

    形式字段 + 意图链。观测 / 尝试 / 下层结论不在基础里 —— 它们走平铺对话
    （assistant/tool/user 消息逐条累积，`turn.ask` 拼接发送）。字节稳定 ⇒
    provider KV 缓存前缀命中，分配节点和叶子同构。
    """
    return "%s%s" % (header(node), lineage(node))


def full_view(node):
    """trace 里给人看的完整快照（模型不收到这份）。

    分配节点：基础 + 本层已有尝试；叶子：基础 + 手上的东西 + 观测历史。
    和 `base_user` 的区别：base 是线上实际发送的，这是给人/日志的记录。
    """
    base = base_user(node)
    if node.kind == "leaf":
        return "%s\n\n手上的东西: bash / read / write（永远都在）\n%s" % (
            base, observations(node))
    return "%s\n\n%s" % (base, attempts(node))


def child_result(rec):
    """一个下层节点的结论，注入父节点对话时的那一条（分配节点的"观测"）。"""
    line = "下层结论：%s｜%s｜%s" % (rec.get("name", ""), rec.get("outcome", ""),
                                  rec.get("text", ""))
    if rec.get("evidence"):
        line += "（证据：%s）" % "; ".join(str(x) for x in rec["evidence"])
    if rec.get("external"):
        line += "（外部需求：%s）" % "、".join(str(x) for x in rec["external"])
    return line
