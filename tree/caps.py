"""能力库：懒加载、按操作检索、注入封顶。

唯一的原则（这决定它成不成立）：
    库的大小必须与上下文大小解耦。
所以它**不进 prompt** —— 它是一个工具（need），只在叶子真要动手那一刻被问。
不需要的节点，成本是 0。

昨天踩过的坑，这里必须避开：**锚点会被稀释**
（根 {2026-12-31} → d1 {close,date,high,low} → 之后谁提 date 都算）。
所以检索 key 从**真实执行过的命令**里抽，不从领域词里抽 ——
按"怎么读邮件"检索，而不是按"量化"检索。后者会让能力收缩到一个方向。
"""

import hashlib
import json
import os
import re
import threading
import time

# 数字只收两位以上：单个数字（如 "1"）几乎出现在所有文本里，
# 收进来会命中一切（实测：查询"算 1 到 100 的和"匹配到"净值为 1"）。
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]{1,}|\d{2,}")
# 中文虚字：由它们拼成的 bigram（"到的" "的和" "是一"）不携带信息，
# 留着会让任何两句话都能对上（实测：查询"算 1 到 100 的和"命中
# "名称到的映射表"）。这跟 IDF 是同一个道理。
FUNC_CHARS = set("的了在是和与到就很也不之其中为以或但而对从把被使且等则")


def _bigrams(text):
    cjk = re.sub(r"[^\u4e00-\u9fff]", "", text or "")
    out = set()
    for i in range(len(cjk) - 1):
        b = cjk[i:i + 2]
        if not set(b) <= FUNC_CHARS:
            out.add(b)
    return out


def tokens(text):
    """拉丁词 + 数字 + 中文 2-gram。不需要分词器，也不引依赖。

    数字必须进 token：查询说"算 1 到 100 的和"，而 cap 里的 100 对不上，
    就会靠 bridge 凑单数 —— 实测就是这样退回来的。但单个数字要排掉。
    """
    t = {w.lower() for w in TOKEN_RE.findall(text or "")}
    return t | _bigrams(text)


def overlap(q, hay):
    """两个 token 集的重合度。索引和能力库共用同一套匹配。

    中文 2-gram 直接重合 + 拉丁词/数字允许前缀匹配（http↔https, broker↔mock_broker）。
    """
    n = len(q & hay)
    ql = {t for t in q if t.isascii() and len(t) >= 4}
    hl = {t for t in hay if t.isascii() and len(t) >= 4}
    for a in ql:
        if any(b != a and (b.startswith(a) or a.startswith(b)) for b in hl):
            n += 1
    return n


def cap_id(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:10]


class Caps:
    """append-only 的 jsonl，按 id 取最新一条。崩溃安全，可直接 diff 看历史。"""

    def __init__(self, path="caps.jsonl"):
        self.path = path
        # 能力自带脚本：内联 heredoc 的正文落在这里，配方指向它。
        # 于是配方可复现，而且跨项目活下来。
        self.scripts_dir = os.path.join(
            os.path.dirname(os.path.abspath(path)), "caps_scripts")
        self._lock = threading.Lock()
        self.entries = {}
        self._load()

    # ---------------------------------------------------------------- 存储
    def _load(self):
        if not os.path.exists(self.path):
            return
        for line in open(self.path):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("id"):
                self.entries[e["id"]] = e

    def _append(self, e):
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        with self._lock:
            with open(self.path, "a") as f:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def record(self, entry):
        e = dict(entry)
        body = e.pop("body", None)
        how = dict(e.get("how") or {})
        eid = e.get("id")
        if body and (body.get("text") or "").strip():
            # 正文不同 = 不同的能力，所以把正文哈希并进 id
            h = hashlib.sha1(body["text"].encode()).hexdigest()[:8]
            eid = eid or cap_id(e.get("does", ""), how.get("cmd", ""), h)
            path = os.path.join(self.scripts_dir, eid + (body.get("ext") or ".py"))
            if not os.path.exists(path):
                os.makedirs(self.scripts_dir, exist_ok=True)
                with open(path, "w") as f:
                    f.write(body["text"])
            how["cmd"] = (how.get("cmd") or "").replace("__SCRIPT__", path)
            how["script_file"] = path
            if body.get("target"):
                how["wrote"] = body["target"]
        eid = eid or cap_id(e.get("does", ""), how.get("cmd", ""))
        old = self.entries.get(eid) or {}
        e["id"] = eid
        e["how"] = how
        e["uses"] = old.get("uses", 0)
        e["fails"] = old.get("fails", 0)
        e["ts"] = round(time.time(), 1)
        self.entries[eid] = e
        self._append(e)
        return eid

    def note_outcome(self, eid, ok):
        e = self.entries.get(eid)
        if not e:
            return
        e = dict(e)
        if ok:
            e["uses"] += 1
        else:
            e["fails"] += 1          # 失败不该算"用过"
        # 自清洁：复用比成功还失败，就退休。库不会自己烂掉。
        if e["uses"] + e["fails"] >= 2 and e["fails"] > e["uses"]:
            e["retired"] = True
        self._append(e)
        self.entries[eid] = e

    # ---------------------------------------------------------------- 检索
    def search(self, query):
        q = tokens(query)
        if len(q) < 1:
            return [], ""
        scored = []
        for e in self.entries.values():
            if e.get("retired"):
                continue
            # does+keys 是能力本身（权重 2）；seen_in 是中文桥（权重 1）。
            # 叶子用中文提问而键是英文，需要这个桥；但不能让桥淹没能力本身，
            # 否则"把 1 到 100 的和写进文件"会命中 `pip install pandas`。
            # keys 是有意提取的（脚本名/包名/模块名），命令正文是副产品。
            # 不分开计分的话，一条很长的 grep 命令会靠两个字赢过真正的做法。
            # seen_in + obs 是中文桥：obs 是那次执行的中文结论，
            # 正好是查询会描述的东西（"已完成，data/000001.SZ.csv 已生成"）。
            k_tok = tokens(" ".join(e.get("keys") or []))
            d_tok = tokens(e.get("does", ""))
            b_tok = tokens(e.get("seen_in", "")
                           + " " + (e.get("evidence") or {}).get("obs", ""))
            b_tok -= (k_tok | d_tok)
            k_hit, d_hit, b_hit = (overlap(q, k_tok), overlap(q, d_tok),
                                   overlap(q, b_tok))
            # 中文桥不能单独召回：否则"把 1 到 100 的和写进文件"会命中 `pip install pandas`。
            if not (k_hit or d_hit or b_hit >= 2):
                continue
            scored.append((3 * k_hit + d_hit + b_hit, e.get("uses", 0), e))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        # 不设 top-k、不设总量封顶：命中多少给你多少。
        # 词法匹配本身就很克制，而且**在背后替你丢掉几条**是最坏的选择 ——
        # 模型根本不知道自己少看了东西。
        return self.render([e for _, _, e in scored])

    def render(self, picked):
        """一条 cap 里最重要的是：怎么用（用法）+ 需要什么前提 + 会影响什么。
        "前提" 尤其重要——复用失败最常见的原因是前提不成立，
        而不是配方错。没这一项，一条好配方会被记成“烂了”。
        """
        out, kept = [], []
        for e in picked:
            how, c = e.get("how") or {}, e.get("契约") or {}
            tag = " [本项目]" if e.get("scope") == "project" else ""
            lines = ["- %s%s" % (c.get("name") or e.get("does", ""), tag),
                     "  用法: %s" % (c.get("func") or how.get("cmd", ""))]
            if c.get("return"):
                lines.append("  产出: %s" % c["return"])
            pre = e.get("前置条件") or {}
            bits = []
            if pre.get("需要网络"):
                bits.append("需要网络")
            if pre.get("需要包已安装"):
                bits.append("需要包 " + ",".join(str(x) for x in pre["需要包已安装"]))
            if pre.get("依赖当前目录"):
                bits.append("必须在原目录跑")
            if bits:
                lines.append("  前提: " + "; ".join(bits))
            eff = e.get("effects") or {}
            fs = eff.get("fs") or {}
            nfs = len(fs.get("create", [])) + len(fs.get("modify", []))
            touched = []
            if nfs:
                touched.append("写 %d 个文件" % nfs)
            if eff.get("proc"):
                touched.append("起常驻进程")
            if eff.get("net"):
                touched.append("联网 " + ",".join(str(x) for x in eff["net"]))
            if eff.get("pkg"):
                touched.append("装包 " + ",".join(str(x) for x in eff["pkg"]))
            if touched:
                lines.append("  会影响: " + "; ".join(touched))
            out.append("\n".join(lines))
            kept.append(e)
        return kept, "\n".join(out)

    def stats(self):
        live = [e for e in self.entries.values() if not e.get("retired")]
        return {"总数": len(live),
                "已退休": len(self.entries) - len(live),
                "自带脚本": sum(1 for e in live if (e.get("how") or {}).get("script_file")),
                "有契约": sum(1 for e in live if e.get("契约")),
                "有复用记录": sum(1 for e in live if e["uses"] + e["fails"] > 0)}