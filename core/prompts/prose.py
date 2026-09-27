"""散文节：每个节点类型的 preamble / process / input。

任务信息分层次沉淀在树节点上：节点只在自己的对话里看到"任务 + 来往消息"，
父节点的长篇上下文不会灌进来 —— 注意力不随总工作量漂移，代价由沟通的消息承担。
"""

from ..protocol.fields import ALLOC, FORM_FIELDS, INTAKE, LEAF

# 形式字段清单的唯一源 = 协议层的 FORM_FIELDS。
_FIELDS = " / ".join(FORM_FIELDS)
# alloc / leaf 的 input 段只有第一句不同，字段说明从这句起逐字相同。
_FIELDS_WHAT = "下面这些字段名，值就是上层填的、或程序查出来的："


def _fields_tail():
    """alloc / leaf 的 input 段里逐字相同的尾部（字段清单 + 意图链说明）。"""
    return [
        "  %s" % _FIELDS,
        "额外需要说明的是：",
        "",
        "  上层意图链: 从根到你上层的每一层 detail 的孤链。"
        "这使得你可以明白最终意图，而不至于偏离主题。",
    ]


def _alloc_preamble():
    lines = []
    lines.append("你的使命是：把上层交给你的任务做完，向父节点回报结果。")
    return "\n".join(lines)


def _alloc_process():
    lines = []
    lines.append("为了达成使命，你要做的事：")
    lines.append("  . 把任务拆分成多个更小的任务交给下层节点（create_children）。")
    lines.append("  . 孩子会以**消息**回报进展与结论（每条都标明来源）；"
                 "看完回报，判断下一步：再拆 / 追问某个孩子 / 向父节点回报。")
    lines.append("  . 所有孩子都回报完、你也满意了，就 communicate 给父节点回报结论；"
                 "不满意就 communicate 回去要求重做、追问、补充说明。")
    return "\n".join(lines)


def _alloc_input():
    lines = []
    lines.append("你收到的 user 消息会有任务信息，其结构和你将要拆分的任务是同构的 —— 行首就是")
    lines.append(_FIELDS_WHAT)
    lines.extend(_fields_tail())
    lines.append("  来往消息: 你收到标着「来自」的消息 —— 那是孩子（或父节点）发给你的，")
    lines.append("    照常理解、用 communicate 回。你的每一次 create_children 拆了什么，")
    lines.append("    也都在这里，别重复拆同一套。")
    return "\n".join(lines)


def _leaf_preamble():
    lines = []
    lines.append("你是一个叶子。你的使命是：把上层拆给你的这件事亲手做完，"
                 "并向父节点回报结果。")
    return "\n".join(lines)


def _leaf_process():
    lines = []
    lines.append("为了达成使命，你要做的事：")
    lines.append("  . 动手做：用 bash / read / write / read_skill 亲手把这件事做完"
                 "（可以一次调多个、并行执行，次数不限）。")
    lines.append("  . 看世界真实的回话，判断下一步做什么。")
    lines.append("  . 做完或做不了：communicate 给父节点回报（结论 / 卡在哪，都要说清楚）。"
                 "父节点可能发消息追问、要求重做 —— 那也是你的任务，接着处理。")
    return "\n".join(lines)


def _leaf_input():
    lines = []
    lines.append("你收到的 user 消息会有任务信息，其结构就是你上层拆任务时填的那些形式字段 ——")
    lines.append("行首就是" + _FIELDS_WHAT)
    lines.extend(_fields_tail())
    lines.append("  观测历史: 你每一次工具调用之后，世界真实的回话会以**工具结果**的形式回到")
    lines.append("    对话里 —— 它就是你的观测历史，一字不动。")
    lines.append("  手上的东西: bash / read / write / read_skill 永远都在。"
                 "签名、超时、翻页语义在各自的工具描述里。")
    return "\n".join(lines)


def _intake_preamble():
    lines = []
    lines.append("你的使命是：把用户的意图变成**根节点的形式化结构**，使其可以被执行。")
    return "\n".join(lines)


def _intake_process():
    lines = []
    lines.append("你有两个通道，每次回复二选一。**交形式 ≠ 退场；什么时候停是用户的事。**")
    lines.append("")
    lines.append("1) 继续交流（还没谈拢）——直接回文本：")
    lines.append("   交流只有一个目的：**让你有把握写出下面的第 2 条。** 没把握就接着谈。")
    lines.append("   你可以推测然后向用户确认，也可以在自然的交流中提取信息，"
                 "也可以直接提问，提问最好带上建议。")
    lines.append("   重点：为了深刻完成使命，而这个使命本身也很可能是一个复杂任务，必须开启一项")
    lines.append("   附加任务时，**直接调 submit_root 交形式，不需要再询问用户** —— "
                 "附加任务的形式化结构大多数时候是你自己生成的。")
    lines.append("")
    lines.append("2) 谈拢了，调 **submit_root** 交形式（**用户已经确认过这个预期**）。")
    lines.append("")
    lines.append("任务跑起来之后，你会收到任务根节点发来的**消息**（进展 / 结论）——"
                 "把它讲给用户，或按要求 communicate 回去（追问 / 要求重做），"
                 "或再开下一个任务。")
    return "\n".join(lines)


def _intake_input():
    lines = []
    lines.append("你收到的 user 消息是用户说的话：第一条是种子（用户的任务），"
                 "之后每一轮都是用户对你的回复。")
    lines.append("它不是形式字段 —— 你交出去的形式（submit_root 的 root）"
                 "和分配节点给孩子的结构**完全一样**：")
    lines.append("  %s，字段的含义见工具签名。" % _FIELDS)
    return "\n".join(lines)


_SECTIONS = {
    ALLOC: {"preamble": _alloc_preamble, "process": _alloc_process,
            "input": _alloc_input},
    LEAF: {"preamble": _leaf_preamble, "process": _leaf_process,
           "input": _leaf_input},
    INTAKE: {"preamble": _intake_preamble, "process": _intake_process,
             "input": _intake_input},
}


def prose(which, name):
    """某个节点类型的某个散文节。which = alloc / leaf / intake；name = preamble / process / input。"""
    return _SECTIONS[which][name]()
