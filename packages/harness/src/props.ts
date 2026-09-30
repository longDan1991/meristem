/**
 * 一条线的属性：树里那个不透明的 `props`（**harness 定义，atree 不解释**）。
 *
 * 名字 / 角色 / 做事目录 —— 都是"给人看的那一面"（DESIGN §3），出生时定死。
 *
 * **没有"状态"这个东西**：一条线在动还是在等人，读账 + 谁在跑就算得出来（必要时现算，
 * 见 `plan.ts`）—— 存一份进账会漂，发一份给界面也会过时。错误也不是状态：它是一段交代
 * （手给的），模型接口失败归人（DESIGN §9.8）。
 *
 * 变因：一条线有哪些人看得见的事实（加一笔、改一笔的含义）。
 */
import type { Store } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import type { WireMessage } from "./shape.ts";

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
