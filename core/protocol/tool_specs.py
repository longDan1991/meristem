"""协议的工具清单与 schema 适配。

工具按节点类型分（`NODE_TOOLS` 是单一事实）：

  · alloc    create_children / conclude
  · leaf     bash / read / write / conclude
  · intake   submit_root

工具的**实现**是 `runtime/tools.py` 里的 `@mcp.tool` 函数（schema 与实现一体，
provider 拿到的是 FastMCP 从签名生成的 schema）。本文件只管：清单、形式字段的
形状（`ChildSpec`）、把 mcp 上的工具转成 litellm 要的 OpenAI 格式。
"""

from fastmcp import FastMCP
from fastmcp.utilities.json_schema import replace_refs
from pydantic import BaseModel, Field

from .. import config as cfg
from ..compression import RETRIEVE_TOOL

# 工具都在同一个实例上注册（实现注册发生在 runtime/tools.py 的 import 时）。
# 进程内当"工具定义表"用，不跑 server。
mcp = FastMCP("tree")

# 每个节点类型的工具清单 —— 单一事实。
# headroom_retrieve 不在表里：只在 COMPRESS 开时由 openai_tools 追加。
NODE_TOOLS = {
    "alloc": ("create_children", "conclude"),
    "leaf": ("bash", "read", "write", "conclude"),
    "intake": ("submit_root",),
}


class ChildSpec(BaseModel):
    """一个子任务的形式字段（= 分配节点交给孩子的格子）。"""

    name: str = Field(description="≤20 字。这件事叫什么，你和孩子靠它互相指认。")
    detail: str = Field(description="≤240 字。孩子看不见你的脑子，只能看你写的字。")
    notes: str = Field(default="", description="可选，不限字数。其它字段放不下的判断依据。")
    accept: str = Field(
        description="验收标准 ≤140 字。必须原样带上你验收标准里的可测物理量"
                    "（日期、两位以上数字、标识符如 CSV/MA5/hello.txt）——"
                    "它是唯一能替你判定「做没做完」的东西，换成下游指标会被代码拒掉。")
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
    """一个工具 → OpenAI 格式（litellm 的 tools= 列表里的一项）。"""
    t = await mcp.get_tool(name)
    if t is None:
        raise RuntimeError(
            "工具 %r 还没注册：实现注册在 core/runtime/tools.py 的 import 时发生，"
            "请先 import core.runtime.tools 再拿 schema。" % name)
    params = _plain(replace_refs(t.parameters))
    params.pop("$defs", None)
    return {"type": "function", "function": {
        "name": t.name, "description": t.description, "parameters": params}}


_openai_cache = None


async def openai_tools():
    """每个节点类型的工具清单（OpenAI 格式，给 litellm）。只建一次。"""
    global _openai_cache
    if _openai_cache is None:
        leaf = [await openai_spec(n) for n in NODE_TOOLS["leaf"]]
        if cfg.COMPRESS:
            leaf.append(RETRIEVE_TOOL)
        _openai_cache = {
            "alloc": [await openai_spec(n) for n in NODE_TOOLS["alloc"]],
            "leaf": leaf,
            "intake": [await openai_spec(n) for n in NODE_TOOLS["intake"]],
        }
    return _openai_cache
