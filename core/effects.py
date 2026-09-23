"""从动作里机械抽 effects：bash 和 write 是同一件事的两个壳，一套抽取同时服务两者。

`前置条件` 和 effects 一样重要 —— 复用失败最常见的原因不是配方错，而是前提不成立。

effects 只进 trace 事件，不落任何节点状态（历史只活在一处）。
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


def abs_path(p, cwd=None):
    """相对当前目录的路径 → 绝对路径；已绝对 / 没给 cwd 就原样返回。"""
    if not p:
        return None
    if p.startswith("/") or not cwd:
        return p
    return os.path.normpath(os.path.join(cwd, p))


def _abs(p, cwd):
    # shell 文本里的 /dev/null 与 "&" 不是产物，不记
    if not p or p.startswith("/dev/") or p.startswith("&"):
        return None
    return abs_path(p, cwd)


def effects_of(tool, args, cwd=None, existed_before=None):
    """返回 (effects, 前置条件)；write 必须传 existed_before —— 本函数在动作之后跑，不传 create 会被记成 modify。"""
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
