# 屏幕 · 这一轮（当前这一轮所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S3：omp 9 条 · jcode 1 条

## 两家在这一刻的对照（事实）

- omp 9 条 / jcode 1 条；omp 是 Plan Review / PAUSED 全屏屏与文件名自动生成、焦点循环；jcode 只有 session_todos（这一轮待办）页。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | PlanToc（plan-toc.ts 解析） | 打开 /plan plan-review 全屏 overlay 时 | 左侧 sidebar 的章节列表（VS Code 风格），缩进按标题层级，有批注标 '✎n'；≥阈值章节才显示侧栏（注：plan-review 全屏屏的 Contents 侧栏，随屏归 S3） | 标题级被去掉（作为 sheet 标题）；宽度不足不显示侧栏 | packages/tui/src/overlays/plan-toc.ts:71 / plan-review-overlay.ts:1265,1575 |
| omp | Queue Mode 选择器 | 【用户看不到】无实例化点 | 面板标题 Queue Mode；两行 one-at-a-time / all 及说明；预选当前值（注：【用户看不到】无实例化点（死路径）） | Esc 取消 | packages/tui/src/overlays/queue-mode-selector.ts:11-62 |
| omp | Save and quit | plan 模式里选择保存计划并退出(计划评审的 save 分支，interactive-mode#promptPlanSavePath) | sm 玻璃 sheet「Save and quit」：Path 输入行(空时显示暗色建议路径 + 反显光标) + 底部 Cancel / Save and quit 按钮 | 提交/取消即关；Esc 取消 | packages/tui/src/overlays/plan-save-overlay.ts:10-16,74-115 |
| omp | 文件名自动生成提示 | 标题生成返回后 | 建议路径被替换(setSuggestedPath)，空输入时显示新建议 | 提交后消失 | packages/coding-agent/src/modes/interactive-mode.ts:5430-5447 |
| omp | Plan Review（全屏） | plan 模式产生待批计划时(showPlanReview)，或 /plan-review 重开 | 标题 Plan Review；Contents 侧栏(≥2 个标题且宽≥64)、计划正文(按 md 分节 + ScrollView)、审批选项列表(可选 model-tier slider)、注解 | Esc 取消(返回 undefined)；正文至少留 3 行；注解编辑器最多 6 行后滚动 | packages/tui/src/overlays/plan-review-overlay.ts:1-27,67-76,1383-1394 |
| omp | 焦点循环 | Tab/Shift+Tab | toc / body / actions 三段焦点依次切换；默认焦点 actions(↑↓选选项、Enter 确认)；external editor 键打开计划 | Esc 取消 | packages/tui/src/overlays/plan-review-overlay.ts:14-22,78 |
| omp | PAUSED 全屏屏 | /pause（冻结 main/subagent/advisor） | 整屏：竖条艺术字、居中标题 P A U S E D、BODY_LINES、paused for HH:MM:SS、resume 提示；原生为 md 居中 sheet「Paused」(transcript 仍可见冻结) | esc/enter/space/ctrl+c 任一即恢复；宽<64 或高<18 退化为 compact 卡 | packages/tui/src/overlays/pause-screen.ts:45-60,99-177 |
| omp | 会话名与 Resume 按钮 | 有 sessionName / 原生渲染 | 会话名(strong) + 「Paused for <elapsed clock>」+ Resume 按钮(keys=esc) | 恢复后整屏消失 | packages/tui/src/overlays/pause-screen.ts:179-200 |
| omp | 计划分节解析 | 【用户看不到】被 plan-review-overlay 的 Contents 侧栏与删除/撤销使用 | parsePlanSections/joinPlanSections/sectionDeletionSpan/stripInlineMarkdown（注：【用户看不到】纯解析 helper） | — | packages/tui/src/overlays/plan-toc.ts:1-160 |
| jcode | session_todos 页（Todos，ephemeral） | /todos panel；不落盘（SSH 下不可用） | 标题 Todos；汇总 “**N/M completed** (x%) · k doing · p pending · b blocked[ · c cancelled]” + ## In progress/Pending/Completed/Cancelled 分组（注：doubt: 这一轮待办屏；亦涉 M11/S6） | 最多 8 条，超出 “_… and N more._”；无 todo 写占位 | crates/jcode-tui/src/tui/app/todos_view.rs:9,415,455,510 |
