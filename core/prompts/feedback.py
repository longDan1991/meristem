"""模型会读到的反馈文本 —— 唯一来源。

runtime / protocol 只决定"发生了什么"，不自己拼给模型看的话；会写回对话的句子都在这里注册。
（工具字段 description 是另一回事，住 `protocol/tool_specs.py`。）
"""

from ..protocol.fields import VERDICTS


def pair_placeholder():
    """结构类工具（create_children / conclude / submit_root）没有 tool 回话，发模型前补的占位回话。"""
    return "（已交给下层，结论随后以消息到达。）"


def bad_shape(err):
    return "工具参数不合形状，被退回：%s" % err


def unknown_tool(name, allowed):
    return "你调用的 %s 不在这一层的工具里（你能用：%s）" % (name, " / ".join(allowed))


def empty_cmd():
    return "cmd 是空的：要么写一条命令，要么用 conclude 出结论"


def criterion_drift(missing):
    return ("子任务的 accept 丢了可测物理量（缺 %s）—— 这是把任务换成了别的东西"
            % ", ".join(sorted(missing)))


def too_many_gates():
    return "一次分配最多一个门槛"


def bad_root(why):
    return "这样不行：" + why + " 改一次再给。"


def gate_failed(conclusion):
    """门槛不成立时，暂缓兄弟的结论文本（会随 child_result 进父节点对话）。"""
    return "门槛不成立：%s" % conclusion


# ---------------------------------------------------------------- gate 的拒绝理由
def missing_fields(fields):
    return "缺必填项: " + ", ".join(fields)


def bad_kind(kind):
    return "kind 必须是 dispatch 或 leaf（给的是 %r）" % kind


def bad_conc_range():
    return "conc_range 必须是 [下限, 上限] 两个正整数，如 [100,500]"


def bad_verdict():
    return "判定必须是 " + "|".join(VERDICTS)


def downgraded_suffix():
    return "（原判「满足」但证据指不到真实的东西，已降级）"


def root_needs_anchor():
    return ("验收标准里必须有一个可测物理量（日期 / 两位以上数字 / "
            "标识符如 hello.txt），否则这棵树判不了自己做没做完")
