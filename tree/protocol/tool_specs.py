"""协议的工具定义：节点与模型之间唯一的通道。

工具按节点类型分（本地/远端同构：都定义在同一个 FastMCP 实例上，
将来要连外部 MCP server，client 拿到的工具进同一个注册表）：

  · alloc    create_children（再拆一层）/ conclude（出结论）
  · leaf     bash / read / write（三只手，叶子的直接工具）/ conclude
  · intake   submit_root（入口交形式）

`NODE_TOOLS` 是**每个节点类型的工具清单，单一事实**：prompts 的 tools/rules
节从它推导（docs/PROMPTS.md §4.2）、turn 的回合校验和 openai_tools 也拿它。
模型每次回复必须调用且只能调用其中一个；没调用 = 协议违规（balk）。
参数形状由 pydantic schema 强制；**语义校验仍走 gate**（clean_spec /
clean_conclusion）—— schema 只保证形状，拒绝信息保持 gate 的中文原文。

字段/工具的"本质"说明住各自的 schema description：provider 会把它们原样
喂给模型，所以它们就是提示词的一部分，只是按工具/字段挂载（W2 去重：
提示词节文件不再重复工具描述）。改字段含义要看 gate.py（同源）。

实现（工具函数体）在 `runtime/turn.py` —— 那里才是"回合怎么走"的逻辑；
本文件只管格子形状与 schema。`openai_tools()` 把 FastMCP 工具转成
litellm 要的 OpenAI 格式（$ref 展平，只建一次）。
"""

from pydantic import BaseModel, Field
from fastmcp import FastMCP
from fastmcp.utilities.json_schema import replace_refs

from .. import config as cfg
from ..compression import RETRIEVE_TOOL

# 工具都在同一个实例上注册。它只在进程内当"工具定义表"用，
# 不跑 server、不建 client —— 传输层等 MCP 需求来了再激活。
mcp = FastMCP("tree")

# 每个节点类型的工具清单 —— 单一事实（docs/PROMPTS.md §4.2）：
# prompts 的 tools/rules 节、turn 的回合校验、openai_tools 都从这里拿。
# headroom_retrieve 不在表里：它只在 COMPRESS 开时由 openai_tools 追加。
NODE_TOOLS = {
    "alloc": ("create_children", "conclude"),
    "leaf": ("bash", "read", "write", "conclude"),
    "intake": ("submit_root",),
}


class ChildSpec(BaseModel):
    """一个子任务的形式字段（= 分配节点写回的孩子格子）。

    必填由 schema 强制；语义（kind 取值、区间顺序、可测物理量继承）由
    gate.clean_spec 复核 —— 两层都过不了时，gate 的中文原因进本层对话。
    """

    name: str = Field(
        description="≤20 字。本质是**归属**：这件事叫什么，你和孩子靠它互相指认。")
    detail: str = Field(
        description="≤240 字。本质是**上下文**：孩子看不见你的脑子，只能看你写的字。")
    notes: str = Field(
        default="",
        description="可选，不限字数。写其它字段里放不下的判断依据。")
    accept: str = Field(
        description="验收标准 ≤140 字。本质是**可机械核对**：它是唯一能替你判定"
                    "「做没做完」的东西，必须原样带上你验收标准里的可测物理量"
                    "（日期、两位以上数字、标识符如 CSV/MA5/hello.txt），"
                    "换成下游指标会被代码拒掉。")
    kind: str = Field(
        description="分工：dispatch = 还要继续拆；leaf = 派一个能亲手干活的叶子。"
                    "没有 execute 分支：「不拆」就是派一个叶子。")
    gate: bool = Field(
        default=False,
        description="可选，一次最多一个。本质是**轻重缓急**：这件事不先做，"
                    "其余全是白做。它会第一个做，在它通过之前其余子任务一律不启动。"
                    "想不出作废条件就别标。")
    conc_range: list[int] = Field(
        description="对孩子结论的字数建议区间，如 [100,500] 或 [1000,2000]。"
                    "本质是判断你想要的成果规模：一句话能说清就给窄区间，"
                    "需要推理、证据、数字就给宽区间。")


# ------------------------------------------------------------------ 适配器
def _plain(o):
    """jsonref 的代理对象转成纯 dict/list（replace_refs 的返回要落盘/送 API）。"""
    if isinstance(o, dict):
        return {k: _plain(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_plain(v) for v in o]
    return o


async def _openai_spec(name):
    t = await mcp.get_tool(name)
    if t is None:
        raise RuntimeError(
            "工具 %r 还没注册：实现注册在 tree/runtime/turn.py 的 import 时发生，"
            "请先 import tree.runtime.turn 再拿 schema。" % name)
    params = _plain(replace_refs(t.parameters))
    params.pop("$defs", None)          # $ref 已展平，$defs 是死重
    return {"type": "function", "function": {
        "name": t.name, "description": t.description, "parameters": params}}


_openai_cache = None


async def openai_spec(name):
    """单个工具 → OpenAI 格式（litellm 的 tools= 列表里的一项）。

    入口（submit_root）和节点工具共用同一个适配器 —— 本地/远端、
    入口/节点，工具的 schema 生成是同一条路。
    """
    return await _openai_spec(name)


async def openai_tools():
    """每个节点类型的工具清单（OpenAI 格式，给 litellm）。只建一次。

    schema 与节点无关，是静态的；工具实现（turn.py）在 import 时已注册到 mcp。
    叶子多挂一个 `headroom_retrieve`（取回被压过的工具输出原文）——
    压缩开着才挂（compression.py 的实现与 store 都在，关了就没有标记可取）。
    """
    global _openai_cache
    if _openai_cache is None:
        leaf_tools = [await _openai_spec(n) for n in NODE_TOOLS["leaf"]]
        if cfg.COMPRESS:
            leaf_tools.append(RETRIEVE_TOOL)
        _openai_cache = {
            "alloc": [await _openai_spec(n) for n in NODE_TOOLS["alloc"]],
            "leaf": leaf_tools,
        }
    return _openai_cache
