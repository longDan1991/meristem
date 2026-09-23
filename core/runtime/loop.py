"""唯一的 Loop：一棵树的唯一控制流。

每轮扫活跃节点（msgs 非空且最后一条不是 assistant）发起 LLM，异步等结果（LLM / 工具 /
入口等用户）；结果回来就拼进该节点 msgs 或并行发工具。没有 per-node 任务，多个节点的
LLM 因此并发。

事件只发消费者真正读的三个：`loop_start` / `loop_end` / `message_update`，都带 `scope=节点 id`。
"""

import asyncio

from .. import config as cfg
from ..compression import compress_messages
from ..events import EventSink
from ..llm import ChatPool
from ..prompts import feedback, render_turn
from ..prompts.messages import base_user
from ..protocol.fields import INTAKE, LEAF
from tools import allowed_names, openai_tools
from tools.defs import run_tool
from .dialogue import pair
from .plan import actionable, which_of


class Loop:
    def __init__(self, store, llm, *, workers=cfg.WORKERS, subscribe=None, ask=None, say=None):
        self.store = store
        self.llm = llm
        self.ask = ask
        self.say = say
        self.pool = ChatPool(llm, workers)  # llm.chat 的并发上限（最贵的资源）
        self.sink = EventSink()
        if subscribe is not None:
            self.sink.subscribe(subscribe)
        self.tools = {}  # which -> OpenAI 工具声明（run 开始时建一次）
        self.active = set()  # 可能有下一个动作的节点
        self.pending = {}  # future -> nid（在飞的 LLM / 工具 / 入口等用户）
        self.busy = {}  # nid -> 在飞数（>0 就不再给这个节点发 LLM）
        self.started = set()  # 发过 loop_start、还没出结论的节点

    def emit(self, nid, type, payload=None):
        self.sink.emit(type, {"scope": nid, **(payload or {})})

    async def run(self):
        self.tools = await openai_tools()  # 建一次，避免并发首建
        self.active = set(self.store.registry)  # 自举：全节点入活跃集
        try:
            while True:
                self.active |= self.store.take_dirty()
                for nid in list(self.active):
                    self.active.discard(nid)
                    if nid in self.busy:
                        continue
                    if not actionable(self.store, nid):
                        continue
                    self._fire(nid, self._chat(nid))
                if self.pending:
                    done, _ = await asyncio.wait(
                        list(self.pending), return_when=asyncio.FIRST_COMPLETED
                    )
                    for fut in done:
                        nid = self.pending.pop(fut)
                        self.busy[nid] -= 1
                        if not self.busy[nid]:
                            del self.busy[nid]
                        exc = fut.exception()
                        if exc is not None:
                            await self._cancel()
                            raise exc
                        self.active.add(nid)
                        node = self.store.registry[nid]
                        if node.verdict and nid in self.started:
                            self.started.discard(nid)
                            self.emit(nid, "loop_end", {"node": node})
                elif not self.active:
                    break
        finally:
            await self._cancel()
            await self.pool.close()
        return self.store

    def _fire(self, nid, coro):
        fut = asyncio.ensure_future(coro)
        self.pending[fut] = nid
        self.busy[nid] = self.busy.get(nid, 0) + 1
        return fut

    async def _cancel(self):
        futs = list(self.pending)
        for fut in futs:
            fut.cancel()
        self.pending.clear()
        self.busy.clear()
        if futs:
            await asyncio.gather(*futs, return_exceptions=True)

    async def _chat(self, nid):
        store = self.store
        node = store.registry[nid]
        which = which_of(node)
        if nid not in self.started:
            self.started.add(nid)
            self.emit(nid, "loop_start", {"node": node})

        wire = await _build_wire(self, node, which)
        store.record(nid, "%s_in" % which, base_user(node))
        assistant = await self.pool.chat(
            wire,
            tools=self.tools[which],
            on_delta=lambda t: self.emit(nid, "message_update", {"kind": "content", "delta": t}),
            on_reasoning=lambda t: self.emit(
                nid, "message_update", {"kind": "reasoning", "delta": t}
            ),
        )
        _log_usage(self, nid, which, assistant.usage)
        store.record(
            nid,
            "%s_out" % which,
            {
                "text": assistant.text,
                "tool_calls": [
                    {"name": tc.name, "arguments": tc.arguments} for tc in assistant.tool_calls
                ],
            },
        )
        ids = store.append_assistant(nid, assistant.text, assistant.tool_calls)

        if which == INTAKE and not assistant.tool_calls:
            self._fire(nid, self._ask(nid, assistant.text))
            return
        if assistant.tool_calls:
            self._fire(nid, self._tools(nid, which, assistant.tool_calls, ids))

    async def _ask(self, nid, text):
        reply = await self.ask(str(text or "").strip())
        self.store.append_user(nid, str(reply))

    async def _tools(self, nid, which, tool_calls, ids):
        results = await asyncio.gather(
            *[_one_tool(self, nid, which, tc, wid) for tc, wid in zip(tool_calls, ids)],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, BaseException):
                raise r


async def run(store, llm, *, workers=cfg.WORKERS, subscribe=None, ask=None, say=None):
    """跑一场会话（一棵树），返回同一份 store；``workers`` = 同时在飞的 llm.chat 数。"""
    loop = Loop(store, llm, workers=workers, subscribe=subscribe, ask=ask, say=say)
    return await loop.run()


# ---------------------------------------------------------------- 内部
async def _build_wire(loop, node, which):
    """这次发给模型的消息：system + 配对规范化后的平铺对话（叶子再压缩）。"""
    store = loop.store
    nid = node.id
    msgs = store.dialogue(nid).to_list()
    wire = render_turn(which, node) + pair(msgs)
    if (
        which == LEAF
        and cfg.COMPRESS
        and any(m.get("role") == "tool" for m in msgs)
    ):
        result = await compress_messages(wire, getattr(loop.llm, "model", ""))
        wire = result.messages
        if result.tokens_saved > 0:
            store.record(
                nid,
                "wire_compressed",
                {
                    "before": result.tokens_before,
                    "after": result.tokens_after,
                    "saved": result.tokens_saved,
                    "transforms": result.transforms_applied,
                },
            )
    return wire


async def _one_tool(loop, nid, which, tc, call_id):
    """驱动一次工具调用；被拒 / 出错写一条 tool 回话，结构类成功不写。"""
    store = loop.store
    names = allowed_names(which)
    if tc.name not in names:
        store.append_tool(nid, call_id, feedback.unknown_tool(tc.name, names))
        return
    text = await run_tool(loop, nid, tc.name, tc.arguments)
    if text is not None:  # None = 结构类成功，不写回话
        store.append_tool(nid, call_id, text)


def _log_usage(loop, nid, phase, usage):
    """把一次调用的 token 账记进 trace；`usage` 随 Message 回来，不经过共享状态。"""
    if not usage:
        return
    loop.store.record(
        nid,
        "usage",
        {
            "phase": phase,
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "reasoning": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
            "cached": (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
            "total": usage.get("total_tokens", 0),
        },
    )
