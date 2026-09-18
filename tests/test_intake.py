#!/usr/bin/env python3
"""入口的定向测试。零成本、确定性（脚本化模型 + 脚本化用户 + 脚本化的树）。

入口不退场：谈成一个能过闸门的根，就**当场跑它**（`tree.intake` 直接调
`tree.runtime.scheduler`），把结论作为一条外部观测回填给对话，再接着调模型 —— 直到
用户中止。所以这里的 `run` 换成脚本，只记下"跑了哪棵根、结论是什么"。

**对话的形式不归代码管** —— 代码不认识回合数，也不规定"一次只能问一个"、
"提问必须带建议"。它只认一条：**只有带 `root` 键的 JSON 算形式，其余都是话。**

  A. 谈定 → 打回 → 交出合规的根 → **跑掉、结论回填**
  B. 形式不合规 → 当场打回并说清为什么
  C. 只认 root：多行的话、带 JSON 但不是 root 的、甚至解析不出来的，都当话送出去
  D. 没有回合数 / 重复次数的限制（计数器删了就不许回来）
  E. 闸门：缺字段 / 没有可测物理量，都当场说不，并给得出理由
  F. 吐字：话一路出去，形式一路按住（连 ```json 围栏也不吐）
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tree.intake as intake_mod                          # noqa: E402
from tree.intake import _Spoken, intake, root_in          # noqa: E402
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
    """按脚本回话的入口模型：脚本里一串字符串，就是它的每次输出。"""

    def __init__(self, replies):
        self.replies, self.last_usage, self.said = list(replies), {}, []

    def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None):
        self.said.append(messages[-1]["content"])
        reply = self.replies.pop(0) if self.replies else "{}"
        if on_reasoning:
            on_reasoning("（想了想）")
        if on_delta:
            for i in range(0, len(reply), 5):    # 一小口一小口地吐
                on_delta(reply[i:i + 5])
        return reply


def fake_run(root, llm, trace, registry=None, budget=None, workers=6,
             caps=None, index=None, **kwargs):
    """脚本化的树：只记下跑了哪棵根，给一个可复核的结论。"""
    RAN.append(root)
    root.close("满足", "跑完了：%s" % root.name, ["证据 %s" % root.name])
    return root


intake_mod.run = fake_run


def run_intake(llm, seed, answers):
    """跑入口；脚本化的用户答完就中止。返回 (问过的话, 旁白)。"""
    asked, said = [], []
    answers = list(answers)

    def ask(t):
        asked.append(t)
        if not answers:
            raise Stop()
        return answers.pop(0)

    try:
        intake(llm, seed, ask=ask, env=ENV, on_say=said.append)
    except Stop:
        pass
    return asked, said


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "keywords": ["A股", "回测", "2026-12-31"], "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def main():
    print("=" * 80)
    print("A. 谈定 → 打回 → 交出合规的根 → 跑掉、结论回填")
    talk = ("你说的「赚大钱」按哪个数字判定？\n"
            "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")), talk, json.dumps(root())])
    RAN.clear()
    asked, said = run_intake(llm, "帮我做个能赚大钱的A股量化系统（我没说怎么算赚到）",
                             ["2026-12-31 收盘前"])
    print("  问过用户: %r" % asked)
    print("  跑过的根: %s" % [r.name for r in RAN])
    line("打了回去，并说了为什么", any("可测物理量" in s for s in said))
    line("话原样送到用户面前（不添字、不包装、不压行）",
         bool(asked) and asked[0] == talk)
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("合规的根被拿去跑了", [r.accept for r in RAN] ==
         ["账户权益在2026-12-31收盘 >= 本金 x 2"])
    line("结论作为外部观测回填给入口",
         any("任务执行结果" in s and "跑完了" in s for s in llm.said))
    line("回填的结论上是判定与证据",
         any("判定: 满足" in s and "证据" in s for s in llm.said))
    line("根的可测物理量被识别出来", bool(anchors(RAN[0].accept)))

    print("=" * 80)
    print("B. 形式不合规 → 打回；改一次就过")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),   # 没有可测物理量
                   json.dumps(root())])
    RAN.clear()
    _, said = run_intake(llm, "帮我赚大钱", [])
    line("打回时把原因摆出来了", any("用不了" in x and "可测物理量" in x for x in said))
    line("改一次后过了闸门并被跑掉", len(RAN) == 1)
    line("打回走旁白，不占用户的话轮", not any("用不了" in x for x in
                                              [str(x) for x in llm.said[:1]]))

    print("=" * 80)
    print("C. 只认 root：其余一律当话")
    # ① 多行的话
    multi = "我先复述一遍你的意思：\n① 做视频\n② 目标是赚钱\n对吗？"
    llm = FakeLLM([multi, json.dumps(root())])
    RAN.clear()
    asked, _ = run_intake(llm, "帮我做视频赚钱", ["对"])
    line("① 多行的话原样送出去", asked and asked[0] == multi)

    # ② 带 JSON 但不是 root（比如模型顺手写了个 ask）
    weird = json.dumps({"ask": {"content": "你要做什么？"}}, ensure_ascii=False)
    llm = FakeLLM([weird, json.dumps(root())])
    RAN.clear()
    asked, _ = run_intake(llm, "帮我赚大钱", ["做系统"])
    line("② 没有 root 键 → 也当话（代码不认第二种形式）",
         asked and asked[0] == weird)
    line("② 照样跑到了一棵根", len(RAN) == 1)

    # ③ 完全不是 JSON
    llm = FakeLLM(["你好，我们聊聊这件事。", json.dumps(root())])
    RAN.clear()
    asked, _ = run_intake(llm, "帮我赚大钱", ["好"])
    line("③ 纯聊天不被当成出错", asked and asked[0] == "你好，我们聊聊这件事。")

    # root_in 的识别规则本身就是唯一事实
    line("root_in 只认带 root 键的 JSON",
         root_in(json.dumps(root())) is not None
         and root_in(json.dumps({"ask": "x"})) is None
         and root_in("我说句话") is None)

    print("=" * 80)
    print("D. 没有回合数 / 重复次数的限制（删掉的计数器不许回来）")
    replies = ["那你要哪个平台？我建议抖音"] * 8 + [json.dumps(root())]
    llm = FakeLLM(replies)
    RAN.clear()
    asked, _ = run_intake(llm, "帮我赚大钱", ["抖音"] * 8)
    print("  同一句话说了 %d 次，仍然继续" % sum("平台" in a for a in asked))
    line("说 8 次也没被计数器逼停", sum("平台" in a for a in asked) == 8,
         "说了 %d 次" % sum("平台" in a for a in asked))
    line("最后照样跑到了一棵根", len(RAN) == 1)

    print("=" * 80)
    print("E. 闸门：缺字段 / 没有可测物理量，都当场说不")
    for spec, tag in (
            (root(accept="系统做好了")["root"], "没有可测物理量"),
            (root(keywords=[])["root"], "keywords 是空的"),
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
    print("F. 吐字：话一路出去，形式一路按住")

    def spoken(reply):
        got = []
        sp = _Spoken(got.append)
        for i in range(0, len(reply), 5):        # 一小口一小口地吐
            sp.feed(reply[i:i + 5])
        return "".join(got)

    text = "你说的「赚大钱」按哪个数字判定？\n我建议写成：账户权益 >= 本金 x 2"
    line("话原样吐出去（碎片拼回来 = 原话）", spoken(text) == text)
    line("形式按住不吐（纯 JSON）", spoken(json.dumps(root())) == "")
    line("形式按住不吐（```json 围栏也没漏出去）",
         spoken("```json\n" + json.dumps(root()) + "\n```") == "")
    line("头一个实义字符不是 { → 当话吐出去",
         spoken("\n\n你好。") == "\n\n你好。")

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
