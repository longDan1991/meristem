"""叶子工具输出的线上压缩：观测走真 role=tool 消息，交给 headroom。

我们只做两件接线：① 发送边界把叶子的对话交给 `headroom.compress`（它按内容路由：
JSON 无损折叠、日志 run-collapse 带取回标记、代码 AST 压缩）；② 实现取回工具
`headroom_retrieve`，按 hash 从本地 SQLite 取回原文。

压缩只发生在发送时，trace 的 `tool` 事件保持原文；不开 ML（载荷是 JSON/日志/代码），
user / system 消息一字不动。
"""

import asyncio
import os

from headroom import CompressConfig, compress
from headroom.cache.compression_store import get_compression_store
from headroom.ccr.tool_injection import CCR_TOOL_NAME, create_ccr_tool_definition

# tiktoken 词表要联网下载（失败卡 10 秒）；数 token 只影响压缩阈值，所以 0 秒直接走估算。
# headroom 首次 compress 才懒读这个值，放在 import 之后来得及。
os.environ.setdefault("HEADROOM_TIKTOKEN_LOAD_TIMEOUT_SECONDS", "0")

RETRIEVE_NAME = CCR_TOOL_NAME
# 取回工具定义始终挂在叶子上，模型看到压缩标记时随时能取
RETRIEVE_TOOL = create_ccr_tool_definition(provider="openai")

# protect_recent 只保护最近 N 条里的代码；工具输出立即压 —— JSON 无损、日志可取回，没问题。
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
    """发送边界的路由压缩，返回 headroom 的 CompressResult（调用方读统计）。

    压缩是 CPU 活，丢线程池不阻塞事件循环；headroom 契约是 fail-open，不在这里再包 try/except。
    """
    return await asyncio.to_thread(compress, msgs, model=model, config=_COMPRESS_CONFIG)


def retrieve_original(arguments):
    """`headroom_retrieve` 的实现：按压缩标记里的 hash 取回完整原文（共享同一个单例 store）。"""
    h = (arguments or {}).get("hash")
    if not h or not isinstance(h, str):
        return _miss("(缺 hash)")
    entry = get_compression_store().retrieve(h)
    if entry is None:
        return _miss(h)
    return entry.original_content
