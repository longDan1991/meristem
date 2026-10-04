# 组件 · M8 完事的时候（一轮结束时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 30 条 · jcode 16 条

## 两家在这一刻的对照（事实）

- omp 30 条 / jcode 16 条；omp 用分隔条/通知/状态行交代完成（Branch/Compaction/Recap/TTSR/Todo/Background job/File mention/统计）；jcode 用 status_notice 与各类通知卡（DM/Task/#channel/Broadcast/Plan/Background task）

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | 粘贴转文件提示 | 大粘贴菜单选 local file 且写盘成功 | "Saved N pasted lines to local://paste-N.md" | 被后续状态覆盖 | packages/coding-agent/src/modes/controllers/input-controller.ts:2555 |
| omp | showStatus 状态行 | 任意操作反馈（队列、粘贴、命令结果等） | transcript 内 dim（或 accent）一行文本（注：泛用瞬时状态行，归完事通知；疑点：亦近 M10 状态带） | 被后续状态/输出覆盖 | packages/coding-agent/src/modes/utils/ui-helpers.ts:139 |
| omp | MessageNoticeComponent（通知外壳） | 控制器 refresh（TTSR/todo 提醒/内联通知） | 反色或 severity 底色的 Box：头行 (icon + header)，空行，body | native 折叠由 preview 行数定；toolActivityVisible=false 时整块不渲染 | packages/tui/src/chrome/message-notice.ts:52 |
| omp | StatusNotice（瞬时状态行） | showStatus：如 'Thinking blocks: hidden'、'Copied to clipboard' | 空行 + 一行 dim 文本（缩进 1） | native 是 2400ms TTL 的 toast（不堆进 history）；ANSI 下留在转录里 | packages/tui/src/chrome/status-notice.ts:17 |
| omp | Branch 分隔条 | 侧支被汇总回主线 | 同一 slim divider，label '⎇ branch'，展开出分支摘要（注：侧支汇总回主线后的分隔条） | 同 compaction 的窄屏降级 | packages/tui/src/chat/compaction-summary-message.ts:296 |
| omp | Recap 通知（recap.*） | 闲置后 agent 写了一段'你不在时发生了什么' | dim italic 一行 '※ recap: …'（native: history 图标 + omp.recap 行） | 像思考一样常驻转录 | packages/tui/src/chat/recap-notice.ts:19 |
| omp | TTSR 通知（规则回退） | 规则命中、流被 rewind | 内联 warning 通知 'Injecting rule: <name> ⟲'；多条时折叠最多 4 条，正文各一行（注：规则注入/流回退的 warning 通知） | 折叠超 4 条 → '… +N more (ctrl+o to expand)'；单条描述超 2 行亦截断 | packages/tui/src/chat/ttsr-notification.ts:31 |
| omp | Todo 提醒通知 | agent 停下但仍有未完成 todo | warning 通知 '<N> incomplete todos - reminder a/b' + 斜体未完成项列表（注：未完成 todo 提醒） | native 支持 checklist 时改为 checklist(reminder) 形态 | packages/tui/src/chat/todo-reminder.ts:19 |
| omp | Stripped tool calls 占位 | 分支上被剥离了工具调用（失败/重试回合） | dim italic '<N> tool calls elided — no result on this branch'（注：分支上被剥离工具调用的占位） | 随 hideToolActivity 一起隐藏/恢复 | packages/tui/src/chat/stripped-tool-calls-placeholder.ts:13 |
| omp | Advisor 卡 | advisor 注入笔记后 | 头 'ⓘ Advisor · N notes [· k blockers]' + 每条 note 一段（severity 徽标 + 竖线 + 文本）（注：advisor 注入笔记卡） | 折叠只显示前 3 条 (COLLAPSED_NOTES)，其余 '… +N more notes'；可 Ctrl+O 展开 | packages/tui/src/chat/advisor-message.ts:14 |
| omp | Hook / Custom message 帧 | 扩展/hook 注入可显示消息 | customMessageBg 框：icon+类型标签头 + Markdown 正文（注：hook/扩展注入的可显示消息框） | hook 折叠前 5 行 (HOOK_COLLAPSED_LINES) 后加 '…'；custom（扩展）不折叠 | packages/tui/src/chrome/message-frame.ts:62 |
| omp | Background job completed / launch completion 状态行 | 后台 bash/task 作业或受监督进程结束 | 每作业一行 '✓ Background job completed [type] <jobId> (12s)'；失败红、完成绿（注：后台作业/受管进程结束状态行） | 有 artifact 错误时追加一行 warning | packages/tui/src/chat/transcript-render-helpers.ts:36 |
| omp | File mention 行（@file 自动读） | 用户消息带 @filepath | 每文件一行 '└ Read <path> (N lines)'；太大/二进制标 '(skipped: …)'（注：@file 自动读取的文件提及行） | 图片标 '(image)'；无行数标 '(unknown lines)' | packages/tui/src/chat/transcript-render-helpers.ts:151 |
| omp | TodoReminderComponent | agent 停下且仍有未完成 todo（todo_reminder 事件） | 提交进 transcript 的 notice 卡：'N incomplete todos - reminder a/b' + 每条 '☐ 内容' | 随 transcript 滚动，不浮在编辑器上 | packages/tui/src/chat/todo-reminder.ts:15 / coding-agent/src/modes/controllers/event-controller.ts:2544 |
| omp | RecapNotice (※ recap:) | 空闲离开后回来、写有 recap 文本时 | 空行+dim 斜体「※ recap: …」1 行；native 为 history 图标+文本 | 常驻转录随滚动离开；wrap 不截断 | packages/tui/src/chat/recap-notice.ts:14 |
| omp | TtsrNotificationComponent | 规则违规致流回退时；同一事件多规则合并入上一块 | 通知卡「Injecting rule: <名> ⟲」+描述；或「Injecting N rules:」+每规则 1 行 | 折叠描述>2 行加「…」；>4 规则「… +N more」 | packages/tui/src/chat/ttsr-notification.ts:30 |
| omp | TodoReminderComponent | agent 停止且仍有未完成 todo | 通知卡「N incomplete todos - reminder a/b」+每 todo 一未勾选框 | 常驻；hideToolActivity 时隐藏 | packages/tui/src/chat/todo-reminder.ts:15 |
| omp | StrippedToolCallsPlaceholder | 分支解析/重试后工具调用被剔除时 | dim 斜体 1 行「N tool calls elided — no result on this branch」 | hideToolActivity 时 render 返回 [] | packages/tui/src/chat/stripped-tool-calls-placeholder.ts:11 |
| omp | HookMessageComponent | hook 注入 hookMessage 且 display | 框卡：hook 图标+customType 头+markdown 正文 | 折叠超 5 行加「…」 | packages/tui/src/chat/hook-message.ts:12 |
| omp | CustomMessageComponent | extension 注入 custom/hookMessage 且 display=true | 框卡：package 图标+customType 头+markdown；live-delegation 无头、accent 边框 | extension 消息不折叠，全文渲染 | packages/tui/src/chat/custom-message.ts:10 |
| omp | createBackgroundTanDispatchBlock (Tangent dispatched) | `/tan` 后台派发时 | 1 行 pill「⟳ Tangent dispatched [task] <jobId> — <work 预览>」（注：/tan 后台派发的 pill 通知） | 单行；work>56 字截断加 … | packages/tui/src/chat/background-tan-message.ts:21 |
| omp | createAdvisorMessageCard | advisor 注入 notes 时 | 卡「Advisor N notes [· k blockers]」+每条注 severity 徽标+rail+T-n+文本 | 折叠>3 条注「… +N more notes」 | packages/tui/src/chat/advisor-message.ts:167 |
| omp | BranchSummaryMessageComponent | 侧枝被折叠回主线时 | 分隔条「⑂ branch」；展开「Branch summary」+文本 | 常驻；太窄退化为裸标签 | packages/tui/src/chat/compaction-summary-message.ts:296 |
| omp | buildAsyncResultBlock (Background job completed) | async-result：后台 bash/task 完成 | 每 job 1 行「✔ Background job completed [type] id (dur)」 | 常驻；artifact 错误各加 1 行 | packages/tui/src/chat/transcript-render-helpers.ts:30 |
| omp | buildLaunchCompletionBlock (Supervised process …) | launch-completion：受管进程退出 | 每 daemon 1 行「✔/✘ Supervised process completed/failed name (exit N) (dur)」 | 常驻；无 daemon 时用 content 1 行 | packages/tui/src/chat/transcript-render-helpers.ts:86 |
| omp | buildFileMentionBlock (Read <path>) | `@file` 自动读取的文件提及 | 每文件 1 行「└ Read <path> (N lines)」 | 常驻；跳过文件标 (skipped: binary, size) | packages/tui/src/chat/transcript-render-helpers.ts:160 |
| omp | StatusNotice | showStatus（如「Thinking blocks: hidden」「Copied to clipboard」） | ANSI：空行+dim 行；native：toast | native toast 2400ms 后消失；改文本重新弹出 | packages/tui/src/chrome/status-notice.ts:17 |
| omp | MessageNoticeComponent | 通知 shell（TTSR/todo 复用） | 反色/severity 色框：header 行（可选 icon）+body；native 可 inline（图标+1 行+可折叠 body） | hideToolActivity 隐藏；折叠由 preview/body 决定 | packages/tui/src/chrome/message-notice.ts:59 |
| omp | FramedMessageComponent | hook/custom 消息框（由 chat/ 子类实例化） | 圆角框：图标+customType 头+markdown；可选 collapseAfterLines | 折叠≥N 行加「…」；renderer 返回空则回退默认卡 | packages/tui/src/chrome/message-frame.ts:60 |
| omp | /stats 结果 notice | /stats（omp 在浏览器提供 dashboard） | transcript 中内联一行 dim 状态文本 + 「Open dashboard ↗」按钮(OSC 打开 URL)（注：transcript 内联一行状态+Open dashboard 按钮；疑点：stats 内容亦近 S11） | 随 transcript 滚动；不开面板 | packages/tui/src/overlays/stats-notice.ts:11-33 |
| jcode | status_notice（临时提示） | set_status_notice 后 3s 内 | accent_color 文本（含取回/队列/切换等文案）（注：doubt: 通用瞬时通知） | 3s 后消失 | crates/jcode-tui/src/tui/ui_input.rs:1749-1755; app/tui_state.rs:985-991 |
| jcode | OpenAI reset 提示 | OpenAI OAuth 且有可用 reset、非处理中 | `{N} reset(s) available · expires… · /reset usage limits openai`，可换行（注：doubt: 用量重置提示；亦涉 S9 计费） | 用量刷新/处理开始 | crates/jcode-tui/src/tui/ui_input.rs:1779-1783,1859-1902,1904-1937 |
| jcode | Remote·重连/reload 完成消息 | 重连成功或 reload 完成后 | “✓ Reconnected successfully.”+(reload 明细/“Reload context restored”)；“Reload complete - …”系列 | 留在聊天记录 | crates/jcode-tui/src/tui/app/remote/reconnect.rs:668/693/890 |
| jcode | Remote·Swarm/服务端通知卡 | 服务端推送通知（DM/频道/广播/Plan/文件活动/后台任务/await） | 聊天卡标题：“DM from X”“Task · X”“#chan · X”“Broadcast · X”“Plan · X”“Swarm · X”“File conflict/File activity · X”“Background task[ progress]”“🐝 Swarm await”“Shared context · X”（注：doubt: 通知卡；亦涉 M11） | 留在聊天记录（消息正文可折叠为 tldr） | crates/jcode-tui/src/tui/app/remote_notifications.rs:152 |
| jcode | DM from <sender> | scope=dm 且非任务指派；进正文（不覆盖屏幕） | `✉ sender` 头 + markdown 正文；带 tldr 时首行 tldr，右侧徽标 | 有 tldr → 默认折叠；点 `▸ expand` 展开整段 | crates/jcode-tui/src/tui/app/remote_notifications.rs:177 |
| jcode | Task · <sender> | dm 且正文以 `Task assigned to you by coordinator:` 开头 | `⚑ sender` 头 + 指派正文（剥离前缀） | 同 DM 的 tldr 折叠规则 | crates/jcode-tui/src/tui/app/remote_notifications.rs:171 |
| jcode | #<channel> · <sender> | scope=channel | 首行 `#chan · ` + `#` 图标 + 正文（剥离 `#chan: `） | 同 tldr 折叠；徽标 `▸ expand` | crates/jcode-tui/src/tui/app/remote_notifications.rs:187 |
| jcode | Broadcast · <sender> | scope=broadcast（子树范围投递） | `📣 sender` 头 + 正文（剥离 `broadcast from x: `） | 同 tldr 折叠 | crates/jcode-tui/src/tui/app/remote_notifications.rs:191 |
| jcode | Plan · <sender> | scope=plan（计划变更通知） | 单行 `🐝 Plan · <压缩摘要>`，超宽省略号截断 | 压成一行，超出即截断 | crates/jcode-tui/src/tui/ui_messages.rs:3158 |
| jcode | Shared context · <sender> | 共享上下文 key 被写入 | `🧠 sender` 头 + 正文，` = ` 替换为 ` · ` | 同 tldr 折叠 | crates/jcode-tui/src/tui/ui_messages.rs:3002 |
| jcode | File activity · <sender> | 其他 agent 改动文件时 | `✎ sender` 头 + `path · 摘要`；路径 >4 段压成 `…/末4段` | diff 预览用 `▸ diff` / `▾ hide` 徽标折叠 | crates/jcode-tui/src/tui/ui_messages.rs:2989 |
| jcode | Swarm · <sender> | 未知/未命名 scope 或 scope=swarm | `◦ sender`（默认灰）头 + 原样正文 | 同 tldr 折叠 | crates/jcode-tui/src/tui/ui_messages.rs:2998 |
| jcode | Background task 卡 | scope=background_task 且为完成/失败通知 | `**Background task** id · tool · ✓completed/✗failed · Ns · exit0` + text 码块预览 + Full output 提示（注：doubt: 后台任务完成/失败通知） | 预览空→`_No output captured._`；正文含 ```` 会被插入零宽字符消毒 | crates/jcode-tui/src/tui/ui_messages.rs:2559 |
| jcode | 通知卡徽标常量 `▸ expand` / `▾ collapse` | 通知卡有 tldr 且折叠（expand）或展开（collapse） | 首行行尾 dim 徽标，是可点击目标 | 无 tldr（普通卡）时不渲染 | crates/jcode-tui/src/tui/ui_messages.rs:2922 |
| jcode | 通知卡徽标常量 `▸ diff` / `▾ hide` | 文件活动/冲突类通知携带 diff 负载时 | 同上位置的 dim 徽标，点开显示 diff 预览 | 无 diff 负载则不渲染 | crates/jcode-tui/src/tui/ui_messages.rs:2924 |
| jcode | 输入上方通知行 | 有 notification（如 OpenAI 重置额度 hint） | 单行文本；reset hint 会按宽换行不裁到期时间 | 清空后不再占行 | crates/jcode-tui/src/tui/ui_input.rs:1904 |
