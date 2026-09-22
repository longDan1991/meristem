"""形式字段：格子长什么样、协议逻辑在哪。

这个会话里反复验出来的那条原则，落在这里：

    形式化的是字段；次数不限；判断只看已经发生的事实；
    完成与否由上层那条可执行标准判 —— 节点连打分的入口都没有。

所以这个文件里**没有任何计数器**。
所有"该不该停"的问题，都由"看得见的事实"回答。
想让它更保守，就把事实说得更清楚，而不是加一个上限。

节点没有"结束"这个概念：它是一个 Loop，`msgs`（平铺对话）就是它的全部历史 ——
观测 / 尝试 / 下层结论都以对话消息累积。它只在"有欠 LLM 一个回答"时才运行
（`runtime/reconcile.py` 的 `actionable`，调度与恢复共用同一个谓词）。
`deferred` 是门槛的暂缓计划（还没出生的子任务规格）—— 唯一不是"已完成事实"
的节点数据，因为那些孩子还没出生，无处可推。

**这个文件只管格子的形状与协议逻辑**：字段怎么定义、怎么落盘、怎么回给上层。
"这个格子填得合不合规"是 `gate.py`；"落盘 / 调度"是 `runtime/`；
"怎么渲成消息给模型看"是 `tree/prompts/messages.py` —— **class Node 里没有任何
消息拼接**，全部提出去放到该放的地方。

`base_user` 渲哪几段、每段叫什么名字，`tree/prompts/prose.py` 的
input 节函数里都逐段点了名（`tests/test_protocol.py` 的 I 段**双向核对**；
prose 里的「观测历史 / 本层已有尝试 / 手上的东西」是线上对话机制与工具清单的
说明 —— 分别由 tool 消息、分配记录、工具列表承担 —— 不渲染成视图）。
形式字段那几行的行首就是字段名，与模型自己要写的键是同一个词 ——
"收到的东西与要交出去的东西同构"。
"""

import uuid
from dataclasses import dataclass, field

# 形式字段的词表是**英文键 + 中文取值**：键是机器词汇（模型输出 / trace
# 共用同一套，中间没有翻译层可以漂移），取值和渲染标签保持中文。
# 这里**没有任何长度限制**。提示词里的字数只是建议 ——
# 判一个字段"超了"没用（模型不会突然写 10000 字），却要在每次写入时多一道检查。

# `外部需求` 这个形式字段的词表：bash 根本做不到的事。
# 代码抽不出来，只能由模型**提议** —— 所以它是词表，不是判据：
# 人确认之后才算事实，而且它只该用来"先探测再决定"。
EXTERNAL_CLASSES = ("需要人到场", "需要真实账户", "需要真实资金", "需要现实设备")


def norm(text):
    """形式字段的规范化：压掉换行和多余空白。**不管长度。**

    提示词里写的字数（名字 ≤20 之类）只是建议 —— 代码不校、不记、更不切。
    「要么可见要么别截」那条纪律只作用于线上视图（`base_user`）；
    这里既然决定了不截，就什么也不用做。
    """
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    return " ".join(s.split())


@dataclass
class Node:
    # ── 形式字段：上层下发，只读 ──
    name: str = ""
    detail: str = ""
    notes: str = ""
    accept: str = ""                  # 验收标准：必须可被观测
    kind: str = "dispatch"            # dispatch | leaf
    gate: bool = False                # 轻重缓急：它不成立，整个分支作废
    conc_range: list = field(default_factory=list)  # 上层要求的结论字数区间，如 [100,500]
    # ── 结构 ──
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent: str = None
    depth: int = 0
    # 出生时物化的**上层意图链**：[[name, detail], …]，从根到自己的上层。
    # 由 `scheduler._spawn` 从父节点上拼出来（O(1)），不在 render 时反查 registry：
    # 形式字段只读 ⇒ 父的 detail 出生后不会再变 ⇒ 物化不可能变旧（§11）。
    lineage: list = field(default_factory=list)
    # ── 结构（程序填）──
    children: list = field(default_factory=list)   # 已出生的孩子 id（含门槛）
    deferred: list = field(default_factory=list)   # 门槛的暂缓计划：还没出生的子任务规格
    # ── 结局 ──
    verdict: str = ""                 # 满足 | 未满足 | 阻塞
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求

    # ---------------------------------------------------------------- 结局
    # 消息拼接一律不在 Node —— 在 tree/prompts/messages.py（header / lineage /
    # base_user）。Node 只装数据 + 协议逻辑。
    # 没有 status：出结论（verdict 非空）就是终态事实，"done" 由展示从 verdict 推导。
    def close(self, verdict, conclusion, evidence, external=None):
        self.verdict = verdict
        self.conclusion = conclusion
        self.evidence = evidence or []
        self.external = external or []

    # ------------------------------------------------------------ 序列化
    def to_dict(self):
        """整棵节点的快照（全字段）。给会话状态检查点用 —— 恢复时按原样
        重建 Node；对话（msgs）在检查点里和 node 并列，不在 Node 上。"""
        return {"name": self.name, "detail": self.detail, "notes": self.notes,
                "accept": self.accept, "kind": self.kind, "gate": self.gate,
                "conc_range": self.conc_range,
                "id": self.id, "parent": self.parent, "depth": self.depth,
                "lineage": self.lineage, "children": self.children,
                "deferred": self.deferred,
                "verdict": self.verdict, "conclusion": self.conclusion,
                "evidence": self.evidence, "external": self.external}

    @classmethod
    def from_dict(cls, d):
        n = cls()
        for k, v in (d or {}).items():
            if hasattr(n, k):
                setattr(n, k, v)
        return n

    def record(self):
        """回给上层的形式化记录。上层据此复核，不采信自报。"""
        r = {"name": self.name, "accept": self.accept, "outcome": self.verdict,
             "text": self.conclusion, "evidence": self.evidence,
             "id": self.id, "kind": self.kind}
        if self.external:
            r["external"] = self.external
        return r


