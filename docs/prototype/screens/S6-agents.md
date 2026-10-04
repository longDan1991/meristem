# 屏幕 · 多 agent 与自主（多 agent 与自主所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S6：omp 19 条 · jcode 7 条

## 两家在这一刻的对照（事实）

- omp 19 条 / jcode 7 条；omp 是 Agents hub / Roster / Detail-Inspector / Activity / Advisor 配置；jcode 是 goals 页、swarm 整页与 AmbientMode（死路径挂件）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Agents 全屏 hub | /agents（showAgentsDashboard） | 全屏「Agents」：sidebar(All agents N / 各 source N / New agent)、body(状态行 + 列表)、footer(chip strip) | Esc 关闭(逐级：strip→列表) | packages/tui/src/overlays/agents-hub.ts:1-11,193-300,1271-1280 |
| omp | Agent 列表行 | 列表视图 | 行：光标 + dot + 名字 + source tag，右侧 badge(Model/Prewalk/Advisor)；原生列 Model/Prewalk/Advisor/Source | 窄屏按列 priority 丢弃；type-to-filter 搜索 | packages/tui/src/overlays/agents-hub.ts:85-90,1076-1084,1470-1490 |
| omp | 属性 strip（配置） | Enter 选中 agent → 打开 strip；再 Enter 进属性值 strip | footer 变 chip 条：agent 级 [enable/disable, model, prewalk, advisor]；属性级 [agent default, on, off, pick model…, pattern…, clear override] | Esc 逐级回退(属性→agent→关)；选模型时车身换成 ModelBrowser | packages/tui/src/overlays/agents-hub.ts:455-540,822-856,1232-1244 |
| omp | 新建 agent 流程 | sidebar 选 New agent | body 换成描述输入 → 生成中 spinner + 流式 JSON → 预览(名称/when/sysprompt 折起)；footer [save, tab scope, r regenerate, esc cancel] | 保存后回列表；Esc 取消 | packages/tui/src/overlays/agents-hub.ts:1506-1540,1700-1720,1800-1836 |
| omp | 原生 picker 形态 | 终端支持 picker | sheet：title Agents、scopes=All agents/各 source、列 Model/Prewalk/Advisor/Source、preview 显示 Status/Source/路径/模式/System prompt 段；actions Toggle/Model/New agent/Reload/Close | Esc 关闭 | packages/tui/src/overlays/agents-hub.ts:1250-1290,1394-1465,1524-1560 |
| omp | Agent Hub · <id> 全屏 transcript | Agent Hub 中对非 live 的 parked subagent/advisor/guest 按 Enter（openChat），或点活动行 | 全屏 alt-screen：复用 ChatTranscriptBuilder 重放该 JSONL，头部「Agent Hub · <id>」+ stats 行(模型/时长/token/context%) | Esc 回 hub；Hub 切换键则连 hub 一起关；文件增长按 append 增量解析 | packages/tui/src/overlays/agent-transcript-viewer.ts:1-46,165-230,695-703 |
| omp | Agent Hub | alt+a（app.agents.hub）或 ctrl+s（app.session.observe） | overlayCard「Agent Hub」：顶部 tab(1 Agents \| 2 Activity) + 主体；宽≥96 时 roster/detail 双栏(58/42) | Esc/再按 hub 键关闭；窄屏 Tab 在 roster 与 inspector 间切换 | packages/tui/src/overlays/agent-hub.ts:108-115,119-121,320-433,695-698 |
| omp | Roster 列表 | Agents 分区 | 每行：状态 glyph + 名称 + 角色 badge + model chip + 指标列 Cost/Time/Req/Tools/Tok/Ctx(按 priority 隐藏)；选中行高亮；unread 计数；↳ parent 提示 | 窄屏逐列丢弃；行序固定不随心跳跳动 | packages/tui/src/overlays/agent-hub.ts:151-158,908-1030 |
| omp | Detail/Inspector 栏 | 选中某 agent（宽屏右栏） | kv 网格(指标/模型/context 用量条) + Recent activity 段(≤20 条) + child ids(≤12) | 无选择时显示「Select an agent to inspect」 | packages/tui/src/overlays/agent-hub.ts:140-143,967-1040,1287-1291 |
| omp | Activity 分区 | 切到 Activity tab | 活动行列表(response/tool/irc/lifecycle)，行有 glyph/摘要/时间；过滤 chip：Follow(space) / scope(s) / Search(/) / Close | Esc 关闭；空时「No response or tool activity yet」 | packages/tui/src/overlays/agent-hub.ts:159-162,1020-1076 |
| omp | 原生 picker 形态 | 终端支持 picker | sheet title Agents、tabs Agents/Activity、列见上、preview=side | Esc 关闭 | packages/tui/src/overlays/agent-hub.ts:845-853 |
| omp | roster 行/状态 glyph/角色 badge/metrics 文本 | 【用户看不到】被 agent-hub 与 agent-transcript-viewer 调用来画行 | statusGlyph/statusText/formatRoleBadge/modelBadge/formatMetrics/clampHubLine 等纯函数，无自有界面（注：【用户看不到】纯渲染 helper） | — | packages/tui/src/overlays/agent-hub-renderer.ts:29-99,143-268 |
| omp | metrics 聚合/tree 投影 | 【用户看不到】agent-hub 计算行指标与父子顺序 | aggregateMetrics/projectAgentTree/progressMetrics/hubRowMetrics 等纯函数（注：【用户看不到】纯数据 helper） | — | packages/tui/src/overlays/agent-hub-projection.ts:20-27,127-190 |
| omp | Advisor configuration | /advisor configure | 全屏：顶部标题「Advisor configuration · <scope>[ ● unsaved]」；list 屏=左栏 advisor 列表(SelectList) + 右栏预览(共享指令/凭证/配额)；其它屏=编辑表单（注：advisor（后台 agent）配置屏；疑点：亦近 S2 记忆技能） | Esc 逐屏回退/关闭；底部 footer 提示行 + 上下边框 | packages/tui/src/overlays/advisor-config.ts:279-300,379-430 |
| omp | 原生 prefs 页 | 终端支持 prefs（aside） | 每个 advisor 一页 + Shared instructions 页；Config problems 分节列出 dropped warnings；模型/工具/指令编辑器覆盖在页上 | Esc 关闭 | packages/tui/src/overlays/advisor-config.ts:404-420,451-460,539-545 |
| omp | 配额行（formatCompactQuota） | 预览 pane 显示 provider 配额时 | 一行紧凑 quota：provider + 用量/窗口/重置 | 无报告时不显示 | packages/tui/src/overlays/advisor-config.ts:132-160 |
| omp | ObservableSession 注册表 | 【用户看不到】被 agent-hub / agent-transcript-viewer 当作进度快照源 | 订阅 task:subagent:progress / lifecycle 频道，维护 ObservableSession 列表（注：【用户看不到】纯 helper） | — | packages/tui/src/overlays/session-observer-registry.ts:1-63 |
| omp | Agent hub 类型 | 【用户看不到】roster/inspector 的结构类型 | MAIN_AGENT_ID / AgentStatus / AgentMetricsSummary / AgentRecordLike / AgentHubRegistry / IrcBusLike（注：【用户看不到】类型） | — | packages/tui/src/overlays/agent-hub-types.ts:1-73 |
| omp | 活动索引模型 | 【用户看不到】agent-hub 的 Activity 分区数据源 | AgentActivityKind/Row/Query/Source + activityRowsFromProgress/activityOneLine（注：【用户看不到】类型/helper） | — | packages/tui/src/overlays/agent-activity.ts:1-60 |
| omp | Agent Hub | alt+a（app.agents.hub）或 ctrl+s（app.session.observe） | overlayCard「Agent Hub」：顶部 tab(1 Agents ｜ 2 Activity) + 主体；宽≥96 时 roster/detail 双栏(58/42) | Esc/再按 hub 键关闭；窄屏 Tab 在 roster 与 inspector 间切换 | packages/tui/src/overlays/agent-hub.ts:108-115,119-121,320-433,695-698 |
| jcode | AmbientMode（ambient 挂件） | 【用户看不到】已被硬禁用：widget_disabled 恒真 → 永不作为 margin 挂件出现 | (渲染函数存在) 图标+状态词在顶边、队列行/Ran…/Next run、底边 budget ▰▱ N%——但不可达（注：【用户看不到】死路径(已被硬禁用); doubt: 【用户看不到】死路径；自主模式挂件） | 恒不出现；ambient 状态改由状态行/输入行显示 | crates/jcode-tui/src/tui/info_widget.rs:732,1795, crates/jcode-tui/src/tui/ui_input.rs:1781 |
| jcode | goals 页（Goals） | /goals 或 goal 工具 list/update 触发 | 标题 Goals；每个 goal 一节：Status/Scope/Progress/Current milestone/Next step/Id | 无 goal 时写占位“No goals yet…”；刷新只更新已开着的 goals 页 | crates/jcode-base/src/goal.rs:258,384, crates/jcode-app-core/src/tool/goal.rs:167 |
| jcode | goal.<id> 页（Goal: <title>） | goal 工具 create/show/update 且 display≠None | 标题 Goal: <title>；Status/Scope/Updated/Progress + Description/Why/Success criteria/Current milestone 勾选/Milestones(→)/Next steps | UpdateOnly 只在页已开时刷新，否则不建页 | crates/jcode-base/src/goal.rs:328,334,395, crates/jcode-app-core/src/tool/goal.rs:325 |
| jcode | Chat 档（未聚焦 strip） | agents.swarm_spawn_mode=inline 且有 member；未聚焦、且 SwarmStatus dock 未在场 | 状态行上方一行 chips：🐝 swarm · ⠙ researcher 8/16 ✓ reviewer … 2/3 active · <ctrl+t> controls；选中项高亮 | chat 宽 <24 或 member 空即不画；dock 挂件在场则 stand-down（含 2s linger） | crates/jcode-tui/src/tui/ui.rs:2967, crates/jcode-tui/src/tui/app/tui_state.rs:2083, crates/jcode-tui-render/src/swarm_gallery.rs:558 |
| jcode | Controls 档（聚焦 strip） | cycle_swarm_panel_view 第一次（focused=true, full_page=false） | 同 chips 行 + 选中 agent 的展开详情（输出尾 + todo 列表），预算 ≤ chat 高/3（夹 3..16）+ 键位提示行 | 预算小退化为单行详情；Esc 回 Chat | crates/jcode-tui/src/tui/app/tui_state.rs:2091, crates/jcode-tui/src/tui/ui.rs:2977 |
| jcode | FullPage 档（整页 swarm） | cycle 第二次（focused=true, full_page=true）→ swarm_panel_full_page | 整个消息区被替换：🐝 swarm · N agents · M active + 键位行 + 按 report_back 归属的嵌套 agent 树 + 选中 agent 的 live 卡（elapsed/model/route/effort） | 再 cycle 回 Chat；member 空则自动回 Chat | crates/jcode-tui/src/tui/app/tui_state.rs:2104, crates/jcode-tui/src/tui/ui.rs:3311, crates/jcode-tui/src/tui/info_widget_swarm_gallery.rs:145,163 |
| jcode | swarm full page（整屏） | 进入 swarm 面板全页（Alt+n 等） | 头 `🐝 swarm · N agents · M active` + 键位行 + 所有权树 + 选中 agent 详情卡（注：doubt: swarm 整页） | esc 退出回 chat | crates/jcode-tui/src/tui/info_widget_swarm_gallery.rs:152 |
