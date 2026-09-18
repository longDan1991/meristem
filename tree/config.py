"""部署配置：工作区在哪、能力库在哪、索引扫哪里。

**这是全项目唯一能定义这些路径的地方，而且必须是显式配置**
（AGENTS §7）：`.env`（或环境变量）说了算，代码不替它推算。
业务代码一律 `from tree.config import WORKSPACE` —— 不许自己拼路径、
不许 `Path(__file__).parent.parent / "data"`、不许拿 cwd 当数据根。

三条路径的关系（都在工作区里面）：
    TREE_WORKSPACE=<绝对路径>        agent 的 cwd + 历史 trace 的堆放地
    TREE_CAPS=<工作区>/caps.jsonl    能力库（跨 session 复用）
    TREE_INDEX=<工作区>/runs/*/trace.jsonl   要索引的老树

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
# 能力库：跨 session 复用的现成做法。默认在工作区里。
CAPS_PATH = _abs(os.environ.get("TREE_CAPS") or os.path.join(WORKSPACE, "caps.jsonl"))
# 要索引的老树：默认扫工作区里所有历史 trace。执行树就是成果树。
INDEX_GLOB = os.environ.get("TREE_INDEX") or os.path.join(
    WORKSPACE, "runs", "*", "trace.jsonl")
