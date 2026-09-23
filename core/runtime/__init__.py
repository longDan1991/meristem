"""运行时：一棵树 + 一个 Loop。

- `store`     一场会话的存储（树 + 落盘记录）：唯一写者，写入即账
- `dialogue`  一个节点的平铺对话 + 线上 wire 的配对规范化
- `plan`      纯规则：这个节点现在该不该跑（`actionable`）
- `tools`     `@mcp.tool` 工具实现（模型与程序之间唯一的通道）
- `loop`      唯一的控制流：扫活跃节点 → 调 LLM / 异步跑工具 → 折回结果

这一层因**机制**而变（并发、落盘、恢复），不因协议字段而变。
"""


def deliver(fut, task):
    """把一次异步任务的结果 / 异常原样搬到另一个 future 上（ChatPool 用）。

    不吞、也不让消费者 task 死掉（消费者死了，后面排队的人就永远等不到）。
    """
    if fut.done():
        return
    if task.cancelled():
        fut.cancel()
    elif task.exception() is not None:
        fut.set_exception(task.exception())
    else:
        fut.set_result(task.result())
