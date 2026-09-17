"""节点 = 形式化字段 + 看见的历史 + 结局。

这个会话里反复验出来的那条原则，落在这里：

    形式化的是字段；次数不限；判断只看已经发生的事实；
    完成与否由上层那条可执行标准判 —— 节点连打分的入口都没有。

所以这个文件里**没有任何计数器**。
所有"该不该停"的问题，都由"看得见的事实"回答：
分配节点看 `attempts`（自己试过什么、下层回了什么），叶子看 `observations`。
想让它更保守，就把事实说得更清楚，而不是加一个上限。
"""

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field

# 形式化字段的边界。"形式化的是格子，不是格子里的字"——
# 格子要少而固定，格子里的字要给足空间。
LIMITS = {"name": 20, "detail": 240, "notes": 120, "accept": 140,
          "conclusion": 160,
          # 上面六个是**提示词明文承诺**的上限，代码只用它们判断"有没有超"
          # （如实记进 trace），**绝不拿它们切内容**。
          #
          # 下面三个是观测历史的**可见预算** —— 必须截断的地方，截了就当面说。
          # 不设它的话，一个叶子 50 次动作 × 每次 4000 字输出就会把上下文撞爆，
          # 那不是"撒谎"而是"跑不起来"。
          "max_attempts_shown": 4, "max_obs_shown": 10,
          "max_obs_chars": 6000, "obs_entry": 1500}


def norm(text, limit=None):
    """形式字段的规范化：压掉换行和多余空白。**不切长度。**

    长度上限由提示词明文承诺（任务名≤20／任务详情≤240／注意事项≤120／
    验收标准≤140／结论≤160）。提示词已经限过的东西，代码再偷偷砍一刀
    就是对模型撒谎 —— 它不知道自己被切了，看到的是断在半句的判据
    （实测：先例的判据被砍到 52 字，35% 的先例判据是残缺的）。

    超长只**如实记下来**（report 里的"字段超长"），不改内容。
    返回 (规范化的字, 是否超过承诺的上限)。
    """
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    s = " ".join(s.split())
    return s, (limit is not None and len(s) > limit)


@dataclass
class Node:
    # ── 形式字段：上层下发，只读 ──
    name: str = ""
    detail: str = ""
    notes: str = ""
    accept: str = ""                  # 验收标准：必须可被观测
    kind: str = "dispatch"            # dispatch | leaf
    gate: bool = False                # 轻重缓急：它不成立，整个分支作废
    # ── 结构 ──
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent: str = None
    depth: int = 0
    # ── 看得见的历史（程序填，模型只读）──
    attempts: list = field(default_factory=list)     # 分配节点：每次分配 + 下层结论
    observations: list = field(default_factory=list)  # 叶子：每次动作的真实返回
    precedents: list = field(default_factory=list)   # 从老树里检索出来的先例
    # ── 结局 ──
    children: list = field(default_factory=list)
    verdict: str = ""                 # 满足 | 未满足 | 阻塞
    conclusion: str = ""
    evidence: list = field(default_factory=list)
    external: list = field(default_factory=list)   # 阻塞时：哪一类外部需求
    status: str = "running"

    # ---------------------------------------------------------------- 视图
    def header(self):
        return ("任务名: %s\n任务详情: %s\n注意事项: %s\n验收标准: %s"
                % (self.name or "(无)", self.detail or "(无)",
                   self.notes or "(无)", self.accept or "(无)"))

    def render_attempts(self):
        if not self.attempts:
            return "本层已有尝试: (还没有)"
        # 注：只列最近几次尝试（这是**条数**上的截断，会明说）；
        # 但每条里的判据和结论**全文给出** —— 它们的长度上限已由提示词承诺。
        lim = LIMITS["max_attempts_shown"]
        shown = self.attempts[-lim:]
        head = "本层已有尝试: 共 %d 次" % len(self.attempts)
        if len(self.attempts) > lim:
            head += "（下面只列最近 %d 次）" % lim
        lines = [head]
        for i, a in enumerate(shown, start=len(self.attempts) - len(shown) + 1):
            lines.append("  第 %d 次分配:" % i)
            for c in a.get("分配", []):
                # 不截：子任务的验收标准上限已由提示词承诺为 140 字
                lines.append("    - %s%s｜验收标准: %s"
                             % (c.get("任务名", ""),
                                "｜[门槛]" if c.get("门槛") else "",
                                c.get("验收标准", ""))) 
            if a.get("被拒"):
                lines.append("    → 这次分配被代码拒了: %s" % a["被拒"])
                continue
            for r in a.get("下层结论", []):
                # 不截：结论上限已由提示词承诺为 160 字
                lines.append("    ← %s｜%s｜%s"
                             % (r.get("任务名", ""), r.get("判定", ""),
                                r.get("内容", "")))
                if r.get("证据"):
                    lines.append("       证据: %s"
                                 % "; ".join(str(x) for x in r["证据"]))
            if a.get("结局"):
                lines.append("    → %s" % a["结局"])
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
        shown = self.observations[-LIMITS["max_obs_shown"]:]
        first = len(self.observations) - len(shown) + 1
        budget = LIMITS["max_obs_chars"]
        rows = []
        for i in range(len(shown) - 1, -1, -1):
            o = shown[i]
            cap = max(200, min(LIMITS["obs_entry"], budget))
            budget -= cap
            # 动作和观测一起算额度：否则一个很长的 write 参数会把观测挤没
            row = "%s → %s" % (str(o.get("动作", "")), str(o.get("观测", "")))
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
        return ("\n\n先例（从以往真实的树里检索出来的，仅供参考，不是事实 —— "
                "判据和环境都可能已经变了）:\n" + "\n\n".join(self.precedents))

    def render(self):
        if self.kind == "leaf":
            return "%s\n\n可用工具: bash / read / write / need\n%s" % (
                self.header(), self.render_observations())
        return "%s%s\n\n%s" % (self.header(), self.render_precedents(),
                                self.render_attempts())

    # ---------------------------------------------------------------- 结局
    def close(self, verdict, conclusion, evidence, external=None):
        self.verdict = verdict
        self.conclusion = conclusion
        self.evidence = evidence or []
        self.external = external or []
        self.status = "done"

    def record(self):
        """回给上层的形式化记录。上层据此复核，不采信自报。"""
        r = {"任务名": self.name, "验收标准": self.accept, "结局": self.verdict,
             "内容": self.conclusion, "证据": self.evidence,
             "id": self.id, "类型": self.kind}
        if self.external:
            r["外部需求"] = self.external
        return r


class Trace:
    """append-only，按 node id 索引。这是"过程下沉"的落点，不是记忆机制。"""

    def __init__(self, path="trace.jsonl"):
        self.path = path
        self._lock = threading.Lock()
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)

    def add(self, node_id, kind, payload):
        rec = {"t": round(time.time(), 3), "node": node_id, "kind": kind,
               "payload": payload}
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        with self._lock:
            with open(self.path, "a") as f:
                f.write(line)
                f.flush()

    def of(self, node_id):
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path) as f:
            for line in f:
                r = json.loads(line)
                if r["node"] == node_id:
                    out.append(r)
        return out


class Budget:
    """纯计数器：只记用掉了多少，给报告看。不设上限。"""

    def __init__(self, max_nodes=None, max_tokens=None, max_hours=None):
        self.max_nodes = max_nodes
        self.max_tokens = max_tokens
        self.max_seconds = max_hours * 3600 if max_hours else None
        self.nodes = 0
        self.tokens = 0
        self.t0 = time.time()
        self._lock = threading.Lock()

    def take_nodes(self, n):
        with self._lock:
            if self.max_nodes is not None and self.nodes + n > self.max_nodes:
                return False
            self.nodes += n
            return True

    def add_tokens(self, n):
        with self._lock:
            self.tokens += n

    def exhausted(self):
        with self._lock:
            if self.max_nodes is not None and self.nodes >= self.max_nodes:
                return True
            if self.max_tokens is not None and self.tokens >= self.max_tokens:
                return True
            if self.max_seconds is not None and time.time() - self.t0 >= self.max_seconds:
                return True
            return False

    def why(self):
        with self._lock:
            return "节点 %d, token %d, %.1f 分钟" % (
                self.nodes, self.tokens, (time.time() - self.t0) / 60)

    def stats(self):
        with self._lock:
            return {"nodes": self.nodes, "tokens": self.tokens,
                    "minutes": round((time.time() - self.t0) / 60, 1)}
