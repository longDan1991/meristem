"""纯规则：这个节点现在该不该跑；调度与恢复共用这一份。

节点没有编排字段，`actionable` 只看一件已发生的事实：最后一条是不是 assistant
（"发出了消息，等对方回应"就是"最后一条是 assistant"；结构类工具成功不写 tool
回话，所以调完 communicate 的节点自然进入等待，对方的消息会把它唤醒）。
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
               notes=spec.get("notes") or "",
               kind=spec["kind"],
               conc_range=spec.get("conc_range") or [],
               parent=parent.id, depth=parent.depth + 1, lineage=lineage)
    parent.children.append(kid.id)
    return kid
