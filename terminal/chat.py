"""终端：和入口谈定预期，并把跑出来的东西显示给人看。

布局与不变量见 docs/TERMINAL.md：左树右流 —— 树是频道选择器，流是选中节点的消息。

真终端：全屏 prompt_toolkit Application，五区固定（左树 / 右流 / 状态条 / 输入行拉通）。
事件只报事实（loop_start / loop_end / message_update / tool_start / tool_end / usage），
怎么画是终端的事。输入只有一个 buffer：回车提交进队列，入口 ask 按顺序取 ——
跑任务时输入不冻结（TERMINAL.md §2）。读交给 prompt_toolkit（编辑 / 历史 / 粘贴 /
Ctrl-D 都是它的事）；分几行写按 Alt-Enter，不绑 `c-j`。

非真终端（管道 / 重定向）：不进全屏，事件来就把树逐帧打印出来（降级，test_tty G 守着）。
"""

import asyncio
import io
import os
import sys
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.output.defaults import create_output
from rich.console import Console

from .picker import pick_session
from .view import render_folded, render_stream
from core import config as cfg
from core.llm import LLM
from core.protocol.fields import INTAKE, Node
from core.protocol.messages import intake_seed
from core.runtime.loop import run
from core.runtime.store import Store

PROMPT = "› "
TREE_WIDTH = 40            # 树窗格宽度（TERMINAL.md §1）
REFRESH_MS = 0.03          # 流式合帧间隔：≈30fps（快模型也看得出在流）


def _stream_console(file, width):
    """流的 rich 渲染器：color_system 钉死 standard（prompt_toolkit ANSI 桥只认标准 SGR）。"""
    return Console(file=file, color_system="standard", width=width)


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C：常态不是错误，就地收手不往上抛。"""


KEYS = KeyBindings()


def _newline(event):
    """回车发送，换行绑 Alt-Enter（`c-j` 会把回车也吃成换行）。"""
    event.current_buffer.insert_text("\n")


KEYS.add("escape", "enter")(_newline)


def _session_of(message, history, inp, output):
    """一条 prompt_toolkit 会话，键位/输出策略只在这里定义（谈阶段与跑阶段共用）。"""
    return PromptSession(message=message, history=history,
                         key_bindings=KEYS, input=inp, output=output)


def _session(inp=None):
    """一条会话，历史跨问题保留；`inp` 只给测试塞管道，走的是真的输入路径。"""
    return _session_of(PROMPT, InMemoryHistory(), inp,
                       DummyOutput() if inp is not None else None)


async def _listen(session):
    """读一条回答；`prompt_async` 必须异步版，同步 `prompt()` 在事件循环里会炸。"""
    try:
        return await session.prompt_async()
    except (EOFError, KeyboardInterrupt):
        raise _Quit() from None


async def opening(session=None):
    """入口开口之前先让用户把要做的事说完，否则种子是空的、模型只会问一句"你要做什么"。"""
    session = session or _session()
    return await _listen(session)


def _view_window(rows, sel, h):
    """树窗格视窗：选中行保持在视窗内（picker 同款）。"""
    n = len(rows)
    if n <= h:
        return rows
    top = min(max(0, sel - h // 2), n - h)
    return rows[top:top + h]


def _tail_window(rows, h, scroll):
    """流窗格视窗：默认贴底，`scroll` 是从底部往上翻的行数（上翻即停跟，End 回底）。"""
    n = len(rows)
    if n <= h:
        return rows
    end = n - scroll
    return rows[max(0, end - h):end]


class SessionApp:
    """全屏会话：五区布局 + 事件路由 + 一条输入队列（谈与跑共用）。

    树是频道选择器：`selected` 决定流的内容（入口根与其它节点同构）。
    输入只有一个 buffer：回车提交进 `lines` 队列，入口的 `ask` 按顺序取。
    """

    def __init__(self, store, *, session):
        self.store = store
        self.registry = store.registry
        self.root = store.root
        self.intake_id = store.root.id
        self.selected = [self.intake_id]
        self.expanded = set()           # 显式展开（压过自动折叠）
        self.streams = {}               # node_id -> {"thinking","speaking"} 实时尾巴
        self.lines = asyncio.Queue()    # 输入行队列（回车提交，ask 取）
        self.scroll = 0                 # 流：从底部往上翻的行数；0 = 贴底
        self.t0 = time.monotonic()
        self.tokens = 0                 # 会话累计 token（usage 事件喂）
        self._render_pending = False

        self.tree_ctl = FormattedTextControl(focusable=True)
        self.stream_ctl = FormattedTextControl()
        self.status_ctl = FormattedTextControl()
        self.input_buffer = Buffer(multiline=True, history=InMemoryHistory())
        tree_window = Window(self.tree_ctl, width=TREE_WIDTH)
        input_window = Window(BufferControl(self.input_buffer), height=1)
        layout = Layout(HSplit([
            VSplit([
                tree_window,
                Window(width=1, char="│"),
                Window(self.stream_ctl, wrap_lines=True),   # 宽行换行，不静默截断（TERMINAL.md §3）
            ]),
            Window(self.status_ctl, height=1),
            input_window,
        ]))
        self.app = Application(layout=layout, key_bindings=self._bindings(),
                               full_screen=True, mouse_support=True,
                               min_redraw_interval=0.03,
                               input=session.app.input,
                               output=create_output())
        self.app.layout.focus(input_window)
        self._render()

    # ── 键位：焦点在输入 buffer 上时 ↑↓ 是历史、回车是提交；焦点在树上时是选中/折叠 ──
    def _input_focused(self):
        return isinstance(self.app.layout.current_control, BufferControl)

    def _bindings(self):
        kb = KeyBindings()

        @kb.add("tab")
        def _tab(event):
            event.app.layout.focus_next()

        @kb.add("up")
        def _up(event):
            if isinstance(event.app.layout.current_control, BufferControl):
                event.app.layout.current_buffer.history_backward()
            else:
                self._move(-1)

        @kb.add("down")
        def _down(event):
            if isinstance(event.app.layout.current_control, BufferControl):
                event.app.layout.current_buffer.history_forward()
            else:
                self._move(+1)

        @kb.add("enter")
        def _enter(event):
            if isinstance(event.app.layout.current_control, BufferControl):
                self._submit()
            else:
                self._toggle_fold()

        @kb.add("escape", "enter")
        def _newline(event):
            event.app.layout.current_buffer.insert_text("\n")

        @kb.add("c-d")
        def _quit(event):
            event.app.exit()

        @kb.add("pageup")
        def _pgup(event):
            self._scroll(-10)

        @kb.add("pagedown")
        def _pgdn(event):
            self._scroll(+10)

        @kb.add("end")
        def _end(event):
            self.scroll = 0
            self._render()

        @kb.add("<scroll-up>")
        def _wu(event):
            self._scroll(-3)

        @kb.add("<scroll-down>")
        def _wd(event):
            self._scroll(+3)

        return kb

    # ── 交互动作 ──
    def _move(self, delta):
        rows = render_folded(self.root, self.registry, selected=self.selected[0],
                             expanded=self.expanded)
        idx = next((i for i, (nid, _) in enumerate(rows) if nid == self.selected[0]), 0)
        idx = max(0, min(len(rows) - 1, idx + delta))
        self.selected[0] = rows[idx][0]
        self._render()

    def _toggle_fold(self):
        node = self.registry.get(self.selected[0])
        if node is not None and node.verdict:   # 在跑的节点永远展开，折叠只对已出结论的
            nid = self.selected[0]
            if nid in self.expanded:
                self.expanded.discard(nid)
            else:
                self.expanded.add(nid)
            self._render()

    def _submit(self):
        text = self.input_buffer.text
        if text.strip():                        # 空/纯空白不入队（TERMINAL.md §2）
            self.lines.put_nowait(text)
        self.input_buffer.reset()
        self._render()

    def _scroll(self, delta):
        n = len(self._stream_rows())
        self.scroll = max(0, min(n - 1, self.scroll + delta))
        self._render()

    # ── 渲染 ──
    def _size(self):
        # prompt_toolkit 的 get_size 内部已兜底 OSError → (24, 80)，非终端也安全
        return self.app.output.get_size()

    def _stream_rows(self):
        nid = self.selected[0]
        node = self.registry.get(nid)
        msgs = self.store.dialogue(nid).to_list() if node is not None else []
        return render_stream(msgs, self.streams.get(nid), intake=(nid == self.intake_id),
                             verdict=node.verdict if node else "",
                             accept=node.accept if node else "",
                             conclusion=node.conclusion if node else "")

    def _status(self):
        n_run = sum(1 for nd in self.registry.values() if not nd.verdict)
        parts = ["%d 运行中" % n_run, "%d 节点" % len(self.registry),
                 "%ds" % int(time.monotonic() - self.t0)]
        if self.tokens:
            parts.append("%d tokens" % self.tokens)
        if self.scroll:
            parts.append("↑ 已上翻")
        return " · ".join(parts)

    def _render(self):
        """整帧：更新控件文本 + 立刻重画（结构性事件 / 交互动作用）。"""
        self._update_texts()
        self.app.invalidate()

    def _update_texts(self):
        """只重算控件文本，不重画。流经 rich 渲成 ANSI 再转 prompt_toolkit 片段。"""
        rows, cols = self._size()
        pane_h = max(1, rows - 2)               # 状态条 + 输入行各占一行
        tree_rows = render_folded(self.root, self.registry, selected=self.selected[0],
                                  expanded=self.expanded)
        sel = next((i for i, (nid, _) in enumerate(tree_rows)
                    if nid == self.selected[0]), 0)
        view = _view_window(tree_rows, sel, pane_h)
        self.tree_ctl.text = [("reverse" if nid == self.selected[0] else "", t + "\n")
                              for nid, t in view]
        # 流：rich 渲染（markdown / Panel / 彩色）→ ANSI 行 → 尾窗 → 片段。
        # color_system 显式钉死 standard：prompt_toolkit 的 ANSI 桥只认标准 SGR，
        # 且不受 NO_COLOR / TERM 环境影响。
        stream_width = max(20, cols - TREE_WIDTH - 1)
        buf = io.StringIO()
        console = _stream_console(file=buf, width=stream_width)
        for r in self._stream_rows():
            console.print(r)
        lines = buf.getvalue().split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        tail = _tail_window(lines, pane_h, self.scroll)
        self.stream_ctl.text = to_formatted_text(ANSI("\n".join(tail)))
        self.status_ctl.text = self._status()

    def _request_update(self):
        """流式合帧 ≈30fps：message_update 一 token 一发，rich 渲染不能每 token 跑。
        文本在下一帧整块更新——快模型也看得出在流（10fps 时是"几坨字"，30fps 是流）。"""
        if self._render_pending:
            return
        self._render_pending = True
        self.app.create_background_task(self._throttled())

    async def _throttled(self):
        await asyncio.sleep(REFRESH_MS)
        self._render_pending = False
        self._update_texts()
        self.app.invalidate()

    # ── 事件路由：一个函数收全部事实，按 scope 分路去画（事件只报事实）──
    def on_sink(self, type, payload):
        if type == "message_update":
            delta = payload.get("delta") or ""
            if not delta:
                return
            key = "thinking" if payload.get("kind") == "reasoning" else "speaking"
            self.streams.setdefault(payload.get("scope"),
                                    {"thinking": "", "speaking": ""})[key] += delta
            self._request_update()
            return
        if type == "usage":
            self.tokens += payload.get("total", 0)
        self._render()

    # ── 入口读通道：唯一一条；跑的时候敲的行先排队，按顺序交出去 ──
    async def _ask(self, _question):
        # 入口整段话此时已提交进对话（append_assistant 先于 ask），思考/说话都进了
        # 历史、尾巴去重后自然消失，不需要手动清 —— 这里先画一帧让 markdown 生效。
        self._render()
        got = await self.lines.get()
        self._defer_render()                     # 等 loop 把 user 消息 append 进对话再画
        return got

    def _defer_render(self):
        self.app.create_background_task(self._after_append())

    async def _after_append(self):
        await asyncio.sleep(0.05)
        self._render()


async def _run_full(store, llm, *, session):
    """真终端：全屏 Application 跑整场会话；Ctrl-D 就地收手。"""
    app = SessionApp(store, session=session)
    task = asyncio.ensure_future(run(store, llm, subscribe=app.on_sink,
                                     ask=app._ask, say=None))
    try:
        await app.app.run_async()
    finally:
        # 无论 Ctrl-D 还是异常退出，run 任务都停：入口不退场，ask 可能正卡在队列上
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, _Quit):
            pass
    return None


async def _run_plain(store, llm, *, session):
    """非真终端（管道 / 重定向）：不进全屏，事件来就把树逐帧打印出来。"""
    console = Console()
    registry = store.registry
    spoke, thinking = [False], [False]

    def piece(text):
        console.print(text, end="", markup=False, highlight=False, soft_wrap=True)

    def line(text):
        console.print(text, markup=False, highlight=False)

    def narrate(text):
        line("  " + str(text).replace("\n", "\n  "))

    async def ask(question):
        if not spoke[0]:
            line(question)
        spoke[0] = False
        while True:
            got = await _listen(session)
            if got.strip():
                return got
            line("（回车发的是空行——Ctrl-D 结束，或重新输入）")

    def on_sink(type, payload):
        if type == "message_update" and payload.get("scope") == store.root.id:
            delta = payload.get("delta") or ""
            if payload.get("kind") == "reasoning":
                thinking[0] = True
                piece(delta)
            else:
                if thinking[0]:
                    thinking[0] = False
                    piece("\n")
                spoke[0] = True
                piece(delta)
            return
        if type in ("loop_start", "loop_end"):
            narrate("\n".join(t for _, t in render_folded(store.root, registry)))

    try:
        await run(store, llm, subscribe=on_sink, ask=ask, say=narrate)
    except (_Quit, asyncio.CancelledError):
        # 谈阶段 Ctrl-D / 跑阶段 Ctrl-D：就地收手，不是错误
        return None
    return None


async def _show_resumed(store):
    """把重建出来的老会话画给人看，先让他看见接的是什么。"""
    console = Console()
    console.print("\n[会话] 已加载：%s" % store.path)
    for _, t in render_folded(store.root, store.registry):
        console.print("  " + t)
    console.print("")


async def run_session(a, session=None):
    """装配运行现场，-r 时选老会话读回整棵树，然后进终端话轮；模型由 converse 自己建。"""
    session = session or _session()
    console = Console()
    console.print("[工作目录] %s" % cfg.WORKSPACE)
    console.print("[并发] %d" % cfg.WORKERS)
    console.print("[限制] 无。轮次/深度/节点/token/时间 全部不限，停止交给 API 自己")

    if a.resume:
        sessions = Store.roots()
        if not sessions:
            console.print("没有可加载的老会话：工作区里还没有跑过任何树。")
            return 1
        picked = await pick_session(sessions)
        if picked is None:
            console.print("取消。")
            return 0
        try:
            store = Store.load(picked)
        except ValueError:
            # 数据损坏就带着是哪个会话炸出来，不静默跳过
            console.print("读不了这个会话（数据损坏，或不是当前格式）：%s" % picked)
            raise
        env = {"store": store}
        await _show_resumed(store)
    else:
        task = await opening(session)
        env = {"store": Store.new(Node(name="会话", kind=INTAKE),
                                  seed=intake_seed(task))}
    console.print("[trace] %s\n" % os.path.abspath(env["store"].path))

    # 落盘由 run 兜底
    return await converse(env, session=session)


async def converse(env, session=None):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口不退场：谈成一个任务就挂到树上跑掉、结论带回对话再接着谈；整场会话是一棵树。
    env 是运行现场（含一份 store，由 run_session 建好），session 是读的那条通道。
    """
    session = session or _session()
    store = env["store"]
    llm = LLM()
    if sys.stdout.isatty():
        return await _run_full(store, llm, session=session)
    return await _run_plain(store, llm, session=session)
