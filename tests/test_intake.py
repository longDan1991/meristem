#!/usr/bin/env python3
"""入口的定向测试。零成本、确定性（脚本化模型 + 脚本化用户）。

入口只被用一次：把用户的一句话谈成**根节点的形式化结构**，然后退场。
它没有手（没有 bash/read/write），产物必须过和分配节点同一台闸门。

**对话的形式不归代码管** —— 代码不认识回合数，也不规定"一次只能问一个"、
"提问必须带建议"。所以这里测的是出口那道闸门，和"代码没有在管对话"。

  A. 谈定：问 → 答 → 交出合规的根；`content` 原样送到用户面前（代码不改写）
  B. **只有一个出口**：模型给 blocked 会被打回 —— 行不行是树跑出来的事实，
     不是入口聊出来的判断
  C. 对话形式自由：不带建议、一次问好几件事、ask 直接是一句话 → 都被当成交流
  D. 没有回合数 / 重复次数的限制（计数器删了就不许回来）
  E. 闸门：缺字段 / 没有可测物理量，都当场说不，并给得出理由
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.intake import intake, validate_root            # noqa: E402
from tree.run import anchors                             # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class FakeLLM:
    """按脚本回话的入口模型。"""

    def __init__(self, replies):
        self.replies, self.last_usage, self.said = list(replies), {}, []

    def chat(self, messages, temperature=0.2):
        self.said.append(messages[-1]["content"])
        return self.replies.pop(0) if self.replies else "{}"


def root(**over):
    r = {"name": "做一个能赚钱的量化系统", "detail": "先拆再干", "notes": "",
         "accept": "账户权益在2026-12-31收盘 >= 本金 x 2", "kind": "dispatch",
         "keywords": ["A股", "回测", "2026-12-31"], "conc_range": [100, 500]}
    r.update(over)
    return {"root": r}


def ask_reply(content):
    """入口现在只说一句 `content`（问题、建议、几件事一起说都在里面）。"""
    return json.dumps({"ask": {"content": content}})


def main():
    print("=" * 80)
    print("A. 谈定：没可测物理量的根被打回 → 问用户 → 交出合规的根")
    content = ("你说的「赚大钱」按哪个数字判定？\n"
               "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),
                   ask_reply(content),
                   json.dumps(root())])
    asked = []

    def ask(q):
        asked.append(q)
        return "2026-12-31 收盘前"

    said = []
    r = intake(llm, "帮我做个能赚大钱的A股量化系统（我没说怎么算赚到）",
               ask=ask, on_say=said.append)
    print("  入口问过: %s" % asked)
    print("  交出来的根: %s" % json.dumps(r.get("root", r), ensure_ascii=False)[:120])
    line("打了回去，并说了为什么", any("可测物理量" in s for s in said))
    line("问了用户", len(asked) == 1)
    line("content 原样送到用户面前（不添字、不包装）",
         bool(asked) and asked[0] == content)
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("最终交出的根过了闸门", "root" in r and r["root"]["accept"] ==
         "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("根的可测物理量被识别出来", bool(anchors(r["root"]["accept"])))

    print("=" * 80)
    print("B. 只有一个出口：模型给 blocked 会被打回")
    llm = FakeLLM([json.dumps({"blocked": {
        "verdict": "阻塞", "text": "开户入金需要本人到柜台，工具里没有这个能力",
        "evidence": ["需要人到场"]}}),
        json.dumps(root())])
    said = []
    r = intake(llm, "帮我开个A股账户并打钱进去", ask=lambda q: "", on_say=said.append)
    print("  打回理由: %s" % [x for x in said if "用不了" in x])
    line("blocked 不再是出口（被打回）", any("用不了" in x for x in said))
    line("打回的理由说清了只认两个键", any("ask 或 root" in x for x in said))
    line("改一次后照样能交出根", "root" in r)

    print("=" * 80)
    print("C. 对话形式自由：代码不管你怎么问")
    # ① 只问一句、不带建议
    llm = FakeLLM([ask_reply("你想做什么？"), json.dumps(root())])
    asked, said = [], []

    def ask1(q):
        asked.append(q)
        return "做个能赚钱的量化系统"

    r = intake(llm, "帮我赚大钱", ask=ask1, on_say=said.append)
    print("  ①不带建议：问了 %s" % asked)
    line("① 不带建议不再被打回", not any("用不了" in s for s in said))
    line("① 问题照样送到用户面前", asked and asked[0] == "你想做什么？")
    line("① 照样谈成了", "root" in r)

    # ② 一次问好几件事
    multi = "① 你要哪个平台？② 多久？③ 多少条？"
    llm = FakeLLM([ask_reply(multi), json.dumps(root())])
    asked = []

    def ask2(q):
        asked.append(q)
        return "抖音，30 天，30 条"

    r = intake(llm, "帮我赚大钱", ask=ask2)
    line("② 一次问三件事照样送出去（没有「一次只问一个」）",
         asked and asked[0] == multi, asked[0][:24] if asked else "")

    # ③ ask 直接是一句话，不是对象
    llm = FakeLLM([json.dumps({"ask": "你要做什么？"}), json.dumps(root())])
    asked = []

    def ask3(q):
        asked.append(q)
        return "做个量化系统"

    r = intake(llm, "帮我赚大钱", ask=ask3)
    line("③ ask 是一句话也能继续", asked and asked[0] == "你要做什么？")

    print("=" * 80)
    print("D. 没有回合数 / 重复次数的限制（删掉的计数器不许回来）")
    replies = [ask_reply("那你要哪个平台？我建议抖音")] * 8 + [json.dumps(root())]
    llm = FakeLLM(replies)
    asked = []
    r = intake(llm, "帮我赚大钱", ask=lambda q: (asked.append(q), "抖音")[1])
    print("  同一个问题问了 %d 次，仍然继续" % len(asked))
    line("问 8 次也没被计数器逼停", len(asked) == 8, "问了 %d 次" % len(asked))
    line("最后照样交出了根（收手是模型自己的判断）", "root" in r)

    print("=" * 80)
    print("E. 闸门：缺字段 / 没有可测物理量，都当场说不")
    for spec, tag in (
            (root(accept="系统做好了")["root"], "没有可测物理量"),
            (root(keywords=[])["root"], "keywords 是空的"),
            (root(conc_range=[500, 100])["root"], "conc_range 形状不对"),
            (root(name="")["root"], "name 是空的"),
            (root(accept="")["root"], "accept 是空的")):
        out, why = validate_root(spec)
        print("  %-16s → %s" % (tag, why))
        line("拒绝: " + tag, out is None and bool(why))
    out, why = validate_root(root()["root"])
    line("合规的根能过", out is not None and why is None)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
