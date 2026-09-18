"""形式字段：格子长什么样、怎么渲染给模型看。

这个会话里反复验出来的那条原则，落在这里：

    形式化的是字段；次数不限；判断只看已经发生的事实；
    完成与否由上层那条可执行标准判 —— 节点连打分的入口都没有。

所以这个文件里**没有任何计数器**。
所有"该不该停"的问题，都由"看得见的事实"回答：
分配节点看 `attempts`（自己试过什么、下层回了什么），叶子看 `observations`。
想让它更保守，就把事实说得更清楚，而不是加一个上限。

**这个文件只管格子的形状与视图**：
字段怎么定义、给模型看时怎么截、渲染成什么中文标签。
"这个格子填得合不合规"是 `gate.py`；"落盘 / 调度"是 `runtime/`。
"""

import uuid
from dataclasses import dataclass, field

# 形式字段的词表是**英文键 + 中文取值**：键是机器词汇（模型输出 / trace / 索引
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


def range_txt(rng):
    """结论字数区间的中文展示，如 [100, 500]。

    区间在进 Node 之前已经过 `gate.parse_range`；这里只负责展示，
    所以形状不对是**调用方的 bug**，当场炸出来而不是编一个字符串糊过去。
    """
    return "[%d, %d]" % (int(rng[0]), int(rng[1]))


@dataclass
class Node:
    # ── 形式字段：上层下发，只读 ──
    name: str = ""
    detail: str = ""
    notes: str = ""
    accept: str = ""                  # 验收标准：必须可被观测
    kind: str = "dispatch"            # dispatch | leaf
    gate: bool = False                # 轻重缓急：它不成立，整个分支作废
    keywords: list = field(default_factory=list)   # 上层给的检索键 → 出生时自动查老树
    conc_range: list = field(default_factory=list)  # 上层要求的结论字数区间，如 [100,500]
    # ── 结构 ──
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent: str = None
    depth: int = 0
    # ── 看得见的历史（程序填，模型只读）──
    attempts: list = field(default_factory=list)     # 分配节点：每次分配 + 下层结论
    observations: list = field(default_factory=list)  # 叶子：每次动作的真实返回
    precedents: list = field(default_factory=list)   # 出生时按检索键查到的老树先例
    caps: list = field(default_factory=list)         # 出生时按同一组键查到的现成做法
    # ── 结局 ──
    children: list = field(default_factory=list)
    verdict: str = ""                 # 满足 | 未满足 | 阻塞
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求
    status: str = "running"

    # ---------------------------------------------------------------- 视图
    def header(self):
        out = ["任务名: %s" % (self.name or "(无)"),
               "任务详情: %s" % (self.detail or "(无)"),
               "注意事项: %s" % (self.notes or "(无)"),
               "验收标准: %s" % (self.accept or "(无)")]
        if self.conc_range:
            out.append("结论字数要求（上层给的）: %s" % range_txt(self.conc_range))
        if self.keywords:
            out.append("检索键（上层给的，已据此查过老树）: %s"
                       % ", ".join(str(k) for k in self.keywords))
        return "\n".join(out)

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
                bits = [c.get("name", "")]
                if c.get("gate"):
                    bits.append("[门槛]")
                if c.get("conc_range"):
                    bits.append("结论 %s" % range_txt(c["conc_range"]))
                if c.get("keywords"):
                    bits.append("检索键 %s" % ",".join(str(k) for k in c["keywords"]))
                lines.append("    - %s｜验收标准: %s"
                             % ("｜".join(bits), c.get("accept", "")))
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

    def render_precedents(self):
        if not self.precedents:
            return ""
        return ("\n\n先例（上层给的检索键自动查出来的老树，仅供参考，不是事实 —— "
                "判据和环境都可能已经变了）:\n" + "\n\n".join(self.precedents))

    def render_caps(self):
        """出生时按检索键查到的现成做法。

        **没有 need 这个动作**：模型不会主动去找工具（它觉得自己都会），
        所以由程序直接塞给它 —— 和先例同理（DESIGN §4.3、§5.4）。
        """
        if not self.caps:
            return ""
        return ("\n\n现成做法（以往真实成功过的，仅供参考 —— 仍要自己跑一遍验证）:\n"
                + "\n".join(self.caps))

    def render(self):
        if self.kind == "leaf":
            return "%s%s\n\n可用工具: bash / read / write\n%s" % (
                self.header(), self.render_caps(), self.render_observations())
        return "%s%s%s\n\n%s" % (self.header(), self.render_precedents(),
                                   self.render_caps(), self.render_attempts())

    # ---------------------------------------------------------------- 结局
    def close(self, verdict, conclusion, evidence, external=None):
        self.verdict = verdict
        self.conclusion = conclusion
        self.evidence = evidence or []
        self.external = external or []
        self.status = "done"

    def record(self):
        """回给上层的形式化记录。上层据此复核，不采信自报。"""
        r = {"name": self.name, "accept": self.accept, "outcome": self.verdict,
             "text": self.conclusion, "evidence": self.evidence,
             "id": self.id, "kind": self.kind}
        if self.external:
            r["external"] = self.external
        return r
