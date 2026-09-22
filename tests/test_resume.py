#!/usr/bin/env python3
"""会话可续跑的定向测试。零成本、确定性（脚本化模型 + 真调度器 + 真落盘）。

核心不变量：**一场会话 = 一棵树**，入口节点（kind="intake"）是根，谈成的任务
都是它的孩子。`trace.jsonl` 的记录里，`state` 检查点只有两样：Node 全字段 +
平铺对话（msgs）—— 没有编排字段。退出（哪怕崩溃）后，`session.load` 读回这
**一棵树**（root / registry / state），直接丢给 `scheduler.run(..., resume=tree)`
接着跑：resume 时用 `reconcile` 补投递（崩溃窗口）、按共享谓词重排队列。

  A. Node 序列化往返：to_dict → from_dict 不丢任何字段（含 deferred）
  B. load 返回一棵树；没根 / 多根当场报错
  B2. 崩溃窗口：孩子有结论但投递丢了 → 恢复补投递
  B3. 门槛窗口：门槛出了结论但父节点没结算 → 恢复按结论作废
  C. 调度器续跑：一棵树跑到一半"崩溃"→ load → resume → 跑完
  D. 入口对话 = 根节点的 msgs（没有独立的 chat_* 通道了）
  E. 整场会话（入口 + 任务）崩溃 → load 一棵树 → resume → 二次 load 全完工
  F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果
  G. 一场会话多个任务 = 一棵树多个孩子，只有没跑完的被接着跑
  I. session_label：当前格式认入口的孩子，档案（无入口）认根本身
"""

import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from tree.llm import Message, ToolCall                             # noqa: E402
from tree.protocol.fields import Node                              # noqa: E402
from tree.prompts.messages import result_ids                       # noqa: E402
from tree.runtime import reconcile                                 # noqa: E402
from tree.runtime.scheduler import run                             # noqa: E402
from tree.runtime.session import load, session_label               # noqa: E402
from tree.runtime.trace import Trace, iter_trace_lines                  # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-52s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def kid(name, accept="2026-12-31 收盘 >= 1"):
    return {"name": name, "detail": "d", "notes": "",
            "accept": "%s（%s 负责）" % (accept, name), "kind": "leaf",
            "gate": False, "conc_range": [1, 10]}


def state_rec(node, msgs):
    """新格式检查点：Node 全字段 + 平铺对话，没有编排字段。"""
    return {"node": node.to_dict(), "msgs": msgs}


def queueable(tree, nid):
    """该不该调 LLM 的共享谓词 —— 调度器 resume 时按它重排队列。"""
    st = tree["state"][nid]
    return reconcile.actionable(st["node"], st["msgs"], result_ids(st["msgs"]))


class ScriptLLM:
    """按脚本回话的模型：tuple = 工具调用，str = 说一句话，Exception = 抛（模拟崩溃）。"""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.calls += 1
        self.last_usage = {"total_tokens": 0}
        action = self.script.pop(0) if self.script else ("text", "嗯。")
        if isinstance(action, Exception):
            raise action
        if isinstance(action, str):
            return Message(text=action)
        name, args = action
        return Message(text="", tool_calls=[ToolCall(name=name, arguments=args)])


async def _run_tree(script, path):
    """用脚本化模型跑一棵"根任务→拆一个叶子"的树。崩溃或跑完都返回根。"""
    root = Node(name="根任务", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    llm = ScriptLLM(script)
    try:
        await run(root, llm, Trace(path))
    except RuntimeError:
        pass
    return root


async def main():
    print("=" * 80)
    print("A. Node 序列化往返：to_dict → from_dict 不丢任何字段")
    n = Node(name="任务", detail="详情", notes="注意", accept="2026-12-31 收盘 >= 1",
             kind="leaf", gate=True, conc_range=[1, 2],
             lineage=[["根", "根的详情"]])
    n.deferred = [kid("暂缓的子任务")]
    n.close("满足", "做完了", ["证据"], ["外部需求"])
    n2 = Node.from_dict(n.to_dict())
    line("字段原样回来", n2.name == n.name and n2.accept == n.accept
         and n2.kind == n.kind and n2.gate == n.gate)
    line("结构/暂缓/结局都在", n2.lineage == n.lineage
         and n2.deferred == n.deferred
         and n2.verdict == "满足" and n2.conclusion == "做完了"
         and n2.evidence == ["证据"])

    print("=" * 80)
    print("B. load 返回一棵树（入口为根）；没根 / 多根当场报错")
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "trace.jsonl")
    # 手工构造：入口根 + 一个跑了一半的叶子任务
    intake = Node(name="会话", kind="intake")
    leaf = Node(name="子A", accept="2026-12-31 收盘 >= 1（子A 负责）", kind="leaf",
                parent=intake.id, depth=1)
    intake.children = [leaf.id]
    tr = Trace(tp)
    tr.add(intake.id, "state", state_rec(intake, [
        {"role": "user", "content": "用户的任务: 帮我做X"}]))
    tr.add(leaf.id, "state", state_rec(leaf, [
        {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_0", "type": "function",
            "function": {"name": "bash", "arguments": '{"cmd": "echo hi"}'}}]},
        {"role": "tool", "tool_call_id": "call_0", "content": "hi"}]))
    tr.drain()
    t = load(tp)
    line("根是入口节点", t["root"].kind == "intake" and t["root"].name == "会话")
    line("state 只有 node + msgs", set(t["state"][leaf.id].keys()) == {"node", "msgs"})
    line("入口对话就是根的 msgs",
         t["state"][intake.id]["msgs"][0]["content"] == "用户的任务: 帮我做X")
    line("重排队列：叶子该跑，入口等孩子（共享谓词）",
         queueable(t, leaf.id) and not queueable(t, intake.id))
    # 空记录 → 报错（没有 state 检查点）
    d0 = tempfile.mkdtemp()
    tp0 = os.path.join(d0, "t.jsonl")
    tr0 = Trace(tp0)
    tr0.add(None, "open", {"name": "只有 open、没有 state"})
    tr0.drain()
    try:
        load(tp0)
        line("空记录报错（没有 state 检查点）", False)
    except ValueError:
        line("空记录报错（没有 state 检查点）", True)
    # 多根 → 报错
    d_multi = tempfile.mkdtemp()
    tp_multi = os.path.join(d_multi, "t.jsonl")
    trm = Trace(tp_multi)
    r1 = Node(name="任务一", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    r2 = Node(name="任务二", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    trm.add(r1.id, "state", state_rec(r1, []))
    trm.add(r2.id, "state", state_rec(r2, []))
    trm.drain()
    try:
        load(tp_multi)
        line("多个根报错（不是入口为根的一棵树）", False)
    except ValueError:
        line("多个根报错（不是入口为根的一棵树）", True)

    # B2：孩子出了结论但投递丢了（崩溃窗口）→ 恢复补投递
    d_b2 = tempfile.mkdtemp()
    tp_b2 = os.path.join(d_b2, "trace.jsonl")
    it2 = Node(name="会话", kind="intake")
    a = Node(name="甲", accept="x（甲 负责）", kind="leaf", parent=it2.id, depth=1)
    a.close("满足", "甲好了", ["e"])
    it2.children = [a.id]
    tr_b2 = Trace(tp_b2)
    tr_b2.add(it2.id, "state", state_rec(it2, []))     # 入口对话里没有甲的结果
    tr_b2.add(a.id, "state", state_rec(a, []))
    tr_b2.drain()
    t_b2 = load(tp_b2)
    line("B2: 投递丢失 → 加载时入口不排队（孩子未结算）",
         not queueable(t_b2, it2.id) and not queueable(t_b2, a.id))
    try:
        await run(t_b2["root"], ScriptLLM(["甲回来了，全部完成。"]),
                  Trace(tp_b2), registry=t_b2["registry"], resume=t_b2,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    line("B2: 补投递后入口看到甲的结果（带 id 标记）",
         any("下层结论" in str(m.get("content", "")) and "id:" in str(m.get("content", ""))
             for m in t_b2["state"][it2.id]["msgs"]))
    line("B2: 二次 load 一棵树还在", load(tp_b2)["root"].kind == "intake")

    # B3：门槛孩子出了"未满足"结论，父节点还没结算 → 恢复按结论作废暂缓分支
    d_b3 = tempfile.mkdtemp()
    tp_b3 = os.path.join(d_b3, "trace.jsonl")
    pr3 = Node(name="父", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    gate = Node(name="门槛", accept="x（门槛 负责）", kind="leaf",
                parent=pr3.id, depth=1, gate=True)
    gate.close("未满足", "不成立", ["e"])
    pr3.children = [gate.id]
    pr3.deferred = [kid("乙")]
    tr_b3 = Trace(tp_b3)
    tr_b3.add(pr3.id, "state", state_rec(pr3, []))
    tr_b3.add(gate.id, "state", state_rec(gate, []))
    tr_b3.drain()
    t_b3 = load(tp_b3)
    await run(t_b3["root"], ScriptLLM([
        ("conclude", {"verdict": "满足", "text": "门槛不成立，做不了",
                      "evidence": ["门槛"]})]),
              Trace(tp_b3), registry=t_b3["registry"], resume=t_b3)
    line("B3: 门槛未满足 → 暂缓的乙从未出生",
         all(n.name != "乙" for n in t_b3["registry"].values()))
    line("B3: 作废旁白写进父节点对话",
         any("暂缓分支作废" in str(m.get("content", ""))
             for m in t_b3["state"][pr3.id]["msgs"]))
    line("B3: 父节点接着跑出了结论", t_b3["root"].verdict == "满足")

    print("=" * 80)
    print("C. 调度器续跑：一棵树跑到一半崩溃 → load → resume → 跑完")
    d2 = tempfile.mkdtemp()
    tp2 = os.path.join(d2, "trace.jsonl")
    await _run_tree(
        [("create_children", {"children": [kid("子A")]}),
         ("bash", {"cmd": "echo hi"}),
         RuntimeError("模拟崩溃")], tp2)
    t = load(tp2)
    line("崩溃后 load 出一棵树", t["root"].name == "根任务")
    llm2 = ScriptLLM([("conclude", {"verdict": "满足", "text": "子A做完了",
                                    "evidence": ["第1次观测"]}),
                      ("conclude", {"verdict": "满足", "text": "全部完成",
                                    "evidence": ["子A 结论"]})])
    await run(t["root"], llm2, Trace(tp2), registry=t["registry"], resume=t)
    line("没跑完的节点接着跑完了",
         t["root"].verdict == "满足" and t["root"].conclusion == "全部完成")
    line("孩子没被重跑（bash 工具调用只有一次）",
         sum(1 for m in t["state"][t["root"].children[0]]["msgs"]
             if m.get("role") == "assistant" and m.get("tool_calls")
             and any(tc.get("function", {}).get("name") == "bash"
                     for tc in m["tool_calls"])) == 1)
    line("再次 load：root 判定在", load(tp2)["root"].verdict == "满足")

    print("=" * 80)
    print("D. 入口对话 = 根节点的 msgs（新会话的种子进根对话）")
    d3 = tempfile.mkdtemp()
    tp3 = os.path.join(d3, "trace.jsonl")
    intake3 = Node(name="会话", kind="intake")
    llm3 = ScriptLLM(["你要做什么？", "明白了。"])
    asks = iter(["帮我做X", EOFError()])
    async def ask3(t):
        a = next(asks)
        if isinstance(a, Exception):
            raise a
        return a
    try:
        await run(intake3, llm3, Trace(tp3), seed="用户的任务: 帮我做X", ask=ask3)
    except EOFError:
        pass
    t3 = load(tp3)
    msgs = t3["state"][intake3.id]["msgs"]
    line("种子进根对话", msgs[0]["content"] == "用户的任务: 帮我做X")
    line("入口回复与用户的话都在根对话里",
         msgs[1]["content"] == "你要做什么？"
         and msgs[-1]["content"] == "帮我做X"
         and len(msgs) == 3)
    line("没有独立的 chat_* 通道了",
         all(r["kind"] != "chat_user" for r in _recs(tp3)))

    print("=" * 80)
    print("E. 整场会话（入口 + 任务）崩溃 → load 一棵树 → resume → 全完工")
    d4 = tempfile.mkdtemp()
    tp4 = os.path.join(d4, "trace.jsonl")
    intake4 = Node(name="会话", kind="intake")
    llm4 = ScriptLLM([
        ("submit_root", {"root": {"name": "任务X", "detail": "d", "notes": "",
                                  "accept": "2026-12-31 收盘 >= 1", "kind": "leaf",
                                  "conc_range": [1, 10]}}),
        RuntimeError("模拟崩溃")])            # 任务还没出生就崩（submit 之后）
    try:
        await run(intake4, llm4, Trace(tp4), seed="用户的任务: X",
                  ask=lambda t: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = load(tp4)
    line("崩溃后一棵树、入口为根", t["root"].kind == "intake")
    task = [n for n in t["registry"].values() if n.parent == t["root"].id]
    line("任务挂成入口的孩子", len(task) == 1 and task[0].kind == "leaf")
    llm5 = ScriptLLM([
        ("bash", {"cmd": "echo hi"}),
        ("conclude", {"verdict": "满足", "text": "任务X做完了", "evidence": ["第1次观测"]}),
        "跑完了。"])
    try:
        await run(t["root"], llm5, Trace(tp4), registry=t["registry"], resume=t,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t2 = load(tp4)
    task2 = [n for n in t2["registry"].values() if n.parent == t2["root"].id][0]
    line("二次 load：任务出结论", task2.verdict == "满足")
    line("入口对话带着任务结论",
         any("下层结论" in str(m.get("content", "")) for m in t2["state"][t2["root"].id]["msgs"]))

    print("=" * 80)
    print("F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果")
    d5 = tempfile.mkdtemp()
    tp5 = os.path.join(d5, "trace.jsonl")
    intake5 = Node(name="会话", kind="intake")
    tr5 = Trace(tp5)
    tr5.add(intake5.id, "state", state_rec(intake5, []))
    tr5.drain()
    with open(tp5, "a", encoding="utf-8") as f:
        f.write('{"kind": "state", "node": "半')     # 写了一半的一笔
    line("半行被跳过，前面的还能读", load(tp5)["root"].kind == "intake")
    line("mid-file 坏行照样炸（那是真损坏，不许吞）",
         _midfile_corrupt_raises(tp5))

    print("=" * 80)
    print("G. 一场会话多个任务 = 一棵树多个孩子，只有没跑完的被接着跑")
    d6 = tempfile.mkdtemp()
    tp6 = os.path.join(d6, "trace.jsonl")
    intake6 = Node(name="会话", kind="intake")
    llm6 = ScriptLLM([
        ("submit_root", {"root": {"name": "任务一", "detail": "d", "notes": "",
                                  "accept": "2026-12-31 收盘 >= 1", "kind": "dispatch",
                                  "conc_range": [1, 10]}}),
        ("create_children", {"children": [kid("甲")]}),
        ("conclude", {"verdict": "满足", "text": "甲好了", "evidence": ["e"]}),
        ("conclude", {"verdict": "满足", "text": "任务一完成", "evidence": ["甲"]}),
        ("submit_root", {"root": {"name": "任务二", "detail": "d", "notes": "",
                                  "accept": "2026-12-31 收盘 >= 2", "kind": "leaf",
                                  "conc_range": [1, 10]}}),
        RuntimeError("崩")])
    try:
        await run(intake6, llm6, Trace(tp6), seed="用户的任务: 两个",
                  ask=lambda t: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = load(tp6)
    tasks = sorted([n.name for n in t["registry"].values()
                    if n.parent == t["root"].id])
    line("两个任务都是入口的孩子", tasks == ["任务一", "任务二"])
    t1 = [n for n in t["registry"].values() if n.name == "任务一"][0]
    t2 = [n for n in t["registry"].values() if n.name == "任务二"][0]
    line("跑完的任务一有判定，任务二没有",
         t1.verdict == "满足" and not t2.verdict)
    line("任务一的孩子也有判定",
         all(n.verdict for n in t["registry"].values() if n.parent == t1.id))
    llm7 = ScriptLLM([
        ("bash", {"cmd": "echo 2"}),
        ("conclude", {"verdict": "满足", "text": "任务二完成", "evidence": ["第1次观测"]}),
        "都跑完了。"])
    try:
        await run(t["root"], llm7, Trace(tp6), registry=t["registry"], resume=t,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t_after = load(tp6)
    t2_after = [n for n in t_after["registry"].values() if n.name == "任务二"][0]
    line("恢复后任务二接着跑完", t2_after.verdict == "满足")
    line("任务一没被动过",
         [n for n in t_after["registry"].values() if n.name == "任务一"][0].verdict == "满足")

    print("=" * 80)
    print("I. session_label：当前格式认入口的孩子，档案（无入口）认根本身")
    d_i = tempfile.mkdtemp()
    tp_i = os.path.join(d_i, "trace.jsonl")
    it_i = Node(name="会话", kind="intake")
    leaf_i = Node(name="子A", accept="x", kind="leaf", parent=it_i.id, depth=1)
    leaf_i.close("满足", "done", ["e"])
    it_i.children = [leaf_i.id]
    tr_i = Trace(tp_i)
    tr_i.add(it_i.id, "state", state_rec(it_i, []))
    tr_i.add(leaf_i.id, "state", state_rec(leaf_i, []))
    tr_i.drain()
    lbl = session_label(tp_i)
    line("当前格式：任务 = 入口的孩子", "子A" in lbl and "[满足]" in lbl)
    d_j = tempfile.mkdtemp()
    tp_j = os.path.join(d_j, "trace.jsonl")
    root_j = Node(name="老任务", accept="x", kind="dispatch")
    root_j.close("阻塞", "做不了", [])
    tr_j = Trace(tp_j)
    tr_j.add(root_j.id, "state", state_rec(root_j, []))
    tr_j.drain()
    lbl2 = session_label(tp_j)
    line("档案：没有入口，根本身就是任务", "老任务" in lbl2 and "[阻塞]" in lbl2)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


def _recs(path):
    return list(iter_trace_lines(path))


def _load_raises(path):
    try:
        load(path)
    except ValueError:
        return True
    return False


def _midfile_corrupt_raises(path):
    """坏行在文件中间（后面还有完整行）→ load 必须报错，不能悄悄跳过。"""
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"kind": "not_json"\n')          # 中间坏行
        f.write('{"kind": "state", "x": 1}\n')   # 后面还有完整行
    return _load_raises(path)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
