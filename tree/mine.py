"""能力提取：从真实执行过的命令里长出 cap。机械提取，不让模型自报。

为什么不让模型自报：昨晚它把 69% 的节点标成"有证据"绕过了约束。
同一类错在这里就是"我学会了 X" —— 于是库里塞满不存在的能力。
所以 cap 只从**真实执行过、且所属节点最终完工**的命令里长出来。

这个模块被两处用：
  - run.py 在线增量：节点一完工就学（回路闭合，同一次运行内的后续节点就能复用）
  - mine.py 离线批量：崩溃/被 kill 之后补挖
"""

import json
import os
import re

from .effects import effects_of, is_runnable

ABS_RE = re.compile(r"(?<![\w.\-:/])/(?!dev/(?:null|stdout|stderr))[\w.\-]+(?:/[\w.\-]+)*")
PATHWORD_RE = re.compile(r"/([A-Za-z_][A-Za-z0-9_.\-]*)")  # 任何路径片段，包括 /Users 这种单段
CD_ABS_RE = re.compile(r"^\s*cd\s+(/\S+)\s*&&\s*")
CD_RE = re.compile(r"^cd\s+\S+\s*&&\s*")
INSTALL_RE = re.compile(r"\b(?:pip3?|npm|apt-get|brew)\s+install\b")
MKDIR_RE = re.compile(r"\bmkdir\b|\bchmod\b|\btouch\b|\bln\s+-s\b|\bgit\s+clone\b")
RUN_RE = re.compile(r"\b(?:python3?|node|bash)\s+[^\s|;&]+\.[a-z]{2,4}\b")
VENV_RE = re.compile(r"-m\s+venv\b")
HEREDOC_RE = re.compile(r"<<\s*['\"]?(\w+)")
ART_RE = re.compile(r"(?:cat\s*>\s*|>>?\s*)([A-Za-z0-9_][A-Za-z0-9_./\-]*)"
                    r"|mkdir\s+(?:-p\s+)?([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
# `bash sum.sh` 里的 sum.sh 是**参数**，不是重定向目标。
# 不把它算成产物，就会漏掉"这个工件已经被跑过了"这件事。
SCRIPT_REF_RE = re.compile(
    r"\b(?:python3?|node|bash|sh|ruby)\s+([A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z]{1,4})")
SCRIPT_EXT = (".py", ".js", ".sh", ".ts", ".rb")

# shell 内建/工具名不是能力关键词
NOISE = {"python", "python3", "node", "bash", "sh", "echo", "cat", "print", "true",
         "false", "test", "bin", "usr", "local", "stdout", "stderr", "dev", "null",
         "tmp", "import", "from", "def", "return", "with", "for", "not", "none",
         "self", "json", "csv", "path", "file", "and", "the", "sleep", "head",
         "tail", "grep", "find", "nohup", "lsof", "curl", "wget", "chmod", "mkdir",
         "touch", "cd", "ls", "pwd", "exit", "eof", "quiet", "include", "version",
         "venv", "pip", "pip3", "install", "source", "export", "kill", "ps", "wc"}
RUNNERS = {"py": "python3", "js": "node", "sh": "bash", "ts": "node", "rb": "ruby"}


def strip_paths(cmd):
    return ABS_RE.sub(" <path> ", cmd or "")


def write_targets(cmd):
    """真正的写文件目标。`2>/dev/null`、`>&1` 不算。"""
    out = []
    for m in re.finditer(r">>?\s*([A-Za-z0-9_&./\-]+)", cmd or ""):
        t = m.group(1)
        if t.startswith("/dev/") or t.startswith("&"):
            continue
        out.append(t)
    return out


def normalize(cmd):
    """叶子本来就在项目目录里跑，所以 `cd /abs && ` 前缀是噪声，而且不可移植。
    剥掉它，cwd 单独记；其余绝对路径换成 <path>。"""
    cwd = None
    m = CD_ABS_RE.match(cmd or "")
    if m:
        cwd = m.group(1).rstrip("/")
        cmd = cmd[m.end():]
    return ABS_RE.sub("<path>", cmd or "").strip(), cwd


def portable_artifacts(raw):
    """产物一律用可移植形式：绝对路径取 basename。"""
    out = []
    for a in artifacts_of(raw):
        p = os.path.basename(a) if a.startswith("/") else a
        if p and p not in out and "<path>" not in p:
            out.append(p)
    return out


def productive(cmd, raw=None):
    """注意：只往 /tmp 写的环境探测不算能力（那是在摸机器，不是在做事）。
    第一版把 `find /Users ... > /tmp/all_pdfs.txt` 挖了进来。

    但**内联脚本算能力**：`python3 <<EOF ... EOF` 没有产物文件、没有安装，
    它却实实在在地做了一件事 —— 这是第一版漏掉的一整类。
    """
    if not cmd or len(cmd) < 8:
        return False
    if extract_heredoc(cmd):
        return True
    if any(not t.startswith(("/", "~")) for t in write_targets(raw or cmd)):
        return True
    return bool(INSTALL_RE.search(cmd) or MKDIR_RE.search(cmd)
                or RUN_RE.search(cmd) or VENV_RE.search(cmd))


def artifacts_of(cmd):
    out = []
    for a, b in ART_RE.findall(cmd or ""):
        p = (a or b).strip()
        if p and p not in out and not p.startswith("/dev/") and not p.startswith("&"):
            out.append(p)
    for m in SCRIPT_REF_RE.findall(cmd or ""):
        if m not in out:
            out.append(m)
    for t in write_targets(cmd):
        if t not in out:
            out.append(t)
    return out


def strip_literals(cmd):
    """把引号里的字面量拿掉 —— 那是**数据**，不是命令。

    只用于"扫词"那一步；pip/import/脚本名这些有意义的提取不走这里，
    否则 `pip install "requests"` 会把包名一起丢掉。
    """
    s = re.sub(r"'[^']*'", " ", cmd or "")
    return re.sub(r'"[^"]*"', " ", s)


def keys_of(recipe, arts, body=""):
    """键描述的是**配方**，不是原始命令。

    两个错都是真实数据打出来的：
      - 扫原始 heredoc 会把脚本内容和 cwd 吸进来（`users, night_quant, mycode`）
      - `/Users` 这种单段路径参数 ABS_RE 抳不到，得单独排
    但 heredoc 正文里的 **import 例外**：那是最可靠的能力信号，
    而且它就在正文里（`list_emails.py` 的 imaplib 只能在正文找到）。
    """
    c = strip_paths(recipe or "")
    paths = {w.lower() for w in PATHWORD_RE.findall(recipe or "")}
    paths |= {w.lower() for w in PATHWORD_RE.findall(body or "")}
    ks = []

    def add(x):
        x = x.lower().strip("./*'\"")
        if (len(x) >= 3 and x not in NOISE and x not in paths
                and "__" not in x and not x.isdigit() and x not in ks):
            ks.append(x)

    for a in arts:
        b = os.path.basename(a)
        if b.endswith(SCRIPT_EXT):
            add(os.path.splitext(b)[0])       # 脚本名最强，排最前，不能被 import 挤掉
    for m in re.findall(r"\b(?:import|from)\s+([\w.]+)", body or ""):
        add(m.split(".")[0])              # 正文里的 import 次之
    for m in re.findall(r"\b(?:pip3?|npm)\s+install\s+(?:-q\s+|--quiet\s+)*([\w\-.]+)", c):
        add(m)
    for m in re.findall(r"\bimport\s+([\w.]+)", c):
        add(m.split(".")[0])
    # 扫词前**先拿掉引号里的字面量** —— 那是数据，不是命令。
    # 实测：`printf 'Account Holder: WXLONG\n...' > evidence.txt` 把写进文件
    # 的内容（bank / account / wxlong）当成了能力键。原来靠 cmd[:240] 截断
    # 遮住了，截断一去掉就露出来了。
    for m in re.findall(r"[A-Za-z_][A-Za-z0-9_\-]{2,}", strip_literals(c)):
        add(m)
    return ks


RUNNER_RE = re.compile(r"(?:[\w./\-]*(?:python3?|bash|node|sh|ruby))")
HEREDOC_LINE_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
TARGET_RE = re.compile(r"(?:cat\s*>\s*|>>?\s*)([A-Za-z0-9_][A-Za-z0-9_./\-]*)")


RUNNER_EXT = {"python": ".py", "python3": ".py", "node": ".js",
              "bash": ".sh", "sh": ".sh", "ruby": ".rb"}
EXT_RUNNER = {".py": "python3", ".js": "node", ".sh": "bash",
              ".rb": "ruby", ".ts": "node"}


def extract_heredoc(cmd):
    """把 `... << 'EOF' \n 正文 \n EOF` 拆开。

    heredoc 正文**完整存在 trace 的 args 里**（只有 obs 被截断），
    所以内联脚本也能机械提取 —— 不用加提示词，不用让模型配合。

    三种情形：
      pip install X && python <<EOF    → pre 保留，runner 照用
      python3 <<EOF                     → 无 pre，无产物，仍然算一条能力
      cat > x.py <<EOF                  → 落盘副本取代内联写入，按后缀推 runner
    返回 {pre, runner, ext, body, target} 或 None。
    """
    lines = (cmd or "").split("\n")
    for i, ln in enumerate(lines):
        m = HEREDOC_LINE_RE.search(ln)
        if not m:
            continue
        tag = m.group(1)
        end = next((k for k in range(i + 1, len(lines)) if lines[k].strip() == tag), None)
        if end is None:
            continue
        body = "\n".join(lines[i + 1:end])
        if not body.strip():
            continue
        head = lines[i][:m.start()]
        t = TARGET_RE.search(head)
        target = t.group(1) if t else None
        if target:
            ext = os.path.splitext(target)[1].lower()
            if ext not in EXT_RUNNER:       # 写的是数据文件（json/txt），不是脚本
                continue
            runner, pre = EXT_RUNNER[ext], ""
        else:
            r = RUNNER_RE.search(head)
            if not r:                       # 既不知写给谁，也不知用什么跑
                continue
            runner = r.group(0).rstrip("-").strip()
            ext = RUNNER_EXT.get(os.path.basename(runner))
            if not ext:
                continue
            pre = re.sub(r"\s*(?:&&|\|\||;)?\s*$", "",
                         head[:r.start()].strip()).strip()
        return {"pre": pre, "runner": runner, "ext": ext,
                "body": body, "target": target}
    return None


def mine_one(cmd, arts):
    """把一条成功命令压成一条短的可复现配方。
    内联 heredoc 的替换在 caps_from_node 里做（那里才知道正文要落哪）。"""
    how = {"cmd": cmd, "artifacts": arts}
    hd = extract_heredoc(cmd)
    if hd:
        how["note"] = ("由 heredoc 写入 %s" % hd["target"]) if hd["target"] \
            else "本体是内联脚本，已落盘到能力库"
    elif HEREDOC_RE.search(cmd):
        script = next((a for a in arts if a.endswith(SCRIPT_EXT)), None)
        if script:
            how["cmd"] = "%s %s" % (RUNNERS[script.rsplit(".", 1)[1]], script)
    return how


def dedupe_key(cmd):
    c = strip_paths(cmd)
    c = CD_RE.sub("", c)
    c = re.sub(r"\s+", " ", c).strip()
    return re.sub(r"\s*[;&|]+\s*$", "", c)


def caps_from_node(nid, task, calls, trace_name, contracts=None, skipped=None):
    """从**单个节点**的成功执行里长出能力。在线增量和离线批量共用它。

    `contracts`：结论里交代的工件（模型写的那一半）。它是**规范能力**的来源 ——
    一个工件一条能力，不管文件是 write 还是 bash 造出来的。
    声明 type="内部" 的不进库。

    `skipped`：可选列表，装"看着像能力但不收"的东西和**理由**。
    不收要说得出来，不悄悄丢。
    """
    by_path = {}
    for c in (contracts or []):
        p = str(c.get("path") or "")
        if p:
            by_path[os.path.basename(p)] = c

    out, seen, bodies = [], set(), {}
    for tool, args, obs in calls:
        if tool != "bash":
            continue
        raw = args.get("cmd")
        if not raw:
            continue
        cmd, cwd = normalize(raw)
        if not productive(cmd, raw):
            if skipped is not None:
                skipped.append({"理由": "只是摸机器（往 /tmp 写、没做事），不算能力",
                                "cmd": cmd})
            continue
        if "工具出错" in obs or ("[exit=" in obs and "[exit=0]" not in obs):
            continue
        arts = portable_artifacts(raw)
        hd = extract_heredoc(cmd)
        rec = mine_one(cmd, arts)
        if cwd:
            rec["cwd"] = cwd
        entry_body = None
        if hd:
            entry_body = {"text": hd["body"], "ext": hd["ext"], "target": hd["target"]}
            if hd["target"]:
                bodies[os.path.basename(hd["target"])] = entry_body
            rec["cmd"] = ((hd["pre"] + " && ") if hd["pre"] else "") + \
                "%s __SCRIPT__" % hd["runner"]
            rec["artifacts"] = ([hd["target"]] if hd["target"] else []) + \
                [a for a in arts if a != hd["target"]]
        # （原来这里有一条 `elif rec["cmd"] == cmd[:240]: continue`，
        #   借"命令被截断"这个信号跳过不可复现的长配方。
        #   截断删了，信号也就没了 —— 换成下面这条明说的判据。）
        scripts = [a for a in rec["artifacts"] if a.endswith(SCRIPT_EXT)]
        # 一条"配方"必须是能**直接照做**的东西。多行又没落成脚本的不算 ——
        # 你没法"粘上就执行"（实测：一个 57 行的 HTML heredoc 被收了进来，
        # 而且路径被换成 <path> 之后 HTML 本身已经坏了）。
        # 不收就**记下理由**，不悄悄丢。
        if "\n" in rec["cmd"] and not hd and not scripts:
            if skipped is not None:
                skipped.append({"理由": "多行且没落成脚本，不能直接照做",
                                "cmd": rec["cmd"]})
            continue
        # 已经有契约的工件：规范能力由契约那条出，这条只是"跑它"，不记第二条
        if any(s in by_path for s in scripts):
            continue
        key = dedupe_key(rec["cmd"]) + "|" + ",".join(sorted(scripts))
        if key in seen:
            continue
        seen.add(key)
        ks = keys_of(rec["cmd"], rec["artifacts"], (hd or {}).get("body", raw))
        does = ("跑 %s" % ", ".join(os.path.basename(s) for s in scripts)) \
            if scripts else ("执行 %s" % " ".join(ks))
        localish = (bool(scripts) and not hd) or ".venv" in cmd or \
            cmd.startswith("./") or "<path>" in cmd
        eff, pre = effects_of(tool, args, cwd=cwd)
        out.append({
            "does": does, "keys": ks, "how": rec, "body": entry_body,
            "scope": "project" if localish else "general",
            "seen_in": ABS_RE.sub("", task or ""),
            "effects": eff, "前置条件": pre,
            "evidence": {"node": nid, "trace": trace_name, "obs": obs},
        })

    # ── 契约：一个工件一条规范能力（不管它是 write 还是 bash 造出来的）
    for c in (contracts or []):
        path = str(c.get("path") or "")
        base = os.path.basename(path)
        contract = c.get("契约") or {}
        if not base or base in seen:
            continue
        if not contract or contract.get("type") == "内部":
            continue                      # 只给自己用的文件不进库
        if not is_runnable(contract):
            # 数据/配置这类产出不是能力：要它就跑生成它的那个东西。
            continue
        seen.add(base)
        eff, pre = effects_of("write", {"path": path}, cwd=None)
        entry = {
            "does": contract.get("name") or ("跑 %s" % base),
            "keys": keys_of(contract.get("func", ""), [base], ""),
            "how": {"cmd": contract.get("func", ""), "artifacts": [base],
                    "func": contract.get("func", "")},
            "scope": "project",
            # 中文桥：契约里的用途优先 —— 那是当初为什么写它
            "seen_in": ABS_RE.sub("", ((contract.get("name") or "") + " "
                                       + (task or ""))),
            "契约": contract,
            "effects": c.get("effects") or eff,
            "前置条件": c.get("前置条件") or pre,
            "evidence": {"node": nid, "trace": trace_name, "obs": ""},
        }
        body = bodies.get(base)
        if body:
            # 正文落盘到能力库，配方指向它 —— 自包含，不依赖项目目录
            entry["body"] = body
            runner = {"py": "python3", "js": "node", "sh": "bash",
                      "rb": "ruby"}.get(body["ext"].lstrip("."), "bash")
            entry["how"]["cmd"] = "%s __SCRIPT__" % runner
        out.append(entry)
    return out


def mine_trace(trace_path):
    """离线：扫整份 trace。

    trace 是历史数据，格式变过两次：形式化之前用 done/leaf_tool，
    之后用 concluded/action。两种都要能读，否则旧的那 14MB 就变成死数据了。
    """
    status, tools, tasks, contracts = {}, {}, {}, {}
    for line in open(trace_path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        k, p, nid = r["kind"], r["payload"], r["node"]
        if k == "open":
            tasks[nid] = p.get("任务名") or p.get("task") or ""
        elif k in ("concluded", "done"):
            status[nid] = "done"
        elif k in ("crashed", "budget_exhausted", "failed") and nid not in status:
            status[nid] = "failed"
        elif k == "leaf_tool":                       # 旧格式
            tools.setdefault(nid, []).append(
                (p.get("tool"), p.get("args") or {}, str(p.get("obs", ""))))
        elif k == "action" and p.get("工具"):         # 新格式
            tools.setdefault(nid, []).append(
                (p.get("工具"), p.get("参数") or {}, str(p.get("观测", ""))))
        elif k == "contract" and p.get("path"):       # write 出来的工件契约
            contracts.setdefault(nid, []).append(
                {"path": p["path"], "契约": p.get("契约") or {},
                 "effects": p.get("effects"), "前置条件": p.get("前置条件")})

    found, out = set(), []
    for nid, calls in tools.items():
        if status.get(nid) != "done":
            continue
        for e in caps_from_node(nid, tasks.get(nid, ""), calls,
                                os.path.basename(trace_path),
                                contracts.get(nid)):
            k = e["how"]["cmd"] + "|" + ",".join(e["keys"])
            if k in found:
                continue
            found.add(k)
            out.append(e)
    return out
