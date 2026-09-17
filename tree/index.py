"""老树的索引。执行树就是成果树 —— 不为它另建一套存储。

节点形式化之后，形式字段本身就是索引：任务名/详情/注意事项/验收标准/结局。
不需要额外的"成果树"，也不需要给节点另起名字。

两条来自实战的约束：

  ① 检索返回的是**路径**，不是散落的节点。判据是沿树继承的，
     单独一个 d3 节点没有意义；能用的是「根判据 → d1判据 → 命中节点」。
  ② 必须按**结局**过滤/加权。昨晚 86% 的节点没完工，盲搜会把垃圾捞回来当先例。
     满足的子树可以照抄计划；阻塞的是死路 —— 死路同样是宝
     （一条"开户必须由人到场"值 11 小时）。

检索参数由 LLM 自己定，可以同时给多组（不同说法/不同侧面），
程序一次扫遍所有老树 —— 本地是完整物化的树，不需要像网络调研那样一层层探。
"""

import json
import os
from collections import defaultdict

from .caps import overlap, tokens

# 形式字段的权重：任务名和验收标准信息量最大
W_NAME, W_ACCEPT, W_DETAIL, W_CONCL = 4, 3, 1, 1


class Node:
    __slots__ = ("tree", "id", "parent", "depth", "name", "detail", "notes",
                 "accept", "kind", "verdict", "conclusion", "external",
                 "workspace", "score")


def _load_tree(path):
    """读一棵树。

    trace 是历史数据，格式变过：形式化之前用 task/criteria/done，
    之后用 任务名/验收标准/concluded。两种都要能读，
    否则昨晚那 2437 个节点的大树就变成死数据了。
    老格式没有 判定 字段，只能近似：done → 满足，failed → 阻塞。
    """
    nodes, order = {}, []
    workspace = None
    for line in open(path, errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        p, nid = r.get("payload") or {}, r.get("node")
        k = r.get("kind")
        if k == "open":
            n = Node()
            n.tree, n.id, n.parent = path, nid, p.get("parent")
            n.depth = p.get("深度", p.get("depth", 0))
            n.name = p.get("任务名") or p.get("task") or ""
            n.detail = p.get("任务详情") or ""
            n.notes = p.get("注意事项") or ""
            n.accept = p.get("验收标准") or p.get("criteria") or ""
            n.kind = p.get("类型") or ("leaf" if p.get("kind") == "evidence" else "dispatch")
            n.verdict, n.conclusion, n.external = "", "", []
            n.workspace = p.get("工作目录")
            if n.parent is None and n.workspace:
                workspace = n.workspace
            n.score = 0.0
            nodes[nid] = n
            order.append(nid)
        elif k == "concluded" and nid in nodes:
            nodes[nid].verdict = p.get("判定", "")
            nodes[nid].conclusion = p.get("内容", "")
            nodes[nid].external = p.get("外部需求") or []
        elif k == "done" and nid in nodes:          # 旧格式
            nodes[nid].verdict = nodes[nid].verdict or "满足"
            nodes[nid].conclusion = nodes[nid].conclusion or str(p.get("result", ""))
        elif k in ("failed", "crashed", "budget_exhausted") and nid in nodes:
            nodes[nid].verdict = nodes[nid].verdict or "阻塞"
            nodes[nid].conclusion = nodes[nid].conclusion or str(p)
    if workspace is None:
        workspace = os.path.dirname(os.path.abspath(path))
    for n in nodes.values():
        n.workspace = workspace
    return nodes, order


class TreeIndex:
    """所有老树的索引。构建成本很低（就是解析 jsonl），所以按需建。"""

    def __init__(self, traces=None, exclude=()):
        self.nodes = {}
        self.trees = []
        self.stats = defaultdict(int)
        excl = {os.path.abspath(t) for t in exclude if t}
        for t in traces or []:
            if not os.path.isfile(t) or os.path.abspath(t) in excl:
                continue
            try:
                nodes, _ = _load_tree(t)
            except Exception:
                continue
            if not nodes:
                continue
            self.trees.append(t)
            self.nodes.update(nodes)
            for n in nodes.values():
                self.stats["节点"] += 1
                if n.verdict:
                    self.stats[n.verdict] += 1

    # ---------------------------------------------------------------- 检索
    def search(self, queries, prefer_done=True):
        """queries 是多组参数（LLM 自己定的不同说法/侧面）。返回 (命中, 文本)。

        不设 top-k、不设总量封顶：实测词法匹配本身就很克制
        （真实查询命中 7–23 条、1.4K–4.4K 字）。命中多少就给你多少，
        不在背后替你丢掉几条。
        """
        if isinstance(queries, str):
            queries = [queries]
        qtok = [tokens(q) for q in queries if q and str(q).strip()]
        # 数字可以加分，但不能单独构成命中：查询里的 100 会命中
        # “closes=[100,110,99]” 这种无关节点（实测就是这样）。
        qword = [{t for t in q if not t.isdigit()} for q in qtok]
        if not qtok or not self.nodes:
            return [], ""

        for n in self.nodes.values():
            name_t, acc_t = tokens(n.name), tokens(n.accept)
            det_t = tokens(n.detail + " " + n.notes)
            con_t = tokens(n.conclusion)
            all_t = name_t | acc_t | det_t | con_t
            best = 0
            for i, q in enumerate(qtok):
                if not overlap(qword[i], all_t):
                    continue            # 至少得有一个词对上
                s = (W_NAME * overlap(q, name_t) + W_ACCEPT * overlap(q, acc_t)
                     + W_DETAIL * overlap(q, det_t) + W_CONCL * overlap(q, con_t))
                best = max(best, s)
            n.score = best            # 必须无条件重置：否则上一次查询的脏分会残留
            if n.score:
                # 结局即质量信号：满足的先例可以照抄计划，阻塞的是死路
                if prefer_done and n.verdict == "满足":
                    n.score += 1

        hits = [n for n in self.nodes.values() if n.score > 0]
        hits.sort(key=lambda n: (-n.score, -n.depth))
        # 同一脉只留分最高的那条（它自带完整判据链）
        picked, seen_chains = [], set()
        for n in hits:
            chain = self.chain_key(n)
            if chain in seen_chains:
                continue
            seen_chains.add(chain)
            picked.append(n)
        return picked, self.render(picked)

    def chain_key(self, n):
        """按"树的哪一脉"去重 —— 往上走到深度 1 的那个节点。
        同一脉里的多个命中只留分最高的，否则三条先例可能是同一件事。"""
        cur = n
        while True:
            par = self.nodes.get(cur.parent) if cur.parent else None
            if par is None or par.parent is None:
                break                     # 走到深度 1 就停
            cur = par
        return (n.tree, cur.id)

    def path_of(self, n):
        """从根到 n 的完整判据链。**不走捷径**：路径就是检索的单位，
        截断祖先链等于把先例讲了一半。"""
        chain, cur = [], n
        while cur is not None:
            chain.append(cur)
            cur = self.nodes.get(cur.parent) if cur.parent else None
        return list(reversed(chain))

    def render(self, picked):
        out = []
        for i, n in enumerate(picked, 1):
            lines = []
            for j, a in enumerate(self.path_of(n)):
                if j == 0:
                    tag = "根"
                else:
                    tag = "  " * j + "└"
                if a.verdict:
                    res = "%s：%s" % (a.verdict, a.conclusion or "")
                else:
                    res = "（没出结论）"
                # 判据（≤140）和结论（≤160）都给全 —— 这正是先例的价值所在。
                # 之前砍到 52/56 字，35% 的先例判据是残缺的。
                lines.append("%s %s｜%s｜%s" % (tag, a.name, a.accept, res))
            lines.append("  工作目录: %s   出处: %s#%s"
                         % (n.workspace or "?", os.path.basename(n.tree), n.id))
            s = "[先例 %d] %s" % (i, "\n".join(lines))
            out.append(s)
        return "\n\n".join(out)

    # ---------------------------------------------------------------- 工作目录
    def workspaces(self):
        return sorted({n.workspace for n in self.nodes.values() if n.workspace})
