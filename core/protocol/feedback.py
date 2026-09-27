"""模型会读到的反馈文本 —— 唯一来源。

runtime / protocol / tools 只决定"发生了什么"，不自己拼给模型看的话；会写回对话的句子
都在这里注册。（工具字段 description 是另一回事，住 `tools/specs.py`。）

物理上住 protocol：它的变因是协议规则（形状校验 / 沟通寻址）与模型措辞，被
gate / runtime / tools 三层共同消费，是依赖图的底部词汇层 —— 谁都不许反向依赖它。
"""

from .fields import KINDS


def pair_placeholder():
    """结构类工具（create_children / communicate / submit_root）没有 tool 回话，发模型前补的占位回话。"""
    return "（已发出，等对方回应。）"


def bad_shape(err):
    return "工具参数不合形状，被退回：%s" % err


def unknown_tool(name, allowed):
    return "你调用的 %s 不在这一层的工具里（你能用：%s）" % (name, " / ".join(allowed))


def tool_error(err):
    return "工具出错: %r" % err


def empty_command():
    return "command 是空的：要么写一条命令，要么用 communicate 向父节点回报"


def bad_comm_to(to):
    return ('communicate 的 to 必须是 "parent"（你的父节点）或你一个孩子的 name'
            "（收到 %r —— 孩子名必须是 create_children 里给过的原样名字）。" % (to,))


def bad_root(why):
    return "这样不行：" + why + " 改一次再给。"


# ---------------------------------------------------------------- gate 的拒绝理由
def missing_fields(fields):
    return "缺必填项: " + ", ".join(fields)


def bad_kind(kind):
    return "kind 必须是 %s（给的是 %r）" % (" 或 ".join(KINDS), kind)


def bad_conc_range():
    return "conc_range 必须是 [下限, 上限] 两个正整数，如 [100,500]"
