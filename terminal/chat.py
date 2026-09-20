"""和入口在终端上把预期谈定，并把入口跑出来的东西显示给人看。

这里只做两件事：把用户敲的字交回去、把入口说的话显示出来。
判断、打回、跑任务、收手全在 `tree/intake.py` 里 —— 不在这里再实现一遍，
否则"什么算合规"就有了两个事实。

三条通道分开，终端才不会把同一句话显示两遍：
  - 模型说的话（一段纯文本）走 `ask` 通道；
  - 模型的思考（`reasoning_content`）走 `on_reasoning` 通道，**画成灰的**；
  - 旁白（"接到任务 / 跑完了"）走 `on_say` 通道。
  - 树里每个节点的吐字走节点级的 `on_delta / on_reasoning`（带 node_id），
    画进任务树跟着 Live 原地重画 —— 树在跑，看得见每个节点正在说什么。

**读**交给 prompt_toolkit：回车发送、方向键改已经敲的字、上下键翻历史、粘贴
多行当一条、Ctrl-D 退出。自己拿 `input()` 拼是拼不出这些的 —— 敲完的一行就
改不了了、没有历史、粘贴进来的多行会被当成好几句。要分几行写按 Alt-Enter：
换行是一个**独立**的键，绝不去动发送键 —— 终端送上来的是 CR 还是 LF 不该由
我们猜（实测：把 `c-j` 绑成换行，某些调用路径下回车会被吃成换行、发送发不出去）。

**任务跑的时候输入不冻结**：树的 Live 接管屏幕（树 + 每个节点的实时吐字 +
最底下一行输入），同时开一条**不渲染**的 prompt_toolkit 会话（DummyOutput）
读键盘 —— 它只读不画，画是 rich 的事。一个屏幕只有一个画家：rich 和
prompt_toolkit 各画一遍会把光标位置搞乱（实测）。敲下的行先进队列，入口下次
提问时按顺序交给它；运行中按 Ctrl-D / Ctrl-C 就是中止整个会话。

**实时视图每节点一行铺开**：跑的时候树用 `render_tree(compact=True)` ——
`· [叶子] 子任务B  ▸ 思考: …`，整棵树按结构铺开，**所有节点正在吐的字都
占一行看得见**，谁也不被折掉（屏幕放不下时只折没在跑的段落）；根出结论那帧
切回详细视图（判定/验收/结论都在，Live 收摊时整幅渲染、能滚动）。

**显示**交给 rich（灰、Live 原地重画）。终端只负责**什么时候画、怎么显示**，
不自己重写画法：树的视图 `render_tree` 在 `tree/protocol/fields.py` ——
树长什么样是树的变因。

模型的吐字是**真流式**：不是等整段回来再一个字一个字放，而是每到一个字
就立刻写到屏幕上。交形式是**工具调用**（`submit_root`），走的是另一条通道，
上不了屏幕 —— 那是给闸门的，不是给人看的。所以 `ask` 不再负责显示模型的话，
它只负责**读**：话已经在吐字时显示过了。
"""

import asyncio
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.output import DummyOutput
from rich.console import Console
from rich.live import Live
from rich.text import Text

from tree.intake import intake
from tree.protocol.fields import render_tree

PROMPT = "› "

KEYS = KeyBindings()


def _newline(event):
    """回车是发送，换行得是一个**不含糊的独立动作** —— 说一句话分几行写。

    只绑 Alt-Enter（`escape,enter`）。**不绑 `c-j`**：终端送上来的是 CR 还是 LF
    不该由我们猜，拿 `c-j` 去顶换行会在某些路径下把回车也吃成换行（实测：
    `prompt_async` 一去不回，buffer 里多出一个 `\n`）。
    """
    event.current_buffer.insert_text("\n")


KEYS.add("escape", "enter")(_newline)


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C。

    这是终端上的常态，不是错误 —— 所以不往上抛，就地收手。
    """


def _session(inp=None):
    """一条会话。历史要跨问题、跨 `opening` 和 `converse` 都留着，所以建一次就够。

    `inp` 只给测试用：塞一条管道进去，键位与历史上走的还是同一套 ——
    测试因此驱的是**真的输入路径**，不是一个替身。
    """
    return PromptSession(message=PROMPT, history=InMemoryHistory(),
                         key_bindings=KEYS, input=inp,
                         output=DummyOutput() if inp is not None else None)


async def _listen(session):
    """读一条回答。编辑 / 历史 / 粘贴 / Ctrl-D 全是 prompt_toolkit 的事。

    `prompt_async` 不是可选的美化：同步的 `prompt()` 在运行中的事件循环里
    直接 `RuntimeError`（实测），而这里就活在 asyncio 里。
    """
    try:
        return await session.prompt_async()
    except (EOFError, KeyboardInterrupt):
        raise _Quit() from None


async def opening(session=None):
    """入口开口之前，先让用户把要做的事说完 —— 用户没在命令行交底时走这里。

    否则种子是空的，那一次模型调用只够换来一句"你要做什么？"（实测），
    看上去就像程序没等你说话就自作主张。
    """
    session = session or _session()
    print("\n[入口] 先说你要做什么？可以粘多行；要换行按 Alt-Enter，回车就是发送。\n",
          flush=True)
    return await _listen(session)


# 树里每个节点的实时尾巴只留这么多字：节点出结论就删，屏幕只画最后一段 ——
# 内存和屏宽都有界，模型吐多长都不该把这块撑成无界缓存（AGENTS §11）。
_STREAM_SHOW = 140         # 存进 streams / 画进树的尾巴长度


def _fit(lines, max_h):
    """树比屏幕高就折：**带实时输出（▸）的节点行永远留着**，折掉的是没在
    跑的段落 —— 折了谁也折不掉正在吐字的节点（用户要的就是每个节点正在
    说什么都看得见）。

    rich Live 原地重画的硬前提是区域高度 ≤ 终端高度 —— 超出会向上翻屏、
    光标对不上，画面就花了（实测 `vertical_overflow="visible"` 的大树）。
    所以这里自己先裁好，Live 只做"不越界"的兜底。
    """
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


async def converse(llm, seed, env, session=None, resume=None):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口现在**不退场**：每谈成一个任务就跑掉、把结论带回来接着谈。
    所以这里没有"交棒"这一步 —— 跑树是 `tree/intake.py` 的事，
    终端只负责介质与话轮。

    env 是运行现场（trace/budget/workers/registry），终端不解释它，
    只转给入口；session 是读的那条通道（测试把管道驱动的会话塞进来）。

    resume：可选的恢复包（`session.load` 出来的）—— 会话重启后接着谈：
    先把已加载的会话画给人看（"加载并显示"），再让入口从恢复的对话继续。
    """
    session = session or _session()
    # 上不上色交给 rich 判断：isatty / NO_COLOR / 颜色系统它都处理。
    # Console 在**这里**建而不是模块级：它按当下的 stdout 判断是不是终端。
    console = Console()
    color = console.color_system is not None

    def piece(text, gray=False):
        """吐字：不加换行、立刻刷出来 —— 模型吐一个字就看见一个字。

        markup / highlight 必须关掉：这是**模型的原话**，rich 默认会把
        `[red]` 这类东西当样式、把日期数字自动上色 —— 那是在改它说的话。
        """
        if text:
            console.print(text, style="dim" if gray and color else None, end="",
                          markup=False, highlight=False, soft_wrap=True)

    def line(text):
        # highlight 也要关：rich 默认会把 `[…]`、日期、数字自动加粗上色 ——
        # 旁白和树是**事实的原文**，不是给它美化的（实测：`[入口]` 会被拆成粗体括号）。
        console.print(text, markup=False, highlight=False)

    def narrate(text):
        # 旁白可能是一整棵任务树（多行）：每行都缩进，不挤到行首
        line("  " + str(text).replace("\n", "\n  "))

    line("\n[入口] 把预期谈定，能过闸门就当场拿去跑，跑完接着谈。")
    line("       回车发送；想分几行写就按 Alt-Enter；跑任务时底下仍可输入。")
    line("       灰色的字是它在想。不想聊了按 Ctrl-D。\n")

    if resume is not None:
        line("\n[会话] 已加载：%s" % resume["path"])
        for t in resume["trees"]:
            narrate("\n".join(render_tree(t["root"], t["registry"])))
        line("")

    spoke = [False]                # 这一轮模型有没有往屏幕上吐过话
    thinking = [False]             # 这一轮刚吐过的是不是思考

    def on_reasoning(text):
        thinking[0] = True
        piece(text, gray=True)

    def on_delta(text):
        if thinking[0]:        # 想完了，开始说：换行，把回答和思考分开
            thinking[0] = False
            piece("\n")
        spoke[0] = True
        piece(text)

    # ── 输入通道 ──
    # 谈阶段用会话直接读（`_listen`）；跑阶段用另一条**不渲染**的会话读 ——
    # 画是 rich 的，prompt_toolkit 只读不画，一个屏幕只有一个画家。
    # 两条会话共用同一根 stdin 与同一本历史，但**绝不同时挂 reader**：
    # 跑阶段开、跑完收，谈阶段才轮到 `_listen`。收和开都是异步的，
    # 不等到旧的真正 detach 就开新的，两个 reader 会互相顶掉、输入变死
    # （实测）—— 所以换手一律 await（`_kick_run_input` / `_drain_run_input`）。
    # 敲下的行先进队列，入口下次提问按顺序取 ——
    # "运行中敲的东西先收着，怎么影响正在跑的树以后再定"。
    lines = asyncio.Queue()
    run_task = [None]                  # 跑阶段那条读会话的任务（含正在收摊的）
    run_session = [None]               # 跑阶段那条会话本身（DummyOutput，不渲染）
    input_line = [""]                  # 跑阶段正在敲的字，画进 Live 帧最底一行

    async def ask(question):
        # 话在吐字时已经显示过了（连换行都是它的一部分）；没吐过（比如被当成
        # 形式按住、其实不是形式）才由这里补一遍，否则同一个问题会显示两遍。
        # 吐字是不加换行的，所以这里把提示符收拢到下一行开头。
        if spoke[0]:
            console.print()
        else:
            line(question)
        spoke[0] = False
        await _drain_run_input()
        if not lines.empty():
            got = lines.get_nowait()
            line("  （运行中你输入了，按顺序交给你：%s）" % got)
            return got
        return await _listen(session)

    # ── 任务树实时视图 ──
    # 调度器每开/关一个节点就发一个 on_event，每个节点的吐字按 node_id 送来
    # （见 runtime/turn.py 的接线）；终端收到就把**当前整棵树**重画一次：
    # 真终端用 rich Live 原地重画（跑的时候终端上没有别的东西在写，
    # 这一块只属于树），不是真终端（测试 / 管道）就逐帧追加。
    # 根的出生（parent 是 None 且 running）= 新任务开始，根出结论 = 这一轮跑完，
    # 把最后一帧留在屏幕上。树比屏幕高就折叠中间，**最底一行永远是输入行**。
    live_ref = [None]
    root_ref = [None]
    streams = {}                       # node_id -> {"thinking","speaking"} 尾巴

    def current_frame():
        # 跑的时候用**每节点一行**的实时视图（compact：整棵树铺开，每个节点
        # 正在吐的字都占一行看得见）；根出结论那帧切回详细视图 —— 判定/验收/
        # 结论都在，那才是跑完的完整结果（Live 收摊时整幅渲染，能滚动）。
        compact = root_ref[0] is not None and root_ref[0].status == "running"
        tree = render_tree(root_ref[0], env.get("registry") or {},
                           streams=streams, compact=compact)
        if live_ref[0] is not None and compact:
            rows = _fit(tree, max(1, console.height - 1)) + [PROMPT + input_line[0]]
        else:
            rows = tree
        # no_wrap + crop：每一行都在终端宽度处裁掉，不换行 ——
        # Live 的区域高度按行数算，一换行高度就对不上，输入行会被挤掉。
        return Text("\n".join(rows), overflow="crop", no_wrap=True)

    def redraw():
        frame = current_frame()
        if live_ref[0] is not None:
            # 只换渲染内容，不强迫立刻重画：快跑完的树（测试 / 短任务）不该
            # 一帧一帧往外漏，重画交给 Live 的刷新线程按节拍来，收摊时再
            # 补最后一笔。键盘除外（见 _on_text_changed）。
            live_ref[0].update(frame)
        else:
            narrate(frame)

    def _push_stream(node_id, key, text):
        # 只留尾巴，节点出结论时由 on_event 删掉 —— 有界（§11）
        if not text:
            return
        buf = streams.setdefault(node_id, {"thinking": "", "speaking": ""})
        buf[key] = (buf[key] + text)[-_STREAM_SHOW:]
        if live_ref[0] is not None:
            live_ref[0].update(current_frame())

    def node_delta(node_id, text):
        _push_stream(node_id, "speaking", text)

    def node_reasoning(node_id, text):
        _push_stream(node_id, "thinking", text)

    intake_task = [None]
    kick_pending = [False]             # 一棵树还没跑完又开一棵时，kick 不许并发

    async def _run_input_loop():
        """跑阶段读输入：只读不画，敲下的行进队列，Ctrl-D/Ctrl-C 中止整个会话。"""
        try:
            while True:
                got = await run_session[0].prompt_async()
                await lines.put(got)
        except (EOFError, KeyboardInterrupt):
            # 运行中按 Ctrl-D / Ctrl-C：和谈阶段一样，就地收手
            intake_task[0].cancel()
        except asyncio.CancelledError:
            return                  # 树跑完了，正常收摊

    def _kick():
        """排一场 kick。上一场的 kick 还挂着就不再排 —— 两场并发会互相
        等（一场 await 另一场正在读输入的任务），输入就死了（实测）。"""
        if kick_pending[0]:
            return
        kick_pending[0] = True
        asyncio.ensure_future(_kick_run_input())

    async def _kick_run_input():
        """开跑阶段的读会话。先等上一棵树的会话收摊（取消是异步的，不等到它
        detach 就 attach 新的，reader 会互相顶掉、输入变死 —— 实测）。"""
        try:
            if run_task[0] is not None:
                try:
                    await run_task[0]
                except asyncio.CancelledError:
                    pass
                run_task[0] = None
            if not sys.stdout.isatty() or not live_ref[0]:
                return
            run_session[0] = PromptSession(message="", history=session.history,
                                           key_bindings=KEYS,
                                           input=session.app.input,
                                           output=DummyOutput())

            def _on_text_changed(_):
                # 敲一个字符就把 Live 帧最底一行的输入同步过去（只 rich 画）
                input_line[0] = run_session[0].default_buffer.document.text
                if live_ref[0] is not None:
                    live_ref[0].update(current_frame(), refresh=True)

            run_session[0].default_buffer.on_text_changed += _on_text_changed
            run_task[0] = asyncio.ensure_future(_run_input_loop())
        finally:
            kick_pending[0] = False

    def _stop_run_input():
        if run_task[0] is not None:
            run_task[0].cancel()

    async def _drain_run_input():
        """跑阶段收摊：等读会话真正退出（detach 完）再往下走。"""
        if run_task[0] is not None:
            t, run_task[0] = run_task[0], None
            try:
                await t
            except asyncio.CancelledError:
                pass

    def on_event(node):
        if node.parent is None and node.status == "running":
            root_ref[0] = node
            if live_ref[0] is None and sys.stdout.isatty():
                live_ref[0] = Live(console=console, vertical_overflow="crop",
                                   refresh_per_second=10)
                live_ref[0].start()
                _kick()
        if node.status != "running":
            streams.pop(node.id, None)      # 出结论就不留它的实时尾巴
        redraw()
        if node.parent is None and node.status != "running":
            _stop_run_input()
            if live_ref[0] is not None:
                live_ref[0].stop()
                live_ref[0] = None

    # 节点级吐字只对真终端开：管道 / 重定向没有 Live，也没有人会看见它，
    # 不给节点级的 llm.chat 平白开 SSE。
    env = dict(env, on_event=on_event)
    if sys.stdout.isatty():
        env = dict(env, on_delta=node_delta, on_reasoning=node_reasoning)

    msgs = (resume["chat_msgs"] or None) if resume is not None else None
    resume_tree = resume["in_flight"] if resume is not None else None
    intake_task[0] = asyncio.ensure_future(
        intake(llm, seed, ask=ask, env=env,
               on_say=narrate, on_delta=on_delta, on_reasoning=on_reasoning,
               msgs=msgs, resume_tree=resume_tree))
    try:
        await intake_task[0]
    except _Quit:
        line("\n[入口] 你在终端上中止了。")
        return None
    except asyncio.CancelledError:
        # 运行中 Ctrl-D / Ctrl-C：intake 正跑着树被中止
        line("\n[入口] 你在终端上中止了。")
        return None
    finally:
        _stop_run_input()
        await _drain_run_input()
        if live_ref[0] is not None:   # 中止也可能发生在跑的过程中
            live_ref[0].stop()
            live_ref[0] = None
    return None
