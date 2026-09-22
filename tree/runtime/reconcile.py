"""编排的纯逻辑：调度器与恢复共用的一处。

节点没有状态字段（没有 finished / waiting / ready / gate_id / rest）。它只是一棵
带对话（msgs）的 Node。两个问题从这里回答，两边各用一份：

  · `actionable` —— 该不该让这个节点调 LLM：没出结论 + 孩子都回话了 + 最后一条
    不是模型自己说的（在等人/等下层）。调度器排队、恢复重建队列都靠它；
  · `settle` —— 孩子出结论怎么结算：结果投进父节点对话（带 id 标记）、
    门槛续跑/作废。运行时（孩子 Loop 返回 stop）和恢复（补投递崩溃窗口里
    没结算的孩子）都走这里。

结算是原子的：调用方在 settle 之后才落检查点，所以"结果出现在对话里" ⟺
"结算跑完了"。恢复据此判断哪些孩子要补投递（`prompts.messages.result_ids`），
不会重复结算。

`deferred`（门槛的暂缓规格）是节点上唯一"计划"性质的数据：那些孩子还没出生，
无处可推，只能存着。
"""

from ..prompts.messages import child_result
from ..protocol.fields import Node


def gate_child(node, registry):
    """父节点唯一带 gate 标记的孩子（一次分配最多一个门槛，代码强制）。"""
    for cid in node.children:
        c = registry.get(cid)
        if c and c.gate:
            return c
    return None


def make_child(parent, spec):
    """把一份子任务规格变成孩子节点（parent 的 children 同步追加）。"""
    kid = Node(name=spec["name"], detail=spec["detail"],
               notes=spec.get("notes") or "",
               accept=spec["accept"], kind=spec["kind"],
               gate=bool(spec.get("gate")),
               conc_range=spec.get("conc_range") or [],
               parent=parent.id, depth=parent.depth + 1,
               lineage=parent.lineage + [[parent.name, parent.detail]])
    parent.children.append(kid.id)
    return kid


def actionable(node, msgs, delivered):
    """该不该让这个节点跑：没出结论、孩子都回话了、最后一条不是模型自己说的。

    delivered：已经投递过结果的孩子 id 集合（运行时维护；恢复时从对话里的
    `（id:…）` 标记重建）。
    """
    if node.verdict:
        return False
    if any(cid not in delivered for cid in node.children):
        return False
    last = msgs[-1] if msgs else None
    if last and last.get("role") == "assistant":
        return False
    return True


def settle(parent, child, delivered, registry, *,
           inject, trace_add=None, spawn=None):
    """孩子出结论 → 结算进父节点：投递结果 + 门槛续跑/作废。

    inject(text)  把一条 user 消息并进父节点对话（写回账本）；
    spawn(specs)  门槛通过后把暂缓规格变成孩子（出生 + 注册），可选；
    trace_add     可选：门槛作废/通过的事件落盘。

    返回：父节点的孩子是否已全部回话（是 → 调度器该重新排队它）。
    """
    rec = child.record()
    inject(child_result(rec))
    delivered.add(child.id)
    gate = gate_child(parent, registry)
    if gate and gate.id == child.id and parent.deferred:
        if child.verdict == "满足":
            specs, parent.deferred = parent.deferred, []
            if spawn:
                spawn(specs)
            if trace_add:
                trace_add(parent.id, "gate_passed",
                          {"started": [s["name"] for s in specs]})
        else:
            names = [s.get("name", "") for s in parent.deferred]
            parent.deferred = []
            inject("门槛「%s」不成立：%s。暂缓分支作废（不启动）：%s"
                   % (child.name, child.conclusion, "、".join(names) or "(无)"))
            if trace_add:
                trace_add(parent.id, "gate_failed",
                          {"gate": child.name, "reason": child.conclusion,
                           "skipped": names})
    return all(cid in delivered for cid in parent.children)
