"""事件出口：把 (type, payload) 按注册顺序分发给消费者。

这是通用管道，不知道有哪些事件类型（生命周期词汇不在这里），所以词汇变了不用动机制。

同步 fan-out：消费者全是同步函数，`message_update` 是热路径（一 token 一发），
异步队列只会白付一次 put/get；事件循环单线程、每个 scope 只有一个生产者，顺序天然保住、无需锁。

消费者抛错不吞：事件是事实，消费失败就地炸。
"""

from typing import Callable

Consumer = Callable[[str, dict], None]


class EventSink:
    """会话级事件出口。零消费者时 emit 是 no-op；按注册顺序逐个分发。"""

    def __init__(self):
        self._consumers: list[Consumer] = []

    def subscribe(self, consumer: Consumer) -> None:
        """consumer(type, payload) -> None；抛错不吞，就地炸。"""
        self._consumers.append(consumer)

    def emit(self, type: str, payload: dict) -> None:
        for c in self._consumers:
            c(type, payload)
