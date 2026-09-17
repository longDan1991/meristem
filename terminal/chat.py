"""和入口在终端上把预期谈定。

这里只做两件事：把用户敲的字交回去、把入口说的话显示出来。
判断、打回、收手全在 `tree/intake.py` 里 —— 不在这里再实现一遍，
否则"什么算合规"就有了两个事实。

两条通道分开，终端才不会把同一个问题显示两遍：
  - 问题与建议走 `ask` 通道，由这里的提示符呈现；
  - 旁白（打回理由、"这个问题你已经问过 3 次了"）走 `on_say` 通道。

一条硬纪律：**回车永远不发送。** 发送是一个不含糊的独立动作（空行）。
理由是中文字输入法：回车是用来确认候选词的，那一下回车如果当成"发送"，
用户还没写完的话就被传进去了（实测）。同理，粘贴里带换行的多行文本
也不该被当成一串回答。所以：回车换行，空行表示说完了。
"""

import sys

from tree.intake import intake

PROMPT = "› "          # 第一行
CONT = "  "            # 续行：看得出来还在同一条回答里


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C，而且什么都没写。

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


def _read_answer(read, out):
    """收一条回答：回车换行，**空行**（或 Ctrl-D）表示说完了。

    Ctrl-D 在已经写了东西时等于"我说完了"，什么都没写时才当中止 ——
    Ctrl-D 打了半天字再按一下就全丢掉，是另一种"没输完就没了"。
    """
    lines = []
    while True:
        try:
            ln = read(PROMPT if not lines else CONT)
        except (EOFError, KeyboardInterrupt):
            if not lines:
                raise _Quit()
            out("  ↳ 收到 Ctrl-D：当你写完了")
            break
        if not ln.strip():
            break
        lines.append(ln.rstrip())
    text = "\n".join(lines)
    out("  ↳ 发出（%d 行）" % len(lines) if lines else "  ↳ 发出（空的）")
    return text


def converse(llm, seed, read=None, out=None):
    """把预期谈定。返回 `tree.intake.intake()` 的原样结果：
    `{"root": {...}}` 或 `{"blocked": {...}}`。

    read(prompt) -> 用户敲的一行；out(text) -> 显示一行。
    默认就是真终端（提示符 + input / print），测试把脚本塞进来。
    """
    read = read or _read_line
    out = out or print

    out("\n[入口] 先把预期谈定，再交给根节点。")
    out("       回车只换行，不会发送；单独一个空行表示说完了。")
    out("       不想聊了按 Ctrl-D。\n")

    def ask(question):
        out(question)
        return _read_answer(read, out)

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
