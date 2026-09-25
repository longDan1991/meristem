#!/usr/bin/env python3
"""入口的定向测试（零成本、确定性：脚本化模型 + 脚本化用户 + 真调度器）。

入口就是会话的根节点（kind="intake"）：谈成能过闸门的任务就 `submit_root` 挂成孩子，
调度器真跑掉、结论以 child_result 回到根对话。代码不认"话里的 JSON"，形式只从工具调用来。

  A. 谈定 → 打回 → 交出合规的任务 → 跑掉、结论回填
  B. 形式不合规 → 当场打回并说清为什么
  C. 只认工具调用：其余一律当话
  D. 没有回合数 / 重复次数的限制
  E. 闸门：缺字段 / 没有可测物理量，都当场说不
  F. 吐字：话一路出去，交形式一路不吐
"""

import asyncio
import json
import tempfile

from harness import line
from core.llm import Message, ToolCall
from core.protocol.fields import Node
from core.protocol.gate import anchors, validate_root
from core.runtime import store
from core.runtime.loop import run
from core.runtime.store import Store


class Stop(Exception):
    """脚本用完了：等价于用户在终端上中止（run 不拦，测试用它收手）。"""


class FakeLLM:
    """按脚本回话的模型：入口说字符串 / 交带 root 的 dict，任务节点跑一次 bash 就 conclude。"""

    def __init__(self, replies):
        self.replies, self.said = list(replies), []

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.said.append(messages[-1]["content"])
        sysmsg = messages[0]["content"]
        if "把用户的意图" not in sysmsg:
            done = any(m.get("role") == "tool" for m in messages)
            if not done:
                return Message(text="", tool_calls=[ToolCall(
                    name="bash", arguments={"command": "echo hi"})])
            return Message(text="", tool_calls=[ToolCall(
                name="conclude", arguments={"verdict": "满足", "text": "跑完了",
                                            "evidence": ["第1次观测"]})])
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


def run_intake(llm, seed, answers):
    """跑入口根；脚本化的用户答完就中止。返回 (问过的话, 旁白, 节点事件)。"""
    asked, said, events = [], [], []

    def collect(t, p):
        if t in ("loop_start", "loop_end") and p.get("node") is not None \
                and p["node"].kind != "intake":
            events.append(p["node"])

    answers = list(answers)

    async def ask(t):
        asked.append(t)
        if not answers:
            raise Stop()
        return answers.pop(0)

    d = tempfile.mkdtemp()
    store.init(d)
    root = Node(name="会话", kind="intake")
    try:
        asyncio.run(run(Store.new(root, seed=seed),
                        llm, subscribe=collect, ask=ask, say=said.append))
    except Stop:
        pass
    return asked, said, events


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "leaf",
         "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def main():
    print("=" * 80)
    print("A. 谈定 → 打回 → 交出合规的任务 → 跑掉、结论回填")
    talk = ("你说的「赚大钱」按哪个数字判定？\n"
            "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2")
    llm = FakeLLM([root(accept="系统做好了"), talk, root()])
    asked, said, events = run_intake(llm, "帮我做个能赚大钱的A股量化系统（我没说怎么算赚到）",
                                     ["2026-12-31 收盘前"])
    print("  问过用户: %r" % asked)
    line("打了回去，并说了为什么", any("可测物理量" in s for s in said))
    line("话原样送到用户面前（不添字、不包装、不压行）",
         bool(asked) and asked[0] == talk)
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("合规的任务真的被跑掉（结论回填进入口对话）",
         any("下层结论" in str(s) and "满足" in str(s) for s in llm.said))
    line("任务的可测物理量被识别出来",
         bool(anchors(any_accept_from(asked))))
    line("任务节点事件一路透传到 run（出生+出结论各一次，同一棵任务）",
         len(events) == 2 and events[0] is events[1])

    print("=" * 80)
    print("B. 形式不合规 → 打回；改一次就过")
    llm = FakeLLM([root(accept="系统做好了"),   # 没有可测物理量
                   root()])
    said = run_intake(llm, "帮我赚大钱", [])[1]
    line("打回时把原因摆出来了", any("用不了" in x and "可测物理量" in x for x in said))
    line("打回走旁白，不占用户的话轮", not any("用不了" in x for x in
                                              [str(x) for x in llm.said[:1]]))

    print("=" * 80)
    print("C. 只认工具调用：其余一律当话")
    # ① 多行的话
    multi = "我先复述一遍你的意思：\n① 做视频\n② 目标是赚钱\n对吗？"
    llm = FakeLLM([multi, root()])
    asked, _, _ = run_intake(llm, "帮我做视频赚钱", ["对"])
    line("① 多行的话原样送出去", asked and asked[0] == multi)

    # ② 带 JSON 但不是 root（比如模型顺手写了个 ask）→ 还是话
    weird = json.dumps({"ask": {"content": "你要做什么？"}}, ensure_ascii=False)
    llm = FakeLLM([weird, root()])
    asked, _, events = run_intake(llm, "帮我赚大钱", ["做系统"])
    line("② 不是 submit_root → 也当话（代码不认第二种形式）",
         asked and asked[0] == weird)
    line("② 照样跑掉了一棵任务", len(events) == 2)

    # ③ 完全不是 JSON
    llm = FakeLLM(["你好，我们聊聊这件事。", root()])
    asked, _, _ = run_intake(llm, "帮我赚大钱", ["好"])
    line("③ 纯聊天不被当成出错", asked and asked[0] == "你好，我们聊聊这件事。")

    print("=" * 80)
    print("D. 没有回合数 / 重复次数的限制（删掉的计数器不许回来）")
    replies = ["那你要哪个平台？我建议抖音"] * 8 + [root()]
    llm = FakeLLM(replies)
    asked, _, _ = run_intake(llm, "帮我赚大钱", ["抖音"] * 8)
    print("  同一句话说了 %d 次，仍然继续" % sum("平台" in a for a in asked))
    line("说 8 次也没被计数器逼停", sum("平台" in a for a in asked) == 8,
         "说了 %d 次" % sum("平台" in a for a in asked))

    print("=" * 80)
    print("E. 闸门：缺字段 / 没有可测物理量 / 给根标了门槛，都当场说不（且说清是哪一条）")
    for spec, tag, want in (
            (root(accept="系统做好了")["root"], "没有可测物理量", "可测物理量"),
            (root(conc_range=[500, 100])["root"], "conc_range 形状不对", "conc_range"),
            (root(name="")["root"], "name 是空的", "缺必填项"),
            (root(kind="dispatch|leaf")["root"], "kind 写成示例里的两种之一", "kind"),
            (root(kind="")["root"], "kind 没填", "kind"),
            (root(gate=True)["root"], "根标了门槛（根没有兄弟）", "门槛"),
            (root(accept="")["root"], "accept 是空的", "缺必填项")):
        out, why = validate_root(spec)
        print("  %-22s → %s" % (tag, why))
        line("拒绝: " + tag, out is None and want in (why or ""), why)
    out, why = validate_root(root()["root"])
    line("合规的根能过", out is not None and why is None)

    print("=" * 80)
    print("F. 吐字：话一路出去，交形式（工具调用）一路不吐")

    def streamed(reply):
        async def stop_ask(t):
            raise Stop()
        got = []

        def collect(t, p):
            if t == "message_update" and p.get("scope") == root.id \
                    and p.get("kind") == "content":
                got.append(p["delta"])

        d = tempfile.mkdtemp()
        store.init(d)
        root = Node(name="会话", kind="intake")
        try:
            asyncio.run(run(Store.new(root, seed="帮我赚大钱"),
                            FakeLLM([reply]), subscribe=collect, ask=stop_ask))
        except Stop:
            pass
        return "".join(got)

    text = "你说的「赚大钱」按哪个数字判定？\n我建议写成：账户权益 >= 本金 x 2"
    line("话一路出去（碎片拼回来 = 原话）", streamed(text) == text)
    line("交形式不吐（纯工具调用，没有 content）",
         streamed(root()) == "")

    print("=" * 80)
    print("G. 空回车不算回答：不入账、不惊动模型、重新提问")
    llm = FakeLLM(["确认一下：模拟盘还是实盘？", root()])
    asked, _, _ = run_intake(llm, "帮我做视频赚钱", ["", "   ", "对"])
    line("空回车/纯空白没被当成一轮（模型第二次收到的是真回答，不是空串）",
         len(llm.said) >= 2 and llm.said[1] == "对", repr(llm.said[:2]))
    line("空回车后同一句问题重新问，直到答上",
         len(asked) >= 3 and asked[0] == asked[1] == asked[2], repr(asked))


def any_accept_from(asked):
    """从问过的话里找一个像验收标准的串（测试断言用，不严谨）。"""
    for a in asked:
        if "2026-12-31" in str(a):
            return str(a)
    return ""


if __name__ == "__main__":
    main()
