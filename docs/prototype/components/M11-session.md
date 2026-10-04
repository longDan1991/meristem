# 组件 · M11 会话层面的东西（跨轮会话层面屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 34 条 · jcode 19 条

## 两家在这一刻的对照（事实）

- omp 34 条 / jcode 19 条；omp 以 HUD/挂件 API（subagent/todo/btw/设置/协作 QR/jobs/实验仪表盘）为主；jcode 以常驻挂件与内联卡（Todos/Memory/BackgroundTasks/SwarmStatus/计划任务/记忆卡/todo band）为主

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | subagentContainer · Subagents HUD | 有 running 的子代理会话 | 空行 + 粗体 'Subagents' + 每行 '• <id> [role] : 描述'（可带模型徽标/一行工具预览）（注：运行中子代理的 HUD 名册） | 超 itemRows 出 '… N more — expand' 切换行；无 running 时清空 | packages/coding-agent/src/modes/interactive-mode.ts:1076 |
| omp | todoContainer / 紧凑 HUD 药丸 | 有 todo 或后台作业在跑 | 右对齐 HUD 行：todo 药丸 + subagent 药丸 + 'N jobs running' 药丸（带 icon/spinner）（注：todo+subagent+后台作业药丸行） | 全空时整行 hidden；非紧凑模式接 renderCompactStatusLine | packages/coding-agent/src/modes/interactive-mode.ts:1411 |
| omp | running-subagent-badge（状态栏右端） | registry 里有 kind=sub 且 status=running 的 agent | 右端加 '<agents 图标> N'（statusLineSubagents 色）；native 为 icon='agents' 的 span（注：状态栏右端运行中子代理计数徽标） | count=0 时不出现；一旦有徽标就压掉配置里的左/右 'subagents' 段 | packages/tui/src/status-line/component.ts:2463 |
| omp | 徽标计数来源（registry 过滤） | AgentRegistry 或 collab guest registry 变化 | list().filter(kind==='sub' && status==='running').map(id) 的长度（注：纯数据来源，非视觉） | collab guest 断开回到本地 registry；无 running 即 0 | packages/tui/src/overlays/running-subagent-badge.ts:14 |
| omp | setWidget(key,content,{placement}) | 扩展调用，默认 placement=aboveEditor | aboveEditor 挂到编辑器上方 hookWidgetContainerAbove；belowEditor 挂编辑器下方 | content=undefined 或换 placement 即移除 | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:349 / extensibility/extensions/types.ts:236 |
| omp | MAX_WIDGET_LINES=10 截断 | setWidget 传字符串数组且行数>10 | 只上前 10 行，第 11 行显示 '... (widget truncated)' | 截断行是最后一行 | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:44,371 |
| omp | hookWidgetContainerAbove / EditorTopGap | 无任何 above 挂件时 | 容器只放一个 EditorTopGap：band 且状态行占位时塌成 0，否则留一空行 | 有挂件时替换为 Spacer+挂件 | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:391 / modes/interactive-mode.ts:1867 |
| omp | setFooter | 扩展调用 | 无——真实 TUI 上下文是空实现，界面上不出现任何东西（注：空实现，界面上不出现任何东西） | — | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:162 |
| omp | setHeader | 扩展调用 | 无——同样空实现，不显示（注：空实现，不显示） | — | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:163 |
| omp | todoContainer | todoPhases 非空、未隐藏、终端行数≥18 | TodoHudContainer：'TODO' 标题+阶段树，阶段名+done/total，活动阶段高亮，spine 填充总体进度 | 紧凑模式(<18行)折进状态行；全完成 auto-clear 隐藏 | packages/coding-agent/src/modes/interactive-mode.ts:649,4143 |
| omp | subagentContainer | ≥1 个 active 子 agent | SubagentHudComponent：'Subagents' 头+每行 'Id ⟨role⟩: 描述'，livePreview 时附一行当前工具调用 | 无运行即清空；超行折叠成 '… n more — expand' | packages/coding-agent/src/modes/interactive-mode.ts:1083,4455 |
| omp | btwContainer | /btw 侧会话可见时 | BtwPanelComponent（问答面板），编辑器上方（注：/btw 侧问面板容器（后台侧任务）） | 关闭/切走即 clear | packages/coding-agent/src/modes/controllers/btw-controller.ts:455,562,691 |
| omp | hookWidgetContainerAbove（新发现） | 有 aboveEditor 扩展挂件（否则只放 EditorTopGap） | 编辑器上方的扩展挂件（每条一个） | clearHookWidgets/setWidget(undefined) | packages/coding-agent/src/modes/interactive-mode.ts:1867 / modes/types.ts:129 |
| omp | hookWidgetContainerBelow（新发现） | 有 belowEditor 扩展挂件 | 编辑器下方的扩展挂件 | clearHookWidgets/setWidget(undefined) | packages/coding-agent/src/modes/interactive-mode.ts:1869 / modes/types.ts:130 |
| omp | running-subagent-badge | syncRunningSubagentBadge 触发（注册表变化/协作快照） | 无自身渲染——只过滤 kind=sub 且 status=running 的 id 交给状态条 subagents 段/徽标 | — | packages/tui/src/overlays/running-subagent-badge.ts:14 / coding-agent/src/modes/interactive-mode.ts:3696 |
| omp | HudPillsRow / jobs pill（native-only） | native 终端有 todo/subagent/后台任务 | 右对齐一排 pill：todo HUD、subagent pill、'N jobs running'（带 spinner，点开 jobs） | 全空则整行 hidden | packages/coding-agent/src/modes/interactive-mode.ts:678,1404 |
| omp | extension-types | 从不直接上屏 | 纯类型：renderer/factory/widget 签名（注：从不直接上屏，纯类型） | n/a | packages/tui/src/chat/extension-types.ts:1 |
| omp | CollabQrCodeComponent | `/collab` 打印浏览器加入二维码时 | QR half-block 图（宽≥minWidth）；native：URL 行+文本 QR（注：/collab 加入二维码块） | 宽/高不足→单行「Join … QR code hidden: …」 | packages/tui/src/chrome/collab-qrcode.ts:34 |
| omp | QrCode / renderQrText / renderQrHalfBlocks | 从不直接上屏（由 CollabQrCodeComponent 调用） | 纯算法：模块网格→half-block 行或文本行（含 4 模块静区）（注：从不直接上屏，QR 纯算法） | n/a | packages/tui/src/chrome/qrcode.ts:519 |
| omp | JobsPanel（/jobs transcript 块） | 输入 /jobs [full] | transcript 块「Background jobs · N running」；task 型 job 画成 agent 节点，其它为 ● + type + elapsed + label；Recent 分节 | 随 transcript 滚动；无 job 显示「No background jobs」 | packages/tui/src/overlays/jobs-panel.ts:95-113,190-260 |
| omp | JobsSheet（jobs pill sheet） | 点击 jobs pill（showJobsSheet；与 /jobs 不同，不写 transcript） | 居中 lg 玻璃 sheet「Background jobs」：任务列表(max 6 行, running 在前) + 选中项详情(状态/elapsed/cwd/pid/exit/完整 command/输出尾) | Esc 或 Close 关闭；X 取消运行中 job；终端回退显示输出尾 ≤8 行 | packages/tui/src/overlays/jobs-panel.ts:93,120-135,160-190 |
| omp | /btw 侧问面板 | /btw <question> | 面板标题「/btw <question>」(复制后加 ✓ Copied)；正文=流式答案；footer 随状态(running/complete/branching/aborted/error)变（注：TUI 内 /btw 侧问面板（后台侧任务）） | Esc/关闭后留存直到关；错误态显示 error 行 | packages/tui/src/overlays/btw-panel.ts:22-40,90-113 |
| omp | BTW history | /btw（不带问题）浏览本会话 BTW 历史 | lg 玻璃 sheet「BTW history」：左右两栏(list 42%宽 max46 \| answer)，行=状态(Running/Complete/…)+时间+问题（注：/btw 历史 sheet） | Esc 关闭；窄屏(≤96)只显左栏；列表高度不足时按行裁剪 | packages/tui/src/overlays/btw-history-panel.ts:68-93,363-420 |
| omp | Follow-up composer | 在选中记录上开 follow-up | answer 栏底部 Input「Follow up: 」，带 remark/notice 行（注：btw follow-up 输入） | Esc 中止；提交成功后收起并跟随最新 | packages/tui/src/overlays/btw-history-panel.ts:216-250 |
| omp | 复制确认 | 按 c 复制选中答案 | 列表项出现已复制标记(#isCopied)（注：复制标记） | 当该记录文本变化后失效 | packages/tui/src/overlays/btw-history-panel.ts:200-210 |
| omp | 运行中子代理徽标数据 | 【用户看不到】状态行的 running-subagents 徽标取 id 用 | getRunningSubagentBadgeRegistry / getRunningSubagentBadgeAgentIds（返回 kind=sub 且 running 的 id）（注：【用户看不到】纯 helper） | — | packages/tui/src/overlays/running-subagent-badge.ts:1-20 |
| omp | BTW 记录模型 | 【用户看不到】btw-panel / btw-history-panel 的数据形状 | BtwHistoryTurn/BtwHistoryRecord + getBtwLatestTurn/getBtwTurns/getBtwCopyText（注：【用户看不到】类型/helper） | — | packages/tui/src/overlays/btw-history.ts:1-32 |
| omp | collapsed 小部件 | 有实验记录且未展开 | `autoresearch N runs K kept +M archived … \| best X baseline Y \| conf \| running/mode` + `ctrl+x expand`（注：后台实验小部件（折叠态）） | 展开或实验清空即换 | packages/tui/src/apps/autoresearch-dashboard.ts:270 |
| omp | running-only 行 | 首次实验在跑且无结果 | spinner `autoresearch running` + 时长 + `\| name \| command`（注：实验运行行） | 有结果后换成 collapsed | packages/tui/src/apps/autoresearch-dashboard.ts:260 |
| omp | expanded widget | `ctrl+x` 展开 | 卡片头 + summary kv + bars 图 + 最近 8 行 table + `… N earlier runs hidden` + 折叠提示（注：实验小部件展开态） | 收起即回一行 | packages/tui/src/apps/autoresearch-dashboard.ts:101 |
| omp | autoresearch overlay | `ctrl+shift+x` 打开浮层 | glass sheet `autoresearch: name`（lg）：summary/chart/全量 table + running 行 + 滚动键提示（注：实验浮层） | esc/q 关闭 | packages/tui/src/apps/autoresearch-dashboard.ts:136 |
| omp | summary kv | 有实验结果时 | Current segment / Baseline / Archived / Pending run / Mode / Best / Secondary（注：实验摘要 kv） | 无结果时换成 pending 文案 | packages/tui/src/apps/autoresearch-dashboard.ts:310 |
| omp | 实验表 | 有实验结果时 | 列 `# commit <metric> [secondary…] status description`，状态着色（注：实验表格） | maxRows>0 时只留最近 N 行 | packages/tui/src/apps/autoresearch-dashboard.ts:310 |
| omp | 趋势图 | 支持 chart 且可见行≥2 | bars 图，每 run 一柱，标注 `metric per run · best X`（注：实验趋势图） | 无 chart 能力则不出现 | packages/tui/src/apps/autoresearch-dashboard.ts:310 |
| omp | BTW history | /btw（不带问题）浏览本会话 BTW 历史 | lg 玻璃 sheet「BTW history」：左右两栏(list 42%宽 max46 ｜ answer)，行=状态(Running/Complete/…)+时间+问题（注：/btw 历史 sheet） | Esc 关闭；窄屏(≤96)只显左栏；列表高度不足时按行裁剪 | packages/tui/src/overlays/btw-history-panel.ts:68-93,363-420 |
| omp | collapsed 小部件 | 有实验记录且未展开 | `autoresearch N runs K kept +M archived … ｜ best X baseline Y ｜ conf ｜ running/mode` + `ctrl+x expand`（注：后台实验小部件（折叠态）） | 展开或实验清空即换 | packages/tui/src/apps/autoresearch-dashboard.ts:270 |
| omp | running-only 行 | 首次实验在跑且无结果 | spinner `autoresearch running` + 时长 + `｜ name ｜ command`（注：实验运行行） | 有结果后换成 collapsed | packages/tui/src/apps/autoresearch-dashboard.ts:260 |
| jcode | ⏰ 计划任务 | 非处理中且 reminder_count>0 | `⏰ next scheduled task {next}{ · N queued}` 蓝（注：doubt: 定时任务提醒；亦涉 M8 通知） | 无待办/处理中 | crates/jcode-tui/src/tui/ui_input.rs:1784-1792; mod.rs:89-101 |
| jcode | swarm strip（内联代理条） | inline swarm 激活且非 dock 接管（或面板聚焦），宽≥24 | 紧凑代理行列表；聚焦行展开 ~14 行（≤1/3 高，3..16） | 面板切页/dock 显示/窄于 24 列 | crates/jcode-tui/src/tui/ui.rs:2965-2997,3218-3222 |
| jcode | Todos（Todos 或 Plan） | todos 非空；右侧、最小高 3；todos 是 swarm plan 投影时标题变 Plan | 边框：Todos 3/7 ●●●○○○○ 左上（pip 米表≤10）+置信度右上，+N more 左下；体内每行一个 todo（⊳阻塞/✓/▶/✗/○、!高优先、分组头 完成/总数） | body 预算 clamp(1,5) 行；超出进 +N more 边框；空列表整块消失 | crates/jcode-tui/src/tui/info_widget.rs:128, crates/jcode-tui/src/tui/info_widget_todos.rs:499,540,620 |
| jcode | MemoryActivity（🧠 N memories） | 【用户看不到】MemoryInfo.should_render（!disabled 且 count>0 或有 activity）；左侧、最小高 3。生产恒为 None→[未核实实际出现] | 边框 🧠 N memories；体行 Now/Last: 状态摘要 · 龄；pipeline 4 步（Load memories/Jev relevance/Inject context/Update memory）；底边 recent trace（注：【用户看不到】死路径(未核实); doubt: 记忆；[未核实实际出现]） | 行数 truncate 到 inner.height；should_show_activity 仅处理中或完成 <5s；数据为 None 即消失 | crates/jcode-tui/src/tui/info_widget.rs:815, crates/jcode-tui/src/tui/info_widget_memory_render.rs:5, crates/jcode-tui/src/tui/app/tui_state.rs:1660 |
| jcode | BackgroundTasks（⏳ Background · N running） | background_info.running_count>0；左侧、最小高 2 | 边框 ⏳ Background · N running；体行最多 3 条任务（首条附 progress_detail），前导 • | 第 4 条起折叠，左下 +N more；running 归零即消失 | crates/jcode-tui/src/tui/info_widget.rs:1540, crates/jcode-tui/src/tui/info_widget_swarm_background.rs:66,200 |
| jcode | SwarmStatus（🐝 Swarm N/M active） | managed_members 非空（本会话在管 agent）才放置；左侧、最小高 3；管理时优先级提到 3 | 边框：🐝 Swarm N/M active 左上、⚠ N 需关注右上、+N more 左下、nodes x/y ▰▰▱▱ 右下；体行一 agent（✗/⠋/★/✓ + name + activity + todo 计数或龄） | 超 DOCK_MAX_ROWS=6 折 +N more；排序 关注→在跑→空闲→完成；无 managed agents 即消失 | crates/jcode-tui/src/tui/info_widget.rs:822, crates/jcode-tui/src/tui/info_widget_swarm_background.rs:196,299 |
| jcode | SwarmStatus 挂件（margin dock）与 strip stand-down | 本会话在管 agent；dock 与 strip 共享同一 members | dock 画在 margin（见①），inline strip 让位；stand-down 含 anchored 隐藏算 engaged + 2s linger | dock 移除 2s 后 strip 才回归；FullPage 时 dock 不参与 | crates/jcode-tui/src/tui/info_widget.rs:1035,1064, crates/jcode-tui/src/tui/ui.rs:2969 |
| jcode | overnight 卡 | role=overnight 且有进度卡负载 | 圆角进度卡；负载解析失败则退化为 system 渲染（注：doubt: 隔夜后台任务进度卡） | 无 | crates/jcode-tui/src/tui/ui_messages.rs:740 |
| jcode | smarm card（compact 单行形态，Background task progress） | scope=background_task 且为进度通知 | `◌ bg <label> · <task_id>` 或 `🐝 <label> · id` 圆角框 + 进度条 + `Latest status:` 提示（注：doubt: 后台任务进度卡） | model refresh 变体去掉提示行 | crates/jcode-tui/src/tui/ui_messages.rs:2841 |
| jcode | ◌ 模型刷新卡 | task_id=refresh-model-list 且 tool=catalog | `◌ model refresh · <label>` 圆角框 + 进度条（无 hint 行）（注：doubt: 后台刷新进度卡） | 无 | crates/jcode-tui/src/tui/ui_messages.rs:2860 |
| jcode | swarm-agent-snapshot 卡 | 标题为 `swarm-agent-snapshot` 且 content 为成员 JSON | 展开的 agent 卡片（label/状态/子 todo/工具意图，经 render_swarm_chat_cards） | JSON 解析失败则走后续通用分支 | crates/jcode-tui/src/tui/ui_messages.rs:3187 |
| jcode | 🧠 saved 记忆卡 | memory 存工具且非 Error | `🧠 saved (类别) · <tokens>` 圆角框 + 内容（宽 ≤72）（注：doubt: 记忆；亦涉 M5 工具卡） | 内容按显示宽切块换行 | crates/jcode-tui/src/tui/ui_messages.rs:3904 |
| jcode | 🧠 recalled 记忆卡 | memory 取工具且解析出 `- [类别] 内容` 条目 | `🧠 recalled N memories · <tokens>` 头 + 记忆 tile（注：doubt: 记忆） | 解析不出条目则退回普通工具行 | crates/jcode-tui/src/tui/ui_messages.rs:3937 |
| jcode | 聊天内联 todo 卡 | todo 工具输出（todo_read/todo_write）；pin_todos 开时该消息从正文隐藏 | 可选 plan 详情行 → 分组头或状态头 → 每项一行（状态 glyph+文本）；宽 <72 时 goal/plan 详情压 1 行 | 空表→压成单行 `  todo  no tasks`；每行按内宽省略号截断 | crates/jcode-tui/src/tui/ui_messages.rs:1094 |
| jcode | todo 评估更新卡 | todo 结果只含 plan/goal 变更（无 todo 列表） | plan 变更块 + 每 goal 的质量/反馈更新行 | 宽 <72 压成一行 | crates/jcode-tui/src/tui/ui_messages.rs:1631 |
| jcode | 置顶 todo band（sticky） | display.pin_todos=true 且滚动时 | viewport 顶部 sticky 区：todo 卡行 + 其后 bg 任务行；预算 = viewport/3 clamp 2..12 | 超预算显 `  … +N more (todo)`（点击展开全部） | crates/jcode-tui/src/tui/ui_viewport.rs:1384 |
| jcode | band 内 bg 任务行 | 有运行中/刚完成的后台任务（随 band 一起） | `◌ bg <label> ━╺── 62%`；完成 `✓ 100%`、失败 `× failed`（6 格条） | 从未占用的卡预算；label 截断保百分比 | crates/jcode-tui/src/tui/ui_viewport.rs:1432 |
| jcode | 内联 todo 归属（swarm 子卡） | batch 子调用里是 todo 工具且成功 | todo 卡整体右缩进 4 格嵌入子调用下方 | 解析失败则不嵌 | crates/jcode-tui/src/tui/ui_messages.rs:4275 |
| jcode | swarm strip（输入上方组件） | 有 swarm 成员且非 full page、且未被 dock widget 顶替 | vertical 布局最多 4 行 chips（含 `+N more` 行）或 horizontal 单行 chips；聚焦时尾部显示 Alt 键位提示（注：doubt: 子 agent 名册条） | 成员超出 4 行折入 `+N more`；dock 展示时 strip 让位（有 2s linger） | crates/jcode-tui/src/tui/info_widget_swarm_gallery.rs:499 |
