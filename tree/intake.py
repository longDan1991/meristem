"""入口：把用户的一句话谈成根节点，**当场拿去跑，把结论带回来接着谈**。

它是这个程序**唯一的入口**（`main --intake`）。和"引导 LLM"不是一回事：
那条路要模型猜用户的话**指哪个节点**（路由），这条路只做入口，产物必须过
和分配节点**同一台闸门**（`protocol/gate.py` 的 `clean_spec` + "验收标准必须有
可测物理量"），所以它不可能偷偷塞进树检查不了的东西。

它自己没有手（没有 bash / read / write）。**手在树上**：谈成一个能过闸门的
`root`，就 `run()` 它，把结论带回来接着谈。纪律：

  ① **交形式 ≠ 退场。** 每交一个 `root` 就跑一次、结论喂回，然后再次调模型。
     入口永不退场 —— 谈和跑交替进行，直到用户自己在终端上中止。
     所以没有"最终根"与"附加任务"之分：**每个 root 都是任务**。
     行不行不是聊出来的判断，而是树跑出来的事实（§2.7）。
  ② 用不了的东西当场打回，并把**为什么**说给它听，让它自己改 ——
     和树里同一个规矩：摆事实，不用计数器逼停。

**通道与节点同构**：模型要么说话（content，流式送给用户），要么调工具
`submit_root(root=...)` 交形式 —— 和节点层"调工具 = 动作、回文本 = 判断"
是同一个分流，root 的格子就是分配节点写回孩子的那套 `ChildSpec`。
所以这里不再有"从文本里猜 JSON 是话还是形式"的识别规则
（旧 `_Spoken` / `root_in` 就是为那个猜法写的，现在删了）。
它是在和真人说话，不是在填表 —— 代码不认识"回合数"，也不规定"一次只能问一个"。
"""

import contextvars
import json

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from .protocol.fields import Node
from .protocol.gate import validate_root
from .protocol.tool_specs import ChildSpec, mcp, openai_spec
from .prompts import INTAKE_SYS
from .runtime.scheduler import run

# submit_root 的运行时接线：intake() 开头写入 {"env", "llm", "say"}，
# 工具函数用 Depends 注入 —— 和 turn.py 的 _step_binding 同一个模式。
_intake_binding: contextvars.ContextVar = contextvars.ContextVar(
    "intake_binding", default=None)


def get_intake_binding():
    return _intake_binding.get()


@mcp.tool
async def submit_root(root: ChildSpec, _b=Depends(get_intake_binding)) -> str:
    """把谈成的任务交出去当场跑。返回跑完的结论（作为工具结果回填给对话）。

    root 的结构和分配节点给孩子的**完全一样** —— 你本来就是根节点的"上层下发"。
    除 notes / gate 外全部必填；accept 必须带上可测物理量（日期、两位以上数字、
    标识符），否则会被当场退回。
    """
    b = _b
    got, why = validate_root(root.model_dump())
    if got is None:
        if b["say"]:
            b["say"]("（入口交的东西用不了：%s）" % why)
        return "这样不行：" + why + " 改一次再给。"
    if b["say"]:
        b["say"]("（接到任务：%s）" % got["name"])
    env = b["env"]
    rnode = Node(name=got["name"], detail=got["detail"], notes=got["notes"],
                 accept=got["accept"], kind=got["kind"],
                 keywords=got["keywords"], conc_range=got["conc_range"])
    await run(rnode, b["llm"], env["trace"], registry=env.get("registry"),
              budget=env.get("budget"), workers=env.get("workers", 6),
              caps=env.get("caps"), index=env.get("index"),
              on_beat=env.get("on_beat"), beat=env.get("beat", 60))
    if b["say"]:
        b["say"]("（跑完了：%s）" % (rnode.verdict or "没有判定"))
    return _result(rnode)


def _result(root):
    """跑完的结论，写成一条能回填给入口的外部观测。

    用词说清楚"这是系统观测、不是用户说的话" —— 模型的对话里
    tool 那条通道会同时装"用户的话"和"世界的回话"，不加标记它会混。
    """
    lines = ["任务执行结果（系统观测，不是用户说的话）:",
             "任务: %s" % root.name,
             "判定: %s" % (root.verdict or "（没有判定）"),
             "结论: %s" % (root.conclusion or "（没有结论）")]
    if root.evidence:
        lines.append("证据: " + "；".join(str(x) for x in root.evidence))
    if root.external:
        lines.append("外部需求: " + "、".join(str(x) for x in root.external))
    return "\n".join(lines)


def _tool_text(res):
    """submit_root 的返回（str）从 ToolResult 里取出来。不是文本就炸（§2）。"""
    for c in getattr(res, "content", None) or []:
        if getattr(c, "type", "") == "text":
            return c.text
    raise TypeError("submit_root 的结果必须是文本（拿到 %r）" % res)


async def intake(llm, msg, ask, env, on_say=None, on_delta=None, on_reasoning=None):
    """和用户谈，谈到形式就跑，跑完把结论带回来接着谈。**只在用户中止时停。**

    ask(text)          -> 用户的回答（真跑时就是 input()，测试里换成脚本）。
                          拿到的是模型那一段话的**原文**，代码不改写它。
    env                -> 运行现场（`trace`/`caps`/`index`/`budget`/`workers`/
                          `registry`），`main` 传进来；入口据此跑树。
    on_say(text)       -> 可选的**旁白**回调：打回理由、"接到任务/跑完了"走这里。
                          模型说的话走 ask 通道 —— 两条通道分开，
                          终端才不会把同一句话显示两遍。
    on_delta(text)     -> 可选的**吐字**回调：模型正在说的话一小口一小口送到这里。
                          交形式那一路不经过它（那是给闸门的，不是给人看的）。
    on_reasoning(text) -> 可选的**思考**回调：模型的 `reasoning_content` 走它。

    用户中止（不再输入）由 ask 那边抛 EOFError/KeyboardInterrupt 出来，
    这里不拦 —— 中止不是结论。
    """
    def say(t):
        if on_say:
            on_say(t)

    _intake_binding.set({"env": env, "llm": llm, "say": say})
    msgs = [{"role": "system", "content": INTAKE_SYS},
            {"role": "user", "content": msg}]
    submit = await openai_spec("submit_root")

    while True:
        rmsg = await llm.chat(msgs, temperature=0.3, on_delta=on_delta,
                              on_reasoning=on_reasoning, tools=[submit])
        if not rmsg.tool_calls:
            # 在说话：原样送到用户面前，代码不改写它、不往里添字。
            # 这里**不过 norm()** —— 那是形式字段的规范化（会压掉换行），
            # 而这是一段说给人听的话，分行是它意思的一部分。
            a = ask(str(rmsg.text or "").strip())
            msgs.append({"role": "assistant", "content": rmsg.text})
            msgs.append({"role": "user", "content": str(a)})
            continue

        # 交了形式 → 逐个跑（每个 root 都是任务），结论作为工具结果回填。
        # assistant 消息要带上工具调用的线格式（多轮对话历史必须合法），
        # 每个调用跟一条 tool 结果 —— 协议要求一一对应。
        tool = await mcp.get_tool("submit_root")
        wire = [{"id": tc.id or "call_%d" % i, "type": "function",
                 "function": {"name": tc.name,
                              "arguments": json.dumps(tc.arguments,
                                                      ensure_ascii=False)}}
                for i, tc in enumerate(rmsg.tool_calls)]
        msgs.append({"role": "assistant", "content": rmsg.text,
                     "tool_calls": wire})
        for tc, w in zip(rmsg.tool_calls, wire):
            try:
                res = await tool.run(tc.arguments)
                result = _tool_text(res)
            except ToolValidationError as e:
                # schema 拒的参数（缺必填 / 类型错）：把原因摆出来让它自己改
                result = "这样不行：" + str(e) + " 改一次再给。"
            msgs.append({"role": "tool", "tool_call_id": w["id"],
                         "content": result})
