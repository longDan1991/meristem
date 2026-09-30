/**
 * 装配：配置 → 账 → 角色 → 传输 → 树 → 界面，返回退出码。
 *
 * 这是唯一把包拼起来的地方，也是**唯一解释环境的地方**：读一次配置，按各包声明过的需要
 * 分头交过去 —— 这棵树的账文件给 atree（`load(cfg.tree)`）、角色目录与技能根给 roles（装载）、
 * 模型引用 / 端点覆盖 / 钥匙给传输（`createClient`）。harness 的 `start` 只收端口（树 / 角色 / 传输），
 * 一个配置值都不收。
 *
 * **全局一棵树**（DESIGN §7）：没有"挑一棵 / 新开一棵"这回事 —— 打开的就是那一棵，空的也没关系
 * （连根都还没有，人在界面上开第一条线）。造根与新会话都是树上的动作（`tree.fork`），
 * 装配层不经手节点。所以这里做的事只有：把账读出来、把角色装好、把传输接上、把树接上、
 * 把界面交出去，退出时收手（取消在跑的作业 —— 否则父进程一没，那些子进程就成了孤儿）。
 *
 * `HandContext` 不在这里造：手是 harness 起执行时现造的，里面只有两样 —— 这条线的 `outputRoot`
 * 与这次执行所在的 `space`（作业表是 roles 那一块自己维护的内存结构）。所以装配层与作业没有关系。
 *
 * 钥匙只在这里取一次、立刻交给传输层：不进配置对象、不打印值。
 *
 * 失败怎么呈现：**退出码 + 一行话**（缺配置、角色不成立、账读不了都是人要去修的事，
 * 不需要栈），所以这里接住异常并返回 1；界面开着时的失败（模型接口失败）归界面（DESIGN §9.8）。
 *
 * 变因：装配顺序与依赖注入。别的模块都不因它而变。
 */
import { load } from "@meristem/atree";
import type { LineProps, LineStore, WireMessage } from "@meristem/harness";
import { createClient, start as startTree } from "@meristem/harness";
import { get, list, start as startRoles } from "@meristem/roles";
import { mount } from "./app.tsx";
import { parseArgs } from "./cli.ts";
import { loadConfig, loadCredential } from "./config.ts";

export async function main(argv: readonly string[]): Promise<number> {
  let store: LineStore | null = null;
  try {
    const args = parseArgs(argv);
    const cfg = loadConfig();
    // 角色先装：它不成立（xml 有问题 / 声明了没接上的东西）就没必要往下走
    await startRoles(cfg.roleDir, cfg.skillDirs);
    const llm = createClient({
      model: cfg.model,
      ...(cfg.modelId === undefined ? {} : { modelId: cfg.modelId }),
      ...(cfg.baseUrl === undefined ? {} : { baseUrl: cfg.baseUrl }),
      credential: loadCredential(),
    });
    store = await load<LineProps, WireMessage>(cfg.tree);
    const tree = startTree({ store, llm, role: get });
    tree.resume();
    try {
      await mount({ store, tree, roles: list(), workspace: cfg.workspace, at: args.at });
    } finally {
      tree.stop();
    }
    return 0;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    return 1;
  } finally {
    if (store !== null) await store.close();
  }
}
