#!/usr/bin/env python3
"""形式化协议的定向测试。零成本、确定性（脚本化假模型）。

  A. 门槛不成立 → 兄弟子任务永不启动，分配节点的历史里留下"门槛不成立"
  B. 门槛通过   → 兄弟此时才启动
  C. 子任务验收标准丢了可测物理量 → 这次分配当场被代码拒，并记进"本层已有尝试"
  D. 判定"满足"但证据指不到任何真实东西 → 降级为"未满足"
  E. 次数不限：反复"再做一次"不被任何计数器阻止，而每次尝试都看得见
  F. 必填项缺一个 → 当场被拒；长字段原样通过（代码不做任何长度检查）
  G. 分配节点没有 execute 分支 ——"不拆"必须是派一个叶子
  H. 检索键：孩子一出生就自动查老树（模型不用自己想起来要查）
"""

import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.node import Node, Trace                    # noqa: E402
from tree import run as R                            # noqa: E402

C_ANCHORED = "账户权益在2026-12-31收盘 >= 本金 x 2"


class FakeIndex:
    """假的老树索引：只记下程序发了什么查询。"""

    def __init__(self):
        self.qs = []

    def search(self, qs):
        self.qs.append(list(qs))
        return [], "[先例] 假的老树"


def kid(name, accept, kind="leaf", gate=False, keywords=None, rng=None,
        detail="按上层要求把这件事做完", notes=""):
    """一个合规的子任务形式（所有必填项都在）。"""
    return {"name": name, "detail": detail, "notes": notes, "accept": accept,
            "kind": kind, "gate": gate,
            "keywords": keywords or ["kw-" + name, "2026-12-31"],
            "conc_range": rng or [100, 500]}


class Scripted:
    """按渲染出来的形式字段回话。mode 决定行为。"""

    def __init__(self, mode):
        self.mode, self.calls, self.last_usage = mode, 0, {}

    def chat(self, messages, temperature=0.2):
        self.calls += 1
        user = messages[-1]["content"]
        name = (re.search(r"任务名:\s*(.+?)\n", user) or [None, "?"])[1].strip()
        fresh = "(还没有)" in user
        m = re.search(r"本层已有尝试: 共 (\d+) 次", user)
        attempts = int(m.group(1)) if m else 0

        if "可用工具" in user:                        # ── 叶子
            if self.mode == "loop":
                # 永远做同一个动作，观测也永远一样
                return json.dumps({"action": {"tool": "bash",
                                               "args": {"cmd": "echo same"}}})
            if name.startswith("GATE"):
                if self.mode == "gate_pass" and fresh:
                    return json.dumps({"action": {"tool": "bash",
                                                   "args": {"cmd": "echo gate-ok"}}})
                v = "满足" if self.mode == "gate_pass" else "阻塞"
                ev = ["第1次观测"] if v == "满足" else []
                return json.dumps({"conclusion": {
                    "verdict": v,
                    "text": "门槛测过了" if v == "满足" else "开户需要人到场，不在工具里",
                    "evidence": ev}})
            if name.startswith("NOEV"):
                return json.dumps({"conclusion": {"verdict": "满足",
                                                   "text": "我发誓真的做完了",
                                                   "evidence": ["凭良心说的"]}})
            if self.mode == "many" and fresh:
                return json.dumps({"action": {"tool": "bash", "args": {"cmd": "echo sib"}}})
            return json.dumps({"conclusion": {"verdict": "满足", "text": "兄弟干完了",
                                               "evidence": ["第1次观测"]}})

        # ── 分配节点
        if self.mode == "many":
            if attempts >= 3:
                return json.dumps({"conclusion": {"verdict": "未满足",
                                                  "text": "试了三种拆法都不行",
                                                  "evidence": []}})
            return json.dumps({"children": [kid(
                "SIB%d" % (attempts + 1),
                "2026-12-31 的权益读数已取到（第%d次尝试）" % (attempts + 1))]},
                ensure_ascii=False)
        if not fresh:
            return json.dumps({"conclusion": {"verdict": "满足", "text": "下层都回来了",
                                               "evidence": ["GATE"]}})
        if self.mode == "anchor":
            return json.dumps({"children": [
                {"name": "跑通就行", "detail": "把代码跑起来", "notes": "",
                 "accept": "代码能跑起来", "kind": "leaf",
                 "keywords": ["跑通"], "conc_range": [100, 500]}]})
        if self.mode == "missing":                  # 故意缺 accept
            return json.dumps({"children": [{
                "name": "缺验收标准的孩子", "detail": "d", "kind": "leaf",
                "keywords": ["x"], "conc_range": [100, 500]}]})
        if self.mode == "badrange":                 # 下限比上限大
            return json.dumps({"children": [{
                "name": "区间写错的孩子", "detail": "d", "notes": "",
                "accept": "2026-12-31 的权益读数已取到", "kind": "leaf",
                "keywords": ["x"], "conc_range": [500, 100]}]})
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
        if self.mode == "newkeywords":
            kids[0]["keywords"] = ["akshare", "回测", "2026-12-31"]
        return json.dumps({"children": kids}, ensure_ascii=False)


def go(mode, accept=C_ANCHORED, kind="dispatch", index=None):
    d = tempfile.mkdtemp()
    trace = Trace(os.path.join(d, "t.jsonl"))
    root = Node(name="ROOT", accept=accept, kind=kind)
    reg, llm = {}, Scripted(mode)
    cwd = os.getcwd()          # 叶子会跑真的 bash：别污染项目目录
    os.chdir(d)
    try:
        R.run(root, llm, trace, registry=reg, workers=2, index=index)
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
    ok &= line("叶子的产物必须是动作或结论",
               all(r["kind"] in ("action", "concluded", "bad_output", "bad_conclusion")
                   for r in recs3 if r["kind"] in
                   ("action", "concluded", "bad_output", "bad_conclusion")))

    print("=" * 80)
    print("J. 无进展检测：重复同一动作、观测一样 → 被停下来")
    root, reg, recs, _ = go("loop", accept="某可观测结果", kind="leaf")
    np_ = [r for r in recs if r["kind"] == "no_progress"]
    stl = [r for r in recs if r["kind"] == "stalled"]
    acts = [r["payload"]["obs"] for r in recs if r["kind"] == "action"]
    print("  动作次数: %d | 无进展告警: %d | 停下: %s"
          % (len(acts), len(np_), root.verdict))
    print("  告警长这样: %s" % (acts[-1] if acts else "").replace("\n", " "))
    ok &= line("重复被检测到并显式告警", bool(np_))
    ok &= line("告警直接写在观测里（不会被忽略）", bool(acts) and "[停止]" in acts[-1])
    ok &= line("最终自己停下来（不是靠轮次上限）",
               bool(stl) and root.verdict == "未满足", root.conclusion)
    ok &= line("停下时把原因写清楚", "没有新信息" in (root.conclusion or ""))

    print("=" * 80)
    print("H. 检索键：孩子一出生就自动查老树（模型不用自己想起来要查）")
    fake = FakeIndex()
    rootH, regH, recsH, _ = go("newkeywords", index=fake)
    g = [n for n in regH.values() if n.name == "GATE"][0]
    pre = [r for r in recsH if r["kind"] == "precedent"]
    print("  程序发出的查询: %s" % fake.qs[:3])
    print("  给孩子注入的先例: %s" % (g.precedents[0][:40] if g.precedents else "无"))
    ok &= line("按上层给的 keywords 查了（不是模型自己想起来的）",
               any("akshare" in q for qs in fake.qs for q in qs))
    ok &= line("命中结果直接进了孩子的提示词",
               any("假的老树" in p for p in g.precedents))
    ok &= line("根没有上层 → 用它自己的名字+验收标准查",
               any(qs and "ROOT" in qs[0] for qs in fake.qs))
    ok &= line("每个节点一条 precedent 记录（不再有「先例」这个动作）",
               len(pre) == len(regH) and '"先例"' not in R.ALLOC_SYS)
    # 上层给的 conc_range / keywords 必须**真的出现在下层的提示词里**。
    # 提示词里只写"如 [100,500]"是不够的 —— 那是举例，不是上层的判断。
    gin = [r["payload"] for r in recsH
           if r["kind"] == "leaf_in" and r.get("node") == g.id]
    ok &= line("上层给的 conc_range 落到了孩子提示词里（不是举例）",
               bool(gin) and "结论字数要求（上层给的）: [100, 500]" in gin[0])
    ok &= line("上层给的 keywords 也落到了孩子提示词里",
               bool(gin) and "检索键（上层给的" in gin[0])

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
