"""rules 节：操作纪律（从工具清单推导）+ 协议规则（手写）。

推导部分随工具清单变；手写部分是协议级不变量，对应 `gate.py` 的形状校验。
"""

from ..protocol.fields import INTAKE
from tools import action_names, scope_names


def rules_section(which):
    """rules 节：`which` 节点类型的操作纪律与协议规则。"""
    lines = []
    tools = set(scope_names(which))
    actions = set(action_names())
    if which != INTAKE:
        lines.append("调用工具时可以一次调多个（并行执行），全部完成再继续；"
                     "调不在本层列表里的 → 当场打回。")
        lines.append("已经试过的都记在历史里 —— 别重复撞同一堵墙。")
    if "create_children" in tools:
        lines.append("create_children 除 notes 外全部必填：缺一个或形状不对，"
                     "这次分配会被代码当场退回（原因写回对话）。")
    if "communicate" in tools:
        lines.append("communicate 的 to 只能是 \"parent\" 或你一个孩子的 name"
                     "（原样照抄 create_children 给过的名字）—— 其它会被代码打回。")
        lines.append("做完了就 communicate 给父节点回报结论；做不了也 communicate 说清楚"
                     "卡在哪（开户/入金/留痕这种要人到场的，明说缺什么，别编一个能做的"
                     "假版本代替）。回报要落在对方要求的回复长度区间里（消息里带）。")
        lines.append("父节点发来的消息要回应：追问就答，要求重做就重做，"
                     "让你等就等 —— 不要假装没收到。")
    if tools & actions:
        lines.append("文件与命令操作一律走 bash / read / write —— 签名、超时、"
                     "翻页语义在各自的工具描述里（provider 原样喂给你），这里不重复。")
    if "submit_root" in tools:
        lines.append("submit_root 除 notes 外全部必填，缺一个或形状不对会被当场退回。")
        lines.append("每次调 submit_root，任务都会**当场拿去跑**。跑完你会收到任务根"
                     "发来的消息（进展 / 结论）—— 据此接着谈：把结论讲给用户、"
                     "communicate 回去要求重做、或再开下一个任务。"
                     "谈成什么是什么，跑的结果说了算，不要替它编结论。")
        lines.append("任务根发来的消息要 communicate 回去时，to 用任务根的 name。")
    return "\n".join("· %s" % line for line in lines)
