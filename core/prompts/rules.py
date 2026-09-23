"""rules 节：操作纪律（从工具清单推导）+ 协议规则（手写）。

推导部分随工具清单变；手写部分是协议级不变量，对应 `gate.py` 的机械校验。
"""

from ..protocol.fields import EXTERNAL_CLASSES, INTAKE
from tools import ACTION_TOOLS, NODE_TOOLS

# `外部需求` 四类的提示文本，从 fields 的词表拼出（改词表这里跟着变）。
_EXTERNAL_HINT = " / ".join(EXTERNAL_CLASSES)


def rules_section(which):
    """rules 节：`which` 节点类型的操作纪律与协议规则。"""
    lines = []
    tools = set(NODE_TOOLS[which])
    if which != INTAKE:
        lines.append("调用工具时可以一次调多个（并行执行），全部完成再继续；"
                     "调不在本层列表里的 → 当场打回。")
        lines.append("已经试过的都记在历史里 —— 别重复撞同一堵墙。")
    if "create_children" in tools:
        lines.append("create_children 除 notes / gate 外全部必填：缺一个或形状不对，"
                     "这次分配会被代码当场退回（原因写回对话）。")
        lines.append("每个子任务的 accept 必须原样带上父/根的可测物理量"
                     "（日期 / 两位以上数字 / 标识符）—— 丢了会被代码拒掉，"
                     "那是把任务换成了别的东西。")
        lines.append("gate 可选、一次最多一个：它是轻重缓急 —— 这件事不先做，"
                     "其余全是白做。想不出作废条件就别标。")
    if "conclude" in tools:
        lines.append("判定「满足」必须指得出具体证据，指不出来会被降级为「未满足」。")
        lines.append("conclude 的 text 落在上层给的 conc_range 区间里。")
        if not tools & set(ACTION_TOOLS):        # 分配节点（自己没有观测）
            lines.append("分配节点自己没有观测：证据只能是子任务的 name（原样照抄一个）"
                         "或磁盘上真存在的产物路径。写「第几次观测」是无效的 —— "
                         "观测只属于叶子。")
    if tools & set(ACTION_TOOLS):
        lines.append("文件与命令操作一律走 bash / read / write —— 签名、超时、"
                     "翻页语义在各自的工具描述里（provider 原样喂给你），这里不重复。")
    if "submit_root" in tools:
        lines.append("submit_root 除 notes / gate 外全部必填，缺一个或形状不对会被当场退回。")
        lines.append("accept 必须带上可测物理量（日期、两位以上数字、标识符如 "
                     "CSV/MA5/hello.txt），否则代码当场退回。这一条是你从对话里谈出来的，"
                     "不是用户交给你的 —— 他确认过就行。")
        lines.append("不用给 gate —— 根没有兄弟，「作废整个分支」对它没有意义。")
        lines.append("每次调 submit_root，任务都会**当场拿去跑**。跑完你会收到一条"
                     "「任务执行结果（系统观测，不是用户说的话）」—— 据此接着谈："
                     "把结论讲给用户，或再开下一个任务。谈成什么是什么，"
                     "跑的结果说了算，不要替它编结论。")
    if which != INTAKE:
        lines.append("反复失败、或需要的动作不在工具里（比如开户/入金/留痕需要人到场），"
                     "就用「阻塞」，把原因写清楚，并指明 external 是哪一类"
                     "（%s）。"
                     "不要编一个你能做的假版本来代替做不到的事。"
                     "「阻塞」只是「这次的条件下没走通」，不是「这条路不行」："
                     "把卡在哪个条件上写清楚，下一代才探测得动。" % _EXTERNAL_HINT)
    return "\n".join("· %s" % line for line in lines)
