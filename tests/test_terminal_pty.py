#!/usr/bin/env python3
"""真终端介质测试：把 Textual 应用真的开到 pty 上跑一遍。

无头驱动（`App.run_test`）看不到的那一层在守这里：真驱动进不进备用屏、
接不接管鼠标、方向键在真终端上解析成什么、敲字回车走不走通、Ctrl-C 能不能干净收手。
这一层慢（≈10s：起子进程 + 真终端握手）且需要 pty，所以只放**介质本身**的事实 ——
行为（切频道、尾巴落地、事件不串台…）在 `test_tty.py` 的无头驱动里测。
"""

import fcntl
import os
import pty
import re
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time

from harness import OK, line, ROOT

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[=>]")
WS = re.compile(r"\s+")

# 子进程：一个真跑起来的会话应用（脚本化模型，不要 API key），按 Ctrl-C 收手。
# 焦点落到输入行那一刻写一个标记文件（PTY_READY），父进程等它 —— 焦点是挂载后
# 下一个消息泵才生效的，早于它敲进去的键会被丢掉（真用户敲不了那么快，测试要等）。
CHILD = '''
import asyncio
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, %r)

from core.llm import Message
from core.protocol.fields import INTAKE, LEAF, Node
from core.runtime import store as store_mod
from core.runtime.store import Store
import terminal.chat as chat

REPLY = "先说三条判断标准：一、账户权益翻倍；二、回撤不超过两成；三、六月三十日前跑完。"


class Fake:
    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        if on_reasoning:
            for i in range(0, len("想清楚再动手，第一步先看数据。"), 5):
                on_reasoning("想清楚再动手，第一步先看数据。"[i:i + 5])
                await asyncio.sleep(0.05)
        if on_delta:
            for i in range(0, len(REPLY), 8):
                on_delta(REPLY[i:i + 8])
                await asyncio.sleep(0.05)
        return Message(text=REPLY)


class App(chat._SessionApp):
    """输入行拿住焦点就举手（测试用它同步"可以开始敲键了"）。"""

    def on_mount(self):
        super().on_mount()
        mark = os.environ.get("PTY_READY")
        if mark:
            self.set_interval(0.05, lambda: self.focused is not None
                              and pathlib.Path(mark).write_text("1", encoding="utf-8"))


d = tempfile.mkdtemp()
store_mod.init(d)
st = Store.new(Node(name="会话", kind=INTAKE), seed="帮我赚大钱")
kid = Node(name="归一化", kind=LEAF, parent=st.root.id, conc_range=[1, 2])
st.put([kid])
st.root.children.append(kid.id)
st.append_user(kid.id, "把数据处理干净")
st.append_assistant(kid.id, "处理好了。", [])

asyncio.run(App(st, Fake()).run_async())
print("APP DONE")
''' % ROOT


class Pty:
    """真 pty 上跑一个子进程：喂键、收屏，"等状态"而不是"等秒数"。"""

    def __init__(self, script, extra_env=None):
        self.dir = tempfile.mkdtemp()
        self.child = os.path.join(self.dir, "pty_child.py")
        with open(self.child, "w", encoding="utf-8") as f:
            f.write(script)
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
        self.ready = os.path.join(self.dir, "ready")
        self.master = master
        self.proc = subprocess.Popen(
            [sys.executable, self.child], stdin=slave, stdout=slave, stderr=slave,
            env=dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor",
                     PTY_READY=self.ready, **(extra_env or {})),
            cwd=ROOT, close_fds=True)
        os.close(slave)
        self.raw = []
        self._mark = 0

    def pump(self, sec):
        """收屏 sec 秒；子进程没了就提前返回。"""
        end = time.monotonic() + sec
        while time.monotonic() < end:
            r, _, _ = select.select([self.master], [], [], 0.05)
            if not r:
                continue
            try:
                data = os.read(self.master, 1 << 16)
            except OSError:
                return False
            if not data:
                return False
            self.raw.append(data)
        return True

    def blob(self):
        return b"".join(self.raw)

    def screen(self):
        return ANSI.sub("", self.blob().decode("utf-8", "replace"))

    def flat(self):
        """去掉空白：重画 / 换行 / 框线都不该搅乱"屏上有没有这句话"。"""
        return WS.sub("", self.screen())

    def mark(self):
        """记一个水位：之后只看这以后收到的字节（累计流里的旧内容不算数）。"""
        self._mark = len(self.raw)

    def since(self):
        return WS.sub("", ANSI.sub("", b"".join(self.raw[self._mark:]).decode("utf-8",
                                                                             "replace")))

    def wait_for(self, marker, timeout=20.0, fresh=False):
        """等屏上出现 marker（去掉空白比对）。fresh=True 只看上一个水位之后的。"""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.pump(0.1)
            if marker in (self.since() if fresh else self.flat()):
                return True
        return False

    def wait_ready(self, timeout=20.0):
        """等输入行拿住焦点（那之前敲的键会被丢掉，子进程用标记文件告诉我们）。"""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.pump(0.1)
            if os.path.exists(self.ready) and os.path.getsize(self.ready):
                return True
        return False

    def key(self, data):
        os.write(self.master, data)
        self.pump(0.4)


def main():
    pty_run = Pty(CHILD)
    try:
        line("应用起来了（真终端驱动、第一帧画完）", pty_run.wait_for("选中会话"))
        line("进了备用屏（屏归应用）", b"\x1b[?1049h" in pty_run.blob())
        line("接管了鼠标（滚轮归应用内的日志区）",
             any(s in pty_run.blob() for s in (b"\x1b[?1000h", b"\x1b[?1002h",
                                               b"\x1b[?1003h", b"\x1b[?1006h")))
        line("种子进了日志区", pty_run.wait_for("帮我赚大钱", 5))
        line("入口的话整段上了屏", pty_run.wait_for("先说三条判断标准", 8))
        line("思考在尾巴区流过", pty_run.wait_for("思考:", 5))
        line("树条带在（含子节点）", "归一化" in pty_run.flat())
        line("状态条在", "选中会话" in pty_run.flat())
        line("输入行常驻（提示在）", "回车发送" in pty_run.flat())

        pty_run.mark()
        pty_run.key(b"\x1b[B")                       # ↓ 真方向键
        line("↓ 切频道：日志区换成子节点的对话",
             pty_run.wait_for("选中归一化", 5, fresh=True)
             and pty_run.wait_for("把数据处理干净", 5, fresh=True))
        pty_run.mark()
        pty_run.key(b"\x1b[A")
        line("↑ 切回入口", pty_run.wait_for("选中会话", 5, fresh=True))

        line("输入行拿住焦点（可以开始敲键）", pty_run.wait_ready(10))
        pty_run.mark()
        # 文字与回车分开写：一整段合成键（`hello\r` 一次写）会和 Textual 的键分发抢跑
        # （字符还在部件队列里，App 级回车绑定先到，提交到的是半截字）；真键盘一个键
        # 一次读，不会撞上这条，所以测试照真键盘的写法来。
        pty_run.key(b"hello")
        pty_run.key(b"\r")
        line("敲的字提交后进日志区", pty_run.wait_for("你:hello", 5, fresh=True))

        pty_run.key(b"\x03")                         # Ctrl-C 收手
        done = pty_run.wait_for("APPDONE", 8)
        line("退出时离开备用屏（终端恢复原样）", b"\x1b[?1049l" in pty_run.blob())
        try:
            code = pty_run.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pty_run.proc.kill()
            code = "TIMEOUT"
        line("干净收手（退出码 0 + 收尾标记）", code == 0 and done, code)
    finally:
        if pty_run.proc.poll() is None:
            pty_run.proc.kill()
        os.close(pty_run.master)

    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
