"""树的视图：把一棵 Node 树画成给终端看的行与组件（TERMINAL.md §1）。

三个渲染：
- `render_folded`（地图）：跑完的子树折一行带统计，返回 `[(node_id, 行)]`，
  树条带靠 node_id 定位选中行；
- `render_stream`（选中节点**已提交**的消息流）：返回 [Widget]；
- `render_tail`（选中节点**还没提交**的实时尾巴的一段）：返回 Widget。

两块分开因为变因不同：已提交的那份住在 store 里（切频道时按它重画），尾巴只活在
事件流里。行样式一律走 CSS 类（`ROW_CSS`，应用并进自己的样式表）：排版与框线是组件的
本职（`Markdown` 管 Markdown、`Collapsible` 管带标题可折的框），这里只挑组件、给文本、
贴类名，不自己画。

名字与内容都是模型给的：文本行一律 `markup=False`（`[` 不许被当命令解）。

树长什么样是展示的变因，所以住终端层、不碰协议字段序列化：字段形状变了这里只是少画/多画一行。
"""

from textual.content import Content
from textual.widgets import Collapsible, Markdown, Static

from core.protocol.fields import DISPATCH, LEAF, SATISFIED

_KIND_TAG = {DISPATCH: "[分配]", LEAF: "[叶子]"}

# 行样式（应用并进 CSS）：思考灰斜体，工具青，判定绿/红，旁白与横幅淡色
ROW_CSS = """
.msg-user { text-style: bold; }
.msg-think { color: $text-muted; text-style: italic; }
.msg-tool { color: cyan; }
.msg-note { color: $text-muted; }
.verdict-ok { color: green; text-style: bold; }
.verdict-bad { color: red; text-style: bold; }
.tail-think { color: $text-muted; text-style: italic; }
.tail-say { color: $foreground; }
.banner { color: $text-muted; }
.narrate { color: $text-muted; }
"""


def line(text, css_class):
    """一行纯文本（`[` 这类字符原样显示，不当标记解）。"""
    return Static(text, markup=False, classes=css_class)


def tail_text(kind, text):
    """尾巴一段的显示文本：思考带 `思考: ` 前缀，说话就是它自己。"""
    return "思考: %s" % text if kind == "think" else text


def render_tail(kind, text):
    """尾巴区的一段：思考灰斜体，说话纯文本（提交后才走 Markdown）。"""
    return line(tail_text(kind, text), "tail-think" if kind == "think" else "tail-say")


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

    返回 (node_id, 行) 而不是纯行：应用层要靠 node_id 选中对应行。
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


def render_stream(msgs, *, intake=False, verdict="", accept="", conclusion=""):
    """选中节点**已提交**的消息流：`msgs` 按序。返回 [Widget]。

    user / 任务消息 = 加粗纯文本行；assistant 内容 = **Markdown** 组件（代码块/列表/加粗，
    TERMINAL.md §4）；工具调用 = 青色一行；工具输出 = **Collapsible 框**（title=工具名，
    与聊天内容分开，全文不截断）；判定 = 绿（满足）/ 红（其它）。还没提交的那一小段走
    `render_tail`（应用层两块分开画：提交进 store 的进日志区，尾巴在日志区下方实时更新）。

    `msgs` 就是 `Dialogue.to_list()` 的平铺账本，渲染层不碰 store。
    """
    rows = []
    who = "你" if intake else "任务"
    # tool_call_id -> 工具名：框的标题只有 assistant 的 tool_calls 才知道
    tool_names = {}
    for m in msgs:
        if m.get("role") == "assistant":
            for w in m.get("tool_calls") or []:
                tool_names[w.get("id")] = (w.get("function") or {}).get("name", "")
    for m in msgs:
        role = m.get("role")
        if role == "user":
            rows.append(line("%s: %s" % (who, m.get("content") or ""), "msg-user"))
        elif role == "assistant":
            if m.get("reasoning"):
                rows.append(line("思考: %s" % m["reasoning"], "msg-think"))
            content = m.get("content") or ""
            if content:
                rows.append(Markdown(content))
            for w in m.get("tool_calls") or []:
                fn = w.get("function") or {}
                rows.append(line("工具: %s(%s)" % (fn.get("name", ""), fn.get("arguments", "")),
                                 "msg-tool"))
        elif role == "tool":
            rows.append(Collapsible(
                line(m.get("content") or "", "msg-note"),
                title=Content.from_text(tool_names.get(m.get("tool_call_id")) or "工具",
                                        markup=False),
                collapsed=False))
    if verdict:
        rows.append(line("[%s] %s" % (verdict, accept or ""),
                         "verdict-ok" if verdict == SATISFIED else "verdict-bad"))
        if conclusion:
            rows.append(line("→ %s" % conclusion, "msg-note"))
    return rows
