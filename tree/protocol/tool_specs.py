"""协议的工具定义：节点与模型之间唯一的通道。

三个工具，两种角色（本地/远端同构：都定义在同一个 FastMCP 实例上，
将来要连外部 MCP server，client 拿到的工具进同一个注册表）：

  · create_children —— 分配节点再拆一层（它唯一的动作）
  · run_code        —— 叶子写一段代码（它唯一的动作）
  · conclude        —— 出结论（两个节点共用）

模型每次回复必须调用且只能调用其中一个；没调用 = 协议违规（balk）。
参数形状由 pydantic schema 强制；**语义校验仍走 gate**（clean_spec /
clean_conclusion）—— schema 只保证形状，拒绝信息保持 gate 的中文原文。

字段的"本质"说明（≤20 字是归属…）从 `prompts/alloc.md` 迁到了这里每个
property 的 description：provider 会把它们原样喂给模型，所以它们就是
提示词的一部分，只是按字段挂载。改字段含义要看 gate.py（同源）。

实现（工具函数体）在 `runtime/turn.py` —— 那里才是"回合怎么走"的逻辑；
本文件只管格子形状与 schema。`openai_tools()` 把 FastMCP 工具转成
litellm 要的 OpenAI 格式（$ref 展平，只建一次）。
"""

from pydantic import BaseModel, ConfigDict, Field
from fastmcp import FastMCP
from fastmcp.utilities.json_schema import replace_refs

# 工具都在同一个实例上注册。它只在进程内当"工具定义表"用，
# 不跑 server、不建 client —— 传输层等 MCP 需求来了再激活。
mcp = FastMCP("tree")


class ChildSpec(BaseModel):
    """一个子任务的形式字段（= 分配节点写回的孩子格子）。

    必填由 schema 强制；语义（kind 取值、区间顺序、可测物理量继承）由
    gate.clean_spec 复核 —— 两层都过不了时，gate 的中文原因进本层尝试。
    """

    name: str = Field(
        description="≤20 字。本质是**归属**：这件事叫什么，你和孩子靠它互相指认。")
    detail: str = Field(
        description="≤240 字。本质是**上下文**：孩子看不见你的脑子，只能看你写的字。")
    notes: str = Field(
        default="",
        description="可选，不限字数。写其它字段里放不下的判断依据；不参与老树检索。")
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
    keywords: list[str] = Field(
        description="一个以上检索键。本质是**不浪费已经做过的工作**：孩子一出生，"
                    "程序就拿这几个键扫所有老树 + 能力库。写包名、命令动词、文件名、"
                    "数字、标识符，不要形容词。")
    conc_range: list[int] = Field(
        description="对孩子结论的字数建议区间，如 [100,500] 或 [1000,2000]。"
                    "本质是判断你想要的成果规模：一句话能说清就给窄区间，"
                    "需要推理、证据、数字就给宽区间。")


class Artifact(BaseModel):
    """结论里交代的一个产物。入口给完整契约；只给自己用的写 type=内部。"""

    model_config = ConfigDict(populate_by_name=True)

    path: str = Field(description="文件路径（相对工作区）。")
    type: str = Field(
        default="", description="程序|配置|数据|脚本|内部。只给自己用、或只是数据/"
                                "日志，写「内部」就行。")
    name: str = Field(default="", description="干什么用的。")
    func: str = Field(
        default="",
        description="**能直接粘上就执行的一条命令**，如 bash sum.sh、"
                    "python3 main.py --flag x；不要写句子（写错了会被退回来）。")
    args: str = Field(default="", description="参数。")
    params: dict = Field(
        default_factory=dict,
        description="func 里 __名字__ 占位符的参数声明："
                    "{\"名字\":{\"type\":\"int|str|float|bool\","
                    "\"default\":默认值}}。写了它 = 把这条做法变成别人可直接"
                    "调用的工具。不想被复用的一次性脚本就别写。")
    ret: str = Field(default="", alias="return", description="返回/写出什么。")
    external: list[str] = Field(default_factory=list)


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
    """
    global _openai_cache
    if _openai_cache is None:
        _openai_cache = {
            "alloc": [await _openai_spec("create_children"),
                      await _openai_spec("conclude")],
            "leaf": [await _openai_spec("run_code"),
                     await _openai_spec("conclude")],
        }
    return _openai_cache
