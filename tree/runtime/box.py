"""盒子：能力库里的 cap 变成子进程里**可调用的 API**。

三个动作，三件事：

    register(entry)          一条能力进盒子（= `Caps.record`）
    search(query)            给一句话，返回命中的工具（= `Caps.search` + 签名）
    call(tool, args)         执行它，返回 (观测, 真跑的那条命令)

`call` 是唯一新增的东西：它把 `func` 里的 `__名字__` 换成调用者给的参数，
然后用**和 bash 同一套**执行（`hands.run`）、同一套可见截断、同一套成败判定。

一张 cap 什么时候算"可调用"：有 `契约.func` 就算（params 可以为空 ——
`bash sum.sh` 这种零参工具也是工具）。没有契约的 cap 仍进盒子，但只作为
「现成做法」展示给模型看 —— 那是今天的用法，不改。

**名字就是身份**：`契约.name` 是模型在代码里写的函数名。它不是 Python 标识符
（中文名、`-`、数字开头）或者会遮住协议自己的名字（`sys`/`print`）时，
退化成 `cap_<id>`。宁可名字难看，也不能让绑定悄悄盖掉别的名字。
"""

import re

from ..memory.mine import dedupe_key
from ..tools import ok_obs

# 协议自己的名字，绝不能被 cap 盖掉（它是在同一份全局命名空间里绑定的）
RESERVED = frozenset((
    "_call", "_api", "search_tools", "print", "sys", "os", "json", "ast",
    "signal", "functools", "globals", "repr", "open", "True", "False", "None",
))
NON_WORD = re.compile(r"\W", re.UNICODE)


def func_name(raw, fallback):
    """cap 的名字 → 子进程里能绑定的函数名。"""
    s = NON_WORD.sub("_", str(raw or "")).strip("_")
    if (not s or s[0].isdigit() or not s.isidentifier() or s in RESERVED):
        return fallback
    return s


def signature(tool):
    """一行签名 —— 模型在代码里看到的就是这个。参数没给默认值的标 (必填)。"""
    bits = []
    for k, spec in (tool.get("params") or {}).items():
        spec = spec if isinstance(spec, dict) else {}
        bits.append("%s:%s%s" % (k, spec.get("type") or "?",
                                 ("=%s" % spec["default"])
                                 if "default" in spec else ""))
    return "%s(%s)" % (tool["name"], ", ".join(bits))


def fill(tool, args):
    """把参数填进 `func` 模板。缺参、多参、类型不对都当场抛 ——
    错的是调用，不是世界；悄悄用一个默认值会让模型以为它调对了。"""
    params = tool.get("params") or {}
    spot = set(args) - set(params)
    if spot:
        raise ValueError("%s 没有这些参数: %s（它的签名是 %s）"
                         % (tool["name"], ", ".join(sorted(spot)),
                            signature(tool)))
    out = tool["cmd"]
    for k, spec in params.items():
        spec = spec if isinstance(spec, dict) else {}
        if k in args:
            v = args[k]
        elif "default" in spec:
            v = spec["default"]
        else:
            raise ValueError("%s 缺少必填参数 %s" % (tool["name"], k))
        t = spec.get("type")
        if t == "int":
            v = int(v)
        elif t == "float":
            v = float(v)
        elif t == "bool":
            v = bool(v)
        elif t == "str":
            v = str(v)
        out = out.replace("__%s__" % k, str(v))
    return out


def reuse_re(template):
    """把一条配方编译成"填过参也算"的正则：`__名字__` 是通配。

    模型把配方照抄到 bash 里时，占位符已经被它换成真值了
    （`echo __text__ > n.txt` → `echo 你好 > n.txt`），所以字面包含
    永远对不上。**在 search 里编译一次**，不在每次 bash 调用里重算（§11）。
    """
    parts = re.split(r"__[A-Za-z_][A-Za-z0-9_]*__", dedupe_key(template))
    return re.compile(r"\s*.*?\s*".join(re.escape(p) for p in parts))


class Box:
    """一个节点出生时拿到的盒子：检索命中几条，就绑几条。"""

    def __init__(self, caps, hands):
        self.caps = caps
        self.hands = hands
        self._tools = {}          # tool_id -> tool
        self._reuse = []          # (编译过的配方正则, cap_id)：给“照抄粘贴”的复用记账

    # ---------------------------------------------------------------- 注册
    def register(self, entry):
        return self.caps.record(entry)

    # ---------------------------------------------------------------- 搜索
    def search(self, query):
        """返回 (可调用的工具, 给模型看的文字, 命中的 cap id)。

        “可调用”和“命中”不是同一批：**文字里有全部命中的做法**（包括只有配方、
        没有签名的 —— 它们仍然能照抄着跑），而工具只有那些声明了 `契约.func` 的，
        也就是“名字 + 参数”都确定的。少给文字里的一条，就是在背后替模型丢东西；
        多绑一个没签名的函数，就是把它引到一条走不通的路上。

        `caps is None`（没有能力库的跑法）时什么都不给。
        """
        if self.caps is None:
            return [], "", []
        picked, text = self.caps.search(query or "")
        self._reuse = [(reuse_re(cmd), e["id"])
                       for cmd, e in (((e.get("how") or {}).get("cmd"), e)
                                      for e in picked) if cmd]
        tools = [t for t in (self._tool(e) for e in picked) if t]
        for t in tools:
            self._tools[t["id"]] = t
        return tools, text, [e["id"] for e in picked]

    def _tool(self, e):
        c = e.get("契约") or {}
        cmd = c.get("func") or ""
        if not cmd:
            return None                     # 没契约：只能是"现成做法"，不是 API
        tid = "cap:%s" % e["id"]
        return {"id": tid, "name": func_name(c.get("name") or e.get("does"),
                                            "cap_%s" % e["id"]),
                "desc": e.get("does") or "", "params": c.get("params") or {},
                "cmd": cmd}

    def bindings(self, tools):
        """子进程里那几行绑定。名字冲突时后面的退化成 cap_<id>。"""
        lines, used = [], set()
        for t in tools:
            name = t["name"]
            if name in used:
                name = "cap_%s" % t["id"].split(":", 1)[1]
            used.add(name)
            lines.append("%s = _api(%r)   # %s ｜ %s"
                         % (name, t["id"], signature(t), t["desc"]))
        return lines

    # ---------------------------------------------------------------- 调用
    def note_reuse(self, cmd, ok):
        """模型没调工具，而是把那条配方**照抄到 bash 里**跑了 —— 这仍是复用。

        没有这一步，只会有"调函数"的复用被记账，粘贴那一半的 uses/fails
        永远是 0，而"失败多于成功就退休"的自清洁就死了一大半。

        只按"配方出现在这条命令里"算：半截的粘贴（只跑了配方的开头）
        不算复用 —— 活干完没有，库不该因为这个数字变好。
        """
        c = dedupe_key(str(cmd or ""))
        if not c:
            return None
        for rx, eid in self._reuse:
            if rx.search(c):
                self.caps.note_outcome(eid, ok)
                return eid
        return None

    async def call(self, tool_id, args):
        """跑一条 cap。返回 (观测, 真跑的那条命令)；命令给能力挖掘看。"""
        t = self._tools.get(tool_id)
        if t is None:
            raise KeyError("这个工具不在本次盒子里: %s（它可能没有声明 params/func，没法调用）"
                           % tool_id)
        cmd = fill(t, args)
        obs = await self.hands.run("bash", {"cmd": cmd})
        self.caps.note_outcome(tool_id.split(":", 1)[1],
                               ok_obs(obs))      # 复用反馈：盒子不会自己烂掉
        return str(obs), cmd