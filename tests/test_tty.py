#!/usr/bin/env python3
"""终端会话的定向测试（零成本、确定性：脚本化模型 + 脚本化终端 + 真调度器）。

这一层只管介质与话轮，判断 / 打回 / 跑树 / 收手都在运行时层，终端只把整场会话丢给 `run`。

读不替身：往真的 prompt_toolkit 会话塞管道（`create_pipe_input`），键位走生产同一套；
显示把 stdout 换成假终端，rich 的判断照旧生效。

  A. 谈定：问 → 答 → 交出的任务被跑掉；问题和建议只显示一遍
  B. 吐字：一小口一小口吐、吐完才轮到读
  C. 读：回车发送、上下键翻历史、Alt-Enter 换行、粘贴多行、Ctrl-D 收手
  D. 思考整段流式吐出，而且是灰的（真终端才上色）
  E. 旁白显示到终端；交形式不吐
  F. 边界守门：terminal 不碰决策层；tree 不 import terminal
  G. 不是真终端（管道 / 重定向）→ 树逐帧追加
  H. 真终端：任务树用 rich Live 原地重画，跑完那帧留屏
  I. 用户没交底：入口开口前先让他把话说完
  J. 节点级吐字：每个节点正在想/说的话画进它的节点下（真终端）
  K. 跑任务时输入不冻结：敲的字进 Live 帧，跑完按顺序交出去
  L. 每节点一行铺开：所有节点正在吐的字都看得见（真终端）
  M. 树视图：非最后一个孩子画竖线、最后一个收尾（缩进只由 is_last 决定）
  N. 事件词汇：工具与用量事件到达终端（tool_start/tool_end/usage）
  O. 折叠渲染：跑完的子树折一行带统计，活跃路径展开（render_folded）
  P. 流渲染：选中节点的 msgs + 实时尾巴（render_stream）
"""

import asyncio
import ast
import contextlib
import io
import os
import re
import sys
import tempfile

from harness import OK, line, ROOT
import terminal.chat as chat
from terminal.view import render_folded, render_stream, render_tree
from prompt_toolkit.input import create_pipe_input
from core.llm import Message, ToolCall
from core.protocol.fields import Node
from core.runtime import store as store_mod
from core.runtime.loop import run
from core.runtime.store import Store

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TIMEOUT = 30


@contextlib.contextmanager
def _tty_env():
    """把颜色相关的环境摆成"真终端"。

    rich 按 TERM / NO_COLOR / FORCE_COLOR / TTY_COMPATIBLE 决定上不上色
    （`converse` 里 `console.color_system is not None` 就是照它的判断走），
    环境里带着 NO_COLOR=1 或 TERM=dumb 时上色被关掉、带着 FORCE_COLOR 时又被硬开，
    不改环境的话断言就变成在考环境而不是考代码。
    """
    keys = ("TERM", "NO_COLOR", "FORCE_COLOR", "TTY_COMPATIBLE")
    old = {k: os.environ.get(k) for k in keys}
    os.environ["TERM"] = "xterm-256color"
    for k in keys[1:]:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class Screen(io.StringIO):
    """假终端：整段文本与每次 write 的碎片都留着（一次吐字一次 write）。"""

    def __init__(self, tty=False):
        super().__init__()
        self.pieces = []
        self._tty = tty

    def isatty(self):
        return self._tty

    def write(self, text):
        self.pieces.append(text)
        return super().write(text)

    def plain(self):
        """去掉颜色码的原文 —— 上没上色是另一条断言的事。"""
        return ANSI.sub("", self.getvalue())


def _env(seed=None):
    """一次会话一棵树：新会话（入口为根），记录根初始化到临时目录。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    return {"store": Store.new(Node(name="会话", kind="intake"), seed=seed)}


class FakeLLM:
    """按脚本回话，同时服务入口（字符串 = 说话、带 root 的 dict = submit_root）与任务节点。

    任务节点动手一次就出满足结论；`slow` 时慢吐，给终端画树、跑阶段输入留时间。
    """

    def __init__(self, replies, reasoning="", screen=None, slow=False, kids=1):
        self.replies, self.said = list(replies), []
        self.seen = []
        self.reasoning, self.screen = reasoning, screen
        self.at_return, self.snapshots, self.slow, self.kids = [], [], slow, kids
        self._spawned = False
        self._did_bash = False

    async def _drip(self, on, text):
        """一小口一小口吐；slow 时每口之间睡一下（真终端才看得见过程）。"""
        for i in range(0, len(text), 5):
            on(text[i:i + 5])
            if self.slow:
                await asyncio.sleep(0.08)

    async def _task_chat(self, messages, on_delta, on_reasoning):
        sysmsg = messages[0]["content"]
        if "你是一个叶子" in sysmsg:
            done = any(m.get("role") == "tool" for m in messages)
            if not done:
                think = ("先看看用户到底要什么，再决定怎么拆。然后想清楚第一步做什么。" * 4)
                if on_reasoning:
                    await self._drip(on_reasoning, think)
                reply = "我要拆成三个子任务。"
                if on_delta:
                    await self._drip(on_delta, reply)
                return Message(text=reply, tool_calls=[ToolCall(
                    name="bash", arguments={"command": "echo hi"})])
            return Message(text="", tool_calls=[ToolCall(
                name="conclude", arguments={"verdict": "满足", "text": "跑完了",
                                            "evidence": ["第1次观测"]})])
        kids_names = ["子任务%s" % c for c in "ABC"][:self.kids]
        have_result = any("下层结论" in str(m.get("content", ""))
                          for m in messages)
        if not self._spawned:
            self._spawned = True
            return Message(text="", tool_calls=[ToolCall(
                name="create_children", arguments={"children": [
                    {"name": n, "detail": "d", "notes": "",
                     "accept": "2026-12-31 收盘 >= 1（%s 负责）" % n,
                     "kind": "leaf", "gate": False, "conc_range": [1, 10]}
                    for n in kids_names]})])
        if not have_result:
            return Message(text="", tool_calls=[ToolCall(
                name="conclude", arguments={"verdict": "满足",
                                            "text": "先等孩子回来"} )])
        return Message(text="", tool_calls=[ToolCall(
            name="conclude", arguments={"verdict": "满足", "text": "全部完成",
                                        "evidence": [kids_names[0]]})])

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.said.append(messages[-1]["content"])
        self.seen.append(messages[-1]["content"])
        if "把用户的意图" not in messages[0]["content"]:
            return await self._task_chat(messages, on_delta, on_reasoning)
        spec = self.replies.pop(0) if self.replies else ""
        if isinstance(spec, dict) and "root" in spec:
            reply, calls = "", [ToolCall(name="submit_root",
                                         arguments={"root": spec["root"]})]
        else:
            reply, calls = str(spec or ""), []
        if self.reasoning and on_reasoning:
            await self._drip(on_reasoning, self.reasoning)
        if on_delta:
            for i in range(0, len(reply), 5):
                on_delta(reply[i:i + 5])
                if self.screen is not None:      # 每吐一口，屏幕当时长什么样
                    self.snapshots.append(self.screen.plain())
        if self.screen is not None:
            self.at_return.append(self.screen.plain())
        return Message(text=reply, tool_calls=calls)


async def _typed(inp, keys, pause=0.1):
    """一条一条敲：一次全灌进去会丢掉方向键（上箭头拿不回历史）。"""
    for k in keys:
        await asyncio.sleep(pause)
        inp.send_text(k)


async def _typed_sched(inp, schedule):
    """按 (延时秒, 按键) 一张表敲键。Ctrl-D 必须排在慢跑（≈0.5s）之后。"""
    for delay, key in schedule:
        await asyncio.sleep(delay)
        inp.send_text(key)


def _guard(work):
    async def go():
        return await asyncio.wait_for(work(), TIMEOUT)
    return asyncio.run(go())


def run_session(keys, replies, reasoning="", tty=False, seed="帮我赚大钱",
                slow=False, kids=1, pause=0.1):
    """跑一次 converse：管道驱动的真会话 + 假 stdout。返回 (屏幕, 模型, 返回值)。"""
    screen = Screen(tty=tty)
    with create_pipe_input() as inp, _tty_env():
        session = chat._session(inp)
        llm = FakeLLM(replies, reasoning=reasoning, screen=screen, slow=slow, kids=kids)
        old_llm, chat.LLM = chat.LLM, (lambda: llm)
        old, sys.stdout = sys.stdout, screen
        env = _env(seed)
        try:
            async def go():
                r, _ = await asyncio.gather(
                    chat.converse(env, session=session),
                    _typed(inp, keys, pause))
                return r

            got = _guard(go)
        finally:
            sys.stdout = old
            chat.LLM = old_llm
    return screen, llm, got


def slow_session(replies, schedule, kids=1):
    """真终端 + 慢跑：返回屏幕上留下的内容（Live 原地画，最后那帧留下）。"""
    screen = Screen(tty=True)
    with create_pipe_input() as inp, _tty_env():
        session = chat._session(inp)
        llm = FakeLLM(replies, screen=screen, slow=True, kids=kids)
        old_llm, chat.LLM = chat.LLM, (lambda: llm)
        old, sys.stdout = sys.stdout, screen
        env = _env("帮我赚大钱")
        try:
            async def go():
                r, _ = await asyncio.gather(
                    chat.converse(env, session=session),
                    _typed_sched(inp, schedule))
                return r

            _guard(go)
        finally:
            sys.stdout = old
            chat.LLM = old_llm
    return screen


def read_session(keys):
    """读一条会话，读完为止（Ctrl-D 收手）。返回读到的每一条。"""
    with create_pipe_input() as inp:
        session = chat._session(inp)

        async def read_all():
            got = []
            try:
                while True:
                    got.append(await chat._listen(session))
            except chat._Quit:
                return got

        async def go():
            got, _ = await asyncio.gather(read_all(), _typed(inp, keys))
            return got

        return _guard(go)


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "leaf",
         "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def talk(text):
    """入口"说话"就是一段纯文本（形式那条才是 JSON）。"""
    return text


class _StopEvents(Exception):
    """脚本用完了：等价于用户在终端上中止（run 不拦，测试用它收手）。"""


class _EventLLM:
    """回话 + 每次调用都带 usage：工具与用量事件都能发出来。

    入口按脚本说话 / 交 root（交完就说话 → 触发 ask → 测试收手）；
    任务节点跑一次 bash 就 conclude。
    """

    def __init__(self, replies, usage):
        self.replies, self.usage = list(replies), usage

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        if "把用户的意图" in messages[0]["content"]:
            spec = self.replies.pop(0) if self.replies else ""
            if isinstance(spec, dict) and "root" in spec:
                return Message(text="", tool_calls=[ToolCall(
                    name="submit_root", arguments={"root": spec["root"]})],
                    usage=self.usage)
            return Message(text=str(spec or ""), usage=self.usage)  # 说话 → 入口 ask
        done = any(m.get("role") == "tool" for m in messages)
        if not done:
            return Message(text="", tool_calls=[ToolCall(
                name="bash", arguments={"command": "echo hi"})], usage=self.usage)
        return Message(text="", tool_calls=[ToolCall(
            name="conclude", arguments={"verdict": "满足", "text": "跑完了",
                                        "evidence": ["第1次观测"]})], usage=self.usage)


def run_events(seed="帮我赚大钱"):
    """直接驱动 run()：收集全部事件，入口再次提问时收手。返回 [(type, payload)]。"""
    got = []
    d = tempfile.mkdtemp()
    store_mod.init(d)
    llm = _EventLLM([root()], {"prompt_tokens": 12, "completion_tokens": 3,
                               "total_tokens": 15})

    async def ask(_):
        raise _StopEvents()

    async def go():
        await run(Store.new(Node(name="会话", kind="intake"), seed=seed),
                  llm, subscribe=lambda t, p: got.append((t, p)), ask=ask)
        return got

    try:
        return asyncio.run(go())
    except _StopEvents:
        return got


def main():
    print("=" * 80)
    print("A. 谈定：问 → 答 → 交出的任务被跑掉")
    Q = "你说的「赚大钱」按哪个数字判定？"
    S = "我建议写成：账户权益 >= 本金 x 2"
    scr, llm, r = run_session(["2026-12-31 收盘\r", "\x04"],
                              [talk(Q + "\n" + S), root()])
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.plain().splitlines()))
    line("模型的话送到了终端", Q in scr.plain() and S in scr.plain())
    line("分行的话不被压成一行（content 原样）", (Q + "\n" + S) in scr.plain())
    line("同一个问题只显示一遍", scr.plain().count(Q) == 1)
    line("答的话进了下一轮上下文", any("2026-12-31 收盘" in s for s in llm.seen))
    line("合规的任务被拿去跑、判定回终端",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())
    line("旁白说清了接到任务", "接到任务" in scr.plain())
    line("树带标记，看得出跑过", "└─" in scr.plain() and "✓" in scr.plain())
    line("用户中止才返回（入口不退场）", r is None)

    print("=" * 80)
    print("C. 读：真会话 —— 回车发送 / 翻历史 / Alt-Enter / 粘多行 / Ctrl-D")
    got = read_session(["第一句\r", "\x1b[A\r", "手写\x1b\r第二行\r",
                        "\x1b[200~粘的\n第二行\x1b[201~\r",
                        "有的终端只送 LF\n", "\x04"])
    print("  读到的：%r" % got)
    line("回车就是发送（不用按空行）", bool(got) and got[0] == "第一句")
    line("上箭头翻出上一条（历史在会话里留着）", len(got) > 1 and got[1] == "第一句")
    line("Alt-Enter 换行：一条里带两行", len(got) > 2 and got[2] == "手写\n第二行")
    line("粘贴多行当一条，不拆成几次读",
         len(got) > 3 and got[3] == "粘的\n第二行")
    line("回车送上来的是 CR 还是 LF 都算发送（发送键不许被绑走）",
         len(got) > 4 and got[4] == "有的终端只送 LF")
    line("Ctrl-D 收手（不是报错，也不是空回答）", len(got) == 5)

    print("=" * 80)
    print("B. 吐字：一小口一小口吐，而且吐完才轮到读")
    Q2 = "你说的「赚大钱」按哪个数字判定？"
    S2 = "我建议写成：账户权益 >= 本金 x 2"
    scr, llm, r = run_session(["2026-12-31 收盘\r", "\x04"],
                              [talk(Q2 + "\n" + S2), root()])
    line("不是等整段回来才上屏：Q 已经在屏幕上时，S 还没吐出来",
         any(Q2 in s and S2 not in s for s in llm.snapshots))
    line("上屏用的是流式的每一口（屏幕状态变过好几次）",
         len(set(llm.snapshots)) > 1, "%d 种" % len(set(llm.snapshots)))
    line("轮到读的时候，话已经整段在屏幕上了",
         llm.at_return and Q2 + "\n" + S2 in llm.at_return[0])

    print("=" * 80)
    print("D. 思考（reasoning_content）整段按流式吐出来，而且是灰的")
    think = "先看看用户到底想要什么，再决定要不要开一个任务"
    scr, llm, _ = run_session(["\x04"], [talk("好，我想清楚了。")],
                              reasoning=think, tty=True)
    line("思考的原文整段都显示了", think in scr.plain())
    line("思考是一小口一小口吐的（不是一次一坨）",
         sum("\x1b[2m" in p for p in scr.pieces) > 1,
         "%d 口" % sum("\x1b[2m" in p for p in scr.pieces))
    line("用的是灰色（dim）", "\x1b[2m" in scr.getvalue())
    line("回答和思考分开了（思考后换了行）", "\n好，我想清楚了。" in scr.plain())

    scr, _, _ = run_session(["\x04"], [talk("好。")], reasoning=think, tty=False)
    line("不是真终端 → 思考只留原文、不上色",
         "\x1b[2m" not in scr.getvalue() and think in scr.plain())

    print("=" * 80)
    print("E. 旁白（打回理由）显示到终端；交形式不吐")
    scr, _, _ = run_session(["\x04"], [root(accept="系统做好了"), root()])
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.plain().splitlines()))
    line("打回理由走了旁白通道", "可测物理量" in scr.plain())
    line("交形式的那一段不吐给用户（那是给闸门的）", "{" not in scr.plain())
    line("打回后照样把改好的任务跑了",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())

    print("=" * 80)
    print("F. 边界：依赖单向（terminal→core，core 不认识 terminal）")
    src = open(os.path.join(ROOT, "terminal", "chat.py"), encoding="utf-8").read()
    line("终端层不碰树的决策层（不 import plan / gate）",
         "from core.protocol.gate" not in src
         and "from core.runtime.plan" not in src)
    hand = [n for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "input"]
    line("终端层不再自己实现输入（不许再长出 input() 那一套）", not hand)
    back = []
    for dirpath, _, names in os.walk(os.path.join(ROOT, "core")):
        for n in names:
            if n.endswith(".py"):
                p = os.path.join(dirpath, n)
                s = open(p, encoding="utf-8").read()
                if re.search(r"^\s*(import|from) terminal", s, re.M):
                    back.append(os.path.relpath(p, ROOT))
    line("core 不许反过来 import terminal", not back, str(back))
    main_src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    line("终端读取只在一个地方（main.py 不再自己读输入）",
         "input(" not in main_src)
    line("main 只做初始化 + 派发（不碰话轮内部 / 不建 LLM / 不碰树）",
         "opening()" not in main_src and "converse(" not in main_src
         and "LLM(" not in main_src and "Trace(" not in main_src)
    line("开场白那条路是 await 的（装配层，不把 coroutine 当任务名送进去）",
         "await opening(session)" in src)

    print("=" * 80)
    print("G. 不是真终端（管道 / 重定向）→ 树逐帧追加")
    scr, _, _ = run_session(["\x04"], [root()])
    line("每开/关一个节点出一帧，不是只画一次", scr.plain().count("└─") >= 2,
         "%d 帧" % scr.plain().count("└─"))
    line("非真终端不抢屏（不上 Live）", "\x1b[?25l" not in scr.getvalue())

    print("=" * 80)
    print("H. 真终端：任务树用 rich Live 原地重画，跑完那帧留在屏幕上")
    scr, _, _ = run_session(["\x04"], [root()], tty=True)
    raw = scr.getvalue()
    line("真终端：Live 接管（隐藏光标）", "\x1b[?25l" in raw)
    line("真终端：跑完干净收手（光标恢复）", "\x1b[?25h" in raw)
    line("树带判定留在屏幕上",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())
    line("树不重复：真终端走 Live 原地画，不逐帧追加", scr.plain().count("└─") == 1,
         "%d 帧" % scr.plain().count("└─"))

    print("=" * 80)
    print("I. 用户没交底：入口开口之前，先让他把话说完")
    scr = Screen()
    with create_pipe_input() as inp:
        session = chat._session(inp)
        old, sys.stdout = sys.stdout, scr
        try:
            async def go():
                got, _ = await asyncio.gather(chat.opening(session=session),
                                              _typed(inp, ["我要做一个能跑通测试的东西\r"]))
                return got

            got = _guard(go)
        finally:
            sys.stdout = old
    print("  收下的开场白：%r" % got)
    line("开场白原样读到了（回车就发出去了）", got == "我要做一个能跑通测试的东西")
    line("opening 只读不抢屏幕（提示语在 converse 的横幅里，不在这里）",
         scr.plain() == "")

    print("=" * 80)
    print("J. 节点级吐字：每个节点正在说的话/想的事，画进树里它的节点下")
    scr = slow_session([root(), "好，那继续谈。"],
                       [(0.4, "2026-12-31 收盘\r"), (5.0, "\x04")])
    line("思考一小口一小口按 node_id 画进树", "▸ 思考: 先看看" in scr.plain())
    line("思考的尾巴跟着长（不是只有头一个字）", "再决定怎么" in scr.plain())
    line("content 也画进树（▸ 说:）", "▸ 说: 我要拆成三个子任务" in scr.plain())
    line("树照样跑完、判定留在屏幕上",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())

    print("=" * 80)
    print("K. 跑任务时输入不冻结：敲的字进 Live 帧，跑完按顺序交出去")
    scr = slow_session([root(), "你说的「赚大钱」按哪个数字判定？", "好。"],
                       [(0.6, "2026-12-31 收盘\r"), (1.2, "先停一下\r"),
                        (1.8, "3\r"), (5.5, "\x04")])
    line("跑的时候敲的字没有丢（进过 Live 帧的输入行）",
         "先停一下" in scr.plain())
    line("跑完后输入行的字按顺序交出去",
         scr.plain().count("（运行中你输入了") >= 2,
         "%d 条" % scr.plain().count("（运行中你输入了"))

    print("=" * 80)
    print("L. 每节点一行铺开：整棵树所有节点正在吐的字都看得见（真终端）")
    scr = slow_session([root(kind="dispatch"), "好，那继续谈。"],
                       [(0.4, "2026-12-31 收盘\r"), (5.5, "\x04")], kids=3)
    line("三个孩子都在各自的节点行上（不是只显示一个）",
         all(x in scr.plain() for x in
             ["子任务A", "子任务B", "子任务C"]))
    line("孩子都在吐字（思考画进树）",
         scr.plain().count("▸ 思考") >= 2)
    line("根出了结论，判定留在屏幕上",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())

    print("=" * 80)
    print("M. 树视图：非最后一个孩子画竖线、最后一个收尾（缩进只由 is_last 决定）")
    top = Node(name="会话", kind="intake")
    kid_a = Node(name="甲", kind="dispatch", parent=top.id, depth=1,
                 accept="A 2026-12-31", verdict="满足")
    kid_b = Node(name="乙", kind="leaf", parent=top.id, depth=1,
                 accept="B 2026-12-31")
    top.children = [kid_a.id, kid_b.id]
    reg = {n.id: n for n in (top, kid_a, kid_b)}
    rows = render_tree(top, reg)
    line("根在最前、没有前缀", rows[0].startswith("└─ "), rows[0])
    line("非最后一个孩子画 ├─，它的续行画 │",
         rows[2].startswith("   ├─ ") and rows[3].startswith("   │ "), rows[3])
    line("最后一个孩子画 └─，它的续行留空",
         rows[4].startswith("   └─ ") and rows[5].startswith("     "), rows[5])

    print("=" * 80)
    print("N. 事件词汇：工具与用量事件到达终端（tool_start/tool_end/usage）")
    evs = run_events()
    starts = [(t, p.get("name")) for t, p in evs if t == "tool_start"]
    ends = [(p.get("name"), p.get("secs")) for t, p in evs if t == "tool_end"]
    usages = [p for t, p in evs if t == "usage"]
    first_start = next((i for i, (t, p) in enumerate(evs)
                        if t == "tool_start" and p.get("name") == "bash"), None)
    first_end = next((i for i, (t, p) in enumerate(evs)
                      if t == "tool_end" and p.get("name") == "bash"), None)
    line("工具开始事件带着工具名", ("tool_start", "bash") in starts, str(starts))
    line("工具结束事件带着名字和耗时",
         any(n == "bash" and isinstance(s, float) and s >= 0 for n, s in ends),
         str(ends))
    line("同一工具先开始后结束",
         first_start is not None and first_end is not None and first_start < first_end,
         "%d < %d" % (first_start, first_end))
    line("用量事件带着 prompt/completion/total",
         bool(usages) and all(p.get("prompt", 0) > 0 and p.get("completion", 0) > 0
                              and p.get("total", 0) > 0 for p in usages),
         "%d 次" % len(usages))

    print("=" * 80)
    print("O. 折叠渲染：跑完的子树折一行带统计，活跃路径展开")
    top = Node(name="会话", kind="intake")
    a = Node(name="甲", kind="dispatch", parent=top.id, depth=1,
             accept="A 2026-12-31", verdict="满足")
    b = Node(name="乙", kind="leaf", parent=top.id, depth=1,
             accept="B 2026-12-31")
    a1 = Node(name="甲1", kind="leaf", parent=a.id, depth=2,
              accept="A1 2026-12-31", verdict="满足")
    a2 = Node(name="甲2", kind="leaf", parent=a.id, depth=2,
              accept="A2 2026-12-31", verdict="未满足")
    top.children = [a.id, b.id]
    a.children = [a1.id, a2.id]
    reg = {n.id: n for n in (top, a, b, a1, a2)}
    rows = render_folded(top, reg)
    texts = [t for _, t in rows]
    line("跑完的子树折成一行带节点数",
         any("[分配] 甲 (2 节点)" in t for t in texts), str(texts))
    line("运行中的节点展开可见", any("· [叶子] 乙" in t for t in texts), str(texts))
    line("入口根不折、孩子不画进来", any("[入口] 会话" in t for t in texts)
         and not any("甲1" in t for t in texts), str(texts))
    rows2 = render_folded(top, reg, selected=a2.id)
    texts2 = [t for _, t in rows2]
    line("选中折叠子树里的节点 → 路径展开",
         any("[叶子] 甲1" in t for t in texts2) and any("[叶子] 甲2" in t for t in texts2),
         str(texts2))
    line("展开后孩子行带竖线前缀", any("   ├─ " in t for t in texts2), str(texts2))
    rows3 = render_folded(top, reg, expanded={a.id})
    texts3 = [t for _, t in rows3]
    line("显式展开压过自动折叠", any("[叶子] 甲1" in t for t in texts3), str(texts3))

    print("=" * 80)
    print("P. 流渲染：选中节点的 msgs + 实时尾巴")
    msgs = [
        {"role": "user", "content": "把数据处理干净"},
        {"role": "assistant", "content": "我先看看。", "tool_calls": [
            {"id": "c1", "type": "function",
             "function": {"name": "bash", "arguments": '{"command": "ls"}'}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "data.csv"},
        {"role": "assistant", "content": "跑完了"},
    ]
    rows = render_stream(msgs, intake=True)
    line("user 消息带你: 前缀", any(k == "user" and t.startswith("你: ") for k, t in rows))
    line("assistant 文本进说", any(k == "say" and t == "说: 我先看看。" for k, t in rows))
    line("工具调用行单独标记", any(k == "tool" and "bash" in t for k, t in rows), str(rows))
    line("工具输出全文进历史", any(k == "toolout" and "data.csv" in t for k, t in rows))
    rows = render_stream(msgs, intake=False)
    line("非入口节点的任务消息标任务: ",
         any(k == "user" and t.startswith("任务: ") for k, t in rows))
    rows = render_stream(msgs, {"thinking": "想…", "speaking": "说…"})
    line("实时尾巴附加在底部", rows[-1] == ("speaking", "说: 说…"), str(rows[-1]))

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
