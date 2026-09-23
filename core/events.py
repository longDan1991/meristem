"""事件出口：把 (type, payload) 按注册顺序分发给消费者。

这是"事件机制"的分发半边，和生命周期词汇（`loop.py` 的 `EventType`）分开住：
词汇跟着生命周期变，机制是通用管道 —— 不 import 词汇、不知道有哪些事件类型。
分开两个文件：只要机制的消费者不被拖进词汇，词汇变了也不用动机制。

同步 fan-out，不是异步队列：
  · 现有消费者全是同步的 —— trace 追加、终端重绘、流式吐字都是同步函数；
  · `message_update` 是热路径（一个模型 token 一发），异步队列白白多付一次
    put/get 的往返，收益为零；
  · 事件循环是单线程，同步 emit 不可能被中途打断 —— 每个 scope 只有一个
    生产者 task，顺序天然保住，不需要锁（AGENTS §9）。

消费者抛错不吞（AGENTS §2）：事件是事实，消费失败就地炸，在最早的点暴露。
"""

from typing import Callable

Consumer = Callable[[str, dict], None]


class EventSink:
    """会话级事件出口。零消费者时 emit 是 no-op；按注册顺序逐个分发。"""

    def __init__(self):
        self._consumers: list[Consumer] = []

    def subscribe(self, consumer: Consumer) -> None:
        """consumer(type, payload) -> None。抛错不吞，就地炸（§2）。"""
        self._consumers.append(consumer)

    def emit(self, type: str, payload: dict) -> None:
        for c in self._consumers:
            c(type, payload)
