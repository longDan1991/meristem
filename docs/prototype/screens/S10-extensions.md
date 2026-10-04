# 屏幕 · 扩展与生态（扩展与生态所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S10：omp 16 条 · jcode 10 条

## 两家在这一刻的对照（事实）

- omp 16 条 / jcode 10 条；omp 是插件/扩展面板体系（列表、详情、Marketplace 详情、设置、Control Center、action bar）；jcode 是侧栏页（model、Managed Markdown、Linked 文件、全屏侧栏）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | PluginListComponent | Settings→Plugins 页 | 面板标题 Plugins；统一列出 npm 与 marketplace 插件行；空列表有提示；选择进入详情 | Esc 返回 | packages/tui/src/overlays/plugin-settings.ts:296-310 |
| omp | PluginDetailComponent | 从列表选中一个 npm 插件 | 插件详情：启用/禁用开关、feature 开关、config 设置项列表 | Esc/Back 返回列表 | packages/tui/src/overlays/plugin-settings.ts:489-500 |
| omp | MarketplacePluginDetailComponent | 从列表选中一个 marketplace 插件 | 同上形态，但 config 以插件名+key 写入 | Esc/Back 返回 | packages/tui/src/overlays/plugin-settings.ts:625-640 |
| omp | ConfigFieldPanel | 编辑某个 config 字段时 | 薄面板包住单个表单字段，标题保持 | 提交/取消后关闭 | packages/tui/src/overlays/plugin-settings.ts:753-760 |
| omp | PluginSettingsComponent | Settings 的 Plugins tab 打开 | 顶层容器，在列表/详情两个视图间切换 | 离开 tab | packages/tui/src/overlays/plugin-settings.ts:863-870 |
| omp | Plugins 选择器 | /marketplace install 或 /marketplace uninstall（无参时交互选择） | 面板标题 Plugins；行=name@version [installed] [user\|project]，description 为插件描述，marketplace 作右侧列；≤20 行；确认按钮 Install | Esc 取消；无插件时显示「No plugins available」+ 引导 /marketplace add | packages/tui/src/overlays/plugin-selector.ts:35-92 |
| omp | Extension Control Center | /extensions（showExtensionsDashboard） | 全屏 alt-screen：标题 Extension Control Center、provider TabBar、两栏(左=inventory 列表 / 右=inspector)；可搜索 | Esc 先清搜索再关闭；原生为 picker sheet(scopes=provider、preview=inspector) | packages/tui/src/overlays/extensions/extension-dashboard.ts:1-27,113-117,675-700 |
| omp | Action bar | 原生/页面形态 | Toggle(space/enter) / Expand(工具展开键) / Close(esc) | Esc 关闭 | packages/tui/src/overlays/extensions/extension-dashboard.ts:683-700 |
| omp | 库存列表 | dashboard 打开（provider tab 或 ALL） | 特定 provider 时 Row#0 为 Master Switch，其余为插件项；按 kind 分组标题；可 fuzzy 搜索；行有 on/off 状态 | 窗口 ≤DEFAULT_MAX_VISIBLE=15 行；master 关闭时其下所有项变暗 | packages/tui/src/overlays/extensions/extension-list.ts:1-59 |
| omp | 详情检查器 | dashboard 中选中一项 | 统一语法：identity → runtime/enablement → description → origin → kind 特有面 → 内容 → config；MCP 工具列表折叠预算(≤3 参数/3 行描述)；带预览段 | 超出按 PREVIEW_LIMITS 折叠；PageUp/Down 或滚轮滚动 | packages/tui/src/overlays/extensions/inspector-panel.ts:1-93 |
| omp | live tool 快照 | 【用户看不到】dashboard/list/inspector 每帧取一次工具快照 | listLiveToolRecords/liveToolRecordFromSession/snapshotToolRuntimeSource（注：【用户看不到】helper） | — | packages/tui/src/overlays/extensions/live-tool-session.ts:1-63 |
| omp | MCP 运行时视图模型 | 【用户看不到】dashboard 把 config 与 live 连接按名字 join | MCPServerDisplay/MCPConnectionDisplay/formatMcpHealthLabel/snapshotMcpRuntime（注：【用户看不到】helper） | — | packages/tui/src/overlays/extensions/mcp-runtime.ts:1-63 |
| omp | dashboard 纯状态机 | 【用户看不到】过滤/树/选择状态 | resolveExtensionState/buildSidebarTree/applyFilter/refreshState/createInitialState（注：【用户看不到】helper） | — | packages/tui/src/overlays/extensions/state-manager.ts:1-43 |
| omp | 扩展面板类型 | 【用户看不到】dashboard 的 Extension/ExtensionKind/ExtensionState/ProviderTab | 10 种 kind（extension-module/skill/rule/tool/mcp/prompt/instruction/context-file/hook/slash-command）（注：【用户看不到】类型） | — | packages/tui/src/overlays/extensions/types.ts:1-63 |
| omp | kind 专用视图模型 | 【用户看不到】inspector 按 kind 生成 surface/contents/config | toolInspectorData/commandInspectorData/skillInspectorData/ruleInspectorData/hookInspectorData/promptInspectorData/contextInspectorData/toolParamsFromSchema（注：【用户看不到】helper） | — | packages/tui/src/overlays/extensions/inspector-model.ts:1-48 |
| omp | 扩展显示串净化 | 【用户看不到】dashboard/inspector 渲染前剥 ANSI/C0-C1 并展开 tab | sanitizeDisplayText/Line/SingleLine/Field（注：【用户看不到】helper） | — | packages/tui/src/overlays/extensions/display-text.ts:1-32 |
| omp | Plugins 选择器 | /marketplace install 或 /marketplace uninstall（无参时交互选择） | 面板标题 Plugins；行=name@version [installed] [user｜project]，description 为插件描述，marketplace 作右侧列；≤20 行；确认按钮 Install | Esc 取消；无插件时显示「No plugins available」+ 引导 /marketplace add | packages/tui/src/overlays/plugin-selector.ts:35-92 |
| jcode | 侧栏页 model + upsert | side_panel 工具 write/append/load/focus/delete；或 decorate_* 每帧注入 ephemeral 页 | 按 page.id 键 upsert（存在则覆盖，否则 push）；源分 Managed/LinkedFile/Ephemeral；格式 Markdown/Pdf（注：doubt: 侧栏=工具/扩展内容面） | delete 移除；page_id 相同即覆盖，不会重复堆叠 | crates/jcode-base/src/side_panel.rs:279,216, jcode-side-panel-types/src/lib.rs:30,64 |
| jcode | 侧栏可见页数 = 1（focused_page） | snapshot.focused_page_id 命中 pages 中某页 | 只渲染 focused 页；其余页仅出现在头部 N/M 计数里 | focused_page_id=None 或 pages 空 → 整栏不画 | crates/jcode-side-panel-types/src/lib.rs:21,78, crates/jcode-tui/src/tui/ui_pinned.rs:534 |
| jcode | 侧栏头部（side <title> N/M …） | 区域宽≥10、高≥3 | 左边框： side <title> N/M <Alt+M 键> fullscreen；聚焦时加 j/k scroll、Tab/Shift-Tab pages、Esc focus chat；有可滚图再加 readable scroll / h/l pan +/- zoom / zoom N% | 宽<10 或高<3 整块不画；右槽与左槽冲突时右槽丢弃 | crates/jcode-tui/src/tui/ui_pinned.rs:522,571-620 |
| jcode | 翻页 Tab / Shift-Tab | 侧栏聚焦且 pages ≥2 | focused_page_id 循环到相邻页（rem_euclid），滚动归零 | 仅 1 页时按键无效 | crates/jcode-tui/src/tui/app/navigation.rs:615, crates/jcode-tui/src/tui/app/navigation.rs:585 |
| jcode | 空白侧栏 | pages 为空 | 不绘制右栏；Alt+M 给出状态提示 “Side panel: no pages (<图键> toggles diagrams)” | 有任意页后即可显示 | crates/jcode-tui/src/tui/app/navigation.rs:1119,1177, crates/jcode-tui/src/tui/ui.rs:2809 |
| jcode | Managed Markdown 页（side_panel write/append） | 工具写页；focus 时聚焦 | 页标题=传入 title，内容=Markdown 渲染（可含 mermaid 内联图） | delete 或会话切换清空 | crates/jcode-base/src/side_panel.rs:21,29, jcode-app-core/src/tool/side_panel.rs:92 |
| jcode | Linked 文件页（.md / .pdf） | side_panel load <file>；LinkedFile 源 | Markdown 原样；PDF 走 Pdf 格式（旧客户端降级为 Markdown fallback），聚焦时按 perf 间隔轮询源文件变化 | 源文件修订未变不刷新；超 MAX_PDF_BYTES(20MB)/总预算 32MB 时降级 | crates/jcode-base/src/side_panel.rs:56,96, crates/jcode-app-core/src/server/client_writer.rs:9 |
| jcode | linked-markdown:<abs path> 页 | 在 transcript 点击仓内 .md 链接；禁止仓外/Scheme/绝对路径 | 标题=文件名，内容=文件原文；打开后强制聚焦并抢占焦点 | 文件不存在/仓外 → 只给状态提示，不建页 | crates/jcode-tui/src/tui/app/navigation.rs:270,314,332 |
| jcode | 侧栏页表面（Markdown/PDF） | focused_page 存在（且非 swarm 全页）→ has_side_panel_content | 占右栏，宽 = chat_area.width × ratio，ratio 夹 25..100，最小 30，最大 chat−20；画左侧 rail | 无 focused 页；或全屏时改为占满整个消息区 | crates/jcode-tui/src/tui/ui.rs:2809,2884, crates/jcode-tui/src/tui/ui_pinned_utils.rs:20 |
| jcode | 全屏侧栏 | Alt+M 第二档（side_panel_fullscreen） | 侧栏占满 messages_area 全宽全高，状态行与输入框保留，transcript 不绘制（注：doubt: 侧栏全屏） | 再按 Alt+M 转 hidden，或 focused 页消失自动取消全屏 | crates/jcode-tui/src/tui/ui.rs:2815,3293, crates/jcode-tui/src/tui/app/navigation.rs:1128 |
