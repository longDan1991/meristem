#!/usr/bin/env python3
"""`llm._stream` 的定向测试：流式解析（文本 / 思考 / 工具参数拼接 / usage）。

零成本、确定性：不碰网络，用假 chunk（SimpleNamespace）喂 `_stream`，模拟
litellm 流式响应（OpenAI 兼容协议形状）。测的是 llm.py 自己的解析逻辑：

  A. 文本 + 思考 + 工具参数两段碎片 → 拼回完整 Message（text / tool_calls）
  B. on_delta / on_reasoning 各自收到碎片
  C. 收尾块 usage（stream_options）→ last_usage 是 dict
  D. 坏参数 JSON → 带工具名 + 原始片段的 ValueError（不糊，fail fast）
  E. 边界：无思考块（reasoning_content 字段不存在）不炸；无 usage 收尾 last_usage=None
  F. 自定义型 tool-call（没有 function 字段）被跳过，不炸
  G. 多个 index 的工具调用按 index 排序、各自解析
"""

import asyncio
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from tree.llm import LLM                                       # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-52s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def NS(**kw):
    return types.SimpleNamespace(**kw)


def tcd(index, tid=None, name=None, args=None):
    """一个工具调用增量（ChatCompletionDeltaToolCall 形状）。function 不给就是
    自定义型（没有 function 字段）。"""
    fn = None if (name is None and args is None) else NS(name=name, arguments=args)
    return NS(index=index, id=tid, function=fn)


def chunk(delta=None, usage=None):
    """一个流式 chunk：delta 为 None 表示收尾块（无 choices，只带 usage）。"""
    return NS(choices=[] if delta is None else [NS(delta=delta)], usage=usage)


async def _run(factory, on_delta=None, on_reasoning=None):
    llm = LLM.__new__(LLM)
    llm._tls = types.SimpleNamespace(usage=None)
    msg = await llm._stream(factory(), on_delta, on_reasoning)
    return llm, msg


def test_full():
    deltas, think = [], []

    async def stream():
        yield chunk(NS(content="你", tool_calls=None))
        yield chunk(NS(content=None, reasoning_content="想一下", tool_calls=None))
        yield chunk(NS(content="好。", tool_calls=None))
        # OpenAI 规范：首块 id+name+空 arguments 一起到，之后只有参数碎片
        yield chunk(NS(content=None, tool_calls=[tcd(0, tid="call_1", name="bash",
                                                     args="")]))
        yield chunk(NS(content=None, tool_calls=[tcd(0, args='{"cmd": "ls')]))
        yield chunk(NS(content=None, tool_calls=[tcd(0, args=' -la"}')]))
        yield chunk(usage=NS(model_dump=lambda: {"total_tokens": 42, "prompt_tokens": 10,
                                                 "completion_tokens": 32}))

    llm, msg = asyncio_run(_run(stream, deltas.append, think.append))
    line("文本碎片拼回整段", msg.text == "你好。", repr(msg.text))
    line("on_delta 逐块收到", deltas == ["你", "好。"], repr(deltas))
    line("on_reasoning 收到思考", think == ["想一下"], repr(think))
    line("工具参数两段拼回 dict", (len(msg.tool_calls) == 1
                                   and msg.tool_calls[0].arguments == {"cmd": "ls -la"}),
         repr(msg.tool_calls))
    line("工具 id / name 取到", (msg.tool_calls[0].id == "call_1"
                                 and msg.tool_calls[0].name == "bash"),
         repr((msg.tool_calls[0].id, msg.tool_calls[0].name)))
    line("收尾块 usage 读成 dict", llm.last_usage == {"total_tokens": 42,
                                                      "prompt_tokens": 10,
                                                      "completion_tokens": 32},
         repr(llm.last_usage))


def test_bad_json():
    async def stream():
        yield chunk(NS(content=None, tool_calls=[tcd(0, tid="x", name="bash",
                                                     args="{bad")]))
        yield chunk(usage=NS(model_dump=lambda: {"total_tokens": 1}))

    try:
        asyncio_run(_run(stream))
        line("坏参数 JSON 当场炸（fail fast）", False, "没炸")
    except ValueError as e:
        line("坏参数 JSON 当场炸（fail fast）", True)
        line("错误带工具名 + 原始片段", "bash" in str(e) and "{bad" in str(e), str(e))


def test_boundaries():
    # 纯文本：无思考、无工具、无 usage 收尾
    async def plain():
        yield chunk(NS(content="纯文本", tool_calls=None))

    llm, msg = asyncio_run(_run(plain))
    line("无思考块不炸（reasoning_content 不存在）", msg.text == "纯文本"
         and not msg.tool_calls)
    line("无 usage 收尾 → last_usage 为 None", llm.last_usage is None,
         repr(llm.last_usage))

    # 自定义型 tool-call（Anthropic 风格：没有 function 字段）→ 整条跳过不炸；
    # 同流里的标准调用照常解析
    async def custom():
        yield chunk(NS(content=None, tool_calls=[tcd(0, tid="c1")]))
        yield chunk(NS(content=None, tool_calls=[tcd(1, tid="s1", name="bash",
                                                     args="{}")]))

    _, msg = asyncio_run(_run(custom))
    line("自定义型 tool-call 整条跳过", (len(msg.tool_calls) == 1
                                       and msg.tool_calls[0].name == "bash"
                                       and msg.tool_calls[0].id == "s1"),
         repr(msg.tool_calls))


def test_multi_index():
    async def stream():
        yield chunk(NS(content=None, tool_calls=[tcd(1, tid="b", name="t2",
                                                     args='{"x": 2}')]))
        yield chunk(NS(content=None, tool_calls=[tcd(0, tid="a", name="t1",
                                                     args='{"x": 1}')]))

    _, msg = asyncio_run(_run(stream))
    line("多个工具调用按 index 排序", [tc.name for tc in msg.tool_calls] == ["t1", "t2"]
         and [tc.arguments for tc in msg.tool_calls] == [{"x": 1}, {"x": 2}],
         repr(msg.tool_calls))


def asyncio_run(coro):
    return asyncio.run(coro)


def main():
    test_full()
    test_bad_json()
    test_boundaries()
    test_multi_index()
    print("=" * 78)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
