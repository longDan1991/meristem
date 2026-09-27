"""终端：和入口谈定预期，并把跑出来的东西显示给人看。

布局与不变量见 docs/TERMINAL.md：**一块 Textual 应用占满整屏** —— 日志区（选中节点的
消息流，应用内滚动）+ 实时尾巴 + 树条带 + 状态条 + 输入行，五区一屏。屏归应用所有，
所以"切频道重绘"是 widget 操作（清日志区再挂回去）：不写裸 ANSI、不需要猜"我上一帧画
了几行"，也不会有第二个渲染器跟它抢同一块屏。

行 / 框 / 列表都是 Textual 组件：说话提交后是 `Markdown`，工具输出是 `Collapsible`，
树条带是 `OptionList`（选中高亮、滚动都是它自己的），样式走 CSS 类（`view.ROW_CSS`）。

树是频道选择器：↑↓ 切选中节点，**切即清日志区重绘**（该节点的完整消息流写回去，
再把它的实时尾巴挂上来）。日志区只画选中节点这一个频道；别的节点在跑，树条带与状态条
看得见（`·` 标记 / `n 运行中`）。

选中的会话流：思考灰色流式（进尾巴区）；说话先缓冲，提交后以 **Markdown** 整段落地
（最终输出才 Markdown）；工具过程青色一行。提交 = 该节点的消息进了 `store`，
日志区重画读的就是它：所以尾巴只装"还没进 store 的那一小段"，落地的时机就是
LLM 调用结束（工具开始 / 入口提问 / 节点出结论都会把它落下来）。

焦点永远在输入行：↑↓ 切树节点（历史让位 Ctrl-P/Ctrl-N）、Enter 提交、Alt-Enter 换行、
Ctrl-T 收/展树条带、Ctrl-F 展开/折叠选中节点、Ctrl-Q / Ctrl-C 收手（不看输入行里有什么）。
Ctrl-D 归输入行自己（有字退一格，不是退路）：退出的路不能只有一条。

事件只报事实（loop_start / loop_end / message_update / tool_start / tool_end / usage），
怎么画是终端的事。非真终端（管道 / 重定向）：不进应用（那里没有屏可占），
事件来就把树逐帧打印出来、输入按行读（降级，test_tty G 守着）。
"""

import asyncio
import json
import os
import sys
import time

from textual.app import App
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.content import Content
from textual.widgets import Markdown, OptionList, Static, TextArea
from textual.widgets.option_list import Option

from .picker import pick_session
from .view import ROW_CSS, line, render_folded, render_stream, render_tail, tail_text
from core import config as cfg
from core.llm import LLM
from core.protocol.fields import INTAKE, Node
from core.protocol.messages import intake_seed
from core.runtime.loop import run
from core.runtime.store import Store

PROMPT = "› "                # 非真终端（管道 / 重定向）那条路的提示符
INPUT_HINT = "› 回车发送 · Alt-Enter 换行 · Ctrl-Q/C 收手"
SEED_HINT = "› 说说你要做什么 · 回车发送 · Ctrl-Q/C 收手"
TREE_STRIP_H = 6             # 树条带行数（默认展开，Ctrl-T 收成 0 行）
_TAIL_MAX_H = 8              # 尾巴区最多几行（再长就自己滚）


class _Quit(Exception):
    """读输入读到 EOF / Ctrl-C：常态不是错误，就地收手不往上抛。"""


def _trace_row(store):
    """装配层要说的那一行：trace 的绝对路径（会话文件在哪）。"""
    return "[trace] %s" % os.path.abspath(store.path)


def _args_text(arguments):
    """工具参数一行：dict 按 JSON 画（模型发来的就是 JSON），字符串原样。"""
    if isinstance(arguments, (dict, list)):
        return json.dumps(arguments, ensure_ascii=False)
    return str(arguments or "")


class _SessionApp(App):
    """一场会话的终端界面（真终端那条路）。

    五区：日志区（选中节点的消息流，应用内滚动）/ 实时尾巴 / 树条带 / 状态条 / 输入行。
    屏归应用，所有重绘都是 widget 操作 —— 擦除与重画是 Textual 渲染器的事。

    `store=None` 是"还没谈定要做什么"：进场先把话收下来（第一条回车就是种子），
    再建树、起 run —— 收种子这一步也在这块屏上，不另开一个提示框。
    """

    CSS = """
    /* 五区一律左右各留一列（输入行的老规矩，推广到全屏）：字别贴着屏幕边 */
    #log, #tail, #tree, #status, #input { padding: 0 1; }
    /* 滚动条不入画（内容占满内容区才像原生终端）：滚轮 / PageUp 照旧，只是不画那条竖杠 */
    #log, #tail, #input { scrollbar-size: 0 0; }
    #log { height: 1fr; }
    #tail { height: auto; max-height: %d; }
    #tree { height: %d; background: transparent; }
    #status { height: 1; color: $text-muted; }
    #input { height: auto; max-height: 8; border: none; }
    """ % (_TAIL_MAX_H, TREE_STRIP_H) + ROW_CSS

    BINDINGS = [
        Binding("up", "tree_up", "选中上一个节点", priority=True),
        Binding("down", "tree_down", "选中下一个节点", priority=True),
        Binding("ctrl+t", "tree_toggle", "收/展树条带", priority=True),
        Binding("ctrl+f", "fold", "展开/折叠选中节点", priority=True),
        Binding("ctrl+p", "hist_prev", "上一条输入", priority=True),
        Binding("ctrl+n", "hist_next", "下一条输入", priority=True),
        Binding("enter", "submit", "发送", priority=True),
        Binding("alt+enter,shift+enter", "newline", "换行", priority=True),
        # 收手：Ctrl-Q / Ctrl-C 都是**任何时候都通**的退路，不看输入行里有什么。
        # Ctrl-D 不占（和终端习惯冲突，退给输入行自己的删字符）；动作名用 Textual 自己的
        # `quit`，把 Textual 默认绑在 Ctrl-C 上的"提示按 ctrl+q 退"压成真退出。
        Binding("ctrl+q,ctrl+c", "quit", "收手", priority=True),
    ]

    def __init__(self, store=None, llm=None, *, banner=()):
        super().__init__()
        self.llm = llm
        self.store = None
        self.registry = {}
        self.root = None
        self.intake_id = None
        self.selected = None
        self.tails = {}                 # nid -> [(kind, 文本, 那个 Static)]：还没进 store 的尾巴
        self.expanded = set()           # 显式展开（压过自动折叠）
        self.tree_on = True             # 树条带开关（Ctrl-T）
        self.lines = asyncio.Queue()    # 输入行队列（回车提交，ask 取）
        self.history = []               # 提交过的行（Ctrl-P / Ctrl-N 翻）
        self.hist_idx = None
        self.asking = None              # 正等着用户回答的节点（状态条上写出来）
        self.banner = list(banner)      # 应用起来之前攒的那几行（工作目录 / 恢复的会话）
        self.t0 = time.monotonic()
        self.tokens = 0                 # 会话累计 token（usage 事件喂）
        self.error = None               # run 炸了就带着原异常收场，不静默
        self._task = None
        if store is not None:
            self._bind(store)

    def _bind(self, store):
        """接上运行现场：树有了，才开始有"选中节点"这回事。"""
        self.store = store
        self.registry = store.registry
        self.root = store.root
        self.intake_id = store.root.id
        self.selected = store.root.id

    # ── 装配 ──
    def compose(self):
        yield VerticalScroll(id="log")          # 日志区：消息流，一条一个组件
        yield VerticalScroll(id="tail")         # 尾巴区：还没提交的那一小段，涨过上限自己滚
        yield OptionList(id="tree", compact=True)
        yield Static(id="status", markup=False)
        yield TextArea(id="input", soft_wrap=True,
                       placeholder=INPUT_HINT if self.store is not None else SEED_HINT)

    def on_mount(self):
        self._write_rows([line(row, "banner") for row in self.banner])
        self.query_one("#input", TextArea).focus()
        if self.store is not None:
            self._start()

    def _start(self):
        """树已经有了：写 trace 行、把开场日志区画上、起 run。"""
        self._write_rows([line(_trace_row(self.store), "banner")])
        self._replay()                          # 开场日志区 = 选中节点（入口）的流
        self._task = asyncio.create_task(self._run())
        self._task.add_done_callback(self._finished)

    async def _run(self):
        await run(self.store, self.llm, subscribe=self.on_sink, ask=self.ask, say=self.say)

    def _finished(self, task):
        """run 收场：正常结束（节点跑完等不到新输入）或炸了。炸了带着原异常退场。"""
        if task.cancelled():
            return
        self.error = task.exception()
        if self.error is not None:
            self.exit()

    def cancel(self):
        """收手：停掉 run（它可能正卡在 ask 上等输入）。"""
        if self._task is not None:
            self._task.cancel()

    # ── 日志区：一条消息一个组件，屏上的历史就是这一区的滚动内容 ──
    def _write_rows(self, rows):
        log = self.query_one("#log", VerticalScroll)
        for row in rows:
            log.mount(row)
        self.call_after_refresh(log.scroll_end, animate=False)

    def _replay(self):
        """切频道：日志区清掉，重画选中节点的已提交消息，再挂上它的实时尾巴。

        清的是应用自己的日志区 —— 不碰终端 scrollback、不写裸 ANSI。
        """
        node = self.registry.get(self.selected)
        msgs = self.store.dialogue(self.selected).to_list() if node is not None else []
        self.query_one("#log", VerticalScroll).remove_children()
        self._write_rows(render_stream(msgs, intake=(self.selected == self.intake_id)))
        self._refresh_tail()
        self._refresh_tree()
        self._refresh_status()

    # ── 面板：树条带 / 状态条 / 尾巴 ──
    def _tree_rows(self):
        return render_folded(self.root, self.store, selected=self.selected,
                             expanded=self.expanded)

    def _refresh_tree(self):
        """条带 = 一棵 OptionList：高亮与滚动交给部件，这里只喂行、把选中挪回去。"""
        tree = self.query_one("#tree", OptionList)
        tree.display = self.tree_on
        if not self.tree_on:
            return
        rows = self._tree_rows()
        sel = next((i for i, (nid, _) in enumerate(rows) if nid == self.selected), 0)
        tree.clear_options()
        tree.add_options([Option(Content.from_text(t, markup=False), id=nid)
                          for nid, t in rows])
        tree.highlighted = sel

    def _status_text(self):
        nd = self.registry.get(self.selected)
        sel = nd.name if nd else "?"
        if len(sel) > 16:
            sel = sel[:15] + "…"
        parts = ["选中 %s" % sel]
        working = sum(1 for nid, n in self.registry.items()
                      if n.kind != INTAKE and not self._resting(nid))
        parts.append("%d 在动" % working)
        parts.append("%d 节点" % len(self.registry))
        parts.append("%ds" % int(time.monotonic() - self.t0))
        if self.tokens:
            parts.append("%d tokens" % self.tokens)
        if self.asking is not None:
            parts.append("等你回答")
        # 退出的路要一直看得见：Ctrl-Q / Ctrl-C 任何时候都通 —— 状态条是唯一常显的地方。
        parts.append("Ctrl-Q/C 收手")
        return " · ".join(parts)

    def _resting(self, nid):
        msgs = self.store.dialogue(nid).to_list()
        return bool(msgs) and msgs[-1].get("role") == "assistant"

    def _refresh_status(self):
        self.query_one("#status", Static).update(self._status_text())

    def _refresh_tail(self):
        """尾巴区：空着不占行；重建的是这一屏的组件，逐字增量只 update 最后一段。"""
        box = self.query_one("#tail", VerticalScroll)
        segs = self.tails.get(self.selected) or []
        box.display = bool(segs)
        box.remove_children()
        if not segs:
            return
        fresh = [(kind, text, render_tail(kind, text)) for kind, text, _ in segs]
        self.tails[self.selected] = fresh
        for _, _, w in fresh:
            box.mount(w)
        self.call_after_refresh(box.scroll_end, animate=False)

    # ── 实时尾巴：还没进 store 的那一小段 ──
    def _append_delta(self, nid, kind, delta):
        segs = self.tails.setdefault(nid, [])
        if segs and segs[-1][0] == kind:
            prev, text, widget = segs[-1]
            text += delta
            segs[-1] = (prev, text, widget)
            if nid == self.selected:
                widget.update(tail_text(prev, text))
                self._scroll_tail()
        else:
            segs.append((kind, delta, render_tail(kind, delta)))   # 换段（思考 ↔ 说话）
            if nid == self.selected:
                self.query_one("#tail", VerticalScroll).mount(segs[-1][2])
                self._scroll_tail()

    def _scroll_tail(self):
        """尾巴涨过上限就滚到最新（实时流要看见的是**最新**那几行）。"""
        box = self.query_one("#tail", VerticalScroll)
        box.display = True
        self.call_after_refresh(box.scroll_end, animate=False)

    def _commit_tail(self, nid):
        """尾巴落地：这一段的消息已经进 store 了，按提交后的样子画进日志区。

        正看着别的频道就只丢尾巴不算丢内容 —— 提交意味着消息在 store 里，切过去时
        日志区从 store 重画，整段都在。
        """
        segs = self.tails.pop(nid, [])
        if not segs or nid != self.selected:
            return
        self._write_rows([line("思考: %s" % text, "msg-think") if kind == "think"
                          else Markdown(text) for kind, text, _ in segs])
        self._refresh_tail()

    # ── 事件路由：日志区 + 尾巴 + 条带 ──
    def on_sink(self, type, payload):
        if not self.is_running:                 # 应用正在收场（run 还没被 cancel）：屏没了，不再画
            return
        nid = payload.get("scope") or self.intake_id
        if type == "message_update":
            delta = payload.get("delta") or ""
            if delta:
                self._append_delta(nid, "think" if payload.get("kind") == "reasoning" else "say",
                                   delta)
            return
        if type in ("tool_start", "tool_end"):
            self._commit_tail(nid)              # 这一轮 LLM 调用完了（工具是下一段）
            if nid == self.selected:
                if type == "tool_start":
                    text = "工具: %s(%s)" % (payload.get("name", ""),
                                             _args_text(payload.get("arguments")))
                else:
                    text = "工具结束: %s (%.1fs)" % (payload.get("name", ""),
                                                     payload.get("secs", 0))
                self._write_rows([line(text, "msg-tool")])
            self._refresh_tree()
            self._refresh_status()
            return
        if type == "loop_end":
            self._commit_tail(nid)
        if type == "usage":
            self.tokens += payload.get("total", 0)
        # 结构 / 标记变了，条带与状态条重画
        self._refresh_tree()
        self._refresh_status()

    async def ask(self, _question):
        """等入口回话：提问的整段先落地，再把行交给 run；跑任务时输入行照样活着。"""
        self._commit_tail(self.intake_id)
        self.asking = self.intake_id
        self._refresh_status()
        try:
            got = await self.lines.get()
        finally:
            self.asking = None
        if self.intake_id == self.selected:
            self._write_rows([line("你: %s" % got, "msg-user")])
        self._refresh_status()
        return got

    def say(self, text):
        """旁白（接到任务 / 打回理由等）：淡色缩进一行。"""
        self._write_rows([line("  " + str(text).replace("\n", "\n  "), "narrate")])

    # ── 输入：唯一通道，跑的时候也活着 ──
    def action_submit(self):
        area = self.query_one("#input", TextArea)
        text = area.text
        if not text.strip():                    # 空/纯空白不进队列（TERMINAL.md §2）
            return
        area.load_text("")
        if self.store is None:                  # 还没谈定：第一条回车就是种子，树这就建起来
            self._bind(Store.new(Node(name="会话", kind=INTAKE), seed=text))
            area.placeholder = INPUT_HINT
            self._start()
            return
        self.history.append(text)
        self.hist_idx = None
        self.lines.put_nowait(text)

    def action_newline(self):
        self.query_one("#input", TextArea).insert("\n")

    def action_hist_prev(self):
        if not self.history:
            return
        self.hist_idx = (len(self.history) - 1 if self.hist_idx is None
                         else max(0, self.hist_idx - 1))
        self._load_input(self.history[self.hist_idx])

    def action_hist_next(self):
        if self.hist_idx is None:
            return
        self.hist_idx = min(len(self.history) - 1, self.hist_idx + 1)
        self._load_input(self.history[self.hist_idx])

    def _load_input(self, text):
        """翻出来的行光标落在末尾：接着能打字，而不是从行首开始改。"""
        area = self.query_one("#input", TextArea)
        area.load_text(text)
        area.cursor_location = area.document.end

    # ── 键位：焦点永远在输入行（↑↓ 切树，历史让位 Ctrl-P/Ctrl-N）──
    def action_tree_up(self):
        self._move(-1)

    def action_tree_down(self):
        self._move(+1)

    def _move(self, delta):
        """↑↓ 交给 OptionList 自己走一格（它管高亮与滚动），选中变了就换频道。"""
        tree = self.query_one("#tree", OptionList)
        (tree.action_cursor_down if delta > 0 else tree.action_cursor_up)()
        idx = tree.highlighted
        if idx is None:                         # 树上还什么都没有
            return
        nid = tree.get_option_at_index(idx).id
        if nid == self.selected:
            return
        self.selected = nid
        self._replay()                          # 切即重画这一个频道

    def action_tree_toggle(self):
        self.tree_on = not self.tree_on
        self._refresh_tree()

    def action_fold(self):
        node = self.registry.get(self.selected)
        # 在动的节点永远展开，折叠只对已休息（交出了消息）的
        if node is not None and self._resting(self.selected):
            if self.selected in self.expanded:
                self.expanded.discard(self.selected)
            else:
                self.expanded.add(self.selected)
            self._refresh_tree()


async def _run_native(store, llm, *, banner=()):
    """真终端：整块屏交给 Textual 应用（日志区 / 尾巴 / 树条带 / 状态条 / 输入行）。

    应用自己起 `run` 任务：ask / say 直接 await 在同一个事件循环里，不需要跨线程桥。
    `store=None`（新会话）时，应用先进场把"要做什么"收下来，再建树起 run。
    """
    app = _SessionApp(store, llm, banner=banner)
    try:
        await app.run_async()
    finally:
        app.cancel()                        # 无论怎么退出，run 都停
    if app.error is not None:
        raise app.error
    return None


async def _listen():
    """非真终端读一行：按行读 stdin（那里没有屏可占），EOF / Ctrl-C 都算收手。"""
    try:
        got = await asyncio.to_thread(sys.stdin.readline)
    except (EOFError, KeyboardInterrupt):
        raise _Quit() from None
    if not got:
        raise _Quit()
    return got.rstrip("\n")


async def _run_plain(store, llm, *, banner=()):
    """非真终端（管道 / 重定向）：不进应用，事件来就把树逐帧打印出来。"""

    def out(text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def out_line(text):
        out(text + "\n")

    def narrate(text):
        out_line("  " + str(text).replace("\n", "\n  "))

    for row in banner:
        out_line(row)
    if store is None:                       # 新会话：种子按行读，读到 EOF / Ctrl-C 就是收手
        out(PROMPT)
        try:
            task = await _listen()
        except _Quit:
            return None
        store = Store.new(Node(name="会话", kind=INTAKE), seed=intake_seed(task))
    out_line(_trace_row(store))

    spoke, thinking = [False], [False]

    async def ask(question):
        if not spoke[0]:
            out_line(question)
        spoke[0] = False
        while True:
            got = await _listen()
            if got.strip():
                return got
            out_line("（回车发的是空行——Ctrl-D 结束，或重新输入）")

    def on_sink(type, payload):
        if type == "message_update" and payload.get("scope") == store.root.id:
            delta = payload.get("delta") or ""
            if payload.get("kind") == "reasoning":
                thinking[0] = True
                out(delta)
            else:
                if thinking[0]:
                    thinking[0] = False
                    out("\n")
                spoke[0] = True
                out(delta)
            return
        if type in ("loop_start", "loop_end"):
            narrate("\n".join(t for _, t in render_folded(store.root, store)))

    try:
        await run(store, llm, subscribe=on_sink, ask=ask, say=narrate)
    except (_Quit, asyncio.CancelledError):
        # 谈阶段 / 跑阶段按行读收手（EOF / Ctrl-C）：就地收手，不是错误
        return None
    return None


async def run_session(a):
    """装配运行现场：-r 时先选一个老会话读回整棵树，然后进终端话轮；模型由 converse 自己建。

    装配层攒出来的那几行（工作目录 / 并发 / 限制）交给话轮去画：真终端画进应用的
    日志区（屏归应用，应用起来之前 print 的东西会被备用屏盖掉），非真终端照旧打印。
    新会话"要做什么"也由话轮自己收：真终端在应用里收（第一条回车就是种子），
    非真终端按行读。
    """
    banner = ["[工作目录] %s" % cfg.WORKSPACE,
              "[并发] %d" % cfg.WORKERS,
              "[限制] 无。轮次/深度/节点/token/时间 全部不限，停止交给 API 自己"]
    store = None
    if a.resume:
        sessions = Store.roots()
        if not sessions:
            print("没有可加载的老会话：工作区里还没有跑过任何树。")
            return 1
        picked = await pick_session(sessions)
        if picked is None:
            print("取消。")
            return 0
        try:
            store = Store.load(picked)
        except ValueError:
            # 数据损坏就带着是哪个会话炸出来，不静默跳过
            print("读不了这个会话（数据损坏，或不是当前格式）：%s" % picked)
            raise
        banner.append("[会话] 已加载：%s" % store.path)
    return await converse(store, banner=banner)


async def converse(store, *, banner=()):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口不退场：谈成一个任务就挂到树上跑掉、结论带回对话再接着谈；整场会话是一棵树。
    `store=None` 是新会话（要做什么还没谈定）。分流按 stdout 是不是真终端：
    真终端进应用，否则逐帧打印。
    """
    llm = LLM()
    if sys.stdout.isatty():
        return await _run_native(store, llm, banner=banner)
    return await _run_plain(store, llm, banner=banner)
