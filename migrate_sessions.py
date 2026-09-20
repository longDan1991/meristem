#!/usr/bin/env python3
"""老会话 → 新格式的一次性迁移：把历史 trace 跑一遍，补上 state 检查点。

历史会话（本功能之前生成的）只有 open/concluded 等事件，没有 `state` 检查点，
也没有对话记录 —— `session.load` 读不出树来，`-r` 选了它像新会话一样。
迁移把每个节点的**轮廓和历史**写成 `state` 检查点：之后 `-r` 就能像新会话
一样加载（显示 + 给模型的上下文），没跑完的树能接着跑。

迁移重建历史用的是老格式里**本来就有的**事件，不编造：
  - 叶子观测 <- `action` / `leaf_tool`（当时跑过的每条命令 + 世界回了什么）
  - 分配尝试 <- 实际子节点（open 的字段做 children 规格，concluded 做 results）——
    根/分配节点恢复后看得到"我拆了谁、谁回了什么"，`满足` 的证据校验才过得了

**运行状态当时就没存，迁移恢复不了**：没跑完的节点迁移后带着字段 + 历史重新跑
（这就是"把老数据跑一遍"的意思 —— 不假装能精确续上，只把历史变成新格式）。

幂等：已有 `state` 检查点的会话不动。

用法：uv run python migrate_sessions.py [glob]
默认扫 TREE_INDEX（工作区里所有老会话）。
"""

import glob
import sys

from tree import config as cfg
from tree.memory.index import iter_trace_lines
from tree.protocol.fields import Node
from tree.runtime.trace import Trace


def _node_from_open(p, nid):
    """open 事件的键名新旧都有（name/accept 与 任务名/验收标准/task/criteria），
    全部认 —— 这是一次性迁移，读旧是它的职责，跑完运行时不再读第二种格式。"""
    kind = p.get("kind") or p.get("类型") or "dispatch"
    return Node(
        name=p.get("name") or p.get("任务名") or p.get("task") or "",
        detail=p.get("detail") or p.get("任务详情") or "",
        notes=p.get("notes") or p.get("注意事项") or "",
        accept=p.get("accept") or p.get("验收标准") or p.get("criteria") or "",
        kind=kind,
        gate=bool(p.get("gate")),
        keywords=p.get("keywords") or [],
        conc_range=p.get("conc_range") or [],
        id=nid, parent=p.get("parent"), depth=p.get("depth", p.get("深度", 0)))


def _action_label(p):
    """一次动作的一行标题：命令的第一行（和 code_label 同一思路），没有命令用工具名。"""
    args = p.get("args") or p.get("参数") or {}
    cmd = str(args.get("cmd", "")) if isinstance(args, dict) else ""
    for ln in cmd.splitlines():
        if ln.strip():
            s = ln.strip()
            return s if len(s) <= 200 else s[:200] + "…"
    return p.get("tool") or p.get("工具") or "(动作)"


def _spec(k):
    """子节点 → 分配尝试里的 children 规格（和渲染用的同一套键）。"""
    return {"name": k.name, "detail": k.detail, "notes": k.notes,
            "accept": k.accept, "kind": k.kind, "gate": k.gate,
            "keywords": k.keywords, "conc_range": k.conc_range}


def _record(k):
    """子节点 → 分配尝试里的 results 记录（和 node.record() 同一套键）。"""
    return {"name": k.name, "accept": k.accept, "outcome": k.verdict,
            "text": k.conclusion, "evidence": k.evidence,
            "id": k.id, "kind": k.kind}


def migrate(path):
    """一场会话。返回是否真的迁移了。"""
    has_state = False
    nodes = {}
    leaf_signal = set()              # nid：跑过叶子动作（action/leaf_tool/leaf_start）
    observations = {}                # nid -> 叶子的观测（action/leaf_tool）
    for r in iter_trace_lines(path):
        k, p = r.get("kind"), r.get("payload") or {}
        nid = r.get("node")
        if k == "state":
            has_state = True
        elif k == "open" and nid:
            nodes[nid] = _node_from_open(p, nid)
        elif k == "concluded" and nid in nodes:
            nodes[nid].close(p.get("verdict") or p.get("判定") or "未满足",
                             p.get("text") or p.get("内容") or "",
                             p.get("evidence") or p.get("证据") or [],
                             p.get("external") or p.get("外部需求") or [])
        elif k == "done" and nid in nodes:                  # 旧格式：done
            nodes[nid].close("满足", str(p.get("result", "")), [])
        elif k in ("failed", "crashed", "budget_exhausted") and nid in nodes:
            why = p.get("result") if isinstance(p, dict) else None
            nodes[nid].close("阻塞", str(why if why else p), [])
        elif k in ("action", "leaf_tool", "leaf_start") and nid in nodes:
            leaf_signal.add(nid)
            if k in ("action", "leaf_tool"):
                observations.setdefault(nid, []).append(
                    {"action": _action_label(p),
                     "obs": str(p.get("obs") or p.get("观测") or "")})
    if has_state or not nodes:
        return False
    # 孩子链接：调度器正常流程里由 _spawn 填，迁移要从 parent 链接重建 ——
    # 否则 state 里的节点没有 children，恢复时整棵树塌缩成只剩根。
    for nid, n in nodes.items():
        if n.parent and n.parent in nodes:
            nodes[n.parent].children.append(nid)
    # 角色推断：老格式的 kind 是"类别"（evidence/infra/…）不是"角色"，
    # 用事件说话 —— split 过的是分配节点，跑过叶子动作的是叶子，
    # 刚出生还没动过的默认分配节点（它总能派一个叶子把活干了）。
    for nid, n in nodes.items():
        kids = [c for c in nodes.values() if c.parent == nid]
        if kids:
            n.kind = "dispatch"
        elif nid in leaf_signal:
            n.kind = "leaf"
        else:
            n.kind = "dispatch"
    # 历史重建（老格式里本来就有的事件，不编造）：
    #  · 叶子：观测历史 <- action/leaf_tool —— 恢复后叶子知道自己试过什么；
    #  · 分配节点：一次尝试（children 规格 + 已完工孩子的 results）—— 恢复后
    #    根看得到"拆了谁、谁回了什么"，`满足` 的证据校验才指得到真实子节点。
    for nid, n in nodes.items():
        kids = [c for c in nodes.values() if c.parent == nid]
        if n.kind == "leaf":
            n.observations = observations.get(nid, [])
        elif kids:
            done = [c for c in kids if c.status == "done"]
            n.attempts = [{"children": [_spec(c) for c in kids],
                           "results": [_record(c) for c in done],
                           "outcome": "下层已全部返回" if len(done) == len(kids)
                           else "等下层"}]
    tr = Trace(path)
    for n in nodes.values():
        tr.add(n.id, "state", {
            "node": n.to_dict(),
            "ready": True, "finished": n.status == "done",
            "waiting": 0, "rest": [], "gate_id": None, "gate_name": None,
            "calls": [], "contracts": [], "artifacts": [], "art_effects": {}})
    tr.drain()
    return True


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else cfg.INDEX_GLOB
    moved = skipped = failed = 0
    for t in sorted(glob.glob(pat)):
        try:
            ok = migrate(t)
        except (ValueError, OSError) as e:
            # 记录损坏（中间坏行）或文件打不开：报出是哪个会话，继续下一个
            print("失败: %s  %s" % (t, e), flush=True)
            failed += 1
            continue
        print("%s %s" % ("迁移" if ok else "跳过", t), flush=True)
        moved += bool(ok)
        skipped += not ok
    print("完成：迁移 %d，跳过 %d，失败 %d" % (moved, skipped, failed), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
