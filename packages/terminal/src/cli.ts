/**
 * 命令行：只有一个动作 —— 打开那棵树（全局只有一棵），可选地指出**人一开始站在哪个节点上**。
 *
 * 没有"新会话 / 接着哪个会话"：**新会话就是根的一个子节点**（界面上的一次分叉），
 * 树一直在那儿，`--at` 缺省就站在根；之后从哪儿接着看是运行中切节点的事。
 * 配置在 terminal 的 `config.ts` 里解释（`.env` / 环境变量说了算），这里不碰。
 *
 * 变因：命令行界面。
 */
import type { NodeId } from "@meristem/atree";
import { main } from "./main.ts";

export interface Args {
  /** 一开始站在哪个节点上；`null` = 根（树的入口）。 */
  readonly at: NodeId | null;
}

/**
 * 只认 `--at <节点>`；没给就站根。
 *
 * `-h` / `--help` **不在这里认**：解析只回一份 `Args`（里面没有"要不要打印用法"这个字段），
 * 而打印是 IO、还得知道用法那句话 —— 那是入口的事（入口先看一眼再叫这里）。所以走到这里还带 `-h`，
 * 它就是"不认识的选项"：不解析、不静默忽略（拼错的选项不该被当成没写）。
 */
export function parseArgs(argv: readonly string[]): Args {
  let at: NodeId | null = null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--at") {
      const value = argv[index + 1];
      if (value === undefined || value === "") throw new Error("--at 后面要跟一个节点 id");
      at = value;
      index += 1;
    } else {
      throw new Error(`不认识的选项：${arg ?? ""}（只认 --at；用法看 -h）`);
    }
  }
  return { at };
}

/** 一行用法（中文）：说清 `--at` 是什么，以及"新会话"在这棵树里是怎么发生的。 */
const USAGE =
  "用法：meristem [--at <节点>] —— --at 指定一开始站在哪个节点（缺省站在树的根）；新会话 = 以根为父的一次分叉";

/** 作为 bin 跑起来：`-h` / `--help` 只打印这一行就收 —— 不碰配置、不开树；其余交给装配层。 */
if (import.meta.main) {
  const argv = process.argv.slice(2);
  if (argv.includes("-h") || argv.includes("--help")) {
    console.log(USAGE);
    process.exit(0);
  }
  process.exit(await main(argv));
}
