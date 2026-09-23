"""纯规则：这个节点现在该不该跑。调度与恢复共用这一份。

节点没有编排字段。它是一个带对话的 Node，`actionable` 只看两样已经发生的事实：
  · 它出结论了吗（verdict 非空 → 不再跑）；
  · 对话的最后一条是不是 assistant（是 → 自己在等回话；不是 → 轮到它说）。
"孩子都在跑"不需要单独判断 —— 分配节点的那条 assistant 消息之后要等所有孩子
的结论被 push 成 user 消息，最后一条才会变，所以"等孩子"就是"最后一条是 assistant"。

孩子怎么结算、门槛怎么续跑/作废，是 `Store.conclude` 的副作用，不是这里的事。
"""

from ..protocol.fields import Node


def which_of(node):
    """节点类型 → 提示词/工具类型（intake 保持；dispatch 归 alloc）。"""
    return node.kind if node.kind in ("leaf", "intake") else "alloc"


def actionable(store, nid):
    """该不该让这个节点现在跑：`msgs` 非空，且最后一条不是 assistant。

    `msgs` 为空（任务还没拼进来）也是未激活。"""
    msgs = store.dialogue(nid).to_list()
    return bool(msgs) and msgs[-1].get("role") != "assistant"


def make_child(parent, spec):
    """一份子任务规格 → 孩子节点（挂进 parent.children）。任务消息由调用方拼。

    任务根的 lineage 是空的（入口不是"上层意图"）；普通子节点继承父的意图链。
    父的 detail 出生后只读，所以出生时物化，不在渲染时反查。
    """
    lineage = [] if parent.kind == "intake" else \
        parent.lineage + [[parent.name, parent.detail]]
    kid = Node(name=spec["name"], detail=spec["detail"],
               notes=spec.get("notes") or "", accept=spec["accept"],
               kind=spec["kind"], gate=bool(spec.get("gate")),
               conc_range=spec.get("conc_range") or [],
               parent=parent.id, depth=parent.depth + 1, lineage=lineage)
    parent.children.append(kid.id)
    return kid
