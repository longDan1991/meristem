"""运行时层：把协议跑成一棵树。

基础设施（各占一个文件）：

  - `store`    一场会话的存储（一个 Store 对象）：roots / load / new / node / put（写入自动落盘）
  - `hands`    节点的三只手（bash / write 串行执行）
  - `loop`     一条消息循环的骨架（问模型 / 跑工具 / 写对话 / 发事件）

决策与恢复：

  - `turn`       一个节点的一回合：问模型 → 过闸门 → 工具动作（bash/read/write）或分配
  - `scheduler`  广度优先、并行扇出、门槛 —— 树怎么长
  - `reconcile`  调度器与恢复共用的纯编排逻辑（该不该跑 / 孩子怎么结算）
  - `intake`     入口节点（kind="intake"）的三处语义

这一层因**机制**而变（并发、落盘、调度、恢复），不因协议字段而变。

`deliver` 是这一层共用的 future 交付件：ChatPool（llm.py）和 Hands（hands.py）
各用一份同样的 —— 不各自抄。
"""


def deliver(fut, task):
    """把一次异步任务的结果 / 异常原样搬到另一个 future 上。

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
