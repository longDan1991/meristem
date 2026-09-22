#!/usr/bin/env python3
"""会话可续跑的定向测试。零成本、确定性（脚本化模型 + 真调度器 + 真落盘）。

核心不变量：**一场会话 = 一棵树**，入口节点（kind="intake"）是根，谈成的任务
都是它的孩子。`trace.jsonl` 的记录里，`state` 检查点只有两样：Node 全字段 +
平铺对话（msgs）—— 没有编排字段。退出（哪怕崩溃）后，`Store.load` 读回这
**一棵树**（root / registry / state），直接丢给 `scheduler.run(store)` 接着跑：
恢复时用 `reconcile` 补投递（崩溃窗口）、按共享谓词重排队列。

  A. Node 序列化往返：to_dict → from_dict 不丢任何字段（含 deferred）
  B. load 返回一棵树；没根 / 多根当场报错
  B2. 崩溃窗口：孩子有结论但投递丢了 → 恢复补投递
  B3. 门槛窗口：门槛出了结论但父节点没结算 → 恢复按结论作废
  C. 调度器续跑：一棵树跑到一半"崩溃"→ load → resume → 跑完
  D. 入口对话 = 根节点的 msgs（没有独立的 chat_* 通道了）
  E. 整场会话（入口 + 任务）崩溃 → load 一棵树 → resume → 二次 load 全完工
  F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果
  G. 一场会话多个任务 = 一棵树多个孩子，只有没跑完的被接着跑
  H. 增量检查点：每节点第一笔全量、之后只带新增消息，load 按序拼回全量
  I. Store.label：当前格式认入口的孩子，档案（无入口）认根本身
"""

import asyncio
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from tree.llm import Message, ToolCall                             # noqa: E402
from tree.protocol.fields import Node                              # noqa: E402
from tree.runtime import reconcile                                 # noqa: E402
from tree.runtime.scheduler import run                             # noqa: E402
from tree.runtime.store import Store                               # noqa: E402

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


def write_recs(path, recs):
    """测试夹具：按磁盘格式手工写一份记录（测的是 load 的读路径）。"""
    with open(path, "a", encoding="utf-8") as f:
        for nid, kind, payload in recs:
            f.write(json.dumps({"t": 0, "node": nid, "kind": kind, "payload": payload},
                               ensure_ascii=False) + "\n")


def msgs_of(store, nid):
    """已加载会话里某节点的对话（load 拼回全量后的 msgs 视图）。"""
    return store.state[nid]["transcript"].to_list()


def queueable(store, nid):
    """该不该调 LLM 的共享谓词 —— 调度器 resume 时按它重排队列。"""
    st = store.state[nid]
    return reconcile.actionable(st["node"], st["transcript"].to_list(),
                                store.delivered[nid])


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
        await run(Store.new(root, trace=path), llm)
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
    write_recs(tp, [
        (intake.id, "state", state_rec(intake, [
            {"role": "user", "content": "用户的任务: 帮我做X"}])),
        (leaf.id, "state", state_rec(leaf, [
            {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_0", "type": "function",
                "function": {"name": "bash", "arguments": '{"cmd": "echo hi"}'}}]},
            {"role": "tool", "tool_call_id": "call_0", "content": "hi"}])),
    ])
    t = Store.load(tp)
    line("根是入口节点", t.root.kind == "intake" and t.root.name == "会话")
    line("检查点只有 node + msgs（没有编排字段）",
         all(set((r.get("payload") or {}).keys()) == {"node", "msgs"}
             for r in Store.iter_lines(tp, kinds=("state",))))
    line("入口对话就是根的 msgs",
         msgs_of(t, intake.id)[0]["content"] == "用户的任务: 帮我做X")
    line("重排队列：叶子该跑，入口等孩子（共享谓词）",
         queueable(t, leaf.id) and not queueable(t, intake.id))
    # 空记录 → 报错（没有 state 检查点）
    d0 = tempfile.mkdtemp()
    tp0 = os.path.join(d0, "t.jsonl")
    write_recs(tp0, [(None, "open", {"name": "只有 open、没有 state"})])
    try:
        Store.load(tp0)
        line("空记录报错（没有 state 检查点）", False)
    except ValueError:
        line("空记录报错（没有 state 检查点）", True)
    # 多根 → 报错
    d_multi = tempfile.mkdtemp()
    tp_multi = os.path.join(d_multi, "t.jsonl")
    r1 = Node(name="任务一", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    r2 = Node(name="任务二", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    write_recs(tp_multi, [(r1.id, "state", state_rec(r1, [])),
                          (r2.id, "state", state_rec(r2, []))])
    try:
        Store.load(tp_multi)
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
    write_recs(tp_b2, [(it2.id, "state", state_rec(it2, [])),   # 入口对话里没有甲的结果
                       (a.id, "state", state_rec(a, []))])
    t_b2 = Store.load(tp_b2)
    line("B2: 投递丢失 → 加载时入口不排队（孩子未结算）",
         not queueable(t_b2, it2.id) and not queueable(t_b2, a.id))
    try:
        await run(t_b2, ScriptLLM(["甲回来了，全部完成。"]),
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    line("B2: 补投递后入口看到甲的结果（带 id 标记）",
         any("下层结论" in str(m.get("content", "")) and "id:" in str(m.get("content", ""))
             for m in msgs_of(t_b2, it2.id)))
    line("B2: 二次 load 一棵树还在", Store.load(tp_b2).root.kind == "intake")

    # B3：门槛孩子出了"未满足"结论，父节点还没结算 → 恢复按结论作废暂缓分支
    d_b3 = tempfile.mkdtemp()
    tp_b3 = os.path.join(d_b3, "trace.jsonl")
    pr3 = Node(name="父", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    gate = Node(name="门槛", accept="x（门槛 负责）", kind="leaf",
                parent=pr3.id, depth=1, gate=True)
    gate.close("未满足", "不成立", ["e"])
    pr3.children = [gate.id]
    pr3.deferred = [kid("乙")]
    write_recs(tp_b3, [(pr3.id, "state", state_rec(pr3, [])),
                       (gate.id, "state", state_rec(gate, []))])
    t_b3 = Store.load(tp_b3)
    await run(t_b3, ScriptLLM([
        ("conclude", {"verdict": "满足", "text": "门槛不成立，做不了",
                      "evidence": ["门槛"]})]))
    line("B3: 门槛未满足 → 暂缓的乙从未出生",
         all(n.name != "乙" for n in t_b3.registry.values()))
    line("B3: 作废旁白写进父节点对话",
         any("暂缓分支作废" in str(m.get("content", ""))
             for m in msgs_of(t_b3, pr3.id)))
    line("B3: 父节点接着跑出了结论", t_b3.root.verdict == "满足")

    print("=" * 80)
    print("C. 调度器续跑：一棵树跑到一半崩溃 → load → resume → 跑完")
    d2 = tempfile.mkdtemp()
    tp2 = os.path.join(d2, "trace.jsonl")
    await _run_tree(
        [("create_children", {"children": [kid("子A")]}),
         ("bash", {"cmd": "echo hi"}),
         RuntimeError("模拟崩溃")], tp2)
    t = Store.load(tp2)
    line("崩溃后 load 出一棵树", t.root.name == "根任务")
    llm2 = ScriptLLM([("conclude", {"verdict": "满足", "text": "子A做完了",
                                    "evidence": ["第1次观测"]}),
                      ("conclude", {"verdict": "满足", "text": "全部完成",
                                    "evidence": ["子A 结论"]})])
    await run(t, llm2)
    line("没跑完的节点接着跑完了",
         t.root.verdict == "满足" and t.root.conclusion == "全部完成")
    line("孩子没被重跑（bash 工具调用只有一次）",
         sum(1 for m in msgs_of(t, t.root.children[0])
             if m.get("role") == "assistant" and m.get("tool_calls")
             and any(tc.get("function", {}).get("name") == "bash"
                     for tc in m["tool_calls"])) == 1)
    line("再次 load：root 判定在", Store.load(tp2).root.verdict == "满足")

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
        await run(Store.new(intake3, seed="用户的任务: 帮我做X", trace=tp3),
                  llm3, ask=ask3)
    except EOFError:
        pass
    t3 = Store.load(tp3)
    msgs = msgs_of(t3, intake3.id)
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
        await run(Store.new(intake4, seed="用户的任务: X", trace=tp4), llm4,
                  ask=lambda t: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = Store.load(tp4)
    line("崩溃后一棵树、入口为根", t.root.kind == "intake")
    task = [n for n in t.registry.values() if n.parent == t.root.id]
    line("任务挂成入口的孩子", len(task) == 1 and task[0].kind == "leaf")
    llm5 = ScriptLLM([
        ("bash", {"cmd": "echo hi"}),
        ("conclude", {"verdict": "满足", "text": "任务X做完了", "evidence": ["第1次观测"]}),
        "跑完了。"])
    try:
        await run(t, llm5,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t2 = Store.load(tp4)
    task2 = [n for n in t2.registry.values() if n.parent == t2.root.id][0]
    line("二次 load：任务出结论", task2.verdict == "满足")
    line("入口对话带着任务结论",
         any("下层结论" in str(m.get("content", "")) for m in msgs_of(t2, t2.root.id)))

    print("=" * 80)
    print("F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果")
    d5 = tempfile.mkdtemp()
    tp5 = os.path.join(d5, "trace.jsonl")
    intake5 = Node(name="会话", kind="intake")
    write_recs(tp5, [(intake5.id, "state", state_rec(intake5, []))])
    with open(tp5, "a", encoding="utf-8") as f:
        f.write('{"kind": "state", "node": "半')     # 写了一半的一笔
    line("半行被跳过，前面的还能读", Store.load(tp5).root.kind == "intake")
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
        await run(Store.new(intake6, seed="用户的任务: 两个", trace=tp6),
                  llm6,
                  ask=lambda t: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = Store.load(tp6)
    tasks = sorted([n.name for n in t.registry.values()
                    if n.parent == t.root.id])
    line("两个任务都是入口的孩子", tasks == ["任务一", "任务二"])
    t1 = [n for n in t.registry.values() if n.name == "任务一"][0]
    t2 = [n for n in t.registry.values() if n.name == "任务二"][0]
    line("跑完的任务一有判定，任务二没有",
         t1.verdict == "满足" and not t2.verdict)
    line("任务一的孩子也有判定",
         all(n.verdict for n in t.registry.values() if n.parent == t1.id))
    llm7 = ScriptLLM([
        ("bash", {"cmd": "echo 2"}),
        ("conclude", {"verdict": "满足", "text": "任务二完成", "evidence": ["第1次观测"]}),
        "都跑完了。"])
    try:
        await run(t, llm7,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t_after = Store.load(tp6)
    t2_after = [n for n in t_after.registry.values() if n.name == "任务二"][0]
    line("恢复后任务二接着跑完", t2_after.verdict == "满足")
    line("任务一没被动过",
         [n for n in t_after.registry.values() if n.name == "任务一"][0].verdict == "满足")

    print("=" * 80)
    print("H. 增量检查点：每节点第一笔全量、之后只带新增消息，load 按序拼回全量")
    d_h = tempfile.mkdtemp()
    tp_h = os.path.join(d_h, "trace.jsonl")
    root_h = Node(name="根任务", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    llm_h = ScriptLLM([
        ("create_children", {"children": [kid("子A")]}),
        ("bash", {"cmd": "echo hi"}),
        ("conclude", {"verdict": "满足", "text": "子A做完了", "evidence": ["第1次观测"]}),
        ("conclude", {"verdict": "满足", "text": "全部完成", "evidence": ["子A 结论"]})])
    await run(Store.new(root_h, trace=tp_h), llm_h)
    events = {}                          # nid -> [state payload，按文件顺序]
    for r in Store.iter_lines(tp_h):
        if r.get("kind") == "state":
            events.setdefault(r.get("node"), []).append(r.get("payload") or {})
    child_h = root_h.children[0]
    ch = events[child_h]
    line("H: 第一笔全量、后续增量（base 递增）",
         "delta" not in ch[0] and "delta" not in ch[1]
         and ch[2].get("delta")
         and ch[0]["msgs"] == []
         and [len(e["msgs"]) for e in ch] == [0, 2, 2]
         and ch[2]["base"] == 2)
    line("H: 增量只带新增消息（不重写已写过的）",
         [len(e["msgs"]) for e in ch[1:]] == [2, 2]
         and ch[-1]["msgs"][-1]["role"] == "tool")
    t_h = Store.load(tp_h)
    msgs_h = msgs_of(t_h, child_h)
    line("H: load 拼回完整对话（assistant/tool 配对、顺序不变）",
         len(msgs_h) == 4
         and [m["role"] for m in msgs_h] == ["assistant", "tool", "assistant", "tool"]
         and msgs_h[0]["tool_calls"][0]["function"]["name"] == "bash")
    line("H: 混着老格式全量检查点也能读（delta 字段缺省 = 全量）",
         _delta_and_legacy_mix_loads(tp_h))

    print("=" * 80)
    print("I. Store.label：当前格式认入口的孩子，档案（无入口）认根本身")
    d_i = tempfile.mkdtemp()
    tp_i = os.path.join(d_i, "trace.jsonl")
    it_i = Node(name="会话", kind="intake")
    leaf_i = Node(name="子A", accept="x", kind="leaf", parent=it_i.id, depth=1)
    leaf_i.close("满足", "done", ["e"])
    it_i.children = [leaf_i.id]
    write_recs(tp_i, [(it_i.id, "state", state_rec(it_i, [])),
                      (leaf_i.id, "state", state_rec(leaf_i, []))])
    lbl = Store.label(tp_i)
    line("当前格式：任务 = 入口的孩子", "子A" in lbl and "[满足]" in lbl)
    d_j = tempfile.mkdtemp()
    tp_j = os.path.join(d_j, "trace.jsonl")
    root_j = Node(name="老任务", accept="x", kind="dispatch")
    root_j.close("阻塞", "做不了", [])
    write_recs(tp_j, [(root_j.id, "state", state_rec(root_j, []))])
    lbl2 = Store.label(tp_j)
    line("档案：没有入口，根本身就是任务", "老任务" in lbl2 and "[阻塞]" in lbl2)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


def _delta_and_legacy_mix_loads(path):
    """同一条消息先被增量检查点写过、又被老格式全量检查点覆盖 —— load 取全量。"""
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "trace.jsonl")
    n = Node(name="会话", kind="intake")
    with open(tp, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": n.to_dict(), "msgs": [],
                                         "delta": True, "base": 0}},
                           ensure_ascii=False) + "\n")
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": n.to_dict(), "msgs": [
                                {"role": "user", "content": "全量覆盖"}]}},
                           ensure_ascii=False) + "\n")
    t = Store.load(tp)
    return msgs_of(t, n.id) == [{"role": "user", "content": "全量覆盖"}]


def _recs(path):
    return list(Store.iter_lines(path))


def _load_raises(path):
    try:
        Store.load(path)
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
