"""闸门：形式字段上的机械校验。不采信自报，只核对指得到的东西。

代码只做四件事（都在形式字段上，不是计数器）：
  ① 规范化字段（**不切长度** —— 上限由提示词承诺，代码不再偷偷砍）
  ② 子任务的验收标准必须携带父/根的可测物理量，否则这次分配当场被拒并记进尝试
  ③ 一次最多一个门槛；门槛不成立，其余子任务不启动
  ④ 判定"满足"却指不出证据 → 降级为"未满足"

再加上结论里的工件契约核对：产出的每个文件都要交代，`func` 必须是能直接执行的命令。

提示词在 `prompts/*.md` —— 改提示词不用碰代码，但改完要回来对一遍上面这几件事。
"""

import os
import re

from ..effects import contract_of, contract_problems
from .fields import EXTERNAL_CLASSES, norm

# 判据里的"可测物理量"：日期、≥2 位数字、标识符。单个数字不算。
ANCHOR_RE = re.compile(
    r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{2,}|[A-Za-z_][A-Za-z0-9_.\-]+")


def anchors(text):
    return set(ANCHOR_RE.findall(text or ""))


def inherits(parent_accept, child_accept):
    """子任务的验收标准是否继承了父任务的同一可测物理量。"""
    a = anchors(parent_accept)
    if not a:
        return True
    return any(x in (child_accept or "") for x in a)


def parse_keywords(v):
    """检索键。键用可执行形状（包名/命令动词/数字/脚本名），不是形容词。"""
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for x in v:
        s = norm(x)
        if s and s not in out:
            out.append(s)
    return out


def parse_range(v):
    """结论字数区间 [下限, 上限]。它是上层对下层回复粒度的要求，不是字数警察。"""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return None
    try:
        lo, hi = int(v[0]), int(v[1])
    except (TypeError, ValueError):
        return None
    if lo < 1 or hi < lo:
        return None
    return [lo, hi]


def clean_spec(spec):
    """规范化一个子任务的形式字段。**没有任何长度检查**（提示词里的字数只是建议）。

    必填：name / detail / accept / kind / keywords / conc_range。
    选填：notes —— 而且它**不参与老树检索**（§5.2：检索键要用可执行形状，
    自由发挥的判断依据放进去只会污染词法匹配）。gate 是个开关，默认 false。
    """
    out = {"name": norm(spec.get("name")),
           "detail": norm(spec.get("detail")),
           "notes": norm(spec.get("notes")),
           "accept": norm(spec.get("accept")),
           "kind": "leaf" if norm(spec.get("kind")) == "leaf" else "dispatch",
           "gate": bool(spec.get("gate")),
           "keywords": parse_keywords(spec.get("keywords")),
           "conc_range": parse_range(spec.get("conc_range"))}
    why = []
    missing = [k for k in ("name", "detail", "accept") if not out[k]]
    if missing:
        why.append("缺必填项: " + ", ".join(missing))
    if not out["keywords"]:
        why.append("keywords 必须是非空数组（它是下层自己去查老树的检索键）")
    if not out["conc_range"]:
        why.append("conc_range 必须是 [下限, 上限] 两个正整数，如 [100,500]")
    return out, ("; ".join(why) or None)


def evidence_ok(node, ev):
    """证据必须指得到真实存在的东西：某次观测、某个子节点、或磁盘上真有的产物。

    这是代码替上层做的**第一道**复核。不加它，`判定:满足` 配一句编出来的
    "子任务A 的结论" 就能过 —— 第一次跑就撞到了。

    证据可能是复合串（模型会写 `第1次观测 / add.py`），所以要拆开逐段看。
    分配节点**自己没有观测**，它的证据只能是子任务名或产物路径。
    """
    valid, bad = [], []
    obs_idx = set(range(1, len(node.observations) + 1))
    # 证据引自**任何一轮**分配出来的子节点都算数。只看最后一轮会误杀：
    # 末轮是"不再拆、直接出结论"那次，results 是空的，于是上一轮真跑过的
    # 子任务名被判成"编出来的"，一次本该满足的结论被降级成未满足。
    kids = []
    for a in node.attempts:
        kids += [c.get("name", "") for c in a.get("results", [])]
    for x in ev:
        s = str(x).strip()
        hit = False
        for part in re.split(r"[/、,，;；|]+", s):
            part = part.strip().strip("'\"` ")
            if not part:
                continue
            if (obs_idx and "观测" in part
                    and any(int(m) in obs_idx for m in re.findall(r"\d+", part))):
                hit = True
                break
            if any(k and (k in part or part in k) for k in kids):
                hit = True
                break
            if os.path.exists(part):
                hit = True
                break
        (valid if hit else bad).append(s)
    return valid, bad


def unaccounted(st, artifacts):
    """哪些产出还没被交代。结论里每一个产出的文件都得出现（给契约或标内部）。"""
    if not st:
        return []
    declared = set()
    for a in artifacts:
        p = str((a or {}).get("path") or "") if isinstance(a, dict) else ""
        if p:
            declared.add(os.path.realpath(p))
    return [os.path.basename(p) for p in sorted(st.get("artifacts", set()) - declared)
            if os.path.exists(p)]


def clean_conclusion(concl, trace, node, st=None):
    """代码检查，都是形式字段上的，不是计数器：
      ① 产出的每一个文件都必须在结论里交代（要么契约，要么声明内部）
      ② 判定"满足"得指得出真证据

    返回 (结论, None) 或 (None, 打回理由)。工件契约的落盘由调用方做
    （那要写 trace / sidecar，是运行时的事）。
    """
    verdict = norm(concl.get("verdict", ""))
    content = norm(concl.get("text", ""))
    ev = concl.get("evidence") or []
    if isinstance(ev, str):
        ev = [ev]
    ev = [norm(x) for x in ev if str(x).strip()]
    ext = concl.get("external") or []
    if isinstance(ext, str):
        ext = [ext]
    ext = [x for x in (str(x).strip() for x in ext) if x in EXTERNAL_CLASSES]
    artifacts = concl.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []
    if verdict not in ("满足", "未满足", "阻塞"):
        return None, "判定必须是 满足|未满足|阻塞"

    # ① 强制措施，放在这最后一步 —— 过程中完全不打扰它
    unacct = unaccounted(st, artifacts)
    if unacct:
        trace.add(node.id, "contract_missing", {"missing": unacct})
        return None, (
            "你这次工作产出了这些文件：%s\n"
            "结论里必须逐个交代它们（放在 \"artifacts\" 里）：\n"
            "  {\"artifacts\":[{\"path\":\"a.sh\",\"type\":\"脚本\","
            "\"name\":\"干什么用的\",\"func\":\"怎么跑\","
            "\"args\":\"\",\"return\":\"写什么\"},\n"
            "                 {\"path\":\"b.py\",\"type\":\"内部\"}]}\n"
            "能跑起来的那个（入口）要给完整契约；其余只给自己用的写 type=内部 就行。"
            % ", ".join(unacct))

    # ② 契约本身不合规 → 同样退回去改（func 必须是能直接跑的命令）
    bad_contracts = []
    for a in artifacts:
        if not isinstance(a, dict) or not a.get("path"):
            continue
        if (contract_of(a).get("type") or "") == "内部":
            continue
        probs = contract_problems(str(a["path"]), contract_of(a))
        if probs:
            bad_contracts.append("%s: %s" % (os.path.basename(str(a["path"])),
                                            "; ".join(probs)))
    if bad_contracts:
        trace.add(node.id, "contract_bad", {"problems": bad_contracts})
        return None, ("这些工件的契约有问题，请修正后重新出结论：\n  - %s\n"
                      "func 要写成**能直接粘上就执行**的一条命令，比如 "
                      "`bash sum.sh` 或 `python3 main.py --flag x`，"
                      "不要写「执行…即可运行」这种句子。"
                      % "\n  - ".join(bad_contracts))

    if verdict == "满足":
        valid, bad = evidence_ok(node, ev)
        if not valid:
            trace.add(node.id, "verdict_downgraded",
                      {"was": "满足", "reason": "证据指不到任何真实存在的东西",
                       "evidence": bad})
            return {"verdict": "未满足", "content": content +
                    "（原判「满足」但证据指不到真实的东西，已降级）",
                    "evidence": [], "external": [], "artifacts": artifacts}, None
        if bad:
            trace.add(node.id, "evidence_trimmed", {"dropped": bad, "kept": valid})
        ev = valid
    return {"verdict": verdict, "content": content, "evidence": ev,
            "external": ext, "artifacts": artifacts}, None


def validate_root(spec):
    """根节点的闸门 = 分配节点给孩子的校验，加一条根专属的：
    验收标准里必须有一个可测物理量。没有它，这棵树判不了自己做没做完。"""
    out, why = clean_spec(spec or {})
    if why:
        return None, why
    if not anchors(out["accept"]):
        return None, ("验收标准里必须有一个可测物理量（日期 / 两位以上数字 / "
                      "标识符如 hello.txt），否则这棵树判不了自己做没做完")
    return out, None
