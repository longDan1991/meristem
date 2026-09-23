"""纯规则：这个节点现在该不该跑；调度与恢复共用这一份。

节点没有编排字段，`actionable` 只看两样已发生的事实：有没有出结论，最后一条是不是 assistant
（"等孩子"就是"最后一条是 assistant"）。孩子怎么结算、门槛怎么续跑/作废是 conclude 的副作用。
"""

from ..protocol.fields import ALLOC, INTAKE, LEAF, Node


def which_of(node):
    """节点类型 → 提示词/工具类型（intake 保持；dispatch 归 alloc）。"""
    return node.kind if node.kind in (LEAF, INTAKE) else ALLOC


def actionable(store, nid):
    """该不该让这个节点现在跑：`msgs` 非空，且最后一条不是 assistant。

    `msgs` 为空（任务还没拼进来）也是未激活。"""
    msgs = store.dialogue(nid).to_list()
    return bool(msgs) and msgs[-1].get("role") != "assistant"


def make_child(parent, spec):
    """一份子任务规格 → 孩子节点（挂进 parent.children），任务消息由调用方拼。

    任务根 lineage 为空（入口不是上层意图），普通子节点在出生时物化父的意图链（父 detail 只读）。
    """
    lineage = [] if parent.kind == INTAKE else \
        parent.lineage + [[parent.name, parent.detail]]
    kid = Node(name=spec["name"], detail=spec["detail"],
               notes=spec.get("notes") or "", accept=spec["accept"],
               kind=spec["kind"], gate=bool(spec.get("gate")),
               conc_range=spec.get("conc_range") or [],
               parent=parent.id, depth=parent.depth + 1, lineage=lineage)
    parent.children.append(kid.id)
    return kid
