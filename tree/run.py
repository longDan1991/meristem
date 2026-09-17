"""两种节点，一套形式化协议。整个设计就在这一段。

    分配节点：读自己的形式字段 + 本层已有尝试 → 「再做一次分配」或「出结论」
    叶子：  读自己的形式字段 + 观测历史   → 「做一个动作」或「出结论」

原则：
  · 形式化的是字段，次数不限，判断只看已经发生的事实
  · 分配节点**没有 execute 分支** ——"不拆"就是派一个叶子
  · 完成与否由上层看证据复核，节点只能说判定，不能自己算数
  · 所以这里没有任何计数器（max_rounds / self_exec / nudged / rejects 全部删除）

代码只做四件事（都在形式字段上，不是计数器）：
  ① 规范化字段（**不切长度** —— 上限由提示词承诺，代码不再偷偷砍）
  ② 子任务的验收标准必须携带父/根的可测物理量，否则这次分配当场被拒并记进尝试
  ③ 一次最多一个门槛；门槛不成立，其余子任务不启动
  ④ 判定"满足"却指不出证据 → 降级为"未满足"

提示词在 `prompts/*.md` ——
改提示词不用碰代码，但改完要回来对一遍上面那四件事。
"""

import json
import os
import re
import threading
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .effects import contract_of, contract_problems, effects_of

# 哪些产出物必须给契约（要么给契约，要么明确声明它属于内部）。
# 日志/缓存这类副产物不在里面。
ARTIFACT_EXT = (".py", ".sh", ".js", ".ts", ".rb", ".json",
                ".yaml", ".yml", ".toml", ".csv", ".sql")
from .llm import parse_json
from .node import EXTERNAL_CLASSES, Budget, Node, Trace, norm
from .prompts import PROMPT
from .tools import TOOLS

TOOL_LOCK = threading.Lock()

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


# 两套系统提示词在 `prompts/alloc.md` / `prompts/leaf.md` —— 它们是协议的一部分，
# 每一条硬性要求都对应下面的一处代码检查。


# ---------------------------------------------------------------- 日志
def _log_usage(llm, trace, node_id, phase, budget=None):
    u = getattr(llm, "last_usage", None)
    if not u:
        return
    total = u.get("total_tokens", 0)
    trace.add(node_id, "usage", {
        "phase": phase, "prompt": u.get("prompt_tokens", 0),
        "completion": u.get("completion_tokens", 0),
        "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        "cached": (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
        "total": total})
    if budget is not None:
        budget.add_tokens(total)


def _ask(llm, trace, node, which, budget):
    trace.add(node.id, "%s_in" % which, node.render())
    text = llm.chat([{"role": "system", "content": PROMPT[which]},
                     {"role": "user", "content": node.render()}])
    _log_usage(llm, trace, node.id, which, budget)
    trace.add(node.id, "%s_out" % which, text)
    try:
        d = parse_json(text)
    except Exception as e:
        return {"_bad": "输出不是合法 JSON：%s" % e}
    if not isinstance(d, dict):
        return {"_bad": "输出必须是一个 JSON 对象"}
    return d


# ---------------------------------------------------------------- 形式校验
def _clean_spec(spec):
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
           "keywords": _parse_keywords(spec.get("keywords")),
           "conc_range": _parse_range(spec.get("conc_range"))}
    why = []
    missing = [k for k in ("name", "detail", "accept") if not out[k]]
    if missing:
        why.append("缺必填项: " + ", ".join(missing))
    if not out["keywords"]:
        why.append("keywords 必须是非空数组（它是下层自己去查老树的检索键）")
    if not out["conc_range"]:
        why.append("conc_range 必须是 [下限, 上限] 两个正整数，如 [100,500]")
    return out, ("; ".join(why) or None)


def _parse_keywords(v):
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


def _parse_range(v):
    """结论字数区间 [下限, 上限]。它是上层对下层回复粒度的要求，不是字数警察。"""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return None
    try:
        lo, hi = int(v[0]), int(v[1])
    except Exception:
        return None
    if lo < 1 or hi < lo:
        return None
    return [lo, hi]


def _evidence_ok(node, ev):
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


def _clean_conclusion(concl, trace, node, st=None):
    """代码检查，都是形式字段上的，不是计数器：
      ① 产出的每一个文件都必须在结论里交代（要么契约，要么声明内部）
      ② 判定"满足"得指得出真证据
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
    unacct = _unaccounted(st, artifacts)
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
        valid, bad = _evidence_ok(node, ev)
        if not valid:
            trace.add(node.id, "verdict_downgraded",
                      {"was": "满足", "reason": "证据指不到任何真实存在的东西",
                       "evidence": bad})
            return {"verdict": "未满足", "content": content +
                    "（原判「满足」但证据指不到真实的东西，已降级）",
                    "evidence": [], "external": []}, None
        if bad:
            trace.add(node.id, "evidence_trimmed", {"dropped": bad, "kept": valid})
        ev = valid
    _accept_artifacts(node, artifacts, trace, st)
    return {"verdict": verdict, "content": content, "evidence": ev,
            "external": ext}, None


def _unaccounted(st, artifacts):
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


def _accept_artifacts(node, artifacts, trace, st):
    """把结论里交代的工件落成契约 + .meta.json。

    只在入口给完整契约；只给自己用的写 type="内部" 就行 —— 两者都要显式出现，
    因为是**结论里一次交代**，不是逼它一边干活一边填表。
    """
    for a in artifacts:
        if not isinstance(a, dict):
            continue
        path = str(a.get("path") or "").strip()
        if not path:
            continue
        rp = os.path.realpath(path)
        contract = contract_of(a)
        internal = contract.get("type") == "内部"
        eff, pre = (st or {}).get("art_effects", {}).get(rp, (None, None))
        problems = [] if internal else contract_problems(path, contract)
        trace.add(node.id, "contract", {"path": path, "contract": contract,
                                        "problems": problems, "source": "conclusion",
                                        "effects": eff, "preconditions": pre})
        st.setdefault("contracts", []).append({"path": path, "契约": contract,
                                               "effects": eff, "前置条件": pre})
        if not internal and contract and not problems:
            _write_sidecar(path, contract, eff, pre)


# ---------------------------------------------------------------- 动作
def _write_sidecar(path, contract, eff=None, pre=None):
    """把契约写在工件旁边。这样即使没有检索，谁看到这个文件都知道怎么用它。"""
    try:
        mp = str(path) + ".meta.json"
        meta = {}
        if os.path.exists(mp):
            try:
                meta = json.load(open(mp))
            except Exception:
                meta = {}
        meta["契约"] = contract
        if eff:
            meta["effects"] = eff
        if pre:
            meta["前置条件"] = pre
        with open(mp, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _sig(tool, args, obs):
    """动作 + 观测的指纹。用于检测"重复同一件事、没有新信息"。

    这不是轮次上限：只要观测变了（比如轮询一个正在启动的服务），
    指纹就不同，永远不会触发。它检测的是**没有新信息**，不是"做得太多"。

    观测**整段参与哈希**：截掉尾巴会让"只在 400 字之后不一样"的两次观测
    看起来一样，于是真的进展被当成原地打转。哈希再长的字符串也不贵。
    """
    import hashlib
    a = json.dumps({"tool": tool, "args": args}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1((a + "\x00" + str(obs)).encode()).hexdigest()


def _bump(seen, sig, trace, node, what):
    """同一份东西重复出现 ≥3 次就显式告警，≥5 次就自己停下。

    不是轮次上限：换一个动作、或者世界回话变了，指纹就不同（§2.4）。
    它检测的是**没有新信息**。这里既用于"重复同一个动作"，也用于
    "重复同一份看不懂的输出" —— 后者根本没有动作，所以更隐蔽
    （实测撞过一次：mock 还在说旧协议的键，同一回合无限重复）。
    """
    seen[sig] = seen.get(sig, 0) + 1
    n = seen[sig]
    if n < 3:
        return n, ""
    trace.add(node.id, "no_progress", {"times": n, "action": what})
    return n, ("\n[停止] 已经有 %d 次是同样的东西了：%s —— 再重复不会带来新信息。\n"
               "换一个动作，或者出结论（阻塞就写清为什么）。" % (n, what))


def _balk(node, why, trace, st, kids=None):
    """把"这次给的东西用不了"变成一条可见的事实，并且**按重复次数处理**。

    四个地方都要走它：看不懂的输出、被代码拒的分配、不合规的结论。
    没有它，模型一直给同样的东西，这一回合就原地无限重复 ——
    实测撞过两次（旧协议的键；总缺 accept 的子任务）。那两种情况下
    根本没有动作，所以"重复动作"那个信号永远不会触发：这里必须自己数。

    这不是轮次上限：换一种拆法、换一个错，指纹就不同（§2.4）。
    """
    if node.kind == "leaf":
        node.observations.append({"action": "(用不了)", "obs": why})
    else:
        node.attempts.append({"children": kids or [], "rejected": why})
    n, note = _bump(st.setdefault("seen_actions", {}),
                    _sig("(balk)", why, ""), trace, node, "(用不了的输出)")
    if n >= 5:
        node.close("未满足", "同一份用不了的东西连续 %d 次，没有新信息：%s"
                   % (n, why), [])
        return {"kind": "finished"}
    if note:
        if node.kind == "leaf":
            node.observations[-1]["obs"] += note
        else:
            node.attempts[-1]["rejected"] += note
    return {"kind": "again"}


def _do_action(node, act, trace, caps, st):
    """执行一个形式化动作。返回观测文本。动作是唯一能改变世界的东西。"""
    tool = str(act.get("tool", ""))
    args = act.get("args") or {}
    if not isinstance(args, dict):
        return "参数必须是一个 JSON 对象"
    fn = TOOLS.get(tool)
    if fn is None:
        return ("没有这个工具：%s（只有 bash / read / write）\n"
                "现成做法已经在上面的「现成做法」里了，直接用 bash 跑。" % tool)
    # offset/limit 必须传下去 —— read 的返回里就写着
    # "read(offset=2000) 取下一段"，不传的话模型照做了也拿不到下一段，
    # 它就只能反复重读（这正是当年读了 25 次的那个坑）。
    call_args = {k: args[k] for k in ("path", "content", "cmd", "timeout",
                                      "offset", "limit") if k in args}
    # write 必须在动作**之前**记下文件存不存在，否则 create 永远被记成 modify
    existed = None
    if tool == "write":
        try:
            existed = os.path.exists(str(args.get("path")))
        except Exception:
            existed = False
    try:
        if tool in ("bash", "write"):
            with TOOL_LOCK:
                obs = fn(**call_args)
        else:
            obs = fn(**call_args)
    except Exception as e:
        # 工具报错**也是一次真实观测**（世界说"不行"），不能提前 return ——
        # 提前 return 会让它绕过调用方的重复计数，于是同一个报错无限重试。
        obs = "工具出错: %r" % e

    # 动作之后统一记账：effects 由代码抽，不给模型自报的机会。
    # bash 和 write 共用这一套 —— 它们本来就是同一件事的两个壳。
    eff, pre = effects_of(tool, args, cwd=os.getcwd(), existed_before=existed)
    # effects / 前置条件 是 effects.py 自己的词表（能力库、sidecar 也用它），
    # 跟形式字段不是一套；这里只把协议那个键写成英文。
    trace.add(node.id, "effects", {"tool": tool, "effects": eff, "前置条件": pre})
    # 产出物由代码记账（模型只管干活）。effects 留着，结论时给契约用。
    made = []
    for p in eff["fs"]["create"] + eff["fs"]["modify"]:
        if str(p).lower().endswith(ARTIFACT_EXT):
            rp = os.path.realpath(p)
            st.setdefault("artifacts", set()).add(rp)
            st.setdefault("art_effects", {})[rp] = (eff, pre)
            if p in eff["fs"]["create"]:
                made.append(os.path.basename(p))
    # 过程中只给一个中性事实，不下指令 —— 不分散注意力
    note = "\n（本次产出：%s）" % ", ".join(made) if made else ""

    # 复用反馈：刚检索出来的做法，用它成没成
    if caps is not None and tool == "bash" and st.get("_caps"):
        cmd = str(args.get("cmd", ""))
        for e in list(st["_caps"]):
            c = (e.get("how") or {}).get("cmd") or ""
            if c and (c in cmd or cmd in c):
                ok = ("工具出错" not in str(obs)
                      and ("[exit=" not in str(obs) or "[exit=0]" in str(obs)))
                caps.note_outcome(e["id"], ok)
                trace.add(node.id, "cap_outcome", {"cap": e["id"], "ok": ok})
                break
        st["_caps"] = []
    # 无进展检测：同一动作 + 同一结果重复多次 = 再重复不会带来新信息。
    # 实测：一个叶子把同一个文件读了 25 次，光摆着历史它停不下来。
    # 所以把"重复"这个事实显式化（内容信号，不是轮次预算）。
    # 计数**不在这里做** —— 这里有好几个 return，漏掉一个就是死循环。
    # 收口在 _step：每一回合的动作都在那里计数，一条路也漏不了。
    return str(obs) + note


# ---------------------------------------------------------------- 一回合
def _step(nid, ctx):
    """一个节点的一回合。不递归，只返回下一步该干什么。"""
    st = ctx["state"][nid]
    node = st["node"]
    llm, trace, budget, caps = ctx["llm"], ctx["trace"], ctx["budget"], ctx["caps"]

    if budget.exhausted():
        node.close("阻塞", "预算耗尽: " + budget.why(), [])
        node.status = "failed"
        trace.add(node.id, "budget_exhausted", node.conclusion)
        return {"kind": "finished"}

    which = "leaf" if node.kind == "leaf" else "alloc"
    d = _ask(llm, trace, node, which, budget)

    if d.get("_bad"):
        # 把非法输出当成一条事实喂回去，让它自己纠正（不加计数器）
        trace.add(node.id, "bad_output", d["_bad"])
        return _balk(node, d["_bad"], trace, st)

    concl = d.get("conclusion")
    if isinstance(concl, dict):
        got, err = _clean_conclusion(concl, trace, node, st)
        if err:
            trace.add(node.id, "bad_conclusion", err)
            return _balk(node, err, trace, st)
        node.close(got["verdict"], got["content"], got["evidence"], got["external"])
        trace.add(node.id, "concluded",
                  {"verdict": got["verdict"], "text": got["content"],
                   "evidence": got["evidence"], "external": got["external"]})
        return {"kind": "finished"}

    if node.kind == "leaf":
        act = d.get("action")
        if not isinstance(act, dict):
            return _balk(
                node,
                "输出里没有能识别的顶层键（你只能给 action 或 conclusion）。"
                "你给的键是: %s" % (", ".join(sorted(d)) or "(空)"),
                trace, st)
        obs = _do_action(node, act, trace, caps, st)
        label = "%s %s" % (act.get("tool", ""),
                           json.dumps(act.get("args") or {}, ensure_ascii=False))
        # 每一回合的动作只在这一处计数：动作成没成、工具报不报错，都得过这里，
        # 所以"同一动作 + 同一结果 ≥3 告警 / ≥5 停下"没有漏网的路。
        n, note = _bump(st.setdefault("seen_actions", {}),
                        _sig(act.get("tool"), act.get("args") or {}, obs),
                        trace, node, str(act.get("tool")))
        if n >= 5:
            st["stalled"] = ("同一动作重复 %d 次、结果完全一样，没有新信息" % n)
        if note:
            obs = str(obs) + note
        node.observations.append({"action": label, "obs": obs})
        st["calls"].append((act.get("tool"), act.get("args") or {}, obs))
        # 存结构化参数：挖掘器要能直接读，不该去反解一个拼出来的字符串
        trace.add(node.id, "action", {"tool": act.get("tool"),
                                      "args": act.get("args") or {},
                                      "obs": obs})
        stalled = st.pop("stalled", None)
        if stalled:
            trace.add(node.id, "stalled", stalled)
            node.close("未满足", stalled, [])
            return {"kind": "finished"}
        return {"kind": "again"}

    # ── 分配节点：再拆一层 ──
    specs = d.get("children")
    if not isinstance(specs, list) or not specs:
        return _balk(
            node,
            "输出里没有能识别的顶层键（你只能给 children 或 conclusion）。"
            "你给的键是: %s" % (", ".join(sorted(d)) or "(空)"),
            trace, st)

    kids_spec, reject = [], None
    for raw in specs:                         # 不砍：拆几个是模型的决定
        s, why = _clean_spec(raw if isinstance(raw, dict) else {})
        if why:
            reject = why
            break
        # ② 子任务的验收标准必须携带父/根的可测物理量
        ra = ctx["root_anchors"]
        ok_parent = inherits(node.accept, s["accept"])
        ok_root = (not ra) or any(x in s["accept"] for x in ra)
        if not (ok_parent and ok_root):
            reject = ("子任务的验收标准丢了可测物理量（缺 %s）—— 这是把任务换成了别的东西"
                      % ", ".join(sorted(ra or anchors(node.accept))))
            trace.add(node.id, "criterion_drift",
                      {"child": s["name"], "accept": s["accept"],
                       "parent_anchors": sorted(anchors(node.accept)),
                       "root_anchors": sorted(ra)})
            break
        kids_spec.append(s)

    if reject:
        # 把被拒这件事变成一条可见的事实（而不是丢弃或加计数器）
        return _balk(node, reject, trace, st, kids=kids_spec)

    gates = [s for s in kids_spec if s["gate"]]
    if len(gates) > 1:
        return _balk(node, "一次分配最多一个门槛", trace, st, kids=kids_spec)
    gate = gates[0] if gates else None
    if gate:
        first = [gate]
        rest = [s for s in kids_spec if s is not gate]
    else:
        first, rest = kids_spec, []          # 没有门槛就没有“暂缓”，不能把全部当成暂缓

    if not budget.take_nodes(len(kids_spec)):
        return _balk(node, "节点预算不足", trace, st, kids=kids_spec)
    node.attempts.append({"children": kids_spec, "results": [], "outcome": "等下层"})
    trace.add(node.id, "allocated",
              {"round": len(node.attempts), "gate": gate["name"] if gate else None,
               "deferred": [s["name"] for s in rest] if gate else []})
    return {"kind": "children", "first": first, "rest": rest,
            "gate_name": gate["name"] if gate else None}


def run(root, llm, trace, registry=None, budget=None, workers=6, caps=None,
        index=None):
    """广度优先、并行扇出的调度器。次数不限——没有 max_depth/max_rounds。"""
    registry = {} if registry is None else registry
    budget = Budget() if budget is None else budget
    trace = trace if isinstance(trace, Trace) else Trace(trace)
    state, pending = {}, deque()

    def register(node, spec=None):
        state[node.id] = {"node": node, "ready": True, "finished": False,
                          "waiting": 0, "rest": [], "gate_id": None,
                          "gate_name": None, "calls": [], "_caps": [],
                          "contracts": [], "artifacts": set(), "art_effects": {},
                          "seen_actions": {}}
        registry[node.id] = node
        trace.add(node.id, "open", {
            "name": node.name, "detail": node.detail, "notes": node.notes,
            "accept": node.accept, "kind": node.kind, "gate": node.gate,
            "depth": node.depth, "parent": node.parent,
            "keywords": node.keywords, "conc_range": node.conc_range,
            "workspace": os.path.abspath(os.getcwd())})
        # 出生即检索：键是**上层给的**（根没有上层，就用它自己的名字+验收标准）。
        # 检索不花 LLM 调用，也不问模型要不要查 —— 实测它没有理由去查，
        # 而真正贵的恰恰是大事（DESIGN §5.4）。
        if index is not None:
            qs = node.keywords or ["%s %s" % (node.name, node.accept)]
            try:
                picked, text = index.search(qs, workspace=os.getcwd())
                if text:
                    node.precedents.append(text)
                trace.add(node.id, "precedent",
                          {"queries": qs, "auto": True,
                           "hits": [p.id for p in picked], "chars": len(text)})
            except Exception as ex:
                trace.add(node.id, "precedent_failed", "%r" % ex)
        # 现成做法也在出生时塞进来：模型没有动机去主动找工具（它觉得自己都会，§4.3），
        # 所以没有 need 这个动作 —— 程序按同一组检索键查能力库，直接给它。
        if caps is not None:
            q = " ".join(str(x) for x in
                         (node.keywords or [node.name, node.accept]))
            try:
                picked, text = caps.search(q)
                if text:
                    node.caps.append(text)
                state[node.id]["_caps"] = picked
                trace.add(node.id, "caps_injected",
                          {"queries": node.keywords or [node.name],
                           "hits": [e["id"] for e in picked], "chars": len(text)})
            except Exception as ex:
                trace.add(node.id, "caps_failed", "%r" % ex)
        pending.append(node.id)

    def learn(node, calls, contracts=None):
        from .mine import caps_from_node
        skipped = []
        try:
            for e in caps_from_node(node.id, node.name, calls,
                                    os.path.basename(getattr(trace, "path", "")),
                                    contracts, skipped):
                caps.record(e)
                trace.add(node.id, "cap_learned",
                          {"does": e["does"], "keys": e["keys"],
                           "scope": e.get("scope"),
                           "有契约": bool(e.get("契约"))})
            # 不收的能力也要说得出来：理由 + 原命令，不悄悄丢
            for s in skipped:
                trace.add(node.id, "cap_skipped", s)
        except Exception as ex:
            trace.add(node.id, "cap_learn_failed", "能力提取出错: %r" % ex)

    def settle(nid, res):
        st = state[nid]
        if res["kind"] == "finished":
            st["finished"] = True
            node = st["node"]
            if node.verdict in ("满足", "未满足") and caps is not None and st["calls"]:
                learn(node, st["calls"], st.get("contracts"))
            parent = node.parent
            if parent and parent in state:
                pst = state[parent]
                pn = pst["node"]
                if pn.attempts:
                    pn.attempts[-1].setdefault("results", []).append(node.record())
                # 门槛不成立 → 整个分支作废，其余子任务永不启动
                if pst.get("gate_id") == nid and node.verdict != "满足":
                    skipped = [s["name"] for s in pst.get("rest") or []]
                    pst["rest"], pst["gate_id"] = [], None
                    if pn.attempts:
                        pn.attempts[-1]["outcome"] = "门槛不成立（%s）: %s" % (
                            node.name, node.conclusion)
                        if skipped:
                            pn.attempts[-1]["results"].append(
                                {"name": "（以下子任务被跳过）", "outcome": "未启动",
                                 "text": ", ".join(skipped), "evidence": []})
                    trace.add(parent, "gate_failed",
                              {"gate": node.name, "reason": node.conclusion,
                               "skipped": skipped})
                    if not pst["finished"]:
                        pst["ready"] = True
                        pending.append(parent)
                    return
                pst["waiting"] -= 1
                if pst["waiting"] <= 0 and not pst["finished"]:
                    if pn.attempts:
                        pn.attempts[-1]["outcome"] = "下层已全部返回"
                    if pst.get("rest"):
                        rest, pst["rest"], pst["gate_id"] = pst["rest"], [], None
                        trace.add(parent, "gate_passed",
                                  {"started": [s["name"] for s in rest]})
                        kids = _spawn(pn, rest, budget, trace)
                        for k in kids:
                            register(k)
                        pst["waiting"] = len(kids)
                    else:
                        pst["ready"] = True
                        pending.append(parent)
        elif res["kind"] == "children":
            for k in res["kids"]:
                register(k)
            st["waiting"] = len(res["kids"])
            st["rest"] = res.get("rest") or []
            st["gate_id"] = res.get("gate_id")
        else:                                      # again：接着再来一回合
            if not st["finished"]:
                st["ready"] = True
                pending.append(nid)

    def _spawn(parent, specs, budget, trace):
        kids = []
        for s in specs:
            kids.append(Node(name=s["name"], detail=s["detail"], notes=s["notes"],
                             accept=s["accept"], kind=s["kind"], gate=s["gate"],
                             keywords=s["keywords"], conc_range=s["conc_range"],
                             parent=parent.id, depth=parent.depth + 1))
        parent.children += [k.id for k in kids]
        return kids

    ctx = {"state": state, "llm": llm, "trace": trace, "budget": budget,
           "root_anchors": anchors(root.accept), "caps": caps, "index": index}

    register(root)

    def dispatch(nid, res):
        """把 _step 的抽象结果翻译成真实的节点/子节点。"""
        if res["kind"] != "children":
            settle(nid, res)
            return
        st = state[nid]
        pn = st["node"]
        first = _spawn(pn, res["first"], budget, trace)
        rest = res["rest"]
        gate_kid = first[0] if res["gate_name"] else None
        # 门槛节点改名以便追踪：它的判定决定其余子任务是否值得启动
        settle(nid, {"kind": "children", "kids": first,
                     "rest": rest,
                     "gate_id": gate_kid.id if gate_kid else None})

    inflight = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or inflight:
            while pending and len(inflight) < workers:
                nid = pending.popleft()
                st = state[nid]
                if st["finished"] or not st["ready"]:
                    continue
                st["ready"] = False
                inflight[pool.submit(_step, nid, ctx)] = nid
            if not inflight:
                break
            done, _ = wait(list(inflight), return_when=FIRST_COMPLETED)
            for fut in done:
                nid = inflight.pop(fut)
                try:
                    dispatch(nid, fut.result())
                except Exception as e:
                    st = state[nid]
                    st["node"].close("阻塞", "异常: %r" % e, [])
                    st["node"].status = "failed"
                    trace.add(nid, "crashed", str(e))
                    settle(nid, {"kind": "finished"})
    return root


def render_tree(root, registry, prefix="", is_last=True, lines=None):
    b = "└─ " if is_last else "├─ "
    mark = {"done": "✓", "failed": "✗", "running": "·"}.get(root.status, "?")
    if lines is None:
        lines = []
    tag = "%s%s" % ("[分配]" if root.kind == "dispatch" else "[叶子]", " [门槛]" if root.gate else "")
    lines.append("%s%s%s %s %s" % (prefix, b, mark, tag, root.name))
    lines.append("%s%s  [%s] %s" % (prefix, "  " if is_last else "│ ",
                                    root.verdict or "…", root.accept))
    if root.conclusion:
        lines.append("%s%s  → %s" % (prefix, "  " if is_last else "│ ",
                                     root.conclusion))
    for i, cid in enumerate(root.children):
        kid = registry.get(cid)
        if kid:
            render_tree(kid, registry, prefix + ("   " if is_last else "│  "),
                        i == len(root.children) - 1, lines)
    return lines
