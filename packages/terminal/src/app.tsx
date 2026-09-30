/**
 * 应用：订阅事件 + 用 tui 的组件装出一屏 + 收人的动作。
 *
 * 人的动作只有三个**写账**的：**说话**（选中哪条线就投给哪条线）、**分叉**（从选中的线分出新的一条，
 * 分叉时挑角色）、**收手**；外加一个**本地**动作：**切节点**（改"我站在哪"，只影响选中与渲染，
 * 不写账）。三者全落在 `Tree` 上，别处不另开写账的口子。不做"给模型看的输入"：人的话就是账里的
 * 一条 user 消息。
 *
 * **照看两件事**（都是"面向人"的动作，DESIGN §9.2）：
 *   · **取消一个作业**：作用在"选中线上那张**选中的手卡片**"上（在线上的作业里选，缺省选最近一个在跑的）；
 *   · **重试**：只在界面上有红字（模型接口失败）时有效 —— `Tree.retry(node)` 把那条线放回推进。
 * 两个都只转发，不在界面里编语义：作业的文本一律来自 `Job.report()` / `Job.output()`
 * （事件只带结构：作业 id、字节数、秒数）。
 *
 * **全局一棵树**（DESIGN §7）：树一直在这儿，所以没有"新会话 / 接着哪个会话"这回事 ——
 * **新会话 = 以根为父的一次分叉**（界面上一个动作）；造根 = 一次"没有父的分叉"，全局只发生一次。
 * 从哪儿接着看 = 切节点（`--at` 是它的启动形式）。
 *
 * 读账直接读 `Store`（渲染树、画一条线）—— 名字 / 角色 / 状态 / 做事目录都在节点的 `props` 里
 * （那是 harness 定的形状），一条线自己的对话在它的内容里。事件从 `Tree.subscribe` 来，
 * 它只是"去看账 / 去看作业"的提示（`state` / `message` / `hand_start` / `job_progress` /
 * `hand_end` / `usage` / `transport_error`），**真相是账与作业本身**。
 *
 * 屏归这一个应用所有：不写裸 ANSI，也不开第二个渲染器抢同一块屏。
 *
 * 变因：交互与布局（几区怎么排、键位、选中语义、把事件映射成组件 props）。
 */
import type { NodeId } from "@meristem/atree";
import type { Tree, LineStore } from "@meristem/harness";
import type { Role } from "@meristem/roles";
import type { ReactElement } from "react";

export interface UiProps {
  readonly store: LineStore;
  readonly tree: Tree;
  /** 分叉时让人挑的角色清单（数据来源只有 roles 一处）。 */
  readonly roles: readonly Role[];
}

/** 一整屏：树条带 + 选中那条线的消息流 + 实时输出 + 状态条 + 输入行。 */
export declare function App(props: UiProps): ReactElement;

/** 接管终端、订阅事件、把人的输入送回账里；返回时终端已还原。非真终端时逐帧追加（降级）。 */
export declare function mount(props: UiProps, opts: { readonly at: NodeId | null }): Promise<void>;
