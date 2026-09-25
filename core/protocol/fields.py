"""形式字段：格子长什么样、协议逻辑在哪。

原则：形式化的是字段，次数不限，判断只看已发生的事实，完成与否由上层那条可执行标准判 ——
所以这里没有任何计数器。

节点没有"结束"概念：它是一个带对话（`msgs`）的节点，只在"有欠 LLM 一个回答"时运行
（`runtime/plan.py` 的 `actionable`：没出结论 + 最后一条不是 assistant）。

本文件只管格子的形状与序列化：合规校验在 `gate.py`，落盘 / 调度在 `runtime/`，
渲成消息在 `core/protocol/messages.py` —— class Node 是纯定义，没有任何方法。

词表与"可测物理量"的定义也住这里（`VERDICTS` / `EXTERNAL_CLASSES` / `ANCHOR_RE` + `ANCHOR_HINT`）：
它比谁都底层，校验、提示词、schema 都 import 得到同一份，不许各自再抄一遍。

树结构只读查询也住这里（`task_root` / `is_task_root`）：它只是 parent / kind 的纯函数，
runtime 的 `store._label`、工具层的验收锚点、终端的任务起止路由都要它，住最底层谁都 import 得到。
"""

import re
import uuid
from dataclasses import dataclass, field, fields

# 形式字段用英文键 + 中文取值；键是机器词汇（模型输出 / trace 共用），取值保持中文。
# 没有任何长度限制：提示词里的字数只是建议，代码不校。

# Node.kind 词表：dispatch = 还要继续拆；leaf = 派一个能亲手干活的叶子；
# intake = 会话入口根（不是子任务）。Node.kind 只有 dispatch / leaf 两种（KINDS）。
DISPATCH = "dispatch"
LEAF = "leaf"
INTAKE = "intake"
KINDS = (DISPATCH, LEAF)

# 提示词 / 工具类型（which）：dispatch 归入分配节点 alloc，leaf / intake 同名。
# 映射见 runtime/plan.which_of；哪些工具住哪个作用域由工具声明处的 `tags` 说（`scope:<层>`）。
ALLOC = "alloc"

# `外部需求` 的词表：bash 做不到的事由模型提议、代码按这张表过滤。
# "人确认后才算事实"是设计意图，控制面（见 HANDOVER §5①）还没实现 —— 现在过滤通过即算事实。
EXTERNAL_CLASSES = ("需要人到场", "需要真实账户", "需要真实资金", "需要现实设备")

# 判定词表：模型能给三种判定（gate 校验 / 渲染 / 证据审计共用）。
SATISFIED = "满足"
UNSATISFIED = "未满足"
BLOCKED = "阻塞"
VERDICTS = (SATISFIED, UNSATISFIED, BLOCKED)
# 代码设置的终态：门槛不成立 → 暂缓兄弟被判「未启动」，不是模型能给的判定。
NOT_STARTED = "未启动"

# 可测物理量（锚点）：日期、≥2 位数字、标识符；单个数字不算。
# 正则与给模型看的措辞必须同源：gate 拿它做继承/根校验，ChildSpec 与提示词拿它讲
# "验收标准必须带什么"（词表只有这一份，改这里就够）。
ANCHOR_RE = re.compile(
    r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{2,}|[A-Za-z_][A-Za-z0-9_.\-]+")
ANCHOR_HINT = "日期 / 两位以上数字 / 标识符如 hello.txt"


# 形式字段（上层下发、模型看到也写到）：节点出厂就带这几个键，任务消息的行首与
# `ChildSpec`（模型写给孩子的形状）必须是同一串键、同一顺序 —— 键清单只有这一份，
# 工具 schema 与它一致由测试守住。
FORM_FIELDS = ("name", "detail", "notes", "accept", "kind", "gate", "conc_range")


def norm(text):
    """形式字段的规范化：压掉换行和多余空白，不管长度。"""
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    return " ".join(s.split())


@dataclass
class Node:
    # ── 形式字段：上层下发，只读 ──
    name: str = ""
    detail: str = ""
    notes: str = ""
    accept: str = ""                  # 验收标准：必须可被观测
    kind: str = DISPATCH              # dispatch | leaf
    gate: bool = False                # 轻重缓急：它不成立，整个分支作废
    conc_range: list = field(default_factory=list)  # 上层要求的结论字数区间，如 [100,500]
    # ── 结构 ──
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent: str = None
    depth: int = 0
    # 出生时物化的上层意图链 [[name, detail], …]（父的 detail 只读，物化不会变旧）
    lineage: list = field(default_factory=list)
    # ── 结构（程序填）──
    children: list = field(default_factory=list)   # 已出生的孩子 id（含门槛）
    # ── 结局 ──
    verdict: str = ""                 # 满足 | 未满足 | 阻塞 | 未启动
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求


_NODE_FIELDS = tuple(f.name for f in fields(Node))


def node_to_dict(node):
    """节点的全字段快照，供检查点恢复；对话 msgs 与 node 并列，不在 Node 上。"""
    return {f.name: getattr(node, f.name) for f in fields(node)}


def node_from_dict(d):
    """dict → Node；只认当前字段。

    旧档案（"入口并入根之前"那批）的节点上带着 keywords / attempts / observations /
    status 等编排字段，一律不采信、直接丢 —— 这是有意的容忍：只有"当前格式的节点"
    一种解释，多出来的键不进内存。缺的字段按默认值补齐。
    """
    return Node(**{k: v for k, v in (d or {}).items() if k in _NODE_FIELDS})


def task_root(node, registry):
    """节点的任务根：入口（INTAKE）的孩子 / 没有入口时的最顶层；它的 accept 是验收锚点来源。"""
    cur = node
    while True:
        p = registry.get(cur.parent) if cur.parent else None
        if p is None or p.kind == INTAKE:
            return cur
        cur = p


def is_task_root(node, registry):
    """node 是不是一棵任务的根（入口节点的孩子 / 无入口档案的最顶层）；入口本身不算。"""
    return node.kind != INTAKE and task_root(node, registry) is node


