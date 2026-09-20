#!/usr/bin/env python3
"""选项 B 的定向测试：叶子工具输出走真 role=tool 消息 + 发送边界压缩。

验证四件事（都是 B 的核心不变量）：

  A. 对话形态：叶子维护真对话 —— assistant(tool_call) 与 tool(观测) 配对，
     工具调用 id 在一条对话里不重复（重复的 call_0 会被 provider 拒 / 串）。
  B. 压缩只发生在发送边界：存储（node.observations / trace 的 code 事件）是原文；
     第 4 回合起，最早那条大工具输出在线上被压短；user（形式字段）一字未动；
     trace 里有 wire_compressed 统计。
  C. 可逆：日志折叠（LOG）在压缩文本里嵌 `Retrieve more: hash=...`，
     按 hash 调 retrieve_original 取回与原文完全一致的文本；FATAL 行幸存。
  D. TREE_COMPRESS=0（保险阀）：不挂取回工具、不产生 wire_compressed。

headroom 的压缩是确定性的（无损折叠 / 日志折叠），所以这些断言不依赖网络。
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.llm import Message, ToolCall                                   # noqa: E402
from tree.protocol.fields import Node                                    # noqa: E402
from tree.prompts import PROMPT                                          # noqa: E402
from tree.runtime import scheduler as R                                  # noqa: E402
from tree.runtime.trace import Trace                                     # noqa: E402
from tree.compression import retrieve_original                           # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-52s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


class ScriptLeaf:
    """按脚本回话的叶子：依次跑代码（每段都真跑），跑完出结论。

    把每次收到的 messages 原样记下来 —— 测试断言的是**线上形态**
    （压缩发生在发送边界，这里看到的就是模型真收到的）。
    """

    def __init__(self, codes):
        self.codes = list(codes)
        self.seen = []
        self.last_usage = {}

    async def chat(self, messages, temperature=0.2, on_delta=None,
                   on_reasoning=None, tools=None):
        self.last_usage = {"total_tokens": 0}
        self.seen.append([dict(m) for m in messages])
        if self.codes:
            code = self.codes.pop(0)
            return Message(tool_calls=[ToolCall(name="run_code",
                                                arguments={"code": code})])
        return Message(tool_calls=[ToolCall(
            name="conclude", arguments={"verdict": "满足", "text": "脚本收尾",
                                        "evidence": ["第1次观测"]})])


def go(codes):
    """跑一棵只有叶子的树。返回 (节点, 记录的线上消息, trace 记录)。"""
    d = tempfile.mkdtemp()
    trace = Trace(os.path.join(d, "t.jsonl"))
    node = Node(name="叶子", accept="2026-12-31 收盘 >= 1", kind="leaf")
    llm = ScriptLeaf(codes)
    cwd = os.getcwd()
    os.chdir(d)
    try:
        asyncio.run(R.run(node, llm, trace, registry={}, caps=None, index=None))
    finally:
        os.chdir(cwd)
    recs = [json.loads(x) for x in open(os.path.join(d, "t.jsonl"))]
    return node, llm, recs


def main():
    big_json = ("import json; print(json.dumps("
                "[{'date': '2026-12-31', 'close': i, 'vol': i * 2} "
                "for i in range(300)], ensure_ascii=False))")
    big_log = ("print('\\n'.join('[INFO] worker %d polling...' % (i % 4) "
               "for i in range(200)) + '\\n[FATAL] out of memory')")

    print("=" * 80)
    print("A. 对话形态：assistant 与 tool 配对，id 不重复")
    node, llm, recs = go([big_json, "print('小输出2')", "print('小输出3')"])
    wire3 = llm.seen[2]                       # 第三回合：3 段代码已跑
    roles = [m["role"] for m in wire3]
    asst = [m for m in wire3 if m["role"] == "assistant" and m.get("tool_calls")]
    tools = [m for m in wire3 if m["role"] == "tool"]
    line("对话形态 = system/user + 成对的 asst/tool",
         roles == ["system", "user", "assistant", "tool", "assistant", "tool"],
         str(roles))
    line("tool 消息都配到了 assistant 的 tool_call",
         all(any(a["tool_calls"][0]["id"] == t["tool_call_id"] for a in asst)
             for t in tools))
    ids = [a["tool_calls"][0]["id"] for a in asst]
    line("工具调用 id 不重复", len(ids) == len(set(ids)), str(ids))
    line("观测以 tool 消息存在（小输出逐字一致）",
         any(t["content"] == node.observations[1]["obs"]
             for t in llm.seen[2] if t["role"] == "tool"))

    print("=" * 80)
    print("B. 压缩只发生在发送边界：存储原文、线上压短、user 一字未动")
    raw = next(r["payload"]["obs"] for r in recs
               if r["kind"] == "code" and "close" in str(r["payload"]["obs"]))
    line("存储（observations）是原文", node.observations[0]["obs"] == raw,
         "%d 字" % len(raw))
    line("trace 的 code 事件是原文",
         any(r["kind"] == "code" and r["payload"]["obs"] == raw for r in recs))
    wire4 = llm.seen[3]                       # 第四回合：最早那条大输出可压了
    tool0 = next(m for m in wire4
                 if m.get("role") == "tool" and m.get("tool_call_id") == "call_0")
    line("最早那条大 JSON 输出在线上被压短",
         len(tool0["content"]) < len(raw),
         "%d -> %d 字" % (len(raw), len(tool0["content"])))
    line("user（形式字段）一字未动",
         wire4[1]["content"] == node.render_wire())
    line("system（协议）一字未动",
         wire4[0]["content"] == PROMPT["leaf"])
    wc = [r for r in recs if r["kind"] == "wire_compressed"]
    line("trace 留下 wire_compressed 统计", bool(wc) and wc[0]["payload"]["saved"] > 0,
         wc[0]["payload"] if wc else "")
    line("小输出低于压缩门槛，在线上保持原文",
         any(m.get("role") == "tool" and m.get("tool_call_id") == "call_4"
             and m["content"] == node.observations[2]["obs"] for m in wire4))

    print("=" * 80)
    print("C. 可逆：日志折叠嵌取回标记，按 hash 取回原文，FATAL 幸存")
    node2, llm2, recs2 = go([big_log, "print('小输出2')", "print('小输出3')"])
    raw2 = next(r["payload"]["obs"] for r in recs2
                if r["kind"] == "code" and "FATAL" in str(r["payload"]["obs"]))
    wire4b = llm2.seen[3]
    tool0b = next(m for m in wire4b
                  if m.get("role") == "tool" and m.get("tool_call_id") == "call_0")
    m = re.search(r"Retrieve more: hash=([0-9a-f]+)", tool0b["content"])
    line("日志折叠把重复行折掉并嵌取回标记",
         m is not None and "压缩" not in tool0b["content"][:60]
         and "lines compressed" in tool0b["content"],
         tool0b["content"][:80].replace("\n", " "))
    line("FATAL 行在压缩文本里幸存", "FATAL" in tool0b["content"])
    if m:
        got = retrieve_original({"hash": m.group(1)})
        line("按 hash 取回 == 存储原文", got == raw2,
             "%d 字" % len(got) if isinstance(got, str) else str(got)[:40])
    else:
        line("按 hash 取回 == 存储原文", False, "没有标记")

    print("=" * 80)
    print("D. TREE_COMPRESS=0：保险阀关掉压缩和取回工具")
    script = ("import os, sys; os.environ['TREE_COMPRESS'] = '0'; "
              "import asyncio; "
              "from tree import config as cfg; "
              "import tree.runtime.turn; "   # 工具实现注册发生在 turn.py 的 import 时
              "from tree.protocol.tool_specs import openai_tools; "
              "assert not cfg.COMPRESS; "
              "names = [t['function']['name'] for t in "
              "asyncio.run(openai_tools())['leaf']]; "
              "assert 'headroom_retrieve' not in names, names; "
              "print('ok:', names)")
    r = subprocess.run([sys.executable, "-c", script], capture_output=True,
                       text=True, cwd=os.path.dirname(os.path.dirname(
                           os.path.abspath(__file__))))
    line("关闭后不挂取回工具", r.returncode == 0 and r.stdout.strip().startswith("ok:"),
         r.stdout.strip()[:60] or r.stderr.strip()[-120:])

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
