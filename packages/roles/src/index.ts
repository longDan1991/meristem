/**
 * `@meristem/roles` 的对外面：**能力**。
 *
 * 只露两个面：
 *   · **LLM 面**：`Role`（`system()` / `hands()`）+ 手的形状（`Hand` / `HandContext`）—— 喂给模型的
 *     和收回来的只有这些；
 *   · **人面**：`start` / `list` / `get` —— 人指一个目录、看清单、挑角色。
 *
 * 另外露**作业**那一块：`Job`（形状）、`settled` / `background`（写一只手要用的底座原语）、
 * `running` / `find` / `all`（只读查询：树算"这条线还有没有活"、界面拿去看）。
 * 作业机制住 `jobs/`，与能力同**块**不同文件 —— 定义只许有一份（DESIGN §8：harness → roles）。
 *
 * 装载、模板填空、技能扫描、MCP 连接、生命周期都在包内部，不导出：它们不是面，是实现。
 */

export type { Hand, HandContext, JsonSchema, Role, RoleId } from "./role.ts";

export type { Job } from "./jobs/job.ts";
export { background, settled } from "./jobs/base.ts";
export { all, find, running } from "./jobs/table.ts";

export { SUMMARY_FORK, get, list, start } from "./registry.ts";
