/**
 * 底座：把一次执行包成 `Job` 的**两个原语**（手只用这两个，不许各写一份）。
 *
 * 底座负责：
 *   · 给 id 与出生时刻，记下 `space` / `name`；
 *   · **登记进作业表**（`table.ts`）—— 手不用自己往表里放东西；
 *   · 还在跑时的进度句（`report()` 的默认说法：作业 #id、名字、已多久、吐了多少）；
 *   · 结束 / 取消时摘除登记，并把结局写成交代。
 * 它不认识这只手在干什么 —— 那在 `name` 与传进来的文本里。
 *
 * **结尾那几句话由底座写**（超时 / 被人取消 / 失败），因为它们都是底座自己造成的事实；
 * 手只写"正常结束时的交代"。三种结尾都会把**尾巴**带上：跑了一半的输出不该因为
 * 超时或取消就从模型眼前消失（§5.6：限制必须说得出来）。
 *
 * 变因：把执行包成作业的机制（计时、尾巴、登记）。
 */
import type { Job, JobFacts } from "./job.ts";
import { register, retire } from "./table.ts";

/** 尾巴窗口：头尾各留这么多字（中间的原文由手自己的交代负责带出来）。 */
const WINDOW = 2000;

/** 错误的说法（四处共用的唯一一份）。 */
export function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** "已多久"的说法（`report()` 与 `job_list` 共用一份）。 */
export function elapsed(ms: number): string {
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m${Math.round(seconds - minutes * 60)}s`;
  return `${Math.floor(minutes / 60)}h${minutes % 60}m`;
}

/** 进度句：`已 3.2s，吐了 120 字`（作业自己说的话，别处不拼）。 */
export function progress(job: Job): string {
  return `已 ${elapsed(Date.now() - job.at)}，吐了 ${job.produced()} 字`;
}

/**
 * 原语一：包一个"已经开始、且立刻/很快结束"的执行。
 *
 * `read` / `write` 这类用它（它们同步算完，所以交出来的是一句**已经写好的**文本），
 * 语义一行都不用改（DESIGN §9.3 的"同步的手零负担"）。
 * 传进来的 promise 就是这一手的交代（错误也走这里：它只是交代，不是特殊的失败状态）。
 */
export function settled(facts: JobFacts, execution: string | Promise<string>): Job {
  const id = nextId();
  const at = Date.now();
  const { promise: waited, resolve: land } = Promise.withResolvers<void>();
  let finished = false;
  let final = "";

  const job: Job = {
    id,
    space: facts.space,
    name: facts.name,
    at,
    produced: () => 0,
    report: () =>
      finished ? final : `作业 #${id}（${facts.name}）还在跑：${progress(job)}`,
    output: () => "",
    cancel: () => {},
    wait: () => waited,
  };

  const settle = (text: string): void => {
    if (finished) return;
    finished = true;
    final = text;
    land();
  };

  if (typeof execution === "string") settle(execution);
  else void execution.then(settle, (error: unknown) => settle(`${facts.name} 失败：${message(error)}`));

  // 立刻结束的执行不进作业表：表里只放"还在跑"的（DESIGN §9.2）。
  return job;
}

/** 一次"起进程 / 发请求、之后才回来"的执行。 */
export interface BackgroundInput extends JobFacts {
  /** 输出的块：底座**始终在消费**它，泵进有界尾巴（头 + 尾窗口）—— 没人读也不许反向背压。 */
  readonly chunks: AsyncIterable<string>;
  /** 等它结束；resolve 的值 = **最终交代**（正常结束的那个说法，从这一条回来）。 */
  readonly done: Promise<string>;
  /** 停：**必须真停**（杀整棵进程树 / 断连）。`cancel()` 与超时都走它 —— 停不住是实现缺陷。 */
  readonly stop: () => void;
  /**
   * 时长上限（秒）：`0` = 明说无限期。**必给**（没有默认参数）—— 强制的不是某个数值，
   * 而是"没有'忘了'这个状态"（DESIGN §9.9）。到点时底座调 `stop()`。
   */
  readonly timeout: number;
  /**
   * 这只手收时间参数用的键名（bash 的 `timeout`）—— 超时交代里要告诉模型"怎么跑更久"。
   * 没有时间参数的手（MCP 服务给的 schema 我们改不了）不给它：那时交代里说的是
   * "这只手没有自己的时间参数，统一按 N 秒杀"（DESIGN §9.9 第三层，必须说出来）。
   */
  readonly timeoutArg?: string;
}

/**
 * 原语二：包一次"起之后才回来"的执行（`bash` / MCP 手用它）。
 *
 * 底座的活儿：泵 `chunks` 进有界尾巴（`output()` 取）、按 `timeout` 计时、把 `cancel()` 接到
 * `stop()`、`done` 落地时把结局写成交代、还在跑时让 `report()` 说得出进度。
 */
export function background(input: BackgroundInput): Job {
  const id = nextId();
  const at = Date.now();
  const window = new Tail();
  const { promise: waited, resolve: land } = Promise.withResolvers<void>();
  let finished = false;
  let final = "";

  const job: Job = {
    id,
    space: input.space,
    name: input.name,
    at,
    produced: () => window.produced,
    report: () => (finished ? final : `作业 #${id}（${input.name}）还在跑：${progress(job)}`),
    output: () => window.text(),
    cancel: () => {
      if (finished) return;
      input.stop();
      settle(`作业 #${id}（${input.name}）：被人取消了（已跑 ${elapsed(Date.now() - at)}）。${tail()}`);
    },
    wait: () => waited,
  };

  const tail = (): string =>
    window.produced === 0 ? "" : `\n到此刻吐了 ${window.produced} 字。\n--- 尾巴 ---\n${window.text()}`;

  const settle = (text: string): void => {
    if (finished) return;
    finished = true;
    final = text;
    clearTimeout(timer);
    retire(job);
    land();
  };

  const timer =
    input.timeout > 0
      ? setTimeout(() => {
          input.stop();
          const how =
            input.timeoutArg === undefined
              ? `这只手没有自己的时间参数，统一按 ${input.timeout} 秒杀`
              : `要跑更久就把 ${input.timeoutArg} 写大些（0 = 不限）`;
          settle(`作业 #${id}（${input.name}）：跑了 ${input.timeout} 秒还没结束，把它杀了；${how}。${tail()}`);
        }, input.timeout * 1000)
      : undefined;

  register(job);
  void pump();
  void collect();

  async function pump(): Promise<void> {
    try {
      for await (const chunk of input.chunks) {
        window.push(chunk);
        if (finished) break;
      }
    } catch (error) {
      // 产出这条线自己断了：不掩盖，它就是这个作业的结局。
      if (!finished) {
        input.stop();
        settle(`作业 #${id}（${input.name}）失败：产出没了 —— ${message(error)}${tail()}`);
      }
    }
  }

  async function collect(): Promise<void> {
    const outcome = await input.done.then(
      (text) => ({ ok: true as const, text }),
      (error: unknown) => ({ ok: false as const, error }),
    );
    // 超时 / 取消先到时结局已经定了：手后来那句交代弃用（它的尾巴已经进过账）。
    if (finished) return;
    settle(
      outcome.ok
        ? outcome.text
        : `作业 #${id}（${input.name}）失败：${message(outcome.error)}${tail()}`,
    );
  }

  return job;
}

/** 有界尾巴：头 + 尾两段原文，中间省略多少字说得出来（`output()` 的唯一来源）。 */
class Tail {
  private head = "";
  private peak = "";
  private count = 0;

  push(chunk: string): void {
    this.count += chunk.length;
    let rest = chunk;
    if (this.head.length < WINDOW) {
      const room = WINDOW - this.head.length;
      this.head += rest.slice(0, room);
      rest = rest.slice(room);
    }
    if (rest.length > 0) this.peak = (this.peak + rest).slice(-WINDOW);
  }

  get produced(): number {
    return this.count;
  }

  text(): string {
    const shown = this.head.length + this.peak.length;
    if (this.count <= shown) return this.head + this.peak;
    return `${this.head}\n…（这里省略 ${this.count - shown} 字）…\n${this.peak}`;
  }
}

let sequence = 0;

/** 作业的稳定名字：短、可读、进程内不重复（账里给人看的那行就用它）。 */
function nextId(): string {
  sequence += 1;
  return `${sequence.toString(36)}${Math.random().toString(36).slice(2, 5)}`;
}
