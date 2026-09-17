#!/usr/bin/env python3
"""索引的定向测试。零成本、确定性。

  A. 返回的是**路径**（祖先判据链），不是散落的节点
  B. 同一脉去重 —— 三条先例不能是同一件事
  C. 数字不能单独构成命中
  D. 虚字 bigram（"到的""的和"）不能构成命中
  E. 老格式的 trace（task/criteria/done）也能读，否则昨晚那棵树就是死数据
  F. 不搜自己那棵树
  G. 结局加权：满足的先例排在前面
  H. 工作目录：只有跟**当前**工作目录相同时才写"工作目录"，
     否则只能写"先例的数据在"（实测：写"工作目录: <老树>"会让模型把
     一个死目录抄进子任务，产出落到老树里去了）
  I. 阻塞枝带回可复核的东西：证据 / 外部需求 / 卡在哪条命令 / 卡住时间
     （DESIGN §2.7：阻塞不是死路。只给一句"做不了"，模型只能照抄）
  J. 老格式的 leaf_tool 也算观测，否则昨晚那棵树答不出"卡在哪"
  K. `notes` 不参与检索（它是自由发挥的判断依据，不是检索键）
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree.index import TreeIndex                      # noqa: E402


def build(spec, workspace="/tmp/ws-x", old_format=False,
          actions=None, ext=None, evid=None, notes=None, t=1789568177.102):
    """spec: [(id, parent, 任务名, 验收标准, 结局, 内容)]

    actions: {节点id: [(工具, 参数, 观测)]} —— 叶子的动作历史。
    ext / evid: {节点id: [...]} —— 阻塞时的外部需求 / 证据。
    notes: {节点id: "..."} —— 注意事项（不参与检索）。
    """
    actions = actions or {}
    ext, evid, notes = ext or {}, evid or {}, notes or {}
    d = tempfile.mkdtemp()
    p = os.path.join(d, "trace.jsonl")
    with open(p, "w") as f:
        for depth, (nid, parent, name, accept, verdict, concl) in enumerate(spec):
            if old_format:
                f.write(json.dumps({"node": nid, "kind": "open", "payload": {
                    "task": name, "criteria": accept, "depth": depth,
                    "parent": parent}, "t": t}, ensure_ascii=False) + "\n")
                # 老格式没有 判定 字段，只能近似：done → 满足，failed → 阻塞
                for tool, args, obs in actions.get(nid, []):
                    f.write(json.dumps({"node": nid, "kind": "leaf_tool",
                                        "payload": {"tool": tool, "args": args,
                                                    "obs": obs}, "t": t},
                                       ensure_ascii=False) + "\n")
                if verdict:
                    f.write(json.dumps({
                        "node": nid,
                        "kind": "failed" if verdict == "阻塞" else "done",
                        "payload": {"result": concl}, "t": t},
                        ensure_ascii=False) + "\n")
            else:
                f.write(json.dumps({"node": nid, "kind": "open", "payload": {
                    "name": name, "accept": accept, "kind": "dispatch",
                    "depth": depth, "parent": parent,
                    "notes": notes.get(nid, ""),
                    "workspace": workspace}, "t": t}, ensure_ascii=False) + "\n")
                for tool, args, obs in actions.get(nid, []):
                    f.write(json.dumps({"node": nid, "kind": "action", "payload": {
                        "tool": tool, "args": args, "obs": obs}, "t": t},
                        ensure_ascii=False) + "\n")
                if verdict:
                    f.write(json.dumps({"node": nid, "kind": "concluded", "payload": {
                        "verdict": verdict, "text": concl,
                        "evidence": evid.get(nid, []),
                        "external": ext.get(nid, [])}, "t": t},
                        ensure_ascii=False) + "\n")
    return p


SPEC = [
    ("r", None, "给公司做一个能赚钱的量化系统", "账户权益在2026-12-31 >= 本金 x 2", "未满足", "账户没开"),
    ("a", "r", "验证策略在历史数据上有正期望", "回测扣费后年化>30% 且样本外有效", "满足", "找到了一个"),
    ("a1", "a", "实现净值序列生成器", "closes=[100,110,99] 时返回长度3的序列", "满足", "通过"),
    ("b", "r", "开户并入金", "账户已入金且可查询", "阻塞", "开户需要人到场"),
    ("c", "r", "构建币种名称到的映射表", "映射表包含至少100种币种", "满足", "建好了"),
]

# I/J 用：一条阻塞枝 + 它卡住的命令历史（4 次，比回放窗口多一次）
SPEC_BLOCK = [
    ("r", None, "给公司做一个能赚钱的量化系统", "账户权益在2026-12-31 >= 本金 x 2", "阻塞", "账户没开"),
    ("b", "r", "开户并入金", "账户已入金且可查询", "阻塞", "开户需要人到场"),
]
ACTIONS = {"b": [
    ("bash", {"cmd": "ls ~/.broker"}, "No such file or directory"),
    ("bash", {"cmd": "python3 account_query.py --open"}, "需要本人到柜台办理"),
    ("bash", {"cmd": "python3 account_query.py --status"}, "{'本金': None, '币种': None}"),
    ("bash", {"cmd": "python3 account_query.py --status"}, "{'本金': None, '币种': None}"),
]}
EXT = {"b": ["需要人到场", "需要真实账户"]}
EVID = {"b": ["第2次观测"]}


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
    print("G/H. 结局加权 + 工作目录只在是当前目录时才这么叫")
    idx3 = TreeIndex([p1, build(SPEC, workspace="/tmp/ws-other")])
    picked, text = idx3.search(["开户并入金"], workspace="/tmp/ws-other")
    print("  %s" % text.replace("\n", " ⏎ "))
    ok &= line("是当前工作目录 → 写成工作目录", "工作目录: /tmp/ws" in text)
    _, text_else = idx3.search(["开户并入金"], workspace="/tmp/somewhere-else")
    print("  %s" % text_else.replace("\n", " ⏎ "))
    ok &= line("不是当前目录 → 不许写成工作目录",
               "工作目录: /tmp/ws" not in text_else)
    ok &= line("但要说清数据在那边、只读",
               "先例的数据在: /tmp/ws" in text_else and "只读" in text_else)

    print("=" * 80)
    print("I. 阻塞枝带回可复核的东西（证据 / 外部需求 / 卡在哪条命令）")
    p_blk = build(SPEC_BLOCK, actions=ACTIONS, ext=EXT, evid=EVID)
    _, text = TreeIndex([p_blk]).search(["开户并入金"])
    print(text)
    ok &= line("外部需求带回来了", "外部需求: 需要人到场、需要真实账户" in text)
    ok &= line("证据带回来了", "证据: 第2次观测" in text)
    ok &= line("卡住时间带回来了", "卡住时间: " in text)
    ok &= line("说了卡在哪条命令", "account_query.py --status" in text)
    ok &= line("说了当时世界回了什么", "币种" in text)
    ok &= line("截断可见（共 4 次，只列最近 3 次）",
               "共 4 次动作" in text and "只列最近 3 次" in text)

    print("=" * 80)
    print("J. 老格式的 leaf_tool 也算观测")
    p_old_blk = build(SPEC_BLOCK, old_format=True, actions=ACTIONS)
    _, text = TreeIndex([p_old_blk]).search(["开户并入金"])
    ok &= line("老格式也说得出来卡在哪条命令", "account_query.py --open" in text)

    print("=" * 80)
    print("K. notes 不参与检索")
    SECRET = "紫色的犀牛在跳舞"
    p_note = build(SPEC, notes={"c": SECRET})
    idx_note = TreeIndex([p_note])
    hit_by_note, _ = idx_note.search([SECRET])
    print("  拿注意事项当查询: 命中 %d 条" % len(hit_by_note))
    ok &= line("notes 里的字不进索引", not hit_by_note)
    hit_named, _ = idx_note.search(["构建币种名称到的映射表"])
    ok &= line("但名字/判据照常检索", bool(hit_named))

    print("=" * 80)
    print("全部通过" if ok else "有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
