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

import asyncio
import json
import os
import threading
from dataclasses import dataclass, field

import litellm

from .runtime import deliver


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


# 我们只依赖 OpenAI 兼容协议（Ark / vLLM / Kimi / Qwen / DeepSeek 都是），
# 所以模型名统一走 openai/ 前缀 + api_base，不交给 litellm 猜 provider。
# 模型名里已带 provider 前缀（如 "deepseek/deepseek-chat"）就原样用。
_COMPAT_PREFIX = "openai/"

litellm.suppress_debug_info = True
litellm.drop_params = True

# 重试次数：**与流式无关**。litellm 的 num_retries 只重试"请求建立阶段"（拿到
# 首个 chunk / 响应头之前）的错误；已经开始吐字后断流会直接抛给调用方、不重发
# 整流 —— 所以不会把同一段话说两遍（openai 兼容端点的语义：流式断流是原样炸
# 不是重来）。之前按"流式就不重试"一刀切，把"没吐字前可重来"也关了。
_RETRIES = 4


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
        **总是流式**（`stream=True`）：内容每到一个字调一次 `on_delta`、模型思考
        每到一个字调一次 `on_reasoning`（None 就不回调）—— 两条分开，终端才能
        把思考画成灰的、回答画成亮的。流式 + tools 也支持：工具调用的参数在
        增量里拼起来（入口那一路：话要流式吐字、形式要结构化收）。

        重试（`_RETRIES`）：只在请求建立阶段生效，与流式无关（见模块注释）。
        """
        resp = await litellm.acompletion(
            model=self._route(self.model),
            messages=messages,
            temperature=temperature,
            api_base=self.base_url or None,
            api_key=self.api_key,
            tools=tools,
            tool_choice="auto" if tools else None,
            parallel_tool_calls=(False if tools else None),  # 一次只能调一个（balk 兜底）
            stream=True,
            stream_options={"include_usage": True},  # 真实 usage 在收尾块里，不必攒 chunks 重拼
            num_retries=_RETRIES,
        )
        return await self._stream(resp, on_delta, on_reasoning)

    async def _stream(self, resp, on_delta, on_reasoning):
        """流式：话（content）一个字一个字回调；思考走 on_reasoning；
        工具调用的增量按 index 拼起来，返回时组装成 Message。"""
        parts, calls = [], []
        tool_deltas = {}                     # index -> {"id", "name", "arguments": [片段]}
        async for chunk in resp:
            if not chunk.choices:            # 收尾块：没内容，只有 usage（stream_options）
                u = getattr(chunk, "usage", None)
                if u:
                    # litellm 的 usage 是 pydantic 对象，._log_usage 要的是 dict
                    self._tls.usage = (u.model_dump() if hasattr(u, "model_dump")
                                       else dict(u))
                continue
            delta = chunk.choices[0].delta
            # 无思考时 litellm 会删掉 reasoning_content 字段（OpenAI 规范），
            # 所以只能 getattr，不能直接 . 访问
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
        return Message(text="".join(parts), tool_calls=calls)


class ChatPool:
    """把 llm.chat 串成 N 路并发：workers = **同时在飞的 llm.chat 数**。

    请求进队列，N 个消费者各取一个跑，结果经 future 原路送回 —— 消息传递，
    没有锁（AGENTS §9）。聊天和节点 Loop 解耦：节点卡在慢工具、或入口在等
    用户时，不占聊天名额；真正被限的是最贵的那个资源（模型请求）。

    异常用 **done-callback** 原样搬到调用方的 future 上（和 hands.py 同一套）：
    不吞、也不让消费者 task 死掉（死了后面的请求就永远等不到）。`asyncio.wait`
    只等完成、不取出异常 —— 消费者靠它占住名额，又不被异常炸死。

    用量仍然落在底层 llm 上（`last_usage` 线程本地）：消费者 await 完 chat
    后**同步**写 usage、同步 resolve future，单线程 asyncio 下调用方 await 一返回
    就读得到，中间不会插进别的 chat。
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
        """把一次聊天调进一个协程：调用本身的同步错误（如签名不匹配）也变成
        task 异常、经 done-callback 原样交付 —— 否则它会在 `ensure_future` 前
        同步炸掉，worker 当场死、后面排队的人永远等不到（实测挂死）。"""
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

