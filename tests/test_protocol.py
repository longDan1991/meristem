#!/usr/bin/env python3
"""形式化协议的定向测试（零成本、确定性，脚本化假模型）。

沟通模型：没有 verdict、没有证据审计 —— 节点之间靠 communicate 消息来往，
代码只做形状校验与投递。这里守的是：寻址（parent / 孩子名 / 错名字打回）、
形状校验、同构（ChildSpec 键 == FORM_FIELDS）、命名分节 wire、作用域清单。
"""

import asyncio
import os
import re
import sys
import tempfile

from harness import line
from core.llm import Message, ToolCall
from core.protocol.fields import FORM_FIELDS, Node
from core.prompts import (build_system_sections, render_system,
                          render_turn)
from core.protocol.messages import base_user, header, lineage
from core.prompts.tools import TOOL_GUIDE
from core.runtime.loop import run as run_loop
from core.runtime import store as store_mod
from core.runtime.store import Store
from tools import ACTION_TAG, action_names, load, scope_names, scope_tag, scopes
from tools.specs import ChildSpec, mcp


def kid(name, kind="leaf", rng=None, detail="按上层要求把这件事做完", notes=""):
    """一个合规的子任务形式（所有必填项都在）。"""
    return {"name": name, "detail": detail, "notes": notes, "kind": kind,
            "conc_range": rng or [100, 500]}


def bash_call(cmd):
    return Message(tool_calls=[ToolCall(name="bash", arguments={"command": cmd})])


def create(children):
    return Message(tool_calls=[ToolCall(name="create_children",
                                        arguments={"children": children})])


def communicate(to, text, rng=None):
    args = {"to": to, "text": text}
    if rng:
        args["conc_range"] = rng
    return Message(tool_calls=[ToolCall(name="communicate", arguments=args)])


class Scripted:
    """按平铺对话回话（发工具调用），mode 决定行为；每个节点都是完整的 Loop。"""

    def __init__(self, mode):
        self.mode, self.calls = mode, 0

    @staticmethod
    def _count(messages, tname):
        """对话里调过某个工具几次（平铺记录数）。"""
        return sum(
            1 for m in messages if m.get("role") == "assistant"
            and m.get("tool_calls")
            and any(tc.get("function", {}).get("name") == tname
                    for tc in m["tool_calls"]))

    @staticmethod
    def _reports(messages):
        """收到的沟通消息（user 且正文带「来自」来源标记）。"""
        return [m for m in messages
                if m.get("role") == "user" and "来自「" in str(m.get("content", ""))]

    @staticmethod
    def _rejected(messages, text):
        return any(text in str(m.get("content", "")) for m in messages
                   if m.get("role") == "tool")

    async def chat(self, messages, temperature=0.2, on_delta=None, on_reasoning=None,
                   tools=None):
        self.calls += 1
        user = next((m["content"] for m in messages
                     if m.get("role") == "user"), "")
        name = (re.search(r"^name:\s*(.+)$", user, re.M) or [None, "?"])[1].strip()
        # 对话里还没有任何 tool 回话 = 还没动过手（分配节点和叶子同一条判据）。
        fresh = not any(m.get("role") == "tool" for m in messages)
        n_alloc = Scripted._count(messages, "create_children")
        reports = Scripted._reports(messages)

        if "kind: leaf" in user:                        # ── 叶子
            if fresh:
                return bash_call("echo %s" % name)
            return communicate("parent", "%s 干完了" % name)

        # ── 分配节点
        if self.mode == "deep":
            # 三层：ROOT(分配) → MID(分配) → LEAF(叶子)，验意图链真的逐层加长
            if name == "MID":
                if fresh:
                    return create([kid("LEAF", detail="读收盘价")])
                return communicate("parent", "叶子回来了")
            if not reports:
                return create([kid("MID", kind="dispatch",
                                   detail="先把数据这条线摸清楚")])
            return Message(text="都回来了")
        if self.mode == "many":
            if n_alloc >= 3:
                return Message(text="试了三种拆法都不行")
            return create([kid("SIB%d" % (n_alloc + 1))])
        if self.mode == "roundtrip":
            # 叶子回报 → 根回一句 → 叶子再回报 → 根收工；验双向寻址
            if not reports:
                return create([kid("A")])
            if len(reports) == 1:
                return communicate("A", "收到，等我总结")
            return Message(text="都回来了")
        if self.mode == "bad_to":
            if not reports:
                return create([kid("A")])
            if not Scripted._rejected(messages, "communicate 的 to"):
                return communicate("不存在的孩子", "这不该送到")
            return Message(text="给不出去，收工")
        if n_alloc > 0:
            return Message(text="都回来了")          # 拆过一次了：交出去休息（根没有父节点，纯文本）
        if self.mode == "missing":                  # 故意缺 detail，gate 拒
            return create([{"name": "缺 detail 的孩子", "kind": "leaf",
                            "conc_range": [100, 500]}])
        if self.mode == "badkind":                  # kind 写成示例里的 "dispatch|leaf"
            s = kid("kind 写错的孩子")
            s["kind"] = "dispatch|leaf"
            return create([s])
        if self.mode == "badrange":                 # 下限比上限大
            return create([{"name": "区间写错的孩子", "detail": "d", "notes": "",
                            "kind": "leaf", "conc_range": [500, 100]}])
        if self.mode == "long":
            return create([kid("长字段", detail="很长" * 200)])
        if self.mode == "note":
            return create([kid("带备注", notes="写在字段里放不下的判断依据。" * 50)])
        return create([kid("A"), kid("B")])


def go(mode, kind="dispatch"):
    d = tempfile.mkdtemp()
    store_mod.init(d)
    root = Node(name="ROOT", kind=kind)
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
    """记录里出现过的节点名（节点出生即写 state 检查点，没有单独的 open 事件）。"""
    seen = {}
    for r in recs:
        if r["kind"] == "state":
            node = (r.get("payload") or {}).get("node")
            if node:
                seen[r["node"]] = node.get("name")
    return list(seen.values())


def has_child_node(recs):
    """记录里有没有带 parent 的节点（= 真的启动过子节点）。"""
    return any(((r.get("payload") or {}).get("node") or {}).get("parent")
               for r in recs if r["kind"] == "state")


# 节点最后落盘的对话（历史只活在这一处）；检查点是增量的，这里按文件顺序拼回全量。
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
    asyncio.run(load())      # 提示词是同步拼的：先把作用域视图从注册表读出来

    print("=" * 80)
    print("A. 双向寻址：子报父、父回子；错名字当场打回")
    root, reg, recs, _ = go("roundtrip")
    a_node = [n for n in reg.values() if n.name == "A"][0]
    ok &= line("孩子的回报进了父的对话（带来源标记）",
               "来自「A」" in msgs_text(recs, root.id))
    ok &= line("父的回复进了孩子的对话（带来源标记）",
               "来自「ROOT」" in msgs_text(recs, a_node.id))
    ok &= line("孩子没有因为父的回复被重跑（bash 只一次）",
               n_calls(recs, a_node.id, "bash") == 1)
    ok &= line("根收工后休息（最后一条是 assistant）",
               last_msgs(recs, root.id)[-1].get("role") == "assistant")
    root2, reg2, recs2, _ = go("bad_to")
    ok &= line("communicate 给不存在的孩子 → 当场打回并说明规则",
               "communicate 的 to" in msgs_text(recs2, root2.id))
    ok &= line("没有孩子真的收到那条消息",
               not any("这不该送到" in msgs_text(recs2, n.id) and n.id != root2.id
                       for n in reg2.values()))

    print("=" * 80)
    print("B. 必填项缺一个 → 当场被拒；长字段原样通过（没有任何长度检查）")
    root2, reg2, recs2, _ = go("missing")
    ok &= line("缺 detail → 被 schema 层拒并把原因写回对话",
               "工具参数不合形状" in msgs_text(recs2, root2.id)
               and "children.0.detail" in msgs_text(recs2, root2.id))
    ok &= line("没有启动任何子节点", not has_child_node(recs2))
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
    print("C. 次数不限，但每次都看得见")
    root, reg, recs, _ = go("many")
    n_attempts = sum(1 for r in recs if r["kind"] == "allocated")
    print("  根分配了 %d 次，启动的节点: %s" % (n_attempts, kinds(recs)))
    ok &= line("反复分配没有被计数器阻止", n_attempts >= 3, "%d 次" % n_attempts)
    ok &= line("每次尝试都在对话里",
               n_calls(recs, root.id, "create_children") == n_attempts)
    ok &= line("孩子每次的回报都在根的对话里",
               sum(1 for m in last_msgs(recs, root.id)
                   if m.get("role") == "user" and "来自「" in str(m.get("content", "")))
               == n_attempts)

    print("=" * 80)
    print("D. 意图链逐层物化：叶子带着从根到上层的整条链")
    _, regI, recsI, _ = go("deep")
    leafI = [n for n in regI.values() if n.name == "LEAF"][0]
    lin = last_msgs(recsI, leafI.id)
    ok &= line("叶子的任务消息里带着从根到它上层的整条意图链",
               bool(lin) and "上层意图链" in lin[0]["content"]
               and "ROOT" in lin[0]["content"] and "MID" in lin[0]["content"])

    print("=" * 80)
    print("E. 分配节点没有 execute 分支")
    allkinds = set()
    for mode in ("many", "roundtrip"):
        _, reg3, recs3, _ = go(mode)
        allkinds |= {n.kind for n in reg3.values()}
    print("  出现过的节点类型: %s" % allkinds)
    ok &= line("只有 dispatch 和 leaf 两种", allkinds <= {"dispatch", "leaf"})

    print("=" * 80)
    print("F. 同构：收到的行首 == 自己要写的键；文档点名的段落 == 真渲染的段落")
    KEYS = FORM_FIELDS
    ok &= line("工具 schema 的键 == 协议的形式字段（同一份、同一顺序）",
               tuple(ChildSpec.model_fields) == KEYS,
               "%s" % (tuple(ChildSpec.model_fields),))
    SECTIONS = ("上层意图链",)

    def sys_text(which):
        """该节点回合的 system 文本（= core/prompts/ 的节组装结果，render_turn 的第一条消息）。"""
        return render_turn(which)[0]["content"]

    def filled(kind_, lineage):
        n = Node(name="N", detail="D", notes="X",
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
        ok &= line("%s 收到的行首 == 自己要写的那 5 个键（同构）" % which,
                   head_keys == list(KEYS), "%s" % head_keys)
        ok &= line("%s: 收到的 5 个键在文档里都点了名" % which,
                   all(k in sys_txt for k in KEYS))
        ok &= line("%s: 文档点名的静态段落 == 基础消息里有的" % which, doc == got)
        ok &= line("%s: conc_range 在文档与基础消息里都在" % which,
                   "conc_range" in sys_txt
                   and "conc_range: [100, 500]" in header(nI))
        ok &= line("%s: 真值都渲染出来了（区间/意图链）" % which,
                   all(s in text for s in ("[100, 500]",
                                           "ROOT: 把量化系统做出来",
                                           "MID: 摸清数据这条线")))
    ok &= line("alloc 的两个出口 = create_children / communicate",
               all(s in sys_text("alloc") for s in ("create_children", "communicate")))
    ok &= line("leaf 的出口 = bash / read / write / read_skill / communicate",
               all(s in sys_text("leaf")
                   for s in ("bash", "read", "write", "read_skill", "communicate")))
    ok &= line("intake 的出口 = submit_root / communicate",
               all(s in sys_text("intake") for s in ("submit_root", "communicate")))
    # 节名集合：沟通模型下没有条件节，六个节全部恒在 —— 这份集合就是契约本身
    # （曾经与 docs/PROMPTS.md 的节表双向核对，那份文档已删）。
    DOC_SECTIONS = {"preamble", "process", "tools", "rules", "skills", "input"}

    def section_names(sys_t):
        names = set(re.findall(r"<([a-z][a-z0-9_-]*)>", sys_t))
        if not sys_t.startswith("<"):
            names.add("preamble")          # preamble 无标签、放在最前
        return names

    for kind_, which in (("dispatch", "alloc"), ("leaf", "leaf")):
        got = section_names(render_turn(which)[0]["content"])
        ok &= line("%s: 渲染出来的节 == 六个恒在节" % which,
                   got == set(DOC_SECTIONS), "%s" % sorted(got))
    ok &= line("intake: 渲染出来的节 == 六个恒在节",
               section_names(render_turn("intake")[0]["content"])
               == set(DOC_SECTIONS))
    ok &= line("根没有上层 → 不渲染意图链", lineage(filled("dispatch", [])) == "")

    def _raises(fn):
        try:
            fn()
        except ValueError:
            return True
        return False

    print("=" * 80)
    print("K. 命名分节 wire：system 只有一条、intake 同样、参数校验")

    def _wire(which):
        return [m["role"] for m in render_turn(which)]

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

    def sec_sys(kind_):
        return render_turn("leaf" if kind_ == "leaf" else "alloc")[0]["content"]

    n_plain = sec_sys("leaf")
    n_alloc = sec_sys("dispatch")
    ok &= line("preamble 在最前无标签，节按固定顺序包同名标签",
               not n_plain.startswith("<") and "<process>" in n_plain
               and n_plain.index("<tools>") < n_plain.index("<rules>")
               < n_plain.index("<input>"))
    ok &= line("<skills> 恒在（三种节点都有）",
               "<skills>" in n_plain and "<skills>" in n_alloc
               and "<skills>" in render_turn("intake")[0]["content"])
    ok &= line("没有 skill_gate 节（门槛机制已删）",
               "<skill_gate>" not in n_plain and "<skill_gate>" not in n_alloc)
    ok &= line("同一节点两次组装字节一致",
               render_system(build_system_sections("leaf"))
               == render_system(build_system_sections("leaf")))
    try:
        render_system({"preamble": "x", "bad name": "y"})
        ok &= line("节名违反 [a-z][a-z0-9_-]* 当场报错", False)
    except ValueError:
        ok &= line("节名违反 [a-z][a-z0-9_-]* 当场报错", True)

    print("=" * 80)
    print("L. 并行工具调用：一次回复多个工具 → 全部执行，全部完成再继续")

    class Multi:
        async def chat(self, messages, temperature=0.2, on_delta=None,
                       on_reasoning=None, tools=None):
            done = sum(1 for m in messages if m.get("role") == "tool")
            if done == 0:
                return Message(tool_calls=[
                    ToolCall(name="bash", arguments={"command": "echo a"}),
                    ToolCall(name="bash", arguments={"command": "echo b"})])
            return Message(text="ok")     # 纯文本：收工休息（叶子没有父节点可报）

    d_m = tempfile.mkdtemp()
    store_mod.init(d_m)
    root_m = Node(name="叶子", kind="leaf")
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
    ok &= line("全部完成后收工休息（最后一条是 assistant）",
               msgs_m[-1].get("role") == "assistant")

    print("=" * 80)
    print("M. 工具作用域：声明只有一处（tags）、清单由库的可见性算出来、指导齐全")

    # 指导表是手写的提示词、清单是从注册表算出来的：两边的覆盖要**对等** ——
    # 少一行 tools 节会当场报错（runtime 那道），多一行就是没人用的死文案。
    expected = {n for w in scopes() for n in scope_names(w)}
    ok &= line("决策指导表与注册表里的工具一一对应",
               set(TOOL_GUIDE) == expected,
               str(sorted(set(TOOL_GUIDE) ^ expected)))

    registered = {t.name: set(t.tags) for t in asyncio.run(mcp.list_tools())}
    untagged = {n: sorted(t) for n, t in registered.items()
                if not any(x.startswith("scope:") for x in t)}
    ok &= line("每个注册的工具都声明了作用域标签（没声明的谁都调不到）",
               not untagged, str(untagged))
    ok &= line("清单 == 注册表里带 scope:<层> 标签的工具（库的可见性过滤）",
               all(set(scope_names(w))
                   == {n for n, t in registered.items() if scope_tag(w) in t}
                   for w in scopes()),
               str({w: scope_names(w) for w in scopes()}))
    ok &= line("动手工具 = 注册表里带 action 标签的那些（bash/read/write/read_skill）",
               set(action_names()) == {n for n, t in registered.items()
                                       if ACTION_TAG in t},
               str(action_names()))
    ok &= line("作用域 = 节点类型（alloc / leaf / intake）",
               set(scopes()) == {"alloc", "leaf", "intake"}, str(scopes()))
    ok &= line("communicate 三种节点都能调（寻址决定发给谁）",
               all("communicate" in scope_names(w) for w in scopes()),
               str({w: scope_names(w) for w in scopes()}))

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
