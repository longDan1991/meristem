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

export interface Args {
  /** 一开始站在哪个节点上；`null` = 根（树的入口）。 */
  readonly at: NodeId | null;
}

export declare function parseArgs(argv: readonly string[]): Args;
