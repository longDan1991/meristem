"""条件节：`node.gate` / `cfg.COMPRESS` 为真时在场的 skill 全文，触发条件各只有一处定义。"""


def skill_gate():
    """<skill_gate>：你是门槛（node.gate 时在场）。"""
    lines = []
    lines.append("你是门槛：这件事不先做，其余全是白做 —— 你不成立，"
                 "整个分支作废（兄弟全不启动）。")
    lines.append("所以更要给准话：拿不到就说拿不到，不要先报个满足。")
    return "\n".join(lines)


def skill_compression():
    """<skill_compression>：工具结果可能被压、带取回标记（cfg.COMPRESS 且叶子时在场）。"""
    lines = []
    lines.append("你收到的工具结果**可能被压缩过**：压缩文本里带取回标记")
    lines.append("（如 `[N lines compressed to M. Retrieve more: hash=...]`）。")
    lines.append("当你要用的细节不在压缩结果里时，调 headroom_retrieve "
                 "取回完整原文（参数就是标记里的 hash）。")
    lines.append("没看到标记就别调它 —— 那说明内容没被压，全都还在。")
    return "\n".join(lines)
