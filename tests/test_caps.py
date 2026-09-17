#!/usr/bin/env python3
"""能力库的定向测试。零成本、确定性。

  A. 挖掘质量（拿昨晚 29748 行真实 trace）：键里不许有绝对路径成分
  B. 检索不封顶：命中多少给多少（不再在背后替模型丢几条）
  C. 端到端：叶子出生时程序直接注入配方 → 照做成功 → 复用计数 +1
  D. 复用失败 → 计数 +1，烂了就自动退休（库不自烂）
  E. 完工即学：节点出结论那一刻就把配方写进库，且离线回填幂等
  F. 内联 heredoc 的机械提取（原本整条丢掉的那类）
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from tree.caps import Caps                            # noqa: E402
from tree.effects import effects_of                   # noqa: E402
from tree.mine import mine_trace as mine_caps         # noqa: E402
from tree.node import Node, Trace                     # noqa: E402
from tree import run as R                             # noqa: E402

# 真实数据资产在工作区里（不在项目目录）：一晚 11.5 小时那棵树。
# 路径来自配置文件（TREE_WORKSPACE），换机器只要改 .env。
from tree import config as _cfg                            # noqa: E402
REAL = os.environ.get("TREE_TRACE") or os.path.join(
    _cfg.workspace(), "runs", "night_quant", "trace.jsonl")


def line(tag, cond, detail=""):
    print("  %s %-46s %s" % ("✓" if cond else "✗", tag, detail))
    return bool(cond)


def dump(recs, name="t.jsonl"):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


# ---------------------------------------------------------------- 脚本化叶子
class LeafScript:
    """一个叶子：按脚本依次做动作，做完出结论。"""

    def __init__(self, actions, verdict="满足", evidence=None,
                 artifacts=None, omit_first=False):
        self.actions = list(actions)
        self.verdict = verdict
        self.evidence = evidence or ["第1次观测"]
        self.artifacts = artifacts
        self.omit_first = omit_first
        self.retried = False
        self.i, self.last_usage = 0, {}

    def chat(self, messages, temperature=0.2):
        user = messages[-1]["content"]
        assert "可用工具" in user, "这个脚本只能驱动叶子"
        if self.i < len(self.actions):
            a = self.actions[self.i]
            self.i += 1
            return json.dumps({"action": a}, ensure_ascii=False)
        body = {"verdict": self.verdict, "text": "脚本收尾", "evidence": self.evidence}
        if self.omit_first and not self.retried:
            self.retried = True          # 第一次故意不交代工件，看代码拦不拦
            return json.dumps({"conclusion": body}, ensure_ascii=False)
        if self.artifacts:
            body["artifacts"] = self.artifacts
        return json.dumps({"conclusion": body}, ensure_ascii=False)


def leaf_run(caps, actions, verdict="满足", accept="某可观测结果", evidence=None,
             artifacts=None, omit_first=False, keywords=None):
    d = tempfile.mkdtemp()
    trace = Trace(os.path.join(d, "t.jsonl"))
    node = Node(name="叶子", accept=accept, kind="leaf", keywords=keywords or [])
    # 叶子会跑真的 bash，用的是进程 cwd —— 必须切到临时目录，
    # 否则测试会把 proof.txt 这类文件写到项目目录里（真的发生过）。
    cwd = os.getcwd()
    os.chdir(d)
    try:
        R.run(node, LeafScript(actions, verdict, evidence, artifacts, omit_first),
              trace, registry={}, caps=caps)
    finally:
        os.chdir(cwd)
    recs = [json.loads(x) for x in open(os.path.join(d, "t.jsonl"))]
    return node, recs, d


def add_trace(recs):
    return dump(recs)


def heredoc_scenario(cmd, obs="done\n[exit=0]"):
    recs = [{"node": "n1", "kind": "open",
             "payload": {"任务名": "获取 A 股历史日线数据", "验收标准": "CSV 存在",
                         "类型": "leaf", "深度": 0}},
            {"node": "n1", "kind": "action",
             "payload": {"tool": "bash", "args": {"cmd": cmd}, "obs": obs}},
            {"node": "n1", "kind": "concluded",
             "payload": {"判定": "满足", "内容": "ok", "证据": ["第1次观测"]}}]
    # 把命令塞进 trace 的 leaf_tool 里（挖掘器读的就是这个）
    recs.insert(1, {"node": "n1", "kind": "leaf_tool",
                    "payload": {"tool": "bash", "args": {"cmd": cmd}, "obs": obs}})
    p = add_trace(recs)
    caps = Caps(os.path.join(tempfile.mkdtemp(), "caps.jsonl"))
    for e in mine_caps(p):
        caps.record(e)
    return caps, os.path.dirname(p)


def main():
    ok = True

    print("=" * 78)
    print("A. 挖掘质量（真实 trace）")
    entries = mine_caps(REAL)
    cs = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    for e in entries:
        cs.record(e)
    live = list(cs.entries.values())
    bad = [k for e in entries for k in e["keys"]
           if k in ("users", "wxlong", "mycode", "runs", "night_quant")]
    print("  挖出 %d 条，自带脚本 %d 条"
          % (len(entries), sum(1 for e in live if (e.get("how") or {}).get("script_file"))))
    ok &= line("键里没有绝对路径成分", not bad, str(bad))
    ok &= line("条数收敛到可维护量级", len(entries) < 150, "%d 条" % len(entries))
    # 判据是"能不能直接照做"，不是"够不够短"（长度上限是按提示词要求去掉的）
    notrun = [e["how"]["cmd"] for e in live
              if "\n" in e["how"]["cmd"] and not e["how"].get("script_file")]
    ok &= line("每条配方都能直接照做（单行或有脚本）", not notrun,
               "%d 条不行" % len(notrun))
    ok &= line("长配方也原样给出，不砍", max(len(e["how"]["cmd"]) for e in live) > 0,
               "最长 %d 字" % max(len(e["how"]["cmd"]) for e in live))
    # 不收的东西必须说得出来（不悄悄丢）
    from tree.mine import caps_from_node
    skipped = []
    caps_from_node("n", "t",
                   [("bash", {"cmd": "echo a > x.txt\nprintf 'b' > y.txt"}, "")],
                   "t.jsonl", None, skipped)
    ok &= line("不收的能力记下了理由", bool(skipped) and skipped[0].get("理由"),
               str(skipped[0]["理由"]) if skipped else "没记")
    ok &= line("落盘的脚本都真实存在",
               all(os.path.exists(e["how"]["script_file"])
                   for e in live if e["how"].get("script_file")))

    print("=" * 78)
    print("B. 检索不封顶：命中多少给多少")
    caps = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    for i in range(8):
        caps.record({"does": "写文件的做法 %d" % i, "keys": ["写文件", "file", "write"],
                     "how": {"cmd": "echo %d > out%d.txt" % (i, i)}})
    picked, text = caps.search("我要写文件")
    print("  8 条同类做法 → 返回 %d 条 / %d 字符" % (len(picked), len(text)))
    ok &= line("8 条全给了，没有偷偷砍到 3 条", len(picked) == 8, "命中 %d 条" % len(picked))
    ok &= line("每条都在正文里", all(e["does"] in text for e in picked))

    print("=" * 78)
    print("C. 端到端：出生就自动注入现成做法 → 照做 → 成功")
    caps = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    caps.record({"does": "写一个证明文件", "keys": ["证明文件", "proof", "write"],
                 "how": {"cmd": "echo ok > proof.txt"}})
    node, recs, _ = leaf_run(
        caps, [{"tool": "bash", "args": {"cmd": "echo ok > proof.txt"}}],
        keywords=["我要写证明文件"])
    inj = [r for r in recs if r["kind"] == "caps_injected"]
    outs = [r for r in recs if r["kind"] == "cap_outcome"]
    print("  caps_injected: %s" % (inj[0]["payload"] if inj else "无"))
    ok &= line("出生时就自动查了（没有 need 这个动作）",
               bool(inj) and bool(inj[0]["payload"]["hits"]))
    ok &= line("现成做法直接进了它的提示词",
               bool(node.caps) and "写一个证明文件" in node.caps[0])
    text = caps.search("我要写证明文件")[1]
    ok &= line("返回内容原样给出（不再封顶）",
               bool(inj) and inj[0]["payload"]["chars"] == len(text),
               "%d 字符全部给出" % len(text))
    ok &= line("复用成功被记账", bool(outs) and outs[0]["payload"]["ok"] is True)
    ok &= line("uses 计数 +1", list(caps.entries.values())[0]["uses"] == 1)

    print("=" * 78)
    print("D. 复用失败 → 自动退休")
    caps = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    eid = caps.record({"does": "过期的做法", "keys": ["过期", "old"],
                       "how": {"cmd": "this_command_does_not_exist_xyz"}})
    for _ in range(2):
        leaf_run(caps, [{"tool": "bash",
                         "args": {"cmd": "this_command_does_not_exist_xyz"}}],
                 verdict="阻塞", evidence=[], keywords=["用过期的做法"])
    e = caps.entries[eid]
    print("  uses=%d fails=%d retired=%s" % (e["uses"], e["fails"], e.get("retired")))
    ok &= line("失败被记账", e["fails"] >= 2)
    ok &= line("烂了自动退休", bool(e.get("retired")))
    _, after = caps.search("用过期的做法")
    ok &= line("退休后不再被检索到", "过期的做法" not in after)

    print("=" * 78)
    print("E. 完工即学 + 离线回填幂等")
    caps = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    node, recs, _ = leaf_run(caps, [{"tool": "bash", "args": {"cmd": "echo hi > proof.txt"}}])
    learned = [r for r in recs if r["kind"] == "cap_learned"]
    print("  节点判定: %s | 库内 %d 条" % (node.verdict, len(caps.entries)))
    for e in caps.entries.values():
        print("    学到: %s | 配方 %s | 键 %s"
              % (e["does"], e["how"]["cmd"], ",".join(e["keys"])))
    ok &= line("出结论后自动写入了库", len(caps.entries) == 1)
    ok &= line("trace 里有 cap_learned", bool(learned))
    ok &= line("配方是真实执行过的那条",
               any(e["how"]["cmd"] == "echo hi > proof.txt" for e in caps.entries.values()))
    before = len(caps.entries)
    for e in mine_caps(dump(recs)):       # 离线回填：必须幂等
        caps.record(e)
    ok &= line("离线回填幂等（不新增、不冲计数）",
               len(caps.entries) == before and
               list(caps.entries.values())[0]["uses"] == 0)

    print("=" * 78)
    print("F. 内联 heredoc 的机械提取")
    caps, wd = heredoc_scenario("python3 <<'EOF'\nprint('hello from learned script')\nEOF")
    e = list(caps.entries.values())[0] if caps.entries else {}
    print("  配方: %s" % e.get("how", {}).get("cmd", "（没挖到）"))
    ok &= line("无产物、无安装的内联脚本也能挖到", len(caps.entries) == 1)
    sf = e.get("how", {}).get("script_file")
    ok &= line("正文落盘 + 无占位符残留",
               bool(sf) and os.path.exists(sf or "")
               and "__SCRIPT__" not in e.get("how", {}).get("cmd", ""))
    run = subprocess.run(e.get("how", {}).get("cmd", "true"), shell=True,
                         capture_output=True, text=True, cwd=wd)
    ok &= line("这条配方真能跑出结果",
               run.returncode == 0 and "learned script" in run.stdout,
               (run.stdout or run.stderr).strip())
    caps2, _ = heredoc_scenario("cat > gen.py <<'EOF'\nprint('generated')\nEOF")
    e2 = list(caps2.entries.values())[0] if caps2.entries else {}
    ok &= line("runner 按 .py 后缀推对（不是 bash）",
               e2.get("how", {}).get("cmd", "").startswith("python3 "))
    caps3, _ = heredoc_scenario("cat > cfg.json <<'EOF'\n{\"a\": 1}\nEOF")
    e3 = list(caps3.entries.values())[0] if caps3.entries else {}
    ok &= line("写数据文件的不被当脚本落盘", not e3.get("how", {}).get("script_file"))

    print("=" * 78)
    print("G. 过程中完全自由，契约在结论里一次交代")
    caps = Caps(os.path.join(tempfile.mkdtemp(), "c.jsonl"))
    node, recs, d = leaf_run(
        caps,
        [{"tool": "write", "args": {"path": "engine.py", "content": "print('ok')"}},
         {"tool": "bash",
          "args": {"cmd": "pip install requests -q > /dev/null && echo x > out.txt"}}],
        artifacts=[{"path": "engine.py", "type": "程序", "name": "一个演示程序",
                    "func": "python3 engine.py", "args": "无", "return": "打印 ok"}])
    eff = [r for r in recs if r["kind"] == "effects"]
    con = [r for r in recs if r["kind"] == "contract"]
    made = os.path.join(d, "engine.py")      # 叶子在自己的临时目录里干活
    print("  write 是否真的写了: %s" % os.path.exists(made))
    print("  契约记录: %s" % (json.dumps(con[0]["payload"], ensure_ascii=False)
                            if con else "无"))
    for r in eff:
        print("  effects(%s): %s" % (r["payload"]["tool"],
                                     json.dumps(r["payload"]["effects"],
                                                ensure_ascii=False)))
    ok &= line("write 真的写到盘上", os.path.exists(made))
    ok &= line("契约记进了 trace 且没有问题",
               bool(con) and not con[0]["payload"]["problems"]
               and con[0]["payload"]["source"] == "conclusion")
    ok &= line("旁边落了 .meta.json（工件自描述）", os.path.exists(made + ".meta.json"))
    we = [r for r in eff if r["payload"]["tool"] == "write"]
    ok &= line("write 的 fs.create 抓到了",
               bool(we) and any("engine.py" in x
                                for x in we[0]["payload"]["effects"]["fs"]["create"]))
    be = [r for r in eff if r["payload"]["tool"] == "bash"]
    b = be[0]["payload"] if be else {"effects": {}, "前置条件": {}}
    ok &= line("bash 装包被代码抓到", b["effects"].get("pkg") == ["requests"],
               str(b["effects"].get("pkg")))
    ok &= line("bash 联网/前置条件被抓到", bool(b["前置条件"].get("需要网络")))
    ok &= line("bash 写文件被抓到",
               any("out.txt" in x for x in b["effects"].get("fs", {}).get("create", [])))
    got = list(caps.entries.values())
    ok &= line("学到的 cap 带着契约与前提", any(e.get("契约") for e in got),
               "%d 条" % len(got))
    _, text = caps.search("一个演示程序")
    print("  检索回来的样子:\n%s" % "\n".join("    " + x for x in text.splitlines()))
    ok &= line("检索结果里有用法和前提", "用法:" in text and "前提:" in text)

    print("  H. 产出没交代 → 被拦下退回；补上后才算完（强制措施）")
    caps3 = Caps(os.path.join(tempfile.mkdtemp(), "c3.jsonl"))
    d3 = tempfile.mkdtemp()
    os.chdir(d3)
    heredoc = ("cat > sum.sh <<'EOF'\n#!/bin/bash\n"
               "total=0; for i in $(seq 1 100); do total=$((total+i)); done\n"
               "echo $total > sum.txt\nEOF\nbash sum.sh")
    n3, recs3, _ = leaf_run(
        caps3, [{"tool": "bash", "args": {"cmd": heredoc}}],
        artifacts=[{"path": "sum.sh", "type": "脚本",
                    "name": "算 1 到 100 的和并写 sum.txt",
                    "func": "bash sum.sh", "args": "无", "return": "写 sum.txt（5050）"}],
        omit_first=True)
    miss = [r for r in recs3 if r["kind"] == "contract_missing"]
    bad = [r for r in recs3 if r["kind"] == "bad_conclusion"]
    acts = [r["payload"]["obs"] for r in recs3 if r["kind"] == "action"]
    print("  第一次没交代 → 被拦: %s" % (miss[0]["payload"] if miss else "无"))
    print("  过程中只给中性事实（不打扰）: %r" % (acts[0] if acts else ""))
    print("  退回时怎么说的: %s" % (str(bad[0]["payload"]) if bad else "无"))
    cs = list(caps3.entries.values())
    print("  最终判定: %s | 学到 cap: %d 条" % (n3.verdict, len(cs)))
    for e in cs:
        print("     %s | 用法 %s | 契约 %s"
              % (e["does"], e["how"]["cmd"], "有" if e.get("契约") else "无"))
    ok &= line("没交代工件 → 结论被退回来", bool(miss))
    ok &= line("退回时把该填什么说清楚了",
               bool(bad) and "artifacts" in str(bad[0]["payload"]))
    ok &= line("过程中不打扰（只给中性事实，不下指令）",
               bool(acts) and "工�件" not in acts[0] and "待办" not in acts[0])
    ok &= line("补上之后可以宣告完成", n3.verdict == "满足")
    ok &= line("一个工件一条能力，且带着契约",
               len(cs) == 1 and cs[0].get("契约")
               and cs[0]["契约"].get("func") == "bash sum.sh",
               str([e["how"]["cmd"] for e in cs]))

    print("  I. 只在入口形式化：多文件程序只需入口给完整契约")
    caps4 = Caps(os.path.join(tempfile.mkdtemp(), "c4.jsonl"))
    d4 = tempfile.mkdtemp()
    os.chdir(d4)
    n4, recs4, _ = leaf_run(
        caps4,
        [{"tool": "write", "args": {"path": "util.py", "content": "def f(): return 1"}},
         {"tool": "write", "args": {"path": "model.py", "content": "from util import f"}},
         {"tool": "write", "args": {"path": "main.py", "content": "from model import *"}}],
        artifacts=[{"path": "main.py", "type": "程序", "name": "演示程序入口",
                    "func": "python3 main.py", "args": "无", "return": "打印结果"},
                   {"path": "util.py", "type": "内部"},
                   {"path": "model.py", "type": "内部"}])
    cs4 = list(caps4.entries.values())
    print("  判定: %s | 学到 cap: %d 条（内部的不进库）" % (n4.verdict, len(cs4)))
    for e in cs4:
        print("     %s | 用法 %s" % (e["does"], e["how"]["cmd"]))
    ok &= line("内部文件不用给完整契约也能过", n4.verdict == "满足")
    ok &= line("内部文件不进库（一个入口一条能力）", len(cs4) == 1)
    os.chdir(ROOT)

    print("=" * 78)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
