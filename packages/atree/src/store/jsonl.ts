/**
 * 落盘机制（默认实现：一行一条 JSON 的追加文件）。**包内部的东西，外面看不到它。**
 *
 * 机制住这一层，形状不住这里 —— 所以接口名里不出现格式：将来换 sqlite / 内存，
 * `store.ts` 一行都不用改（反正外面只认识 `load(path)`）。
 *
 * 纪律：
 *   · **懒创建**：打开一个还没有内容的路径不会在盘上留空壳，第一次真落盘才建目录与文件；
 *   · 追加只写文件尾巴（`open(path, "a")`），不重写整文件；缓冲区攒够 `FLUSH_BYTES`
 *     或过了 `FLUSH_MS` 落一次，不每条记录都 open / write；
 *   · 读是**流式**的（一块一块切行，不整文件进内存）；崩溃留下的**最后半行**丢掉
 *     （前面已经跑出来的成果一笔都不丢），中间读不动的行由 `replay` 当场炸。
 *
 * **写是同步的**（`writeSync`）：一是错误必须从 `append` 那一刻带着路径炸出来，不能变成
 * 无主的 promise rejection；二是每笔都只是往页缓存里追加一次，量小且被节流，不挡事件循环。
 * 定时落盘那一次（无人 await）失败就是未捕获异常，进程当场死 —— 这是对的，账写不进去不该继续。
 *
 * 变因：持久化机制（格式、分片、落盘节奏、发现）。
 */
import { closeSync, createReadStream, existsSync, mkdirSync, openSync, writeSync } from "node:fs";
import { dirname } from "node:path";
import { encode, type LedgerRecord } from "./record.ts";

/** 攒够这么多字节就落一次盘（不到就等定时器）。 */
const FLUSH_BYTES = 64 * 1024;
/** 有没落盘的内容时最多留这么久。 */
const FLUSH_MS = 200;

/** 内部：一份账文件的读与写。 */
export interface LedgerFile<P, M> {
  append(record: LedgerRecord<P, M>): void;
  /** 流式重放：一次一块切行。 */
  read(): AsyncIterable<string>;
  /** 缓冲落盘并放手。 */
  close(): Promise<void>;
}

/** 同一份账只允许一个写者（两个 fd 交错追加 = 静默写坏，所以这里当场拦）。 */
const writing = new Set<string>();

/** 内部：指向某个路径的一份账（此刻不碰盘）。 */
export function openFile<P, M>(path: string): LedgerFile<P, M> {
  if (writing.has(path)) throw new Error(`这份账已经打开了（同一份账只能有一个写者）：${path}`);
  writing.add(path);

  let fd: number | null = null;
  let pending: string[] = [];
  let bytes = 0;
  let timer: NodeJS.Timeout | null = null;
  let closed = false;

  function flush(): void {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    if (pending.length === 0) return;
    const chunk = pending.join("");
    pending = [];
    bytes = 0;
    try {
      if (fd === null) {
        mkdirSync(dirname(path), { recursive: true });
        fd = openSync(path, "a");
      }
      writeSync(fd, chunk);
    } catch (cause) {
      throw new Error(`账落盘失败：${path}`, { cause });
    }
  }

  async function* read(): AsyncGenerator<string> {
    if (closed) throw new Error(`这份账已经关了，不能再读：${path}`);
    if (!existsSync(path)) return;
    let tail = "";
    for await (const chunk of createReadStream(path, { encoding: "utf8" })) {
      const lines = (tail + chunk).split("\n");
      tail = lines.pop() ?? "";
      for (const line of lines) yield line;
    }
    // `tail` 非空 = 最后一笔没写完（崩在第几笔上就丢第几笔，前面的照收）。
  }

  return {
    append(record) {
      if (closed) throw new Error(`这份账已经关了，不能再写：${path}`);
      const line = `${encode(record)}\n`;
      pending.push(line);
      bytes += Buffer.byteLength(line);
      if (bytes >= FLUSH_BYTES) {
        flush();
        return;
      }
      if (timer === null) {
        timer = setTimeout(() => {
          timer = null;
          flush();
        }, FLUSH_MS);
        timer.unref();
      }
    },

    read,

    async close() {
      if (closed) return;
      closed = true;
      flush();
      if (fd !== null) {
        closeSync(fd);
        fd = null;
      }
      writing.delete(path);
    },
  };
}
