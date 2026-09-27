"""会话选择器：`-r` 时用一个列表让用户挑要加载哪场老会话。

列表用 Textual 的 `OptionList`（↑↓ 挪高亮、回车选中都是部件自己的能力），
这里只把"用户挑了哪一个"还回去。
"""

import sys

from textual.app import App
from textual.binding import Binding
from textual.content import Content
from textual.widgets import OptionList, Static

TITLE = "选择要加载的会话"


class _PickerApp(App):
    """一屏：标题 + 会话列表（拿焦点）+ 一行键位提示。"""

    CSS = """
    #title, #hint { height: 1; padding: 0 1; }
    #hint { color: $text-muted; }
    #picker { height: 1fr; }
    """

    BINDINGS = [Binding("ctrl+c", "cancel", "取消", priority=True)]

    def __init__(self, items, title):
        super().__init__()
        self.items = items
        self.title = title

    def compose(self):
        yield Static(self.title, markup=False, id="title")
        yield OptionList(*[Content.from_text(label, markup=False) for _, label in self.items],
                         id="picker")
        yield Static(" ↑/↓ 选择 · 回车加载 · Ctrl-C 取消", markup=False, id="hint")

    def on_mount(self):
        self.query_one("#picker", OptionList).focus()

    def on_option_list_option_selected(self, event):
        event.stop()
        self.exit(event.option_index)

    def action_cancel(self):
        self.exit(None)


async def pick_session(items, title=TITLE):
    """让用户挑一个会话；items = [(值, 显示行)]，回车返回选中值，取消返回 None。"""
    if not items:
        return None
    if not sys.stdin.isatty():
        # stdin 不是真终端（管道 / 重定向）：Textual 输入驱动在 EOF 下不退出会
        # 挂死（新版不抛 EOFError），没有屏幕可交互就等同取消，不进应用。
        return None
    try:
        index = await _PickerApp(items, title).run_async()
    except EOFError:
        # stdin 关了（不是终端 / 管道没输入），等同于取消
        return None
    return None if index is None else items[index][0]
