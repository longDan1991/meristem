"""LLM 适配层：只暴露一个函数 —— 给 messages，返回文本。

底层是 `litellm`：任何 OpenAI 兼容端点都能用（OpenAI / DeepSeek / Kimi /
Qwen / 本地 vLLM / 火山 ark……），重试、超时、流式、usage 都是它的事，
这里不自己写 HTTP / SSE / 退避（那是重复造轮子）。

给了 `on_delta` 就换成流式：内容一个字一个字回调，同时照旧返回整段文本。
`on_reasoning` 另开一条：推理模型的 `reasoning_content`（思考）走它，
和回答分开，终端才能把思考画成灰的、回答画成亮的。
MockLLM 让整棵树在没有 API key 的情况下也能跑通。

`last_usage` 是**线程本地**的：每个 worker 记自己那一次调用的用量，
`turn._log_usage` 立刻读走，所以这里不需要共享计数器、也不需要锁（AGENTS §9）。
"""

import json
import os
import threading

import litellm
from json_repair import loads as _json_repair_loads

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

    def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None):
        """给 messages，返回整段文本。

        `on_delta` / `on_reasoning` 给了任一个就**流式**：内容每到一个字就调
        一次 `on_delta(这一小口)`，模型思考每到一个字就调一次
        `on_reasoning(这一小口)` —— 两条分开，终端才能把思考画成灰的、
        回答画成亮的。同时照旧把整段攒起来返回。

        重试（litellm 的 num_retries）：**没吐字之前的网络错误可以重来**；
        已经开始吐字就不重试 —— 重试会把同一段话说两遍（§2.5 实测教训）。
        """
        streaming = on_delta is not None or on_reasoning is not None
        resp = litellm.completion(
            model=self._route(self.model),
            messages=messages,
            temperature=temperature,
            api_base=self.base_url or None,
            api_key=self.api_key,
            stream=streaming,
            num_retries=0 if streaming else 4,
        )
        if not streaming:
            self._tls.usage = _usage_dict(resp)
            return resp.choices[0].message.content
        return self._stream(resp, messages, on_delta, on_reasoning)

    def _stream(self, resp, messages, on_delta, on_reasoning):
        parts, chunks = [], []
        for chunk in resp:
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
        full = litellm.stream_chunk_builder(chunks, messages=messages)
        self._tls.usage = _usage_dict(full)
        return "".join(parts)


def _usage_dict(resp):
    """litellm 的 usage 是 pydantic 对象，._log_usage 要的是 dict。"""
    u = getattr(resp, "usage", None) or {}
    if hasattr(u, "model_dump"):
        return u.model_dump()
    if hasattr(u, "dict"):
        return u.dict()
    return dict(u)


def parse_json(text):
    """从模型输出里取出第一个完整 JSON 对象，能修就修（围栏 / 尾逗号 / 散落正文）。

    模型吐的 JSON 常常不干净：包在 ```json 围栏里、有尾逗号、前后有解释的话。
    手工正则只会捡起第一对花括号之间的东西；`json_repair` 专门处理这种烂输出。
    实在修不出就抛 `ValueError`（调用方按"用不了"处理）。
    """
    if not text:
        raise ValueError("空输出")
    try:
        return _json_repair_loads(text)
    except ValueError as e:
        raise ValueError("没有 JSON: %s" % e) from e


class MockLLM:
    """不调模型也能跑通整棵树：分配节点先拆一次、拿到下层结论就出结论；
    叶子做一个动作再出结论。"""

    def __init__(self):
        self.calls = 0

    def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None):
        self.calls += 1
        self.last_usage = {"total_tokens": 0}
        user = messages[-1]["content"]
        fresh = "(还没有)" in user

        if "可用工具" in user:                      # 叶子
            if fresh:
                text = json.dumps({"action": {"tool": "bash",
                                               "args": {"cmd": "echo mock"}}},
                                  ensure_ascii=False)
            else:
                text = json.dumps({"conclusion": {"verdict": "满足",
                                                   "text": "叶子做完了（mock）",
                                                   "evidence": ["第1次观测"]}},
                                  ensure_ascii=False)
        elif fresh:                                 # 分配节点：拆一次
            def kid(n):
                return {"name": n, "detail": "mock 详情", "notes": "",
                        "accept": "%s 的可观测结果" % n, "kind": "leaf",
                        "gate": False, "keywords": ["mock", "echo"],
                        "conc_range": [50, 200]}
            text = json.dumps({"children": [kid("子任务A"), kid("子任务B")]},
                              ensure_ascii=False)
        else:
            text = json.dumps({"conclusion": {"verdict": "满足",
                                               "text": "下层都回来了（mock）",
                                               "evidence": ["子任务A 的结论"]}},
                              ensure_ascii=False)
        if on_delta:
            on_delta(text)
        return text
