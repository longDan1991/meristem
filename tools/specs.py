"""工具注册表与 schema 适配（`mcp` 实例也住这里，工具注册共用同一实例）。

**作用域用 fastmcp 自己的功能，不另写一套**：工具在自己声明处带 `scope:<层>` 标签
（`@mcp.tool(tags={scope_tag(LEAF)})`），要问"某层能调哪些工具"就把定义表挂成一个只读视图，
交给库的可见性 allowlist（`enable(tags=..., only=True)` + `list_tools()`）自己筛（见 `_view`）——
清单不是这里手抄的表。`action` 标签另外标出"亲手接触世界的动手工具"（证据审计认的观测）。

`scope_names` / `action_names` / `scopes` 是同步读的（提示词是同步拼的），值来自 `load()`
那次库查询；没加载就调会当场报错 —— `openai_tools()` / `loop.run()` 会先 `await load()`。

工具实现是 `tools/defs.py` / `tools/bash.py` 的 `@mcp.tool` 函数（schema 与实现一体），
`defs` / `bash` 在 import 时注册，所以拿清单前要先 `import tools.defs`。
"""

from fastmcp import FastMCP
from fastmcp.utilities.json_schema import replace_refs
from pydantic import BaseModel, Field

from core.protocol.fields import ANCHOR_HINT

# 工具都注册在同一个实例上（实现在 tools/defs.py 的 import 时注册）；进程内当定义表用，不跑 server
mcp = FastMCP("tree")

# 作用域标签的命名（对齐 fastmcp 文档里 `namespace:xxx` 的惯例）；另一族标签是 ACTION_TAG
_SCOPE_PREFIX = "scope:"
ACTION_TAG = "action"


def scope_tag(which):
    """`scope:<层>` 标签名 —— 作用域标签的命名只有这一处。"""
    return _SCOPE_PREFIX + which


def _view(*tags):
    """定义表的只读视图：挂进一个临时 server，给了 tags 就用库的 allowlist（只有这些标签的组件可见）。

    视图是另一台 server，所以定义表本身（`get_tool` 给别的层拿 schema）不受影响。
    """
    view = FastMCP("view")
    view.mount(mcp)
    return view.enable(tags=set(tags), only=True) if tags else view


async def _names(view):
    return tuple(t.name for t in await view.list_tools())


_loaded = False
_scopes: dict[str, tuple[str, ...]] = {}
_actions: tuple[str, ...] = ()


async def load():
    """把作用域视图从 fastmcp 注册表里读出来（进程内一次；工具是静态的，不随节点变）。

    作用域名来自注册表里出现的 `scope:` 标签，每层的工具名由库的可见性过滤给出 ——
    没有一处是手抄的映射。
    """
    global _loaded, _scopes, _actions
    if _loaded:
        return
    registered = await _view().list_tools()
    tags = sorted({t for x in registered for t in x.tags if t.startswith(_SCOPE_PREFIX)})
    scopes = {tag[len(_SCOPE_PREFIX):]: await _names(_view(tag)) for tag in tags}
    actions = await _names(_view(ACTION_TAG))
    _scopes, _actions, _loaded = scopes, actions, True


def _require_loaded():
    if not _loaded:
        raise RuntimeError("工具作用域还没加载：先 await tools.specs.load()"
                           "（tools.defs 的 import 只负责注册，load 才读注册表）")


def scopes():
    """全部作用域（= 节点类型），来自注册表里的 `scope:` 标签。"""
    _require_loaded()
    return tuple(_scopes)


def scope_names(which):
    """某作用域能调的工具名 —— 工具清单的唯一出口。"""
    _require_loaded()
    if which not in _scopes:
        raise ValueError("未知作用域 %r（注册表里有：%s）"
                         % (which, " / ".join(_scopes) or "一个都没有"))
    return _scopes[which]


def action_names():
    """动手工具名（证据审计唯一认的"观测"来源）。"""
    _require_loaded()
    return _actions


class ChildSpec(BaseModel):
    """一个子任务的形式字段（分配节点交给孩子的格子）。"""

    name: str = Field(description="≤20 字。这件事叫什么，你和孩子靠它互相指认。")
    detail: str = Field(description="≤240 字。孩子看不见你的脑子，只能看你写的字。")
    notes: str = Field(default="", description="可选，不限字数。其它字段放不下的判断依据。")
    accept: str = Field(
        description="验收标准 ≤140 字。必须原样带上你验收标准里的可测物理量"
                    "（%s）——"
                    "它是唯一能替你判定「做没做完」的东西，换成下游指标会被代码拒掉。"
                    % ANCHOR_HINT)
    kind: str = Field(
        description="分工：dispatch = 还要继续拆；leaf = 派一个能亲手干活的叶子。"
                    "没有 execute 分支：「不拆」就是派一个叶子。")
    gate: bool = Field(
        default=False,
        description="可选，一次最多一个。这件事不先做，其余全是白做 —— "
                    "它第一个做，在它通过之前其余子任务一律不启动。")
    conc_range: list[int] = Field(
        description="对孩子结论的字数建议区间，如 [100,500]。判断你想要的成果规模。")


def _plain(o):
    if isinstance(o, dict):
        return {k: _plain(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_plain(v) for v in o]
    return o


async def openai_spec(name):
    """一个工具 → OpenAI 格式（chat.completions 的 tools= 列表里的一项）。"""
    t = await mcp.get_tool(name)
    if t is None:
        raise RuntimeError("工具 %r 不在注册表里（注册发生在 tools/defs.py 的 import 时）" % name)
    params = _plain(replace_refs(t.parameters))
    params.pop("$defs", None)
    return {"type": "function", "function": {
        "name": t.name, "description": t.description, "parameters": params}}


_specs_cache = None


async def openai_tools():
    """每个作用域的工具清单（OpenAI 格式，给 chat.completions）。只建一次。"""
    global _specs_cache
    await load()
    if _specs_cache is None:
        _specs_cache = {which: [await openai_spec(n) for n in scope_names(which)]
                        for which in scopes()}
    return _specs_cache
