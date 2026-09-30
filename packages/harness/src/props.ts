/**
 * 一条线的属性：树里那个不透明的 `props`（**harness 定义，atree 不解释**）。
 *
 * 名字 / 角色 / 做事目录 —— 都是"给人看的那一面"（DESIGN §3），出生时定死。
 *
 * **状态不住这里**：在动 / 等我 是**推出来的**（读账 + 谁在跑就算得出来，见 `plan.ts`），
 * 所以它不进账 —— 落一份进账只会漂：进程一没，账里那句"在动"就成了永远不对的话。
 * 它经 `Event.state` 给人看（重读账时也算得出来）。
 *
 * **没有"出错"态**：错误是一段交代（手给的交代），模型接口失败归人（DESIGN §9.8）。
 * 作业在跑 = 这条线在动（`running` 已经说清楚了）—— 不需要第三种说法。
 *
 * 变因：一条线有哪些人看得见的事实（加一笔、改一笔的含义）。
 */
import type { Store } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import type { WireMessage } from "./shape.ts";

/** 状态：在动 / 等我 / 休眠（前两个推得出来，休眠是人给的 —— 归档那一层落地时才有）。 */
export type NodeState = "running" | "waiting" | "resting";

export interface LineProps {
  /** 人给的名字（或由代码取他第一句的前几个字）—— 不许模型生成摘要冒充它。 */
  readonly name: string;
  /** 这条线用哪块能力（人选的）。 */
  readonly role: RoleId;
  /** 做事的目录：出生时定死（缺省与父同目录）。 */
  readonly outputRoot: string;
}

/** 一条线的账：属性是 `LineProps`，内容是消息。 */
export type LineStore = Store<LineProps, WireMessage>;
