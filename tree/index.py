"""老树的索引。执行树就是成果树 —— 不为它另建一套存储。

节点形式化之后，形式字段本身就是索引：任务名/详情/注意事项/验收标准/结局。
不需要额外的"成果树"，也不需要给节点另起名字。

两条来自实战的约束：

  ① 检索返回的是**路径**，不是散落的节点。判据是沿树继承的，
     单独一个 d3 节点没有意义；能用的是「根判据 → d1判据 → 命中节点」。
  ② 必须按**结局**分别对待。昨晚 86% 的节点没完工，盲搜会把垃圾捞回来当先例。
     满足的子树可以照抄计划；阻塞的**不是死路**，是"上次卡在这条命令、这个条件上"——
     所以阻塞枝要把命令和观测一起带回去，让模型自己重判（DESIGN §2.7）。

检索参数由 LLM 自己定，可以同时给多组（不同说法/不同侧面），
程序一次扫遍所有老树 —— 本地是完整物化的树，不需要像网络调研那样一层层探。
"""

import json
import os
import time
from collections import defaultdict

from .caps import overlap, tokens
from .node import VIEW

# 形式字段的权重：任务名和验收标准信息量最大
W_NAME, W_ACCEPT, W_DETAIL, W_CONCL = 4, 3, 1, 1

# 阻塞枝回放几次动作。要的是"卡在哪条命令"，不是整段历史 ——
# 截了就说（render 里会写清"共 N 次动作，只列最近 M 次"）。
BLOCKED_ACTIONS_SHOWN = 3


class Node:
    __slots__ = ("tree", "id", "parent", "depth", "name", "detail", "notes",
                 "accept", "kind", "verdict", "conclusion", "external",
                 "evidence", "actions", "t_open", "t_end",
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
            # 英文键是新协议的；中文键是历史 trace 的。两种都必须认 ——
            # 否则昨晚那些树就变成死数据了。
            n.depth = p.get("depth", p.get("深度", 0))
            n.name = p.get("name") or p.get("任务名") or p.get("task") or ""
            n.detail = p.get("detail") or p.get("任务详情") or ""
            n.notes = p.get("notes") or p.get("注意事项") or ""
            n.accept = p.get("accept") or p.get("验收标准") or p.get("criteria") or ""
            kk = p.get("kind") or p.get("类型") or "dispatch"
            n.kind = "leaf" if kk == "evidence" else kk
            n.verdict, n.conclusion, n.external, n.evidence = "", "", [], []
            n.actions, n.t_open, n.t_end = [], r.get("t"), None
            n.workspace = p.get("workspace") or p.get("工作目录")
            if n.parent is None and n.workspace:
                workspace = n.workspace
            n.score = 0.0
            nodes[nid] = n
            order.append(nid)
        elif k == "concluded" and nid in nodes:
            nodes[nid].verdict = p.get("verdict") or p.get("判定", "")
            nodes[nid].conclusion = p.get("text") or p.get("内容", "")
            nodes[nid].external = p.get("external") or p.get("外部需求") or []
            nodes[nid].evidence = p.get("evidence") or p.get("证据") or []
            nodes[nid].t_end = r.get("t")
        elif k in ("action", "leaf_tool") and nid in nodes:
            # 一次动作 + 世界回了什么。两种键名（新格式 / 老格式）都要认 ——
            # 阻塞枝靠它回答"卡在哪条命令"，没有它，一条阻塞先例就只是
            # 一句没有探测方式的断言（DESIGN §2.7）。
            nodes[nid].actions.append((
                p.get("工具") or p.get("tool") or "",
                p.get("参数") or p.get("args") or {},
                p.get("观测") or p.get("obs") or ""))
        elif k == "done" and nid in nodes:          # 旧格式
            nodes[nid].verdict = nodes[nid].verdict or "满足"
            nodes[nid].conclusion = nodes[nid].conclusion or str(p.get("result", ""))
            nodes[nid].t_end = r.get("t")
        elif k in ("failed", "crashed", "budget_exhausted") and nid in nodes:
            nodes[nid].verdict = nodes[nid].verdict or "阻塞"
            # 老格式的 failed 里原因在 result；直接 str(p) 会把整行 dump 出来
            why = p.get("result") if isinstance(p, dict) else None
            nodes[nid].conclusion = nodes[nid].conclusion or str(why if why else p)
            nodes[nid].t_end = r.get("t")
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
    def search(self, queries, workspace=None):
        """queries 是多组参数（LLM 自己定的不同说法/侧面）。返回 (命中, 文本)。

        workspace：**当前**工作目录（就是进程 cwd）。先例自己的目录只有跟它
        相同时才写进提示词 —— 否则模型会把一个死目录抄进子任务里当"当前
        工作目录"，产出就落到别处去了（实测：hello.py 被写进了一棵老树里）。

        不设 top-k、不设总量封顶：实测词法匹配本身就很克制
        （真实查询命中 7–23 条、1.4K–4.4K 字）。命中多少就给你多少，
        不在背后替你丢掉几条。

        结局**只加分、不扣分、不过滤**：满足的先例可以照抄计划，
        阻塞的先例仍然全文给回去（它有自己的价值，而且"阻塞"不是"死路"）。
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
            # notes **不参与检索**（DESIGN §5.2：键要用可执行形状；
            # 注意事项是自由发挥的判断依据，放进去只会污染词法匹配）。
            det_t = tokens(n.detail)
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
                # 结局即质量信号：满足的先例可以照抄计划。
                # 阻塞的**不扣分、不过滤** —— 见 search 的注释。
                if n.verdict == "满足":
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
        return picked, self.render(picked, workspace)

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

    def _blocked_detail(self, a, pad):
        """阻塞枝要能复核：卡在哪条命令、当时世界回了什么。

        这是"阻塞 ≠ 死路"（DESIGN §2.7）在检索里的落点 —— 只给一句"做不了"，
        模型只能照抄；给了探测方式和观测原文，它才能自己重判一次。

        截断仍然可见：只列最近几次动作，并说明一共几次、全部在哪。
        """
        out = []
        if a.external:
            out.append("%s外部需求: %s" % (pad, "、".join(str(x) for x in a.external)))
        if a.evidence:
            out.append("%s证据: %s" % (pad, "；".join(str(x) for x in a.evidence)))
        if a.t_end:
            out.append("%s卡住时间: %s" % (pad, time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(a.t_end))))
        if a.actions:
            shown = a.actions[-BLOCKED_ACTIONS_SHOWN:]
            head = "%s卡在哪: 共 %d 次动作" % (pad, len(a.actions))
            if len(a.actions) > len(shown):
                head += "（只列最近 %d 次 —— 全部在 %s#%s）" % (
                    len(shown), os.path.basename(a.tree), a.id)
            out.append(head)
            for tool, args, obs in shown:
                row = "%s %s → %s" % (tool, json.dumps(args, ensure_ascii=False), obs)
                if len(row) > VIEW["obs_entry"]:
                    row = row[:VIEW["obs_entry"]] + \
                        "…[截断：这一次共 %d 字]" % len(row)
                out.append("%s  - %s" % (pad, row))
        return out

    def render(self, picked, workspace=None):
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
                if a.verdict == "阻塞":
                    lines.extend(self._blocked_detail(a, "  " * (j + 1) + "  "))
            # 只有先例的目录**就是当前工作目录**时才能写成"工作目录"。
            # 不同的话只能说清"数据在那边"，并明说不能当 cwd 用 ——
            # 否则模型会照抄，产出去到一棵早就不该再写的老树里。
            if workspace and n.workspace and n.workspace != workspace:
                lines.append("  先例的数据在: %s（只读，不是你的工作目录；"
                             "产出必须落在当前工作目录）   出处: %s#%s"
                             % (n.workspace, os.path.basename(n.tree), n.id))
            else:
                lines.append("  工作目录: %s   出处: %s#%s"
                             % (n.workspace or "?", os.path.basename(n.tree), n.id))
            s = "[先例 %d] %s" % (i, "\n".join(lines))
            out.append(s)
        return "\n\n".join(out)
