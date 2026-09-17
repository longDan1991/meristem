#!/usr/bin/env python3
"""入口的定向测试。零成本、确定性（脚本化模型 + 脚本化用户）。

入口只被用一次：把用户的一句话谈成**根节点的形式化结构**，然后退场。
它没有手（没有 bash/read/write），产物必须过和分配节点同一台闸门。

  A. 谈定：先给一个没可测物理量的根 → 被打回 → 问用户 → 交出合规的根
  B. 判断不该开工 → 交一条正式的 blocked 结论（不是客套话）
  C. 一直乱说 → 重复 ≥5 次就收手，写清原因（同一个规矩，DESIGN §2.4）
  D. 同一个问题反复问 → 也会收手（用户答不上来 = 现在不成立）
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


def main():
    print("=" * 80)
    print("A. 谈定：没可测物理量的根被打回 → 问用户 → 交出合规的根")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),
                   json.dumps({"ask": {
                       "question": "你说的「赚大钱」按哪个数字判定？",
                       "suggest": "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2"}}),
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
    line("问了用户（一次一个问题）", len(asked) == 1)
    line("问的同时给了建议", bool(asked) and "我建议" in asked[0])
    line("建议跟着问题一起送到用户面前", bool(asked) and "我的建议" in asked[0])
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("最终交出的根过了闸门", "root" in r and r["root"]["accept"] ==
         "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("根的可测物理量被识别出来", bool(anchors(r["root"]["accept"])))

    print("=" * 80)
    print("A2. 光问不给建议 → 打回（用户只能说「你看着办」，这一轮就白聊）")
    llm = FakeLLM([json.dumps({"ask": "你要赚多少算赚到？"}),
                   json.dumps(root())])
    said = []
    r = intake(llm, "帮我赚大钱", ask=lambda q: "你说吧", on_say=said.append)
    print("  打回的理由: %s" % [s for s in said if "建议" in s])
    line("光问不给建议被打回", any("必须给出你的建议" in s for s in said))
    line("补上建议后能继续", "root" in r)

    print("=" * 80)
    print("B. 判断不该开工 → 正式的 blocked 结论")
    llm = FakeLLM([json.dumps({"blocked": {
        "verdict": "阻塞", "text": "开户入金需要本人到柜台，工具里没有这个能力",
        "evidence": ["需要人到场"]}})])
    r = intake(llm, "帮我开个A股账户并打钱进去", ask=lambda q: "")
    print("  %s" % r["blocked"])
    line("交的是 blocked，不是编一个假目标", "blocked" in r and "root" not in r)
    line("判定和原因都在", r["blocked"]["verdict"] == "阻塞"
         and "柜台" in r["blocked"]["text"])

    print("=" * 80)
    print("C. 一直乱说 → 重复 ≥5 次就收手")
    llm = FakeLLM(["我看不懂你在说什么"] * 6)
    r = intake(llm, "随便", ask=lambda q: "")
    print("  %s" % r["blocked"]["text"])
    line("收手并说清是同一份错重复了", "blocked" in r and "5 次" in r["blocked"]["text"])
    line("第 5 次就收手了（没用到第 6 条回复）",
         len(llm.said) == 5 and len(llm.replies) == 1, "模型被调了 %d 次" % len(llm.said))

    print("=" * 80)
    print("D. 同一个问题反复问 → 也会收手（答不上来 = 现在不成立）")
    llm = FakeLLM([json.dumps({"ask": {"question": "赚大钱是多少钱？",
                                      "suggest": "我建议写成：账户权益 >= 100 万"}})] * 6)
    r = intake(llm, "帮我赚大钱", ask=lambda q: "不知道")
    print("  %s" % r["blocked"]["text"])
    line("问同一个问题也会收手", "blocked" in r and "同一个问题" in r["blocked"]["text"])

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
