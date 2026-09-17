#!/usr/bin/env python3
"""终端会话的定向测试。零成本、确定性（脚本化模型 + 脚本化终端）。

这一层只管"介质与话轮"：把用户敲的字交回去、把入口说的话显示出来、
回车不发送、Ctrl-D/Ctrl-C 干净收手。判断 / 打回 / 收手都是 `tree/intake.py` 的事。

  A. 谈定：问 → 答 → 交出合规的根；问题和建议只显示一遍
  B. 回车不发送：分几行写的回答拼成**一条**交给模型（半句话不会被提前发出去）
  C. 写了东西再按 Ctrl-D = 说完了（照样发出去，不丢）
  D. 什么都没写按 Ctrl-D / Ctrl-C → 干净收手（返回 None），不是 traceback
  E. 旁白（打回理由）显示到终端
  F. 边界守门：terminal 不碰树的决策层；tree 不 import terminal；
     main.py 不再自己读输入
  G. 不是真终端（管道 / 重定向）→ 提示符自己收尾，不粘到下一行
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from terminal.chat import converse, _read_line             # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class FakeLLM:
    """按脚本回话的入口模型，并记下每一轮它看见了什么。"""

    def __init__(self, replies):
        self.replies, self.last_usage, self.seen = list(replies), {}, []

    def chat(self, messages, temperature=0.2):
        self.seen.append(messages[-1]["content"])
        return self.replies.pop(0) if self.replies else "{}"


class Screen:
    """脚本化的终端：read 按顺序吐行，out 把显示过的都收起来。

    它同时是"没有绕过终端"的证明 —— converse 只能通过这个 read 拿到输入。
    """

    def __init__(self, lines):
        self.lines, self.shown, self.prompts = list(lines), [], []

    def read(self, prompt):
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError()
        return self.lines.pop(0)

    def out(self, text):
        self.shown.append(str(text))

    def text(self):
        return "\n".join(self.shown)


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "keywords": ["A股", "回测", "2026-12-31"], "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def ask_reply(content):
    """入口只说一句 content（问题、建议都在里面）。"""
    return json.dumps({"ask": {"content": content}})


def main():
    print("=" * 80)
    print("A. 谈定：问 → 答 → 交出合规的根")
    Q = "你说的「赚大钱」按哪个数字判定？"
    S = "我建议写成：账户权益 >= 本金 x 2"
    llm = FakeLLM([ask_reply(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["2026-12-31 收盘", ""])          # 一行回答 + 空行表示说完
    r = converse(llm, "帮我赚大钱", read=scr.read, out=scr.out)
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.shown))
    line("交出了合规的根", "root" in r
         and r["root"]["accept"] == "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("问题送到了终端", Q in scr.text())
    line("建议跟着问题一起送到", S in scr.text())
    line("分行的话不被压成一行（content 原样）", (Q + "\n" + S) in scr.text())
    line("同一个问题只显示一遍", scr.text().count(Q) == 1)
    line("答的话进了下一轮上下文",
         any("2026-12-31 收盘" in s for s in llm.seen))
    line("回答要经终端读（第一行 + 空行各读一次）", len(scr.prompts) == 2)
    line("发了之后说清发出去了", "发出" in scr.text())
    line("交棒时说清了根长什么样", "入口交棒" in scr.text())

    print("=" * 80)
    print("B. 回车不发送：分几行写的回答拼成一条（半句话不会被提前发出去）")
    llm = FakeLLM([ask_reply(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["我要一个", "能跑通这个仓库所有测试的", "任务", ""])
    r = converse(llm, "帮我赚大钱", read=scr.read, out=scr.out)
    print("  模型看见的那一条：%r" % llm.seen[1][-40:])
    line("三行都进去了", all(x in llm.seen[1] for x in ("我要一个", "能跑通", "任务")))
    line("拼成的是**一条**消息（换行分隔，不是三条）",
         "我要一个\n能跑通这个仓库所有测试的\n任务" in llm.seen[1])
    line("第一行没被当成答完（模型第一轮只见过问题）",
         "我要一个" not in llm.seen[0])
    line("读了三次（三行 + 空行收尾）", len(scr.prompts) == 4,
         "读了 %d 次" % len(scr.prompts))
    line("续行的提示符与首行不同（看得出还在同一条里）",
         scr.prompts[0] != scr.prompts[1])

    print("=" * 80)
    print("C. 写了东西再按 Ctrl-D = 说完了（不丢）")
    llm = FakeLLM([ask_reply(Q + "\n" + S), json.dumps(root())])
    scr = Screen(["就按你说的办"])                    # 之后 EOF
    r = converse(llm, "帮我赚大钱", read=scr.read, out=scr.out)
    line("写了的内容照样发出去", any("就按你说的办" in s for s in llm.seen))
    line("终端上说明白是 Ctrl-D 收的", "Ctrl-D" in scr.text())
    line("没被当成中止", "root" in r)

    print("=" * 80)
    print("D. 什么都没写按 Ctrl-D / Ctrl-C → 干净收手")
    scr = Screen([])                       # 一行都没有：read 直接 EOF
    r = converse(FakeLLM([ask_reply(Q + "\n" + S)]), "帮我赚大钱",
                 read=scr.read, out=scr.out)
    line("返回 None（中止不是结论）", r is None)
    line("终端上说清了是中止", "中止" in scr.text())

    def interrupted(prompt):
        raise KeyboardInterrupt()

    r = converse(FakeLLM([ask_reply(Q + "\n" + S)]), "帮我赚大钱",
                 read=interrupted, out=lambda t: None)
    line("Ctrl-C 也收手", r is None)

    print("=" * 80)
    print("E. 旁白（打回理由）显示到终端")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),   # 没有可测物理量
                   json.dumps(root())])
    scr = Screen([])
    r = converse(llm, "帮我赚大钱", read=scr.read, out=scr.out)
    print("  终端上显示的：\n%s" % "\n".join("    " + x for x in scr.shown))
    line("打回理由走了旁白通道", "可测物理量" in scr.text())
    line("打回后照样能谈成", "root" in r)

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
    import contextlib
    import io

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
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
