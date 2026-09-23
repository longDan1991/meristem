#!/usr/bin/env python3
"""会话可续跑的定向测试。零成本、确定性（脚本化模型 + 真 Loop + 真落盘）。

核心不变量：**一场会话 = 一棵树**，入口节点（kind="intake"）是根，谈成的任务
都是它的孩子。`state` 检查点只有两样：Node 全字段 + 平铺对话（msgs）—— 没有
任何编排字段。退出（哪怕崩溃）后 `Store.load` 读回这**一棵树**，直接丢给
`runtime.loop.run` 接着跑：

  · 该不该跑由 `plan.actionable` 从数据推导（msgs 非空 + 最后一条不是 assistant）。

  A. Node 序列化往返：to_dict → from_dict 不丢任何字段
  B. load 返回一棵树；没根 / 多根当场报错
  C. 续跑：一棵树跑到一半"崩溃" → load → resume → 跑完
  D. 入口对话 = 根节点的 msgs（种子进根对话）
  E. 整场会话（入口 + 任务）崩溃 → load 一棵树 → resume → 全完工
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
from core.llm import Message, ToolCall                        # noqa: E402
from core.protocol.fields import Node                         # noqa: E402
from core.runtime import store as store_mod                   # noqa: E402
from core.runtime.loop import run                             # noqa: E402
from core.runtime.store import Store                          # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-52s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def kid(name, accept="2026-12-31 收盘 >= 1", kind="leaf", gate=False):
    return {"name": name, "detail": "d", "notes": "",
            "accept": "%s（%s 负责）" % (accept, name), "kind": kind,
            "gate": gate, "conc_range": [1, 10]}


def state_rec(node, msgs):
    """检查点：Node 全字段 + 平铺对话，没有编排字段。"""
    return {"node": node.to_dict(), "msgs": msgs}


def write_recs(path, recs):
    """测试夹具：按磁盘格式手工写一份记录（测的是 load 的读路径）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for nid, kind, payload in recs:
            f.write(json.dumps({"t": 0, "node": nid, "kind": kind,
                                "payload": payload}, ensure_ascii=False) + "\n")


def load_tree(d, root, recs):
    """夹具：记录根初始化到 d、写一份记录，再读回一棵树。"""
    store_mod.init(d)
    write_recs(os.path.join(d, "runs", "t", "trace.jsonl"), recs)
    return Store.load(root.id)


def msgs_of(store, nid):
    return store.dialogue(nid).to_list()


class ScriptLLM:
    """按脚本回话：tuple = 工具调用，str = 说一句话，Exception = 抛（模拟崩溃）。"""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    async def chat(self, messages, temperature=0.2, on_delta=None,
                   on_reasoning=None, tools=None):
        self.calls += 1
        self.last_usage = {"total_tokens": 0}
        action = self.script.pop(0) if self.script else ("text", "嗯。")
        if isinstance(action, Exception):
            raise action
        if isinstance(action, str):
            return Message(text=action)
        name, args = action
        return Message(text="", tool_calls=[ToolCall(name=name, arguments=args)])


async def main():
    print("=" * 80)
    print("A. Node 序列化往返：to_dict → from_dict 不丢任何字段")
    n = Node(name="任务", detail="详情", notes="注意", accept="2026-12-31 收盘 >= 1",
             kind="leaf", gate=True, conc_range=[1, 2],
             lineage=[["根", "根的详情"]])
    n.close("满足", "做完了", ["证据"], ["外部需求"])
    n2 = Node.from_dict(n.to_dict())
    line("字段原样回来", n2.name == n.name and n2.accept == n.accept
         and n2.kind == n.kind and n2.gate == n.gate)
    line("结构/结局都在", n2.lineage == n.lineage
         and n2.verdict == "满足" and n2.conclusion == "做完了"
         and n2.evidence == ["证据"])

    print("=" * 80)
    print("B. load 返回一棵树（入口为根）；没根 / 多根当场报错")
    d = tempfile.mkdtemp()
    intake = Node(name="会话", kind="intake")
    leaf = Node(name="子A", accept="2026-12-31 收盘 >= 1（子A 负责）", kind="leaf",
                parent=intake.id, depth=1)
    intake.children = [leaf.id]
    t = load_tree(d, intake, [
        (intake.id, "state", state_rec(intake, [
            {"role": "user", "content": "用户的任务: 帮我做X"}])),
        (leaf.id, "state", state_rec(leaf, [
            {"role": "user", "content": "name: 子A"}]))])
    line("根是入口节点", t.root.kind == "intake" and t.root.name == "会话")
    line("检查点只有 node + msgs（没有编排字段）",
         all(set((r.get("payload") or {}).keys()) <= {"node", "msgs", "delta", "base"}
             for r in Store.iter_lines(os.path.join(d, "runs", "t", "trace.jsonl"),
                                       kinds=("state",))))
    line("入口对话就是根的 msgs",
         msgs_of(t, intake.id)[0]["content"] == "用户的任务: 帮我做X")
    d0 = tempfile.mkdtemp()
    store_mod.init(d0)
    write_recs(os.path.join(d0, "runs", "t", "trace.jsonl"),
               [(None, "open", {"name": "只有 open、没有 state"})])
    try:
        Store.load("no-such-session")
        line("空记录报错（没有 state 检查点）", False)
    except ValueError:
        line("空记录报错（没有 state 检查点）", True)
    d_multi = tempfile.mkdtemp()
    r1 = Node(name="任务一", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    r2 = Node(name="任务二", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    store_mod.init(d_multi)
    write_recs(os.path.join(d_multi, "runs", "t", "trace.jsonl"),
               [(r1.id, "state", state_rec(r1, [])),
                (r2.id, "state", state_rec(r2, []))])
    try:
        Store.load(r1.id)
        line("多个根报错（不是入口为根的一棵树）", False)
    except ValueError:
        line("多个根报错（不是入口为根的一棵树）", True)

    print("=" * 80)
    print("C. 续跑：一棵树跑到一半崩溃 → load → resume → 跑完")
    d2 = tempfile.mkdtemp()
    store_mod.init(d2)
    root2 = Node(name="根任务", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    try:
        await run(Store.new(root2), ScriptLLM([
            ("create_children", {"children": [kid("子A")]}),
            ("bash", {"cmd": "echo hi"}),
            RuntimeError("模拟崩溃")]))
    except RuntimeError:
        pass
    t = Store.load(root2.id)
    line("崩溃后 load 出一棵树", t.root.name == "根任务")
    cid = t.root.children[0]
    line("崩溃前分配 + 子A做过一次观测",
         any(m.get("role") == "assistant" and m.get("tool_calls")
             and any(tc.get("function", {}).get("name") == "bash"
                     for tc in m["tool_calls"]) for m in msgs_of(t, cid)))
    await run(t, ScriptLLM([
        ("conclude", {"verdict": "满足", "text": "子A做完了", "evidence": ["第1次观测"]}),
        ("conclude", {"verdict": "满足", "text": "全部完成", "evidence": ["子A"]})]))
    line("没跑完的节点接着跑完了",
         t.root.verdict == "满足" and t.root.conclusion == "全部完成")
    line("孩子没被重跑（bash 工具调用只有一次）",
         sum(1 for m in msgs_of(t, cid)
             if m.get("role") == "assistant" and m.get("tool_calls")
             and any(tc.get("function", {}).get("name") == "bash"
                     for tc in m["tool_calls"])) == 1)
    line("再次 load：root 判定在", Store.load(root2.id).root.verdict == "满足")

    print("=" * 80)
    print("D. 入口对话 = 根节点的 msgs（新会话的种子进根对话）")
    d3 = tempfile.mkdtemp()
    store_mod.init(d3)
    intake3 = Node(name="会话", kind="intake")
    llm3 = ScriptLLM(["你要做什么？", "明白了。"])
    asks = iter(["帮我做X", EOFError()])

    async def ask3(t):
        a = next(asks)
        if isinstance(a, Exception):
            raise a
        return a
    try:
        await run(Store.new(intake3, seed="用户的任务: 帮我做X"), llm3, ask=ask3)
    except EOFError:
        pass
    t3 = Store.load(intake3.id)
    msgs = msgs_of(t3, intake3.id)
    line("种子进根对话", msgs[0]["content"] == "用户的任务: 帮我做X")
    line("入口回复与用户的话都在根对话里",
         msgs[1]["content"] == "你要做什么？"
         and any(m.get("role") == "user" and m.get("content") == "帮我做X"
                 for m in msgs)
         and len(msgs) == 4)          # 第二次 assistant 已入账，ask 才被中止

    print("=" * 80)
    print("E. 整场会话（入口 + 任务）崩溃 → load 一棵树 → resume → 全完工")
    d4 = tempfile.mkdtemp()
    store_mod.init(d4)
    intake4 = Node(name="会话", kind="intake")
    llm4 = ScriptLLM([
        ("submit_root", {"root": kid("任务X", kind="leaf")}),
        RuntimeError("模拟崩溃")])
    try:
        await run(Store.new(intake4, seed="用户的任务: X"), llm4,
                  ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = Store.load(intake4.id)
    line("崩溃后一棵树、入口为根", t.root.kind == "intake")
    task = [n for n in t.registry.values() if n.parent == t.root.id]
    line("任务挂成入口的孩子", len(task) == 1 and task[0].kind == "leaf")
    llm5 = ScriptLLM([
        ("bash", {"cmd": "echo hi"}),
        ("conclude", {"verdict": "满足", "text": "任务X做完了",
                      "evidence": ["第1次观测"]}),
        "跑完了。"])
    try:
        await run(t, llm5, ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t2 = Store.load(intake4.id)
    task2 = [n for n in t2.registry.values() if n.parent == t2.root.id][0]
    line("二次 load：任务出结论", task2.verdict == "满足")
    line("入口对话带着任务结论",
         any("下层结论" in str(m.get("content", "")) for m in msgs_of(t2, t2.root.id)))

    print("=" * 80)
    print("F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果")
    d5 = tempfile.mkdtemp()
    intake5 = Node(name="会话", kind="intake")
    p5 = load_tree(d5, intake5,
                   [(intake5.id, "state", state_rec(intake5, []))]).path
    with open(p5, "a", encoding="utf-8") as f:
        f.write('{"kind": "state", "node": "半')
    line("半行被跳过，前面的还能读", Store.load(intake5.id).root.kind == "intake")
    line("mid-file 坏行照样炸（那是真损坏，不许吞）",
         _midfile_corrupt_raises(p5, intake5.id))

    print("=" * 80)
    print("G. 一场会话多个任务 = 一棵树多个孩子，只有没跑完的被接着跑")
    d6 = tempfile.mkdtemp()
    store_mod.init(d6)
    intake6 = Node(name="会话", kind="intake")
    llm6 = ScriptLLM([
        ("submit_root", {"root": kid("任务一", kind="dispatch")}),
        ("create_children", {"children": [kid("甲")]}),
        ("conclude", {"verdict": "满足", "text": "甲好了", "evidence": ["e"]}),
        ("conclude", {"verdict": "满足", "text": "任务一完成", "evidence": ["甲"]}),
        ("submit_root", {"root": kid("任务二", kind="leaf")}),
        RuntimeError("崩")])
    try:
        await run(Store.new(intake6, seed="用户的任务: 两个"), llm6,
                  ask=lambda t: (_ for _ in ()).throw(EOFError()))
    except (RuntimeError, EOFError):
        pass
    t = Store.load(intake6.id)
    tasks = sorted([n.name for n in t.registry.values() if n.parent == t.root.id])
    line("两个任务都是入口的孩子", tasks == ["任务一", "任务二"])
    t1 = [n for n in t.registry.values() if n.name == "任务一"][0]
    t2 = [n for n in t.registry.values() if n.name == "任务二"][0]
    line("跑完的任务一有判定，任务二没有",
         t1.verdict == "满足" and not t2.verdict)
    llm7 = ScriptLLM([
        ("bash", {"cmd": "echo 2"}),
        ("conclude", {"verdict": "满足", "text": "任务二完成",
                      "evidence": ["第1次观测"]}),
        "都跑完了。"])
    try:
        await run(t, llm7, ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t_after = Store.load(intake6.id)
    t2_after = [n for n in t_after.registry.values() if n.name == "任务二"][0]
    line("恢复后任务二接着跑完", t2_after.verdict == "满足")
    line("任务一没被动过",
         [n for n in t_after.registry.values() if n.name == "任务一"][0].verdict
         == "满足")

    print("=" * 80)
    print("H. 增量检查点：每节点第一笔全量、之后只带新增消息，load 按序拼回全量")
    d_h = tempfile.mkdtemp()
    store_mod.init(d_h)
    root_h = Node(name="根任务", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    llm_h = ScriptLLM([
        ("create_children", {"children": [kid("子A")]}),
        ("bash", {"cmd": "echo hi"}),
        ("conclude", {"verdict": "满足", "text": "子A做完了", "evidence": ["第1次观测"]}),
        ("conclude", {"verdict": "满足", "text": "全部完成", "evidence": ["子A"]})])
    st_h = await run(Store.new(root_h), llm_h)
    events = {}
    for r in Store.iter_lines(st_h.path):
        if r.get("kind") == "state":
            events.setdefault(r.get("node"), []).append(r.get("payload") or {})
    child_h = root_h.children[0]
    ch = events[child_h]
    line("H: 第一笔全量、任务消息一笔、之后增量（base 递增）",
         "delta" not in ch[0] and ch[0]["msgs"] == []
         and "delta" not in ch[1]
         and [m["role"] for m in ch[1]["msgs"]] == ["user"]
         and ch[2].get("delta") and ch[2]["base"] == 1
         and ch[3].get("delta") and ch[3]["base"] == 2)
    t_h = Store.load(root_h.id)
    msgs_h = msgs_of(t_h, child_h)
    line("H: load 拼回完整对话（任务 + asst/tool 配对、顺序不变）",
         [m["role"] for m in msgs_h] == ["user", "assistant", "tool",
                                         "assistant"]
         and msgs_h[1]["tool_calls"][0]["function"]["name"] == "bash")
    line("H: 混着老格式全量检查点也能读（delta 字段缺省 = 全量）",
         _delta_and_legacy_mix_loads())

    print("=" * 80)
    print("I. Store.label：当前格式认入口的孩子，档案（无入口）认根本身")
    d_i = tempfile.mkdtemp()
    it_i = Node(name="会话", kind="intake")
    leaf_i = Node(name="子A", accept="x", kind="leaf", parent=it_i.id, depth=1)
    leaf_i.close("满足", "done", ["e"])
    it_i.children = [leaf_i.id]
    p_i = load_tree(d_i, it_i, [(it_i.id, "state", state_rec(it_i, [])),
                                (leaf_i.id, "state", state_rec(leaf_i, []))]).path
    lbl = Store.label(p_i)
    line("当前格式：任务 = 入口的孩子", "子A" in lbl and "[满足]" in lbl)
    d_j = tempfile.mkdtemp()
    root_j = Node(name="老任务", accept="x", kind="dispatch")
    root_j.close("阻塞", "做不了", [])
    p_j = load_tree(d_j, root_j, [(root_j.id, "state", state_rec(root_j, []))]).path
    lbl2 = Store.label(p_j)
    line("档案：没有入口，根本身就是任务", "老任务" in lbl2 and "[阻塞]" in lbl2)

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


def _delta_and_legacy_mix_loads():
    """同一条对话先被增量检查点写过、又被老格式全量覆盖 —— load 取全量。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    n = Node(name="会话", kind="intake")
    p = os.path.join(d, "runs", "t", "trace.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": n.to_dict(), "msgs": [],
                                        "delta": True, "base": 0}},
                           ensure_ascii=False) + "\n")
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": n.to_dict(), "msgs": [
                                {"role": "user", "content": "全量覆盖"}]}},
                           ensure_ascii=False) + "\n")
    t = Store.load(n.id)
    return msgs_of(t, n.id) == [{"role": "user", "content": "全量覆盖"}]


def _midfile_corrupt_raises(path, session_id):
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"kind": "not_json"\n')
        f.write('{"kind": "state", "x": 1}\n')
    try:
        Store.load(session_id)
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
