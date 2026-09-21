#!/usr/bin/env python3
"""会话可续跑的定向测试。零成本、确定性（脚本化模型 + 真调度器 + 真落盘）。

核心不变量：trace.jsonl 是一场会话的完整记录（节点生命周期 + state 检查点 +
chat_* 对话）。退出（哪怕崩溃）后，`session.load` 能把它读回能继续跑的状态，
调度器接着把没跑完的节点跑完。

  A. Node 序列化往返：to_dict → from_dict 不丢任何字段
  B. session.load：从 state 检查点重建 registry / state / pending（finished 不动、
     waiting>0 等下层、其余重新排队）
  C. 调度器续跑：一棵树跑到一半"崩溃"→ load → resume → 跑完；再次 load 全部完工
  D. intake 对话落盘：chat_* 事件一条不丢；load 原样回放
  E. intake 续跑：悬空的 submit_root 被接着跑完、结论回填并落盘、对话继续
  F. 末行截断容错：崩溃写了一半的最后一行不埋掉整棵树的成果
"""

import asyncio
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from tree.intake import intake                                     # noqa: E402
from tree.llm import Message, ToolCall                             # noqa: E402
from tree.protocol.fields import Node                              # noqa: E402
from tree.runtime.scheduler import run                             # noqa: E402
from tree.runtime.session import load, session_context             # noqa: E402
from tree.runtime.trace import Trace                               # noqa: E402
from migrate_sessions import migrate                               # noqa: E402

OK = []


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(bool(cond))


def kid(name, accept="2026-12-31 收盘 >= 1"):
    return {"name": name, "detail": "d", "notes": "",
            "accept": "%s（%s 负责）" % (accept, name), "kind": "leaf",
            "gate": False, "conc_range": [1, 10]}


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
    n.attempts = [{"children": [kid("子")], "results": [], "outcome": "等下层"}]
    n.observations = [{"action": "跑了一段", "obs": "看到了输出"}]
    n.close("满足", "做完了", ["证据"], ["外部需求"])
    n2 = Node.from_dict(n.to_dict())
    line("字段原样回来", n2.name == n.name and n2.accept == n.accept
         and n2.kind == n.kind and n2.gate == n.gate)
    line("结构/历史/结局都在", n2.lineage == n.lineage
         and n2.attempts == n.attempts and n2.observations == n.observations
         and n2.verdict == "满足" and n2.conclusion == "做完了"
         and n2.evidence == ["证据"] and n2.status == "done")

    print("=" * 80)
    print("B. session.load：从 state 检查点重建现场")
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "trace.jsonl")
    # 手工构造：根已拆出一个叶子；根 waiting=1，叶子跑过一次（again）还没完工
    root = Node(name="根任务", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    leaf = Node(name="子A", accept="2026-12-31 收盘 >= 1（子A 负责）", kind="leaf",
                parent=root.id, depth=1)
    root.children = [leaf.id]
    tr = Trace(tp)
    tr.add(root.id, "state", {"node": root.to_dict(), "ready": False,
                              "finished": False, "waiting": 1, "rest": [],
                              "gate_id": None, "gate_name": None, "calls": [],
                              "contracts": [], "artifacts": [], "art_effects": {}})
    tr.add(leaf.id, "state", {"node": leaf.to_dict(), "ready": False,
                              "finished": False, "waiting": 0, "rest": [],
                              "gate_id": None, "gate_name": None,
                              "calls": [["bash", {"cmd": "echo hi"}, "hi"]],
                              "contracts": [], "artifacts": [], "art_effects": {}})
    tr.drain()
    sess = load(tp)
    line("重建出 2 个节点", len(sess["trees"][0]["registry"]) == 2)
    st = sess["trees"][0]["state"]
    line("finished 原样回来", st[root.id]["finished"] is False
         and st[leaf.id]["finished"] is False)
    line("waiting/rest/gate 原样回来", st[root.id]["waiting"] == 1
         and st[root.id]["rest"] == [] and st[root.id]["gate_id"] is None)
    line("calls 回来可解包（能力挖掘要）", st[leaf.id]["calls"] ==
         [["bash", {"cmd": "echo hi"}, "hi"]])
    line("重排规则：根 waiting>0 不排队，叶子重新排队",
         all(n != root.id for n in sess["trees"][0]["pending"])
         and leaf.id in sess["trees"][0]["pending"])
    line("in_flight = 有没完工节点的树", sess["in_flight"] is not None)

    # B2：父节点 waiting 是旧的（中断在孩子完工与父结算之间），但孩子都完工了
    # → 恢复必须按孩子状态重算，把父节点重新排队，不能让它永远等下层
    d_b2 = tempfile.mkdtemp()
    tp_b2 = os.path.join(d_b2, "trace.jsonl")
    pr = Node(name="父", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    a = Node(name="甲", accept="x（甲 负责）", kind="leaf", parent=pr.id, depth=1)
    b = Node(name="乙", accept="x（乙 负责）", kind="leaf", parent=pr.id, depth=1)
    a.close("满足", "甲好了", ["e"])
    b.close("满足", "乙好了", ["e"])
    pr.children = [a.id, b.id]
    tr_b2 = Trace(tp_b2)
    for n, done in ((pr, False), (a, True), (b, True)):
        tr_b2.add(n.id, "state", {"node": n.to_dict(), "ready": False,
                                  "finished": done, "waiting": 2, "rest": [],
                                  "gate_id": None, "gate_name": None, "calls": [],
                                  "contracts": [], "artifacts": [], "art_effects": {}})
    tr_b2.drain()
    t_b2 = load(tp_b2)["trees"][0]
    line("B2: 父节点 waiting 旧值被孩子状态重算掉（不信任存量）",
         t_b2["state"][pr.id]["waiting"] == 0
         and pr.id in t_b2["pending"]
         and all(c not in t_b2["pending"] for c in (a.id, b.id)))

    # B3：门槛孩子已出"未满足"结论，父节点还没结算 → 恢复按结论作废暂缓分支
    d_b3 = tempfile.mkdtemp()
    tp_b3 = os.path.join(d_b3, "trace.jsonl")
    pr3 = Node(name="父", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    gate = Node(name="门槛", accept="x（门槛 负责）", kind="leaf",
                parent=pr3.id, depth=1, gate=True)
    gate.close("未满足", "不成立", ["e"])
    pr3.children = [gate.id]
    tr_b3 = Trace(tp_b3)
    tr_b3.add(pr3.id, "state", {"node": pr3.to_dict(), "ready": False,
                                "finished": False, "waiting": 1,
                                "rest": [{"name": "乙"}], "gate_id": gate.id,
                                "gate_name": "门槛", "calls": [],
                                "contracts": [], "artifacts": [], "art_effects": {}})
    tr_b3.add(gate.id, "state", {"node": gate.to_dict(), "ready": False,
                                 "finished": True, "waiting": 0, "rest": [],
                                 "gate_id": None, "gate_name": None, "calls": [],
                                 "contracts": [], "artifacts": [], "art_effects": {}})
    tr_b3.drain()
    t_b3 = load(tp_b3)["trees"][0]
    line("B3: 门槛未满足 → 暂缓分支作废、父节点重新排队",
         t_b3["state"][pr3.id]["rest"] == []
         and t_b3["state"][pr3.id]["gate_id"] is None
         and pr3.id in t_b3["pending"])

    print("=" * 80)
    print("C. 调度器续跑：跑到一半崩溃 → load → resume → 跑完")
    d2 = tempfile.mkdtemp()
    tp2 = os.path.join(d2, "trace.jsonl")
    root = await _run_tree(
        [("create_children", {"children": [kid("子A")]}),
         ("bash", {"cmd": "echo hi"}),
         RuntimeError("模拟崩溃")], tp2)
    sess = load(tp2)
    t = sess["in_flight"]
    line("崩溃后还有 in_flight 树", t is not None)
    # 恢复：叶子接着 conclude，根接着 conclude
    llm2 = ScriptLLM([("conclude", {"verdict": "满足", "text": "子A做完了",
                                    "evidence": ["证据A"]}),
                      ("conclude", {"verdict": "满足", "text": "全部完成",
                                    "evidence": ["子A 结论"]})])
    await run(t["root"], llm2, Trace(tp2), registry=t["registry"],
              resume={"state": t["state"], "pending": t["pending"],
                      "root": t["root"]})
    line("没跑完的节点接着跑完了",
         t["root"].verdict == "满足" and t["root"].conclusion == "全部完成")
    line("孩子没被重跑（观测只有一次 bash）",
         len(t["registry"][t["root"].children[0]].observations) == 1)
    sess2 = load(tp2)
    line("再次 load：全部完工，没有 in_flight",
         sess2["in_flight"] is None)
    line("再次 load：root 判定在", sess2["trees"][0]["root"].verdict == "满足")

    print("=" * 80)
    print("D. intake 对话落盘：chat_* 一条不丢，load 原样回放")
    d3 = tempfile.mkdtemp()
    tp3 = os.path.join(d3, "trace.jsonl")
    tr3 = Trace(tp3)
    tr3.add(None, "chat_user", {"text": "用户的任务: 帮我做X"})
    tr3.add(None, "chat_model", {"text": "好。", "tool_calls": None})
    tr3.add(None, "chat_user", {"text": "继续"})
    wire = [{"id": "call_9", "type": "function",
             "function": {"name": "submit_root",
                          "arguments": json.dumps({"root": kid("子A")})}}]
    tr3.add(None, "chat_model", {"text": "", "tool_calls": wire})
    tr3.add(None, "chat_tool", {"tool_call_id": "call_9",
                                "content": "任务执行结果…"})
    tr3.drain()
    msgs = load(tp3)["chat_msgs"]
    line("角色顺序原样", [m["role"] for m in msgs] ==
         ["user", "assistant", "user", "assistant", "tool"])
    line("内容原样（含 seed、含工具线格式）",
         msgs[0]["content"] == "用户的任务: 帮我做X"
         and msgs[3]["tool_calls"] == wire
         and msgs[4]["tool_call_id"] == "call_9")

    print("=" * 80)
    print("E. intake 续跑：悬空的 submit_root 被接着跑完、结论回填、对话继续")
    d4 = tempfile.mkdtemp()
    tp4 = os.path.join(d4, "trace.jsonl")
    root = await _run_tree(
        [("create_children", {"children": [kid("子A")]}),
         ("bash", {"cmd": "echo hi"}),
         RuntimeError("模拟崩溃")], tp4)
    tr4 = Trace(tp4)
    tr4.add(None, "chat_user", {"text": "用户的任务: 根任务"})
    wire = [{"id": "call_1", "type": "function",
             "function": {"name": "submit_root",
                          "arguments": json.dumps({"root": {
                              "name": "根任务", "detail": "", "notes": "",
                              "accept": "2026-12-31 收盘 >= 1",
                              "kind": "dispatch", "conc_range": []}})}
             }]
    tr4.add(None, "chat_model", {"text": "好，我来。", "tool_calls": wire})
    tr4.drain()

    sess = load(tp4)
    line("读回悬空的 submit_root", sess["chat_msgs"][-1].get("tool_calls") is not None)
    line("读回 in_flight 树", sess["in_flight"] is not None)

    async def ask(t):
        if not getattr(ask, "n", 0):
            ask.n = 0
        ask.n += 1
        if ask.n == 2:
            raise EOFError            # 第二轮：模拟用户中止
        return "（用户回答 %d）" % ask.n

    env = {"trace": Trace(tp4), "budget": None,
           "workers": 2, "registry": dict(sess["in_flight"]["registry"])}
    llm2 = ScriptLLM([("conclude", {"verdict": "满足", "text": "子A做完了",
                                    "evidence": ["证据"]}),
                      ("conclude", {"verdict": "满足", "text": "全部完成",
                                    "evidence": ["子A"]}),
                      "我们继续谈。", "好。"])
    try:
        await intake(llm2, None, ask=ask, env=env, msgs=sess["chat_msgs"],
                     resume_tree=sess["in_flight"])
    except EOFError:
        pass
    env["trace"].drain()      # 对话最后几笔必须落盘才能读到
    line("树接着跑完了", sess["in_flight"]["root"].verdict == "满足")
    sess2 = load(tp4)
    roles = [m["role"] for m in sess2["chat_msgs"]]
    line("结论回填进对话并落盘（二次 load 看得到 tool 结果）",
         "tool" in roles and "任务执行结果" in sess2["chat_msgs"][2]["content"])
    line("对话继续走了一轮（用户回答落盘）",
         any(m["role"] == "user" and m["content"].startswith("（用户回答")
             for m in sess2["chat_msgs"]))
    line("角色顺序完整", roles == ["user", "assistant", "tool", "assistant", "user"])

    print("=" * 80)
    print("F. 末行截断容错：崩溃写了一半的最后一行不埋掉成果")
    d5 = tempfile.mkdtemp()
    tp5 = os.path.join(d5, "trace.jsonl")
    tr5 = Trace(tp5)
    tr5.add(root.id, "state", {"node": root.to_dict(), "ready": True,
                               "finished": False, "waiting": 0, "rest": [],
                               "gate_id": None, "gate_name": None, "calls": [],
                               "contracts": [], "artifacts": [], "art_effects": {}})
    tr5.drain()
    with open(tp5, "a", encoding="utf-8") as f:
        f.write('{"kind": "state", "node": "半')     # 写了一半的一笔
    sess5 = load(tp5)
    line("半行被跳过，前面的还能读", len(sess5["trees"]) == 1)
    line("mid-file 坏行照样炸（那是真损坏，不许吞）",
         _midfile_corrupt_raises(tp5))

    print("=" * 80)
    print("G. 一场会话多棵树：只把没跑完的那棵当 in_flight，恢复后互不影响")
    d6 = tempfile.mkdtemp()
    tp6 = os.path.join(d6, "trace.jsonl")
    r1 = Node(name="任务一", accept="2026-12-31 收盘 >= 1", kind="dispatch")
    await run(r1, ScriptLLM([("create_children", {"children": [kid("甲")]}),
                             ("conclude", {"verdict": "满足", "text": "甲好了",
                                           "evidence": ["e"]}),
                             ("conclude", {"verdict": "满足", "text": "任务一完成",
                                           "evidence": ["甲"]})]),
              Trace(tp6))
    r2 = Node(name="任务二", accept="2026-12-31 收盘 >= 2", kind="dispatch")
    try:
        await run(r2, ScriptLLM([("create_children", {"children": [kid("乙")]}),
                                 ("bash", {"cmd": "echo 2"}),
                                 RuntimeError("崩")]),
                  Trace(tp6))
    except RuntimeError:
        pass
    sess = load(tp6)
    line("两棵都在，按提交顺序", [t["root"].name for t in sess["trees"]] ==
         ["任务一", "任务二"])
    line("跑完的那棵不当 in_flight", sess["in_flight"]["root"].name == "任务二")
    line("第一棵的节点全 finished",
         all(st["finished"] for st in sess["trees"][0]["state"].values()))
    t2 = sess["in_flight"]
    await run(t2["root"], ScriptLLM([("conclude", {"verdict": "满足", "text": "乙好了",
                                                     "evidence": ["e"]}),
                                      ("conclude", {"verdict": "满足",
                                                     "text": "任务二完成",
                                                     "evidence": ["乙"]})]),
              Trace(tp6), registry=t2["registry"],
              resume={"state": t2["state"], "pending": t2["pending"],
                      "root": t2["root"]})
    sess2 = load(tp6)
    line("恢复后两棵都完工、没有 in_flight",
         sess2["in_flight"] is None and all(
             st["finished"] for st in sess2["trees"][1]["state"].values()))

    print("=" * 80)
    print("H. 老会话迁移：旧格式（task/criteria/done）跑一遍变新格式，load 能读")
    d7 = tempfile.mkdtemp()
    tp7 = os.path.join(d7, "trace.jsonl")
    tr7 = Trace(tp7)
    root_id, kid_id = "r1", "k1"
    tr7.add(root_id, "open", {"task": "创建 notes/summary.txt",
                              "criteria": "内容恰好是 alpha",
                              "depth": 0, "parent": None})
    tr7.add(kid_id, "open", {"task": "写文件", "criteria": "内容恰好是 alpha",
                             "depth": 1, "parent": root_id})
    tr7.add(kid_id, "done", {"result": "写好了"})
    tr7.add(root_id, "done", {"result": "全部完成"})
    tr7.drain()
    line("迁移前 load 读不到树（没有 state）", len(load(tp7)["trees"]) == 0)
    line("迁移跑了", migrate(tp7) is True)
    line("迁移幂等（再跑就跳过）", migrate(tp7) is False)
    s = load(tp7)
    line("迁移后读得出树", len(s["trees"]) == 1)
    t = s["trees"][0]
    line("节点键名（task/criteria）被归一到新格式",
         t["root"].name == "创建 notes/summary.txt"
         and t["root"].accept == "内容恰好是 alpha"
         and len(t["registry"]) == 2)
    line("done 被归一成满足的判定", t["root"].verdict == "满足")
    line("恢复出的树孩子链完整", t["root"].children == [kid_id])
    ctx = session_context(s["trees"])
    line("上下文带任务与判定（模型知道这场会话做过什么）",
         ctx is not None and "创建 notes/summary.txt" in ctx and "满足" in ctx)

    # H2：没跑完的树迁移后能接着跑 —— 叶子观测/分配尝试从老事件重建，
    # 恢复时叶子知道自己试过什么、根看得到"拆了谁、谁回了什么"，满足才指得到证据
    d8 = tempfile.mkdtemp()
    tp8 = os.path.join(d8, "trace.jsonl")
    tr8 = Trace(tp8)
    tr8.add("r1", "open", {"task": "量化系统", "criteria": "2026-12-31 收盘 >= 本金 x 2",
                            "depth": 0, "parent": None})
    tr8.add("k1", "open", {"task": "回测", "criteria": "2026-12-31 收盘 >= 本金 x 2（回测 负责）",
                            "depth": 1, "parent": "r1"})
    tr8.add("k1", "leaf_tool", {"tool": "bash",
                                 "args": {"cmd": "python3 backtest.py"},
                                 "obs": "收益 3%"})
    tr8.drain()
    migrate(tp8)
    t8 = load(tp8)["in_flight"]
    line("没跑完的树迁移后是 in_flight", t8 is not None)
    k1 = t8["registry"][t8["root"].children[0]]
    line("旧格式没 kind 的叶子从动作事件推断出来", k1.kind == "leaf")
    line("叶子观测从 leaf_tool 重建（恢复后知道自己试过什么）",
         k1.observations == [{"action": "python3 backtest.py", "obs": "收益 3%"}])
    line("根的分配尝试从实际子节点重建（满足的证据指得到）",
         t8["root"].attempts and t8["root"].attempts[0]["children"][0]["name"] == "回测")

    # H2 续跑：脚本化模型让叶子/根 conclude，判定不再被证据校验降级
    class S2:
        def __init__(self, script): self.script = list(script)
        async def chat(self, messages, temperature=0.2, on_delta=None,
                       on_reasoning=None, tools=None):
            self.last_usage = {"total_tokens": 0}
            action = self.script.pop(0) if self.script else ("text", "嗯。")
            if isinstance(action, str):
                return Message(text=action)
            name, args = action
            return Message(text="", tool_calls=[ToolCall(name=name, arguments=args)])

    env = {"trace": Trace(tp8), "budget": None,
           "workers": 2, "registry": dict(t8["registry"])}
    llm = S2([("conclude", {"verdict": "满足", "text": "回测好了",
                             "evidence": ["第1次观测"]}),
              ("conclude", {"verdict": "满足", "text": "全部完成",
                            "evidence": ["回测"]}),
              "我们继续。", "好。", "嗯。"])

    async def ask(tx):
        if not getattr(ask, "n", 0):
            ask.n = 0
        ask.n += 1
        if ask.n == 2:
            raise EOFError()
        return "（回答%d）" % ask.n
    try:
        await intake(llm, None, ask=ask, env=env, resume_tree=t8)
    except EOFError:
        pass
    env["trace"].drain()
    line("迁移的 in_flight 树续跑，判定不被证据校验降级",
         k1.verdict == "满足" and t8["root"].verdict == "满足")

    print("=" * 80)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


def _midfile_corrupt_raises(path):
    """坏行在文件中间（后面还有完整行）→ load 必须报错，不能悄悄跳过。"""
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"kind": "not_json"\n')          # 中间坏行
        f.write('{"kind": "state", "x": 1}\n')   # 后面还有完整行
    try:
        load(path)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
