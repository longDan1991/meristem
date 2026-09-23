"""会话选择器：`-r` 时用一个列表让用户挑要加载哪场老会话。

用 prompt_toolkit 自绘极简列表（RadioList 的回车是"只选中不确认"，与"选中即加载"不符）；
它只把"用户挑了哪一个"还回去。
"""

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl

MAX_ROWS = 12


def _visible(items, index):
    n = len(items)
    if n <= MAX_ROWS:
        return items, 0
    top = min(max(0, index - MAX_ROWS // 2), n - MAX_ROWS)
    return items[top:top + MAX_ROWS], top


async def pick_session(items, title="选择要加载的会话", inp=None):
    """让用户挑一个会话；items = [(值, 显示行)]，回车返回选中值，取消返回 None。

    `inp` 只给测试塞管道，键位走的是生产用的同一套。
    """
    if not items:
        return None
    idx = [0]
    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        idx[0] = max(0, idx[0] - 1)

    @kb.add("down")
    def _down(event):
        idx[0] = min(len(items) - 1, idx[0] + 1)

    @kb.add("enter")
    def _enter(event):
        event.app.exit(result=items[idx[0]][0])

    @kb.add("c-d")
    @kb.add("c-c")
    def _cancel(event):
        event.app.exit(result=None)

    def frags():
        visible, top = _visible(items, idx[0])
        out = []
        for off, (_, label) in enumerate(visible):
            i = top + off
            out.append(("class:hl" if i == idx[0] else "",
                        ("> %s\n" if i == idx[0] else "  %s\n") % label))
        return out

    ctrl = FormattedTextControl(frags, key_bindings=kb, focusable=True)
    container = HSplit([
        Window(FormattedTextControl([("bold", " %s" % title)]), height=1),
        Window(ctrl),
        Window(FormattedTextControl([("dim", " ↑/↓ 选择 · 回车加载 · Ctrl-D 取消")]),
               height=1),
    ])
    app = Application(layout=Layout(container), full_screen=True, input=inp)
    try:
        return await app.run_async()
    except EOFError:
        # stdin 关了（不是终端 / 管道没输入），等同于取消
        return None
