"""从动作里机械抽 effects。能测的就不许模型自报。

bash 和 write 是同一件事的两个壳：`echo hi > a.txt` 就是 write("a.txt","hi")。
所以这里一套抽取同时服务两者 —— 因为复用者只关心"碰了什么"，
不关心命令长什么样。

`前置条件` 和 effects 一样重要：复用失败最常见的原因不是配方错，
而是前提不成立（没网、包没装、不在那个目录）。没有这一项，
一次冤枉的失败会把一条好配方记成"烂了"。
"""

import os
import re

URL_RE = re.compile(r"\b(?:https?|ftp)://([\w.\-]+)(?::(\d+))?")
REDIR_RE = re.compile(r"(>>?)\s*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
READ_RE = re.compile(r"<\s*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
MKDIR_RE = re.compile(r"\bmkdir\s+(?:-p\s+)?([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
TOUCH_RE = re.compile(r"\btouch\s+([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
RM_RE = re.compile(r"\brm\s+(?:-\w+\s+)*([A-Za-z0-9_][A-Za-z0-9_./\-]*)")
PKG_RE = re.compile(r"\b(?:pip3?|npm|apt-get|brew)\s+install\s+(?:-[\w-]+\s+)*([\w\-.]+)")
NOHUP_RE = re.compile(r"\bnohup\b")
TAILBG_RE = re.compile(r"&\s*$")

# 需要人到场 / 真实账户 / 真实资金 —— bash 根本做不到的。模型必填，代码抽不出来。
EXTERNAL_CLASSES = ("需要人到场", "需要真实账户", "需要真实资金", "需要现实设备")


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


CONTRACT_KEYS = ("type", "name", "func", "args", "return", "external")

# func 必须是一条**能直接粘上就执行**的命令，不是一句描述。
# 实测模型会写"执行 bash sum.sh 即可运行，将结果写入 sum.txt"——那是给人看的，
# 不是给复用者用的。
RUNNABLE_RE = re.compile(
    r"^\s*(?:sudo\s+)?(?:python3?|node|bash|sh|zsh|ruby|perl|curl|wget|make|"
    r"docker|npm|npx|pip3?|uv|poetry|go|cargo|java)\b|^\s*\./|^\s*/|^\s*\$\s+")
# type 属于这几类的，func 必须是一条命令
RUNNABLE_TYPES = ("程序", "脚本", "工具", "服务", "命令", "库", "模块", "cli", "CLI")


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
        else:
            v = str(v or "").strip()
        if v:
            c[k] = v
    return c


def contract_problems(path, contract):
    """能机械核对的那部分。不自动跑它（跑会带来副作用），
    只核对它声称的入口真的存在、func 是不是一条能跑的命令、该填的填了。"""
    problems = []
    ctype = contract.get("type", "")
    internal = ctype == "内部"
    if not internal:
        if not contract.get("func"):
            problems.append("type 不是内部，但没写 func（别人怎么调用它）")
        if not contract.get("name"):
            problems.append("没写 name（这东西是干什么用的）")
        if ctype in RUNNABLE_TYPES and not is_runnable(contract):
            problems.append(
                "type 是「%s」，但 func 不是一条能直接执行的命令"
                "（要以 python3 / bash / ./ 之类开头）：%r"
                % (ctype, str(contract.get("func"))))
    for ref in re.findall(r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z]{1,4}", 
                          str(contract.get("func") or "")):
        if not os.path.exists(ref):
            problems.append("func 里引用的入口不存在: %s" % ref)
    bad = [x for x in (contract.get("external") or [])
           if x not in EXTERNAL_CLASSES]
    if bad:
        problems.append("external 只认这几类: %s（收到 %s）"
                        % (" / ".join(EXTERNAL_CLASSES), bad))
    if path and not os.path.exists(path):
        problems.append("path 指向的文件不存在: %s" % path)
    return problems
