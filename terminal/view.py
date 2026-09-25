"""树的视图：把一棵 Node 树画成给终端看的行（TERMINAL.md §1）。

两个渲染：`render_folded` 是地图（折叠 + 状态标记，返回 [(node_id, 行)]，
应用层靠 node_id 高亮/定位）；`render_stream` 是选中节点的消息流
（历史 msgs + 实时尾巴 + 判定行，返回 [rich Renderable] —— Markdown / Panel /
带样式 Text，颜色在 renderable 里，应用层经 rich Console 渲成 ANSI 上屏）。

树长什么样是展示的变因，所以住终端层、不碰协议字段序列化：字段形状变了这里只是少画/多画一行。
"""

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from core.protocol.fields import DISPATCH, LEAF, SATISFIED

_KIND_TAG = {DISPATCH: "[分配]", LEAF: "[叶子]"}

# 行样式：思考蓝斜体（区别于说话正文与工具青）、工具青、判定绿/红（TERMINAL.md §4）
THINK_STYLE = "blue italic"
_TOOL_STYLE = "cyan"
_USER_STYLE = "bold"


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
    """选中节点的消息流：历史 `msgs` 按序 + 实时尾巴。返回 [rich Renderable]。

    user / 任务消息 = 加粗文本行；assistant 内容 = **Markdown**（代码块/列表/加粗，
    TERMINAL.md §4）；工具调用 = 青色一行；工具输出 = **Panel 框**（title=工具名，
    与聊天内容分开）；思考尾巴 = 蓝斜体一行；说话尾巴 = 纯文本（未提交，提交后变
    Markdown）；判定 = 绿（满足）/ 红（其它）。

    `msgs` 就是 `Dialogue.to_list()` 的平铺账本，渲染层不碰 store。说话尾巴与
    对话去重：已提交进对话的整段话不重复显示（尾巴里只露超出最后一条已提交
    说话的部分）；思考不进对话（`dialogue.assistant` 只存 content），永远实时。
    """
    rows = []
    who = "你" if intake else "任务"
    # tool_call_id -> 工具名：面板标题只有 assistant 的 tool_calls 才知道
    tool_names = {}
    for m in msgs:
        if m.get("role") == "assistant":
            for w in m.get("tool_calls") or []:
                tool_names[w.get("id")] = (w.get("function") or {}).get("name", "")
    last_say = ""
    last_reason = ""
    for m in reversed(msgs):
        if m.get("role") == "assistant":
            if m.get("content") and not last_say:
                last_say = m["content"]
            if m.get("reasoning") and not last_reason:
                last_reason = m["reasoning"]
            if last_say and last_reason:
                break
    for m in msgs:
        role = m.get("role")
        if role == "user":
            rows.append(Text("%s: %s" % (who, m.get("content") or ""), style=_USER_STYLE))
        elif role == "assistant":
            if m.get("reasoning"):
                rows.append(Text("思考: %s" % m["reasoning"], style=THINK_STYLE))
            content = m.get("content") or ""
            if content:
                rows.append(Markdown(content))
            for w in m.get("tool_calls") or []:
                fn = w.get("function") or {}
                rows.append(Text("工具: %s(%s)" % (fn.get("name", ""), fn.get("arguments", "")),
                                 style=_TOOL_STYLE))
        elif role == "tool":
            rows.append(Panel(m.get("content") or "", title=tool_names.get(m.get("tool_call_id")) or "工具",
                              border_style=_TOOL_STYLE))
    if verdict:
        rows.append(Text("[%s] %s" % (verdict, accept or ""),
                         style="bold green" if verdict == SATISFIED else "bold red"))
        if conclusion:
            rows.append(Text("→ %s" % conclusion, style="dim"))
    if streams:
        # 思考 / 说话尾巴都只露超出最后一条已提交的部分（提交后历史里有整段）
        think = streams.get("thinking") or ""
        if think and not (last_reason and think.startswith(last_reason)):
            rows.append(Text("思考: %s" % think, style=THINK_STYLE))
        elif think and last_reason and think.startswith(last_reason):
            shown = think[len(last_reason):]
            if shown:
                rows.append(Text("思考: %s" % shown, style=THINK_STYLE))
        tail = streams.get("speaking") or ""
        if tail and not (last_say and tail.startswith(last_say)):
            rows.append(Text(tail))
        elif tail and last_say and tail.startswith(last_say):
            shown = tail[len(last_say):]
            if shown:
                rows.append(Text(shown))
    return rows
