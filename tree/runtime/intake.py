"""入口：会话的**根节点**（kind="intake"）—— 和其他节点没啥不同。

它不是另开的一条通道，就是树上的第一个节点：

  · 它是一棵带对话（`msgs`）的 Node —— 对话就是它的状态检查点（{node, msgs}），
    没有别的存档；
  · 它的孩子 = 谈成的任务树（`submit_root` 把任务挂成孩子）；
  · "该不该调 LLM"由共享谓词 `reconcile.actionable` 回答：最后一条不是模型
    自己说的（用户刚说话、或任务刚交回结论）才跑；
  · 它从不"出结论"（会话一直开到用户 Ctrl-D），所以没有 verdict。

自己**没有手**（没有 bash / read / write）—— 手在树上：谈成一个能过闸门的
任务（`validate_root` = `clean_spec` + "验收标准必须有可测物理量"），就
`submit_root` 把它挂成孩子、让调度器去跑；跑出的结论以 child_result 消息
回到本节点的对话里，模型据此接着谈。

`ask`（拿用户的话）由终端经 `run(..., ask=...)` 注入；`spawn_task`（挂任务）
由调度器注入 —— 入口节点只填三处语义（`intake_hooks`），不自己跑树。
"""

import contextvars

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ValidationError as ToolValidationError

from ..protocol.gate import validate_root
from ..protocol.tool_specs import ChildSpec, mcp, openai_spec
from .loop import Hooks, Outcome, ToolResult

# submit_root 的运行时接线：intake_tools 调用前写入 {"spawn_task", "say"}，
# 工具函数用 Depends 注入 —— 和 turn.py 的 _step_binding 同一个模式。
_intake_binding: contextvars.ContextVar = contextvars.ContextVar(
    "intake_binding", default=None)


def get_intake_binding():
    return _intake_binding.get()


@mcp.tool
async def submit_root(root: ChildSpec, _b=Depends(get_intake_binding)) -> dict:
    """把谈成的任务交出去当场跑。返回跑起来的任务名（作为工具结果回填给对话）。

    root 的结构和节点给孩子的**完全一样** —— 你本来就是任务树的"上层下发"。
    除 notes / gate 外全部必填；accept 必须带上可测物理量（日期、两位以上数字、
    标识符），否则会被当场退回。
    """
    b = _b
    got, why = validate_root(root.model_dump())
    if got is None:
        if b["say"]:
            b["say"]("（入口交的东西用不了：%s）" % why)
        return {"obs": "这样不行：" + why + " 改一次再给。"}
    if b["say"]:
        b["say"]("（接到任务：%s）" % got["name"])
    task = b["spawn_task"](got)
    return {"obs": "已启动任务「%s」（它跑完把结论交回来）。" % task.name,
            "kind": "suspend", "task": task.id}


def intake_hooks(nid, runtime):
    """入口节点的三处语义（和 turn.node_hooks 同构：问模型 / 看回复 / 看工具结果）。"""
    ask = runtime["ask"]

    async def before_chat(transcript):
        return transcript.wire()

    async def after_chat(transcript, assistant):
        if assistant.tool_calls:
            return None                     # 交形式 → 交给循环去跑 submit_root
        # 纯文本 → 送到用户面前（原样，不改写），把回答写回对话，接着谈
        a = await ask(str(assistant.text or "").strip())
        transcript.add_user(str(a))
        return Outcome("continue")

    async def after_tool(transcript, assistant, results):
        for r in results:
            if r.effect == "stop":
                return Outcome("stop")
            if r.effect == "suspend":
                return Outcome("suspend", payload=r.payload)
        return Outcome("continue")

    return Hooks(before_chat=before_chat, after_chat=after_chat,
                 after_tool=after_tool)


async def intake_spec(nid, runtime):
    """入口节点的工具声明：只有 submit_root。"""
    return [await openai_spec("submit_root")]


def intake_tools(nid, runtime):
    """入口节点的工具：submit_root → 校验 + 挂任务（不自己跑树）。"""
    async def call(args):
        _intake_binding.set({"spawn_task": runtime["spawn_task"],
                             "say": runtime.get("say")})
        tool = await mcp.get_tool("submit_root")
        try:
            res = await tool.run(args)
        except ToolValidationError as e:
            # schema 拒的参数（缺必填 / 类型错）：一条可见的事实，让模型改
            return ToolResult(text="这样不行：%s 改一次再给。" % e)
        d = res.structured_content
        if not isinstance(d, dict):
            raise TypeError("submit_root 必须返回 dict（拿到 %r）" % d)
        if d.get("kind") == "suspend":
            return ToolResult(text=d.get("obs") or "", effect="suspend",
                              payload={"task": d.get("task")})
        return ToolResult(text=d.get("obs") or "")

    return {"submit_root": call}
