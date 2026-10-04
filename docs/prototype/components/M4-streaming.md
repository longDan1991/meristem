# 组件 · M4 它在说话（模型吐字时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 27 条 · jcode 18 条

## 两家在这一刻的对照（事实）

- omp 27 条 / jcode 18 条；omp 以 Markdown 流式正文 + 思考块（Thinking…/Thought for Ns/隐藏脉冲）+ 反应徽标 + 若干纯逻辑文件；jcode 以正文 markdown + 思考折叠行 + 内联图（mermaid/pinned diagram/图片预览）为主

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | AssistantMessageComponent 流式正文（Markdown） | assistant 文本逐 delta 追加、块未封 | 正文按 Markdown 重排；块 mode=appendOnly，已冻结的前缀可先退休进 scrollback | 封块后冻结；超容量按 settled 前缀整块退休，停在第一个 active 块 | packages/tui/src/chat/assistant-message.ts:718 |
| omp | 思考块·展开中（Thinking…） | 思考可见且是流式 tail（tail 块为 thinking） | starburst ✻/✼❉… + ' Thinking…' + 走动的计时 + tok/s；正文 italic thinkingText | 思考一结束就折成一行 'Thought for Ns' | packages/tui/src/chat/assistant-message.ts:813 |
| omp | 思考块·已完成（Thought for Ns） | 思考块写完（clock.end 有值） | native: 折叠 section，head 一行 'Thought for 12s'，tokens 走 title，body 折叠 | 常驻；终端可本地展开，Ctrl+T 隐藏时整块不显示 | packages/tui/src/chat/assistant-message.ts:42 |
| omp | 隐藏思考的脉冲（hideThinkingBlock） | 设置隐藏思考，且模型正在推理（未封块、无工具启动） | 单行 starburst 帧 + ' Thinking' + ' · 1.2k' tokens + ' · 88.3 tok/s'，宽度固定不跳列 | 文本开始流 / 工具调用启动 / 块 seal 即消失 | packages/tui/src/chat/assistant-message.ts:603 |
| omp | 思考 prose 折叠（formatThinkingForDisplay） | proseOnly 模式且思考内含 fenced code | 保留散文，围栏代码整体折成尾行 '…'；空注释 '<!-- -->' 噪声行丢弃 | 切到 raw 模式（或展开扩展渲染器）可见全文 | packages/tui/src/chat/thinking-display.ts:255 |
| omp | 思考扩展 renderer（AssistantThinkingRenderer） | 注册了 thinking 渲染器且思考块可见 | 思考正文后追加扩展组件（每个内容下标一组） | hideThinkingBlock 时不挂；扩展抛错则静默保留原文 | packages/tui/src/chat/assistant-message.ts:1393 |
| omp | 反应徽标（reaction badge） | assistant 回复以 emoji 开头，反应到前一块 | 前一块底部右上角一枚 emoji 徽标；流式中不完整 emoji 先扣住不闪（注：消息底部的 emoji 反应徽标，随消息角色区分） | 重建 transcript 时按持久化文本重算，不落盘 | packages/tui/src/chat/reaction.ts:22 |
| omp | ChatBlock（生命周期基类） | 任何'返回块交给 host 挂载'的转录块 | 本身不画；提供 mount/finish/dispose，未 finish 时 isTranscriptBlockFinalized=false 保持可重画（注：无视觉内容，块生命周期基类） | finish() 冻结在最终帧；dispose() 由 host 丢弃 | packages/tui/src/chrome/chat-block.ts:26 |
| omp | StreamingPanelContent（覆盖层流式壳） | btw/cleanse/omfg 等流式覆盖层每次 transition 后 refresh | 空行 + 各 section（之间空行）+ 末行 footer（muted 文本）（注：btw/cleanse/omfg 等流式覆盖层的外壳） | section 为 undefined/空数组即跳过；footer 每帧重读 | packages/tui/src/chrome/streaming-panel.ts:58 |
| omp | Skill 卡（用户 /skill: 调用） | 用户提交的草稿含 /skill:<name> | skill 色左栏用户气泡：chip（链到 SKILL.md）+ 行数 + 草稿 Markdown（注：用户 /skill: 提交的用户气泡卡） | 展开追加 'prompt' 小标题与 SKILL.md 全文；乐观行在 reconcile 前保持可移除 | packages/tui/src/chat/skill-message.ts:38 |
| omp | User 气泡（回合起点） | 用户提交输入 | userMessageBg 气泡：可选缩略图行 + 正文 Markdown（关键词发光/chip）；native 悬停出时间/Copy/Rewind | 拥挤时缩略图折成 '#N' chip；live-steered 顶左标 '*'，反应徽标在右下 | packages/tui/src/chat/user-message.ts:141 |
| omp | chatContainer（新发现） | 恒在——transcript 主体 | TranscriptContainer：所有消息/工具/notice 滚动历史（注：transcript 主体容器） | resetTranscript/重建时清空 | packages/coding-agent/src/modes/interactive-mode.ts:1815 / modes/types.ts:114 |
| omp | CollabPromptMessageComponent | 协作 guest 发来提示时 | 用户气泡「«from» ›」+markdown 正文（注：协作 guest 发来的用户气泡） | 常驻转录 | packages/tui/src/chat/collab-prompt-message.ts:15 |
| omp | splitReaction / ReactionTarget | 助手回复文本以 emoji 开头时 | emoji 被抬为前一块（用户气泡）上的徽标；流式中未完成 emoji 前缀被扣留（注：反应徽标纯逻辑） | 重建转录时按持久文本重现 | packages/tui/src/chat/reaction.ts:48 |
| omp | SkillMessageComponent | 用户 `/skill:<name>` 提交（token 在首=callout，居中=inline chip） | 用户气泡卡：skill chip（链 SKILL.md）+行数+草稿 markdown；展开追加 prompt | 普通气泡折叠；展开由 ctrl+o 控制 | packages/tui/src/chat/skill-message.ts:33 |
| omp | UserMessageComponent | 用户提交消息（synthetic=agent 注入为 muted） | 用户气泡：markdown+chip/mention+图片缩略；native 有 hover 工具条(时间/Copy/Rewind)、steered 与 emoji 徽标 | 常驻；工具条仅在有 action host 时描述 | packages/tui/src/chat/user-message.ts:121 |
| omp | CollapsedSyntheticMessageComponent | 转录查看器中的 synthetic 输入（如 Session update 巨型转储） | 默认 1 行「<标题> · 大小 · N lines · ctrl+o 展开」；展开才建 markdown | 默认折叠；展开建重体 | packages/tui/src/chat/user-message.ts:356 |
| omp | AssistantMessageComponent | 助手回合（流式/完成/错误/恢复/回退） | markdown 正文；thinking 段（流「✻ Thinking… 计时 tok/s」/完成「Thought for 12s」折叠）；错误卡「Request failed」+状态徽标+Retry/Copy error/Switch model；↺ rewound 徽标；turn usage 行 | 错误体折叠 ≤8 行；隐藏 thinking 时只留 live 头 | packages/tui/src/chat/assistant-message.ts:226 |
| omp | ChatTranscriptBuilder | 从不直接上屏（重建/追加转录时按消息类型分派） | 后台类：把各角色消息分派到上述卡片（注：从不直接上屏，分派构建各消息卡） | n/a | packages/tui/src/chat/chat-transcript-builder.ts:88 |
| omp | thinking-display | 从不直接上屏 | 思考文本折行/去空注释/去重的纯函数（供 assistant-message）（注：从不直接上屏，思考文本纯函数） | n/a | packages/tui/src/chat/thinking-display.ts:255 |
| omp | messages.ts | 从不直接上屏 | 消息类型与常量、silent/user-interrupt abort 判定与标签（注：从不直接上屏，消息类型/常量） | n/a | packages/tui/src/chat/messages.ts:21 |
| omp | transcript-entry | 从不直接上屏 | 持久化条目→消息/草稿/单行标签的还原函数（注：从不直接上屏，持久化条目还原函数） | n/a | packages/tui/src/chat/transcript-entry.ts:39 |
| omp | transcript-actions | 从不直接上屏 | retry/switch-model/rewind/resume/copy 动作总线；控件只在有 host 时被描述（注：从不直接上屏，动作总线） | n/a | packages/tui/src/chat/transcript-actions.ts:24 |
| omp | TranscriptContainer | 始终（转录根，容纳所有块） | 块按序排列；压力下退为单行，块前显示「N more transcript blocks active」 | 提交块退休进 scrollback；live 块>256 强制退休 | packages/tui/src/chrome/transcript-container.ts:170 |
| omp | TranscriptBlock | 从不直接上屏 | 仅把兄弟行归为一个可变语义块的空容器基类（注：从不直接上屏，空容器基类） | n/a | packages/tui/src/chrome/transcript-container.ts:1233 |
| omp | StreamingPanelContent (+Footer) | 流式 overlay 面板（/btw、/cleanse、/omfg 等） | 空行分隔的 sections 栈 + 底部 muted footer 行 | 面板关闭；footer 每帧重读 | packages/tui/src/chrome/streaming-panel.ts:58 |
| omp | ChatBlock | 从不直接上屏 | 块生命周期基类（mount/onCleanup/finish/dispose），无视觉内容（注：从不直接上屏，块生命周期基类） | finish/dispose 后冻结或移除 | packages/tui/src/chrome/chat-block.ts:28 |
| jcode | Diagrams（◇ Diagram） | 仅 diagram_mode=Margin 且 transcript 有活动 mermaid 图；右侧空隙≥24 宽、≥5 行 | 边框：◇ Diagram 左上，>1 图时右上 1/N；体内只画第 1 张图（按格放大/缩小填满）（注：doubt: margin 图渲染） | 无图/切到 Pinned 模式即消失；多图只显示第 1 张，无 N more | crates/jcode-tui/src/tui/app/tui_state.rs:1599, crates/jcode-tui/src/tui/info_widget.rs:755,1229, crates/jcode-tui/src/tui/info_widget.rs:167 |
| jcode | pinned diagram 面板（pinned） | diagram_mode=Pinned 且 pane_enabled；位置 Side(默认)/Top | 边框： pinned N/M <fit-mode> zoom X% Ctrl+←/→ Ctrl+H/L focus <hide> [alt+T ⇄ top/side] [o open]；体内按 fit/fit-fill 缩放居中或裁切视口（注：doubt: 右侧栏图面；无对应 S，故归 M4） | 只要右栏被侧栏页/File diff 占用即整块不出现（三态互斥） | crates/jcode-tui/src/tui/ui.rs:2817,2820, crates/jcode-tui/src/tui/ui_diagram_pane.rs:779,807 |
| jcode | pinned diagram 宽度/位置 | Side 位置 | 宽 = width×ratio（夹 25..100），最小 24 列、最多留 20 列给聊天；Top 位置高夹 20..100、最小 6 行 | 放不下 ≥24/≥6 即整块不出现；ratio 默认 40 | crates/jcode-tui/src/tui/ui.rs:2826,2864, crates/jcode-tui/src/tui/app/tui_lifecycle.rs:605 |
| jcode | Image preview（整屏） | 在聊天/侧栏点内联图片的像素格后 | 圆角框“ Image preview ”；图片按字体像素比缩放居中；框底“ Click or Esc to close ”（注：doubt: 整屏图预览；无对应 S） | Esc/Enter/q 或再点击关闭 | crates/jcode-tui/src/tui/ui_panel_image_preview.rs:31；分派 crates/jcode-tui/src/tui/ui.rs:2702 |
| jcode | Image preview 空态 | 预览 hash 已不在 PNG 缓存（被回收） | 框内一行“Image is no longer available. Press Esc to return.” | Esc | crates/jcode-tui/src/tui/ui_panel_image_preview.rs:31（else 分支） |
| jcode | user（用户 prompt 行） | 每次提交后进正文；语音也走这里 | `N› 文本`，整行 user 背景高亮；多行按同前缀缩进 | 不截断；滚出视口后由 sticky 预览接管 | crates/jcode-tui/src/tui/ui_prepare.rs:359 |
| jcode | 🎙 语音 prompt 行 | 语音输入提交后（含 <transcription> 包装） | 麦克风标记 + 剥离标签后的口述原文 | 同 user 行 | crates/jcode-tui/src/tui/ui_prepare.rs:367 |
| jcode | assistant（正文 markdown） | 助手消息提交/流式收尾时 | markdown：标题/粗体/列表/表格/代码块；居中模式重排结构化块 | 无行数上限，按宽换行 | crates/jcode-tui/src/tui/ui_messages.rs:82 |
| jcode | reasoning（思考折叠行） | reasoning_display=current/full 时随流式出现 | 高度塌缩的 dim/italic 摘要行 | 过时（滚出/结束时）溶解，零可见位移 | crates/jcode-tui/src/tui/ui_messages.rs:303 |
| jcode | 内联图 label 行 | 锚定/底部区有图（pin_images） | `  名称 1920×1080  [Alt] [⇧] [I] hide`（隐藏时 `show image`） | 宽度不足截断左侧 label，右侧徽标优先保留 | crates/jcode-tui/src/tui/ui_inline_image.rs:934 |
| jcode | 内联图占位/图像区 | 图片可见时 | 按宽算行高（Fit ≤16 行），只画 label+占位，不画图形 | 隐藏时整块塌缩只留 label 一行 | crates/jcode-tui/src/tui/ui_inline_image.rs:966 |
| jcode | Plan graph · vN（聊天内联图卡） | 收到 SwarmPlan 事件且 mermaid 开；正文角色 swarm | `🐝 Plan · vN` 头 + ```mermaid flowchart 图（inline image 占位） | 旧版本事件丢弃；只保留一张，移到正文末尾；mermaid 关则完全不 push | crates/jcode-tui/src/tui/ui_messages.rs:3124 |
| jcode | 正文内 mermaid 内联图 | assistant 正文含 ```mermaid 且渲染启用 | 内联图区：label 行 + 按宽算出的占位行（真图由 image 管线绘入该 region） | 渲染中先显 'rendering mermaid diagram...' 占位；隐藏图片时只留 label | crates/jcode-tui/src/tui/ui_messages.rs:3279 |
| jcode | pinned diagram 侧栏 | diagram_mode=margin/pinned 且 pane 启用、有活动图 | 标题 ` pinned 2/3 fit@85% zoom 100% Ctrl+←/→ Ctrl+H/L ... hide`（多图带序号/切换键） | 宽度不足依次丢 hint；fit 差时提示 `focus+o open` | crates/jcode-tui/src/tui/ui_diagram_pane.rs:799 |
| jcode | Plan graph · vN 卡 | 见 B 组同名项 | 压缩后的 plan mermaid 图卡，占据正文一条消息 | 见 B 组 | crates/jcode-tui/src/tui/ui_messages.rs:3124 |
| jcode | 内联图展开等级（Fit/Large/Full） | 点击图片本体或 label 时按级递增 | Fit=≤16 行；Large=≤40 行；Full=≤200 行（行高固定，不受视口影响） | 重复尺寸跳过；循环回 Fit | crates/jcode-tui/src/tui/ui_inline_image.rs:91 |
| jcode | sticky 上一条 prompt 预览 | display.prompt_preview=true 且 scroll>0 | 顶部 `N› 文本`（dim+user 底）；过长折叠为两行 `head ...` / `... tail`（注：doubt: 正文 sticky 预览） | 宽不足时改用 head/tail 双行形态 | crates/jcode-tui/src/tui/ui_viewport.rs:1281 |
| jcode | 右侧用户行标记 `│` | 可见区间内有 user prompt 行 | 正文最右 1 列的 user 色竖线，指向每个 prompt 起行 | 行滚出可见区即不画 | crates/jcode-tui/src/tui/ui_viewport.rs:1205 |
