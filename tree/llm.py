"""LLM 适配层：只暴露一个函数 —— 给 messages，返回文本。

任何 OpenAI 兼容端点都能用（OpenAI / DeepSeek / Kimi / Qwen / 本地 vLLM）。
MockLLM 让整棵树在没有 API key 的情况下也能跑通。
"""

import json
import os
import re
import threading
import time
import urllib.request


class LLM:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.environ.get("TREE_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("TREE_BASE_URL")
                         or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("TREE_API_KEY", "")
        self._tls = threading.local()
        self._lock = threading.Lock()
        self.total_tokens = 0

    @property
    def last_usage(self):
        return getattr(self._tls, "usage", None)

    def chat(self, messages, temperature=0.2, attempts=4):
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }).encode()
        last = None
        for i in range(attempts):
            try:
                req = urllib.request.Request(
                    self.base_url + "/chat/completions",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + self.api_key,
                    },
                )
                with urllib.request.urlopen(req, timeout=600) as r:
                    data = json.load(r)
                self._tls.usage = data.get("usage") or {}
                with self._lock:
                    self.total_tokens += self._tls.usage.get("total_tokens", 0)
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                last = e
                time.sleep(min(60, 3 * (2 ** i)))
        raise last


def parse_json(text):
    """从模型输出里取出第一个完整 JSON 对象。"""
    if not text:
        raise ValueError("空输出")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("没有 JSON: " + text)
    return json.loads(m.group(0))


class MockLLM:
    """不调模型也能跑通整棵树：分配节点先拆一次、拿到下层结论就出结论；
    叶子做一个动作再出结论。"""

    def __init__(self, max_depth=None):
        self.calls = 0
        self.last_usage = {}
        self.total_tokens = 0

    def chat(self, messages, temperature=0.2):
        self.calls += 1
        self.last_usage = {"total_tokens": 0}
        user = messages[-1]["content"]
        fresh = "(还没有)" in user

        if "可用工具" in user:                      # 叶子
            if fresh:
                return json.dumps({"动作": {"工具": "bash",
                                            "参数": {"cmd": "echo mock"}}},
                                  ensure_ascii=False)
            return json.dumps({"结论": {"判定": "满足",
                                        "内容": "叶子做完了（mock）",
                                        "证据": ["第1次观测"]}}, ensure_ascii=False)

        if fresh:                                   # 分配节点：拆一次
            return json.dumps({"再做一次": [
                {"任务名": "子任务A", "任务详情": "mock 详情", "注意事项": "",
                 "验收标准": "子任务A 的可观测结果", "类型": "叶子"},
                {"任务名": "子任务B", "任务详情": "mock 详情", "注意事项": "",
                 "验收标准": "子任务B 的可观测结果", "类型": "叶子"},
            ]}, ensure_ascii=False)
        return json.dumps({"结论": {"判定": "满足", "内容": "下层都回来了（mock）",
                                    "证据": ["子任务A 的结论"]}}, ensure_ascii=False)
