#!/usr/bin/env python3
"""终端会话的定向测试。零成本、确定性（脚本化模型 + 脚本化终端 + 脚本化的树）。

这一层只管"介质与话轮"：把用户敲的字交回去、把入口说的话显示出来、
思考画成灰的、回车不发送、Ctrl-D/Ctrl-C 干净收手。判断 / 打回 / 跑树 /
收手都是 `tree/intake.py` 的事（这里把 `tree.intake.run` 换成脚本）。

入口现在不退场：谈成一个根就跑一次、结论回填，再接着谈。所以 `converse`
到最后总是**由用户中止**才返回 `None`（没有"交棒"那一步了）。

  A. 谈定：问 → 答 → 交出的根被跑掉；问题和建议只显示一遍
  B. 回车不发送：分几行写的回答拼成**一条**交给模型（半句话不会被提前发出去）
  C. 写了东西再按 Ctrl-D = 说完了（照样发出去，不丢）
  D. 什么都没写按 Ctrl-D / Ctrl-C → 干净收手（返回 None），不是 traceback
  E. 旁白（打回理由、接到任务/跑完了）显示到终端
  F. 边界守门：terminal 不碰树的决策层；tree 不 import terminal；
     main.py 不再自己读输入
  G. 不是真终端（管道 / 重定向）→ 提示符自己收尾，不粘到下一行
  H. 用户没交底：入口开口之前，先让他把话说完（不是先调模型）
  I. 思考（reasoning_content）整段按流式吐出来，而且是灰的
"""

import asyncio
import contextlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import tree.intake as intake_mod                           # noqa: E402
from terminal.chat import GRAY, converse, opening, _read_line   # noqa: E402

OK = []
RAN = []
ENV = {"trace": None}


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class FakeLLM:
    """按脚本回话的入口模型，并记下每一轮它看见了什么。"""

    def __init__(self, replies, reasoning=""):
        self.replies, self.last_usage, self.seen = list(replies), {}, []
        self.reasoning = reasoning

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None):
        self.seen.append(messages[-1]["content"])
        if self.reasoning and on_reasoning:
            for i in range(0, len(self.reasoning), 4):   # 思考也一小口一小口
                on_reasoning(self.reasoning[i:i + 4])
        reply = self.replies.pop(0) if self.replies else "{}"
        if on_delta:
            for i in range(0, len(reply), 5):    # 一小口一小口地吐
                on_delta(reply[i:i + 5])
        return reply


async def fake_run(root, llm, trace, registry=None, budget=None, workers=6,
                caps=None, index=None, **kwargs):
    """脚本化的树：记下跑了哪棵根，给一个可复核的结论。"""
    RAN.append(root)
    root.close("满足", "跑完了：%s" % root.name, ["证据"])
    return root


intake_mod.run = fake_run


class Screen:
    """脚本化的终端：read 按顺序吐行，out 收整行，write 收吐字碎片。

    它同时是"没有绕过终端"的证明 —— converse 只能通过这个 read 拿到输入。
    """

    def __init__(self, lines):
        self.lines, self.shown, self.prompts = list(lines), [], []
        self.stream = []

    def read(self, prompt):
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError()
        return self.lines.pop(0)

    def out(self, text):
        self.shown.append(str(text))

    def write(self, text):
        self.stream.append(str(text))

    def text(self):
        return "\n".join(self.shown) + "".join(self.stream)


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "keywords": ["A股", "回测", "2026-12-31"], "conc_range": [100, 500]}
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
    llm = FakeLLM([talk(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["2026-12-31 收盘", ""])          # 一行回答 + 空行表示说完
    RAN.clear()
    r = asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=scr.out,
                            write=scr.write))
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.shown))
    line("模型的话送到了终端", Q in scr.text() and S in scr.text())
    line("分行的话不被压成一行（content 原样）", (Q + "\n" + S) in scr.text())
    line("同一个问题只显示一遍", scr.text().count(Q) == 1)
    line("模型的话是一小口一小口吐出来的（不是整段一次）", len(scr.stream) > 1,
         "%d 口" % len(scr.stream))
    line("吐到屏幕上的拼起来就是模型的原话",
         "".join(scr.stream).strip() == (Q + "\n" + S))
    line("答的话进了下一轮上下文",
         any("2026-12-31 收盘" in s for s in llm.seen))
    line("合规的根被拿去跑了", len(RAN) == 1
         and RAN[0].accept == "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("旁白说清了接到任务、跑完了",
         "接到任务" in scr.text() and "跑完了" in scr.text())
    line("回答经终端读（首行 + 续行）",
         scr.prompts[:2] == ["› ", "  "])
    line("发了之后说清发出去了", "发出" in scr.text())
    line("用户中止才返回（入口不退场）", r is None)

    print("=" * 80)
    print("B. 回车不发送：分几行写的回答拼成一条（半句话不会被提前发出去）")
    llm = FakeLLM([talk(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["我要一个", "能跑通这个仓库所有测试的", "任务", ""])
    RAN.clear()
    asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=scr.out, write=scr.write))
    print("  模型看见的那一条：%r" % llm.seen[1][-40:])
    line("三行都进去了", all(x in llm.seen[1] for x in ("我要一个", "能跑通", "任务")))
    line("拼成的是**一条**消息（换行分隔，不是三条）",
         "我要一个\n能跑通这个仓库所有测试的\n任务" in llm.seen[1])
    line("第一行没被当成答完（模型第一轮只见过问题）",
         "我要一个" not in llm.seen[0])
    line("三行各读一次、空行收尾",
         scr.prompts[:4] == ["› ", "  ", "  ", "  "], str(scr.prompts[:4]))
    line("续行的提示符与首行不同（看得出还在同一条里）",
         scr.prompts[0] != scr.prompts[1])

    print("=" * 80)
    print("C. 写了东西再按 Ctrl-D = 说完了（不丢）")
    llm = FakeLLM([talk(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["就按你说的办"])                    # 之后 EOF
    RAN.clear()
    asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=scr.out, write=scr.write))
    line("写了的内容照样发出去", any("就按你说的办" in s for s in llm.seen))
    line("终端上说明白是 Ctrl-D 收的", "Ctrl-D" in scr.text())
    line("内容没丢：根照样被跑掉", len(RAN) == 1)

    print("=" * 80)
    print("D. 什么都没写按 Ctrl-D / Ctrl-C → 干净收手")
    scr = Screen([])                       # 一行都没有：read 直接 EOF
    r = asyncio.run(converse(FakeLLM([talk(Q + "\n" + S)]), "帮我赚大钱", ENV,
                              read=scr.read, out=scr.out, write=scr.write))
    line("返回 None（中止不是结论）", r is None)
    line("终端上说清了是中止", "中止" in scr.text())

    def interrupted(prompt):
        raise KeyboardInterrupt()

    r = asyncio.run(converse(FakeLLM([talk(Q + "\n" + S)]), "帮我赚大钱", ENV,
                              read=interrupted, out=lambda t: None,
                              write=lambda t: None))
    line("Ctrl-C 也收手", r is None)

    print("=" * 80)
    print("E. 旁白（打回理由）显示到终端")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),   # 没有可测物理量
                   json.dumps(root())])
    scr = Screen([])
    RAN.clear()
    asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=scr.out, write=scr.write))
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.shown))
    line("打回理由走了旁白通道", "可测物理量" in scr.text())
    line("交形式的那一段不吐给用户（那是给闸门的）",
         "{" not in "".join(scr.stream))
    line("打回后照样把改好的根跑了", len(RAN) == 1)

    print("=" * 80)
    print("F. 边界：依赖单向（terminal→tree.intake，tree 不认识 terminal）")
    src = open(os.path.join(ROOT, "terminal", "chat.py"), encoding="utf-8").read()
    line("终端层不碰树的决策层（tree.run / tree.node）",
         "tree.run" not in src and "tree.node" not in src)
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

    print("=" * 80)
    print("G. 不是真终端（管道 / 重定向）→ 提示符自己收尾")

    class NotATty(io.StringIO):
        def isatty(self):
            return False

    old, sys.stdin = sys.stdin, NotATty("答案\n")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            got = _read_line("› ")
    finally:
        sys.stdin = old
    line("读到了那一行", got == "答案")
    line("提示符后面补了换行（否则下一句会挂到同一行）",
         buf.getvalue() == "› \n", repr(buf.getvalue()))

    print("=" * 80)
    print("H. 用户没交底：入口开口之前，先让他把话说完")
    scr = Screen(["我要做一个", "能跑通这个仓库所有测试的东西", ""])
    got = opening(read=scr.read, out=scr.out)
    print("  收下的开场白：%r" % got)
    line("多行拼成一条开场白", got == "我要做一个\n能跑通这个仓库所有测试的东西")
    line("先问了他要做什么（不是先调模型）",
         any("先说你要做什么" in s for s in scr.shown))

    print("=" * 80)
    print("I. 思考（reasoning_content）整段按流式吐出来，而且是灰的")
    think = "先看看用户到底想要什么，再决定要不要开一个任务"
    llm = FakeLLM([talk("好，我想清楚了。")], reasoning=think)
    scr = Screen([""])                     # 空行收尾，之后中止
    class Tty(io.StringIO):
        def isatty(self):
            return True
    buf = Tty()
    old = sys.stdout
    sys.stdout = buf
    try:
        asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=None, write=None))
    finally:
        sys.stdout = old
    got = buf.getvalue()
    plain = re.sub(r"\033\[[0-9;]*m", "", got)       # 去掉颜色码看原文
    line("思考的原文整段都显示了", think in plain)
    line("思考是一小口一小口吐的（不是一次一坨）", got.count(GRAY) > 1,
         "%d 次" % got.count(GRAY))
    line("用的是灰色", GRAY in got)
    line("回答和思考分开了（思考后换了行）", "\n好，我想清楚了。" in plain)

    llm = FakeLLM([talk("好。")], reasoning=think)
    scr = Screen([""])
    asyncio.run(converse(llm, "帮我赚大钱", ENV, read=scr.read, out=scr.out, write=scr.write))
    line("不是真终端（自定义 write）→ 思考只留原文、不上色",
         GRAY not in "".join(scr.stream) and think in "".join(scr.stream))

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
