"""和入口在终端上把预期谈定。

这里只做两件事：把用户敲的一行交回去、把入口说的话显示出来。
判断、打回、收手全在 `tree/intake.py` 里 —— 不在这里再实现一遍，
否则"什么算合规"就有了两个事实。

两条通道分开，终端才不会把同一个问题显示两遍：
  - 问题与建议走 `ask` 通道，由这里的提示符呈现；
  - 旁白（打回理由、"这个问题你已经问过 3 次了"）走 `on_say` 通道。
"""

import sys

from tree.intake import intake


PROMPT = "› "


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C。

    这是终端上的常态，不是错误 —— 所以不往上抛，就地收手。
    """


def _read_line(prompt):
    """真终端下就是 input：提示符后面跟着你敲的字（tty 自己回显）。

    但 stdin 不是 tty 时（管道、重定向、别人写脚本驱动它），敲的字不回显、
    回车也不回显，input 的提示符就把后面的话挂到了同一行上 —— 实测过。
    所以这种情况自己把提示符和收尾的换行打出来。
    """
    if not sys.stdin.isatty():
        print(prompt, end="", flush=True)
        line = input()
        print()
        return line
    return input(prompt)


def converse(llm, seed, read=None, out=None):
    """把预期谈定。返回 `tree.intake.intake()` 的原样结果：
    `{"root": {...}}` 或 `{"blocked": {...}}`。

    read(prompt) -> 用户敲的一行；out(text) -> 显示一行。
    默认就是真终端（提示符 + input / print），测试把脚本塞进来。
    """
    read = read or _read_line
    out = out or print

    out("\n[入口] 先把预期谈定，再交给根节点。")
    out("       拿不准就直说；不想聊了按 Ctrl-D。\n")

    def ask(question):
        out(question)
        try:
            return read(PROMPT)
        except (EOFError, KeyboardInterrupt):
            raise _Quit()

    try:
        r = intake(llm, seed, ask=ask, on_say=lambda t: out("  " + str(t)))
    except _Quit:
        out("\n[入口] 你在终端上中止了，没有开工。")
        return {"blocked": {"verdict": "阻塞",
                            "text": "用户在终端上中止了入口对话（Ctrl-D / Ctrl-C）",
                            "evidence": []}}

    if "root" in r:
        s = r["root"]
        out("\n[入口交棒] %s" % s["name"])
        out("           验收: %s" % s["accept"])
        out("           检索键: %s" % "、".join(s["keywords"] or []))
    else:
        out("\n[入口判定] %s：%s"
            % (r["blocked"]["verdict"], r["blocked"]["text"]))
    return r
