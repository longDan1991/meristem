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

PROMPT 是可变层：自优化只允许改它。
"""

import json
import os
import re
import threading
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .effects import (EXTERNAL_CLASSES, contract_of, contract_problems,
                      effects_of)

# 哪些产出物必须给契约（要么给契约，要么明确声明它属于内部）。
# 日志/缓存这类副产物不在里面。
ARTIFACT_EXT = (".py", ".sh", ".js", ".ts", ".rb", ".json",
                ".yaml", ".yml", ".toml", ".csv", ".sql")
from .llm import parse_json
from .node import LIMITS, Budget, Node, Trace, norm
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


ALLOC_SYS = """你是一个分配节点。根据事实，决定"再做一次分配"还是"出结论"。

形式字段（上层下发，只读，不许改）：
  任务名 ≤20字 ／ 任务详情 ≤240字 ／ 注意事项 ≤120字 ／ 验收标准 ≤140字

只输出一个 JSON，二选一：

0) 想看以往有没有做过类似的事（大任务在第一次拆之前，建议先看一次）：
{"先例":{"查询":["2026-12-31 权益翻倍 的判据","A股 回测 扣费后正期望","开户 入金 实盘"]}}
   可以同时给多组查询（不同说法、不同侧面）。程序一次扫遍**所有老树**，
   返回从根到命中节点的**判据链**和它的工作目录。
   满足的先例可以照抄判据和拆法；阻塞的是死路——直接省掉重撞一遍。
   它是参考，不是事实：判据和环境都可能已经变了，要自己复核。
   看完了再拆，也不影响。

1) 再做一次分配：
{"再做一次":[{"任务名":"...","任务详情":"...","注意事项":"...","验收标准":"...","类型":"分配|叶子","门槛":true}]}
   硬性要求一：子任务的验收标准要比你的更接近"能直接观测"，做不到就不要拆。
   硬性要求二：子任务的验收标准里必须原样出现你验收标准里的可测物理量
   （日期、两位以上数字、标识符如 CSV/MA5/hello.txt）。换成下游指标不算，
   会被代码拒掉。
   硬性要求三：最多一个 门槛 —— 这一堆里哪一条不成立，整个分支就作废？
   它会被第一个做，且在它通过之前其余子任务一律不启动。想不出作废条件就别标。
    次数不限。但你已经试过的都记在"本层已有尝试"里 —— 别重复撞同一堵墙。

2) 出结论：
{"结论":{"判定":"满足|未满足|阻塞","内容":"≤160字","证据":["..."]}}
   判定"满足"必须指得出具体证据，指不出来会被降级为"未满足"。
   **分配节点自己没有观测**，所以你的证据只能填两种：
     ・子任务的**任务名**（原样照抄一个）
     ・磁盘上真存在的产物路径
   写"第几次观测"是无效的 —— 观测只属于叶子。
   反复失败、或需要的动作不在工具里（比如开户/入金/留痕需要人到场），
   就用"阻塞"，并把原因写清楚 —— 不要编一个你能做的假版本来代替做不到的事。
"""

LEAF_SYS = """你是一个叶子。判断自由，但动作必须形式化。

形式字段（上层下发，只读，不许改）：
  任务名 ≤20字 ／ 任务详情 ≤240字 ／ 注意事项 ≤120字 ／ 验收标准 ≤140字

只输出一个 JSON，二选一：

1) 做一个动作（唯一能改变世界的东西，一次一个，次数不限）：
{"动作":{"工具":"bash|read|write|need","参数":{...}}}
   · bash:  {"cmd":"..."}         —— 随你写。跑完由**代码**记下它碰了什么。
   · read:  {"path":"..."}
   · write: {"path":"...","content":"..."}
     —— 内容完全自由，**过程中不用填任何形式化的东西**，专心把活干好。
   · need:  {"query":"用 IMAP 读邮箱并落成 JSON"}
     不知道怎么做时先问一次。返回的是以往真实成功过的做法，仅供参考。

2) 出结论（这是唯一需要交付形式的地方）：
{"结论":{"判定":"满足|未满足|阻塞","内容":"≤160字","证据":["第几次观测 / 产物路径"],
          "外部需求":"需要人到场|需要真实账户|需要真实资金|需要现实设备",
          "工件":[{"path":"...","type":"程序|配置|数据|脚本|内部",
                   "name":"干什么用的",
                   "func":"**能直接粘上就执行的一条命令**，如 `bash sum.sh`、`python3 main.py --flag x`；\
不要写句子（写错了会被退回来）",
                   "args":"参数","return":"返回/写出什么","external":[]}]}}

   两条硬性要求（由代码核对，对不上会被退回来重出）：
   ① 判定"满足"必须指得出具体证据（第几次观测 / 产物路径 / 子节点名）。
   ② **你这次产出的每一个代码/配置/数据文件，都要在「工件」里交代**：
      能跑起来的入口给完整契约（type/name/func/args/return，func 必须是一条命令）；
      只给自己用、或只是产出的数据/日志，写 {"path":"...","type":"内部"} 就行。
      （数据文件如果想留个说明，写 type="数据" 也可以。）
   日志/缓存这类副产物不用管。

   反复失败、或需要的动作不在工具里，就用"阻塞"，说清为什么，并指明外部需求是哪一类。
   不要编一个你能做的假版本来代替做不到的事。
"""

# 可变层：自优化唯一被允许修改的东西。
PROMPT = {"alloc": ALLOC_SYS, "leaf": LEAF_SYS}


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
def _clean_spec(spec, trace, parent):
    """规范化字段（压空白），并如实记下超长的。**不切。**

    上限由提示词承诺（20/240/120/140）—— 提示词已经限过的，代码不再偷偷砍。
    超长只是一条事实，记进 trace 供 report 统计。
    """
    out, over = {}, []
    for k_src, k_lbl, k_lim in (("任务名", "name", LIMITS["name"]),
                                ("任务详情", "detail", LIMITS["detail"]),
                                ("注意事项", "notes", LIMITS["notes"]),
                                ("验收标准", "accept", LIMITS["accept"])):
        v, was = norm(spec.get(k_src, ""), k_lim)
        if was:
            over.append(k_src)
        out[k_lbl] = v
    if over:
        trace.add(parent.id, "field_over",
                  {"字段": over, "子任务": out["name"]})
    return out


def _evidence_ok(node, ev):
    """证据必须指得到真实存在的东西：某次观测、某个子节点、或磁盘上真有的产物。

    这是代码替上层做的**第一道**复核。不加它，`判定:满足` 配一句编出来的
    "子任务A 的结论" 就能过 —— 第一次跑就撞到了。

    证据可能是复合串（模型会写 `第1次观测 / add.py`），所以要拆开逐段看。
    分配节点**自己没有观测**，它的证据只能是子任务名或产物路径。
    """
    valid, bad = [], []
    obs_idx = set(range(1, len(node.observations) + 1))
    kids = []
    if node.attempts:
        kids = [c.get("任务名", "") for c in node.attempts[-1].get("下层结论", [])]
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
    verdict, _ = norm(concl.get("判定", ""))
    content, _ = norm(concl.get("内容", ""), LIMITS["conclusion"])
    ev = concl.get("证据") or []
    if isinstance(ev, str):
        ev = [ev]
    ev = [norm(x)[0] for x in ev if str(x).strip()]
    ext = concl.get("外部需求") or []
    if isinstance(ext, str):
        ext = [ext]
    ext = [x for x in (str(x).strip() for x in ext) if x in EXTERNAL_CLASSES]
    artifacts = concl.get("工件")
    if not isinstance(artifacts, list):
        artifacts = []
    if verdict not in ("满足", "未满足", "阻塞"):
        return None, "判定必须是 满足|未满足|阻塞"

    # ① 强制措施，放在这最后一步 —— 过程中完全不打扰它
    unacct = _unaccounted(st, artifacts)
    if unacct:
        trace.add(node.id, "contract_missing", {"没交代的产出": unacct})
        return None, (
            "你这次工作产出了这些文件：%s\n"
            "结论里必须逐个交代它们（放在 \"工件\" 里）：\n"
            "  {\"工件\":[{\"path\":\"a.sh\",\"type\":\"脚本\","
            "\"name\":\"干什么用的\",\"func\":\"怎么跑\","
            "\"args\":\"\",\"return\":\"写什么\"},\n"
            "           {\"path\":\"b.py\",\"type\":\"内部\"}]}\n"
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
        trace.add(node.id, "contract_bad", {"问题": bad_contracts})
        return None, ("这些工件的契约有问题，请修正后重新出结论：\n  - %s\n"
                      "func 要写成**能直接粘上就执行**的一条命令，比如 "
                      "`bash sum.sh` 或 `python3 main.py --flag x`，"
                      "不要写「执行…即可运行」这种句子。"
                      % "\n  - ".join(bad_contracts))

    if verdict == "满足":
        valid, bad = _evidence_ok(node, ev)
        if not valid:
            trace.add(node.id, "verdict_downgraded",
                      {"原判定": "满足", "原因": "证据指不到任何真实存在的东西",
                       "原本写的证据": bad})
            return {"verdict": "未满足", "content": content +
                    "（原判「满足」但证据指不到真实的东西，已降级）",
                    "evidence": [], "external": []}, None
        if bad:
            trace.add(node.id, "evidence_trimmed", {"丢掉": bad, "留下": valid})
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
        trace.add(node.id, "contract", {"path": path, "契约": contract,
                                        "问题": problems, "来源": "结论",
                                        "effects": eff, "前置条件": pre})
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
    """
    import hashlib
    a = json.dumps({"工具": tool, "参数": args}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1((a + "\x00" + str(obs)[:400]).encode()).hexdigest()[:12]


def _do_action(node, act, trace, caps, st):
    """执行一个形式化动作。返回观测文本。动作是唯一能改变世界的东西。"""
    tool = str(act.get("工具", ""))
    args = act.get("参数") or {}
    if not isinstance(args, dict):
        return "参数必须是一个 JSON 对象"
    if tool == "need":
        if caps is None:
            return "能力库不可用"
        picked, text = caps.search(str(args.get("query", "")))
        st["_caps"] = picked
        trace.add(node.id, "cap_need", {"query": str(args.get("query", "")),
                                        "hits": [e["id"] for e in picked],
                                        "chars": len(text)})
        if not text:
            return "没有现成做法。用 bash 自己做；这次做成了，做法会被自动记下来。"
        return ("现成做法（以往真实成功过的，仅供参考，仍要自己跑一遍验证）:\n" + text)
    fn = TOOLS.get(tool)
    if not fn:
        return "没有这个工具：%s（只有 bash / read / write / need）" % tool
    call_args = {k: args[k] for k in ("path", "content", "cmd") if k in args}
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
        return "工具出错: %r" % e

    # 动作之后统一记账：effects 由代码抽，不给模型自报的机会。
    # bash 和 write 共用这一套 —— 它们本来就是同一件事的两个壳。
    eff, pre = effects_of(tool, args, cwd=os.getcwd(), existed_before=existed)
    trace.add(node.id, "effects", {"工具": tool, "effects": eff, "前置条件": pre})
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
    # 无进展检测：同一动作 + 同一观测重复多次 = 再重复不会带来新信息。
    # 实测：一个叶子把同一个文件读了 25 次，光摆着历史它停不下来。
    # 所以把"重复"这个事实显式化（内容信号，不是轮次预算）。
    sig = _sig(tool, args, obs)
    seen = st.setdefault("seen_actions", {})
    seen[sig] = seen.get(sig, 0) + 1
    if seen[sig] >= 3:
        note += ("\n[停止] 这个动作你已经做过 %d 次，观测**完全一样** —— "
                 "再重复不会带来新信息。换一个动作，或者出结论"
                 "（阻塞就写清为什么）。" % seen[sig])
        trace.add(node.id, "no_progress",
                  {"重复次数": seen[sig], "动作": str(tool)})
        if seen[sig] >= 5:
            st["stalled"] = ("同一动作重复 %d 次、观测完全一样，没有新信息"
                             % seen[sig])
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
        if node.kind == "leaf":
            node.observations.append({"动作": "(非法输出)", "观测": d["_bad"]})
        else:
            node.attempts.append({"分配": [], "被拒": d["_bad"]})
        trace.add(node.id, "bad_output", d["_bad"])
        return {"kind": "again"}

    # ── 先例：分配节点的一个"读"动作。懒加载，只在它想看时才检索。 ──
    prec = d.get("先例")
    if isinstance(prec, dict) and node.kind != "leaf":
        qs = prec.get("查询") or prec.get("queries") or []
        if isinstance(qs, str):
            qs = [qs]
        qs = [str(q) for q in qs if str(q).strip()]
        idx = ctx.get("index")
        if idx is None:
            node.precedents.append("（这次没有可检索的老树）")
            trace.add(node.id, "precedent", {"查询": qs, "命中": [], "chars": 0})
        else:
            picked, text = idx.search(qs)
            trace.add(node.id, "precedent",
                      {"查询": qs, "命中": [p.id for p in picked],
                       "chars": len(text)})
            node.precedents.append(text or "（没有找到类似的先例）")
        return {"kind": "again"}

    concl = d.get("结论")
    if isinstance(concl, dict):
        got, err = _clean_conclusion(concl, trace, node, st)
        if err:
            if node.kind == "leaf":
                node.observations.append({"动作": "(结论不合规)", "观测": err})
            else:
                node.attempts.append({"分配": [], "被拒": err})
            trace.add(node.id, "bad_conclusion", err)
            return {"kind": "again"}
        node.close(got["verdict"], got["content"], got["evidence"], got["external"])
        trace.add(node.id, "concluded",
                  {"判定": got["verdict"], "内容": got["content"],
                   "证据": got["evidence"], "外部需求": got["external"]})
        return {"kind": "finished"}

    if node.kind == "leaf":
        act = d.get("动作")
        if not isinstance(act, dict):
            node.observations.append({"动作": "(无法识别)", "观测": str(d)})
            return {"kind": "again"}
        obs = _do_action(node, act, trace, caps, st)
        label = "%s %s" % (act.get("工具", ""),
                           json.dumps(act.get("参数") or {}, ensure_ascii=False))
        node.observations.append({"动作": label, "观测": obs})
        st["calls"].append((act.get("工具"), act.get("参数") or {}, obs))
        # 存结构化参数：挖掘器要能直接读，不该去反解一个拼出来的字符串
        trace.add(node.id, "action", {"工具": act.get("工具"),
                                      "参数": act.get("参数") or {},
                                      "观测": obs})
        stalled = st.pop("stalled", None)
        if stalled:
            trace.add(node.id, "stalled", stalled)
            node.close("未满足", stalled, [])
            return {"kind": "finished"}
        return {"kind": "again"}

    # ── 分配节点：再做一次分配 ──
    specs = d.get("再做一次")
    if not isinstance(specs, list) or not specs:
        node.attempts.append({"分配": [], "被拒": "「再做一次」必须是非空数组"})
        return {"kind": "again"}

    kids_spec, reject = [], None
    for raw in specs:                         # 不砍：拆几个是模型的决定
        s = _clean_spec(raw if isinstance(raw, dict) else {}, trace, node)
        s["kind"] = "leaf" if raw.get("类型") == "叶子" else "dispatch"
        s["gate"] = bool(raw.get("门槛"))
        # ② 子任务的验收标准必须携带父/根的可测物理量
        ra = ctx["root_anchors"]
        ok_parent = inherits(node.accept, s["accept"])
        ok_root = (not ra) or any(x in s["accept"] for x in ra)
        if not (ok_parent and ok_root):
            reject = ("子任务的验收标准丢了可测物理量（缺 %s）—— 这是把任务换成了别的东西"
                      % ", ".join(sorted(ra or anchors(node.accept))))
            trace.add(node.id, "criterion_drift",
                      {"子任务": s["name"], "验收标准": s["accept"],
                       "父锚点": sorted(anchors(node.accept)), "根锚点": sorted(ra)})
            break
        if not s["name"] or not s["accept"]:
            reject = "子任务必须有 任务名 和 验收标准"
            break
        kids_spec.append(s)

    if reject:
        # 把被拒这件事变成一条可见的事实（而不是丢弃或加计数器）
        node.attempts.append({"分配": kids_spec, "被拒": reject})
        return {"kind": "again"}

    gates = [s for s in kids_spec if s["gate"]]
    if len(gates) > 1:
        node.attempts.append({"分配": kids_spec, "被拒": "一次分配最多一个门槛"})
        return {"kind": "again"}
    gate = gates[0] if gates else None
    if gate:
        first = [gate]
        rest = [s for s in kids_spec if s is not gate]
    else:
        first, rest = kids_spec, []          # 没有门槛就没有“暂缓”，不能把全部当成暂缓

    if not budget.take_nodes(len(kids_spec)):
        node.attempts.append({"分配": kids_spec, "被拒": "节点预算不足"})
        return {"kind": "again"}
    node.attempts.append({"分配": kids_spec, "下层结论": [], "结局": "等下层"})
    trace.add(node.id, "allocated",
              {"第几次": len(node.attempts), "门槛": gate["name"] if gate else None,
               "暂缓": [s["name"] for s in rest] if gate else []})
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
            "任务名": node.name, "任务详情": node.detail, "注意事项": node.notes,
            "验收标准": node.accept, "类型": node.kind, "门槛": node.gate,
            "深度": node.depth, "parent": node.parent,
            "工作目录": os.path.abspath(os.getcwd())})
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
                    pn.attempts[-1].setdefault("下层结论", []).append(node.record())
                # 门槛不成立 → 整个分支作废，其余子任务永不启动
                if pst.get("gate_id") == nid and node.verdict != "满足":
                    skipped = [s["name"] for s in pst.get("rest") or []]
                    pst["rest"], pst["gate_id"] = [], None
                    if pn.attempts:
                        pn.attempts[-1]["结局"] = "门槛不成立（%s）: %s" % (
                            node.name, node.conclusion)
                        if skipped:
                            pn.attempts[-1]["下层结论"].append(
                                {"任务名": "（以下子任务被跳过）", "结局": "未启动",
                                 "内容": ", ".join(skipped), "证据": []})
                    trace.add(parent, "gate_failed",
                              {"门槛": node.name, "原因": node.conclusion,
                               "被跳过的子任务": skipped})
                    if not pst["finished"]:
                        pst["ready"] = True
                        pending.append(parent)
                    return
                pst["waiting"] -= 1
                if pst["waiting"] <= 0 and not pst["finished"]:
                    if pn.attempts:
                        pn.attempts[-1]["结局"] = "下层已全部返回"
                    if pst.get("rest"):
                        rest, pst["rest"], pst["gate_id"] = pst["rest"], [], None
                        trace.add(parent, "gate_passed",
                                  {"已启动": [s["name"] for s in rest]})
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
                             parent=parent.id, depth=parent.depth + 1))
        parent.children += [k.id for k in kids]
        return kids

    ctx = {"state": state, "llm": llm, "trace": trace, "budget": budget,
           "root_anchors": anchors(root.accept), "caps": caps, "index": index}

    # 根节点：自动检索一次先例。检索不花 LLM 调用，只有根付一次性封顶注入。
    # 不交给模型判断 —— 实测它会觉得"这么小的活不用查"，而真正贵的
    # 恰恰是大事（一个大任务里 40% 的算力花在一个本来就不该开工的分支上）。
    # 子孙节点仍然是选填的（它们自己调「先例」动作），因为它们的查询不一样。
    if index is not None:
        try:
            picked, text = index.search(["%s %s" % (root.name, root.accept)])
            if text:
                root.precedents.append(text)
                trace.add(root.id, "precedent", {"查询": [root.name], "自动": True,
                                                 "命中": [p.id for p in picked],
                                                 "chars": len(text)})
        except Exception as ex:
            trace.add(root.id, "precedent_failed", "%r" % ex)

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
