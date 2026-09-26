#!/usr/bin/env python3
"""终端会话的定向测试（零成本、确定性：脚本化模型 + 脚本化按键 + 真调度器）。

这一层只管介质与话轮，判断 / 打回 / 跑树 / 收手都在运行时层，终端只把整场会话丢给 `run`。

两套介质各测各的：
  真终端 = Textual 应用（`chat._SessionApp`）—— 用 Textual 自己的无头驱动 + Pilot 按键，
  断言**合成器真画出来的那一屏**（"人看到什么"就是它），键位走生产同一套；
  非真终端 = 逐帧打印那条路 —— 假 stdout + 假 stdin（按行读）。

  A. 谈定：问 → 答 → 交出的任务被跑掉；问题和建议只显示一遍
  B. 吐字：一小口一小口上屏、吐完才轮到读
  C. 非真终端读一行：按行读 stdin，EOF / Ctrl-C 当收手
  D. 思考整段流式吐出（尾巴区），历史里的思考行也留着
  E. 旁白显示到日志区；交形式不吐
  F. 边界守门：terminal 不碰决策层；tree/view 不 import terminal；core 不 import terminal；
     rich / prompt_toolkit 已删净（依赖与代码都不留）；日志区不手写裸 ANSI
  G. 不是真终端（管道 / 重定向）→ 树逐帧追加、种子按行读
  H. 真终端 = Textual 应用：日志区 / 树条带 / 状态条 / 工具过程 / Ctrl-C 干净收手；
     converse 按 stdout 分流（真终端 → 应用，否则 → 逐帧打印）
  I. 用户没交底：应用先进场把话收下来（第一条回车就是种子）
  J. 选中节点 → 日志区切到它的内容（↑↓ 直接切树，切即重画）
  K. 跑任务时输入不冻结：敲的行排队，按顺序交给入口
  L. 并行：跑任务的三个孩子同时挂在树上（并行地图）
  M. 折叠渲染的缩进：非最后一个孩子画竖线、最后一个收尾（is_last 决定）
  N. 事件词汇：工具与用量事件到达终端（tool_start 带参数 / tool_end 带耗时 / usage）
  O. 折叠渲染：跑完的子树折一行带统计，活跃路径展开（render_folded）
  P. 流渲染：Textual 组件 —— Markdown / Collapsible 框 / 类名；尾巴是另一块（render_tail）
  Q. 应用交互：↑↓ 切频道 / Ctrl-T 收展 / Ctrl-F 折叠 / Ctrl-P·Ctrl-N 翻历史 /
     Enter 提交 / Alt-Enter 换行 / 尾巴落地 / 事件只进选中频道 / Ctrl-Q / Ctrl-C 收手（有字也收）
  S. `-r` 的会话选择器：列表在 / ↑↓ 挪高亮 / 回车挑中 / Ctrl-C 取消
"""

import asyncio
import ast
import contextlib
import inspect
import io
import os
import re
import sys
import tempfile
import time

from harness import OK, line, ROOT
from textual.widgets import Collapsible, Markdown, OptionList, Static
import terminal.chat as chat
import terminal.picker as picker
from terminal.view import render_folded, render_stream, render_tail
from core.llm import Message, ToolCall
from core.protocol.fields import INTAKE, LEAF, Node
from core.runtime import store as store_mod
from core.runtime.loop import run
from core.runtime.store import Store

TIMEOUT = 60



def _env(seed=None):
    """一次会话一棵树：新会话（入口为根），记录根初始化到临时目录。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    return {"store": Store.new(Node(name="会话", kind="intake"), seed=seed)}


# ── 真终端那套：应用 + Pilot ──
def screen_text(app):
    """合成器真画出来的那一屏（行尾空白去掉）：断言"人看到什么"用它。"""
    return "\n".join("".join(seg.text for seg in strip).rstrip()
                     for strip in app.screen._compositor.render_strips())


def screen_rows(app):
    """整屏每行的 Segment（样式还在）：要断言"上了色"用它。"""
    return app.screen._compositor.render_strips()


def _py_files(root):
    """仓库自己的 .py（跳过 .venv / .git / 缓存）—— 守门守的是"我们的代码里没有"。"""
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".venv", ".git", "__pycache__", ".ruff_cache")]
        for n in names:
            if n.endswith(".py"):
                yield os.path.join(dirpath, n)


class Screen(io.StringIO):
    """假终端（非真终端那条路用）：整段文本与每次 write 的碎片都留着。"""

    def __init__(self, tty=False):
        super().__init__()
        self.pieces = []
        self._tty = tty

    def isatty(self):
        return self._tty

    def write(self, text):
        self.pieces.append(text)
        return super().write(text)


def tree_bg(app):
    """树条带上每行渲染出来的底色（选中那行的底色是 OptionList 自己画的）。"""
    region = app.query_one("#tree", OptionList).region
    return [str(seg.style.bgcolor)
            for strip in screen_rows(app)[region.y:region.bottom]
            for seg in strip if "[入口]" in seg.text or "[叶子]" in seg.text]


def status_text(app):
    """状态条那一行（就一个 Static，直接读它的内容，不受屏幕裁切影响）。"""
    return str(app.query_one("#status", Static).content)


def chars(text):
    """动作：一个字一个字敲进去（空格要按 `space` 这个键名）。"""
    async def act(pilot, _app):
        await pilot.press(*[("space" if c == " " else c) for c in text])
    return act


def press(*keys):
    """动作：按键名按（`down` / `enter` / `ctrl+p` / `alt+enter` …）。"""
    async def act(pilot, _app):
        await pilot.press(*keys)
    return act


def wait(sec):
    """动作：等一会儿（让跑着的会话往前走，好中途看一眼屏）。"""
    async def act(_pilot, _app):
        await asyncio.sleep(sec)
    return act


def look(sink):
    """动作：此刻屏上长什么样，收进 `sink`（流式"一小口一小口"就是这么看的）。"""
    async def act(_pilot, app):
        sink.append(screen_text(app))
    return act


def wait_for(pred, sink, *, timeout=8.0):
    """动作：屏上直到 `pred(screen)` 成立为止（每 0.1s 看一眼收进 sink）。

    等的是**状态**（"孩子挂在树上了"），不是秒数 —— 秒数赌的是机器快慢。
    """
    async def act(_pilot, app):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            shot = screen_text(app)
            sink.append(shot)
            if pred(shot):
                return True
            await asyncio.sleep(0.1)
        return False
    return act


def drive(store, llm, script, then, *, size=(100, 30), run_it=None):
    """装配 `_SessionApp`，用 Textual 无头驱动 + Pilot 驱一遍再断言。

    `script` 每步要么是 `chars/press/wait/look` 造出来的动作，要么是 (延时, 动作)；
    `then(app)` 在应用起来之后跑断言。返回 `then` 的返回值。
    `llm=None` 就是不跑树（介质测试直接喂事件，等价于旧 `drive_panel` 不进 run）。
    """
    async def go():
        app = chat._SessionApp(store, llm)
        old_run = chat.run
        if not (llm is not None if run_it is None else run_it):
            async def _nop(*_a, **_k):
                return None
            chat.run = _nop
        try:
            async with app.run_test(size=size) as pilot:
                for step in script:
                    if isinstance(step, tuple):
                        delay, action = step
                    else:
                        delay, action = 0.2, step
                    await asyncio.sleep(delay)
                    if app.is_running:
                        await pilot.pause()
                    result = action(pilot, app)
                    if inspect.isawaitable(result):
                        await result
                if app.is_running:
                    await pilot.pause()
                return then(app)
        finally:
            chat.run = old_run
    return _guard(go)


class FakeLLM:
    """按脚本回话，同时服务入口（字符串 = 说话、带 root 的 dict = submit_root）与任务节点。

    任务节点动手一次就出满足结论；`slow` 时慢吐，给"看着它吐"的断言留时间。
    """

    def __init__(self, replies, reasoning="", slow=False, kids=1):
        self.replies, self.said = list(replies), []
        self.seen = []
        self.reasoning = reasoning
        self.slow, self.kids = slow, kids
        self._spawned = False

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
        have_result = any("下层结论" in str(m.get("content", "")) for m in messages)
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
                name="conclude", arguments={"verdict": "满足", "text": "先等孩子回来"})])
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
            await self._drip(on_delta, reply)
        return Message(text=reply, tool_calls=calls, reasoning=self.reasoning)


def _guard(work):
    async def go():
        return await asyncio.wait_for(work(), TIMEOUT)
    return asyncio.run(go())


def read_lines(feed):
    """非真终端读一行：把 `feed` 摆成 stdin，读到 EOF / 收手为止。返回读到的每一条。"""
    old, sys.stdin = sys.stdin, io.StringIO(feed)
    try:
        async def read_all():
            got = []
            try:
                while True:
                    got.append(await chat._listen())
            except chat._Quit:
                return got

        return _guard(read_all)
    finally:
        sys.stdin = old


def feed_stdin(feed, screen, work):
    """把 stdin / stdout 都摆成"非真终端"，跑 `work()` 再还回去。返回 work 的结果。"""
    old_out, old_in = sys.stdout, sys.stdin
    sys.stdout, sys.stdin = screen, io.StringIO(feed)
    try:
        return _guard(work)
    finally:
        sys.stdout, sys.stdin = old_out, old_in


def _subseq(needle, hay):
    """needle 是否按序出现在 hay 里（允许中间插入其它字符：换行 / 空白 / 框线）。"""
    it = iter(hay)
    return all(c in it for c in needle)


def q_store():
    """Q 段专用树：1 入口 + 2 叶子（甲满足/乙未满足），叶子带各自的短对话。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    st = store_mod.Store.new(Node(name="会话", kind=INTAKE), seed="帮我赚大钱")
    for i, name in enumerate(["甲", "乙"]):
        nd = Node(name=name, kind=LEAF, parent=st.root.id,
                  accept="a", conc_range=[1, 2])
        nd.verdict, nd.conclusion = ("满足" if i == 0 else "未满足", "干完" + name)
        st.put([nd])
        st.root.children.append(nd.id)
        st.append_user(nd.id, "输入给" + name)
        st.append_assistant(nd.id, "给%s的回复。" % name, [])
    return st


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
    env = _env("帮我赚大钱")
    llm = FakeLLM([talk(Q + "\n" + S), root()], slow=True)
    shots = []
    got = drive(env["store"], llm,
                [look(shots), (0.15, look(shots)), (0.15, look(shots)),
                 (0.15, look(shots)), chars("2026-12-31 收盘"), press("enter"), wait(4.0)],
                screen_text)
    print("  屏上：\n%s" % "\n".join("    " + x for x in got.splitlines() if x.strip()))
    line("模型的话上屏", Q in got and S in got)
    line("不是等整段回来才上屏（Q 完整了 S 还没到）",
         any(Q in s and S not in s for s in shots), "%d 次取样" % len(shots))
    line("同一个问题只显示一遍", got.count(Q) == 1)
    line("答的话进了下一轮上下文", any("2026-12-31 收盘" in s for s in llm.seen))
    line("合规的任务被拿去跑、判定以标记回终端（✓ 在树上）",
         "✓ [叶子] 做一个能赚钱的量化系统" in got)
    line("旁白说清了接到任务", "接到任务" in got)
    line("用户的话进日志区", "你: 2026-12-31 收盘" in got, got.splitlines()[:3])
    line("树带标记，看得出跑过", "└─" in got and "✓" in got)

    print("=" * 80)
    print("B. 吐字：一小口一小口上屏、吐完才轮到读")
    Q2 = "你说的「赚大钱」按哪个数字判定？"
    S2 = "我建议写成：账户权益 >= 本金 x 2"
    env = _env("帮我赚大钱")
    llm = FakeLLM([talk(Q2 + "\n" + S2), root()], slow=True)
    shots = []
    got = drive(env["store"], llm,
                [look(shots), (0.15, look(shots)), (0.15, look(shots)),
                 (0.15, look(shots)), (0.15, look(shots)), (0.2, look(shots)),
                 chars("2026-12-31 收盘"), press("enter"), wait(4.0)],
                screen_text)
    reply = Q2 + "\n" + S2
    line("不是等整段回来才上屏（屏上有半截话的时候整段还没到）",
         any(reply[:12] in s and reply not in s for s in shots),
         "%d 次取样" % len(shots))
    line("上屏用的是流式的每一口（屏幕状态变过好几次）", len(set(shots)) > 2,
         "%d 种" % len(set(shots)))
    line("轮到读的时候，话已经整段在屏幕上了", Q2 in got and S2 in got)

    print("=" * 80)
    print("C. 非真终端读一行：按行读 stdin（回车一条），EOF / Ctrl-C 当收手")
    got = read_lines("第一句\n\n第二句没有换行收尾")
    print("  读到的：%r" % got)
    line("一行一条（空行也是一条，要不要由调用方定）",
         got == ["第一句", "", "第二句没有换行收尾"], got)
    line("换行符不进内容", read_lines("带\r回车符\n") == ["带\r回车符"])
    line("读到 EOF 是收手（不报错、也不返回空串）", read_lines("") == [])

    class _CtrlC(io.StringIO):
        def readline(self, *a):
            raise KeyboardInterrupt

    old_in, sys.stdin = sys.stdin, _CtrlC()
    try:
        async def go():
            try:
                await chat._listen()
            except chat._Quit:
                return True
            return False

        line("Ctrl-C 翻成收手（KeyboardInterrupt 不往上抛）", _guard(go))
    finally:
        sys.stdin = old_in

    print("=" * 80)
    print("D. 思考（reasoning）整段在尾巴里流式吐出，落地成灰斜体历史行")
    think = "先看看用户到底想要什么，再决定要不要开一个任务"
    env = _env("帮我赚大钱")
    llm = FakeLLM([talk("好，我想清楚了。")], reasoning=think, slow=True)
    shots = []
    got, rows = drive(env["store"], llm,
                      [look(shots), (0.3, look(shots)), wait(2.0)],
                      lambda app: (screen_text(app), screen_rows(app)))
    line("思考的原文在屏上（换行只因窗格宽度）", _subseq(think, got), repr(got[:80]))
    line("思考行是流式上屏的（中途那几眼也能看见它）",
         any("思考:" in s for s in shots))
    line("思考行上了灰斜体（样式真到了屏上）",
         any(seg.style.italic for r in rows for seg in r if "思考:" in seg.text))
    line("思考沉成历史行（不只活在实时尾巴里）", "思考: " in got)
    line("回答不加前缀（就是它说的话）", "好，我想清楚了。" in got)

    print("=" * 80)
    print("E. 旁白（打回理由）显示到终端；交形式不吐")
    env = _env("帮我赚大钱")
    llm = FakeLLM([root(accept="系统做好了"), root()])
    got = drive(env["store"], llm, [chars("开始"), press("enter"), wait(4.0)],
                screen_text)
    print("  屏上：\n%s" % "\n".join("    " + x for x in got.splitlines() if x.strip()))
    line("打回理由走了旁白通道", "可测物理量" in got)
    line("交形式只走工具那一行（说话里不重复吐）",
         got.count('{"root"') == got.count("工具: submit_root(") > 0, got[:120])
    line("打回后照样把改好的任务跑了（✓ 标记）",
         "✓ [叶子] 做一个能赚钱的量化系统" in got)

    print("=" * 80)
    print("F. 边界：依赖单向（terminal→core，core 不认识 terminal）；rich / prompt_toolkit 删净")
    chat_src = open(os.path.join(ROOT, "terminal", "chat.py"), encoding="utf-8").read()
    view_src = open(os.path.join(ROOT, "terminal", "view.py"), encoding="utf-8").read()
    line("终端层不碰树的决策层（不 import plan / gate）",
         "from core.protocol.gate" not in chat_src
         and "from core.runtime.plan" not in chat_src)
    line("终端层不再自己实现输入（不许再长出 input() 那一套）",
         not [n for n in ast.walk(ast.parse(chat_src))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "input"])
    line("视图层产 Textual 组件（不吃 rich renderable）",
         "textual" in view_src and "rich" not in view_src)
    line("日志区重画是 widget 操作（不再手写裸 ANSI 清屏 / 不再 patch_stdout）",
         "\x1b[2J" not in chat_src and "patch_stdout" not in chat_src)
    back = [os.path.relpath(p, ROOT) for p in _py_files(os.path.join(ROOT, "core"))
            if re.search(r"^\s*(import|from) terminal", open(p, encoding="utf-8").read(), re.M)]
    line("core 不许反过来 import terminal", not back, str(back))
    main_src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    line("终端读取只在一个地方（main.py 不再自己读输入）", "input(" not in main_src)
    line("main 只做初始化 + 派发（不碰话轮内部 / 不建 LLM / 不碰树）",
         "converse(" not in main_src and "LLM(" not in main_src and "Trace(" not in main_src)

    # rich / prompt_toolkit 删净：依赖表与源码都不留（textual 自带 rich 是它的内务，不算）
    pyproject = open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8").read()
    line("依赖表里没有 rich / prompt-toolkit",
         '"rich"' not in pyproject and "prompt" not in pyproject)
    hits = [os.path.relpath(p, ROOT) for p in _py_files(ROOT)
            if re.search(r"^\s*(import|from)\s+(rich|prompt_toolkit)\b",
                         open(p, encoding="utf-8").read(), re.M)]
    line("源码里没有 rich / prompt_toolkit 的 import", not hits, str(hits[:3]))

    print("=" * 80)
    print("G. 不是真终端（管道 / 重定向）→ 树逐帧追加、种子按行读")
    env = _env("帮我赚大钱")
    llm = FakeLLM([root()])
    screen = Screen(tty=False)
    old_llm, chat.LLM = chat.LLM, (lambda: llm)
    try:
        r = feed_stdin("开始\n", screen,
                       lambda: chat.converse(env["store"], banner=["[trace] x"]))
    finally:
        chat.LLM = old_llm
    plain = screen.getvalue()
    line("每开/关一个节点出一帧，不是只画一次", plain.count("└─") >= 2,
         "%d 帧" % plain.count("└─"))
    line("非真终端不抢屏（不进 Textual 应用）", "\x1b[?1049h" not in plain)
    line("装配层攒的横幅照旧打印", "[trace]" in plain)
    line("用户中止才返回（入口不退场）", r is None)

    seeds = []
    screen = Screen(tty=False)
    old_seed, chat.intake_seed = chat.intake_seed, lambda t: seeds.append(t) or "种子"
    old_llm, chat.LLM = chat.LLM, (lambda: FakeLLM([root()]))
    try:
        r = feed_stdin("我要做一个能跑通测试的东西\n", screen,
                       lambda: chat.converse(None, banner=[]))
    finally:
        chat.intake_seed = old_seed
        chat.LLM = old_llm
    line("新会话的种子按行读（读到的第一条就是它）",
         seeds == ["我要做一个能跑通测试的东西"] and r is None, str(seeds))

    screen = Screen(tty=False)
    old_llm, chat.LLM = chat.LLM, (lambda: FakeLLM([]))
    try:
        r = feed_stdin("", screen, lambda: chat.converse(None, banner=[]))
    finally:
        chat.LLM = old_llm
    line("种子那一步就读到 EOF 也是收手（不抛不炸）", r is None,
         screen.getvalue()[-40:])

    print("=" * 80)
    print("H. 真终端 = Textual 应用：五区在、工具过程在、Ctrl-C 干净收手；converse 分流")
    env = _env("帮我赚大钱")
    llm = FakeLLM([root()])
    shots = []
    got = drive(env["store"], llm,
                [chars("开始"), press("enter"), (2.5, look(shots)), press("down")],
                screen_text)
    intake_screen = next((s for s in shots if s), "")
    line("入口的对话在日志区", "你: 开始" in intake_screen)
    line("树条带带着任务行", "[叶子] 做一个能赚钱的量化系统" in intake_screen)
    line("入口的工具过程写进了它的日志区", "工具结束: submit_root" in intake_screen)
    line("切到任务节点：它的工具过程与结论在它的频道里",
         "工具: bash(" in got and "工具: conclude(" in got and "→ 跑完了" in got,
         got[-160:])
    line("状态条在（选中/运行中/节点）",
         "选中" in got and "运行中" in got and "节点" in got)
    line("输入行常驻（空着也看得见提示）",
         "回车发送" in got, got.splitlines()[-1:])

    calls = []

    async def fake_native(store, llm, *, banner=()):
        calls.append(("native", [str(b) for b in banner]))
        return None

    async def fake_plain(store, llm, *, banner=()):
        calls.append(("plain", [str(b) for b in banner]))
        return None

    old_n, old_p, old_llm = chat._run_native, chat._run_plain, chat.LLM
    chat._run_native, chat._run_plain = fake_native, fake_plain
    chat.LLM = lambda: llm
    old = sys.stdout
    try:
        for tty in (True, False):
            sys.stdout = Screen(tty=tty)
            _guard(lambda: chat.converse(_env("帮我赚大钱")["store"],
                                         banner=["[trace] x"]))
    finally:
        sys.stdout = old
        chat._run_native, chat._run_plain, chat.LLM = old_n, old_p, old_llm
    line("真终端 → 应用（横幅交给它画）",
         calls[0][0] == "native" and calls[0][1] == ["[trace] x"], str(calls[:1]))
    line("非真终端 → 逐帧打印", calls[1][0] == "plain", str(calls[1:]))

    print("=" * 80)
    print("I. 用户没交底：应用先进场把话收下来（第一条回车就是种子）")
    llm = FakeLLM([root()])
    shots = []
    got, seeded = drive(None, llm,
                        [look(shots), chars("做一个能跑通测试的东西"), press("enter"),
                         wait(1.0)],
                        lambda app: (screen_text(app), app.store))
    print("  种子进 store 与否：%s" % (seeded is not None))
    line("进场先摆出要干什么（还没谈定就不起树）",
         "说说你要做什么" in shots[0] and "你: " not in shots[0], shots[0][-60:])
    line("第一条回车成了种子（写进 store 的第一条用户消息）",
         seeded is not None
         and "做一个能跑通测试的东西" in seeded.dialogue(seeded.root.id).to_list()[0]["content"])
    line("种子在日志区看得见（在应用里收，不另开提示框）",
         "做一个能跑通测试的东西" in got)
    line("收下之后提示换成常态输入", "说说你要做什么" not in got)

    print("=" * 80)
    print("J. 选中节点 → 日志区切到它的内容（↑↓ 直接切树，切即重画）")
    st = q_store()
    text, selected, hl = drive(
        st, None, [press("down"), press("down"), press("up")],
        lambda app: (screen_text(app), app.selected, tree_bg(app)))
    line("↑ 切回上一个节点", selected == st.root.children[0])
    line("日志区是甲的对话", "给甲的回复。" in text, text.splitlines()[:3])
    line("树的选中行跟着高亮（选中底色落在选中那一行）",
         len(hl) == 3 and hl[1] != hl[0] and hl[2] == hl[0], hl)
    line("日志区只画当前频道（乙的话不在）", "给乙的回复。" not in text)

    got = drive(st, None, [press("down"), press("down")], screen_text)
    line("↓ 到乙：日志区换成乙的对话", "给乙的回复。" in got and "给甲的回复。" not in got)

    print("=" * 80)
    print("K. 跑任务时输入不冻结：敲的行排队，按顺序交给入口")
    env = _env("帮我赚大钱")
    llm = FakeLLM([root(), "你说的「赚大钱」按哪个数字判定？", "好。"], slow=True, kids=1)
    shots = []
    got = drive(env["store"], llm,
                [chars("2026-12-31 收盘"), press("enter"), wait(0.4),
                 chars("先停一下"), look(shots), press("enter"), wait(0.4),
                 chars("3"), press("enter"), wait(5.0)],
                screen_text)
    line("跑的时候敲的字没有丢（输入行草稿上过屏）",
         any("先停一下" in s for s in shots))
    line("敲的行按顺序交出去（你: 出现在日志区）",
         got.find("你: 2026-12-31 收盘") < got.find("你: 3")
         and "你: 2026-12-31 收盘" in got,
         "%d < %d" % (got.find("你: 2026-12-31 收盘"), got.find("你: 3")))

    print("=" * 80)
    print("L. 并行：跑任务的三个孩子同时挂在树上（并行地图）")
    env = _env("帮我赚大钱")
    llm = FakeLLM([root(kind="dispatch"), "好，那继续谈。"], slow=True, kids=3)
    names = ["子任务A", "子任务B", "子任务C"]
    shots = []
    got = drive(env["store"], llm,
                [chars("2026-12-31 收盘"), press("enter"),
                 wait_for(lambda s: all(x in s for x in names), shots)],
                screen_text)
    first = next((s for s in shots if all(x in s for x in names)), "")
    line("三个孩子都在各自的节点行上（不是只显示一个）", bool(first))
    no_ws = re.sub(r"[^\S\n]+", "", first)
    line("孩子都在跑（· 标记，运行中不折叠）",
         all(("·[叶子]" + x) in no_ws for x in names), first.replace("\n", " / "))
    line("分配根在条带上", "[分配] 做一个能赚钱的量化系统" in got)

    print("=" * 80)
    print("M. 折叠渲染的缩进：非最后一个孩子画 ├─、最后一个收尾（is_last 决定）")
    top = Node(name="会话", kind="intake")
    kid_a = Node(name="甲", kind="dispatch", parent=top.id, depth=1,
                 accept="A 2026-12-31", verdict="满足")
    kid_b = Node(name="乙", kind="leaf", parent=top.id, depth=1,
                 accept="B 2026-12-31")
    top.children = [kid_a.id, kid_b.id]
    reg = {n.id: n for n in (top, kid_a, kid_b)}
    texts = [t for _, t in render_folded(top, reg)]
    line("根在最前、没有前缀", texts[0].startswith("└─ "), texts[0])
    line("非最后一个孩子画 ├─", texts[1].startswith("   ├─ "), texts[1])
    line("最后一个孩子画 └─", texts[2].startswith("   └─ "), texts[2])

    print("=" * 80)
    print("N. 事件词汇：工具与用量事件到达终端（tool_start / tool_end / usage）")
    evs = run_events()
    starts = [(t, p.get("name")) for t, p in evs if t == "tool_start"]
    ends = [(p.get("name"), p.get("secs")) for t, p in evs if t == "tool_end"]
    usages = [p for t, p in evs if t == "usage"]
    args = [p.get("arguments") for t, p in evs
            if t == "tool_start" and p.get("name") == "bash"]
    first_start = next((i for i, (t, p) in enumerate(evs)
                        if t == "tool_start" and p.get("name") == "bash"), None)
    first_end = next((i for i, (t, p) in enumerate(evs)
                      if t == "tool_end" and p.get("name") == "bash"), None)
    line("工具开始事件带着工具名", ("tool_start", "bash") in starts, str(starts))
    line("工具开始事件带着参数（终端要画 `工具: 名(参数)`）",
         bool(args) and args[0] == {"command": "echo hi"}, str(args))
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
    print("P. 流渲染：Textual 组件（Markdown / Collapsible 框 / 类名）；尾巴是另一块")
    msgs = [
        {"role": "user", "content": "把数据处理干净"},
        {"role": "assistant", "content": "**先**看看。", "tool_calls": [
            {"id": "c1", "type": "function",
             "function": {"name": "bash", "arguments": '{"command": "ls"}'}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "data.csv"},
        {"role": "assistant", "content": "跑完了"},
    ]
    rows = render_stream(msgs, intake=True)
    line("user 消息 = 加粗纯文本行（类名 msg-user）",
         isinstance(rows[0], Static) and rows[0].content == "你: 把数据处理干净"
         and "msg-user" in rows[0].classes, str(rows[0]))
    line("assistant 内容 = Markdown 组件（排版交给它）",
         any(isinstance(r, Markdown) for r in rows))
    line("工具调用 = 青色一行（类名 msg-tool）",
         any(isinstance(r, Static) and str(r.content).startswith("工具: bash")
             and "msg-tool" in r.classes for r in rows))
    line("工具输出 = Collapsible 框（title=工具名）",
         any(isinstance(r, Collapsible) and r.title.plain == "bash" for r in rows))
    rows = render_stream([{"role": "assistant", "content": "好", "reasoning": "想想"}])
    line("已提交的思考画成历史行（随消息，不只在尾巴里）",
         any(isinstance(r, Static) and r.content == "思考: 想想" for r in rows))
    rows = render_stream(msgs, intake=True, verdict="满足", accept="产出 clean.csv",
                         conclusion="全部完成")
    line("判定行 = 绿字（类名 verdict-ok）",
         any(isinstance(r, Static) and r.content == "[满足] 产出 clean.csv"
             and "verdict-ok" in r.classes for r in rows))
    think_tail = render_tail("think", "想…")
    line("思考尾巴 = 灰斜体（类名 tail-think，带 `思考: ` 前缀）",
         isinstance(think_tail, Static) and think_tail.content == "思考: 想…"
         and "tail-think" in think_tail.classes)
    line("说话尾巴 = 纯文本", render_tail("say", "说…").content == "说…")

    # 组件真上屏：Markdown 被解析、工具的框带着工具名
    st = store_mod.Store.new(Node(name="会话", kind=INTAKE), seed="帮我赚大钱")
    cid = st.append_assistant(st.root.id, "**加粗的结论**",
                              [ToolCall(name="bash", arguments={"command": "ls"})])[0]
    st.append_tool(st.root.id, cid, "data.csv")
    text = drive(st, None, [], screen_text)
    line("Markdown 真被解析（`**` 没原样上屏）",
         "加粗的结论" in text and "**" not in text, text.splitlines()[:4])
    line("工具输出的框带着工具名", "bash" in text and "data.csv" in text)

    print("=" * 80)
    print("Q. 应用交互：↑↓ 切频道 / Ctrl-T / Ctrl-F / Ctrl-P·N / 尾巴落地 / 事件不串台")
    st = q_store()
    got = drive(st, None, [press("down"), press("down")],
                lambda app: (app.selected, screen_text(app), status_text(app)))
    selected, screen, status = got
    line("↑↓ 在输入行上直接切树节点", selected == st.root.children[1])
    line("切即重画：日志区清成选中节点的对话",
         "给乙的回复。" in screen and "给甲的回复。" not in screen, screen[:60])
    line("树条带没被清掉（甲、乙都还在）", "甲" in screen and "乙" in screen)
    line("状态条跟着选中走", "选中 乙" in status, status)
    line("状态条常显收手键（输入行有字时也看得见退路）", "Ctrl-Q/C 收手" in status, status)

    got = drive(st, None, [press("ctrl+t")], lambda app: (app.tree_on,
                                                          app.query_one("#tree").display))
    line("Ctrl-T 收起树条带", got == (False, False), got)
    got = drive(st, None, [press("ctrl+t"), press("ctrl+t")],
                lambda app: (app.tree_on, app.query_one("#tree").size.height))
    line("再按 Ctrl-T 展开（条带还是 6 行）", got == (True, 6), got)

    got = drive(st, None, [chars("2026-12-31 收盘"), press("enter"), press("ctrl+p")],
                lambda app: (app.lines.qsize(), app.query_one("#input").text,
                             app.query_one("#input").cursor_location))
    line("回车提交进队列", got[0] == 1, got)
    line("Ctrl-P 翻回提交过的行（↑↓ 让位给树）", got[1] == "2026-12-31 收盘", got)
    line("翻出来的光标在末尾（接着能打字）", got[2] == (0, len("2026-12-31 收盘")), got[2])
    got = drive(st, None, [chars("a"), press("enter"), press("enter")],
                lambda app: (app.lines.qsize(), app.query_one("#input").text))
    line("空行不入队、清空输入行", got == (1, ""), got)
    got = drive(st, None, [chars("手写"), press("alt+enter"), chars("第二行")],
                lambda app: (app.query_one("#input").text,
                             app.query_one("#input").size.height, app.lines.qsize()))
    line("Alt-Enter 换行（一条里带两行，不提交）",
         got[0] == "手写\n第二行" and got[2] == 0, got)
    line("换行后输入行长高", got[1] > 1, got[1])

    def feed(_pilot, app):
        st2 = app.store
        jia = st2.root.children[0]
        app.on_sink("message_update", {"scope": jia, "kind": "reasoning",
                                       "delta": "想清楚再动手"})
        app.on_sink("message_update", {"scope": jia, "kind": "content",
                                       "delta": "先看看 schema"})
        return jia

    got = drive(st, None, [press("down"), feed],
                lambda app: (screen_text(app), app.query_one("#tail").display))
    screen, shown = got
    line("思考行进尾巴（未提交）", "思考: 想清楚再动手" in screen, screen[-60:])
    line("说话进尾巴、不上日志区", "先看看 schema" in screen)
    line("尾巴有内容才占位", shown is True)

    def tool(_pilot, app):
        app.on_sink("tool_start", {"scope": app.store.root.children[0], "name": "bash",
                                   "arguments": {"command": "ls"}})

    got = drive(st, None, [press("down"), feed, tool],
                lambda app: (screen_text(app), app.query_one("#tail").display))
    screen, shown = got
    line("tool_start 把尾巴落地进日志区",
         "思考: 想清楚再动手" in screen and "先看看 schema" in screen, screen[-120:])
    line("工具开始带参数进日志区", '工具: bash({"command": "ls"})' in screen, screen[-60:])
    line("落地后尾巴清空", shown is False)

    def tool_end(_pilot, app):
        app.on_sink("tool_end", {"scope": app.store.root.children[0], "name": "bash",
                                 "secs": 0.3})

    got = drive(st, None, [press("down"), tool_end], screen_text)
    line("工具结束带耗时", "工具结束: bash (0.3s)" in got, got[-60:])

    def usage(_pilot, app):
        app.on_sink("usage", {"scope": app.store.root.children[0], "total": 15})

    got = drive(st, None, [press("down"), usage], status_text)
    line("用量进状态条", "15 tokens" in got, got)

    def other_channel(_pilot, app):
        # 别人在说话 + 别人的高频事件，都不该串进当前频道的日志区
        app.on_sink("message_update", {"scope": app.store.root.children[1], "kind": "content",
                                      "delta": "乙在说"})
        app.on_sink("usage", {"scope": app.store.root.children[1], "total": 7})

    got = drive(st, None, [press("down"), other_channel], screen_text)
    line("别的频道的事件不写进当前日志区", "乙在说" not in got, got[-60:])

    def long_tail(_pilot, app):
        for i in range(1, 13):          # 12 行思考，超过尾巴区上限（8 行）
            app.on_sink("message_update", {"scope": app.store.root.id, "kind": "reasoning",
                                           "delta": "第%d行。\n" % i})

    got = drive(st, None, [long_tail, wait(0.4), wait(0.3)],
                lambda app: (screen_text(app), app.query_one("#log").size.height))
    line("长尾巴滚到最新那几行（不卡在头 8 行）", "第12行" in got[0], got[0][-140:])
    line("尾巴不外溢（日志区还有地方）", got[1] >= 8, "日志区 %d 行" % got[1])
    got = drive(st, None, [press("down"), other_channel, press("down")], screen_text)
    line("切过去才看到它的实时尾巴", "乙在说" in got, got[-80:])

    def conclude(_pilot, app):
        nd = app.store.registry[app.store.root.children[1]]   # 乙 未满足 → 满足
        nd.verdict = "满足"
        app.on_sink("loop_end", {"scope": nd.id})

    got = drive(st, None, [press("down"), press("down"), conclude], screen_text)
    line("loop_end 后条带按新判定重画（✗ → ✓）",
         "✓ [叶子] 乙" in got and "✗ [叶子] 乙" not in got, got.replace("\n", " | "))

    got = drive(st, None, [press("down"), press("ctrl+f")],
                lambda app: set(app.expanded))
    line("Ctrl-F 只对已出结论的节点显式展开", got == {st.root.children[0]}, got)

    got = drive(st, None, [chars("草稿"), press("ctrl+c")], lambda app: app.is_running)
    line("Ctrl-C 有字也收手（退路不看输入行里有什么）", got is False, got)
    got = drive(st, None, [press("ctrl+c")],
                lambda app: app.error)
    line("Ctrl-C 空输入行干净收手（应用收场、run 停）", got is None)
    got = drive(st, None, [press("ctrl+d")],
                lambda app: (app.is_running, app.query_one("#input").text))
    line("Ctrl-D 不再收手（那把让给终端，空行按它什么事都不发生）",
         got == (True, ""), got)
    got = drive(st, None, [chars("草稿"), press("left"), press("ctrl+d")],
                lambda app: (app.is_running, app.query_one("#input").text))
    line("Ctrl-D 有字时是退一格（输入行自己的删字符），不关应用",
         got == (True, "草"), got)
    got = drive(st, None, [chars("草稿"), press("ctrl+q")], lambda app: app.is_running)
    line("Ctrl-Q 有字也收手（退路不看输入行里有什么）", got is False, got)

    print("=" * 80)
    print("R. 应用收场：run 炸了带着原异常退场，不吞")
    env = _env("帮我赚大钱")

    class Boom:
        async def chat(self, *a, **k):
            raise RuntimeError("模型挂了")

    async def go():
        app = chat._SessionApp(env["store"], Boom())
        with contextlib.suppress(Exception):
            await app.run_async(headless=True, size=(80, 24))
        return app

    app = _guard(go)
    line("异常记在 app.error 上（不吞）", isinstance(app.error, RuntimeError), app.error)

    print("=" * 80)
    print("S. 会话选择器（-r 的列表）：列表在、↑↓ 挪高亮、回车挑中、Ctrl-C 取消")
    items = [("s1", "第一场 8 节点 2 分钟"), ("s2", "第二场 3 节点 40 秒")]

    async def pick(keys):
        """驱一遍选择器，返回（返回值, 第一帧, 每按一次键之后的高亮下标）。"""
        app = picker._PickerApp(items, "选择要加载的会话")
        async with app.run_test(size=(80, 10)) as pilot:
            await pilot.pause()
            first = screen_text(app)
            hl = [app.query_one("#picker", OptionList).highlighted]
            for k in keys:
                if not app.is_running:
                    break
                await pilot.press(k)
                await pilot.pause()
                if app.is_running:
                    hl.append(app.query_one("#picker", OptionList).highlighted)
            return app.return_value, first, hl

    value, first, hl = _guard(lambda: pick([]))
    line("列表在（标题 / 两场会话 / 键位提示）",
         all(x in first for x in ("选择要加载的会话", "第一场", "第二场", "回车加载")),
         first.splitlines()[:2])
    line("一开始高亮在第一项", hl == [0], hl)

    value, _, hl = _guard(lambda: pick(["down"]))
    line("↓ 挪高亮", hl == [0, 1], hl)

    value, _, _ = _guard(lambda: pick(["down", "enter"]))
    line("回车挑中的是选中那一行（返回它的下标）", value == 1, value)
    value, _, _ = _guard(lambda: pick(["enter"]))
    line("不改选中就是第一项", value == 0, value)
    value, _, _ = _guard(lambda: pick(["ctrl+c"]))
    line("Ctrl-C 取消（返回 None，不是第一项）", value is None, value)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
