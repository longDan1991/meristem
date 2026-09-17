"""入口：把用户的一句话变成**根节点的形式化结构**，然后退场。

只用一次，之后不留记忆 —— 因为结论已经落成根节点的形式字段了，
而**树就是记忆**（DESIGN §2.1、§2.8）。

它和"引导 LLM"不是一回事：那条路要模型猜用户的话**指哪个节点**（路由），
这条路只做入口，产物必须过和分配节点**同一台闸门**（`_clean_spec` +
"验收标准必须有可测物理量"），所以它不可能偷偷塞进树检查不了的东西。

它也没有手：没有 bash / read / write。只问、只交形式。四条纪律：
  ① 只能产出两种东西：能过闸门的 `root`，或一条正式的 `blocked` 结论。
     问用户那一轮要**同时给建议**（`{"ask":{"question","suggest"}}`）——
     用户说"你看着办"是常态，光问不给建议，这一轮就白聊。
  ② 不合规的东西直接打回，并把**为什么**说给它听。
  ③ 同一份用不了的东西、或者同一个问题，重复 ≥5 次就收手
     （和树里同一个规矩，见 DESIGN §2.4）。
"""

from .llm import parse_json
from .node import norm
from .prompts import INTAKE_SYS
from .run import _clean_spec, anchors


def validate_root(spec):
    """根节点的闸门 = 分配节点给孩子的校验，加一条根专属的：
    验收标准里必须有一个可测物理量。没有它，这棵树判不了自己做没做完。"""
    out, why = _clean_spec(spec or {})
    if why:
        return None, why
    if not anchors(out["accept"]):
        return None, ("验收标准里必须有一个可测物理量（日期 / 两位以上数字 / "
                      "标识符如 hello.txt），否则这棵树判不了自己做没做完")
    return out, None


def intake(llm, msg, ask, on_say=None):
    """和用户把预期谈定。返回 {"root": {...}} 或 {"blocked": {...}}。

    ask(question) -> 用户的回答（真跑时就是 input()，测试里换成脚本）。
    on_say(text)   -> 可选的旁白回调（把入口说的话打出来）。
    """
    def say(t):
        if on_say:
            on_say(t)

    msgs = [{"role": "system", "content": INTAKE_SYS},
            {"role": "user", "content": msg}]
    asked, bad = {}, {}

    for _ in range(200):                  # 兜底，防止实现出错时真的转不出去
        text = llm.chat(msgs, temperature=0.3)
        d, why = None, None
        try:
            d = parse_json(text)
        except Exception as e:
            why = "输出必须是一个 JSON 对象（%r）" % e

        if d is not None:
            a = d.get("ask")
            if a is not None:
                q, sug = "", ""
                if isinstance(a, dict):
                    q, sug = norm(a.get("question")), norm(a.get("suggest"))
                    if not q or not sug:
                        why = ("ask 里的 question 和 suggest 都必须有 —— "
                               "问的同时要给一个能直接用的建议")
                else:
                    # 光问不给建议，用户只能说"你看着办"，这一轮就白聊
                    why = ('ask 要写成 {"ask":{"question":"...","suggest":"..."}}'
                           " —— 问的同时必须给出你的建议")
                if not why:
                    asked[q] = asked.get(q, 0) + 1
                    n = asked[q]
                    say("问：%s" % q)
                    say("我建议：%s" % sug)
                    if n >= 3:
                        say("（这个问题你已经问过 %d 次了 —— 用户答不上来，"
                            "说明这件事现在还不成立，该给 blocked 了。）" % n)
                    if n >= 5:
                        return {"blocked": {
                            "verdict": "阻塞",
                            "text": "同一个问题问了 %d 次，用户答不上来：%s" % (n, q),
                            "evidence": []}}
                    # 建议要跟着问题一起送到用户面前
                    a2 = ask("%s\n（我的建议：%s）" % (q, sug))
                    msgs.append({"role": "assistant", "content": text})
                    msgs.append({"role": "user", "content": str(a2)})
                    continue

            # `why is None` 这个条件不能少：上面 ask 那条分支已经判过
            # "用不了"了，这一链再走一遍会把理由覆盖成"只能给三个键之一"。
            if why is None and isinstance(d.get("root"), dict):
                spec, why = validate_root(d["root"])
                if spec is not None:
                    return {"root": spec}

            elif why is None and isinstance(d.get("blocked"), dict):
                b = d["blocked"]
                return {"blocked": {"verdict": norm(b.get("verdict")) or "阻塞",
                                    "text": norm(b.get("text")),
                                    "evidence": b.get("evidence") or []}}
            elif why is None:
                why = "只能给 ask / root / blocked 三个键之一"
        # 交回来的东西用不了：说清原因让它改；同一份错重复 ≥5 次就收手
        bad[why] = bad.get(why, 0) + 1
        say("（入口交的东西用不了：%s）" % why)
        if bad[why] >= 5:
            return {"blocked": {
                "verdict": "阻塞",
                "text": "入口连续 %d 次交不出能用的东西：%s" % (bad[why], why),
                "evidence": []}}
        msgs.append({"role": "assistant", "content": text})
        msgs.append({"role": "user", "content": "这样不行：" + why + " 改一次再给。"})

    return {"blocked": {"verdict": "阻塞", "text": "入口没有收敛", "evidence": []}}
