#!/usr/bin/env python3
"""入口的定向测试。零成本、确定性（脚本化模型 + 脚本化用户 + 脚本化的树）。

入口不退场：谈成一个能过闸门的根，就**当场跑它**（`tree.intake` 直接调
`tree.runtime.scheduler`），把结论作为工具结果回填给对话，再接着调模型 —— 直到
用户中止。所以这里的 `run` 换成脚本，只记下"跑了哪棵根、结论是什么"。

**通道与节点同构**：模型要么说话（content，流式送出去），要么调 `submit_root`
交形式。代码不认"话里的 JSON"，所以不再有"从文本里猜形式"的识别规则。

  A. 谈定 → 打回 → 交出合规的根 → **跑掉、结论回填**
  B. 形式不合规 → 当场打回并说清为什么
  C. 只认工具调用：不带 root 的话、甚至不是 root 的 JSON，都当话送出去
  D. 没有回合数 / 重复次数的限制（计数器删了就不许回来）
  E. 闸门：缺字段 / 没有可测物理量，都当场说不，并给得出理由
  F. 吐字：话一路出去，交形式（工具调用）一路不吐
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tree.intake as intake_mod                          # noqa: E402
from tree.intake import intake                            # noqa: E402
from tree.llm import Message, ToolCall                    # noqa: E402
from tree.protocol.gate import anchors, validate_root     # noqa: E402

OK = []
RAN = []
ENV = {"trace": None}


class Stop(Exception):
    """脚本用完了：等价于用户在终端上中止（intake 不拦，测试用它收手）。"""


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class FakeLLM:
    """按脚本回话的入口模型：字符串 = 说话，带 root 的 dict = 调 submit_root。"""

    def __init__(self, replies):
        self.replies, self.last_usage, self.said = list(replies), {}, []

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.said.append(messages[-1]["content"])
        spec = self.replies.pop(0) if self.replies else ""
        if isinstance(spec, dict) and "root" in spec:
            reply, calls = "", [ToolCall(name="submit_root",
                                         arguments={"root": spec["root"]})]
        elif isinstance(spec, dict):                     # 带 JSON 但不是 root → 当话
            reply, calls = json.dumps(spec, ensure_ascii=False), []
        else:
            reply, calls = str(spec or ""), []
        if on_reasoning:
            on_reasoning("（想了想）")
        if on_delta:
            for i in range(0, len(reply), 5):    # 一小口一小口地吐
                on_delta(reply[i:i + 5])
        return Message(text=reply, tool_calls=calls)


async def fake_run(root, llm, trace, registry=None, budget=None, workers=6,
                on_event=None, **kwargs):
    """脚本化的树：只记下跑了哪棵根，给一个可复核的结论。

    真调度器每开/关一个节点发一次 on_event，这里也照发两次（出生+出结论），
    证明入口把 env["on_event"] 一路透传到了 run。
    """
    RAN.append(root)
    if on_event:
        on_event(root)
    root.close("满足", "跑完了：%s" % root.name, ["证据 %s" % root.name])
    if on_event:
        on_event(root)
    return root


intake_mod.run = fake_run


def run_intake(llm, seed, answers):
    """跑入口；脚本化的用户答完就中止。返回 (问过的话, 旁白, 节点事件)。"""
    asked, said, events = [], [], []
    answers = list(answers)

    async def ask(t):
        asked.append(t)
        if not answers:
            raise Stop()
        return answers.pop(0)

    env = dict(ENV, on_event=events.append)
    try:
        asyncio.run(intake(llm, seed, ask=ask, env=env, on_say=said.append))
    except Stop:
        pass
    return asked, said, events


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def main():
    print("=" * 80)
    print("A. 谈定 → 打回 → 交出合规的根 → 跑掉、结论回填")
    talk = ("你说的「赚大钱」按哪个数字判定？\n"
            "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2")
    llm = FakeLLM([root(accept="系统做好了"), talk, root()])
    RAN.clear()
    asked, said, events = run_intake(llm, "帮我做个能赚大钱的A股量化系统（我没说怎么算赚到）",
                                     ["2026-12-31 收盘前"])
    print("  问过用户: %r" % asked)
    print("  跑过的根: %s" % [r.name for r in RAN])
    line("打了回去，并说了为什么", any("可测物理量" in s for s in said))
    line("话原样送到用户面前（不添字、不包装、不压行）",
         bool(asked) and asked[0] == talk)
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("合规的根被拿去跑了", [r.accept for r in RAN] ==
         ["账户权益在2026-12-31收盘 >= 本金 x 2"])
    line("结论作为工具结果回填给入口",
         any("任务执行结果" in s and "跑完了" in s for s in llm.said))
    line("回填的结论上是判定与证据",
         any("判定: 满足" in s and "证据" in s for s in llm.said))
    line("根的可测物理量被识别出来", bool(anchors(RAN[0].accept)))
    line("节点事件一路透传到 run（出生+出结论各一次，同一棵根）",
         len(events) == 2 and all(e is RAN[0] for e in events))

    print("=" * 80)
    print("B. 形式不合规 → 打回；改一次就过")
    llm = FakeLLM([root(accept="系统做好了"),   # 没有可测物理量
                   root()])
    RAN.clear()
    _, said, _ = run_intake(llm, "帮我赚大钱", [])
    line("打回时把原因摆出来了", any("用不了" in x and "可测物理量" in x for x in said))
    line("改一次后过了闸门并被跑掉", len(RAN) == 1)
    line("打回走旁白，不占用户的话轮", not any("用不了" in x for x in
                                              [str(x) for x in llm.said[:1]]))

    print("=" * 80)
    print("C. 只认工具调用：其余一律当话")
    # ① 多行的话
    multi = "我先复述一遍你的意思：\n① 做视频\n② 目标是赚钱\n对吗？"
    llm = FakeLLM([multi, root()])
    RAN.clear()
    asked, _, _ = run_intake(llm, "帮我做视频赚钱", ["对"])
    line("① 多行的话原样送出去", asked and asked[0] == multi)

    # ② 带 JSON 但不是 root（比如模型顺手写了个 ask）→ 还是话
    weird = json.dumps({"ask": {"content": "你要做什么？"}}, ensure_ascii=False)
    llm = FakeLLM([weird, root()])
    RAN.clear()
    asked, _, _ = run_intake(llm, "帮我赚大钱", ["做系统"])
    line("② 不是 submit_root → 也当话（代码不认第二种形式）",
         asked and asked[0] == weird)
    line("② 照样跑到了一棵根", len(RAN) == 1)

    # ③ 完全不是 JSON
    llm = FakeLLM(["你好，我们聊聊这件事。", root()])
    RAN.clear()
    asked, _, _ = run_intake(llm, "帮我赚大钱", ["好"])
    line("③ 纯聊天不被当成出错", asked and asked[0] == "你好，我们聊聊这件事。")

    print("=" * 80)
    print("D. 没有回合数 / 重复次数的限制（删掉的计数器不许回来）")
    replies = ["那你要哪个平台？我建议抖音"] * 8 + [root()]
    llm = FakeLLM(replies)
    RAN.clear()
    asked, _, _ = run_intake(llm, "帮我赚大钱", ["抖音"] * 8)
    print("  同一句话说了 %d 次，仍然继续" % sum("平台" in a for a in asked))
    line("说 8 次也没被计数器逼停", sum("平台" in a for a in asked) == 8,
         "说了 %d 次" % sum("平台" in a for a in asked))
    line("最后照样跑到了一棵根", len(RAN) == 1)

    print("=" * 80)
    print("E. 闸门：缺字段 / 没有可测物理量，都当场说不")
    for spec, tag in (
            (root(accept="系统做好了")["root"], "没有可测物理量"),
            (root(conc_range=[500, 100])["root"], "conc_range 形状不对"),
            (root(name="")["root"], "name 是空的"),
            (root(kind="dispatch|leaf")["root"], "kind 写成示例里的两种之一"),
            (root(kind="")["root"], "kind 没填"),
            (root(accept="")["root"], "accept 是空的")):
        out, why = validate_root(spec)
        print("  %-16s → %s" % (tag, why))
        line("拒绝: " + tag, out is None and bool(why))
    out, why = validate_root(root()["root"])
    line("合规的根能过", out is not None and why is None)

    print("=" * 80)
    print("F. 吐字：话一路出去，交形式（工具调用）一路不吐")

    def streamed(reply):
        async def stop_ask(t):
            raise Stop()
        got = []
        llm = FakeLLM([reply])
        try:
            asyncio.run(intake(llm, "帮我赚大钱", ask=stop_ask, env=ENV,
                               on_delta=got.append))
        except Stop:
            pass
        return "".join(got)

    text = "你说的「赚大钱」按哪个数字判定？\n我建议写成：账户权益 >= 本金 x 2"
    line("话原样吐出去（碎片拼回来 = 原话）", streamed(text) == text)
    line("交形式不吐（纯工具调用，没有 content）", streamed(root()) == "")
    line("头一个实义字符不是 { → 当话吐出去", streamed("\n\n你好。") == "\n\n你好。")

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
