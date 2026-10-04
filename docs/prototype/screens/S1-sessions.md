# 屏幕 · 会话与历史（浏览、恢复会话所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S1：omp 22 条 · jcode 11 条

## 两家在这一刻的对照（事实）

- omp 22 条 / jcode 11 条；omp 是转录浏览器 / Session Tree / 多形态选择器（resume、copy、selectSession、原生 sheet），jcode 集中在 Session picker 一屏（标题栏、列表行、搜索、预览区、崩溃批量恢复横幅、Onboarding 动作带）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | TranscriptBrowser | 打开 /tree、/resume 等转录浏览器屏 | DynamicBorder 框+header+滚动 body(自动滚动条)+footer，行首缩进 1 | 屏关闭；body 至少 3 行 | packages/tui/src/chat/transcript-browser.ts:97 |
| omp | transcript-outline (outlineRows/composeOutlineColumn/positionRail) | 浏览器/选择器的点线大纲 | 「┆」边+点线 rule+可选 caption、positionRail「… ○ ◉ ○ …」（注：浏览器/选择器屏的点线大纲） | 由调用屏控制 | packages/tui/src/chat/transcript-outline.ts:169 |
| omp | Session Tree（/tree） | /tree 命令，或 app.session.tree 键(默认无绑定)，或双 Esc 且 cfgDoubleEscapeAction=tree | 面板：帮助行、搜索行、筛选 tab(Default/No tools/User only/Labeled/All)、树列表(层级缩进+标签 badge+active 路径点) | Esc 先清搜索再关闭；树为空时 100ms 后自动取消；可见行 ≤ 终端高/2 且留 8 行 chrome | packages/tui/src/overlays/tree-selector.ts:1325-1420,1538-1552 |
| omp | Label 输入行 | 按 shift+l（选中项上编辑标签） | 树容器下方换成单行 Input，Enter 保存 / Esc 取消 | 保存或取消后回到树 | packages/tui/src/overlays/tree-selector.ts:1275-1285 |
| omp | 原生 picker 形态 | 终端支持 picker | sheet「Session tree」：tabs=筛选、layout=tree、preview=side、actions=Switch/Summarize & switch/Label/Filter/Close | Esc 关闭 | packages/tui/src/overlays/tree-selector.ts:1449-1469 |
| omp | Resume Session 面板 | /resume（无参）、/resume @claude\|@codex；或 app.session.resume 键(默认无绑定)；或 `omp --resume` 独立进程(全屏) | 标题 Resume Session (current folder\|all projects)；scope tab、搜索行、会话列表、预览栏、键位提示 | Esc 取消；列表高度按终端行数自适应并 pin 底部 | packages/tui/src/overlays/session-selector.ts:1331-1450,1697-1700 |
| omp | 会话列表行 | 面板打开即见 | 每行：标题(或首条消息)、右值 日期 · 大小；pin 图标、fork badge、current 点、history badge；有 query 时按相关度，否则 Pinned/Today/Yesterday/This week/Earlier 分组 | 超出窗口滚动；空结果显示提示 | packages/tui/src/overlays/session-selector.ts:959-1010,1086-1097 |
| omp | 会话预览栏 | 选中项静止 60ms 后 | 标题 + kv 网格(Folder/Created/Modified/Size/Status/Forked from) + Conversation 段(首 prompt + 末段回答，各截 1200 字) | 随选择切换；截断到 PREVIEW_EXCERPT_CHARS | packages/tui/src/overlays/session-selector.ts:125-127,150-190 |
| omp | 删除确认 | ctrl+d 删除选中会话 | HookSelector 确认对话替换列表槽位(不是追加)，两个选项 | 确认/取消后回到列表 | packages/tui/src/overlays/session-selector.ts:1343-1356 |
| omp | Session info | /session info | 底部居中 md 玻璃 sheet，标题 Session info：正文为 kv 报告分节、ID 为可复制 mono 行、File 行可复制、可选 context 用量表 | Esc 关闭；内容超出可滚动 | packages/tui/src/overlays/session-info-overlay.ts:88-140,203-260 |
| omp | 回退选择器（全屏） | 双击 Esc（cfgDoubleEscapeAction 默认 rewind）或 app.session.fork 键 | alt-screen 重放整条分支，点状虚线框住将落到的 transcript 块；岔路口下方半宽分支条(当前路径在前)，Left/Right 缓动切换 | Esc 取消；A 加载更早轮次；不可渲染的条目(通知/隐藏 custom/折叠工具结果)永不描边 | packages/tui/src/overlays/rewind-selector.ts:1-30,93-154,159-165 |
| omp | 原生 picker 形态 | 终端支持 picker（Tern） | screen 形态：transcript 自身块 + pick/drop 标记替代虚线 | Esc 取消 | packages/tui/src/overlays/rewind-selector.ts:26-29,159+ |
| omp | History 搜索 | ctrl+r（app.history.search） | 面板标题 History；搜索行 + 结果行(提示词 + 相对时间/日期，匹配 token 高亮)；≤10 行(MAX_VISIBLE) | Esc 取消(空查询时可再按关) | packages/tui/src/overlays/history-search.ts:65-66,190-194,345-360 |
| omp | Copy 全屏选择器 | /copy（无参）；或内置 /annotate 自定义命令的消息选择（标题 Select message to annotate） | 全屏 alt-screen 重放分支，绿色点状框住当前 turn；底栏提示 ↑↓ step/enter copy/right blocks/a earlier turns/esc close | Esc 关闭；Enter 复制并关闭；A 加载更早轮次 | packages/tui/src/overlays/copy-selector.ts:1-13,317-319,690-820 |
| omp | 块视图(descend) | 按 Right 进入当前 turn | 该 turn 拆成带标题的块预览(code/quote/command/output/link)，每块 ≤12 行(BLOCK_PREVIEW_LINES)，标题带 ⧉ copy / ↗ open 控件 | Left/Esc 返回 turn 层 | packages/tui/src/overlays/copy-selector.ts:317,753-814,939-990 |
| omp | 原生 picker 形态 | 终端支持 picker | sheet「Copy」（或宿主标题）layout=timeline、preview=side、noun=turns | Esc 关闭 | packages/tui/src/overlays/copy-selector.ts:695-719 |
| omp | Code Review / Annotate Text 全屏 | 内置 /annotate 自定义命令（fullscreen.ts）；代码评审或文本评审两种构造 | 标题 Code Review（文本模式 Annotate Text）；文件侧栏(+add/-del/✎count)、diff/文本行区、模式行、动作列表(Continue/Paste)、注解行(✎)与注解编辑器 | Esc/完成即关；正文 ≥3 行；注解编辑器 ≤6 行后滚动；侧栏需宽≥64 且正文≥40 | packages/tui/src/overlays/annotation-overlay.ts:113-123,148-160,1150-1215 |
| omp | 原生 sheet | 终端支持 picker | overlayCard：lines 列表(diff/文本) + files 侧栏(≤34ch) + mode 行 + actions 列表 + 注解 chooser | Esc 关闭 | packages/tui/src/overlays/annotation-overlay.ts:1208-1215,1290-1300 |
| omp | copy 目标抽取 | 【用户看不到】被 copy-selector / rewind-selector / annotate 的 text-source 使用 | assistantText/extractBlocks(围栏代码与引用块)/LastCommand 等纯函数；也在 copy-selector 里定义 collectBlocks/targetCopy（注：【用户看不到】纯函数） | — | packages/tui/src/overlays/copy-targets.ts:1-63; packages/tui/src/overlays/copy-selector.ts:1054-1151 |
| omp | 评审数据类型 | 【用户看不到】annotation-overlay 的 diff/text 行与注解模型 | ReviewDiffRow/CodeReviewAnnotation/TextReviewAnnotation/结果类型（注：【用户看不到】类型） | — | packages/tui/src/overlays/annotation-types.ts:1-78 |
| omp | selectSession 全屏会话选择器 | `--resume` 等启动路径挑会话 | 全屏 overlay 会话列表：标题、scope 标签、cwd、pin、可删、全局范围、历史搜索（注：--resume 等启动路径的会话选择屏） | 选中返回会话；esc 取消返回 null | packages/tui/src/apps/session-picker.ts:35 |
| omp | session-picker overlay 配置 | 始终（挂载方式） | top-left + 100% 全屏 overlay，占备用屏，鼠标行可点（注：会话选择屏的挂载配置） | finish/exit 后 overlay.hide() | packages/tui/src/apps/session-picker.ts:87 |
| omp | Resume Session 面板 | /resume（无参）、/resume @claude｜@codex；或 app.session.resume 键(默认无绑定)；或 `omp --resume` 独立进程(全屏) | 标题 Resume Session (current folder｜all projects)；scope tab、搜索行、会话列表、预览栏、键位提示 | Esc 取消；列表高度按终端行数自适应并 pin 底部 | packages/tui/src/overlays/session-selector.ts:1331-1450,1697-1700 |
| jcode | catchup 页（Catch Up，ephemeral） | /catchup next 跳转某会话后（需共享 server 会话） | 标题 Catch Up；头 = 图标/名/状态/updated；Queue x of y、From；Why>引用；Your last prompt；What happened；What changed；Latest agent response；mermaid 流程图(features.mermaid) | 离开/再次抓取时由 snapshot_without_catchup 移除；不落盘 | crates/jcode-tui/src/tui/app/catchup.rs:6,70, crates/jcode-app-core/src/catchup.rs:104,120 |
| jcode | Session picker·标题栏 | picker 打开后每帧；按过滤/选中实时变化 | “N sessions”或 Active 视图“N active · ↻M working · ●K ready”+ 过滤器名 +“(s/S filter)”+“(+M hidden)”+“🔍query”+“✓N selected” | 窄终端截断；计数随可见行变化 | crates/jcode-tui/src/tui/session_picker/render.rs:439 |
| jcode | Session picker·会话项（列表行） | 每个可见会话项（选中行加底纹加粗） | 行1：○/●选择标+图标+标题(≤54字)+🔬/🧪/📌+状态图标词+时间+“标签”+来源徽标+[BATCH]+◀ current+▸ here；行2：N user · M assistant · ~X tok；可选 prompt 行(≤72字)；created+📁目录；崩溃加 reason 行（>54字截断） | 整项约3–6行；溢出列表右侧原生滚动条；标题/目录按字符数省略号 | crates/jcode-tui/src/tui/session_picker/render.rs:176 |
| jcode | Session picker·服务器/分组头 | 多 server 分组、孤儿会话组、Saved 组 | “⚡ 名字  vX · N sessions” / “📦 Other sessions  N sessions” / “📌 Saved  N” | 无（随分组出现） | crates/jcode-tui/src/tui/session_picker/render.rs:439（PickerItem::ServerHeader/OrphanHeader/SavedHeader 臂） |
| jcode | Session picker·搜索条 | search_active 或 query 非空 | “🔍 查询▎”+“Esc to clear”（激活）/“/ to edit”；列表标题另显示“🔍"query"” | 清空查询且退出搜索即隐藏 | crates/jcode-tui/src/tui/session_picker.rs:2247（render() 内） |
| jcode | Session picker·崩溃批量恢复横幅 | 检测到相关崩溃会话组（crashed_sessions） | 框“ R restore shown group · N relevant crashed session(s) detected(+ · X older skipped)”；💥 + 名字列表；“Press R (or B) to restore only this guessed recent group.” | 按 R/B 恢复或恢复完成 | crates/jcode-tui/src/tui/session_picker/render.rs:723 |
| jcode | Session picker·预览区（Preview）头部字段 | 选中会话（右栏 60%，焦点框色变化） | 框“ Preview ”；图标+短名+状态词(active/closed X ago/…/errored)；标题；📌Saved as"label"；📁dir；状态行 ▶/✓/💥/🔄/📦/⏳/❌；批恢复/多选标记行；分隔线 | 无会话→“No session selected”；加载中→“Loading preview…”；空→“(empty session)”；内容溢出加滚动条 | crates/jcode-tui/src/tui/session_picker.rs:1302（内容构建 :1553） |
| jcode | Session picker·预览区消息体 | 预览有消息 | 按 TUI 样式渲染每条 user/assistant 与工具调用/差异；仅渲染可见窗口 | 只显示可见窗口，滚动复用缓存；超出滚动条 | crates/jcode-tui/src/tui/session_picker.rs:1553 |
| jcode | Session picker·预览“上一条 prompt”粘性头 | 预览向上滚动使上一条用户 prompt 滚出顶部 | 顶部固定一条 dim 的“N› prompt 摘要”（长则折行） | 滚回底部或换会话 | crates/jcode-tui/src/tui/session_picker.rs:1999 |
| jcode | Session picker·Onboarding 动作带 | onboarding_banner 存在（列表为空时独占全屏） | 居中：提示句 + 检测到的登录 ✓ 列表 + pills“Import / Jcode subscription / Import less / Telemetry”+价格一行；或“Find bugs in my most active repo”/“Start in the current directory”（注：doubt: 会话 picker 内 onboarding；亦涉 S12） | 选择后进入 picker 或新会话；高度不足时整带降级 | crates/jcode-tui/src/tui/session_picker.rs:2098；激活 :750 |
| jcode | Remote·session picker 的服务器分组 | 远程 /resume 等打开 picker | 列表按 server 分组头“⚡ 名字  vX · N sessions”，下辖该 server 会话项 | 无远程分组时不出现 | crates/jcode-tui/src/tui/session_picker/render.rs:439（PickerItem::ServerHeader 臂） |
