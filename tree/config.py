"""部署配置：工作区在哪、历史会话扫哪里。

**这是全项目唯一能定义这些路径的地方，而且必须是显式配置**
（AGENTS §7）：`.env`（或环境变量）说了算，代码不替它推算。
业务代码一律 `from tree.config import WORKSPACE` —— 不许自己拼路径、
不许 `Path(__file__).parent.parent / "data"`、不许拿 cwd 当数据根。

跑出来的东西**一律落在工作区**：工作区既是 agent 的 cwd（上次写的代码和数据
还在），也是历史 trace 的堆放地。项目目录里只有代码。
"""

import os

from dotenv import load_dotenv

# 配置文件本身的位置（这不是数据根，是"配置放哪"）：环境变量可覆盖，
# 默认用随代码走的那份 `.env`。数据根一律从它读出来的值里来。
ENV_FILE = os.environ.get("TREE_ENV") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# .env 由 python-dotenv 解析（引号 / export / 换行等边界它都处理）。
# override=False：已存在的环境变量不覆盖（shell 优先）。
# 文件不存在不算错：环境变量可能已经把该给的都给了。
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _abs(p):
    return os.path.abspath(os.path.expanduser(p))


def _required(name):
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(
            "%s 没配。数据根不许推算：在 %s 里（或环境变量里）给它一个绝对路径。"
            % (name, ENV_FILE))
    return v


# 工作区：持久工作目录。同一个任务族共用它，上次写的代码和数据就还在。
WORKSPACE = _abs(_required("TREE_WORKSPACE"))
# 历史会话的堆放地：`-r` 从这里列老会话。执行树就是成果树。
INDEX_GLOB = os.environ.get("TREE_INDEX") or os.path.join(
    WORKSPACE, "runs", "*", "trace.jsonl")

# 叶子工具输出的线上压缩（选项 B）。0/false/no/off = 关：压缩是 lossy 功能，
# 这是个保险阀（故障排查 / 复现时关掉，让模型看原文）。关闭后取回工具也不再挂。
COMPRESS = os.environ.get("TREE_COMPRESS", "1").strip().lower() not in \
    ("0", "false", "no", "off")
