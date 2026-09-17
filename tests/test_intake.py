#!/usr/bin/env python3
"""入口的定向测试。零成本、确定性（脚本化模型 + 脚本化用户）。

入口只被用一次：把用户的一句话谈成**根节点的形式化结构**，然后退场。
它没有手（没有 bash/read/write），产物必须过和分配节点同一台闸门。

**对话的形式不归代码管** —— 代码不认识回合数，也不规定"一次只能问一个"、
"提问必须带建议"。它只认一条：**只有带 `root` 键的 JSON 算形式，其余都是话。**

  A. 谈定：说话 → 答 → 交出合规的根（话原样送到用户面前）
  B. 形式不合规 → 当场打回并说清为什么；改一次就能过闸门
  C. 只认 root：多行的话、带 JSON 但不是 root 的、甚至解析不出来的，都当话送出去
  D. 没有回合数 / 重复次数的限制（计数器删了就不许回来）
  E. 闸门：缺字段 / 没有可测物理量，都当场说不，并给得出理由
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.intake import intake, root_in, validate_root     # noqa: E402
from tree.run import anchors                              # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class FakeLLM:
    """按脚本回话的入口模型：脚本里一串字符串，就是它的每次输出。"""

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
    print("A. 谈定：说话 → 答 → 交出合规的根")
    talk = ("你说的「赚大钱」按哪个数字判定？\n"
            "我建议写成：账户权益在 2026-12-31 收盘 >= 本金 x 2")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")), talk, json.dumps(root())])
    asked = []

    def ask(t):
        asked.append(t)
        return "2026-12-31 收盘前"

    said = []
    r = intake(llm, "帮我做个能赚大钱的A股量化系统（我没说怎么算赚到）",
               ask=ask, on_say=said.append)
    print("  入口说过: %r" % asked)
    print("  交出来的根: %s" % json.dumps(r.get("root", r), ensure_ascii=False)[:100])
    line("打了回去，并说了为什么", any("可测物理量" in s for s in said))
    line("算了话，也问了用户", len(asked) == 1)
    line("话原样送到用户面前（不添字、不包装、不压行）",
         bool(asked) and asked[0] == talk)
    line("用户的话进了下一轮上下文", any("2026-12-31 收盘前" in s for s in llm.said))
    line("最终交出的根过了闸门", "root" in r and r["root"]["accept"] ==
         "账户权益在2026-12-31收盘 >= 本金 x 2")
    line("根的可测物理量被识别出来", bool(anchors(r["root"]["accept"])))

    print("=" * 80)
    print("B. 形式不合规 → 打回；改一次就过")
    llm = FakeLLM([json.dumps(root(accept="系统做好了")),   # 没有可测物理量
                   json.dumps(root())])
    said = []
    r = intake(llm, "帮我赚大钱", ask=lambda t: "随便", on_say=said.append)
    print("  打回理由: %s" % [x for x in said if "用不了" in x])
    line("打回时把原因摆出来了", any("用不了" in x and "可测物理量" in x for x in said))
    line("改一次后过闸门", "root" in r)
    line("打回走旁白，不占用户的话轮", not any("用不了" in x for x in
                                              [str(x) for x in llm.said[:1]]))

    print("=" * 80)
    print("C. 只认 root：其余一律当话")
    # ① 多行的话
    multi = "我先复述一遍你的意思：\n① 做视频\n② 目标是赚钱\n对吗？"
    llm = FakeLLM([multi, json.dumps(root())])
    asked = []
    intake(llm, "帮我做视频赚钱", ask=lambda t: (asked.append(t), "对")[1])
    line("① 多行的话原样送出去", asked and asked[0] == multi)

    # ② 带 JSON 但不是 root（比如模型顺手写了个 ask）
    weird = json.dumps({"ask": {"content": "你要做什么？"}}, ensure_ascii=False)
    llm = FakeLLM([weird, json.dumps(root())])
    asked = []
    r = intake(llm, "帮我赚大钱", ask=lambda t: (asked.append(t), "做系统")[1])
    line("② 没有 root 键 → 也当话（代码不认第二种形式）",
         asked and asked[0] == weird)
    line("② 照样谈成了", "root" in r)

    # ③ 完全不是 JSON
    llm = FakeLLM(["你好，我们聊聊这件事。", json.dumps(root())])
    asked = []
    intake(llm, "帮我赚大钱", ask=lambda t: (asked.append(t), "好")[1])
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
    asked = []
    r = intake(llm, "帮我赚大钱", ask=lambda t: (asked.append(t), "抖音")[1])
    print("  同一句话说了 %d 次，仍然继续" % len(asked))
    line("说 8 次也没被计数器逼停", len(asked) == 8, "说了 %d 次" % len(asked))
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
