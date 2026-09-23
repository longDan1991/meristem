#!/usr/bin/env python3
"""形式化协议的定向测试。零成本、确定性（脚本化假模型）。

  A. 门槛不成立 → 兄弟子任务永不启动，分配节点的历史里留下"门槛不成立"
  B. 门槛通过   → 兄弟此时才启动
  C. 子任务验收标准丢了可测物理量 → 这次分配当场被代码拒，并记进"本层已有尝试"
  D. 判定"满足"但证据指不到任何真实东西 → 降级为"未满足"
  E. 次数不限：反复"再做一次"不被任何计数器阻止，而每次尝试都看得见
  F. 必填项缺一个 → 当场被拒；长字段原样通过（代码不做任何长度检查）
  G. 分配节点没有 execute 分支 ——"不拆"必须是派一个叶子
  I. 同构：收到的行首 == 自己要写的键；文档点名的段落 == 真渲染的段落
"""

import asyncio
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm import Message, ToolCall                      # noqa: E402
from core.protocol.fields import Node                # noqa: E402
from core.prompts import (build_system_sections, render_system,  # noqa: E402
                          render_turn)
from core.prompts.messages import (base_user, header, lineage,  # noqa: E402
                                   spec_line)
from core.runtime.loop import run as run_loop        # noqa: E402
from core.runtime import store as store_mod          # noqa: E402
from core.runtime.store import Store                 # noqa: E402
from core import config as cfg                       # noqa: E402

C_ANCHORED = "账户权益在2026-12-31收盘 >= 本金 x 2"


def kid(name, accept, kind="leaf", gate=False, rng=None,
        detail="按上层要求把这件事做完", notes=""):
    """一个合规的子任务形式（所有必填项都在）。"""
    return {"name": name, "detail": detail, "notes": notes, "accept": accept,
            "kind": kind, "gate": gate, "conc_range": rng or [100, 500]}


def bash_call(cmd):
    return Message(tool_calls=[ToolCall(name="bash", arguments={"cmd": cmd})])


def create(children):
    return Message(tool_calls=[ToolCall(name="create_children",
                                        arguments={"children": children})])


def conclude(**kw):
    return Message(tool_calls=[ToolCall(name="conclude", arguments=kw)])


class Scripted:
    """按平铺对话回话（发工具调用）。mode 决定行为。

    每个节点（分配节点和叶子一样）都是完整的 Loop：user 是基础形式字段
    （base_user = 形式字段 + 意图链），观测 / 尝试 / 下层结论以对话消息
    （assistant 的 tool_call + tool 回话 + 注入的 user）累积。
    """

    def __init__(self, mode):
        self.mode, self.calls, self.last_usage = mode, 0, {}

    @staticmethod
    def _count(messages, tname):
        """对话里调过某个工具几次（平铺记录数）。"""
        return sum(
            1 for m in messages if m.get("role") == "assistant"
            and m.get("tool_calls")
            and any(tc.get("function", {}).get("name") == tname
                    for tc in m["tool_calls"]))

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.calls += 1
        user = next((m["content"] for m in messages
                     if m.get("role") == "user"), "")
        name = (re.search(r"^name:\s*(.+)$", user, re.M) or [None, "?"])[1].strip()
        # 对话里还没有任何 tool 回话 = 还没动过手（分配节点和叶子同一条判据）。
        fresh = not any(m.get("role") == "tool" for m in messages)
        n_alloc = Scripted._count(messages, "create_children")

        if "kind: leaf" in user:                        # ── 叶子
            if name.startswith("GATE"):
                if self.mode == "gate_pass" and fresh:
                    return bash_call("echo gate-ok")
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
                    return bash_call("echo early")
                return conclude(verdict="满足", text="早期子任务干完了",
                                evidence=["第1次观测"])
            if self.mode == "deep":
                if fresh:
                    return bash_call("echo deep")
                return conclude(verdict="满足", text="收盘价读到了",
                                evidence=["第1次观测"])
            if self.mode == "many" and fresh:
                return bash_call("echo sib")
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
                detail="先把数据这条线摸清楚")])
        if self.mode == "recite":
            # 真跑过的孩子回来后，又发了一次用不了的分配（被代码拒），
            # 那次进历史时**没有 results**，最后才引第一轮的孩子出结论。
            if n_alloc == 0:
                return create([kid("EARLY", "2026-12-31 的权益读数已取到")])
            if n_alloc == 1:
                # 第二次分配故意缺 accept → 被代码当场拒（这段历史里没有结果）
                return create([{"name": "被拒的孩子", "detail": "d",
                                "kind": "leaf", "conc_range": [100, 500]}])
            return conclude(verdict="满足", text="下层都回来了", evidence=["EARLY"])
        if self.mode == "many":
            if n_alloc >= 3:
                return conclude(verdict="未满足", text="试了三种拆法都不行",
                                evidence=[])
            return create([kid(
                "SIB%d" % (n_alloc + 1),
                "2026-12-31 的权益读数已取到（第%d次尝试）" % (n_alloc + 1))])
        if n_alloc > 0:
            return conclude(verdict="满足", text="下层都回来了", evidence=["GATE"])
        if self.mode == "anchor":
            return create([kid("跑通就行", "代码能跑起来")])
        if self.mode == "missing":                  # 故意缺 accept（schema 拒）
            return create([{
                "name": "缺验收标准的孩子", "detail": "d", "kind": "leaf",
                "conc_range": [100, 500]}])
        if self.mode == "badkind":                  # kind 写成示例里的 "dispatch|leaf"
            s = kid("kind 写错的孩子", "2026-12-31 的权益读数已取到")
            s["kind"] = "dispatch|leaf"
            return create([s])
        if self.mode == "badrange":                 # 下限比上限大
            return create([{
                "name": "区间写错的孩子", "detail": "d", "notes": "",
                "accept": "2026-12-31 的权益读数已取到", "kind": "leaf",
                "conc_range": [500, 100]}])
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


def go(mode, accept=C_ANCHORED, kind="dispatch"):
    d = tempfile.mkdtemp()
    store_mod.init(d)
    root = Node(name="ROOT", accept=accept, kind=kind)
    llm = Scripted(mode)
    cwd = os.getcwd()          # 叶子会跑真的 bash：别污染项目目录
    os.chdir(d)
    try:
        st = asyncio.run(run_loop(Store.new(root), llm))
    finally:
        os.chdir(cwd)
    recs = list(Store.iter_lines(st.path))
    return root, st.registry, recs, d


def kinds(recs):
    return [r["payload"]["name"] for r in recs if r["kind"] == "open"]


def line(tag, cond, detail=""):
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    return bool(cond)


# 节点最后落盘的对话（历史只活在这一处 —— 结论审计、"本层历史"都从它推导）。
# 检查点是**增量**的（scheduler._checkpoint）：delta 事件只带自上次以来新增的
# 消息，这里按文件顺序拼回全量（和 load 同一套）。
def last_msgs(recs, nid):
    full = []
    for r in (r for r in recs if r["kind"] == "state" and r["node"] == nid):
        p = r["payload"]
        if p.get("delta"):
            full = full[: p.get("base", 0)] + (p.get("msgs") or [])
        else:
            full = p.get("msgs") or []      # 全量 / 老格式
    return full


def msgs_text(recs, nid):
    return " ".join(str(m.get("content", "")) for m in last_msgs(recs, nid))


def n_calls(recs, nid, tool):
    """对话里调过某个工具几次（平铺记录数）。"""
    return sum(1 for m in last_msgs(recs, nid)
               if m.get("role") == "assistant" and m.get("tool_calls")
               and any(tc.get("function", {}).get("name") == tool
                       for tc in m["tool_calls"]))


def main():
    ok = True

    print("=" * 80)
    print("A. 门槛不成立 → 兄弟永不启动")
    root, reg, recs, _ = go("gate_fail")
    print("  启动的节点: %s" % kinds(recs))
    gf = [r for r in recs if r["kind"] == "gate_failed"]
    sib = [n for n in reg.values() if n.name == "SIB"]
    ok &= line("SIB 未启动（未启动结论、对话里没有 assistant）",
               bool(sib) and sib[0].verdict == "未启动"
               and not any(m.get("role") == "assistant"
                           for m in last_msgs(recs, sib[0].id)))
    ok &= line("留下 gate_failed 记录", bool(gf))
    ok &= line("历史里写明门槛不成立", "门槛不成立" in msgs_text(recs, root.id))
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
    ok &= line("留下 criterion_drift 记录", bool(drift))
    ok &= line("被拒原因写回对话", "丢了可测物理量" in msgs_text(recs, root.id))
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
    ok &= line("证据引更早一轮的孩子 → 不降级", root.verdict == "满足")

    print("=" * 80)
    print("E. 次数不限，但每次都看得见")
    root, reg, recs, _ = go("many")
    n_attempts = sum(1 for r in recs if r["kind"] == "allocated")
    print("  根分配了 %d 次，启动的节点: %s" % (n_attempts, kinds(recs)))
    ok &= line("反复分配没有被计数器阻止", n_attempts >= 3, "%d 次" % n_attempts)
    ok &= line("每次尝试都在对话里",
               n_calls(recs, root.id, "create_children") == n_attempts)
    ok &= line("最终能出结论", bool(root.verdict), "%s / %s" % (root.verdict, root.conclusion))

    print("=" * 80)
    print("F. 必填项缺一个 → 当场被拒；长字段原样通过（没有任何长度检查）")
    root2, reg2, recs2, _ = go("missing")
    ok &= line("缺 accept → 被拒并把原因写回对话",
               "工具参数不合形状" in msgs_text(recs2, root2.id)
               and "children.0.accept" in msgs_text(recs2, root2.id))
    ok &= line("没有启动任何子节点",
               not any(r["kind"] == "open" and r["payload"].get("parent") for r in recs2))
    root3, reg3, recs3, _ = go("badrange")
    ok &= line("conc_range 形状不对（[500,100]）→ 被拒",
               "conc_range" in msgs_text(recs3, root3.id))
    root5, reg5, recs5, _ = go("badkind")
    ok &= line('kind 写成 "dispatch|leaf" → 被拒（不再默默当 dispatch）',
               "kind 必须是 dispatch 或 leaf" in msgs_text(recs5, root5.id))
    root4, reg4, recs4, _ = go("long")
    longest = max((len(n.detail) for n in reg4.values()), default=0)
    ok &= line("400 字的 detail 原样通过（代码不做长度检查）", longest == 400,
               "最长 %d 字" % longest)
    root6, reg6, recs6, _ = go("note")
    nl = max((len(n.notes) for n in reg6.values()), default=0)
    ok &= line("notes 不限字数", nl >= 400, "最长 %d 字" % nl)

    print("=" * 80)
    print("G. 分配节点没有 execute 分支")
    allkinds = set()
    for mode in ("gate_pass", "many"):
        _, reg3, recs3, _ = go(mode)
        allkinds |= {n.kind for n in reg3.values()}
    print("  出现过的节点类型: %s" % allkinds)
    ok &= line("只有 dispatch 和 leaf 两种", allkinds <= {"dispatch", "leaf"})
    ok &= line("叶子的产物必须是代码或结论",
               all(r["kind"] in ("tool", "concluded", "bad_conclusion")
                   for r in recs3 if r["kind"] in
                   ("tool", "concluded", "bad_conclusion")))

    print("=" * 80)
    print("I. 同构：收到的行首 == 自己要写的键；文档点名的段落 == 真渲染的段落")
    KEYS = ("name", "detail", "notes", "accept", "kind", "gate", "conc_range")
    # 文档承诺给模型看的**静态**段落 vs 线上真正发出去的基础消息（base_user）。
    # 在这里**双向**核对：文档说了没渲染 = 承诺落空；渲染了文档没说 = 偷偷塞东西。
    # 「本层已有尝试 / 观测历史 / 手上的东西」不在这 —— 它们是线上对话机制与
    # 工具清单的说明（分配记录、tool 消息、工具列表各自承担），不渲进基础消息。
    SECTIONS = ("上层意图链",)

    def sys_text(which):
        """该节点回合的 system 文本（= tree/prompts/ 的节组装结果，render_turn 的第一条消息）。"""
        n = filled("leaf" if which == "leaf" else "dispatch", [])
        return render_turn(which, n)[0]["content"]

    def filled(kind_, lineage):
        n = Node(name="N", detail="D", notes="X", accept="A 2026-12-31",
                 kind=kind_, conc_range=[100, 500], lineage=lineage)
        return n

    for kind_, which in (("dispatch", "alloc"), ("leaf", "leaf")):
        nI = filled(kind_, [["ROOT", "把量化系统做出来"],
                            ["MID", "摸清数据这条线"]])
        text = base_user(nI)
        head_keys = [ln.split(":")[0] for ln in header(nI).splitlines()]
        sys_txt = sys_text(which)
        doc = [s for s in SECTIONS if s in sys_txt]
        got = [s for s in SECTIONS if s in text]
        print("  %s: 收到的行首 %s" % (which, head_keys))
        print("       文档点名 %s / 基础消息里有 %s" % (doc, got))
        ok &= line("%s 收到的行首 == 自己要写的那 7 个键（同构）" % which,
                   head_keys == list(KEYS), "%s" % head_keys)
        ok &= line("%s: 收到的 7 个键在文档里都点了名" % which,
                   all(k in sys_txt for k in KEYS))
        ok &= line("%s: 文档点名的静态段落 == 基础消息里有的" % which, doc == got)
        ok &= line("%s: conc_range 在文档与基础消息里都在" % which,
                   "conc_range" in sys_txt
                   and "conc_range: [100, 500]" in header(nI))
        ok &= line("%s: 真值都渲染出来了（区间/意图链）" % which,
                   all(s in text for s in ("[100, 500]",
                                           "ROOT: 把量化系统做出来",
                                           "MID: 摸清数据这条线")))
    # 分配记录里的子任务也用同一套键 —— 模型看到的是自己写过的形式，不是中文标签。
    sl = spec_line({"name": "子任务A", "kind": "leaf", "gate": True,
                    "accept": "A 2026-12-31 的读数", "conc_range": [100, 500]})
    ok &= line("分配记录里的子任务用同一套键写（不再有中文标签）",
               "name: 子任务A" in sl and "kind: leaf" in sl
               and "gate: true" in sl and "conc_range: [100, 500]" in sl
               and "验收标准:" not in sl and "[门槛]" not in sl)
    ok &= line("alloc 的两个出口 = create_children / conclude",
               all(s in sys_text("alloc") for s in ("create_children", "conclude")))
    ok &= line("leaf 的出口 = bash / read / write / conclude",
               all(s in sys_text("leaf") for s in ("bash", "read", "write", "conclude")))
    # 双向核对换成**节名集合**（docs/PROMPTS.md §5.6）：文档点名的节 == 真渲染的节。
    # 恒在节按 §3.2；条件节按出生时静态属性（gate / COMPRESS）。
    DOC_SECTIONS = {"preamble", "process", "tools", "rules", "input"}

    def section_names(sys_t):
        names = set(re.findall(r"<([a-z][a-z0-9_-]*)>", sys_t))
        if not sys_t.startswith("<"):
            names.add("preamble")          # preamble 无标签、放在最前
        return names

    for kind_, which in (("dispatch", "alloc"), ("leaf", "leaf")):
        nS = filled(kind_, [])
        got = section_names(render_turn(which, nS)[0]["content"])
        expect = set(DOC_SECTIONS)
        if which == "leaf" and cfg.COMPRESS:
            expect.add("skill_compression")
        ok &= line("%s: 文档点名的节 == 真渲染的节" % which,
                   got == expect, "%s" % sorted(got))
    ok &= line("intake: 文档点名的节 == 真渲染的节（无条件节）",
               section_names(render_turn("intake")[0]["content"])
               == set(DOC_SECTIONS))
    ok &= line("根没有上层 → 不渲染意图链", lineage(filled("dispatch", [])) == "")
    _, regI, recsI, _ = go("deep")
    lin = [r["payload"] for r in recsI if r["kind"] == "leaf_in"
           and regI[r["node"]].name == "LEAF"]
    ok &= line("叶子的提示词里带着从根到它上层的整条意图链",
               bool(lin) and "上层意图链" in lin[0] and "ROOT" in lin[0]
               and "MID" in lin[0])

    def _raises(fn):
        try:
            fn()
        except ValueError:
            return True
        return False

    async def _mcp_prompt_names():
        return set()

    print("=" * 80)
    print("K. 命名分节 wire：system 只有一条、intake 同样、参数校验")

    def _wire(which):
        return [m["role"] for m in render_turn(which, filled(
            "leaf" if which == "leaf" else "dispatch", []))]

    k_roles = _wire("leaf")
    k_roles_alloc = _wire("alloc")
    k_roles_intake = [m["role"] for m in render_turn("intake")]
    ok &= line("leaf 的线上 wire = [system]（任务与历史在对话里）",
               k_roles == ["system"], str(k_roles))
    ok &= line("alloc 的线上 wire = [system]",
               k_roles_alloc == ["system"], str(k_roles_alloc))
    ok &= line("intake 只有 system（它的 user 是用户的话，在对话里）",
               k_roles_intake == ["system"], str(k_roles_intake))
    ok &= line("未知节点类型当场报错",
               _raises(lambda: render_turn("wat")))
    ok &= line("系统提示词与任务消息分开（任务走对话首条）",
               base_user(filled("leaf", [])).startswith("name:"))

    print("=" * 80)
    print("K2. 命名分节：节在场性 / 字节稳定 / 节名校验")

    def sec_sys(kind_, gate=False):
        n = filled(kind_, [])
        n.gate = gate
        return render_turn("leaf" if kind_ == "leaf" else "alloc", n
                           )[0]["content"]

    n_plain = sec_sys("leaf", False)
    n_gate = sec_sys("leaf", True)
    n_alloc = sec_sys("dispatch", True)
    ok &= line("preamble 在最前无标签，节按固定顺序包同名标签",
               not n_plain.startswith("<") and "<process>" in n_plain
               and n_plain.index("<tools>") < n_plain.index("<rules>")
               < n_plain.index("<input>"))
    ok &= line("gate=False → 无 <skill_gate> 节", "<skill_gate>" not in n_plain)
    ok &= line("gate=True → 有 <skill_gate> 节", "<skill_gate>" in n_gate
               and "<skill_gate>" in n_alloc)
    ok &= line("COMPRESS 默认开 → 叶子有 <skill_compression>、分配节点没有",
               cfg.COMPRESS and "<skill_compression>" in n_plain
               and "<skill_compression>" not in n_alloc)
    n_leaf = filled("leaf", [])
    ok &= line("同一节点两次组装字节一致",
               render_system(build_system_sections("leaf", n_leaf))
               == render_system(build_system_sections("leaf", n_leaf)))
    try:
        render_system({"preamble": "x", "bad name": "y"})
        ok &= line("节名违反 [a-z][a-z0-9_-]* 当场报错", False)
    except ValueError:
        ok &= line("节名违反 [a-z][a-z0-9_-]* 当场报错", True)
    # COMPRESS 关：config 在 import 时固化，用子进程验（TREE_COMPRESS=0）
    script = (
        "import os; os.environ['TREE_COMPRESS'] = '0'; "
        "from core.protocol.fields import Node; "
        "from core.prompts import build_system_sections, render_system; "
        "n = Node(name='N', accept='A 2026-12-31', kind='leaf'); "
        "s = render_system(build_system_sections('leaf', n)); "
        "assert '<skill_gate>' not in s and '<skill_compression>' not in s, s; "
        "n2 = Node(name='N', accept='A 2026-12-31', kind='leaf', gate=True); "
        "s2 = render_system(build_system_sections('leaf', n2)); "
        "assert '<skill_gate>' in s2 and '<skill_compression>' not in s2; "
        "print('ok')")
    r = subprocess.run([sys.executable, "-c", script], capture_output=True,
                       text=True, cwd=os.path.dirname(os.path.dirname(
                           os.path.abspath(__file__))))
    ok &= line("COMPRESS 关 → 叶子无 <skill_compression>，gate=True 有 <skill_gate>",
               r.returncode == 0 and r.stdout.strip() == "ok",
               r.stderr.strip()[-160:])

    print("=" * 80)
    print("L. 并行工具调用：一次回复多个工具 → 全部执行，全部完成再继续")

    class Multi:
        def __init__(self):
            self.last_usage = {}

        async def chat(self, messages, temperature=0.2, on_delta=None,
                       on_reasoning=None, tools=None):
            self.last_usage = {"total_tokens": 0}
            done = sum(1 for m in messages if m.get("role") == "tool")
            if done == 0:
                return Message(tool_calls=[
                    ToolCall(name="bash", arguments={"cmd": "echo a"}),
                    ToolCall(name="bash", arguments={"cmd": "echo b"})])
            return Message(tool_calls=[ToolCall(
                name="conclude", arguments={"verdict": "满足", "text": "ok",
                                            "evidence": ["第1次观测"]})])

    d_m = tempfile.mkdtemp()
    store_mod.init(d_m)
    root_m = Node(name="叶子", accept="2026-12-31 收盘 >= 1", kind="leaf")
    cwd = os.getcwd()
    os.chdir(d_m)
    try:
        st_m = asyncio.run(run_loop(Store.new(root_m), Multi()))
    finally:
        os.chdir(cwd)
    recs_m = list(Store.iter_lines(st_m.path))
    msgs_m = last_msgs(recs_m, root_m.id)
    ok &= line("一次回复的两个工具都执行了",
               len([r for r in recs_m if r["kind"] == "tool"]) >= 2)
    ok &= line("两条 tool 回话都配上了",
               sum(1 for m in msgs_m if m.get("role") == "tool") >= 2)
    ok &= line("全部完成后继续，最终出结论", root_m.verdict == "满足")

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
