"""终端：和入口谈定预期，并把跑出来的东西显示给人看。

终端只把整场会话（入口为根的树）丢给 `run`，判断 / 打回 / 跑树 / 收手都在运行时层。

通道分开，同一句话才不会显示两遍：入口的话走 `ask`，思考走 `on_reasoning`（画成灰的），
旁白走 `on_say`，树里各节点的吐字走 `message_update`（scope=node_id）。

读交给 prompt_toolkit（编辑 / 历史 / 粘贴 / Ctrl-D 都是它的事）；分几行写按 Alt-Enter，
不绑 `c-j`（终端送上来的是 CR 还是 LF 不该由我们猜）。

跑任务时输入不冻结：rich Live 接管屏幕，另开一条只读不画的 prompt_toolkit 会话
（DummyOutput）读键盘，敲下的行进队列；运行中 Ctrl-D / Ctrl-C 中止整个会话。

实时视图每节点一行（`render_tree(compact=True)`），所有节点正在吐的字都看得见；
任务出结论那帧切回详细视图。显示交给 rich，tree 视图在 `terminal/view.py`。

入口的话是真流式：每到一个字就写屏；`ask` 只负责读，不负责显示。
"""

import asyncio
import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.output import DummyOutput
from rich.console import Console
from rich.live import Live
from rich.text import Text

from .picker import pick_session
from .view import render_tree
from core import config as cfg
from core.llm import LLM
from core.protocol.fields import INTAKE, Node, is_task_root
from core.protocol.messages import intake_seed
from core.runtime.loop import run
from core.runtime.store import Store

PROMPT = "› "

KEYS = KeyBindings()


def _newline(event):
    """回车发送，换行绑 Alt-Enter（`c-j` 会把回车也吃成换行）。"""
    event.current_buffer.insert_text("\n")


KEYS.add("escape", "enter")(_newline)


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C：常态不是错误，就地收手不往上抛。"""


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


class RunInput:
    """跑阶段读输入通道：只读不画，敲下的行进队列，Ctrl-D / Ctrl-C 中止会话。

    谈阶段用会话直接读（`_listen`），跑阶段用这一条只读不画的会话读；
    两条读会话绝不同时挂 reader，换手一律 await（`settle`），否则输入会死。
    敲下的行先进 `lines` 队列，入口下次提问按顺序取。
    """

    def __init__(self, session, *, live_get, get_frame, on_eof):
        self.session = session
        self._live_get = live_get        # () -> Live | None（跑阶段上屏才不空）
        self._get_frame = get_frame      # () -> 当前帧 Text（Live 重画用）
        self._on_eof = on_eof            # Ctrl-D / Ctrl-C：中止整场会话
        self.lines = asyncio.Queue()
        self.task = None                 # 读会话的任务（含正在收摊的）
        self.reader = None               # 读会话本身（DummyOutput，不渲染）
        self.typed = ""                  # 正在敲的字，画进 Live 帧最底一行
        self.kick_pending = False

    async def _loop(self):
        try:
            while True:
                got = await self.reader.prompt_async()
                await self.lines.put(got)
        except (EOFError, KeyboardInterrupt):
            # 运行中 Ctrl-D / Ctrl-C：和谈阶段一样就地收手
            self._on_eof()
        except asyncio.CancelledError:
            return                     # 树跑完了，正常收摊

    def kick(self):
        """排一场 kick；上一场还挂着就不再排（两场并发会互相等，输入就死了）。"""
        if self.kick_pending:
            return
        self.kick_pending = True
        asyncio.ensure_future(self._kick())

    async def _kick(self):
        """开跑阶段的读会话，先等上一棵树的会话真正收摊再 attach 新的。"""
        try:
            await self.settle()
            if not sys.stdout.isatty() or self._live_get() is None:
                return
            self.reader = _session_of("", self.session.history, self.session.app.input,
                                      DummyOutput())

            def _on_text_changed(_):
                self.typed = self.reader.default_buffer.document.text
                live = self._live_get()
                if live is not None:
                    live.update(self._get_frame(), refresh=True)

            self.reader.default_buffer.on_text_changed += _on_text_changed
            self.task = asyncio.ensure_future(self._loop())
        finally:
            self.kick_pending = False

    def stop(self):
        if self.task is not None:
            self.task.cancel()

    async def settle(self):
        """收摊：等读会话真正退出（detach 完）再往下走；没挂着就什么都不做。"""
        t, self.task = self.task, None
        if t is None:
            return
        try:
            await t
        except asyncio.CancelledError:
            pass


async def opening(session=None):
    """入口开口之前先让用户把要做的事说完，否则种子是空的、模型只会问一句"你要做什么"。"""
    session = session or _session()
    return await _listen(session)


def _fit(lines, max_h):
    """树高于屏幕就折没在跑的段落，带实时输出（▸）的节点行永远留着 —— Live 原地重画要求区域高度 ≤ 终端高度。"""
    if len(lines) <= max_h:
        return lines
    live = [i for i, ln in enumerate(lines) if "▸" in ln]
    keep = sorted(set([0] + live))[:max_h]
    out = []
    prev = -1
    for k in keep:
        if k - prev > 1:
            out.append("… %d 行折叠" % (k - prev - 1))
        out.append(lines[k])
        prev = k
    if prev < len(lines) - 1:
        out.append("… %d 行折叠" % (len(lines) - 1 - prev))
    return out[:max_h]


def _show_resumed(store):
    """把重建出来的老会话画给人看，先让他看见接的是什么。"""
    print("\n[会话] 已加载：%s" % store.path)
    for ln in render_tree(store.root, store.registry):
        print("  " + ln)
    print("", flush=True)


async def run_session(a, session=None):
    """装配运行现场，-r 时选老会话读回整棵树，然后进终端话轮；模型由 converse 自己建。"""
    session = session or _session()
    print("[工作目录] %s" % cfg.WORKSPACE, flush=True)
    print("[并发] %d" % cfg.WORKERS, flush=True)
    print("[限制] 无。轮次/深度/节点/token/时间 全部不限，停止交给 API 自己", flush=True)

    if a.resume:
        sessions = Store.roots()
        if not sessions:
            print("没有可加载的老会话：工作区里还没有跑过任何树。", flush=True)
            return 1
        picked = await pick_session(sessions)
        if picked is None:
            print("取消。", flush=True)
            return 0
        try:
            store = Store.load(picked)
        except ValueError:
            # 数据损坏就带着是哪个会话炸出来，不静默跳过
            print("读不了这个会话（数据损坏，或不是当前格式）：%s" % picked, flush=True)
            raise
        env = {"store": store}
        _show_resumed(store)
    else:
        task = await opening(session)
        env = {"store": Store.new(Node(name="会话", kind=INTAKE),
                                  seed=intake_seed(task))}
    print("[trace] %s\n" % os.path.abspath(env["store"].path), flush=True)

    # 落盘由 run 兜底
    return await converse(env, session=session)


async def converse(env, session=None):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口不退场：谈成一个任务就挂到树上跑掉、结论带回对话再接着谈；整场会话是一棵树。
    env 是运行现场（含一份 store，由 run_session 建好），session 是读的那条通道。
    """
    session = session or _session()
    # Console 在这里建而不是模块级：它按当下的 stdout 判断是不是终端。
    console = Console()
    color = console.color_system is not None

    def piece(text, gray=False):
        """吐字：不加换行、立刻刷出；关掉 markup / highlight，不改模型的原话。"""
        if text:
            console.print(text, style="dim" if gray and color else None, end="",
                          markup=False, highlight=False, soft_wrap=True)

    def line(text):
        # 关掉 highlight：旁白和树是事实的原文，不是给 rich 美化的
        console.print(text, markup=False, highlight=False)

    def narrate(text):
        # 旁白可能是一整棵任务树（多行）：每行都缩进，不挤到行首
        line("  " + str(text).replace("\n", "\n  "))

    line("\n[入口] 把预期谈定，能过闸门就当场拿去跑，跑完接着谈。")
    line("       回车发送；想分几行写就按 Alt-Enter；跑任务时底下仍可输入。")
    line("       灰色的字是它在想。不想聊了按 Ctrl-D。\n")

    # 这一轮的状态：spoke / thinking（吐没吐过话）、live_ref / root_ref / running /
    # session_root / streams（跑阶段实时视图）、intake_task（整场会话的 run 任务）、
    # run_input（跑阶段读输入通道，见 `RunInput`）。
    spoke = [False]                # 这一轮模型有没有往屏幕上吐过话
    thinking = [False]             # 这一轮刚吐过的是不是思考
    live_ref = [None]
    root_ref = [None]
    running = [False]              # 有任务在跑才上屏 / 开运行输入
    session_root = [None]          # 入口节点（会话根）
    streams = {}                   # node_id -> {"thinking","speaking"} 尾巴
    intake_task = [None]
    run_input = RunInput(session=session,
                         live_get=lambda: live_ref[0],
                         get_frame=lambda: current_frame(),
                         on_eof=lambda: intake_task[0].cancel())

    async def ask(question):
        # 话在吐字时已显示过；没吐过才补一遍，否则同一个问题显示两遍。
        if spoke[0]:
            console.print()
        else:
            line(question)
        spoke[0] = False
        await run_input.settle()
        while True:
            if not run_input.lines.empty():
                got = run_input.lines.get_nowait()
                if got.strip():
                    line("  （运行中你输入了，按顺序交给你：%s）" % got)
                    return got
                continue
            got = await _listen(session)
            if got.strip():
                return got
            line("（回车发的是空行——Ctrl-D 结束，或重新输入）")

    # ── 任务树实时视图 ──
    # 调度器开 / 关节点发 loop_start / loop_end、吐字发 message_update；终端收到就重画整棵树。
    # 真终端用 rich Live 原地重画，非真终端逐帧追加；任务根出结论 = 这一轮跑完，留最后一帧。
    # 会话 = 一棵树（入口为根），registry 是 run() 登记的运行态，终端靠它画树。
    store = env["store"]
    registry = store.registry
    session_root[0] = store.root

    def current_frame():
        # 跑时每节点一行（compact），任务根出结论那帧切回详细视图（判定/验收/结论都在）
        compact = root_ref[0] is not None and not root_ref[0].verdict
        lines = render_tree(root_ref[0], registry, streams=streams, compact=compact)
        if live_ref[0] is not None and compact:
            rows = _fit(lines, max(1, console.height - 1)) + [PROMPT + run_input.typed]
        else:
            rows = lines
        # no_wrap + crop：一换行 Live 区域高度就对不上、输入行会被挤掉
        return Text("\n".join(rows), overflow="crop", no_wrap=True)

    def redraw():
        if not running[0]:
            return                     # 谈阶段不上屏：屏幕上只有对话
        frame = current_frame()
        if live_ref[0] is not None:
            # 只换渲染内容不立刻重画，重画交给 Live 的刷新线程（键盘除外）
            live_ref[0].update(frame)
        else:
            narrate(frame)

    def _push_stream(node_id, key, text):
        # 整段留着不截，节点出结论时由 loop_end 删掉
        if not text:
            return
        buf = streams.setdefault(node_id, {"thinking": "", "speaking": ""})
        buf[key] = buf[key] + text
        if live_ref[0] is not None:
            live_ref[0].update(current_frame())

    # ── 事件路由：一个函数收全部事实，按 scope 分路去画 ──
    # scope=入口节点 id 走对话通道，其余 scope 是节点 id；事件只报事实，怎么画是终端的事。
    def on_sink(type, payload):
        scope = payload.get("scope")
        sroot = session_root[0]
        if sroot is not None and scope == sroot.id:
            if type == "message_update":
                delta = payload.get("delta") or ""
                if payload.get("kind") == "reasoning":
                    thinking[0] = True
                    piece(delta, gray=True)
                else:
                    if thinking[0]:        # 想完了，开始说：换行，把回答和思考分开
                        thinking[0] = False
                        piece("\n")
                    spoke[0] = True
                    piece(delta)
            return
        if type == "message_update":
            _push_stream(scope, "thinking" if payload.get("kind") == "reasoning"
                         else "speaking", payload.get("delta") or "")
            return
        node = payload.get("node") or registry.get(scope)
        if node is None:
            return

        if type == "loop_start":
            if is_task_root(node, registry) and not node.verdict:
                running[0] = True
                root_ref[0] = node
                if live_ref[0] is None and sys.stdout.isatty():
                    live_ref[0] = Live(console=console, vertical_overflow="crop",
                                       refresh_per_second=10)
                    live_ref[0].start()
                    run_input.kick()
            redraw()
        elif type == "loop_end":
            streams.pop(scope, None)      # 出结论就不留实时尾巴
            redraw()
            if is_task_root(node, registry):
                running[0] = False
                run_input.stop()
                if live_ref[0] is not None:
                    live_ref[0].stop()
                    live_ref[0] = None

    llm = LLM()
    intake_task[0] = asyncio.ensure_future(
        run(store, llm, subscribe=on_sink, ask=ask, say=narrate))
    try:
        await intake_task[0]
    except (_Quit, asyncio.CancelledError):
        # 谈阶段 Ctrl-D / 跑阶段 Ctrl-D|Ctrl-C：就地收手，不是错误
        line("\n[入口] 你在终端上中止了。")
        return None
    finally:
        run_input.stop()
        await run_input.settle()
        if live_ref[0] is not None:   # 中止也可能发生在跑的过程中
            live_ref[0].stop()
            live_ref[0] = None
    return None
