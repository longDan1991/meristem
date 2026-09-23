"""部署配置：工作区在哪、历史会话扫哪里。

这是全项目唯一能定义这些路径的地方，而且必须是显式配置（`.env` / 环境变量说了算，
代码不替它推算）。业务代码一律 `from core.config import WORKSPACE`，不许自己拼路径或拿 cwd 当数据根。

跑出来的东西一律落在工作区：它既是 agent 的 cwd，也是历史 trace 的堆放地；项目目录只有代码。
"""

import os

from dotenv import load_dotenv

# 配置文件本身的位置（不是数据根）：环境变量可覆盖，默认用随代码走的那份 `.env`
ENV_FILE = os.environ.get("TREE_ENV") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# override=False：已存在的环境变量不覆盖；文件不存在不算错
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


WORKSPACE = _abs(_required("TREE_WORKSPACE"))

# 叶子工具输出的线上压缩：0/false/no/off = 关（保险阀，关掉后取回工具也不挂）
COMPRESS = os.environ.get("TREE_COMPRESS", "1").strip().lower() not in \
    ("0", "false", "no", "off")

# 同时在飞的模型调用数（ChatPool）：限的是最贵的资源，不是节点数
WORKERS = int(os.environ.get("TREE_WORKERS", "6"))
