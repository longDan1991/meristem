"""消息循环：把"一轮消息往返"转起来，在关键位置发事件、调钩子。

生命周期只在这里定义，只有这一个地方：

    loop_start            ← 调用方发（节点出生 / 会话开始）
      └─ (turn_start → message_* → tool_* → turn_end)*
            └─ 每轮产物 Outcome：continue / suspend / stop
    loop_end              ← 调用方发（节点完工 / 会话结束）

**骨架由循环自己走**（调用方不再写这些）：
  · 问模型、开流式、发 message_* 事件；
  · 写账本：assistant 入账、工具结果按 id 配回去（`Transcript`）；
  · 跑工具：查 `tools` 里的函数逐个调，发 tool_* 事件。

**调用方只填三处语义**（`Hooks`）：
  · before_chat —— 问模型之前：拼好要发的消息（也就带上了压缩），或直接给 Outcome 停；
  · after_chat  —— 模型回来之后、跑工具之前：看回复决定要不要跑工具（给 Outcome 就跳过工具）；
  · after_tool  —— 工具跑完之后：看结果给下一拍（Outcome）。

**事件出口归自己管**（第 4 点）：`Loop` **内建**自己的 `EventSink` 并拼好带 scope
的 `emit`，消费方经 `Loop.subscribe` 订阅循环定义的那几个 `EventType`，不自己拼闭包。
`EventSink`（分发机制）在 `events.py`；词汇（`EventType`）在这里，分家不变。

一轮是**原子**的：本轮消息先进 staging，三个钩子都成功后并入真账本 ——
中断（如用户 Ctrl-D）的那一步作废，不落半笔（和会话恢复"在飞的那一步作废"同一语义）。
"""

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal

from ..events import EventSink

EventType = Literal[
    "loop_start", "loop_end",
    "turn_start", "turn_end",
    "message_start", "message_update", "message_end",
    "tool_start", "tool_update", "tool_end",
]


@dataclass
class Outcome:
    """一轮的产物。循环只认 kind，不解释 payload / reason：
      continue → 下一回合；
      suspend  → 把控制权交回调用方（调度器等孩子），之后续跑；
      stop     → 循环终止。
    """
    kind: Literal["continue", "suspend", "stop"]
    payload: Any = None
    reason: str = ""


@dataclass
class ToolResult:
    """一次工具调用的产物：循环用它写回对话，调用方用它决定下一拍。

      text    写回对话的 tool 结果（观测 / 打回理由）；
      effect  工具自己给的下一拍：continue / suspend / stop；
      payload suspend 的负载（分配节点的孩子 / 门槛信息）；
      reject  非空 = 这次没执行、是打回，after_tool 据此 balk。
    """
    text: str = ""
    effect: str = "continue"
    payload: Any = None
    reject: str = ""


def outcome_after_tools(results):
    """工具结果列表 → 下一拍：stop / suspend 优先，默认 continue。

    每个节点类型（叶子 / 分配 / 入口）的 after_tool 都只做这一件事 ——
    工具结果本身是事实，下一拍是循环的语义；两份各抄一遍就会漂。
    """
    for r in results:
        if r.effect == "stop":
            return Outcome("stop")
        if r.effect == "suspend":
            return Outcome("suspend", payload=r.payload)
    return Outcome("continue")


@dataclass(frozen=True)
class Hooks:
    """调用方注入的三处语义。骨架（问模型 / 跑工具 / 写对话 / 发事件）在循环里。"""
    before_chat: Callable[[dict], Awaitable[list | Outcome]]
    after_chat: Callable[[dict, Any], Awaitable[Outcome | None]]
    after_tool: Callable[[dict, Any, list], Awaitable[Outcome]]


class Transcript:
    """平铺对话账本：系统提示词 + 对话，assistant ↔ tool 结果一一配对。

    配对协议（wire 形状、缺 id 时怎么退、每个 tool_call 必须有一条 tool 回话）
    只在这里实现一次。读用 `wire()`（发给模型）/ `to_list()`（对话本身）；
    写一律走方法，不许从外面 `.msgs.append`。

    `on_append` 可选：每入账一条就回调一次（入口用它把 chat_* 落进 trace；
    节点不用 —— 节点的持久化是 state 检查点）。
    """

    def __init__(self, system=None, msgs=None, on_append=None, offset=0):
        self.system = system if system is not None else []   # 提示词（system + 基础 user）
        self.msgs = msgs if msgs is not None else []         # 对话账本
        self._on_append = on_append
        # 暂存账本用：id 回退接在真账本后面数，否则每轮都从 call_0 起（会撞号）
        self._offset = offset
        # 就地改写标记：add_user_merged 并进已入账的 user 时置位，检查点靠它
        # 决定增量不可用（增量会丢/错已写过的消息，见 checkpoint）
        self._last_mutated = False

    def _append(self, msg):
        self.msgs.append(msg)
        if self._on_append is not None:
            self._on_append(msg)

    def wire(self):
        """发给模型的消息 = 系统提示词 + 对话账本。"""
        return self.system + self.msgs

    def add_assistant(self, text, tool_calls):
        """assistant 入账；返回 (落账的 id 列表, wire 或 None)。id 回退按对话长度算。"""
        ids = [tc.id or "call_%d" % (self._offset + len(self.msgs) + i)
               for i, tc in enumerate(tool_calls)]
        wire = [{"id": i, "type": "function",
                 "function": {"name": tc.name,
                              "arguments": json.dumps(tc.arguments,
                                                      ensure_ascii=False)}}
                for i, tc in zip(ids, tool_calls)]
        msg = {"role": "assistant", "content": text or None}
        if wire:
            msg["tool_calls"] = wire
        self._append(msg)
        return ids, (wire or None)

    def add_tool_result(self, tool_call_id, content):
        self._append({"role": "tool", "tool_call_id": tool_call_id,
                      "content": content})

    def add_user(self, text):
        self._append({"role": "user", "content": text})

    def add_feedback(self, text):
        """把一条打回理由写回对话：上一条是带工具调用的 assistant 就配成 tool
        回话（每个 id 一条），否则写 user 消息（对话不能断在两个 assistant 之间）。"""
        last = self.msgs[-1] if self.msgs else None
        if last and last.get("role") == "assistant" and last.get("tool_calls"):
            for w in last["tool_calls"]:
                self.add_tool_result(w["id"], text)
        else:
            self.add_user(text)

    def add_user_merged(self, text):
        """并到上一条 user 里（连着注多条世界回话时，provider 不接受两条 user）。
        就地改写会置位 `_last_mutated` —— 检查点不再信任增量（见 checkpoint）。"""
        if self.msgs and self.msgs[-1].get("role") == "user":
            self.msgs[-1]["content"] = str(self.msgs[-1]["content"]) + "\n" + text
            self._last_mutated = True
        else:
            self.add_user(text)

    def merge(self, other):
        """把另一本账本的消息并进自己（合并本轮 staging —— 触发记录回调）。"""
        for m in other.msgs:
            self._append(m)

    def to_list(self):
        return self.msgs

    def checkpoint(self, base=0):
        """一笔状态检查点的消息负载（增量落盘，§11：不把整份历史每回合重写一遍）。

        优先只给 `base` 之后新增的消息（增量）；但期间**就地改写**过头消息
        （add_user_merged 并进已入账的 user）或 base==0（第一笔 / 恢复重开）
        时给全量。返回 (msgs, 是不是增量, 消息起点 base)。
        """
        if self._last_mutated or len(self.msgs) < base or base == 0:
            self._last_mutated = False
            return self.msgs, False, 0
        return self.msgs[base:], True, base


class Loop:
    """一条消息循环。自己管事件出口（内建 EventSink，subscribe 暴露），自己走一轮骨架。

    参数只给需要的那几个：llm、账本、喂给模型的工具声明（tools_spec）、
    模型回来要调用的函数（tools：名字 → async 函数 → ToolResult）、三处语义（hooks）。
    流式是常开的：`_chat` 总是带 on_delta / on_reasoning（不白开 SSE 的开关已删）。
    **不认识 scope**：每个 Loop 一个独立 sink，它发出的每个事件被谁订阅、
    代表哪个节点，由订阅那一刻决定（scheduler 订阅时打上 scope）——
    Loop 自己不需要知道自己的身份。
    """

    def __init__(self, llm, transcript, tools_spec, tools, hooks):
        self.llm = llm
        self.transcript = transcript
        self.tools_spec = tools_spec
        self.tools = tools
        self.hooks = hooks
        self._sink = EventSink()          # 机制内建：每个 Loop 自持一个出口
        self._emit = self._sink.emit      # 不带 scope：身份由订阅关系决定

    def subscribe(self, consumer):
        """外界订阅循环发的事实。consumer(type, payload) -> None。"""
        self._sink.subscribe(consumer)

    async def run(self, on_turn=None):
        """跑到 suspend 或 stop。on_turn(outcome) 每轮结束调一次（同步，给落检查点）。"""
        while True:
            out = await self._turn()
            if on_turn is not None:
                on_turn(out)
            if out.kind != "continue":
                return out

    async def _turn(self):
        self._emit("turn_start", {})
        prepared = await self.hooks.before_chat(self.transcript)
        if isinstance(prepared, Outcome):
            self._emit("turn_end", {"kind": prepared.kind,
                                    "reason": prepared.reason})
            return prepared
        assistant = await self._chat(prepared)

        # 本轮消息先进 staging：三个钩子都成功才并入真账本（中断的那一步作废）。
        staging = Transcript(offset=len(self.transcript.msgs))
        ids, _wire = staging.add_assistant(assistant.text, assistant.tool_calls)
        out = await self.hooks.after_chat(staging, assistant)
        if out is None:                      # after_chat 没叫停 → 跑工具
            results = []
            for tc, wid in zip(assistant.tool_calls, ids):
                self._emit("tool_start", {"name": tc.name})
                r = await self.tools[tc.name](tc.arguments)
                staging.add_tool_result(wid, r.text)
                results.append(r)
                self._emit("tool_end", {"name": tc.name, "error": bool(r.reject)})
            out = await self.hooks.after_tool(staging, assistant, results)
        self.transcript.merge(staging)
        self._emit("turn_end", {"kind": out.kind, "reason": out.reason})
        return out

    async def _chat(self, messages):
        """问模型：总是流式（on_delta / on_reasoning 各一条），发 message_* 事件。"""
        self._emit("message_start", {})
        msg = await self.llm.chat(
            messages, tools=self.tools_spec,
            on_delta=lambda t: self._emit(
                "message_update", {"kind": "content", "delta": t}),
            on_reasoning=lambda t: self._emit(
                "message_update", {"kind": "reasoning", "delta": t}))
        self._emit("message_end", {
            "text": msg.text,
            "tool_calls": [{"name": tc.name, "arguments": tc.arguments}
                           for tc in msg.tool_calls]})
        return msg
