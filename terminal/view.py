"""树的视图：把一棵 Node 树画成一串带树形标记的行（给人看）。

树长什么样是展示的变因，所以住终端层、不碰协议字段序列化：字段形状变了这里只是少画/多画一行。
"""

from core.protocol.fields import DISPATCH, LEAF, SATISFIED

_KIND_TAG = {DISPATCH: "[分配]", LEAF: "[叶子]"}


def render_tree(root, registry, prefix="", is_last=True, lines=None, streams=None,
                compact=False):
    """整棵树的视图：每层的拆分 / 判定 / 结论，画成一串带树形标记的行。

    根是入口，registry 是登记的全部节点（id → Node）；运行中画 ·，出结论按状态画 ✓ / ✗。
    streams 是可选的活动节点吐字尾巴（node_id → {"thinking", "speaking"}），正在吐字就在它下面补一行 ▸。

    compact=True 是实时视图：每个节点一行，运行中的把正在吐的字并排带上，出结论的并排带上判定 + 验收标准。
    """
    lines = [] if lines is None else lines
    branch = "└─ " if is_last else "├─ "
    # 孩子行的前缀 / 这一层内容行的缩进：最后一个孩子后面留空，否则画竖线
    child_prefix = prefix + ("   " if is_last else "│  ")
    content_prefix = prefix + ("  " if is_last else "│ ")
    # 没有 status 字段：verdict 非空就是终态，否则运行中
    mark = "✓" if root.verdict == SATISFIED else ("✗" if root.verdict else "·")
    tag = "%s%s" % (_KIND_TAG.get(root.kind, "[入口]"), " [门槛]" if root.gate else "")
    stream = streams.get(root.id) if streams else None

    if compact:
        # 实时视图：一行一个节点，正在说什么就显示什么（结论留到跑完的详细帧）
        if not root.verdict:
            extra = ""
            if stream:
                if stream.get("speaking"):
                    extra = "  ▸ 说: %s" % stream["speaking"]
                elif stream.get("thinking"):
                    extra = "  ▸ 思考: %s" % stream["thinking"]
            lines.append("%s%s%s %s %s%s" % (prefix, branch, mark, tag, root.name, extra))
        else:
            lines.append("%s%s%s %s %s  [%s] %s" % (
                prefix, branch, mark, tag, root.name,
                root.verdict or "…", root.accept or ""))
    else:
        lines.append("%s%s%s %s %s" % (prefix, branch, mark, tag, root.name))
        lines.append("%s  [%s] %s" % (content_prefix, root.verdict or "…", root.accept))
        if stream and not root.verdict:
            if stream.get("thinking"):
                lines.append("%s  ▸ 思考: %s" % (content_prefix, stream["thinking"]))
            if stream.get("speaking"):
                lines.append("%s  ▸ 说: %s" % (content_prefix, stream["speaking"]))
        if root.conclusion:
            lines.append("%s  → %s" % (content_prefix, root.conclusion))
    for i, cid in enumerate(root.children):
        kid = registry.get(cid)
        if kid:
            render_tree(kid, registry, child_prefix,
                        i == len(root.children) - 1, lines, streams, compact)
    return lines
