/**
 * 事件出口：唯一通知面 —— 长得出来的只有这几件事，多一个都不发。
 *
 * 事件是"给看得见的人看"的：代码给的状态、流式吐字、手的过程（作业）、用量、模型接口失败。
 * 手自己没有"说话"事件：它要跟人说话只有两个口子，都在作业上（尾巴给人看、交代给模型）——
 * 单一来源，不给手第二个出口。
 * 这里没有"向上汇报"：系统没有上层，只有一个人（DESIGN §5.1 / §5.7）。
 *
 * **事件不是账**：事件说"去看账"（界面据此重读 `Store` 重画），账才是真相。
 * 作业那三个事件只带**结构**（作业 id、字节数、秒数），文本一个字都不带 ——
 * 界面要看字就去问作业（`Job.report()` / `Job.output()`，DESIGN §9.2 的"面向人"）。
 *
 * 这个 sink 是 **harness 的内部机制**：对外的那一面是 `Loop.subscribe`（操作与事件是同一个
 * 对象的两个方向）。所以别处不要注入 sink —— 事件的出口只有一处，订阅者从 `Loop` 上收。
 *
 * 变因：终端要看得见什么。加事件 = 改这份清单 + 消费它的那一处。
 */
import type { NodeId } from "@meristem/atree";
import type { Usage } from "./shape.ts";
import type { NodeState } from "./props.ts";

export type Event =
  /** 代码给的状态（不是发言者的自我描述）：在动 / 等我 / 休眠。 */
  | { readonly type: "state"; readonly node: NodeId; readonly state: NodeState }
  /** 一条线正在吐的字：正文与思考两条通道分开。 */
  | {
      readonly type: "message";
      readonly node: NodeId;
      readonly channel: "text" | "thought";
      readonly delta: string;
    }
  /** 一只手伸出去（作业起了）：`job` 是它的稳定名字，界面据此画那张手卡片。 */
  | {
      readonly type: "hand_start";
      readonly node: NodeId;
      readonly name: string;
      readonly args: unknown;
      readonly job: string;
    }
  /** 作业还在跑时的**节流**进度（不是每次吐字都发）：界面据此重画那张卡片。 */
  | {
      readonly type: "job_progress";
      readonly node: NodeId;
      readonly job: string;
      readonly bytes: number;
      readonly secs: number;
    }
  /** 作业结束（交代已经进账）；`secs` 是它跑了多久。 */
  | {
      readonly type: "hand_end";
      readonly node: NodeId;
      readonly name: string;
      readonly job: string;
      readonly secs: number;
    }
  | { readonly type: "usage"; readonly node: NodeId; readonly usage: Usage }
  /**
   * **模型接口失败**（不是任何一手的事）：不入 msgs、不推进、不自动重试，只交给界面
   * （红字 + 重试命令）。它进不了账 —— 那条线手里的事实没有变（DESIGN §9.8）。
   */
  | { readonly type: "transport_error"; readonly node: NodeId; readonly error: Error };

export interface EventSink {
  emit(event: Event): void;
  /** 订阅；返回退订函数。分发顺序 = 注册顺序。 */
  subscribe(consumer: (event: Event) => void): () => void;
}

export declare function createSink(): EventSink;
