"""LLM 适配层：只暴露一个函数 —— 给 messages，返回 Message（文本 + 工具调用）。

底层是 `litellm`：任何 OpenAI 兼容端点都能用（OpenAI / DeepSeek / Kimi /
Qwen / 本地 vLLM / 火山 ark……），重试、超时、流式、usage 都是它的事，
这里不自己写 HTTP / SSE / 退避（那是重复造轮子）。

给了 `tools` 就走**工具调用**（非流式）：模型要么调用工具、要么回文本，
两者都原样装进 `Message`。工具调用是现在大模型的通用基础能力，
litellm 把它透传给任何 OpenAI 兼容端点。

给了 `on_delta`（没给 tools）就换成流式：内容一个字一个字回调，同时照旧
返回整段文本。`on_reasoning` 另开一条：推理模型的 `reasoning_content`（思考）
走它，和回答分开，终端才能把思考画成灰的、回答画成亮的。

`last_usage` 是**线程本地**的：每个 worker 记自己那一次调用的用量，
`turn._log_usage` 立刻读走，所以这里不需要共享计数器、也不需要锁（AGENTS §9）。
"""

import json
import os
import threading
from dataclasses import dataclass, field

import litellm


@dataclass
class ToolCall:
    """一次工具调用：id（多轮对话回写历史用）+ 名字 + 已解析成 dict 的参数。"""
    id: str = ""
    name: str = ""
    arguments: dict = field(default_factory=dict)


@dataclass
class Message:
    """模型一次回复：要么有文本、要么有工具调用（或两者）。"""
    text: str = ""
    tool_calls: list = field(default_factory=list)


def _to_message(msg):
    """litellm 的 message 对象 → 我们的 Message。参数是 provider 按 schema
    生成的结构化 JSON，解析失败就把原文原样留着（不悄悄丢掉，§2）。"""
    calls = []
    for tc in (getattr(msg, "tool_calls", None) or []):
        fn = getattr(tc, "function", None)
        if fn is None:
            continue
        raw = getattr(fn, "arguments", None)
        if isinstance(raw, dict):
            args = raw
        elif isinstance(raw, str):
            try:
                args = json.loads(raw)
            except ValueError:
                args = {"_unparsed_json": raw}
        else:
            args = {}
        calls.append(ToolCall(id=getattr(tc, "id", "") or "",
                              name=getattr(fn, "name", "") or "",
                              arguments=args))
    return Message(text=getattr(msg, "content", None) or "", tool_calls=calls)

# 我们只依赖 OpenAI 兼容协议（Ark / vLLM / Kimi / Qwen / DeepSeek 都是），
# 所以模型名统一走 openai/ 前缀 + api_base，不交给 litellm 猜 provider。
# 模型名里已带 provider 前缀（如 "deepseek/deepseek-chat"）就原样用。
_COMPAT_PREFIX = "openai/"

litellm.suppress_debug_info = True
litellm.drop_params = True


class LLM:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.environ.get("TREE_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("TREE_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.environ.get("TREE_API_KEY")
        self._tls = threading.local()

    @property
    def last_usage(self):
        return getattr(self._tls, "usage", None)

    def _route(self, model):
        return model if "/" in model else _COMPAT_PREFIX + model

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        """给 messages，返回 Message（文本 + 工具调用）。真异步（P4）：走 `litellm.acompletion`。

        `tools` 给了就带工具（`tool_choice="auto"`）：模型要么调工具要么回文本。
        `on_delta` / `on_reasoning` 给了任一个就**流式**：内容每到一个字就调
        一次 `on_delta(这一小口)`，模型思考每到一个字就调一次
        `on_reasoning(这一小口)` —— 两条分开，终端才能把思考画成灰的、
        回答画成亮的。**流式 + tools 也支持**：工具调用的参数在增量里拼起来
        （入口那一路：话要流式吐字、形式要结构化收）。

        重试（litellm 的 num_retries）：**没吐字之前的网络错误可以重来**；
        已经开始吐字就不重试 —— 重试会把同一段话说两遍（实测教训）。
        """
        streaming = on_delta is not None or on_reasoning is not None
        resp = await litellm.acompletion(
            model=self._route(self.model),
            messages=messages,
            temperature=temperature,
            api_base=self.base_url or None,
            api_key=self.api_key,
            tools=tools,
            tool_choice="auto" if tools else None,
            parallel_tool_calls=(False if tools else None),  # 一次只能调一个（balk 兜底）
            stream=streaming,
            num_retries=0 if streaming else 4,
        )
        if not streaming:
            self._tls.usage = _usage_dict(resp)
            return _to_message(resp.choices[0].message)
        return await self._stream(resp, messages, on_delta, on_reasoning)

    async def _stream(self, resp, messages, on_delta, on_reasoning):
        """流式：话（content）一个字一个字回调；思考走 on_reasoning；
        工具调用的增量按 index 拼起来，返回时组装成 Message。"""
        parts, chunks = [], []
        tool_deltas = {}                     # index -> {"id", "name", "arguments": [片段]}
        async for chunk in resp:
            chunks.append(chunk)
            try:
                delta = chunk.choices[0].delta
            except (IndexError, TypeError):
                continue                # usage-only 收尾块，没有 choices
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                on_reasoning(reasoning)
            piece = getattr(delta, "content", None)
            if piece:
                parts.append(piece)
                on_delta(piece)
            for tcd in (getattr(delta, "tool_calls", None) or []):
                idx = getattr(tcd, "index", 0)
                slot = tool_deltas.setdefault(idx, {"id": "", "name": "", "args": []})
                if getattr(tcd, "id", None):
                    slot["id"] = tcd.id
                fn = getattr(tcd, "function", None)
                if fn is None:
                    continue
                if getattr(fn, "name", None):
                    slot["name"] = fn.name
                if getattr(fn, "arguments", None):
                    slot["args"].append(fn.arguments)
        full = litellm.stream_chunk_builder(chunks, messages=messages)
        self._tls.usage = _usage_dict(full)
        calls = []
        for i in sorted(tool_deltas):
            slot = tool_deltas[i]
            raw = "".join(slot["args"])
            try:
                args = json.loads(raw)
            except ValueError:
                args = {"_unparsed_json": raw}
            calls.append(ToolCall(id=slot["id"], name=slot["name"], arguments=args))
        return Message(text="".join(parts), tool_calls=calls)


def _usage_dict(resp):
    """litellm 的 usage 是 pydantic 对象，._log_usage 要的是 dict。"""
    u = getattr(resp, "usage", None) or {}
    if hasattr(u, "model_dump"):
        return u.model_dump()
    if hasattr(u, "dict"):
        return u.dict()
    return dict(u)

