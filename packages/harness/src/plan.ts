/**
 * 纯规则：这条线现在该不该动。调度与恢复共用这一份。
 *
 * 看三件**已经发生的事实**：
 *   1. **最后一条消息是谁说的**：收到话 → 该模型说；模型说完 → 等人
 *      （`user` 是人的话或手的交代，`tool` 是起手那条回话 —— 它后面要么还有在跑的作业
 *      （下一件事实把它挡住），要么就没什么再来了）。等待不是结束，也不追加任何上限。
 *   2. **这条线上有没有还没回来的作业**（`hasRunningJob`）：有 → **不动**
 *      —— 作业 settle 时这条线会被叫一声（§9.5 的唤醒条件）。
 *   3. **账末是不是"伸出去了、还没回话的手"**（进程崩在起手与结束之间，作业随进程一起没了）：
 *      是 → **停住不推进**（不替它编一条回话 —— 账上不编；要接着干就分叉一条新线）。
 *
 * **出错不在这条规则里**：模型接口失败是内存里的一件事（§9.8：账里一个字都不多，也不自动重试），
 * 由树自己记住（只在内存里）、由人重试。**休眠**不是这一层的状态：归档落地时再谈（§7）——
 * 那时它也是人给的既成事实，不是推出来的。
 *
 * `stateOf` 是**给界面看的**（事件）：树的推进只看 `actionable` ——
 * 状态不进账、也不当判据，不给自己留第二份真相。
 *
 * **内部规则**：不上面 —— 状态经事件给界面，调度只在树里用这一份。
 *
 * 变因：调度规则（"该谁动"的判断算法）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, NodeState } from "./props.ts";
import type { WireMessage } from "./shape.ts";

/** 按事实该给这条线什么状态（只推得出在动 / 等我）—— 给界面看，不当判据。 */
export function stateOf(store: LineStore, node: NodeId, hasRunningJob: boolean): NodeState {
  if (hasRunningJob) return "running";
  return actionable(store, node, hasRunningJob) ? "running" : "waiting";
}

/** 现在该让这条线说话吗（手上有活、或者最后一句不是别人说的，就轮不到它说话）。 */
export function actionable(store: LineStore, node: NodeId, hasRunningJob: boolean): boolean {
  if (hasRunningJob) return false;
  const messages = store.content(node);
  const last = messages.at(-1);
  if (last === undefined) return false;
  if (last.role === "assistant" || last.role === "system") return false;
  return !danglingHand(messages);
}

/**
 * 这条线里有没有"伸出去了、还没回话的手"（重启后留下的未完成区）。
 *
 * 判据是形状：任何一条带 `tool_calls` 的 assistant 后面，**紧跟着的必须是它的回话**。
 * 一旦有一条没有，这条线**整条停住** —— 包括人后来说了话也不推进：账上不编那条回话
 * （编了就分不清哪句是手说的），要接着干就分叉一条新线。
 */
function danglingHand(messages: readonly WireMessage[]): boolean {
  return messages.some(
    (message, index) =>
      message.role === "assistant" &&
      (message.toolCalls?.length ?? 0) > 0 &&
      messages[index + 1]?.role !== "tool",
  );
}
