#!/usr/bin/env python3
"""形式化协议的定向测试。零成本、确定性（脚本化假模型）。

  A. 门槛不成立 → 兄弟子任务永不启动，分配节点的历史里留下"门槛不成立"
  B. 门槛通过   → 兄弟此时才启动
  C. 子任务验收标准丢了可测物理量 → 这次分配当场被代码拒，并记进"本层已有尝试"
  D. 判定"满足"但证据指不到任何真实东西 → 降级为"未满足"
  E. 次数不限：反复"再做一次"不被任何计数器阻止，而每次尝试都看得见
  F. 必填项缺一个 → 当场被拒；长字段原样通过（代码不做任何长度检查）
  G. 分配节点没有 execute 分支 ——"不拆"必须是派一个叶子
  H. 检索键：分配节点一出生就自动查老树，叶子只查能力库
  I. 同构：收到的行首 == 自己要写的键；文档点名的段落 == 真渲染的段落
"""

import asyncio
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.llm import Message, ToolCall                      # noqa: E402
from tree.protocol.fields import Node                # noqa: E402
from tree.runtime.trace import Trace                 # noqa: E402
from tree.prompts import PROMPT                      # noqa: E402
from tree.runtime import scheduler as R              # noqa: E402

C_ANCHORED = "账户权益在2026-12-31收盘 >= 本金 x 2"


class FakeIndex:
    """假的老树索引：只记下程序发了什么查询。"""

    def __init__(self):
        self.qs = []

    def search(self, qs, workspace=None):
        self.qs.append(list(qs))
        self.workspace = workspace
        return [], "[先例] 假的老树"


def kid(name, accept, kind="leaf", gate=False, keywords=None, rng=None,
        detail="按上层要求把这件事做完", notes=""):
    """一个合规的子任务形式（所有必填项都在）。"""
    return {"name": name, "detail": detail, "notes": notes, "accept": accept,
            "kind": kind, "gate": gate,
            "keywords": keywords or ["kw-" + name, "2026-12-31"],
            "conc_range": rng or [100, 500]}


def run_code(code):
    return Message(tool_calls=[ToolCall(name="run_code", arguments={"code": code})])


def create(children):
    return Message(tool_calls=[ToolCall(name="create_children",
                                        arguments={"children": children})])


def conclude(**kw):
    return Message(tool_calls=[ToolCall(name="conclude", arguments=kw)])


class Scripted:
    """按渲染出来的形式字段回话（发工具调用）。mode 决定行为。"""

    def __init__(self, mode):
        self.mode, self.calls, self.last_usage = mode, 0, {}

    async def chat(self, messages, temperature=0.2, tools=None):
        self.calls += 1
        # 叶子（选项 B）是对话：user 是基础形式字段（render_wire），
        # 观测走 role=tool 消息 —— 所以找 user 消息，不用 messages[-1]。
        user = next((m["content"] for m in messages
                     if m.get("role") == "user"), "")
        name = (re.search(r"^name:\s*(.+)$", user, re.M) or [None, "?"])[1].strip()
        # "是不是第一次"：叶子看有没有 tool 消息（还没有 = 该动手），
        # 分配节点看"本层已有尝试"是不是空的（它是单发 render，永远没有 tool）。
        if "手上的东西" in user:
            fresh = not any(m.get("role") == "tool" for m in messages)
        else:
            fresh = "(还没有)" in user
        m = re.search(r"本层已有尝试: 共 (\d+) 次", user)
        attempts = int(m.group(1)) if m else 0

        if "手上的东西" in user:                        # ── 叶子
            if self.mode == "loop":
                # 永远做同一个动作，观测也永远一样
                return run_code("print(bash(cmd='echo same'))")
            if name.startswith("GATE"):
                if self.mode == "gate_pass" and fresh:
                    return run_code("print(bash(cmd='echo gate-ok'))")
                v = "满足" if self.mode == "gate_pass" else "阻塞"
                ev = ["第1次观测"] if v == "满足" else []
                return conclude(verdict=v,
                                text="门槛测过了" if v == "满足"
                                else "开户需要人到场，不在工具里",
                                evidence=ev)
            if name.startswith("NOEV"):
                return conclude(verdict="满足", text="我发誓真的做完了",
                                evidence=["凭良心说的"])
            if name.startswith("EARLY"):
                # 第一轮拆出来的孩子：真的做过、真的出过结论
                if fresh:
                    return run_code("print(bash(cmd='echo early'))")
                return conclude(verdict="满足", text="早期子任务干完了",
                                evidence=["第1次观测"])
            if self.mode == "deep":
                if fresh:
                    return run_code("print(bash(cmd='echo deep'))")
                return conclude(verdict="满足", text="收盘价读到了",
                                evidence=["第1次观测"])
            if self.mode == "many" and fresh:
                return run_code("print(bash(cmd='echo sib'))")
            return conclude(verdict="满足", text="兄弟干完了",
                            evidence=["第1次观测"])

        # ── 分配节点
        if self.mode == "deep":
            # 三层：ROOT(分配) → MID(分配) → LEAF(叶子)，验意图链真的逐层加长
            if name == "MID":
                if fresh:
                    return create([kid(
                        "LEAF", "2026-12-31 的权益读数已取到",
                        detail="读收盘价")])
                return conclude(verdict="满足", text="叶子回来了",
                                evidence=["LEAF"])
            if not fresh:
                return conclude(verdict="满足", text="都回来了", evidence=["MID"])
            return create([kid(
                "MID", "2026-12-31 的权益读数已取到", kind="dispatch",
                detail="先把数据这条线摸清楚",
                keywords=["akshare", "回测", "2026-12-31"])])
        if self.mode == "recite":
            # 真跑过的孩子回来后，又发了一次用不了的分配（被代码拒），
            # 那次进历史时**没有 results**，最后才引第一轮的孩子出结论。
            if attempts == 0:
                return create([kid("EARLY", "2026-12-31 的权益读数已取到")])
            if attempts == 1:
                return Message(text="我什么都不想调")   # 没调任何工具 → 被拒
            return conclude(verdict="满足", text="下层都回来了", evidence=["EARLY"])
        if self.mode == "many":
            if attempts >= 3:
                return conclude(verdict="未满足", text="试了三种拆法都不行",
                                evidence=[])
            return create([kid(
                "SIB%d" % (attempts + 1),
                "2026-12-31 的权益读数已取到（第%d次尝试）" % (attempts + 1))])
        if not fresh:
            return conclude(verdict="满足", text="下层都回来了", evidence=["GATE"])
        if self.mode == "anchor":
            return create([
                {"name": "跑通就行", "detail": "把代码跑起来", "notes": "",
                 "accept": "代码能跑起来", "kind": "leaf",
                 "keywords": ["跑通"], "conc_range": [100, 500]}])
        if self.mode == "missing":                  # 故意缺 accept（schema 拒）
            return create([{
                "name": "缺验收标准的孩子", "detail": "d", "kind": "leaf",
                "keywords": ["x"], "conc_range": [100, 500]}])
        if self.mode == "badkind":                  # kind 写成示例里的 "dispatch|leaf"
            s = kid("kind 写错的孩子", "2026-12-31 的权益读数已取到")
            s["kind"] = "dispatch|leaf"
            return create([s])
        if self.mode == "badrange":                 # 下限比上限大
            return create([{
                "name": "区间写错的孩子", "detail": "d", "notes": "",
                "accept": "2026-12-31 的权益读数已取到", "kind": "leaf",
                "keywords": ["x"], "conc_range": [500, 100]}])
        gate = (self.mode != "noevidence")
        kids = []
        if gate:
            kids.append(kid("GATE", "2026-12-31 之前存在一个正期望策略", gate=True))
        sib_name = "NOEV" if self.mode == "noevidence" else "SIB"
        kids.append(kid(sib_name, "截至 2026-12-31 系统已就绪"))
        if self.mode == "long":
            kids[0]["detail"] = "很长" * 200
        if self.mode == "note":
            kids[0]["notes"] = "写在字段里放不下的判断依据。" * 50
        return create(kids)


def go(mode, accept=C_ANCHORED, kind="dispatch", index=None):
    d = tempfile.mkdtemp()
    trace = Trace(os.path.join(d, "t.jsonl"))
    root = Node(name="ROOT", accept=accept, kind=kind)
    reg, llm = {}, Scripted(mode)
    cwd = os.getcwd()          # 叶子会跑真的 bash：别污染项目目录
    os.chdir(d)
    try:
        asyncio.run(R.run(root, llm, trace, registry=reg,
                          workers=2, index=index))
    finally:
        os.chdir(cwd)
    recs = [json.loads(x) for x in open(os.path.join(d, "t.jsonl"))]
    return root, reg, recs, d


def kinds(recs):
    return [r["payload"]["name"] for r in recs if r["kind"] == "open"]


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    return bool(cond)


def main():
    ok = True

    print("=" * 80)
    print("A. 门槛不成立 → 兄弟永不启动")
    root, reg, recs, _ = go("gate_fail")
    print("  启动的节点: %s" % kinds(recs))
    gf = [r for r in recs if r["kind"] == "gate_failed"]
    print("  根的尝试记录: %s" % json.dumps(root.attempts, ensure_ascii=False))
    ok &= line("SIB 从未启动", not any(k == "SIB" for k in kinds(recs)))
    ok &= line("留下 gate_failed 记录", bool(gf))
    ok &= line("历史里写明门槛不成立", "门槛不成立" in str(root.attempts))
    ok &= line("根出了结论", bool(root.verdict), root.verdict)

    print("=" * 80)
    print("B. 门槛通过 → 兄弟此时才启动")
    root, reg, recs, _ = go("gate_pass")
    print("  启动的节点: %s" % kinds(recs))
    ok &= line("GATE 通过后 SIB 启动了", any(k == "SIB" for k in kinds(recs)))
    ok &= line("留下 gate_passed 记录", any(r["kind"] == "gate_passed" for r in recs))

    print("=" * 80)
    print("C. 子任务验收标准丢了可测物理量 → 这次分配被代码拒")
    root, reg, recs, _ = go("anchor")
    drift = [r for r in recs if r["kind"] == "criterion_drift"]
    print("  根的尝试记录: %s" % json.dumps(root.attempts, ensure_ascii=False))
    ok &= line("留下 criterion_drift 记录", bool(drift))
    ok &= line("被拒这件事进了本层历史", "rejected" in str(root.attempts))
    ok &= line("没有启动任何子节点",
               not any(r["kind"] == "open" and r["payload"].get("parent") for r in recs))

    print("=" * 80)
    print("D. 判定「满足」但证据指不到真实东西 → 降级")
    root, reg, recs, _ = go("noevidence")
    down = [r for r in recs if r["kind"] == "verdict_downgraded"]
    noev = [n for n in reg.values() if n.name == "NOEV"][0]
    print("  NOEV 的判定: %s | %s" % (noev.verdict, noev.conclusion))
    ok &= line("被降级并留下记录", bool(down))
    ok &= line("判定变成未满足", noev.verdict == "未满足")

    print("=" * 80)
    print("D2. 证据引自**上一轮**的子节点，也算指到了真东西")
    root, reg, recs, _ = go("recite")
    early = [n for n in reg.values() if n.name == "EARLY"]
    print("  EARLY 的判定: %s | 根的判定: %s"
          % (early[0].verdict if early else "?", root.verdict))
    ok &= line("早期子节点真的跑过", bool(early) and early[0].verdict == "满足")
    ok &= line("末轮是被拒那次（没有 results）",
               bool(root.attempts) and "results" not in root.attempts[-1])
    ok &= line("证据引更早一轮的孩子 → 不降级", root.verdict == "满足")

    print("=" * 80)
    print("E. 次数不限，但每次都看得见")
    root, reg, recs, _ = go("many")
    n_attempts = len(root.attempts)
    print("  根分配了 %d 次，启动的节点: %s" % (n_attempts, kinds(recs)))
    ok &= line("反复分配没有被计数器阻止", n_attempts >= 3, "%d 次" % n_attempts)
    ok &= line("每次尝试都在历史里", all("children" in a for a in root.attempts))
    ok &= line("最终能出结论", bool(root.verdict), "%s / %s" % (root.verdict, root.conclusion))

    print("=" * 80)
    print("F. 必填项缺一个 → 当场被拒；长字段原样通过（没有任何长度检查）")
    root2, reg2, recs2, _ = go("missing")
    print("  被拒原因: %s" % str(root2.attempts)[:120])
    ok &= line("缺 accept → 被拒并留下原因", "rejected" in str(root2.attempts))
    ok &= line("没有启动任何子节点",
               not any(r["kind"] == "open" and r["payload"].get("parent") for r in recs2))
    root3, reg3, recs3, _ = go("badrange")
    ok &= line("conc_range 形状不对（[500,100]）→ 被拒",
               "conc_range" in str(root3.attempts))
    root5, reg5, recs5, _ = go("badkind")
    print("  kind 写错的原因: %s" % str(root5.attempts)[:100])
    ok &= line('kind 写成 "dispatch|leaf" → 被拒（不再默默当 dispatch）',
               "rejected" in str(root5.attempts) and "kind" in str(root5.attempts))
    root4, reg4, recs4, _ = go("long")
    longest = max((len(n.detail) for n in reg4.values()), default=0)
    ok &= line("400 字的 detail 原样通过（代码不做长度检查）", longest == 400,
               "最长 %d 字" % longest)
    root6, reg6, recs6, _ = go("note")
    nl = max((len(n.notes) for n in reg6.values()), default=0)
    ok &= line("notes 不限字数（它不参与检索）", nl >= 400, "最长 %d 字" % nl)

    print("=" * 80)
    print("G. 分配节点没有 execute 分支")
    allkinds = set()
    for mode in ("gate_pass", "many"):
        _, reg3, recs3, _ = go(mode)
        allkinds |= {n.kind for n in reg3.values()}
    print("  出现过的节点类型: %s" % allkinds)
    ok &= line("只有 dispatch 和 leaf 两种", allkinds <= {"dispatch", "leaf"})
    ok &= line("叶子的产物必须是代码或结论",
               all(r["kind"] in ("code", "concluded", "bad_output", "bad_conclusion")
                   for r in recs3 if r["kind"] in
                   ("code", "concluded", "bad_output", "bad_conclusion")))

    print("=" * 80)
    print("J. 无进展检测：重复同一段代码、输出一样 → 被停下来")
    root, reg, recs, _ = go("loop", accept="某可观测结果", kind="leaf")
    np_ = [r for r in recs if r["kind"] == "no_progress"]
    stl = [r for r in recs if r["kind"] == "stalled"]
    acts = [r["payload"]["obs"] for r in recs if r["kind"] == "code"]
    print("  代码段数: %d | 无进展告警: %d | 停下: %s"
          % (len(acts), len(np_), root.verdict))
    print("  告警长这样: %s" % (acts[-1] if acts else "").replace("\n", " "))
    ok &= line("重复被检测到并显式告警", bool(np_))
    ok &= line("告警直接写在观测里（不会被忽略）", bool(acts) and "[停止]" in acts[-1])
    ok &= line("最终自己停下来（不是靠轮次上限）",
               bool(stl) and root.verdict == "未满足", root.conclusion)
    ok &= line("停下时把原因写清楚", "没有新信息" in (root.conclusion or ""))

    print("=" * 80)
    print("H. 检索键：分配节点一出生就自动查老树，叶子只查能力库")
    fake = FakeIndex()
    _, regH, recsH, _ = go("deep", index=fake)
    mid = [n for n in regH.values() if n.name == "MID"][0]
    leaf = [n for n in regH.values() if n.name == "LEAF"][0]
    n_dispatch = len([n for n in regH.values() if n.kind == "dispatch"])
    pre = [r for r in recsH if r["kind"] == "precedent"]
    print("  程序发出的查询: %s" % fake.qs)
    print("  给 MID 注入的先例: %s"
          % (mid.precedents[0][:40] if mid.precedents else "无"))
    ok &= line("按上层给的 keywords 查了（不是模型自己想起来的）",
               any("akshare" in q for qs in fake.qs for q in qs))
    ok &= line("根没有上层 → 用它自己的名字+验收标准查",
               any(qs and "ROOT" in qs[0] for qs in fake.qs))
    ok &= line("老树只给分配节点查（每个 dispatch 一条，叶子零条）",
               len(pre) == n_dispatch > 0
               and all(regH[r["node"]].kind == "dispatch" for r in pre)
               and not leaf.precedents)
    ok &= line("不再有「先例」这个动作（文档只把它当程序注入的东西）",
               '"先例"' not in PROMPT["alloc"])
    # 上层给的 conc_range / keywords 必须**真的出现在下层的提示词里**。
    # 提示词里只写"如 [100,500]"是不够的 —— 那是举例，不是上层的判断。
    gin = [r["payload"] for r in recsH
           if r["kind"] == "leaf_in" and r.get("node") == leaf.id]
    ok &= line("上层给的 conc_range 落到了孩子提示词里（不是举例）",
               bool(gin) and "conc_range: [100, 500]" in gin[0])
    ok &= line("上层给的 keywords 也落到了孩子提示词里",
               bool(gin) and "keywords: [" in gin[0])
    ok &= line("叶子的提示词里没有老树（它只要工具）",
               bool(gin) and "假的老树" not in gin[0])
    min_ = [r["payload"] for r in recsH
            if r["kind"] == "alloc_in" and r.get("node") == mid.id]
    ok &= line("命中结果进了分配节点的提示词",
               bool(min_) and "假的老树" in min_[0])

    print("=" * 80)
    print("I. 同构：收到的行首 == 自己要写的键；文档点名的段落 == 真渲染的段落")
    KEYS = ("name", "detail", "notes", "accept", "kind", "gate",
            "keywords", "conc_range")
    # 文档承诺给模型看的段落就这几样；在这里**双向**核对：
    #   文档说了没渲染 = 承诺落空；渲染了文档没说 = 偷偷塞东西。
    SECTIONS = ("先例", "现成做法", "上层意图链", "本层已有尝试",
                "观测历史", "手上的东西")

    def filled(kind_, lineage):
        n = Node(name="N", detail="D", notes="X", accept="A 2026-12-31",
                 kind=kind_, keywords=["akshare"], conc_range=[100, 500],
                 lineage=lineage)
        n.precedents.append("[先例] 假的老树")
        n.caps.append("pip install akshare")
        return n

    for kind_, which in (("dispatch", "alloc"), ("leaf", "leaf")):
        nI = filled(kind_, [["ROOT", "把量化系统做出来"],
                            ["MID", "摸清数据这条线"]])
        text = nI.render()
        head_keys = [ln.split(":")[0] for ln in nI.header().splitlines()]
        doc = [s for s in SECTIONS if s in PROMPT[which]]
        got = [s for s in SECTIONS if s in text]
        print("  %s: 收到的行首 %s" % (which, head_keys))
        print("       文档点名 %s / 真渲染 %s" % (doc, got))
        ok &= line("%s 收到的行首 == 自己要写的那 8 个键（同构）" % which,
                   head_keys == list(KEYS), "%s" % head_keys)
        ok &= line("%s: 收到的 8 个键在文档里都点了名" % which,
                   all(k in PROMPT[which] for k in KEYS))
        ok &= line("%s 的文档段落与渲染段落一致" % which, doc == got)
        ok &= line("%s: conc_range 在文档与渲染里都在" % which,
                   "conc_range" in PROMPT[which]
                   and "conc_range: [100, 500]" in nI.header())
        ok &= line("%s: 真值都渲染出来了（区间/检索键/意图链）" % which,
                   all(s in text for s in ("[100, 500]", "akshare",
                                           "ROOT: 把量化系统做出来",
                                           "MID: 摸清数据这条线")))
    # 分配节点历史里的子任务也要用同一套键 —— 它看到的是自己写过的形式，
    # 不是另一套中文标签。
    nA = filled("dispatch", [])
    nA.attempts.append({
        "children": [{"name": "子任务A", "kind": "leaf", "gate": True,
                      "accept": "A 2026-12-31 的读数", "keywords": ["akshare"],
                      "conc_range": [100, 500]}], "results": []})
    hist = nA.render_attempts()
    print("  历史长这样: %s" % hist.splitlines()[-1].strip())
    ok &= line("历史里的子任务用同一套键写（不再有中文标签）",
               "name: 子任务A" in hist and "gate: true" in hist
               and "conc_range: [100, 500]" in hist
               and "验收标准:" not in hist and "[门槛]" not in hist)
    ok &= line("alloc 的两个出口 = create_children / conclude",
               all(s in PROMPT["alloc"] for s in ("create_children", "conclude")))
    ok &= line("leaf 的两个出口 = run_code / conclude",
               all(s in PROMPT["leaf"] for s in ("run_code", "conclude")))
    ok &= line("叶子看不到「先例」（它只要工具）",
               "先例" not in filled("leaf", []).render())
    ok &= line("分配节点看得到「先例」",
               "先例" in filled("dispatch", []).render())
    ok &= line("根没有上层 → 不渲染意图链",
               filled("dispatch", []).render_lineage() == "")
    _, regI, recsI, _ = go("deep")
    lin = [r["payload"] for r in recsI if r["kind"] == "leaf_in"
           and regI[r["node"]].name == "LEAF"]
    ok &= line("叶子的提示词里带着从根到它上层的整条意图链",
               bool(lin) and "上层意图链" in lin[0] and "ROOT" in lin[0]
               and "MID" in lin[0])

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
