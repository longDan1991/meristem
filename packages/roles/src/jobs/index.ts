/**
 * `jobs`：作业这一块的对外面（本包其它模块与 harness 用它）。
 *
 * 这一块自己不关心节点 / 消息 / 角色 —— 只认 `space`（筛选用）与作业事实。
 *
 * 分五个文件，各有各的变因：
 *   · `job.ts`     -- `Job` 的形状（一手伸出去之后世界的样子）；
 *   · `table.ts`   -- 作业表（模块级内存结构：登记 / 摘除 / 按空间筛）；
 *   · `channel.ts` -- 回调 → 异步流的小桥（bash / MCP 手共用，底座只认 `AsyncIterable`）；
 *   · `base.ts`    -- 底座原语（把执行包成作业）+ 进度与"已多久"的说法；
 *   · `hands.ts`   -- 模型侧那三只共享手。
 */

export { background, settled, message, elapsed, progress, type BackgroundInput } from "./base.ts";
export { JOB_CANCEL, JOB_HANDS, JOB_LIST, JOB_OUTPUT } from "./hands.ts";
export type { Job, JobFacts } from "./job.ts";
export { all, find, register, retire, running } from "./table.ts";
