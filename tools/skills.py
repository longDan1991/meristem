"""通用 skill 加载：扫描 SKILLS_DIRS 下 `*/SKILL.md` 挂成 fastmcp 资源，read_skill 按需读。

对齐 oh-my-pi 的 skill 范式（docs/skills.md）：skill = 静态内容包 —— SKILL.md frontmatter
的 `name` / `description` 是检索面（清单进 system prompt），正文是用法（模型按需读）。
system prompt 只放 name + description 清单（`<skills>` 节，渲染在 core/prompts/skills.py），
全文经 read_skill 按需读 `skill://<名字>/<路径>`。

agent-reach 只是注册进来的一个 skill，本模块对任何具体 skill 一无所知 ——
它的目录落在默认扫描根 `~/.agents/skills` 下而已（`agent-reach skill --install` 的落点）。
"""

from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import NotFoundError, ResourceError
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from core import config as cfg
from core.protocol import feedback
from core.protocol.fields import LEAF
from tools.context import _action_result, _current, get_binding
from tools.specs import ACTION_TAG, mcp, scope_tag

# import 时扫描一次（进程内静态 → system 字节稳定，KV 缓存按节命中）；根目录不存在 = 空 provider。
_skills = SkillsDirectoryProvider(roots=cfg.SKILLS_DIRS)
mcp.add_provider(_skills)


def discovered(provider=None):
    """已注册技能的 (name, description) 清单 —— `<skills>` 节的唯一来源。

    description 压平换行（YAML block scalar 可能跨行，清单节要一行一个技能）。
    """
    p = provider or _skills
    return [(x.skill_info.name,
             x.skill_info.description.replace("\n", " "))
            for x in p.providers]


async def _read_skill(mcp_inst, uri):
    """读一个已注册 skill 的资源：内容文本；读不到 → 带上下文的错误文本。"""
    # skill://<技能名>/<文件路径>：缺名字或路径为空（skill://demo/）会让 fastmcp 内部断言
    # 炸掉，这是工具的输入契约，先挡掉给清楚的说法（§2：错误带上下文，不炸穿调用方）。
    if not isinstance(uri, str) or not uri.startswith("skill://"):
        return feedback.tool_error(ValueError(
            "read_skill 的 URI 必须是 skill://<技能名>/<文件路径>，收到 %r" % (uri,)))
    segs = uri[len("skill://"):].split("/")
    if not segs[0] or not any(segs[1:]):
        return feedback.tool_error(ValueError(
            "read_skill 的 URI 必须是 skill://<技能名>/<文件路径>，收到 %r" % (uri,)))
    try:
        res = await mcp_inst.read_resource(uri)
    except (NotFoundError, ResourceError, ValueError, FileNotFoundError,
            AssertionError) as e:
        return feedback.tool_error(e)
    texts = [c.content for c in res.contents if getattr(c, "content", None)]
    return "\n\n".join(texts) if texts else str(res)


_URI_DESC = ("要读的 skill 资源 URI。先读 skill://<名字>/_manifest 看文件清单，"
             "再读 skill://<名字>/SKILL.md（路由表）或子文件（重试链）。")


@mcp.tool(tags={scope_tag(LEAF), ACTION_TAG})
async def read_skill(uri: Annotated[str, _URI_DESC],
                     _b=Depends(get_binding)) -> dict:
    """读一个已注册 skill 的文件：清单节里列出的任何技能，全文按需读。"""
    _loop, store, nid, _node = _current(_b)
    obs = await _read_skill(mcp, uri)
    return {"text": _action_result(store, nid, "read_skill", {"uri": uri}, obs)}
