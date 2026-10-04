# 组件 · M3 排队与待发（消息排队待发时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 8 条 · jcode 8 条

## 两家在这一刻的对照（事实）

- omp 8 条 / jcode 8 条；omp 以「队列带/出队提示/pills/DeferredCommandPreview」呈现排队与被打断的命令输出；jcode 用 ↻/⚡/⏳ 行号指示 pending 软中断/interleave/queued 并支持取回编辑

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | 队列带标题 | 有 steering 或 follow-up 排队消息 | "Steering · N" / "After yield · N"（muted） | 组为空则该组不画 | packages/tui/src/prompt/queued-messages.ts:32 |
| omp | 队列消息行 | 同组内每条消息 | ` 1. <text>`（换行显示为 " ↵ "）dim | 投递后消失 | packages/tui/src/prompt/queued-messages.ts:36 |
| omp | 出队提示行 | 队列带存在时 | `  ↳ alt+up to edit` dim | 队列清空即消失 | packages/tui/src/prompt/queued-messages.ts:40 |
| omp | 原生队列 pills（TSP） | 有排队消息（原生渲染面） | 每消息一 pill：↳ 文本 ⌥↑Edit；首 pill 带总数 badge | 溢出由终端截断 | packages/tui/src/prompt/queued-messages.ts:43 |
| omp | 排队提交状态行 | Enter 提交排队/压缩期间排队 | "Queued message for when the agent yields" 等 | 被后续状态覆盖 | packages/coding-agent/src/modes/controllers/input-controller.ts:1837 |
| omp | deferredCommandContainer / DeferredCommandPreview | agent 流式中用户敲了 /usage 等命令，输出被排队 | 真实面板原样预览 + 尾注 'N command outputs — repeated in the transcript when the agent pauses'（注：流式中命令输出被排队预览） | 上限 max(6, 视口40%) 行；超出 → '… N more rows — …；agent 暂停时整段进转录 | packages/coding-agent/src/modes/interactive-mode.ts:757 |
| omp | deferredCommandContainer | 流式期间执行命令输出（presentCommandOutput 且 streaming） | DeferredCommandPreview：真实面板按 maxRows 截断+'1 command output — …shown in full when the agent pauses' | 回合结束后 flush 进 transcript 即清空 | packages/coding-agent/src/modes/interactive-mode.ts:7113,7208,757 |
| omp | pendingMessagesContainer | 有排队/打断消息（streaming 中提交） | QueuedMessagesBand：分组头（Steering/After yield·N）+编号行+'⌥↑ to edit'；native 为 pill 栈（注：排队/打断消息容器） | dequeue/回合开始 flush 后即清空 | packages/coding-agent/src/modes/utils/ui-helpers.ts:1091 |
| jcode | ↻ pending soft interrupt 行 | 处理中且 pending_soft_interrupts 非空 | `{num} ↻ {msg}`，pending_color；msg 原文 | 注入/取回后消失 | crates/jcode-tui/src/tui/ui_input.rs:509-545 |
| jcode | ⚡ interleave 行 | 处理中且 interleave_message 非空 | `{num} ⚡ {msg}`，asap_color | 发送/取回后消失 | crates/jcode-tui/src/tui/ui_input.rs:517-522,536-538 |
| jcode | ⏳ queued 行 | queued_messages 非空 | `{num} ⏳ {msg}`，queued_color 且 dim | 派发/取回后消失 | crates/jcode-tui/src/tui/ui_input.rs:526-538 |
| jcode | 行号（彩虹） | 每行 | start_num=用户消息数+1，距离越远越灰 | 随派发重排 | crates/jcode-tui/src/tui/ui_input.rs:533-535,2990-2996 |
| jcode | 溢出（>3 条） | pending_count>3 | 只画前 3 行，无 "+N more" | 多余行直接不渲染 | crates/jcode-tui/src/tui/ui.rs:3000-3001; ui_input.rs:519-521 |
| jcode | 取回编辑（↑ / Ctrl+↑） | 输入框为空时按 ↑（或提示历史修饰键） | soft+interleave+queued 合并进输入框（\n\n 连接） | 取回后排队条清空 | crates/jcode-tui/src/tui/app/input.rs:1505-1542,2119-2121,3169-3172 |
| jcode | 取回提示（通知行） | 取回成功 | `Retrieved N pending message(s) for editing`（status_notice） | 3s 后消失 | crates/jcode-tui/src/tui/app/input.rs:1533-1538 |
| jcode | 队列消息行 | 处理中有 pending 软中断 / interleave / 排队消息 | `↻`/`⚡`/`⏳` 指示 + rainbow 序号 + 文本 | 超出可见行数时按序截断 | crates/jcode-tui/src/tui/ui_input.rs:509 |
