"""形式字段：格子长什么样、怎么渲染给模型看。

这个会话里反复验出来的那条原则，落在这里：

    形式化的是字段；次数不限；判断只看已经发生的事实；
    完成与否由上层那条可执行标准判 —— 节点连打分的入口都没有。

所以这个文件里**没有任何计数器**。
所有"该不该停"的问题，都由"看得见的事实"回答：
分配节点看 `attempts`（自己试过什么、下层回了什么），叶子看 `observations`。
想让它更保守，就把事实说得更清楚，而不是加一个上限。

**这个文件只管格子的形状与视图**：
字段怎么定义、给模型看时怎么截、渲成什么形状（行首是键，和它写回去的同一套）。
"这个格子填得合不合规"是 `gate.py`；"落盘 / 调度"是 `runtime/`。

**注入面是公开的**：`render()` 会渲哪几段、每段叫什么名字，`prompts/*.md` 里
都逐段点了名（`tests/test_protocol.py` 的 I 段**双向核对**：文档说了没渲 =
承诺落空；渲了文档没说 = 偷偷塞东西）。形式字段那几行的行首就是字段名，
与模型自己要写的键是同一个词 —— "收到的东西与要交出去的东西同构"。
提示词文件是 system，被注入的那几行在**另一条 user 消息**里（`turn.ask`）——
占位符不做任何模板替换。
"""

import json
import uuid
from dataclasses import dataclass, field

# 形式字段的词表是**英文键 + 中文取值**：键是机器词汇（模型输出 / trace
# 共用同一套，中间没有翻译层可以漂移），取值和渲染标签保持中文。
#
# 这里**没有任何长度限制**。提示词里的字数只是建议 ——
# 判一个字段"超了"没用（模型不会突然写 10000 字），却要在每次写入时多一道检查。
#
# VIEW 是另一回事：它是"一次给模型看多少历史"，不是"限制模型写多少"。
# 单次工具输出可能有 1GB、观测历史会一直涨 —— 这两处不截就根本跑不起来。
# 所以它们是**必须截断**的地方，按 §2.5 的纪律：截了就要当面说。
VIEW = {"max_attempts_shown": 4, "max_obs_shown": 10,
        "max_obs_chars": 6000, "obs_entry": 1500}


# `外部需求` 这个形式字段的词表：bash 根本做不到的事。
# 代码抽不出来，只能由模型**提议** —— 所以它是词表，不是判据：
# 人确认之后才算事实（DESIGN §2.8），而且它只该用来"先探测再决定"（§2.7）。
EXTERNAL_CLASSES = ("需要人到场", "需要真实账户", "需要真实资金", "需要现实设备")


def norm(text):
    """形式字段的规范化：压掉换行和多余空白。**不管长度。**

    提示词里写的字数（名字 ≤20 之类）只是建议 —— 代码不校、不记、更不切。
    §2.5 那条纪律的原话是"要么可见要么别截"；既然决定了不截，就什么也不用做。
    """
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    return " ".join(s.split())


def as_json(v):
    """值按 JSON 形状渲染（数组就是数组，假就是 false），空写 (无)。

    收到的行和模型要写出去的 JSON 必须是同一套值形状 —— 否则它得先猜
    "逗号分隔的一串算不算数组"，而这正是漂移的开始。
    """
    if v is None or v == "" or v == []:
        return "(无)"
    return json.dumps(v, ensure_ascii=False)


def spec_line(c):
    """一次分配里的一个子任务 —— 按**它自己输出的那套键**列出来。

    历史里看到的是自己写过的形式，不是另一套中文标签：同一个词在"收到的"
    和"写回去的"两边指同一个东西，模型不用做翻译。
    """
    return " | ".join([
        "name: %s" % (c.get("name") or "(无)"),
        "kind: %s" % (c.get("kind") or "(无)"),
        "gate: %s" % as_json(bool(c.get("gate"))),
        "conc_range: %s" % as_json(c.get("conc_range")),
        "accept: %s" % (c.get("accept") or "(无)")])


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
    observations: list = field(default_factory=list)  # 叶子：每次 run_code 的真实返回
    # ── 结局 ──
    children: list = field(default_factory=list)
    verdict: str = ""                 # 满足 | 未满足 | 阻塞
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求
    status: str = "running"

    # ---------------------------------------------------------------- 视图
    def header(self):
        """形式字段 —— **行首就是字段名**，和模型自己写给孩子的键一模一样。

        这是"收到的东西与要交出去的东西同构"：同一个词既在收到的行首，
        也在它输出的 JSON 里，中间没有"中文标签 → 键"的翻译层可漂移。
        哪一行是谁给的（上层给的 / 程序查出来的）由 `prompts/*.md` 说，
        不放进行内 —— 行内只留键和值。
        """
        return "\n".join([
            "name: %s" % (self.name or "(无)"),
            "detail: %s" % (self.detail or "(无)"),
            "notes: %s" % (self.notes or "(无)"),
            "accept: %s" % (self.accept or "(无)"),
            "kind: %s" % (self.kind or "(无)"),
            "gate: %s" % as_json(bool(self.gate)),
            "conc_range: %s" % as_json(self.conc_range)])

    def render_lineage(self):
        """从根到自己的上层的意图链（程序物化的，不是上层下发的字段）。

        没有它，节点只知道"我要干什么"，不知道"这件事为什么值得做" ——
        拆到第三层就没人记得最初的验收标准是给谁用的了。**叶子也要看**。
        """
        if not self.lineage:
            return ""
        lines = ["上层意图链（从根到你上层，只读）:"]
        for i, (name, detail) in enumerate(self.lineage, start=1):
            lines.append("  %d. %s: %s" % (i, name, detail or "(无)"))
        return "\n\n" + "\n".join(lines)

    def render_attempts(self):
        if not self.attempts:
            return "本层已有尝试: (还没有)"
        # 注：只列最近几次尝试（这是**条数**上的截断，会明说）；
        # 但每条里的判据和结论全文给出 —— 字数是模型自己的决定，代码不管。
        lim = VIEW["max_attempts_shown"]
        shown = self.attempts[-lim:]
        head = "本层已有尝试: 共 %d 次" % len(self.attempts)
        if len(self.attempts) > lim:
            head += "（下面只列最近 %d 次）" % lim
        lines = [head]
        for i, a in enumerate(shown, start=len(self.attempts) - len(shown) + 1):
            lines.append("  第 %d 次分配:" % i)
            for c in a.get("children", []):
                lines.append("    - %s" % spec_line(c))
            if a.get("rejected"):
                lines.append("    → 这次分配被代码拒了: %s" % a["rejected"])
                continue
            for r in a.get("results", []):
                lines.append("    ← %s｜%s｜%s"
                             % (r.get("name", ""), r.get("outcome", ""),
                                r.get("text", "")))
                if r.get("evidence"):
                    lines.append("       证据: %s"
                                 % "; ".join(str(x) for x in r["evidence"]))
            if a.get("outcome"):
                lines.append("    → %s" % a["outcome"])
        return "\n".join(lines)

    def render_observations(self):
        """把观测历史讲给模型听。

        两条纪律（都是修一个真 bug 换来的）：
          ① **截断必须可见** —— 静默截断会让模型以为"那就是全部输出"，
             实测它因此把同一个文件反复读了 25 次。
          ② 额度从最新往回给 —— 越近越完整。旧观测被压短是安全的
             （结论已经在别处），新观测被压短是致命的（它正要用）。
        """
        if not self.observations:
            return "观测历史: (还没有)"
        shown = self.observations[-VIEW["max_obs_shown"]:]
        first = len(self.observations) - len(shown) + 1
        budget = VIEW["max_obs_chars"]
        rows = []
        for i in range(len(shown) - 1, -1, -1):
            o = shown[i]
            cap = max(200, min(VIEW["obs_entry"], budget))
            budget -= cap
            # 动作和观测一起算额度：否则一个很长的 write 参数会把观测挤没
            row = "%s → %s" % (str(o.get("action", "")), str(o.get("obs", "")))
            if len(row) > cap:
                row = row[:cap] + "…[截断：这一次共 %d 字]" % len(row)
            rows.append("  [%d] %s" % (first + i, row))
        rows.reverse()
        head = "观测历史: 共 %d 次" % len(self.observations)
        if first > 1:
            head += "（下面只列最近 %d 次）" % len(shown)
        return "\n".join([head] + rows)

    def render(self):
        if self.kind == "leaf":
            return ("%s%s\n\n手上的东西: bash / read / write（永远都在）\n%s"
                    % (self.header(), self.render_lineage(),
                       self.render_observations()))
        return "%s%s\n\n%s" % (self.header(), self.render_lineage(),
                                 self.render_attempts())

    def render_wire(self):
        """叶子对话的**基础** user 消息（选项 B 的线上形态）。

        不含观测历史 —— 观测走真 role=tool 消息（turn.step 每回合追加），
        所以这里只有出生后永不变的东西：形式字段 + 意图链 + 手上的东西。
        字节稳定 ⇒ 既是协议字段的家，也让 provider KV 缓存前缀命中。
        render() 仍用于 trace（给人看的完整视图）；这个是实际发送的。
        """
        return ("%s%s\n\n手上的东西: bash / read / write（永远都在）"
                % (self.header(), self.render_lineage()))

    # ---------------------------------------------------------------- 结局
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
    和 Node 的其它 render_* 一样住在数据旁 —— 树长什么样是树的变因，
    不是调度器的（调度器只编排谁先谁后）。
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
