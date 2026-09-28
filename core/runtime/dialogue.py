"""一个节点的平铺对话账本，以及线上 wire 的配对规范化。

对话是节点的全部历史：首个 user 消息就是任务（子节点出生时拼 `base_user`，入口首条是用户的话），
之后 assistant / tool / user 逐条累积；没有单独的"任务字段"，写一律走方法。

`pair(msgs)` 是发射边界的规范化、不进账本：provider 要求每个 tool_call 都有配对回话，
而结构类工具不产出 tool 回话，发送前补一条占位。
"""

import json

from ..protocol.feedback import pair_placeholder


class Dialogue:
    """平铺消息账本；`msgs` 就是模型看到的历史（不含 system，任务首条由创建者拼）。"""

    def __init__(self, msgs=None):
        self.msgs = msgs if msgs is not None else []

    def to_list(self):
        return self.msgs

    def assistant(self, text, tool_calls, reasoning=""):
        """assistant 入账，返回落账的 tool_call id 列表（缺 id 时按回合数算）。

        `reasoning` 是思考原文（`reasoning_content`），随消息进历史 ——
        终端把思考画成历史里的一行，会话续跑也在。
        """
        offset = sum(1 for m in self.msgs if m.get("role") in ("assistant", "tool"))
        ids = [tc.id or "call_%d" % (offset + i) for i, tc in enumerate(tool_calls)]
        wire = [
            {
                "id": i,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for i, tc in zip(ids, tool_calls)
        ]
        msg = {"role": "assistant", "content": text or None}
        if reasoning:
            msg["reasoning"] = reasoning
        if wire:
            msg["tool_calls"] = wire
        self.msgs.append(msg)
        return ids

    def tool(self, call_id, content):
        self.msgs.append({"role": "tool", "tool_call_id": call_id, "content": content})

    def user(self, text):
        self.msgs.append({"role": "user", "content": text})

    def feedback(self, text):
        """把打回理由写回对话：上一条是带工具调用的 assistant 就配成 tool 回话，否则写 user 消息。"""
        last = self.msgs[-1] if self.msgs else None
        if last and last.get("role") == "assistant" and last.get("tool_calls"):
            for w in last["tool_calls"]:
                self.tool(w["id"], text)
        else:
            self.user(text)


def pair(msgs):
    """线上 wire 的配对规范化：给没有回话的 tool_call 补一条占位 tool 回话（账本一个字不改）。

    同时剥掉账本私有键（`from`：沟通消息的来源标记，只有账本 / 终端用，
    OpenAI 不认识它 —— 发射边界上删掉，不动账本）。
    """
    answered = {m.get("tool_call_id") for m in msgs if m.get("role") == "tool"}
    out = []
    for m in msgs:
        wire = dict(m)
        wire.pop("from", None)
        out.append(wire)
        if m.get("role") == "assistant":
            for w in m.get("tool_calls") or []:
                if w.get("id") not in answered:
                    out.append(
                        {"role": "tool", "tool_call_id": w["id"], "content": pair_placeholder()}
                    )
    return out
