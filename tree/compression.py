"""叶子工具输出的线上压缩（选项 B）：观测走真 role=tool 消息，交给 headroom。

headroom 是成熟库（AGENTS §13），我们只做两件接线：
  ① 发送边界：把叶子的对话（system + 基础 user + 累积的 asst/tool 消息）
     交给 `headroom.compress` —— 它按内容路由：JSON/表格 → SmartCrusher
     （无损紧凑折叠，全量保留）、日志 → LOG（run-collapse，FATAL 行保留、
     嵌取回标记）、代码 → CodeCompressor（AST）。
  ② 取回：headroom 只在 proxy/MCP 模式自动注入 `headroom_retrieve`，
     库模式由**我们**注入（tool_specs.openai_tools）并在这里实现 ——
     按压缩文本里的 hash 从它自己的本地 SQLite 库（get_compression_store，
     默认 TTL 30 分钟）取回原文。

压缩只发生在发送时：`node.observations` / trace 保持原文，
`turn.sig`/`bump` 的无进展检测（对原文全量哈希）不受影响（AGENTS §2/§5）。

不开 ML：`kompress_model="disabled"` —— 本项目的载荷是 JSON/日志/代码，
SmartCrusher + LOG 折叠 + CodeCompressor 覆盖，散文压缩是杀鸡用牛刀。
user / system 消息一字不动：前者是形式字段（协议），后者是协议文本。
"""

import asyncio
import os

from headroom import CompressConfig, compress
from headroom.cache.compression_store import get_compression_store
from headroom.ccr.tool_injection import CCR_TOOL_NAME, create_ccr_tool_definition

# headroom 用 tiktoken 数 token（决定 min_tokens_to_compress 阈值）。词表要联网下载，
# 下载失败会卡 10 秒才回退估算 —— 本项目数 token 只影响压缩阈值，预算计的是 API
# 真实用量，所以不背那 10 秒：0 秒直接走估算。headroom 是懒读取这个值（首次
# compress 才生效），放在模块体顶部（import 之后）就来得及。
os.environ.setdefault("HEADROOM_TIKTOKEN_LOAD_TIMEOUT_SECONDS", "0")

RETRIEVE_NAME = CCR_TOOL_NAME
# OpenAI 格式的取回工具定义（静态）。headroom 的代理在"压缩发生"时才注入；
# 我们始终在叶子上挂着它 —— 模型看到压缩标记时随时能取。
RETRIEVE_TOOL = create_ccr_tool_definition(provider="openai")

# 注意：protect_recent 只保护**最近 N 条里的代码**（headroom 语义），
# 工具输出（role=tool）会被立即压 —— 对本项目 OK：JSON 走无损折叠（全量保留），
# 日志折叠带取回标记，模型随时能拿原文。user/system 才是真正一字不动的。
_COMPRESS_CONFIG = CompressConfig(
    compress_user_messages=False,
    compress_system_messages=False,
    protect_recent=4,
    kompress_model="disabled",
)

_MISS = (
    "取回失败：hash %r 不在库里（可能是无损折叠根本没丢数据 —— 数据全在压缩文本里；"
    "也可能是 CCR 条目已过期 / 未写入）。要完整原文就重跑那条命令或重读那个文件。"
)


def _miss(h):
    return _MISS % h


async def compress_messages(msgs, model):
    """发送边界的路由压缩。返回 headroom 的 CompressResult（调用方读统计）。

    压缩是 CPU 活，可能碰到大载荷 —— 丢线程池，不阻塞事件循环（AGENTS §11）。
    headroom 的契约是 fail-open（内部吞异常返回原样），调用方按 §2 信任这个契约，
    不在这里再包一层 try/except。
    """
    return await asyncio.to_thread(compress, msgs, model=model, config=_COMPRESS_CONFIG)


def retrieve_original(arguments):
    """`headroom_retrieve` 的实现：按压缩标记里的 hash 取回完整原文。

    与 ContentRouter 共享同一个 store（get_compression_store 是单例，
    SQLite 后端），所以压缩时存的原文这里一定查得到。
    """
    h = (arguments or {}).get("hash")
    if not h or not isinstance(h, str):
        return _miss("(缺 hash)")
    entry = get_compression_store().retrieve(h)
    if entry is None:
        return _miss(h)
    return entry.original_content
