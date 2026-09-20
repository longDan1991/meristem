"""从动作里机械抽 effects，并核对/落盘工件契约。能测的就不许模型自报。

bash 和 write 是同一件事的两个壳：`echo hi > a.txt` 就是 write("a.txt","hi")。
所以这里一套抽取同时服务两者 —— 因为复用者只关心"碰了什么"，
不关心命令长什么样。

`前置条件` 和 effects 一样重要：复用失败最常见的原因不是配方错，
而是前提不成立（没网、包没装、不在那个目录）。没有这一项，
一次冤枉的失败会把一条好配方记成"烂了"。

**契约**也归这里：`func` 是不是一条能直接跑的命令、入口在不在、
`.meta.json` 怎么写。它和 effects 共享同一个变因 —— "工件被怎样描述"。
"""

import json
import os
import re

from .protocol.fields import EXTERNAL_CLASSES

URL_RE = re.compile(r"\b(?:https?|ftp)://([\w.\-]+)(?::(\d+))?")
REDIR_RE = re.compile(r"(>>?)\s*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
READ_RE = re.compile(r"<\s*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
MKDIR_RE = re.compile(r"\bmkdir\s+(?:-p\s+)?([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
TOUCH_RE = re.compile(r"\btouch\s+([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
RM_RE = re.compile(r"\brm\s+(?:-\w+\s+)*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
PKG_RE = re.compile(r"\b(?:pip3?|npm|apt-get|brew)\s+install\s+(?:-[\w-]+\s+)*([\w\-.]+)")
NOHUP_RE = re.compile(r"\bnohup\b")
TAILBG_RE = re.compile(r"&\s*$")

# 哪些产出物必须给契约（要么给契约，要么明确声明它属于内部）。
# 日志/缓存这类副产物不在里面。
ARTIFACT_EXT = (".py", ".sh", ".js", ".ts", ".rb", ".json",
                ".yaml", ".yml", ".toml", ".csv", ".sql")


def _abs(p, cwd):
    if not p or p.startswith("/dev/") or p.startswith("&"):
        return None
    if p.startswith("/") or not cwd:
        return p
    return os.path.normpath(os.path.join(cwd, p))


def effects_of(tool, args, cwd=None, existed_before=None):
    """返回 (effects, 前置条件)。

    existed_before：write 必须传。effects_of 是在动作**之后**跑的，
    那时文件已经存在了，不传的话 create 永远会被记成 modify。
    """
    fs = {"create": [], "modify": [], "delete": []}
    pkg, proc, net, data = [], [], [], []

    def add(lst, x):
        if x and x not in lst:
            lst.append(x)

    if tool == "read":
        add(data, _abs(args.get("path"), cwd))
    elif tool == "write":
        p = _abs(args.get("path"), cwd)
        if p:
            add(fs["modify" if existed_before else "create"], p)
    else:
        cmd = str(args.get("cmd") or "")
        for op, target in REDIR_RE.findall(cmd):
            p = _abs(target, cwd)
            if p:
                add(fs["create" if op == ">" else "modify"], p)
        for m in MKDIR_RE.findall(cmd):
            add(fs["create"], _abs(m, cwd))
        for m in TOUCH_RE.findall(cmd):
            add(fs["create"], _abs(m, cwd))
        for m in RM_RE.findall(cmd):
            add(fs["delete"], _abs(m, cwd))
        for m in PKG_RE.findall(cmd):
            add(pkg, m)
        if NOHUP_RE.search(cmd) or TAILBG_RE.search(cmd.strip()):
            add(proc, cmd.strip())
        for host, port in URL_RE.findall(cmd):
            add(net, host + (":" + port if port else ""))
        for m in READ_RE.findall(cmd):
            add(data, _abs(m, cwd))

    pre = {}
    if pkg or net:
        pre["需要网络"] = True
    if pkg:
        pre["需要包已安装"] = list(pkg)
    touched = fs["create"] + fs["modify"] + fs["delete"]
    if any(not str(x).startswith("/") for x in touched) or data:
        pre["依赖当前目录"] = os.path.abspath(cwd or ".")
    return ({"fs": fs, "pkg": pkg, "proc": proc, "net": net, "data": data,
             "cwd": os.path.abspath(cwd) if cwd else None}, pre)


CONTRACT_KEYS = ("type", "name", "func", "args", "params", "return",
                 "external")

# params 是**可调用**那一半：`func` 里的 `__名字__` 就是占位符，params 说它是什么类型。
# 没有 params 的仍是一条能直接粘上就跑的命令。
PARAM_TYPES = ("int", "str", "float", "bool")
PLACEHOLDER_RE = re.compile(r"__([A-Za-z_][A-Za-z0-9_]*)__")


def placeholders(func):
    return PLACEHOLDER_RE.findall(str(func or ""))


def param_problems(contract):
    """params 与 func 里的 `__x__` 占位符必须一一对上。对不上就是一条**错签名**，
    而错签名比没有签名更坏：盒子会把模型引到一条走不通的路上。"""
    func = str(contract.get("func") or "")
    params = contract.get("params") or {}
    slots = placeholders(func)
    if not isinstance(params, dict):
        return ["params 必须是一个对象，如 {\"epochs\":{\"type\":\"int\",\"default\":50}}"]
    bad = []
    for k, spec in params.items():
        if k not in slots:
            bad.append("params 里的 %s 在 func 里没有 __%s__ 占位符" % (k, k))
        if not isinstance(spec, dict):
            bad.append("params.%s 必须是对象（type/default/required）" % k)
            continue
        t = spec.get("type")
        if t not in PARAM_TYPES:
            bad.append("params.%s.type 必须是 %s（收到 %r）"
                       % (k, "/".join(PARAM_TYPES), t))
    for s in slots:
        if s not in params:
            bad.append("func 里的 __%s__ 没在 params 里说它是什么" % s)
    return bad

# func 必须是一条**能直接粘上就执行**的命令，不是一句描述。
# 实测模型会写"执行 bash sum.sh 即可运行，将结果写入 sum.txt"——那是给人看的，
# 不是给复用者用的。
# 允许开头的 `cd <dir> &&`：它就是一条能直接跑的命令，
# 拦掉它会让 `cd sub && python3 x.py` 被冤枉成"不是命令"。
RUNNABLE_RE = re.compile(
    r"^\s*(?:cd\s+\S+\s*(?:&&|;)\s*)?(?:sudo\s+)?"
    r"(?:python3?|node|bash|sh|zsh|ruby|perl|curl|wget|make|"
    r"docker|npm|npx|pip3?|uv|poetry|go|cargo|java)\b|^\s*\./|^\s*/|^\s*\$\s+")
# type 属于这几类的，func 必须是一条命令
RUNNABLE_TYPES = ("程序", "脚本", "工具", "服务", "命令", "库", "模块", "cli", "CLI")

# func 里引用到的文件：**开头那个 / 必须收进来**。之前的写法把绝对路径的
# 前导 / 丢了，于是 /a/b/hello.py 被当成相对路径去 cwd 里找，永远找不到 ——
# 实测连续 5 轮报"入口不存在"，白烧 5 万 token。
FILE_REF_RE = re.compile(r"/?[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z]{1,4}")
URL_IN_FUNC_RE = re.compile(r"\b(?:https?|ftp)://\S+")
CD_RE = re.compile(r"^\s*cd\s+(\S+?)\s*(?:&&|;|$)")


def is_runnable(contract):
    """能不能被复用者直接跑起来。只有这种工件才算一条能力。"""
    return bool(RUNNABLE_RE.match(str((contract or {}).get("func") or "")))


def contract_of(args):
    """从 write 的参数里取出模型填的契约（它才知道的那一半）。"""
    c = {}
    for k in CONTRACT_KEYS:
        v = args.get(k)
        if isinstance(v, list):
            v = [str(x) for x in v if str(x).strip()]
        elif isinstance(v, dict):
            v = {str(a): b for a, b in v.items() if b is not None}
        else:
            v = str(v or "").strip()
        if v:
            c[k] = v
    return c


def contract_problems(path, contract, base=None):
    """能机械核对的那部分。不自动跑它（跑会带来副作用），
    只核对它声称的入口真的存在、func 是不是一条能跑的命令、该填的填了。

    base：相对路径（含 `cd sub`）按它解析。默认进程 cwd —— 就是工作区。
    """
    base = base or os.getcwd()
    root = base          # 工件本体和 path 永远按工作区算，不跟着 func 里的 cd 走
    problems = []
    ctype = contract.get("type", "")
    internal = ctype == "内部"
    if not internal:
        if not contract.get("func"):
            problems.append("type 不是内部，但没写 func（别人怎么调用它）")
        if not contract.get("name"):
            problems.append("没写 name（这东西是干什么用的）")
        problems += param_problems(contract)
        if ctype in RUNNABLE_TYPES and not is_runnable(contract):
            problems.append(
                "type 是「%s」，但 func 不是一条能直接执行的命令"
                "（要以 python3 / bash / ./ 之类开头）：%r"
                % (ctype, str(contract.get("func"))))
    func = str(contract.get("func") or "")
    cd = CD_RE.match(func)
    if cd:
        here = os.path.join(base, cd.group(1))
        if not os.path.isdir(here):
            problems.append("func 里的 cd 目录不存在: %s" % cd.group(1))
        else:
            base = here          # func 里的相对路径是按 cd 后的目录算的
    # URL 里的 host/path 不是文件，别拿它们去做存在性检查
    scanned = URL_IN_FUNC_RE.sub(" ", func)
    for ref in FILE_REF_RE.findall(scanned):
        if not os.path.exists(ref if ref.startswith("/")
                              else os.path.join(base, ref)):
            problems.append("func 里引用的入口不存在: %s" % ref)
    bad = [x for x in (contract.get("external") or [])
           if x not in EXTERNAL_CLASSES]
    if bad:
        problems.append("external 只认这几类: %s（收到 %s）"
                        % (" / ".join(EXTERNAL_CLASSES), bad))
    if path and not os.path.exists(path if path.startswith("/")
                                  else os.path.join(root, path)):
        problems.append("path 指向的文件不存在: %s" % path)
    return problems


# 产出记账：**只认这个节点自己报过的路径**，不去 diff 整个工作区。
#
# 为什么不用全局 diff：工作区是共享的、节点是并发的 —— 全局 diff 会把别的
# 节点此刻写的文件算到它头上，于是 gate 反过来逼它交代一个不是它做的文件
# （假阳性比漏报坏得多：漏报就是现状，假阳性会让它卡在这里或者编个契约）。
# 候选只有两个来源，都是**这个节点自己做过的事**：
#   · 它的代码里 open()/os.open() 写过的（子进程自己报上来，见 sandbox.BOOTSTRAP）
#   · 它真跑过的命令（走协议回调宿主的那几次）里解析出来的目标
# 然后逐个 stat，和“跑之前的快照”对比，分 create / modify。
SKIP_DIRS = ("__pycache__", ".git", ".venv", ".tree")
SKIP_SUFFIX = (".meta.json",)


def snapshot_workspace(root, skip=()):
    """{绝对路径: (mtime_ns, 大小)}。只走一遍，不读文件内容。

    它在一次动作**之前**跑，用来回答两个问题：这个路径原来存不存在（create vs
    modify）、它变没变。skip：程序自己的账本（trace），它每回合都在改。
    """
    skip = {os.path.realpath(p) for p in skip if p}
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(SKIP_SUFFIX):
                continue
            p = os.path.join(dirpath, name)
            if os.path.realpath(p) in skip:
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue          # 跑的过程中被删掉的临时文件
            snap[p] = (st.st_mtime_ns, st.st_size)
    return snap


def classify_paths(candidates, before, cwd):
    """候选产出 → (created, modified)。相对路径按 cwd 算，已写盘的才算。"""
    created, modified = [], []
    for raw in candidates:
        p = str(raw)
        ap = os.path.normpath(p if p.startswith("/") else os.path.join(cwd, p))
        try:
            st = os.stat(ap)
        except OSError:
            continue              # 说写了但真没写（被删了、被放弃了）
        if ap in before:
            if before[ap] != (st.st_mtime_ns, st.st_size):
                modified.append(ap)
        else:
            created.append(ap)
    return sorted(set(created)), sorted(set(modified))


def write_sidecar(path, contract, eff=None, pre=None):
    """把契约写在工件旁边。这样即使没有检索，谁看到这个文件都知道怎么用它。"""
    mp = str(path) + ".meta.json"
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {}
    meta["契约"] = contract
    if eff:
        meta["effects"] = eff
    if pre:
        meta["前置条件"] = pre
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def accept_artifacts(node, artifacts, trace, st):
    """把结论里交代的工件落成契约 + .meta.json 记录。

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
        entry = (st or {}).get("art_effects", {}).get(rp) or {}
        eff, pre = entry.get("effects"), entry.get("preconditions")
        problems = [] if internal else contract_problems(path, contract)
        trace.add(node.id, "contract", {"path": path, "contract": contract,
                                        "problems": problems, "source": "conclusion",
                                        "effects": eff, "preconditions": pre})
        st.setdefault("contracts", []).append({"path": path, "契约": contract,
                                               "effects": eff, "前置条件": pre})
        if not internal and contract and not problems:
            write_sidecar(path, contract, eff, pre)
