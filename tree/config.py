"""配置文件（.env）+ 路径规则。零依赖。

`.env` 是唯一的事实来源：**工作区在哪、能力库在哪、索引扫哪里**。
代码必须真的去读它 —— 否则"工作区的路径写在配置文件里"就只是写在纸上。

三条路径的关系（都在工作区里面）：
    TREE_WORKSPACE=/Users/wxlong/output/humanoid
    TREE_CAPS   =<工作区>/caps.jsonl            能力库（跨 session 复用）
    TREE_INDEX  =<工作区>/runs/*/trace.jsonl   要索引的老树（执行树就是成果树）

跑出来的东西**一律落在工作区**：工作区既是 agent 的 cwd（上次写的代码和数据
还在），也是历史 trace 的堆放地。项目目录里只有代码。
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path=None):
    """把 .env 灌进 os.environ。已存在的环境变量不覆盖（shell 优先）。"""
    path = path or os.path.join(ROOT, ".env")
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return out
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        if ln.startswith("export "):
            ln = ln[7:].strip()
        k, v = ln.split("=", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        out[k] = v
        os.environ.setdefault(k, v)
    return out


def workspace():
    """持久工作目录。同一个任务族共用它，上次写的代码和数据就还在。"""
    load_env()
    return os.path.abspath(os.environ.get("TREE_WORKSPACE")
                           or os.path.join(ROOT, "workspace"))


def caps_path():
    load_env()
    return os.path.abspath(os.environ.get("TREE_CAPS")
                           or os.path.join(workspace(), "caps.jsonl"))


def index_glob():
    """要索引的老树。默认扫工作区里所有历史 trace。"""
    load_env()
    return os.environ.get("TREE_INDEX") or os.path.join(
        workspace(), "runs", "*", "trace.jsonl")
