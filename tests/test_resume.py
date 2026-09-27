#!/usr/bin/env python3
"""会话可续跑的定向测试（零成本、确定性：脚本化模型 + 真 Loop + 真落盘）。

沟通模型下"跑完/没跑完"没有 verdict，只有消息：发出 communicate 的节点最后一条是
assistant（休息，等回应），收到消息的节点最后一条是 user（醒来）。崩溃恢复后
`actionable` 用同一条判据，所以没说完的接着说完、说完的不被重跑 —— 这里守的就是这个。
"""

import asyncio
import json
import os
import sys
import tempfile
import time as _time

from harness import OK, line
from core.llm import Message, ToolCall
from core.protocol.fields import Node, node_from_dict, node_to_dict
from core.runtime import store as store_mod
from core.runtime.loop import run
from core.runtime.store import Store


def kid(name, kind="leaf"):
    return {"name": name, "detail": "d", "notes": "", "kind": kind,
            "conc_range": [1, 10]}


def state_rec(node, msgs):
    """检查点：Node 全字段 + 平铺对话，没有编排字段。"""
    return {"node": node_to_dict(node), "msgs": msgs}


def write_recs(path, recs):
    """夹具：按磁盘格式手工写一份记录（测的是 load 的读路径）。"""
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
        action = self.script.pop(0) if self.script else ("text", "嗯。")
        if isinstance(action, Exception):
            raise action
        if isinstance(action, str):
            return Message(text=action)
        name, args = action
        return Message(text="", tool_calls=[ToolCall(name=name, arguments=args)])


def comm(name, text):
    return ("communicate", {"to": "parent", "text": text})


async def main():
    print("=" * 80)
    print("A. Node 序列化往返：node_to_dict → node_from_dict 不丢任何字段")
    n = Node(name="任务", detail="详情", notes="注意", kind="leaf",
             conc_range=[1, 2], lineage=[["根", "根的详情"]])
    n2 = node_from_dict(node_to_dict(n))
    line("字段原样回来", n2.name == n.name and n2.kind == n.kind
         and n2.detail == n.detail and n2.notes == n.notes)
    line("结构都在", n2.lineage == n.lineage and n2.conc_range == [1, 2])
    line("旧档案的 accept/gate/verdict 键被丢（只认当前字段）",
         not hasattr(node_from_dict({**node_to_dict(n), "accept": "x",
                                     "verdict": "满足"}), "accept")
         and not hasattr(node_from_dict({**node_to_dict(n), "gate": True}), "gate"))

    print("=" * 80)
    print("B. load 返回一棵树（入口为根）；没根 / 多根当场报错")
    d = tempfile.mkdtemp()
    intake = Node(name="会话", kind="intake")
    leaf = Node(name="子A", kind="leaf", parent=intake.id, depth=1)
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
               [(None, "tool", {"obs": "只有非 state 记录、没有检查点"})])
    try:
        Store.load("no-such-session")
        line("空记录报错（没有 state 检查点）", False)
    except ValueError:
        line("空记录报错（没有 state 检查点）", True)
    d_multi = tempfile.mkdtemp()
    r1 = Node(name="任务一", kind="dispatch")
    r2 = Node(name="任务二", kind="dispatch")
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
    print("C. 续跑：一棵树跑到一半崩溃 → load → resume → 说完")
    d2 = tempfile.mkdtemp()
    store_mod.init(d2)
    root2 = Node(name="根任务", kind="dispatch")
    try:
        await run(Store.new(root2), ScriptLLM([
            ("create_children", {"children": [kid("子A")]}),
            ("bash", {"command": "echo hi"}),
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
        comm("子A", "子A做完了"),
        "全部完成"]))
    line("子A的回报进了根的对话",
         any("来自「子A」" in str(m.get("content", "")) for m in msgs_of(t, root2.id)))
    line("根收到回报后把这一轮交出去了（休息）",
         msgs_of(t, root2.id)[-1].get("role") == "assistant")
    line("孩子没被重跑（bash 工具调用只有一次）",
         sum(1 for m in msgs_of(t, cid)
             if m.get("role") == "assistant" and m.get("tool_calls")
             and any(tc.get("function", {}).get("name") == "bash"
                     for tc in m["tool_calls"])) == 1)
    line("再次 load：回报还在对话里",
         any("来自「子A」" in str(m.get("content", ""))
             for m in msgs_of(Store.load(root2.id), root2.id)))

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
        ("bash", {"command": "echo hi"}),
        comm("任务X", "任务X做完了"),
        "跑完了。"])
    try:
        await run(t, llm5, ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t2 = Store.load(intake4.id)
    line("任务把回报发给了入口",
         any("来自「任务X」" in str(m.get("content", ""))
             for m in msgs_of(t2, t2.root.id)))

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
        comm("甲", "甲好了"),
        comm("任务一", "任务一完成"),
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
    line("任务一回报过、任务二没有",
         _sent_comm(msgs_of(t, t1.id)) and not _sent_comm(msgs_of(t, t2.id)))
    llm7 = ScriptLLM([
        ("bash", {"command": "echo 2"}),
        comm("任务二", "任务二完成"),
        "都跑完了。"])
    try:
        await run(t, llm7, ask=lambda tx: (_ for _ in ()).throw(EOFError()))
    except EOFError:
        pass
    t_after = Store.load(intake6.id)
    t2_after = [n for n in t_after.registry.values() if n.name == "任务二"][0]
    line("恢复后任务二接着回报", _sent_comm(msgs_of(t_after, t2_after.id)))
    line("任务一没被动过",
         _sent_comm(msgs_of(t_after, t1.id))
         and len(msgs_of(t_after, t1.id)) == len(msgs_of(t, t1.id)))

    print("=" * 80)
    print("H. 增量检查点：每节点第一笔全量、之后只带新增消息，load 按序拼回全量")
    d_h = tempfile.mkdtemp()
    store_mod.init(d_h)
    root_h = Node(name="根任务", kind="dispatch")
    llm_h = ScriptLLM([
        ("create_children", {"children": [kid("子A")]}),
        ("bash", {"command": "echo hi"}),
        comm("子A", "子A做完了"),
        "全部完成"])
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
         and ch[3].get("delta") and ch[3]["base"] == 2
         and ch[4].get("delta") and ch[4]["base"] == 3)
    t_h = Store.load(root_h.id)
    msgs_h = msgs_of(t_h, child_h)
    line("H: load 拼回完整对话（任务 + asst/tool 配对 + 沟通，顺序不变）",
         [m["role"] for m in msgs_h] == ["user", "assistant", "tool",
                                         "assistant"]
         and msgs_h[1]["tool_calls"][0]["function"]["name"] == "bash"
         and msgs_h[3]["tool_calls"][0]["function"]["name"] == "communicate")
    line("H: 混着老格式全量检查点也能读（delta 字段缺省 = 全量）",
         _delta_and_legacy_mix_loads())

    print("=" * 80)
    print("I. 会话摘要（Store.roots）：当前格式认入口的孩子，档案（无入口）认根本身")
    d_i = tempfile.mkdtemp()
    it_i = Node(name="会话", kind="intake")
    leaf_i = Node(name="子A", kind="leaf", parent=it_i.id, depth=1)
    it_i.children = [leaf_i.id]
    leaf_msgs = [{"role": "assistant", "content": None,
                  "tool_calls": [{"id": "1", "type": "function",
                                  "function": {"name": "communicate",
                                               "arguments": "{}"}}]}]
    load_tree(d_i, it_i, [(it_i.id, "state", state_rec(it_i, [])),
                          (leaf_i.id, "state", state_rec(leaf_i, leaf_msgs))])
    lbl = _label_of(it_i.id)
    line("当前格式：任务 = 入口的孩子，回报过 = 已回报",
         "子A" in lbl and "[已回报]" in lbl, lbl)
    d_j = tempfile.mkdtemp()
    root_j = Node(name="老任务", kind="dispatch")
    load_tree(d_j, root_j, [(root_j.id, "state", state_rec(root_j, []))])
    lbl2 = _label_of(root_j.id)
    line("档案：没有入口，根本身就是任务；没回报 = 运行中",
         "老任务" in lbl2 and "[运行中]" in lbl2, lbl2)

    print("=" * 80)
    print("J. 一场会话多个任务：摘要认最新谈成的那个任务")
    d_m = tempfile.mkdtemp()
    it_m = Node(name="会话", kind="intake")
    first = Node(name="第一个任务", kind="dispatch", parent=it_m.id, depth=1)
    second = Node(name="第二个任务", kind="dispatch", parent=it_m.id, depth=1)
    it_m.children = [first.id, second.id]
    first_msgs = [{"role": "assistant", "content": None,
                   "tool_calls": [{"id": "1", "type": "function",
                                   "function": {"name": "communicate",
                                                "arguments": "{}"}}]}]
    load_tree(d_m, it_m, [(it_m.id, "state", state_rec(it_m, [])),
                          (first.id, "state", state_rec(first, first_msgs)),
                          (second.id, "state", state_rec(second, []))])
    lbl_m = _label_of(it_m.id)
    line("认最新那个（第二个），不是第一个", "第二个任务" in lbl_m
         and "第一个任务" not in lbl_m and "共 2 个任务" in lbl_m, lbl_m)

    print("=" * 80)
    print("K. 记录读路径：非 state 记录里嵌了同形键、真 state 用紧凑分隔符 —— 该读到的还是它")
    line("嵌入 kind 的非 state 记录不算 state；紧凑分隔符写的 state 照样认",
         _lookalike_records_are_ignored())

    print("=" * 80)
    print("L. 同一秒里连开两场会话不撞进同一条记录")
    line("目录名带随机、两场各自可读回来",
         _two_sessions_in_one_second_stay_apart())

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


def _sent_comm(msgs):
    return any(m.get("role") == "assistant" and m.get("tool_calls")
               and any((tc.get("function") or {}).get("name") == "communicate"
                       for tc in m["tool_calls"])
               for m in msgs)


class _FrozenSecond:
    """把 `%m%d-%H%M%S` 冻住，其余照真 time —— 用来守"同一秒连开两场不撞同一条记录"。"""

    @staticmethod
    def strftime(fmt, *args):
        return "0101-000000" if fmt == "%m%d-%H%M%S" else _time.strftime(fmt, *args)

    def __getattr__(self, name):
        return getattr(_time, name)


def _label_of(sid):
    """按会话 id 取摘要 —— 不靠 `roots()` 的顺序（它按 mtime 倒序，不是"被测的那场"）。"""
    return next(t for sid_, t in Store.roots() if sid_ == sid)


def _two_sessions_in_one_second_stay_apart():
    """目录名若只由"时间"决定，同一秒连开两场会写进同一条记录：两个根 → 谁都读不回来。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    old = store_mod.time
    store_mod.time = _FrozenSecond()
    try:
        a = Store.new(Node(name="会话", kind="intake"), seed="s")
        b = Store.new(Node(name="会话", kind="intake"), seed="s")
    finally:
        store_mod.time = old
    return a.path != b.path and len(Store.roots()) == 2


def _lookalike_records_are_ignored():
    """病态输入：`tool` 记录的 payload 里嵌了 `{"kind": "state"}`，真 state 用紧凑分隔符写。

    按原始行做子串匹配的读法会选错：要么把 tool 记录当 state（它的 payload 里没有 node），
    要么漏掉用紧凑分隔符写的真 state —— 两种都会让这场会话读不回来。
    """
    d = tempfile.mkdtemp()
    store_mod.init(d)
    n = Node(name="真任务", kind="dispatch")
    p = os.path.join(d, "runs", "t", "trace.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "tool", "node": "别的节点",
                            "payload": {"tool": "bash", "args": {"kind": "state"}}},
                           ensure_ascii=False) + "\n")
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": node_to_dict(n), "msgs": []}},
                           ensure_ascii=False, separators=(",", ":")) + "\n")
    try:
        st = Store.load(n.id)
    except ValueError:
        return False
    return st.root.name == "真任务"


def _delta_and_legacy_mix_loads():
    """同一条对话先被增量检查点写过、又被老格式全量覆盖 —— load 取全量。"""
    d = tempfile.mkdtemp()
    store_mod.init(d)
    n = Node(name="会话", kind="intake")
    p = os.path.join(d, "runs", "t", "trace.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": node_to_dict(n), "msgs": [],
                                        "delta": True, "base": 0}},
                           ensure_ascii=False) + "\n")
        f.write(json.dumps({"kind": "state", "node": n.id,
                            "payload": {"node": node_to_dict(n), "msgs": [
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
