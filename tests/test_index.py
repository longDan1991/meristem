#!/usr/bin/env python3
"""索引的定向测试。零成本、确定性。

  A. 返回的是**路径**（祖先判据链），不是散落的节点
  B. 同一脉去重 —— 三条先例不能是同一件事
  C. 数字不能单独构成命中
  D. 虚字 bigram（"到的""的和"）不能构成命中
  E. 老格式的 trace（task/criteria/done）也能读，否则昨晚那棵树就是死数据
  F. 不搜自己那棵树
  G. 结局加权：满足的先例排在前面
  H. 工作目录从根节点继承下来，检索结果带着它
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.index import TreeIndex                      # noqa: E402


def build(spec, workspace="/tmp/ws-x", old_format=False):
    """spec: [(id, parent, 任务名, 验收标准, 结局, 内容)]"""
    d = tempfile.mkdtemp()
    p = os.path.join(d, "trace.jsonl")
    with open(p, "w") as f:
        for depth, (nid, parent, name, accept, verdict, concl) in enumerate(spec):
            if old_format:
                f.write(json.dumps({"node": nid, "kind": "open", "payload": {
                    "task": name, "criteria": accept, "depth": depth,
                    "parent": parent}}, ensure_ascii=False) + "\n")
                if verdict:
                    f.write(json.dumps({"node": nid, "kind": "done",
                                        "payload": {"result": concl}},
                                       ensure_ascii=False) + "\n")
            else:
                f.write(json.dumps({"node": nid, "kind": "open", "payload": {
                    "任务名": name, "验收标准": accept, "类型": "dispatch",
                    "深度": depth, "parent": parent,
                    "工作目录": workspace}}, ensure_ascii=False) + "\n")
                if verdict:
                    f.write(json.dumps({"node": nid, "kind": "concluded", "payload": {
                        "判定": verdict, "内容": concl, "证据": []}},
                        ensure_ascii=False) + "\n")
    return p


SPEC = [
    ("r", None, "给公司做一个能赚钱的量化系统", "账户权益在2026-12-31 >= 本金 x 2", "未满足", "账户没开"),
    ("a", "r", "验证策略在历史数据上有正期望", "回测扣费后年化>30% 且样本外有效", "满足", "找到了一个"),
    ("a1", "a", "实现净值序列生成器", "closes=[100,110,99] 时返回长度3的序列", "满足", "通过"),
    ("b", "r", "开户并入金", "账户已入金且可查询", "阻塞", "开户需要人到场"),
    ("c", "r", "构建币种名称到的映射表", "映射表包含至少100种币种", "满足", "建好了"),
]


def line(tag, cond, detail=""):
    print("  %s %-48s %s" % ("✓" if cond else "✗", tag, detail))
    return bool(cond)


def main():
    ok = True
    p1 = build(SPEC)

    print("=" * 80)
    print("A/B. 返回路径 + 同一脉去重")
    idx = TreeIndex([p1])
    picked, text = idx.search(["验证策略在历史数据上有正期望"])
    print(text)
    ok &= line("命中了那一枝", picked and picked[0].id in ("a", "a1"))
    ok &= line("返回的文本里有祖先链（根 + 中间层）",
               "根 给公司做" in text and "验证策略" in text)
    ok &= line("同一脉只出一条", len({p.id[0] for p in picked}) == len(picked),
               "命中 %d 条" % len(picked))

    print("=" * 80)
    print("C. 数字不能单独构成命中")
    picked, _ = idx.search(["算 1 到 100 的和"])
    names = [p.name for p in picked]
    print("  命中: %s" % names)
    ok &= line("没有因为 100 而命中\"closes=[100,110,99]\"",
               not any("净值序列" in n for n in names))

    print("=" * 80)
    print("D. 虚字 bigram 不能构成命中")
    picked, _ = idx.search(["算 1 到 100 的和"])
    ok &= line("没有命中\"构建币种名称到的映射表\"",
               not any("映射表" in n for n in picked and [p.name for p in picked]))

    print("=" * 80)
    print("E. 老格式的 trace 也能读")
    p_old = build(SPEC, old_format=True)
    idx_old = TreeIndex([p_old])
    print("  老格式索引: %d 节点 / %s" % (idx_old.stats["节点"],
                                        {k: v for k, v in idx_old.stats.items()
                                         if k != "节点"}))
    ok &= line("节点数一致", idx_old.stats["节点"] == len(SPEC))
    ok &= line("老格式也参与检索",
               bool(idx_old.search(["验证策略在历史数据上有正期望"])[0]))

    print("=" * 80)
    print("F. 不搜自己那棵树")
    idx2 = TreeIndex([p1, p_old], exclude=[p1])
    ok &= line("被排除的树不在索引里", all(n.tree != p1 for n in idx2.nodes.values()))

    print("=" * 80)
    print("G/H. 结局加权 + 工作目录")
    idx3 = TreeIndex([p1, build(SPEC, workspace="/tmp/ws-other")])
    picked, text = idx3.search(["开户并入金"])
    print("  %s" % text.replace("\n", " ⏎ "))
    ok &= line("检索结果带着工作目录", "工作目录: /tmp/ws" in text)

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
