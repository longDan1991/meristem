"""入口：把用户的一句话谈成**根节点的形式化结构**，然后退场。

只用一次，之后不留记忆 —— 因为结论已经落成根节点的形式字段了，
而**树就是记忆**（DESIGN §2.1、§2.8）。

它和"引导 LLM"不是一回事：那条路要模型猜用户的话**指哪个节点**（路由），
这条路只做入口，产物必须过和分配节点**同一台闸门**（`_clean_spec` +
"验收标准必须有可测物理量"），所以它不可能偷偷塞进树检查不了的东西。

它也没有手：没有 bash / read / write。只谈、只交形式。纪律只有两条：

  ① 出口只有一个：能过闸门的 `root`。**没有"这个不该开工"这一条** ——
     行不行不是聊出来的判断，而是树跑出来的事实（根节点自己会出 `阻塞` 结论）。
     用户不再输入，就是中止（`ask` 那边抛出来），也不是一条结论。
  ② 用不了的东西当场打回，并把**为什么**说给它听，让它自己改 ——
     和树里同一个规矩：摆事实，不用计数器逼停。

**对话的形式不归代码管。** 问几个问题、怎么问、要不要先复述一遍，
都是模型的事 —— 它是在和真人说话，不是在填表。代码不认识"回合数"，
也不规定"一次只能问一个"，只在出口校验产物。
"""

from .llm import parse_json
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
    """和用户把预期谈定。**只有一个出口：`{"root": {...}}`。**

    ask(content)   -> 用户的回答（真跑时就是 input()，测试里换成脚本）。
                      拿到的是模型 `ask.content` 的**原文**，代码不改写它。
    on_say(text)   -> 可选的**旁白**回调：只有打回理由走这里。
                      交流内容走 ask 通道 —— 两条通道分开，
                      终端才不会把同一句话显示两遍。

    用户中止（不再输入）由 ask 那边抛 EOFError/KeyboardInterrupt 出来，
    这里不拦 —— 中止不是结论。
    """
    def say(t):
        if on_say:
            on_say(t)

    msgs = [{"role": "system", "content": INTAKE_SYS},
            {"role": "user", "content": msg}]

    while True:
        text = llm.chat(msgs, temperature=0.3)

        def again(why):
            """交回来的东西用不了：把原因摆出来让它自己改（不是计数器）。"""
            say("（入口交的东西用不了：%s）" % why)
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user",
                         "content": "这样不行：" + why + " 改一次再给。"})

        try:
            d = parse_json(text)
        except Exception as e:
            again("输出必须是一个 JSON 对象（%r）" % e)
            continue

        # 继续交流。`content` 原样送到用户面前 —— 代码不改写它、不往里添字：
        # 说什么、带不带建议、一次说几件事，都是模型的事。
        # 这里**不过 norm()**：那是形式字段的规范化（会压掉换行），
        # 而这是一段说给人听的话，分行是它意思的一部分。
        a = d.get("ask")
        if a is not None:
            raw = a.get("content") if isinstance(a, dict) else a
            a2 = ask(str(raw or "").strip())
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user", "content": str(a2)})
            continue

        if isinstance(d.get("root"), dict):
            spec, why = validate_root(d["root"])
            if spec is not None:
                return {"root": spec}
        else:
            why = "只能给 ask 或 root 两个键之一"
        again(why)
