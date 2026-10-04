/**
 * 作业表：**模块级内存结构，Job 机制自己维护**（不靠外面传进来，也没有回调）。
 *
 * 它不关心节点、消息、角色 —— 只认两样：作业 id 与 `space`（筛选用）。
 * 里面放的是**还在跑的作业**：一结束（或被人取消）就摘掉 —— 交代已经进账、输出不再有人要，
 * 所以它天然有界（§3 不许无界缓存）。
 *
 * 登记与摘除都由底座做（`base.ts`，也就是 `Hand.run` 内部）：手不用自己往表里放东西，
 * 树也不写这张表。外面**只读**：`job_list` 按 `space` 筛、树算"这条线还有没有活"、界面拿去看。
 *
 * **查询一律带空间**：`find` / `running` 都要 `space` —— 这是"只有这条线上起的作业在列"
 * 那条规则的下限（从父线继承下来的消息里提到过的作业不在你这个空间里）。
 *
 * 变因：作业的登记与发现（内存结构本身）。
 */
import type { Job } from "./job.ts";

/** space → (id → 作业)；内层 Map 保持出生顺序。 */
const bySpace = new Map<string, Map<string, Job>>();

/** 登记（底座在造出**还在跑**的作业时调）。 */
export function register(job: Job): void {
  let bucket = bySpace.get(job.space);
  if (bucket === undefined) {
    bucket = new Map();
    bySpace.set(job.space, bucket);
  }
  bucket.set(job.id, job);
}

/** 摘除（底座在作业结束 / 被取消时调；重复摘除是允许的）。 */
export function retire(job: Job): void {
  const bucket = bySpace.get(job.space);
  if (bucket === undefined) return;
  bucket.delete(job.id);
  if (bucket.size === 0) bySpace.delete(job.space);
}

/** 某个空间里还在跑的作业（出生顺序）。 */
export function running(space: string): readonly Job[] {
  const bucket = bySpace.get(space);
  return bucket === undefined ? [] : [...bucket.values()];
}

/** 在这个空间里按 id 找一个还在跑的作业；没有就 `null`（`job_output` / `job_cancel` 用它）。 */
export function find(space: string, id: string): Job | null {
  return bySpace.get(space)?.get(id) ?? null;
}

/** 全部（所有空间里还在跑的）—— 给界面用。 */
export function all(): readonly Job[] {
  return [...bySpace.values()].flatMap((bucket) => [...bucket.values()]);
}
