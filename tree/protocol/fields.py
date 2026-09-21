"""形式字段：格子长什么样、协议逻辑在哪。

这个会话里反复验出来的那条原则，落在这里：

    形式化的是字段；次数不限；判断只看已经发生的事实；
    完成与否由上层那条可执行标准判 —— 节点连打分的入口都没有。

所以这个文件里**没有任何计数器**。
所有"该不该停"的问题，都由"看得见的事实"回答：
分配节点看 `attempts`（自己试过什么、下层回了什么），叶子看 `observations`。
想让它更保守，就把事实说得更清楚，而不是加一个上限。

**这个文件只管格子的形状与协议逻辑**：字段怎么定义、怎么落盘、怎么回给上层。
"这个格子填得合不合规"是 `gate.py`；"落盘 / 调度"是 `runtime/`；
"怎么渲成消息给模型看"是 `tree/prompts/messages.py` —— **class Node 里没有任何
消息拼接**，全部提出去放到该放的地方。

`base_user` / `full_view` 渲哪几段、每段叫什么名字，`tree/prompts/prose.py` 的
input 节函数里都逐段点了名（`tests/test_protocol.py` 的 I 段**双向核对**）。
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
    「要么可见要么别截」那条纪律只作用于视图（messages.py 的 VIEW）；
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
    # ── 看得见的历史（程序填，模型只读）──
    attempts: list = field(default_factory=list)     # 分配节点：每次分配 + 下层结论
    observations: list = field(default_factory=list)  # 叶子：每次工具调用的真实返回
    # ── 结局 ──
    children: list = field(default_factory=list)
    verdict: str = ""                 # 满足 | 未满足 | 阻塞
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求
    status: str = "running"

    # ---------------------------------------------------------------- 结局
    # 消息拼接一律不在 Node —— 在 tree/prompts/messages.py（header / lineage /
    # attempts / observations / base_user / full_view）。Node 只装数据 + 协议逻辑。
    def close(self, verdict, conclusion, evidence, external=None):
        self.verdict = verdict
        self.conclusion = conclusion
        self.evidence = evidence or []
        self.external = external or []
        self.status = "done"

    # ------------------------------------------------------------ 序列化
    def to_dict(self):
        """整棵节点的快照（全字段）。给会话状态检查点用 —— 恢复时按原样
        重建 Node，attempts/observations 一字不差地回到模型眼前。"""
        return {"name": self.name, "detail": self.detail, "notes": self.notes,
                "accept": self.accept, "kind": self.kind, "gate": self.gate,
                "conc_range": self.conc_range,
                "id": self.id, "parent": self.parent, "depth": self.depth,
                "lineage": self.lineage, "attempts": self.attempts,
                "observations": self.observations, "children": self.children,
                "verdict": self.verdict, "conclusion": self.conclusion,
                "evidence": self.evidence, "external": self.external,
                "status": self.status}

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


def render_tree(root, registry, prefix="", is_last=True, lines=None, streams=None,
                compact=False):
    """整棵树的视图：每层的拆分 / 判定 / 结论，画成一串带树形标记的行。

    根是入口，registry 是出生时登记的全部节点（id → Node），孩子按 id 查。
    运行中的节点画成 ·，出过结论的按状态画成 ✓ / ✗。
    streams 是可选的活动节点吐字尾巴（node_id → {"thinking", "speaking"}）：
    运行中的节点如果正在吐字，在它下面补一行 ▸ —— 树在跑，看得见每个节点
    正在说什么。尾巴怎么截由终端定，这里只负责画。

    compact=True 是**实时视图**（终端跑任务时用）：每个节点一行 ——
    运行中的节点：`· [叶子] 名字  ▸ 思考: …`（正在吐的字并排在自己那行）；
    出过结论的：`✓ [叶子] 名字  [满足] 验收标准`。一行一个节点，整棵树按
    结构铺开，每个节点的输出都占一行看得见（屏幕放不下时终端负责裁）。
    树长什么样是树的变因，不是调度器的（调度器只编排谁先谁后）；
    它不是消息拼接（那是 messages.py 的事），是给人看的展示。
    """
    b = "└─ " if is_last else "├─ "
    mark = {"done": "✓", "failed": "✗", "running": "·"}.get(root.status, "?")
    if lines is None:
        lines = []
    tag = "%s%s" % ("[分配]" if root.kind == "dispatch" else "[叶子]",
                     " [门槛]" if root.gate else "")
    if compact:
        # 实时视图：一行一个节点。运行中的把正在吐的字并排带上 ——
        # 正在说什么就显示什么（吐过话就显示说，还在想就显示思考）；
        # 出过结论的把判定 + 验收标准并排带上（结论留到跑完的详细帧）。
        if root.status == "running":
            extra = ""
            if streams:
                s = streams.get(root.id)
                if s:
                    if s.get("speaking"):
                        extra = "  ▸ 说: %s" % s["speaking"]
                    elif s.get("thinking"):
                        extra = "  ▸ 思考: %s" % s["thinking"]
            lines.append("%s%s%s %s %s%s" % (prefix, b, mark, tag, root.name,
                                               extra))
        else:
            lines.append("%s%s%s %s %s  [%s] %s" % (
                prefix, b, mark, tag, root.name,
                root.verdict or "…", root.accept or ""))
    else:
        lines.append("%s%s%s %s %s" % (prefix, b, mark, tag, root.name))
        lines.append("%s%s  [%s] %s" % (prefix, "  " if is_last else "│ ",
                                        root.verdict or "…", root.accept))
        if streams and root.status == "running":
            s = streams.get(root.id)
            if s:
                if s.get("thinking"):
                    lines.append("%s%s  ▸ 思考: %s" % (
                        prefix, "  " if is_last else "│ ", s["thinking"]))
                if s.get("speaking"):
                    lines.append("%s%s  ▸ 说: %s" % (
                        prefix, "  " if is_last else "│ ", s["speaking"]))
        if root.conclusion:
            lines.append("%s%s  → %s" % (prefix, "  " if is_last else "│ ",
                                         root.conclusion))
    for i, cid in enumerate(root.children):
        kid = registry.get(cid)
        if kid:
            render_tree(kid, registry, prefix + ("   " if is_last else "│  "),
                        i == len(root.children) - 1, lines, streams, compact)
    return lines
