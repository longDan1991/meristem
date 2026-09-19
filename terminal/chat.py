"""和入口在终端上把预期谈定，并把入口跑出来的东西显示给人看。

这里只做两件事：把用户敲的字交回去、把入口说的话显示出来。
判断、打回、跑任务、收手全在 `tree/intake.py` 里 —— 不在这里再实现一遍，
否则"什么算合规"就有了两个事实。

三条通道分开，终端才不会把同一句话显示两遍：
  - 模型说的话（一段纯文本）走 `ask` 通道；
  - 模型的思考（`reasoning_content`）走 `on_reasoning` 通道，**画成灰的**；
  - 旁白（"接到任务 / 跑完了"）走 `on_say` 通道。

**读**交给 prompt_toolkit：回车发送、方向键改已经敲的字、上下键翻历史、粘贴
多行当一条、Ctrl-D 退出。自己拿 `input()` 拼是拼不出这些的 —— 敲完的一行就
改不了了、没有历史、粘贴进来的多行会被当成好几句。要分几行写按 Alt-Enter：
换行是一个**独立**的键，绝不去动发送键 —— 终端送上来的是 CR 还是 LF 不该由
我们猜（实测：把 `c-j` 绑成换行，某些调用路径下回车会被吃成换行、发送发不出去）。

**显示**交给 rich（灰、Live 原地重画）。终端只负责**什么时候画、怎么显示**，
不自己重写画法：树的视图 `render_tree` 在 `tree/protocol/fields.py` ——
树长什么样是树的变因。

模型的吐字是**真流式**：不是等整段回来再一个字一个字放，而是每到一个字
就立刻写到屏幕上。交形式是**工具调用**（`submit_root`），走的是另一条通道，
上不了屏幕 —— 那是给闸门的，不是给人看的。所以 `ask` 不再负责显示模型的话，
它只负责**读**：话已经在吐字时显示过了。
"""

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


async def converse(llm, seed, env, session=None):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口现在**不退场**：每谈成一个任务就跑掉、把结论带回来接着谈。
    所以这里没有"交棒"这一步 —— 跑树是 `tree/intake.py` 的事，
    终端只负责介质与话轮。

    env 是运行现场（trace/caps/index/budget/workers/registry），终端不解释它，
    只转给入口；session 是读的那条通道（测试把管道驱动的会话塞进来）。
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

    async def ask(question):
        # 话在吐字时已经显示过了（连换行都是它的一部分）；没吐过（比如被当成
        # 形式按住、其实不是形式）才由这里补一遍，否则同一个问题会显示两遍。
        # 吐字是不加换行的，所以这里把提示符收拢到下一行开头。
        if spoke[0]:
            console.print()
        else:
            line(question)
        spoke[0] = False
        return await _listen(session)

    def narrate(text):
        # 旁白可能是一整棵任务树（多行）：每行都缩进，不挤到行首
        line("  " + str(text).replace("\n", "\n  "))

    line("\n[入口] 把预期谈定，能过闸门就当场拿去跑，跑完接着谈。")
    line("       回车发送；想分几行写就按 Alt-Enter。")
    line("       灰色的字是它在想。不想聊了按 Ctrl-D。\n")

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

    # ── 任务树实时视图 ──
    # 调度器每开/关一个节点就发一个 on_event（见 runtime/scheduler.py）；
    # 终端收到就把**当前整棵树**重画一次：真终端用 rich Live 原地重画
    # （跑的时候终端上没有别的东西在写，这一块只属于树），不是真终端
    # （测试 / 管道）就逐帧追加。根的出生（parent 是 None 且 running）
    # = 新任务开始，根出结论 = 这一轮跑完，把最后一帧留在屏幕上。
    live_ref = [None]
    root_ref = [None]

    def on_event(node):
        if node.parent is None and node.status == "running":
            root_ref[0] = node
            if live_ref[0] is None and sys.stdout.isatty():
                live_ref[0] = Live(console=console, vertical_overflow="visible")
                live_ref[0].start()
        # 帧用 Text 而不是裸 str：裸 str 会被 rich 当 markup/高亮处理，
        # 把 `[满足]` 的方括号加粗、日期数字上色 —— 那是树的原文，不是给它美化的。
        frame = Text("\n".join(render_tree(root_ref[0], env.get("registry") or {})))
        if live_ref[0] is not None:
            live_ref[0].update(frame)
        else:
            narrate(frame)
        if node.parent is None and node.status != "running" and live_ref[0] is not None:
            live_ref[0].stop()
            live_ref[0] = None

    env = dict(env, on_event=on_event)
    try:
        await intake(llm, seed, ask=ask, env=env,
                     on_say=narrate,
                     on_delta=on_delta, on_reasoning=on_reasoning)
    except _Quit:
        line("\n[入口] 你在终端上中止了。")
        return None
    finally:
        if live_ref[0] is not None:   # 中止也可能发生在跑的过程中
            live_ref[0].stop()
            live_ref[0] = None
    return None
