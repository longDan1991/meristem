"""LLM 适配层：给 messages，返回 Message（文本 + 工具调用）。

底层是 `litellm`（任何 OpenAI 兼容端点），重试、超时、流式、usage 都是它的事。
给 `tools` 就走工具调用，给 `on_delta` 就走流式；`on_reasoning` 另开一条走模型的
`reasoning_content`，和回答分开，终端才能把思考画成灰的。

用量随回复走：`Message.usage` 就是这次调用的 token 账（没有收尾块时为 None）。
ChatPool 的 worker 是同一线程里的 asyncio task，线程本地装不下"每次调用各自的用量"，
所以用量跟结果对象一起回来，不经过任何共享槽。
"""

import asyncio
import json
import os
from dataclasses import dataclass, field

import litellm

from .runtime import deliver


@dataclass
class ToolCall:
    """一次工具调用：id（回写历史用）+ 名字 + 已解析成 dict 的参数。"""
    id: str = ""
    name: str = ""
    arguments: dict = field(default_factory=dict)


@dataclass
class Message:
    """模型一次回复：要么有文本、要么有工具调用（或两者）。

    `usage` 是这次调用的 token 用量（dict 或 None），和消息同生共死 ——
    并发下不会串到别的节点头上。
    """
    text: str = ""
    tool_calls: list = field(default_factory=list)
    usage: dict = None


# 只依赖 OpenAI 兼容协议：模型名统一走 openai/ 前缀 + api_base，不交给 litellm 猜 provider
_COMPAT_PREFIX = "openai/"

litellm.suppress_debug_info = True
litellm.drop_params = True

# 重试次数与流式无关：litellm 的 num_retries 只重试请求建立阶段的错误，
# 开始吐字后断流直接抛出、不重发，所以不会把同一段话说两遍。
_RETRIES = 4


class LLM:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.environ.get("TREE_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("TREE_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.environ.get("TREE_API_KEY")

    def _route(self, model):
        return model if "/" in model else _COMPAT_PREFIX + model

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        """给 messages，返回 Message；总是流式，`tools` 给了就带工具调用。

        内容每到一个字调一次 `on_delta`、思考调一次 `on_reasoning`（None 不回调）；
        工具调用的参数在增量里拼起来。重试只在请求建立阶段生效。
        """
        resp = await litellm.acompletion(
            model=self._route(self.model),
            messages=messages,
            temperature=temperature,
            api_base=self.base_url or None,
            api_key=self.api_key,
            tools=tools,
            tool_choice="auto" if tools else None,
            parallel_tool_calls=(True if tools else None),
            stream=True,
            stream_options={"include_usage": True},  # 真实 usage 在收尾块里，不必攒 chunks 重拼
            num_retries=_RETRIES,
        )
        return await self._stream(resp, on_delta, on_reasoning)

    async def _stream(self, resp, on_delta, on_reasoning):
        """流式：话与思考逐字回调，工具调用增量按 index 拼起来组装成 Message（带 usage）。

        部分 provider 把 usage 带在最后一个有内容的块上而不是独立收尾块，
        所以每块都试着收一次，最后一次写到的就是整段调用的账。
        """
        parts, calls = [], []
        tool_deltas = {}                     # index -> {"id", "name", "arguments": [片段]}
        usage = None
        async for chunk in resp:
            u = getattr(chunk, "usage", None)   # 收尾块只有 usage；有的 provider 挂在最后一块内容上
            if u:
                # usage 是 pydantic 对象，落到 Message.usage 前先转成 dict
                usage = (u.model_dump() if hasattr(u, "model_dump")
                         else dict(u))
            if not chunk.choices:            # 收尾块：没内容，只有 usage（stream_options）
                continue
            delta = chunk.choices[0].delta
            # 无思考时字段不存在（OpenAI 规范），只能 getattr
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning and on_reasoning is not None:
                on_reasoning(reasoning)
            piece = delta.content
            if piece:
                parts.append(piece)
                if on_delta is not None:
                    on_delta(piece)
            for tcd in (delta.tool_calls or ()):
                fn = getattr(tcd, "function", None)  # 自定义型（Anthropic 风格）没有 function，整条跳过
                if fn is None:
                    continue
                slot = tool_deltas.setdefault(tcd.index, {"id": "", "name": "", "args": []})
                if tcd.id:
                    slot["id"] = tcd.id
                if fn.name:
                    slot["name"] = fn.name
                if fn.arguments:
                    slot["args"].append(fn.arguments)
        for i in sorted(tool_deltas):
            slot = tool_deltas[i]
            raw = "".join(slot["args"])
            try:
                args = json.loads(raw)
            except ValueError as e:
                raise ValueError("工具「%s」的参数不是合法 JSON：%r（%s）"
                                 % (slot["name"], raw, e))
            calls.append(ToolCall(id=slot["id"], name=slot["name"], arguments=args))
        return Message(text="".join(parts), tool_calls=calls, usage=usage)


class ChatPool:
    """把 llm.chat 串成 N 路并发（workers = 同时在飞的 llm.chat 数），消息传递、无锁。

    异常用 done-callback 原样搬到调用方的 future 上：不吞、也不让消费者 task 死掉。
    """

    def __init__(self, llm, workers):
        self.llm = llm
        self._q = asyncio.Queue()
        self._workers = [asyncio.ensure_future(self._serve())
                         for _ in range(max(1, int(workers)))]

    async def _serve(self):
        while True:
            fut, kwargs = await self._q.get()
            task = asyncio.ensure_future(self._call(kwargs))
            task.add_done_callback(lambda t, f=fut: deliver(f, t))
            await asyncio.wait([task])      # 占住名额，但不取异常（交给回调）

    async def _call(self, kwargs):
        """调用本身的同步错误也变成 task 异常经回调交付，否则 worker 会当场死、后面的请求永远等不到。"""
        return await self.llm.chat(**kwargs)

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        fut = asyncio.get_running_loop().create_future()
        await self._q.put((fut, {"messages": messages, "temperature": temperature,
                                 "on_delta": on_delta, "on_reasoning": on_reasoning,
                                 "tools": tools}))
        return await fut

    async def close(self):
        for w in self._workers:
            w.cancel()

