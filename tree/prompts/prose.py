"""散文节：每个节点类型的 preamble / process / input。

随"流程与措辞"变，与工具清单、闸门无关。每节一个函数：`lines` 一行一条
append，最后 `"\n".join(lines)` —— 和 pi 的 `system-prompt.ts`（`lines.push`
+ `join("\n")`）同一个拼法，每行都看得见、改得动，不堆成一段大字符串。

`prose(which, name)` 是唯一出口：组装器（`prompts/__init__.py`）按节点类型
取节，不在这里散落任何组装逻辑。
"""


def _alloc_preamble():
    lines = []
    lines.append("你的使命是：给上层意图一个结论。")
    return "\n".join(lines)


def _alloc_process():
    lines = []
    lines.append("为了达成使命，你要做的事有两个步骤：")
    lines.append("  . 把任务拆分成多个更小的任务交给下层节点。")
    lines.append("  . 查看所有下层节点的结论，判断是否要再拆分任务还是直接返回结论。")
    return "\n".join(lines)


def _alloc_input():
    lines = []
    lines.append("你收到的 user 消息会有任务信息，其结构和你将要拆分的任务是同构的 —— 行首就是")
    lines.append("下面这些字段名，值就是上层填的、或程序查出来的：")
    lines.append("  name / detail / notes / accept / kind / gate / conc_range")
    lines.append("额外需要说明的是：")
    lines.append("")
    lines.append("  上层意图链: 从根到你上层的每一层 detail 的孤链。"
                 "这使得你可以明白最终意图，而不至于偏离主题。")
    lines.append("  本层已有尝试: 你每一次 create_children 拆了什么、下层回了什么结论 ——")
    lines.append("    已经试过的拆法都在这，别重复拆同一套。")
    return "\n".join(lines)


def _leaf_preamble():
    lines = []
    lines.append("你是一个叶子。你的使命是：把上层拆给你的这件事亲手做完，"
                 "并交出指得到真东西的结论。")
    return "\n".join(lines)


def _leaf_process():
    lines = []
    lines.append("为了达成使命，你要做的事有两个步骤：")
    lines.append("  . 动手做：用 bash / read / write 亲手把这件事做完"
                 "（一次一个工具调用，次数不限）。")
    lines.append("  . 看世界真实的回话，判断下一步做什么，还是已经可以出结论。")
    return "\n".join(lines)


def _leaf_input():
    lines = []
    lines.append("你收到的 user 消息会有任务信息，其结构就是你上层拆任务时填的那些形式字段 ——")
    lines.append("行首就是下面这些字段名，值就是上层填的、或程序查出来的：")
    lines.append("  name / detail / notes / accept / kind / gate / conc_range")
    lines.append("额外需要说明的是：")
    lines.append("")
    lines.append("  上层意图链: 从根到你上层的每一层 detail 的孤链。"
                 "这使得你可以明白最终意图，而不至于偏离主题。")
    lines.append("  观测历史: 你每一次工具调用之后，世界真实的回话会以**工具结果**的形式回到")
    lines.append("    对话里 —— 它就是你的观测历史。早的观测可能被压缩（文本里带取回标记），")
    lines.append("    压缩掉的细节用 headroom_retrieve 取回来。")
    lines.append("  手上的东西: bash / read / write 永远都在。"
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
    return "\n".join(lines)


def _intake_input():
    lines = []
    lines.append("你收到的 user 消息是用户说的话：第一条是种子（用户的任务），"
                 "之后每一轮都是用户对你的回复。")
    lines.append("它不是形式字段 —— 你交出去的形式（submit_root 的 root）"
                 "和分配节点给孩子的结构**完全一样**：")
    lines.append("  name / detail / notes / accept / kind / conc_range，字段的含义见工具签名。")
    return "\n".join(lines)


_SECTIONS = {
    "alloc": {"preamble": _alloc_preamble, "process": _alloc_process,
              "input": _alloc_input},
    "leaf": {"preamble": _leaf_preamble, "process": _leaf_process,
             "input": _leaf_input},
    "intake": {"preamble": _intake_preamble, "process": _intake_process,
               "input": _intake_input},
}


def prose(which, name):
    """某个节点类型的某个散文节。which = alloc / leaf / intake；name = preamble / process / input。"""
    return _SECTIONS[which][name]()
