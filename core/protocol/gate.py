"""闸门：形式字段上的机械校验，不采信自报，只核对指得到的东西。

代码只做四件事（都在形式字段上，不是计数器）：① 规范化字段（不切长度，kind 只能是
dispatch / leaf）；② 子任务验收标准必须携带父/根的可测物理量，否则当场被拒；
③ 一次最多一个门槛，不成立则其余子任务不启动；④ 判定"满足"却指不出证据就降级为"未满足"。

提示词在 `core/prompts/`，改完要回来对一遍上面这几件事。
"""

import os
import re

from ..prompts import feedback
from ..prompts.messages import result_marks
from .fields import EXTERNAL_CLASSES, SATISFIED, UNSATISFIED, VERDICTS, norm
from .tool_specs import ACTION_TOOLS

# "可测物理量"：日期、≥2 位数字、标识符；单个数字不算
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


def parse_range(v):
    """结论字数区间 [下限, 上限]；是上层对下层回复粒度的要求，不是字数警察。"""
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
    """规范化一个子任务的形式字段，没有任何长度检查。

    必填 name / detail / accept / kind / conc_range，选填 notes、gate；kind 写错当场拒、
    不默认成 dispatch（兜底会把"没说清"变成既成事实）。
    """
    kind = norm(spec.get("kind"))
    out = {"name": norm(spec.get("name")),
           "detail": norm(spec.get("detail")),
           "notes": norm(spec.get("notes")),
           "accept": norm(spec.get("accept")),
           "kind": kind,
           "gate": bool(spec.get("gate")),
           "conc_range": parse_range(spec.get("conc_range"))}
    why = []
    missing = [k for k in ("name", "detail", "accept") if not out[k]]
    if missing:
        why.append(feedback.missing_fields(missing))
    # kind 不默默兜底成 dispatch：写错不是非法值，是没填对
    if kind not in ("dispatch", "leaf"):
        why.append(feedback.bad_kind(kind))
    if not out["conc_range"]:
        why.append(feedback.bad_conc_range())
    return out, ("; ".join(why) or None)


# 结论审计里的"观测"只指叶子亲手做的动作（bash/read/write）；分配节点的 tool 回话不算观测。
def _obs_rounds(msgs):
    """一份对话里叶子动手过的轮数（观测序号从 1 数）。"""
    n = 0
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        for tc in m.get("tool_calls") or []:
            if (tc.get("function") or {}).get("name") in ACTION_TOOLS:
                n += 1
                break
    return n


def evidence_ok(ev, msgs):
    """证据必须指得到真实存在的东西：某次观测、某个子节点、或磁盘上真有的产物。

    这是代码替上层做的第一道复核（不加它，编一句"子任务A 的结论"就能过）。证据可能是
    复合串（`第1次观测 / add.py`），拆开逐段看；分配节点自己没有观测，只能引子任务名或产物路径。

    观测序号 = 对话里叶子动手过的轮数；子任务名 = 注入过的下层结论；都从 msgs 推导。
    """
    valid, bad = [], []
    obs_idx = set(range(1, _obs_rounds(msgs) + 1))
    _, kids = result_marks(msgs)
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


def clean_conclusion(concl, store, node, msgs=None):
    """判定必须是 满足|未满足|阻塞，判定"满足"得指得出真证据（观测 / 子任务 / 磁盘产物）。

    返回 (结论, None) 或 (None, 打回理由)；msgs 是平铺对话，证据校验从这里推导。
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
    if verdict not in VERDICTS:
        return None, feedback.bad_verdict()

    if verdict == SATISFIED:
        valid, bad = evidence_ok(ev, msgs or [])
        if not valid:
            store.record(node.id, "verdict_downgraded",
                      {"was": SATISFIED, "reason": "证据指不到任何真实存在的东西",
                       "evidence": bad})
            return {"verdict": UNSATISFIED, "content": content +
                    feedback.downgraded_suffix(),
                    "evidence": [], "external": []}, None
        if bad:
            store.record(node.id, "evidence_trimmed", {"dropped": bad, "kept": valid})
        ev = valid
    return {"verdict": verdict, "content": content, "evidence": ev,
            "external": ext}, None


def validate_root(spec):
    """根节点的闸门 = 分配节点的校验，加一条：验收标准必须有一个可测物理量，否则这棵树判不了做没做完。"""
    out, why = clean_spec(spec or {})
    if why:
        return None, why
    if not anchors(out["accept"]):
        return None, feedback.root_needs_anchor()
    return out, None
