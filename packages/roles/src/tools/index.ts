/**
 * `tools`：内置手（bash / read / write）—— **共享件**。
 *
 * 每个角色引用它们、只声明"这次要哪些"，不许各写一份实现。
 * 每把手自带三份文字（都在它自己的声明处，单一来源，不漂）：
 *   · `description` —— 语义的唯一来源（schema 那一份，喂给 provider）；
 *   · `snippet`     —— 一行短句，进 system 的 tools 节（模型靠它知道"我有哪些手"）；
 *   · `guidelines`  —— 纪律条目，汇总进 system 的 rules 节（去重）。
 *
 * 一只一只手一个文件（一只手的语义就是一个变因）；作业那三只共享手不在这里，
 * 它们是执行机制的一部分，住 `jobs/hands.ts`。
 *
 * 纪律（DESIGN §5.6）：限制必须说得出来（超时 / 翻页 / 被夹的参数都要写清）。
 *
 * 变因：内置手的目录（有哪些内置手）。
 */
import type { Hand } from "../role.ts";
import { BASH } from "./bash.ts";
import { READ } from "./read.ts";
import { WRITE } from "./write.ts";

export type { BashArgs } from "./bash.ts";
export type { ReadArgs } from "./read.ts";
export type { WriteArgs } from "./write.ts";

/** 内置手的表：角色按名字挑（清单只有这一份）。 */
export const ALL: readonly Hand[] = [BASH, READ, WRITE];

export { BASH, READ, WRITE };
