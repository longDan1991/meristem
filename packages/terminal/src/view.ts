/**
 * 视图：**纯函数** —— 只读账 → 行。不认识账怎么写、不认识事件、不认识 tui。
 *
 * 展示的变因住这一层：树怎么折、选中谁、状态怎么标、一行里放什么字。
 * 颜色 / 布局 / 键位归 `app.tsx`（那头才认识外壳）。
 *
 * 变因：展示（出哪些行、每行标什么）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, NodeState } from "@meristem/harness";
import type { Job } from "@meristem/roles";

/** 行的语义标签：只说"这是什么行"，颜色由 app 定。 */
export type RowTag = "title" | "dim" | "user" | "model" | "thought" | "hand" | "state" | "error";

export interface Row {
  readonly text: string;
  readonly tag: RowTag;
}

/**
 * 树条带：每条线一行 —— **人写的名字 + 角色 + 代码给的状态**（三样都在节点的 `props` 里），
 * 外加**在跑的作业的记号**（这条线手上还有没回来的活）。不在选中路径上、也没有在动的子树
 * 折成一行带节点数。
 */
export declare function treeRows(
  store: LineStore,
  states: (node: NodeId) => NodeState,
  selected: NodeId | null,
  jobs: readonly Job[],
): readonly Row[];

/**
 * 选中那条线的正文：它自己的平铺对话（人 / 模型 / 思考 / 手的过程）+ 正在吐的尾巴。
 *
 * 手的过程画成**卡片**：名字 / 参数 / 已跑多久 / 现在吐了什么（`Job.output()`，尾巴是原始窗口）。
 * 文本一律来自作业自己（`report()` / `output()`）—— 展示层不拼、不猜（DESIGN §9.2 的"面向人"）。
 */
export declare function lineRows(
  store: LineStore,
  node: NodeId,
  tail: readonly Row[],
  jobs: readonly Job[],
): readonly Row[];
