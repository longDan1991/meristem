"""树的视图：把一棵 Node 树画成一串带树形标记的行（给人看）。

终端是唯一消费方 —— 树长什么样、怎么折行、吐字尾巴怎么并排，都是**展示**的
变因，和协议（字段形状）不同。所以它住终端层，不碰协议字段的序列化。
`Node` 的字段形状变了，这里只是少画/多画一行；这里的画法变了，协议不动。
"""


def render_tree(root, registry, prefix="", is_last=True, lines=None, streams=None,
                compact=False):
    """整棵树的视图：每层的拆分 / 判定 / 结论，画成一串带树形标记的行。

    根是入口，registry 是出生时登记的全部节点（id → Node），孩子按 id 查。
    运行中的节点画成 ·，出过结论的按状态画成 ✓ / ✗。
    streams 是可选的活动节点吐字尾巴（node_id → {"thinking", "speaking"}）：
    运行中的节点如果正在吐字，在它下面补一行 ▸ —— 树在跑，看得见每个节点
    正在说什么。尾巴怎么截由终端定，这里只负责画。

    compact=True 是**实时视图**（终端跑任务时用）：每个节点一行 ——
    运行中的节点：`· [叶子] 名字  ▸ 思考: …`（正在吐的字并排在自己那行）；
    出过结论的：`✓ [叶子] 名字  [满足] 验收标准`。一行一个节点，整棵树按
    结构铺开，每个节点的输出都占一行看得见（屏幕放不下时终端负责裁）。
    """
    b = "└─ " if is_last else "├─ "
    # 没有 status 字段：出过结论（verdict 非空）就是终态，否则运行中。
    mark = "✓" if root.verdict == "满足" else ("✗" if root.verdict else "·")
    if lines is None:
        lines = []
    tag = "%s%s" % ({"dispatch": "[分配]", "leaf": "[叶子]"}.get(root.kind, "[入口]"),
                     " [门槛]" if root.gate else "")
    if compact:
        # 实时视图：一行一个节点。运行中的把正在吐的字并排带上 ——
        # 正在说什么就显示什么（吐过话就显示说，还在想就显示思考）；
        # 出过结论的把判定 + 验收标准并排带上（结论留到跑完的详细帧）。
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
