#!/usr/bin/env python3
"""老会话 → 新格式的一次性迁移：把整场会话收成一棵**入口为根的树**。

新格式的不变量：一场会话 = 一棵树，入口节点（kind="intake"）是根，谈成的任务
都是它的孩子。检查点只有两样：Node 全字段 + 平铺对话（msgs）—— 历史只活在一处。

历史老会话有两种，都在这里一次迁移掉：
  · 老格式：只有 open/concluded 等事件，没有 state 检查点；任务根 parent=None，
    历史（叶子的每次动作、分配节点的尝试）从事件重建成对话消息；
  · 过渡格式：有 state 检查点，但没有入口根 —— 任务还是各自 parent=None 的
    树，入口对话在 `chat_*` 事件里。
两种都归到：建一个入口节点（msgs = 旧的 chat_*），把那些 parent=None 的任务根
挂成它的孩子。

**运行状态当时就没存，迁移恢复不了**：没跑完的节点迁移后带着字段 + 历史重新跑
（这就是"把老数据跑一遍"的意思 —— 不假装能精确续上，只把历史变成新格式）。

幂等：已经有入口根的会话不动。

用法：uv run python migrate_sessions.py [glob]
默认扫 TREE_INDEX（工作区里所有老会话）。
"""

import glob
import json
import sys

from tree.prompts.messages import child_result
from tree.protocol.fields import Node
from tree.runtime.trace import Trace, get_traces, iter_trace_lines


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
        conc_range=p.get("conc_range") or [],
        id=nid, parent=p.get("parent"), depth=p.get("depth", p.get("深度", 0)))


def _action_label(p):
    """一次动作的一行标题：命令的第一行，没有命令用工具名。"""
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
            "conc_range": k.conc_range}


def _msgs_from_old(node, observations, attempts):
    """老格式的历史 → 新格式的平铺对话（历史只活在一处）。

    叶子：每次动作重建成一个工具轮次（assistant 的 tool_call + tool 结果）——
    这样「第 N 次观测」的证据校验指得到（观测序号 = 对话里的工具轮数）。
    老格式丢了参数，action 标签就是当时做过的事，不编造更多。
    分配节点：「本层已有尝试」+ 每条下层结论（child_result，带 id 标记）。
    """
    out = []
    if node.kind == "leaf":
        for i, o in enumerate(observations, 1):
            tid = "migrated_%d" % i
            out.append({"role": "assistant", "content": None,
                        "tool_calls": [{"id": tid, "type": "function",
                                        "function": {"name": "bash",
                                                     "arguments": json.dumps(
                                                         {"cmd": o.get("action", "")},
                                                         ensure_ascii=False)}}]})
            out.append({"role": "tool", "tool_call_id": tid,
                        "content": o.get("obs", "")})
    else:
        for a in attempts:
            out.append({"role": "user", "content": "本层已有尝试: %s"
                        % (a.get("rejected")
                           or " ".join(c.get("name", "") for c in a.get("children", [])))})
            for r in a.get("results", []):
                out.append({"role": "user", "content": child_result(r)})
    return out


def _collect(path):
    """扫一遍 trace，返回 (chat, states, old_nodes, observations, leaf_signal)。"""
    chat, states, old_nodes = [], {}, {}
    observations, leaf_signal = {}, set()
    for r in iter_trace_lines(path):
        k, p, nid = r.get("kind"), r.get("payload") or {}, r.get("node")
        if k == "state":
            states[nid] = p
        elif k == "chat_user":
            chat.append({"role": "user", "content": p.get("text")})
        elif k == "chat_model":
            m = {"role": "assistant", "content": p.get("text") or ""}
            if p.get("tool_calls"):
                m["tool_calls"] = p["tool_calls"]
            chat.append(m)
        elif k == "chat_tool":
            chat.append({"role": "tool", "tool_call_id": p.get("tool_call_id"),
                         "content": p.get("content")})
        elif k == "open" and nid:
            old_nodes[nid] = _node_from_open(p, nid)
        elif k == "concluded" and nid in old_nodes:
            old_nodes[nid].close(p.get("verdict") or p.get("判定") or "未满足",
                                 p.get("text") or p.get("内容") or "",
                                 p.get("evidence") or p.get("证据") or [],
                                 p.get("external") or p.get("外部需求") or [])
        elif k == "done" and nid in old_nodes:                  # 旧格式：done
            old_nodes[nid].close("满足", str(p.get("result", "")), [])
        elif k in ("failed", "crashed", "budget_exhausted") and nid in old_nodes:
            why = p.get("result") if isinstance(p, dict) else None
            old_nodes[nid].close("阻塞", str(why if why else p), [])
        elif k in ("action", "leaf_tool", "leaf_start") and nid in old_nodes:
            leaf_signal.add(nid)
            if k in ("action", "leaf_tool"):
                observations.setdefault(nid, []).append(
                    {"action": _action_label(p),
                     "obs": str(p.get("obs") or p.get("观测") or "")})
    return chat, states, old_nodes, observations, leaf_signal


def _nodes_from_old(old_nodes, observations, leaf_signal):
    """老格式的事件 → {nid: Node} + {nid: msgs}（孩子链 + 角色推断 + 历史重建）。"""
    for nid, n in old_nodes.items():
        if n.parent and n.parent in old_nodes:
            old_nodes[n.parent].children.append(nid)
    attempts = {}
    for nid, n in old_nodes.items():
        kids = [c for c in old_nodes.values() if c.parent == nid]
        if kids:
            n.kind = "dispatch"
            done = [c for c in kids if c.verdict]
            attempts[nid] = [{"children": [_spec(c) for c in kids],
                              "results": [{"name": c.name, "accept": c.accept,
                                           "outcome": c.verdict,
                                           "text": c.conclusion,
                                           "evidence": c.evidence,
                                           "id": c.id, "kind": c.kind}
                                          for c in done],
                              "rejected": ""}]
        elif nid in leaf_signal:
            n.kind = "leaf"
        else:
            n.kind = "dispatch"
    msgs = {nid: _msgs_from_old(n, observations.get(nid, []), attempts.get(nid, []))
            for nid, n in old_nodes.items()}
    return old_nodes, msgs


def migrate(path):
    """一场会话：把任务根挂到一个新建的入口节点下，写成新格式。返回是否迁移了。"""
    chat, states, old_nodes, observations, leaf_signal = _collect(path)
    if states:
        nodes = {nid: Node.from_dict(p["node"]) for nid, p in states.items()}
        if any(n.kind == "intake" and n.parent is None for n in nodes.values()):
            return False                       # 已经有入口根 → 新格式，不动
        msgs = {nid: p.get("msgs", []) for nid, p in states.items()}
    elif old_nodes:
        nodes, msgs = _nodes_from_old(old_nodes, observations, leaf_signal)
    else:
        return False
    roots = [n for n in nodes.values() if n.parent is None]
    intake = Node(name="会话", kind="intake")
    intake.children = [n.id for n in roots]
    for n in roots:
        n.parent = intake.id
        n.depth = 1
    nodes[intake.id] = intake
    msgs[intake.id] = chat
    tr = Trace(path)
    tr.add(intake.id, "open", {"kind": "intake", "name": "会话", "parent": None})
    for nid, n in nodes.items():
        tr.add(nid, "state", {"node": n.to_dict(), "msgs": msgs.get(nid, [])})
    tr.drain()
    return True


def main():
    if len(sys.argv) > 1:
        files = sorted(glob.glob(sys.argv[1]))
    else:
        files = get_traces()
    moved = skipped = failed = 0
    for t in files:
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
    print("迁移 %d，跳过 %d，失败 %d" % (moved, skipped, failed), flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
