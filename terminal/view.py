"""树的视图：把一棵 Node 树画成一串带树形标记的行（给人看）。

树长什么样是展示的变因，所以住终端层、不碰协议字段序列化：字段形状变了这里只是少画/多画一行。
"""

from core.protocol.fields import DISPATCH, LEAF, SATISFIED

_KIND_TAG = {DISPATCH: "[分配]", LEAF: "[叶子]"}


def _subtree_stats(root, registry):
    """一次迭代后序：每个节点的（有无运行中后代, 后代总数）。O(n)。

    折叠规则"跑完的子树折一行带统计"要的就是这两个数，一趟算齐，
    不让每帧渲染退化成 O(n²)。
    """
    active, size = {}, {}
    stack = [(root, False)]
    while stack:
        nd, visited = stack.pop()
        kids = [registry[c] for c in nd.children if c in registry]
        if visited:
            active[nd.id] = (not nd.verdict) or any(active[k.id] for k in kids)
            size[nd.id] = 1 + sum(size[k.id] for k in kids)
        else:
            stack.append((nd, True))
            for k in kids:
                stack.append((k, False))
    return active, size


def render_folded(root, registry, *, selected=None, expanded=frozenset()):
    """折叠视图：跑完的子树折成一行带统计，活跃路径展开。返回 [(node_id, 行)]。

    折叠规则（TERMINAL.md §5）：出了结论、下面没有在跑的后代、也不在选中路径上
    → 折成一行带节点数；显式展开（`expanded`）压过自动折叠。渲染量只跟
    "正在动的东西 + 选中路径"走，折叠的子树一行带统计。

    返回 (node_id, 行) 而不是纯行：应用层要靠 node_id 高亮选中行、定位滚动。
    """
    active, size = _subtree_stats(root, registry)
    sel_chain = set()
    n = registry.get(selected) if selected is not None else None
    while n is not None:
        sel_chain.add(n.id)
        n = registry.get(n.parent)
    rows = []

    def fold_of(node):
        if node.id in expanded:
            return False
        if not node.verdict or active[node.id] or node.id in sel_chain:
            return False
        return True

    def emit(node, prefix, is_last):
        branch = "└─ " if is_last else "├─ "
        child_prefix = prefix + ("   " if is_last else "│  ")
        mark = "✓" if node.verdict == SATISFIED else ("✗" if node.verdict else "·")
        tag = "%s%s" % (_KIND_TAG.get(node.kind, "[入口]"), " [门槛]" if node.gate else "")
        if fold_of(node):
            rows.append((node.id, "%s%s%s %s %s (%d 节点)" % (
                prefix, branch, mark, tag, node.name, size[node.id] - 1)))
            return
        rows.append((node.id, "%s%s%s %s %s" % (prefix, branch, mark, tag, node.name)))
        for i, cid in enumerate(node.children):
            kid = registry.get(cid)
            if kid is not None:
                emit(kid, child_prefix, i == len(node.children) - 1)

    emit(root, "", True)
    return rows


def render_stream(msgs, streams=None, *, intake=False, verdict="", accept="", conclusion=""):
    """选中节点的消息流：历史 `msgs` 按序 + 实时尾巴。返回 [(kind, text)]。

    kind 词表：user / say / tool / toolout / verdict / thinking / speaking ——
    颜色由应用层按 kind 定（思考灰、说话正文、工具青色）。工具输出全文进历史
    （TERMINAL.md §4，不截断）；实时阶段只画调用行，耗时由 `tool_end` 事件补。

    `msgs` 就是 `Dialogue.to_list()` 的平铺账本，渲染层不碰 store。说话尾巴与
    对话去重：已提交进对话的整段话不重复显示（尾巴里只露超出最后一条已提交
    说话的部分）；思考不进对话（`dialogue.assistant` 只存 content），永远实时。
    """
    rows = []
    who, say = ("你", "入口") if intake else ("任务", "说")
    last_say = ""
    for m in reversed(msgs):
        if m.get("role") == "assistant" and m.get("content"):
            last_say = m["content"]
            break
    for m in msgs:
        role = m.get("role")
        if role == "user":
            rows.append(("user", "%s: %s" % (who, m.get("content") or "")))
        elif role == "assistant":
            content = m.get("content") or ""
            if content:
                rows.append(("say", "%s: %s" % (say, content)))
            for w in m.get("tool_calls") or []:
                fn = w.get("function") or {}
                rows.append(("tool", "工具: %s(%s)" % (
                    fn.get("name", ""), fn.get("arguments", ""))))
        elif role == "tool":
            rows.append(("toolout", "输出: %s" % (m.get("content") or "")))
    if verdict:
        rows.append(("verdict", "[%s] %s" % (verdict, accept or "")))
        if conclusion:
            rows.append(("verdict", "→ %s" % conclusion))
    if streams:
        think = streams.get("thinking") or ""
        if think:
            rows.append(("thinking", "思考: %s" % think))
        tail = streams.get("speaking") or ""
        if tail and not (last_say and tail.startswith(last_say)):
            rows.append(("speaking", "%s: %s" % (say, tail)))
        elif tail and last_say and tail.startswith(last_say):
            shown = tail[len(last_say):]
            if shown:
                rows.append(("speaking", "%s: %s" % (say, shown)))
    return rows


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
