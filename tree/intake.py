"""入口：把用户的一句话谈成根节点，**当场拿去跑，把结论带回来接着谈**。

它是这个程序**唯一的入口**（`main` 默认就是它，`-r` 恢复会话也回到这里）。和"引导 LLM"不是一回事：
那条路要模型猜用户的话**指哪个节点**（路由），这条路只做入口，产物必须过
和节点**同一台闸门**（`protocol/gate.py` 的 `clean_spec` + "验收标准必须有
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
是同一个分流，root 的格子就是节点写回孩子的那套 `ChildSpec`。
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

    root 的结构和节点给孩子的**完全一样** —— 你本来就是根节点的"上层下发"。
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
                 conc_range=got["conc_range"])
    await _run_tree(rnode, env, b["llm"])
    if b["say"]:
        b["say"]("（跑完了：%s）" % (rnode.verdict or "没有判定"))
    return _result(rnode)


async def _run_tree(rnode, env, llm, resume=None):
    """把一棵根树跑起来（或接着跑）。submit_root 和恢复共用这一处 ——
    run 的调用面只在这里变。resume：恢复包 {"state", "pending", "root"}，
    有就给（接着跑被打断的树），没有就新跑。"""
    await run(rnode, llm, env["trace"], registry=env.get("registry"),
              budget=env.get("budget"), workers=env.get("workers", 6),
              on_beat=env.get("on_beat"), beat=env.get("beat", 60),
              on_event=env.get("on_event"),
              on_delta=env.get("on_delta"), on_reasoning=env.get("on_reasoning"),
              resume=resume)


def _chat(env, kind, payload):
    """把 intake 对话的一条消息落进会话记录（trace 的 chat_* 事件）。

    恢复时对话原样回放：用户说的、模型回的（含交形式的工具调用）、
    工具回填的，一条不丢 —— 会话重启后模型还记着谈过什么。"""
    tr = env.get("trace")
    if tr is not None:
        tr.add(None, kind, payload)


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


def _root_spec(root):
    """根节点 → ChildSpec 形状（给恢复时补的交形式用）。"""
    return {"name": root.name, "detail": root.detail, "notes": root.notes,
            "accept": root.accept, "kind": root.kind,
            "conc_range": root.conc_range}


def _tool_text(res):
    """submit_root 的返回（str）从 ToolResult 里取出来。不是文本就炸（§2）。"""
    for c in getattr(res, "content", None) or []:
        if getattr(c, "type", "") == "text":
            return c.text
    raise TypeError("submit_root 的结果必须是文本（拿到 %r）" % res)


async def intake(llm, msg, ask, env, on_say=None, on_delta=None, on_reasoning=None,
                 msgs=None, resume_tree=None):
    """和用户谈，谈到形式就跑，跑完把结论带回来接着谈。**只在用户中止时停。**

    ask(text)          -> 用户回答的 coroutine（真跑时是终端上那次读，测试里换成
                          脚本）。拿到的是模型那一段话的**原文**，代码不改写它。
                          返回 coroutine 是因为读在真终端上要等 I/O，不能把
                          事件循环按住（那期间调度器可能正跑着）。
    env                -> 运行现场（`trace`/`budget`/`workers`/`registry`），
                          `main` 传进来；入口据此跑树。
    on_say(text)       -> 可选的**旁白**回调：打回理由、"接到任务/跑完了"走这里。
                          模型说的话走 ask 通道 —— 两条通道分开，
                          终端才不会把同一句话显示两遍。
    on_delta(text)     -> 可选的**吐字**回调：模型正在说的话一小口一小口送到这里。
                          交形式那一路不经过它（那是给闸门的，不是给人看的）。
    on_reasoning(text) -> 可选的**思考**回调：模型的 `reasoning_content` 走它。

    msgs                -> 可选的**恢复**对话（`session.load` 回放出来的）：
                          非空时不再以 msg 开局，而是从这份对话继续谈。
    resume_tree         -> 可选的恢复包（`session.load` 的 in_flight）：会话被打断
                          在"交形式 → 跑树"中间时，先把那棵树接着跑完、结论回填，
                          再接着谈。

    env["on_event"](node) 可选：节点**出生 / 出结论**各调一次，给实时展示用
    （终端据此重画任务树）。入口不解释它，只把它转给 `run()`。

    用户中止（不再输入）由 ask 那边抛 EOFError/KeyboardInterrupt 出来，
    这里不拦 —— 中止不是结论。
    """
    def say(t):
        if on_say:
            on_say(t)

    _intake_binding.set({"env": env, "llm": llm, "say": say})
    if msgs is None:
        msgs = [{"role": "system", "content": INTAKE_SYS},
                {"role": "user", "content": msg}]
        _chat(env, "chat_user", {"text": msg})
    else:
        msgs = [{"role": "system", "content": INTAKE_SYS}] + \
               [m for m in msgs if m["role"] != "system"]
    submit = await openai_spec("submit_root")

    # 恢复：有一棵没跑完的树 → 先把它接着跑完，结论回填，再接着谈。
    # 回填的位置有两种：
    #  · 新格式会话：对话最后一条是未回填的 submit_root，结论回填到那条；
    #  · 迁移来的旧会话：没有对话、没有悬空的交形式（msgs 开头就是种子），
    #    把这次续跑补成一条 assistant 交形式 + 结论 —— 还原"模型提交了这棵树"
    #    这件事，结论才有合法位置，模型才知道跑出了什么。
    if resume_tree is not None:
        root = resume_tree["root"]
        if env.get("on_event") and root.status == "running":
            env["on_event"](root)                     # 让终端把树画起来
        say("（继续跑没跑完的任务树…）")
        await _run_tree(root, env, llm, resume={
            "state": resume_tree["state"],
            "pending": resume_tree["pending"],
            "root": root})
        res = _result(root)
        say("（跑完了：%s）" % (root.verdict or "没有判定"))
        if msgs and msgs[-1].get("tool_calls") \
                and msgs[-1]["tool_calls"][0]["function"]["name"] == "submit_root":
            wire = msgs[-1]["tool_calls"][0]
        else:
            wire = [{"id": "resume_root", "type": "function",
                     "function": {"name": "submit_root",
                                  "arguments": json.dumps(
                                      _root_spec(root), ensure_ascii=False)}}]
            msgs.append({"role": "assistant", "content": "",
                         "tool_calls": wire})
            _chat(env, "chat_model", {"text": "", "tool_calls": wire})
            wire = wire[0]
        msgs.append({"role": "tool", "tool_call_id": wire["id"],
                     "content": res})
        _chat(env, "chat_tool", {"tool_call_id": wire["id"],
                                 "content": res})
    elif msgs and msgs[-1].get("tool_calls"):
        # 边角：对话末尾挂着 submit_root，但没有 in_flight 树 —— 退出点在
        # "交形式落盘 → 跑树"之间（树从没开始），或"跑完 → 结论回填"之间。
        # 重跑一遍保对话合法；后者会重复跑一棵已完工的树（窗口以纳秒计，
        # 重复比把对话弄坏强）。
        wire = msgs[-1]["tool_calls"][0]
        if wire["function"]["name"] == "submit_root":
            try:
                tool = await mcp.get_tool("submit_root")
                res = await tool.run(json.loads(wire["function"]["arguments"]))
                result = _tool_text(res)
            except ToolValidationError as e:
                result = "这样不行：" + str(e) + " 改一次再给。"
            msgs.append({"role": "tool", "tool_call_id": wire["id"],
                         "content": result})
            _chat(env, "chat_tool", {"tool_call_id": wire["id"],
                                     "content": result})

    while True:
        rmsg = await llm.chat(msgs, temperature=0.3, on_delta=on_delta,
                              on_reasoning=on_reasoning, tools=[submit])
        if not rmsg.tool_calls:
            # 在说话：原样送到用户面前，代码不改写它、不往里添字。
            # 这里**不过 norm()** —— 那是形式字段的规范化（会压掉换行），
            # 而这是一段说给人听的话，分行是它意思的一部分。
            a = await ask(str(rmsg.text or "").strip())
            msgs.append({"role": "assistant", "content": rmsg.text})
            _chat(env, "chat_model", {"text": rmsg.text, "tool_calls": None})
            msgs.append({"role": "user", "content": str(a)})
            _chat(env, "chat_user", {"text": str(a)})
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
        _chat(env, "chat_model", {"text": rmsg.text, "tool_calls": wire})
        for tc, w in zip(rmsg.tool_calls, wire):
            try:
                res = await tool.run(tc.arguments)
                result = _tool_text(res)
            except ToolValidationError as e:
                # schema 拒的参数（缺必填 / 类型错）：把原因摆出来让它自己改
                result = "这样不行：" + str(e) + " 改一次再给。"
            msgs.append({"role": "tool", "tool_call_id": w["id"],
                         "content": result})
            _chat(env, "chat_tool", {"tool_call_id": w["id"], "content": result})
