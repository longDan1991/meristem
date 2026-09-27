"""闸门：形式字段上的机械形状校验。

只做两件事：子任务/任务根的必填项与形状（`clean_spec`）、`conc_range` 区间形状
（`parse_range`）。代码不判内容、不判做没做完 —— 判定权在父节点（最终是人），
代码只保证"形状合法，字段没被模型写坏"。

提示词在 `core/prompts/`，改完要回来对一遍上面这几件事。
"""

from . import feedback
from .fields import KINDS, norm


def parse_range(v):
    """回报字数区间 [下限, 上限]；是上层对下层回复粒度的要求，不是字数警察。"""
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

    必填 name / detail / kind / conc_range，选填 notes；kind 写错当场拒、
    不默认成 dispatch（兜底会把"没说清"变成既成事实）。
    """
    kind = norm(spec.get("kind"))
    out = {"name": norm(spec.get("name")),
           "detail": norm(spec.get("detail")),
           "notes": norm(spec.get("notes")),
           "kind": kind,
           "conc_range": parse_range(spec.get("conc_range"))}
    why = []
    missing = [k for k in ("name", "detail") if not out[k]]
    if missing:
        why.append(feedback.missing_fields(missing))
    # kind 不默默兜底成 dispatch：写错不是非法值，是没填对
    if kind not in KINDS:
        why.append(feedback.bad_kind(kind))
    if not out["conc_range"]:
        why.append(feedback.bad_conc_range())
    return out, ("; ".join(why) or None)
