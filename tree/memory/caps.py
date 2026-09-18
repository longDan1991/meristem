"""能力库：append-only 的 jsonl，按操作检索，跨 session 复用。

唯一的原则（这决定它成不成立）：
    库的大小必须与上下文大小解耦。
所以它**不进系统提示词** —— 它在节点出生时按检索键被问一次（`runner` 里
`register` 干这件事）。不需要的节点，成本是 0。

昨天踩过的坑，这里必须避开：**锚点会被稀释**
（根 {2026-12-31} → d1 {close,date,high,low} → 之后谁提 date 都算）。
所以检索 key 从**真实执行过的命令**里抽，不从领域词里抽 ——
按"怎么读邮件"检索，而不是按"量化"检索。

**单线程独占**：`entries` / 文件 / 脚本都由库自己的线程改（`_serve`），
调用方通过队列收发 —— 没有锁（AGENTS §9）。token 集合在载入/写入时算一次，
不在每次检索里重算（AGENTS §11）。
"""

import hashlib
import json
import os
import queue
import threading
import time

from .text import overlap, tokens


def cap_id(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:10]


class Caps:
    def __init__(self, path="caps.jsonl"):
        self.path = path
        # 能力自带脚本：内联 heredoc 的正文落在这里，配方指向它。
        # 于是配方可复现，而且跨项目活下来。
        self.scripts_dir = os.path.join(
            os.path.dirname(os.path.abspath(path)), "caps_scripts")
        self.entries = {}
        self._tok = {}
        self._load()
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    # ---------------------------------------------------------------- 存储
    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                e = json.loads(line)
                if e.get("id"):
                    self.entries[e["id"]] = e
                    self._index(e)

    def _index(self, e):
        """一条能力的三组 token 算一次存下来。检索时直接用，不重算。"""
        k = tokens(" ".join(e.get("keys") or []))
        d = tokens(e.get("does", ""))
        b = tokens(e.get("seen_in", "")
                   + " " + (e.get("evidence") or {}).get("obs", ""))
        b -= (k | d)
        self._tok[e["id"]] = (k, d, b)

    def _append(self, e):
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def _record(self, entry):
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
                with open(path, "w", encoding="utf-8") as f:
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
        self._index(e)
        self._append(e)
        return eid

    def _note_outcome(self, eid, ok):
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
    def _search(self, query):
        q = tokens(query)
        if len(q) < 1:
            return [], ""
        scored = []
        for e in self.entries.values():
            if e.get("retired"):
                continue
            # does+keys 是能力本身（权重 2）；seen_in + obs 是中文桥（权重 1）。
            # 叶子用中文提问而键是英文，需要这个桥；但不能让桥淹没能力本身，
            # 否则"把 1 到 100 的和写进文件"会命中 `pip install pandas`。
            k_tok, d_tok, b_tok = self._tok[e["id"]]
            k_hit, d_hit, b_hit = (overlap(q, k_tok), overlap(q, d_tok),
                                   overlap(q, b_tok))
            # 中文桥不能单独召回。
            if not (k_hit or d_hit or b_hit >= 2):
                continue
            scored.append((3 * k_hit + d_hit + b_hit, e.get("uses", 0), e))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        # 不设 top-k、不设总量封顶：命中多少给你多少。
        # 词法匹配本身就很克制，而且**在背后替你丢掉几条**是最坏的选择 ——
        # 模型根本不知道自己少看了东西。
        return self._render([e for _, _, e in scored])

    def _render(self, picked):
        """一条 cap 里最重要的是：怎么用（用法）+ 需要什么前提 + 会影响什么。
        "前提" 尤其重要——复用失败最常见的原因是前提不成立，
        而不是配方错。没这一项，一条好配方会被记成"烂了"。
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

    def _stats(self):
        live = [e for e in self.entries.values() if not e.get("retired")]
        return {"总数": len(live),
                "已退休": len(self.entries) - len(live),
                "自带脚本": sum(1 for e in live if (e.get("how") or {}).get("script_file")),
                "有契约": sum(1 for e in live if e.get("契约")),
                "有复用记录": sum(1 for e in live if e["uses"] + e["fails"] > 0)}

    # ---------------------------------------------------------------- 单线程门
    def _serve(self):
        while True:
            op, arg, reply = self._q.get()
            if op == "record":
                reply.put(self._record(arg))
            elif op == "note_outcome":
                eid, ok = arg
                self._note_outcome(eid, ok)
                reply.put(None)
            elif op == "search":
                reply.put(self._search(arg))
            else:
                reply.put(self._stats())

    def _call(self, op, arg=None):
        if not self._thread.is_alive():
            raise RuntimeError("能力库线程已死（%s）：后续操作不再安全" % self.path)
        reply = queue.Queue()
        self._q.put((op, arg, reply))
        try:
            return reply.get(timeout=60)
        except queue.Empty:
            raise RuntimeError("能力库线程没有响应（%s）" % self.path)

    def record(self, entry):
        return self._call("record", entry)

    def note_outcome(self, eid, ok):
        self._call("note_outcome", (eid, ok))

    def search(self, query):
        return self._call("search", query)

    def stats(self):
        return self._call("stats")
