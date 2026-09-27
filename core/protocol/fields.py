"""形式字段：格子长什么样、协议逻辑在哪。

任务信息分层次沉淀在树节点上：节点出生带形式字段（上层下发），之后一切靠
`communicate` 消息来往——父向子追问/要求重做/再下任务，子向父回报进展与结论。
判定权不在代码、不在子节点，在父节点（最终是人）。代码只做形状校验，不判内容。

形式字段用英文键 + 中文取值；键是机器词汇（模型输出 / trace 共用），取值保持中文。
没有任何长度限制：提示词里的字数只是建议，代码不校。
"""

import uuid
from dataclasses import dataclass, field, fields

# Node.kind 词表：dispatch = 还要继续拆；leaf = 派一个能亲手干活的叶子；
# intake = 会话入口根（不是子任务）。Node.kind 只有 dispatch / leaf 两种（KINDS）。
DISPATCH = "dispatch"
LEAF = "leaf"
INTAKE = "intake"
KINDS = (DISPATCH, LEAF)

# 提示词 / 工具类型（which）：dispatch 归入分配节点 alloc，leaf / intake 同名。
ALLOC = "alloc"


def norm(text):
    """形式字段的规范化：压掉换行和多余空白，不管长度。"""
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    return " ".join(s.split())


# 形式字段（上层下发、模型看到也写到）：节点出厂就带这几个键，任务消息的行首与
# `ChildSpec`（模型写给孩子的形状）必须是同一串键、同一顺序 —— 键清单只有这一份，
# 工具 schema 与它一致由测试守住。
FORM_FIELDS = ("name", "detail", "notes", "kind", "conc_range")


@dataclass
class Node:
    # ── 形式字段：上层下发，只读 ──
    name: str = ""
    detail: str = ""
    notes: str = ""
    kind: str = DISPATCH              # dispatch | leaf
    conc_range: list = field(default_factory=list)  # 上层要求的回报字数区间，如 [100,500]
    # ── 结构 ──
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent: str | None = None
    depth: int = 0
    # 出生时物化的上层意图链 [[name, detail], …]（父的 detail 只读，物化不会变旧）
    lineage: list = field(default_factory=list)
    # ── 结构（程序填）──
    children: list = field(default_factory=list)   # 已出生的孩子 id


_NODE_FIELDS = tuple(f.name for f in fields(Node))


def node_to_dict(node):
    """节点的全字段快照，供检查点恢复；对话 msgs 与 node 并列，不在 Node 上。"""
    return {f.name: getattr(node, f.name) for f in fields(node)}


def node_from_dict(d):
    """dict → Node；只认当前字段。

    旧档案（还带 accept / gate / verdict 那批）的节点上这些键一律不采信、直接丢 ——
    这是有意的容忍：只有"当前格式的节点"一种解释，多出来的键不进内存。
    缺的字段按默认值补齐。
    """
    return Node(**{k: v for k, v in (d or {}).items() if k in _NODE_FIELDS})


def task_root(node, registry):
    """节点的任务根：入口（INTAKE）的孩子 / 没有入口时的最顶层。"""
    cur = node
    while True:
        p = registry.get(cur.parent) if cur.parent else None
        if p is None or p.kind == INTAKE:
            return cur
        cur = p


def is_task_root(node, registry):
    """node 是不是一棵任务的根（入口节点的孩子 / 无入口档案的最顶层）；入口本身不算。"""
    return node.kind != INTAKE and task_root(node, registry) is node
