"""协议操作：模型动作在树上的语义 —— conclude / create_children / submit_root 的实现体。

`core/protocol/gate.py` 是协议的机械校验，这里是校验通过后的操作：判定结算、门槛作废、
孩子物化、下层结论回填。两者同一变因（协议规则），所以并置在 core 内层，不穿工具壳；
工具壳（`tools/defs.py`）只负责注册与参数适配，动作清单（`action_names`）由调用方传入
（协议层不认识工具层）。

变因：协议规则 —— 加字段 / 改校验 / 改结算语义，都只动这一层和 gate / fields / messages。
"""

from ..protocol import feedback
from ..protocol.fields import NOT_STARTED, SATISFIED, task_root
from ..protocol.gate import anchors, clean_conclusion, clean_spec, covers, validate_root
from ..protocol.messages import base_user, child_result, result_marks
from .plan import make_child


def task_root_anchors(node, registry):
    """任务根的 accept 里的可测物理量（任务根 = 入口节点的孩子 / 无父节点）。"""
    return anchors(task_root(node, registry).accept)


def deferred(store, parent):
    """父节点上还没启动的孩子：没结论、对话也为空。"""
    out = []
    for cid in parent.children:
        c = store.registry.get(cid)
        if c is not None and not c.verdict and not store.dialogue(cid).to_list():
            out.append(c)
    return out


def resolve_gate(store, nid):
    """门槛孩子出了结论 → 续跑 / 作废它的暂缓兄弟（幂等）。"""
    node = store.registry.get(nid)
    if node is None or not node.gate or not node.verdict or not node.parent:
        return
    parent = store.registry.get(node.parent)
    if parent is None:
        return
    siblings = [c for c in deferred(store, parent) if c.id != nid]
    if not siblings:
        return
    if node.verdict == SATISFIED:
        for c in siblings:
            store.append_user(c.id, base_user(c))
        store.record(parent.id, "gate_passed",
                     {"gate": node.name, "started": [c.name for c in siblings]})
    else:
        for c in siblings:
            store.set_verdict(c.id, NOT_STARTED, feedback.gate_failed(node.conclusion), [], [])
        store.record(parent.id, "gate_failed",
                     {"gate": node.name, "reason": node.conclusion,
                      "skipped": [c.name for c in siblings]})


def push_results(store, pid):
    """父节点的孩子都出结论了就把结果逐条拼回父对话（幂等）。"""
    parent = store.registry.get(pid)
    if parent is None or not parent.children:
        return
    kids = [store.registry.get(c) for c in parent.children]
    if any(k is None or not k.verdict for k in kids):
        return
    seen, _ = result_marks(store.dialogue(pid).to_list())
    for k in kids:
        if k.id not in seen:
            store.append_user(pid, child_result(k))


def create_children(store, nid, children):
    """一份已 model_dump 的子任务形状 → 物化孩子；返回打回理由或 None（成功）。"""
    node = store.registry[nid]
    parent_anchors = anchors(node.accept)
    root_anchors = task_root_anchors(node, store.registry)
    specs, reject = [], None
    for raw in children:
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        if not (covers(parent_anchors, s["accept"])
                and covers(root_anchors, s["accept"])):
            reject = feedback.criterion_drift(root_anchors or parent_anchors)
            store.record(nid, "criterion_drift",
                         {"child": s["name"], "accept": s["accept"],
                          "root_anchors": sorted(root_anchors)})
            break
        specs.append(s)
    if reject:
        return reject
    gates = [s for s in specs if s["gate"]]
    if len(gates) > 1:
        return feedback.too_many_gates()
    gate = gates[0] if gates else None
    kids = [make_child(node, s) for s in specs]
    store.put(kids, on_id=nid)
    active = [k for k in kids if gate is None or k.gate]
    active_ids = {k.id for k in active}
    for k in active:
        store.append_user(k.id, base_user(k))
    store.record(nid, "allocated",
                 {"gate": gate["name"] if gate else None,
                  "deferred": [k.name for k in kids if k.id not in active_ids]})
    return None


def conclude(store, nid, verdict, text, evidence, external, *, action_tools):
    """判定 满足|未满足|阻塞 落账；返回打回理由或 None。`action_tools` 由调用方传入。"""
    node = store.registry[nid]
    got, err = clean_conclusion(
        {"verdict": verdict, "text": text, "evidence": evidence or [],
         "external": external}, store, node, msgs=store.dialogue(nid).to_list(),
        action_tools=action_tools)
    if err:
        store.record(nid, "bad_conclusion", err)
        return err
    store.set_verdict(nid, got["verdict"], got["content"],
                      got["evidence"], got["external"])
    store.record(nid, "concluded",
                 {"verdict": got["verdict"], "text": got["content"],
                  "evidence": got["evidence"], "external": got["external"]})
    resolve_gate(store, nid)
    if node.parent:
        push_results(store, node.parent)
    return None


def submit_root(loop, store, nid, root):
    """入口交出的任务形状 → 当场物化成任务根的孩子；返回打回理由或 None。"""
    node = store.registry[nid]
    got, why = validate_root(root)
    if got is None:
        if loop.say:
            loop.say("（入口交的东西用不了：%s）" % why)
        return feedback.bad_root(why)
    if loop.say:
        loop.say("（接到任务：%s）" % got["name"])
    task = make_child(node, got)
    store.put([task], on_id=nid)
    store.append_user(task.id, base_user(task))
    store.record(nid, "submitted", {"task": task.id, "name": task.name})
    return None
