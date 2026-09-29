/**
 * 手：`bash` —— 起一条命令，跑在 pi-natives 的进程内 shell 上（不 fork / exec 系统二进制）。
 *
 * 它是**作业**（DESIGN §9.3）：用底座的 `background(...)` 包一次执行（命令可能跑几分钟）。
 * **时间纪律**（§9.9）：schema 里收 `timeout`（模型自己写的命令，它比谁都清楚这条要多久），
 * 缺省值写进 `description`；无论走哪条路，起执行时都会给底座一个值（`0` = 明说无限期）。
 * 被停掉时，交代里要说清"你写的多少、实际按多少、怎么跑更久"（§5.6 的限制必须说得出来）。
 *
 * 输出**全量**留着（它就是正常结束时的交代）：尾巴只是给人看的窗口，不是交付。
 * 命令自己吐出来的东西不该因为"只留了个窗口"而丢。
 *
 * 变因：这一只手的语义与实现。
 */
import { executeShell } from "@oh-my-pi/pi-natives";
import type { Hand } from "../role.ts";
import { background, message, settled } from "../jobs/base.ts";
import { channel } from "../jobs/channel.ts";
import { resolvePath } from "./paths.ts";

export interface BashArgs {
  readonly command: string;
  /** 换目录用 `cwd`，不要 `cd`；相对路径落在这条线的输出根下。 */
  readonly cwd?: string;
  /**
   * 秒；`0` = 不限。模型按命令的预期给（编译 / 测试 / 装依赖类就该写大一点）。
   * 不写就用 `description` 里写着的缺省值；被停掉时交代里会写出"你写的多少、实际按多少"。
   */
  readonly timeout?: number;
}

/** 不写 `timeout` 时按这个（秒）—— 同一个数写在 `description` 里给模型看。 */
const DEFAULT_TIMEOUT = 120;

export const BASH: Hand = {
  name: "bash",
  description:
    "起一条命令，跑在本进程内的 shell 上（不另外唤醒系统的 shell 程序）。\n" +
    "· cwd：工作目录；相对路径落在你这棵树的输出根下。换目录用它，别在命令里 cd（cd 只在那条命令里有效）。\n" +
    `· timeout：秒；不写就是 ${DEFAULT_TIMEOUT} 秒，0 = 不限。你比谁都清楚这条要多久：` +
    "编译 / 测试 / 装依赖就写大一点。到点会被杀掉，交代里会说清跑了多久、被杀、怎么跑更久。\n" +
    "· 输出：全量进交代（跑出多少就是多少，不截断）；跑的过程中你可以自己 job_output 看尾巴。\n" +
    "· 退出码非 0 不等于这次调用失败 —— 交代里写着 exit <码>，你自己判断。",
  schema: {
    type: "object",
    properties: {
      command: { type: "string", description: "要跑的命令（shell 语法）" },
      cwd: { type: "string", description: "工作目录（相对路径落在这条线的输出根下）" },
      timeout: {
        type: "integer",
        description: `秒；缺省 ${DEFAULT_TIMEOUT}，0 = 不限`,
      },
    },
    required: ["command"],
    additionalProperties: false,
  },
  snippet: "起一条 shell 命令（本进程内的 shell，可能跑很久）",
  guidelines: [
    "命令可能跑很久：预期久的（编译 / 装依赖 / 跑测试）自己写更大的 timeout（0 = 不限），别让它被缺省值杀掉。",
    "别用 `&` / `nohup` 把命令丢到后台：那等于这次执行立刻结束，它的产出再也回不来。",
  ],
  async run(args: unknown, ctx) {
    const { command, cwd: givenCwd, timeout } = args as BashArgs;
    if (timeout !== undefined && (!Number.isFinite(timeout) || timeout < 0)) {
      return settled(
        { space: ctx.space, name: "bash" },
        `bash 没能起：timeout 要是 ≥ 0 的秒数（收到 ${JSON.stringify(timeout)}）。` +
          `按缺省 ${DEFAULT_TIMEOUT} 秒重来，或写 0 = 不限。`,
      );
    }
    const cwd = givenCwd === undefined ? ctx.outputRoot : resolvePath(ctx.outputRoot, givenCwd);

    const chunks = channel<string>();
    const abort = new AbortController();
    let produced = "";
    let streamFailure: Error | null = null;

    const done = executeShell(
      { command, cwd, signal: abort.signal },
      (error, chunk) => {
        if (error !== null) {
          streamFailure ??= error;
          return;
        }
        produced += chunk;
        chunks.push(chunk);
      },
    ).then(
      (result) => {
        chunks.close();
        if (streamFailure !== null) throw streamFailure;
        return compose(command, result.exitCode, result.workingDir ?? cwd, produced);
      },
      (error: unknown) => {
        // 起都起不来（cwd 不存在之类）也是交代：说清是在哪儿起的，别让模型猜。
        chunks.close();
        throw new Error(`没能起这条命令（cwd=${cwd}）：${message(error)}`);
      },
    );

    return background({
      space: ctx.space,
      name: "bash",
      chunks: chunks.stream,
      done,
      stop: () => abort.abort(),
      timeout: timeout ?? DEFAULT_TIMEOUT,
      timeoutArg: "timeout",
    });
  },
};

/** 正常结束时的交代：命令、输出原文、结局一行（§5.2：事实说清楚，不加工）。 */
function compose(command: string, exitCode: number | undefined, cwd: string, output: string): string {
  const body = output.replace(/\n+$/, "");
  const ending = exitCode === undefined ? "被中断（没有退出码）" : `exit ${exitCode}`;
  return `$ ${command}\n${body === "" ? "（没有输出）" : body}\n（${ending}；cwd=${cwd}）`;
}
