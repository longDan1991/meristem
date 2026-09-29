/**
 * 纯规则：这条线现在该不该动。调度与恢复共用这一份。
 *
 * 看三件**已经发生的事实**：
 *   1. **最后一条消息是谁说的**：收到话（人的话 / 手的交代）→ 该模型说；模型说完 → 等人。
 *      等待不是结束，也不追加任何上限。
 *   2. **这条线上有没有还没回来的作业**（`hasRunningJob`）：有 → **不动**
 *      —— 作业 settle 时循环会被唤醒（§9.5 的唤醒条件）。
 *   3. **账末是不是“伸出去了、还没回话的手”**（进程崩在起手与结束之间，作业随进程一起没了）：
 *      是 → **停住不推进**（不替它编一条回话 —— 账上不编；要接着干就分叉一条新线）。
 *
 * 出错 / 休眠**不在这条规则里**：那两态推不出来（模型接口失败归人、收手由人给，见 §9.8），
 * 它们靠实际发生的事经 `patch` 落到 props 上。
 *
 * **内部规则**：不上面 —— 界面要的状态读账（`props.state`），调度只在循环里用这一份。
 *
 * 变因：调度规则（"该谁动"的判断算法）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, NodeState } from "./props.ts";

/** 按调度规则该给这条线什么状态（只推得出在动 / 等我）。 */
export declare function stateOf(store: LineStore, node: NodeId, hasRunningJob: boolean): NodeState;

/** 现在该让这条线说话吗（手上有活、或者上一手还没回话，就轮不到它说话）。 */
export declare function actionable(store: LineStore, node: NodeId, hasRunningJob: boolean): boolean;
