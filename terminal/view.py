"""树的视图：把一棵 Node 树画成一串带树形标记的行（给人看）。

树长什么样是展示的变因，所以住终端层、不碰协议字段序列化：字段形状变了这里只是少画/多画一行。
"""

from core.protocol.fields import SATISFIED


def render_tree(root, registry, prefix="", is_last=True, lines=None, streams=None,
                compact=False):
    """整棵树的视图：每层的拆分 / 判定 / 结论，画成一串带树形标记的行。

    根是入口，registry 是登记的全部节点（id → Node）；运行中画 ·，出结论按状态画 ✓ / ✗。
    streams 是可选的活动节点吐字尾巴（node_id → {"thinking", "speaking"}），正在吐字就在它下面补一行 ▸。

    compact=True 是实时视图：每个节点一行，运行中的把正在吐的字并排带上，出结论的并排带上判定 + 验收标准。
    """
    b = "└─ " if is_last else "├─ "
    # 没有 status 字段：verdict 非空就是终态，否则运行中
    mark = "✓" if root.verdict == SATISFIED else ("✗" if root.verdict else "·")
    if lines is None:
        lines = []
    tag = "%s%s" % ({"dispatch": "[分配]", "leaf": "[叶子]"}.get(root.kind, "[入口]"),
                     " [门槛]" if root.gate else "")
    if compact:
        # 实时视图：一行一个节点，正在说什么就显示什么（结论留到跑完的详细帧）
        if not root.verdict:
            extra = ""
            if streams:
                s = streams.get(root.id)
                if s:
                    if s.get("speaking"):
                        extra = "  ▸ 说: %s" % s["speaking"]
                    elif s.get("thinking"):
                        extra = "  ▸ 思考: %s" % s["thinking"]
            lines.append("%s%s%s %s %s%s" % (prefix, b, mark, tag, root.name,
                                               extra))
        else:
            lines.append("%s%s%s %s %s  [%s] %s" % (
                prefix, b, mark, tag, root.name,
                root.verdict or "…", root.accept or ""))
    else:
        lines.append("%s%s%s %s %s" % (prefix, b, mark, tag, root.name))
        lines.append("%s%s  [%s] %s" % (prefix, "  " if is_last else "│ ",
                                        root.verdict or "…", root.accept))
        if streams and not root.verdict:
            s = streams.get(root.id)
            if s:
                if s.get("thinking"):
                    lines.append("%s%s  ▸ 思考: %s" % (
                        prefix, "  " if is_last else "│ ", s["thinking"]))
                if s.get("speaking"):
                    lines.append("%s%s  ▸ 说: %s" % (
                        prefix, "  " if is_last else "│ ", s["speaking"]))
        if root.conclusion:
            lines.append("%s%s  → %s" % (prefix, "  " if is_last else "│ ",
                                         root.conclusion))
    for i, cid in enumerate(root.children):
        kid = registry.get(cid)
        if kid:
            render_tree(kid, registry, prefix + ("   " if is_last else "│  "),
                        i == len(root.children) - 1, lines, streams, compact)
    return lines
