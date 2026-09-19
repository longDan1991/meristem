#!/usr/bin/env python3
"""盒子与 code-mode 的纪律测试：**能力库里的 cap 变成可调用的 API**。

这套东西的前提是「散文 → API」那一步：模型不抄配方，而是调函数。所以这里
逐个钉住那些一步走错就会静默出错的地方：
  A. 注册 → 搜索 → 签名（可调用的与只有配方的分得清）
  B. 调用：填模板、类型转换、缺参/多参当场抛（错签名比没签名更坏）
  C. 绑定：名字净化（中文名 / 非法名 / 协议自己的名字不能被盖掉）
  D. 一段代码跑起来：print 是观测、最后一行表达式的值回传、错误可见
  E. 超时是**一条观测**（不是静默杀掉）
  F. 运行时搜索：命中什么就当场装成可调用的函数
  G. 产出记账靠**工作区 diff**（代码里直接 open() 写的文件也跑不掉）
  H. 复用反馈：调函数和"照抄配方"两条路都记账（自清洁靠它）

不需要模型、不需要网络：跑的是真 bash，但都是 echo / 写文件这类本地命令。
"""

import asyncio
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = tempfile.mkdtemp()                      # 工作区必须在 import config 之前定
os.environ["TREE_CAPS"] = os.path.join(WORK, "caps.jsonl")
os.environ["TREE_SNIPPET_DIR"] = os.path.join(WORK, ".tree")

from tree.memory.caps import Caps                            # noqa: E402
from tree.runtime.box import Box, fill, func_name, signature  # noqa: E402
from tree.runtime.hands import Hands                         # noqa: E402
from tree.runtime import sandbox                             # noqa: E402
from tree.effects import classify_paths, contract_problems, snapshot_workspace  # noqa: E402
from tree.memory.mine import caps_from_node                   # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-48s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def tool(name, cmd, params=None):
    """`fill` 的输入 —— 盒子里那个形状（`Box._tool` 的产物）。"""
    return {"id": "cap:t", "name": name, "desc": "", "params": params or {},
            "cmd": cmd}


def entry(name, func, params=None, cmd=None, does="一条做法", keys=("tool",)):
    """一条**可调用**的 cap：契约里有 name/func（params 可选）。"""
    return {"does": does, "keys": list(keys),
            "契约": {"type": "脚本", "name": name, "func": func,
                     "params": params or {}},
            "how": {"cmd": cmd or func}}


def main():
    asyncio.run(_go())
    print("=" * 78)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


async def _go():
    caps = Caps(os.environ["TREE_CAPS"])
    hands = Hands()
    box = Box(caps, hands)
    cwd = os.getcwd()
    os.chdir(WORK)
    try:
        await _run(caps, box, hands)
    finally:
        os.chdir(cwd)
        await hands.close()


async def _run(caps, box, hands):
    print("=" * 78)
    print("A. 注册 → 搜索 → 签名")
    box.register(entry("write_note", "echo __text__ > note.txt",
                             {"text": {"type": "str", "default": "hi"}},
                             does="把一段话写进 note.txt", keys=["note", "写"]))
    box.register({"does": "只给配方、没有契约的做法", "keys": ["note", "配方"],
                  "how": {"cmd": "echo 配方"}})
    tools, text, hits = box.search("写 note")
    print("  命中 %d 条，其中可调用 %d 条：" % (len(hits), len(tools)))
    for t in tools:
        print("    %s ｜ %s" % (signature(t), t["desc"]))
    print("  给模型看的文字:\n%s" % "\n".join("    " + x for x in text.splitlines()))
    line("没有契约的做法也在文字里（不偷偷丢）", "只给配方" in text)
    line("只有声明了 func 的才变成函数",
         len(tools) == 1 and tools[0]["name"] == "write_note",
         str([t["name"] for t in tools]))
    line("签名里有参数名、类型和默认值",
         signature(tools[0]) == "write_note(text:str=hi)", signature(tools[0]))

    print("=" * 78)
    print("B. 调用：填模板 / 类型转换 / 缺参当场抛")
    t = tools[0]
    line("默认值填进去了", fill(t, {}) == "echo hi > note.txt")
    line("传参覆盖默认值", fill(t, {"text": "你好"}) == "echo 你好 > note.txt")
    it = tool("n_times", "python3 -c 'print(__n__ * 2)'", {"n": {"type": "int"}})
    print("  \"08\" → %s" % fill(it, {"n": "08"}))
    line("int 真的按 int 填（拼字符串会留下 08）",
         "print(8 * 2)" in fill(it, {"n": "08"}))
    st = tool("say", "echo __s__", {"s": {"type": "str"}})
    line("str 参数原样填", fill(st, {"s": "a b"}) == "echo a b")
    for tag, args in (("缺必填参数当场抛", {}),
                      ("多给一个参数也当场抛（错的是调用）", {"n": 1, "typo": 2})):
        try:
            fill(tool("need", "echo __n__", {"n": {"type": "int"}}), args)
            line(tag, False, "没抛")
        except ValueError as e:
            line(tag, True, str(e)[:46])
    line("盒子里的模板没填完就报错（不留 __占位符__ 去执行）",
         "__" not in fill(t, {"text": "x"}))

    print("=" * 78)
    print("C. 绑定名：中文名能用，脏名字和保留名要退化成 cap_<id>")
    line("中文名是合法标识符（Python 允许）", func_name("算总和", "x") == "算总和")
    line("带横杠/空格的名字被净化", func_name("run it-now", "x") == "run_it_now")
    line("协议自己的名字不许被盖掉", func_name("sys", "cap_1") == "cap_1"
         and func_name("print", "cap_1") == "cap_1")
    line("纯符号/数字开头 → 退化", func_name("1st", "cap_1") == "cap_1"
         and func_name("---", "cap_1") == "cap_1")
    bind = box.bindings([{"id": "cap:a", "name": "same", "desc": "一",
                          "params": {}, "cmd": "echo 1"},
                         {"id": "cap:b", "name": "same", "desc": "二",
                          "params": {}, "cmd": "echo 2"}])
    line("重名时后面的退化成 cap_<id>", "cap_b = _api('cap:b')" in bind[1], bind[1])

    print("=" * 78)
    print("D. 一段代码跑起来：print 是观测，最后一行的值回传")
    obs, calls, wrote = await sandbox.run("print('看得见')\nbash(cmd='echo 命令也看得见')\n1 + 2",
                                 [], box, hands, cwd=WORK)
    print("  观测: %r" % obs)
    line("print 进观测", "看得见" in obs)
    line("最后一行表达式的值自动回传", obs.strip().endswith("3"))
    line("真跑过的调用被记下来了", calls and calls[0][0] == "bash", str(calls)[:60])
    obs, _, _ = await sandbox.run("raise ValueError('故意炸一下')", [], box, hands, cwd=WORK)
    line("异常原样给模型看（不是静默）", "ValueError" in obs and "[exit=1]" in obs)
    obs, _, _ = await sandbox.run("nosuchthing()", [], box, hands, cwd=WORK)
    line("名字写错 = NameError（可诊断）", "NameError" in obs)

    print("=" * 78)
    print("E. 超时是一条观测，不是静默杀掉")
    saved = sandbox.SNIPPET_TIMEOUT
    sandbox.SNIPPET_TIMEOUT = 2
    try:
        t0 = time.time()
        obs, _, _ = await sandbox.run("while True:\n    pass", [], box, hands, cwd=WORK)
        print("  花了 %.1f 秒，观测: %r" % (time.time() - t0, obs.strip()[:80]))
        line("说清楚了这是超时", "[超时]" in obs)
        line("说了怎么办（起后台任务再轮询）", "后台" in obs and "轮询" in obs)
        line("没等满默认额度就回来了", time.time() - t0 < 20)
    finally:
        sandbox.SNIPPET_TIMEOUT = saved

    print("=" * 78)
    print("F. 运行时搜索：命中什么就当场装成函数")
    obs, _, _ = await sandbox.run(
        "found = search_tools('note')\n"
        "print('装了:', write_note is not None)\n"
        "write_note(text='late')\n"
        "print(open('note.txt').read().strip())", [], box, hands, cwd=WORK)
    line("search_tools 之后名字就能用", "装了: True" in obs)
    line("调它真的落盘了", "late" in obs)

    print("=" * 78)
    print("G. 产出记账：只认它自己报的路径（不把并发节点写的算到它头上）")
    skip = [caps.path, os.path.join(WORK, "trace.jsonl")]
    before = snapshot_workspace(WORK, skip=skip)
    obs, no_calls, wrote = await sandbox.run(
        "open('direct.py', 'w').write('print(1)')\n"
        "open('data.txt', 'w').write('x')\n"
        "print('写完了')", [], box, hands, cwd=WORK)
    print("  它自己报的写入: %s" % wrote)
    created, _ = classify_paths(wrote, before, WORK)
    names = [os.path.basename(p) for p in created]
    line("代码里 open() 写的文件被抓住了（自己报的）",
         "direct.py" in names and "data.txt" in names, str(names))
    line("没有调用任何工具也不影响记账", no_calls == [] and "写完了" in obs)
    # 并发场景：另一个"节点"（这里是测试自己）在这段时间写的文件，不在它报的名单里
    with open(os.path.join(WORK, "someone_else.py"), "w") as f:
        f.write("x")
    created2, _ = classify_paths(wrote, before, WORK)
    line("别人写的文件不会被算成它的产出",
         "someone_else.py" not in [os.path.basename(p) for p in created2],
         str([os.path.basename(p) for p in created2]))

    print("=" * 78)
    print("H. 复用反馈：调函数 + 照抄配方，两条路都记账")
    caps2 = Caps(os.path.join(WORK, "c2.jsonl"))
    box2 = Box(caps2, hands)
    a = box2.register(entry("write_note2", "echo __text__ > n2.txt",
                            {"text": {"type": "str", "default": "x"}},
                            keys=["write_note2"]))
    tools2, _, _ = box2.search("write_note2")
    await sandbox.run("write_note2(text='a')", tools2, box2, hands, cwd=WORK)
    e = caps2.get(a)
    line("调函数记了 uses", e["uses"] == 1, "uses=%d" % e["uses"])
    for filler in ("b", "c"):
        await sandbox.run("print(bash(cmd=%r))" % ("echo %s > n2.txt" % filler),
                 tools2, box2, hands, cwd=WORK)
    line("把配方照抄到 bash 里跑也算复用，而且每次都记",
         caps2.get(a)["uses"] == 3, "uses=%d" % caps2.get(a)["uses"])

    print("=" * 78)
    print("I. 调用失败是子进程里的异常，且失败被记进库")
    bad = box2.register(entry("always_fail", "false && echo never",
                              keys=["always_fail"]))
    bad_tools, _, _ = box2.search("always_fail")
    obs, _, _ = await sandbox.run("always_fail()", bad_tools, box2, hands, cwd=WORK)
    line("工具本身的失败回到代码里（不是宿主崩）", "Traceback" in obs or "exit" in obs)
    line("失败记进了库（自清洁的原料）", caps2.get(bad)["fails"] == 1,
         "fails=%d" % caps2.get(bad)["fails"])

    print("=" * 78)
    print("J. 闭环：结论里的 params → 下一个节点就能调它")
    # 这是整个机制的命脉：叶子完工 → 挖出带签名的 cap → 后来的节点拿到同名函数。
    learned = caps_from_node(
        "n1", "训练一个模型",
        [("bash", {"cmd": "python3 train.py --epochs 50"}, "done\n[exit=0]")],
        "t.jsonl",
        contracts=[{"path": "/w/train.py", "effects": None, "前置条件": None,
                    "契约": {"type": "程序", "name": "train_model",
                             "func": "python3 train.py --epochs __epochs__",
                             "params": {"epochs": {"type": "int",
                                                    "default": 50}}}}])
    print("  挖出 %d 条，可调用的 %d 条"
          % (len(learned), sum(1 for e in learned if (e.get("契约") or {}).get("func"))))
    caps3 = Caps(os.path.join(WORK, "c3.jsonl"))
    box3 = Box(caps3, hands)
    for e in learned:
        box3.register(e)
    tools3, text3, _ = box3.search("训练一个模型 train epochs")
    names = [t["name"] for t in tools3]
    print("  下一节点拿到: %s" % names)
    line("契约里的 params 跟着 cap 一起进了库",
         any((e.get("契约") or {}).get("params") for e in learned))
    line("下一个节点把它当函数拿得到", "train_model" in names, str(names))
    if "train_model" in names:
        t3 = [t for t in tools3 if t["name"] == "train_model"][0]
        line("签名带参数（它知道要传 epochs:int）",
             signature(t3) == "train_model(epochs:int=50)", signature(t3))
        line("调它拼出的就是当初那条命令",
             fill(t3, {"epochs": 80}) == "python3 train.py --epochs 80")

    print("=" * 78)
    print("K. 错签名进不了库：params 和 func 里的占位符必须对得上")
    for tag, c in (
            ("params 里的名字 func 里没有",
             {"type": "程序", "name": "x", "func": "python3 a.py",
              "params": {"n": {"type": "int"}}}),
            ("func 里有占位符但 params 没说",
             {"type": "程序", "name": "x", "func": "python3 a.py --n __n__"}),
            ("类型不认识",
             {"type": "程序", "name": "x", "func": "python3 a.py __n__",
              "params": {"n": {"type": "list"}}})):
        probs = contract_problems("a.py", c)
        line(tag + " → 被拒", bool(probs), str(probs)[:60])


if __name__ == "__main__":
    sys.exit(main())
