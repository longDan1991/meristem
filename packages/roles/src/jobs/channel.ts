/**
 * 把回调式的产出变成 `AsyncIterable`：**bash / MCP 手共用的那座小桥**。
 *
 * 底座的原语要 `AsyncIterable<string>`（它自己始终在消费），而 pi-natives 的 shell 与 MCP 的
 * 传输都给的是回调（`onChunk` / `onmessage`）。这座桥收一边、放一边。
 *
 * 它是**单消费者**的（底座就是那唯一的消费者），队列因此只可能因为"生产者比消费者快"短暂积压；
 * 消费者提前停了（超时 / 取消后底座不再取）时 `return()` 会把桥关掉，之后的 `push` 直接丢掉 ——
 * 不许留一个没人取、还在涨的队列（§11）。
 *
 * 变因：回调 → 异步流的适配（只有这一份，别在每只手里各写一遍）。
 */

export interface Channel<T> {
  /** 给底座的那一面。 */
  readonly stream: AsyncIterable<T>;
  /** 生产这一面：来一块放一块。 */
  push(value: T): void;
  /** 不会再有新块了。 */
  close(): void;
}

export function channel<T>(): Channel<T> {
  const queue: T[] = [];
  let closed = false;
  let waiting: ((result: IteratorResult<T>) => void) | null = null;

  const stream: AsyncIterable<T> = {
    [Symbol.asyncIterator]() {
      return {
        next(): Promise<IteratorResult<T>> {
          const value = queue.shift();
          if (value !== undefined) return Promise.resolve({ value, done: false });
          if (closed) return Promise.resolve({ value: undefined, done: true });
          const { promise, resolve } = Promise.withResolvers<IteratorResult<T>>();
          waiting = resolve;
          return promise;
        },
        return(): Promise<IteratorResult<T>> {
          closed = true;
          queue.length = 0;
          return Promise.resolve({ value: undefined, done: true });
        },
      };
    },
  };

  return {
    stream,
    push(value: T): void {
      if (closed) return;
      const resolve = waiting;
      if (resolve !== null) {
        waiting = null;
        resolve({ value, done: false });
        return;
      }
      queue.push(value);
    },
    close(): void {
      closed = true;
      const resolve = waiting;
      waiting = null;
      resolve?.({ value: undefined, done: true });
    },
  };
}
