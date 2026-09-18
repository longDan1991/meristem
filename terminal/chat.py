"""和入口在终端上把预期谈定，并把入口跑出来的东西显示给人看。

这里只做两件事：把用户敲的字交回去、把入口说的话显示出来。
判断、打回、跑任务、收手全在 `tree/intake.py` 里 —— 不在这里再实现一遍，
否则"什么算合规"就有了两个事实。

三条通道分开，终端才不会把同一句话显示两遍：
  - 模型说的话（一段纯文本）走 `ask` 通道；
  - 模型的思考（`reasoning_content`）走 `on_reasoning` 通道，**画成灰的**；
  - 旁白（"接到任务 / 跑完了"）走 `on_say` 通道。

模型的吐字是**真流式**：不是等整段回来再一个字一个字放，而是每到一个字
就立刻写到屏幕上。交形式那一路上不了屏幕 —— 那是给闸门的，不是给人看的
（见 `tree/intake.py` 的 `_Spoken`）。所以 `ask` 不再负责显示模型的话，
它只负责**读**：话已经在吐字时显示过了。

一条硬纪律：**回车永远不发送。** 发送是一个不含糊的独立动作（空行）。
理由是中文字输入法：回车是用来确认候选词的，那一下回车如果当成"发送"，
用户还没写完的话就被传进去了（实测）。同理，粘贴里带换行的多行文本
也不该被当成一串回答。所以：回车换行，空行表示说完了。
"""

import sys

from rich.console import Console
from rich.style import Style

from tree.intake import intake

PROMPT = "› "          # 第一行
CONT = "  "            # 续行：看得出来还在同一条回答里
# 思考的颜色：用 rich 的 dim 样式（`Style(dim=True)` 渲染出来就是这个开码）。
GRAY = "\x1b[2m"


class _Quit(Exception):
    """用户在终端上按了 Ctrl-D / Ctrl-C，而且什么都没写。

    这是终端上的常态，不是错误 —— 所以不往上抛，就地收手。
    """


def _write(text):
    """吐字：不加换行、立刻刷出来 —— 模型吐一个字就看见一个字。"""
    sys.stdout.write(text)
    sys.stdout.flush()


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


def opening(read=None, out=None):
    """入口开口之前，先让用户把要做的事说完 —— 用户没在命令行交底时走这里。

    否则种子是空的，那一次模型调用只够换来一句"你要做什么？"（实测），
    看上去就像程序没等你说话就自作主张。回车只换行、空行才发出的规矩，
    和后面谈定时一模一样。
    """
    read = read or _read_line
    out = out or print
    out("\n[入口] 先说你要做什么？可以分几行写，单独一个空行表示说完了。\n")
    return _read_answer(read, out)


def converse(llm, seed, env, read=None, out=None, write=None):
    """和入口一直谈下去，直到用户在终端上中止（返回 `None`）。

    入口现在**不退场**：每谈成一个任务就跑掉、把结论带回来接着谈。
    所以这里没有"交棒"这一步 —— 跑树是 `tree/intake.py` 的事，
    终端只负责介质与话轮。

    env 是运行现场（trace/caps/index/budget/workers/registry），终端不解释它，
    只转给入口；read(prompt) -> 用户敲的一行；out(text) -> 显示一行；
    write(text) -> 吐字（不加换行）。
    默认就是真终端（提示符 + input / print / stdout），测试把脚本塞进来。
    """
    read = read or _read_line
    out = out or print
    # 上不上色交给 rich 判断：isatty / NO_COLOR / 颜色系统它都处理。
    # 注入 write（非真终端，比如测试脚本）时一律不上色。
    console = Console(file=sys.stdout)
    color = write is None and console.color_system is not None
    write = write or _write

    at_start = [True]              # 上一次写到行首了吗（吐字不加换行，但得记得收行）

    def piece(text, gray=False):
        if not text:
            return
        if gray and color:
            text = Style(dim=True).render(text)
        write(text)
        at_start[0] = text.endswith("\n")

    def close_line():
        if not at_start[0]:
            piece("\n")

    def line(text):
        close_line()
        out(text)
        at_start[0] = True

    line("\n[入口] 把预期谈定，能过闸门就当场拿去跑，跑完接着谈。")
    line("       回车只换行，不会发送；单独一个空行表示说完了。")
    line("       灰色的字是它在想。不想聊了按 Ctrl-D。\n")

    spoken = []                    # 这一轮模型已经吐到屏幕上的话（不含思考）
    thinking = [False]             # 这一轮刚吐过的是不是思考

    def on_reasoning(text):
        thinking[0] = True
        piece(text, gray=True)

    def on_delta(text):
        if thinking[0]:        # 想完了，开始说：换行，把回答和思考分开
            thinking[0] = False
            close_line()
        spoken.append(text)
        piece(text)

    def ask(question):
        # 话在吐字时已经显示过了（连换行都是它的一部分）；
        # 没吐过（比如被当成形式按住、其实不是形式）才由这里补一遍，
        # 否则同一个问题会显示两遍。
        if spoken:
            close_line()
            spoken.clear()
        else:
            line(question)
        return _read_answer(read, out)

    try:
        intake(llm, seed, ask=ask, env=env,
               on_say=lambda t: line("  " + str(t)),
               on_delta=on_delta, on_reasoning=on_reasoning)
    except _Quit:
        line("\n[入口] 你在终端上中止了。")
        return None
    return None
