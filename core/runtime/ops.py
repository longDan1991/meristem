"""协议操作：模型动作在树上的语义 —— create_children / communicate / submit_root 的实现体。

`core/protocol/gate.py` 是协议的机械校验（形状），这里是校验通过后的操作：孩子物化、
消息投递。判定权不在这一层 —— 做没做完由父节点（最终是人）从消息里判断，
代码只负责把消息送到对的对话。

变因：协议规则 —— 加字段 / 改消息格式 / 改寻址，都只动这一层和 gate / fields / messages。
"""

from ..protocol import feedback
from ..protocol.gate import clean_spec, parse_range
from ..protocol.messages import base_user, comm_content
from .plan import make_child


def create_children(store, nid, children):
    """一份已 model_dump 的子任务形状 → 物化孩子；返回打回理由或 None（成功）。

    所有孩子出生即带上任务消息（base_user），立即开始干 —— 想推迟谁，用
    communicate 对还没开始的孩子说"先别动，等我消息"。成功不写 tool 回话（结构类）。
    """
    node = store.registry[nid]
    specs, reject = [], None
    for raw in children:
        s, why = clean_spec(raw)
        if why:
            reject = why
            break
        specs.append(s)
    if reject:
        return reject
    kids = [make_child(node, s) for s in specs]
    store.put(kids, on_id=nid)
    for k in kids:
        store.append_user(k.id, base_user(k))
    store.record(nid, "allocated", {"children": [k.name for k in kids]})
    return None


def _target(store, node, to):
    """communicate 的目标节点：\"parent\" = 父节点，否则按 name 在已有孩子里找。"""
    if to == "parent":
        return node.parent
    for cid in node.children:
        c = store.registry.get(cid)
        if c is not None and c.name == to:
            return cid
    return None


def communicate(store, nid, to, text, conc_range=None):
    """沟通：把一条消息发给父节点或某个孩子（进对方的对话，对方醒来处理）。

    返回打回理由或 None（成功 = 结构类，不写 tool 回话 —— 调用方进入等待）。
    判定权在收消息的一方，这里只负责投递 + 带上来源。
    """
    node = store.registry[nid]
    tid = _target(store, node, to)
    if tid is None:
        return feedback.bad_comm_to(to)
    rng = parse_range(conc_range) if conc_range is not None else None
    if conc_range is not None and rng is None:
        return feedback.bad_conc_range()
    store.append_user(tid, comm_content(node.name, text, rng), sender=node.id)
    store.record(nid, "communicated", {"to": store.registry[tid].name, "text": text})
    return None


def submit_root(loop, store, nid, root):
    """入口交出的任务形状 → 当场物化成任务根的孩子；返回打回理由或 None。"""
    node = store.registry[nid]
    got, why = clean_spec(root)
    if why:
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
