#!/usr/bin/env python3
"""终端会话的定向测试。零成本、确定性（脚本化模型 + 脚本化终端 + 脚本化的树）。

这一层只管"介质与话轮"：把用户敲的字交回去、把入口说的话显示出来、
思考画成灰的、Ctrl-D/Ctrl-C 干净收手。判断 / 打回 / 跑树 / 收手都是
`tree/intake.py` 的事（这里把 `tree.intake.run` 换成脚本）。

入口不退场：谈成一个根就跑一次、结论回填，再接着谈。所以 `converse`
到最后总是**由用户中止**才返回 `None`。

**读不替身**：测试往**真的** prompt_toolkit 会话里塞一条管道
（`create_pipe_input`），键位与历史走的是生产用的同一套 —— 于是
"回车发送 / 翻历史 / 粘贴多行 / Alt-Enter / Ctrl-D"全都能断言，
而不用自己写一个假的 read。**显示**把 stdout 换成假终端，rich 的判断
（上不上色、走不走 Live）照旧生效。

  A. 谈定：问 → 答 → 交出的根被跑掉；问题和建议只显示一遍
  B. 读：回车发送（CR / LF 都算）、上下键翻历史、Alt-Enter 换行、粘贴多行当一条、
     Ctrl-D 收手
  C. 吐字：一小口一小口吐（不等整段回来）、吐完才轮到读
  D. 思考（reasoning_content）整段按流式吐出来，而且是灰的（真终端才上色）
  E. 旁白（打回理由、接到任务/跑完了）显示到终端；交形式不吐
  F. 边界守门：terminal 不碰树的决策层；tree 不 import terminal；
     main.py 不再自己读输入；terminal 不再自己实现输入
  G. 不是真终端（管道 / 重定向）→ 树逐帧追加
  H. 真终端：任务树用 rich Live 原地重画，跑完那帧留在屏幕上
  I. 用户没交底：入口开口之前，先让他把话说完（不是先调模型）
  J. 节点级吐字：每个节点正在想/正在说的话，画进树里它的节点下（真终端）
  K. 跑任务时输入不冻结：敲的字进 Live 帧，跑完按顺序交出去
  L. 每节点一行铺开：整棵树所有节点正在吐的字都看得见（真终端）
"""

import asyncio
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import tree.intake as intake_mod                           # noqa: E402
import terminal.chat as chat                               # noqa: E402
from prompt_toolkit.input import create_pipe_input         # noqa: E402
from tree.llm import Message, ToolCall                     # noqa: E402
from tree.protocol.fields import Node                      # noqa: E402

OK = []
RAN = []
ENV = {"trace": None}
ANSI = re.compile(r"\033\[[0-9;?]*[a-zA-Z]")
TIMEOUT = 20               # 读法出问题时要**报错**，不能把整批测试挂住


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class Screen(io.StringIO):
    """假终端：整段文本留在自己身上，每次 write 的碎片也留着。

    `pieces` 是"吐字是不是一小口一小口""思考上没上灰"的证据 ——
    一次吐字一次 write。
    """

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


class FakeLLM:
    """按脚本回话的入口模型，并记下每一轮它看见了什么、屏幕上当时有什么。"""

    def __init__(self, replies, reasoning="", screen=None):
        self.replies, self.last_usage, self.seen = list(replies), {}, []
        self.reasoning, self.screen = reasoning, screen
        self.at_return, self.snapshots = [], []

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.seen.append(messages[-1]["content"])
        if self.reasoning and on_reasoning:
            for i in range(0, len(self.reasoning), 4):   # 思考也一小口一小口
                on_reasoning(self.reasoning[i:i + 4])
        spec = self.replies.pop(0) if self.replies else ""
        if isinstance(spec, dict) and "root" in spec:
            reply, calls = "", [ToolCall(name="submit_root",
                                         arguments={"root": spec["root"]})]
        else:
            reply, calls = str(spec or ""), []
        if on_delta:
            for i in range(0, len(reply), 5):    # 一小口一小口地吐
                on_delta(reply[i:i + 5])
                if self.screen is not None:      # 每吐一口，屏幕当时长什么样
                    self.snapshots.append(self.screen.plain())
        if self.screen is not None:
            self.at_return.append(self.screen.plain())
        return Message(text=reply, tool_calls=calls)


async def fake_run(root, llm, trace, registry=None, budget=None, workers=6,
                on_event=None, **kwargs):
    """脚本化的树：记下跑了哪棵根，给一个可复核的结论。

    真调度器每开/关一个节点发一次 on_event，这里也照发（出生+出结论），
    终端才会真的把树一帧一帧画出来。
    """
    RAN.append(root)
    if on_event:
        on_event(root)
    root.close("满足", "跑完了：%s" % root.name, ["证据"])
    if on_event:
        on_event(root)
    return root


intake_mod.run = fake_run


async def slow_stream_run(root, llm, trace, registry=None, budget=None, workers=6,
                          on_event=None, on_delta=None,
                          on_reasoning=None, **kwargs):
    """慢跑的树替身：按 node_id 吐字、给够时间让跑阶段的输入会话活一阵。

    真调度器把终端的节点级 on_delta/on_reasoning 接到 llm.chat（turn.ask），
    这里直接照发，证明终端把这一路画进了树的节点下。总时长约 0.5s。
    """
    if registry is not None:
        registry[root.id] = root
    if on_event:
        on_event(root)
    think = "先看看用户到底要什么，再决定怎么拆。"
    for i in range(0, len(think), 4):
        if on_reasoning:
            on_reasoning(root.id, think[i:i + 4])
        await asyncio.sleep(0.08)
    if on_delta:
        on_delta(root.id, "我要拆成三个子任务。")
    await asyncio.sleep(0.15)
    root.close("满足", "跑完了：%s" % root.name, ["证据"])
    if on_event:
        on_event(root)
    return root


async def multi_stream_run(root, llm, trace, registry=None, budget=None, workers=6,
                            on_event=None, on_delta=None,
                            on_reasoning=None, **kwargs):
    """慢跑的多节点树替身：根 + 三个孩子并发吐字（各自不同的内容）。

    证明实时视图是**每节点一行铺开** —— 三个孩子同时在想，三路思考都在
    各自的节点行上看得见（不是只显示一个节点的）。总时长约 0.5s。
    """
    if registry is not None:
        registry[root.id] = root
    if on_event:
        on_event(root)
    for i in range(0, 16, 4):
        if on_reasoning:
            on_reasoning(root.id, "根在想怎么拆这一句"[i:i + 4])
        await asyncio.sleep(0.05)
    kids = []
    for name, accept in [("子任务A", "A在2026-12-31 >= 1"),
                         ("子任务B", "B在2026-12-31 >= 1"),
                         ("子任务C", "C在2026-12-31 >= 1")]:
        n = Node(name=name, detail="d", notes="", accept=accept, kind="leaf",
                 gate=False, conc_range=[], parent=root.id, depth=1)
        root.children.append(n.id)
        if registry is not None:
            registry[n.id] = n
        kids.append(n)
        if on_event:
            on_event(n)
    thinks = {"子任务A": "孩子A在琢磨验收标准怎么定",
              "子任务B": "孩子B在琢磨验收标准怎么定",
              "子任务C": "孩子C准备写第一段代码"}

    async def stream(kid, txt):
        for i in range(0, len(txt), 4):
            if on_reasoning:
                on_reasoning(kid.id, txt[i:i + 4])
            await asyncio.sleep(0.05)

    await asyncio.gather(*(stream(k, thinks[k.name]) for k in kids))
    for k in kids:
        k.close("满足", "做完了：%s" % k.name, ["证据"])
        if on_event:
            on_event(k)
    root.close("满足", "全部完成", ["证据"])
    if on_event:
        on_event(root)
    return root


async def _typed_sched(inp, schedule):
    """按 (延时秒, 按键) 一张表敲键。Ctrl-D 必须排在慢跑（≈0.5s）之后：
    跑阶段还开着时按 Ctrl-D = 运行中中止（那是设计行为，不是本节的断言）。"""
    for delay, key in schedule:
        await asyncio.sleep(delay)
        inp.send_text(key)


def slow_session(replies, schedule):
    """真终端 + 慢跑：返回屏幕上留下的内容（Live 原地画，最后那帧留下）。"""
    screen = Screen(tty=True)
    old_run, old_out = intake_mod.run, sys.stdout
    intake_mod.run, sys.stdout = slow_stream_run, screen
    try:
        with create_pipe_input() as inp:
            session = chat._session(inp)
            llm = FakeLLM(replies)

            async def go():
                r, _ = await asyncio.gather(
                    chat.converse(llm, "帮我赚大钱", ENV, session=session),
                    _typed_sched(inp, schedule))
                return r

            _guard(go)
    finally:
        sys.stdout = old_out
        intake_mod.run = old_run
    return screen


def multi_session(replies, schedule):
    """真终端 + 多节点慢跑：返回屏幕上留下的内容（Live 原地画，最后那帧留下）。"""
    screen = Screen(tty=True)
    env = {"trace": None, "registry": {}}
    old_run, old_out = intake_mod.run, sys.stdout
    intake_mod.run, sys.stdout = multi_stream_run, screen
    try:
        with create_pipe_input() as inp:
            session = chat._session(inp)
            llm = FakeLLM(replies)

            async def go():
                r, _ = await asyncio.gather(
                    chat.converse(llm, "帮我赚大钱", env, session=session),
                    _typed_sched(inp, schedule))
                return r

            _guard(go)
    finally:
        sys.stdout = old_out
        intake_mod.run = old_run
    return screen


async def _typed(inp, keys, pause=0.1):
    """一条一条敲进去。

    一次全灌进去会丢掉方向键（实测：上箭头拿不回历史）—— 人是一下一下敲的，
    这里也一下一下来。
    """
    for k in keys:
        await asyncio.sleep(pause)
        inp.send_text(k)


def _guard(work):
    async def go():
        return await asyncio.wait_for(work(), TIMEOUT)
    return asyncio.run(go())


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


def run_session(keys, replies, reasoning="", tty=False, seed="帮我赚大钱"):
    """跑一次 converse：管道驱动的真会话 + 假 stdout。返回 (屏幕, 模型, 返回值)。"""
    screen, RAN[:] = Screen(tty=tty), []
    with create_pipe_input() as inp:
        session = chat._session(inp)
        llm = FakeLLM(replies, reasoning=reasoning, screen=screen)
        old, sys.stdout = sys.stdout, screen
        try:
            async def go():
                r, _ = await asyncio.gather(
                    chat.converse(llm, seed, ENV, session=session),
                    _typed(inp, keys))
                return r

            got = _guard(go)
        finally:
            sys.stdout = old
    return screen, llm, got


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def talk(text):
    """入口"说话"就是一段纯文本（形式那条才是 JSON）。"""
    return text


def main():
    print("=" * 80)
    print("A. 谈定：问 → 答 → 交出的根被跑掉")
    Q = "你说的「赚大钱」按哪个数字判定？"
    S = "我建议写成：账户权益 >= 本金 x 2"
    scr, llm, r = run_session(["2026-12-31 收盘\r", "\x04"],
                              [talk(Q + "\n" + S), root()])
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.plain().splitlines()))
    line("模型的话送到了终端", Q in scr.plain() and S in scr.plain())
    line("分行的话不被压成一行（content 原样）", (Q + "\n" + S) in scr.plain())
    line("同一个问题只显示一遍", scr.plain().count(Q) == 1)
    line("答的话进了下一轮上下文", any("2026-12-31 收盘" in s for s in llm.seen))
    line("合规的根被拿去跑了", len(RAN) == 1
         and RAN[0].accept == "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("旁白说清了接到任务、跑完了",
         "接到任务" in scr.plain() and "跑完了" in scr.plain())
    line("跑完的任务树画在终端上（判定/验收标准都在）",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())
    line("树带分支与状态标记，看得出拆分过程",
         "└─" in scr.plain() and "✓" in scr.plain())
    line("用户中止才返回（入口不退场）", r is None)

    print("=" * 80)
    print("B. 吐字：一小口一小口吐，而且吐完才轮到读")
    line("不是等整段回来才上屏：Q 已经在屏幕上时，S 还没吐出来",
         any(Q in s and S not in s for s in llm.snapshots))
    line("上屏用的是流式的每一口（屏幕状态变过好几次）",
         len(set(llm.snapshots)) > 1, "%d 种" % len(set(llm.snapshots)))
    line("轮到读的时候，话已经整段在屏幕上了", Q + "\n" + S in llm.at_return[0])

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
    line("打回后照样把改好的根跑了", len(RAN) == 1)

    print("=" * 80)
    print("F. 边界：依赖单向（terminal→tree.intake，tree 不认识 terminal）")
    src = open(os.path.join(ROOT, "terminal", "chat.py"), encoding="utf-8").read()
    line("终端层不碰树的决策层（tree.run / tree.node）",
         "tree.run" not in src and "tree.node" not in src)
    hand = [n for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "input"]
    line("终端层不再自己实现输入（不许再长出 input() 那一套）", not hand)
    back = []
    for dirpath, _, names in os.walk(os.path.join(ROOT, "tree")):
        for n in names:
            if n.endswith(".py"):
                p = os.path.join(dirpath, n)
                if "terminal" in open(p, encoding="utf-8").read():
                    back.append(os.path.relpath(p, ROOT))
    line("tree 不许反过来 import terminal", not back, str(back))
    main_src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
    line("终端读取只在一个地方（main.py 不再自己读输入）",
         "input(" not in main_src)
    line("开场白那条路是 await 的（不把 coroutine 当任务名送进去）",
         "await opening()" in main_src)

    print("=" * 80)
    print("G. 不是真终端（管道 / 重定向）→ 树逐帧追加")
    scr, _, _ = run_session(["\x04"], [root()])
    print("  帧数: %d" % scr.plain().count("└─"))
    line("每开/关一个节点出一帧，不是只画一次", scr.plain().count("└─") >= 2,
         "%d 帧" % scr.plain().count("└─"))
    line("非真终端不抢屏（不上 Live）", "\x1b[?25l" not in scr.getvalue())

    print("=" * 80)
    print("H. 真终端：任务树用 rich Live 原地重画，跑完那帧留在屏幕上")
    scr, _, _ = run_session(["\x04"], [root()], tty=True)
    raw = scr.getvalue()
    print("  帧数: %d" % scr.plain().count("└─"))
    line("真终端：Live 接管（隐藏光标）", "\x1b[?25l" in raw)
    line("真终端：跑完干净收手（光标恢复）", "\x1b[?25h" in raw)
    line("树带判定留在屏幕上",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())
    line("树不重复：真终端走 Live 原地画，不逐帧追加", scr.plain().count("└─") == 1,
         "%d 帧" % scr.plain().count("└─"))
    line("根照样被跑掉", len(RAN) == 1)

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
    line("先问了他要做什么（不是先调模型）", "先说你要做什么" in scr.plain())
    line("说清了怎么发、怎么换行",
         "回车就是发送" in scr.plain() and "Alt-Enter" in scr.plain())

    print("=" * 80)
    print("J. 节点级吐字：每个节点正在说的话/想的事，画进树里它的节点下")
    scr = slow_session([root(), "好，那继续谈。"],
                       [(0.2, "2026-12-31 收盘\r"), (2.2, "\x04")])
    line("思考一小口一小口按 node_id 画进树", "▸ 思考: 先看看" in scr.plain())
    line("思考的尾巴跟着长（不是只有头一个字）", "再决定怎么" in scr.plain())
    line("content 也画进树（▸ 说:）", "▸ 说: 我要拆成三个子任务" in scr.plain())
    line("树照样跑完、判定留在屏幕上",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())

    print("=" * 80)
    print("K. 跑任务时输入不冻结：敲的字进 Live 帧，跑完按顺序交出去")
    scr = slow_session([root(), "你说的「赚大钱」按哪个数字判定？", "好。"],
                       [(0.15, "2026-12-31 收盘\r"), (0.3, "先停一下\r"),
                        (0.45, "3\r"), (2.5, "\x04")])
    line("跑的时候敲的字没有丢（进过 Live 帧的输入行）",
         "先停一下" in scr.plain())
    line("跑完后输入行的字按顺序交出去",
         scr.plain().count("（运行中你输入了") >= 2,
         "%d 条" % scr.plain().count("（运行中你输入了"))

    print("=" * 80)
    print("L. 每节点一行铺开：整棵树所有节点正在吐的字都看得见（真终端）")
    scr = multi_session([root(), "好，那继续谈。"],
                        [(0.2, "2026-12-31 收盘\r"), (3.0, "\x04")])
    line("三个孩子都在各自的节点行上（不是只显示一个）",
         all(x in scr.plain() for x in
             ["子任务A", "子任务B", "子任务C"]))
    line("三路思考都画进树（每节点一行）",
         all(x in scr.plain() for x in
             ["孩子A在琢磨", "孩子B在琢磨", "孩子C准备写"]))
    line("根的吐字也在自己那行", "根在想怎么拆" in scr.plain())
    line("跑完切回详细帧（判定 + 验收标准都在）",
         "[满足] 账户权益在2026-12-31收盘 >= 本金 x 2" in scr.plain())

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
