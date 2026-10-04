# 组件 · M7 要我做决定（需要我选择或确认时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 16 条 · jcode 14 条

## 两家在这一刻的对照（事实）

- omp 16 条 / jcode 14 条；omp 有完整 picker 体系（通用选项/radio/checkbox/单行多行对话/standalone select/模型选择器）；jcode 以 palette 浮层 picker（Model/非 Model）+ 圆角框内联视图 + plan 卡 + Claude 接管模态

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | 大粘贴菜单 | 粘贴行数 ≥ paste.largeMenuThreshold | 标题 "Pasted N lines" + 3 选项（wrapped block / local file / inline）+ Esc 提示（注：粘贴大文本后的三选项菜单（wrapped/local/inline），需用户选择） | 选中或 Esc 即关 | packages/coding-agent/src/modes/controllers/input-controller.ts:2503 |
| omp | 裸命令二次确认提示 | 非空会话外单独输入裸命令词（input.bareSlashCommands） | "Press Enter again to run /x; add a leading space to send…"（注：需二次回车确认，属确认） | 其它键或提交后清除 | packages/coding-agent/src/modes/controllers/input-controller.ts:1044 |
| omp | CountdownTimer | 带 timeout 的对话框（ask/hook-input/hook-selector） | 标题里的「(Ns)」；native elapsed 节点自计时（注：带 timeout 对话框里的倒计时） | 到 0 触发 onExpire 并 dispose | packages/tui/src/chrome/countdown-timer.ts:8 |
| omp | 通用选项选择器 | 扩展 ui.select、会话删除确认(showHookSelector) | 标题 + 选项列表(每行 cursor/accent 高亮、description 第二行、可禁选变暗)，可搜索(status 行显示 n/total)、可选 slider 段轨、countdown | Esc 取消；列表窗口 maxVisible(默认 12，host 传 min(15, rows-12))；选中行整块 selectedBg 高亮 | packages/tui/src/overlays/hook-selector.ts:56-96,128-137,213-267,347-360 |
| omp | radio/checkbox 标记 | 调用方设置 selectionMarker | 前导 radio/checkbox glyph，cursor 行填充；markableCount 之后的控制行保留普通 cursor 前缀 | — | packages/tui/src/overlays/hook-selector.ts:83-96,365-380 |
| omp | 原生 picker 形态 | 终端支持 picker | docked picker：确认 Select + Close；total/empty「No matching options」 | Esc 关闭 | packages/tui/src/overlays/hook-selector.ts:714-724 |
| omp | 单行输入对话 | 扩展 ui.input / 需要一行文本时 | 面板标题=<title>(带倒计时时变「<title> (Ns)」)；一个 TextFormField + hint「enter submit  esc cancel」 | 超时自动取消；Enter 提交、Esc 取消 | packages/tui/src/overlays/hook-input.ts:28-55,84-101 |
| omp | 多行编辑器对话 | 扩展 ui.editor；ask 的 Custom answer / Note for <option> | 标题行(+把问题折成最多 3 行的 detail 行) + Editor(可带图、promptStyle 时 > 前缀) + hint(提交/取消/外部编辑器) | Esc 取消；编辑器最多 maxHeight(默认 终端行-12)行后滚动 | packages/tui/src/overlays/hook-editor.ts:39-52,120-183 |
| omp | Ask 对话 | 扩展 ask 工具 / ui.ask（extension-ui-controller#showLocalAskDialog） | 置于 editor 位置的面板「Ask」：header(问题标题≤4 行) / 分隔线 / body(选项列表+描述) / 分隔线 / footer(1 行)；多问题时顶部 tab 条，末页为 Submit 汇总 | Esc=Skip(取消)；body 至少 MIN_BODY_ROWS=5；选项描述默认 2 行，Ctrl+O 展开；对话框高 ≤ 终端 70% | packages/tui/src/overlays/ask-dialog.ts:116-127,530-620,690-710 |
| omp | 选项行 | 每个问题 | cursor + radio/checkbox 标记 + label(内联 md) + 最多 2 行描述 + 可选「✎ note」标记；其它行=自定义答案 | 描述超出 2 行折叠为展开提示 | packages/tui/src/overlays/ask-dialog.ts:222-244,431-470 |
| omp | 底部操作条 | 原生 sheet | Note(n) / Skip(esc) / Submit(enter)；有 timeout 时显示倒计时环「Ns」 | 提交/跳过即关；超时自动回答推荐项 | packages/tui/src/overlays/ask-dialog.ts:736-777,880-910 |
| omp | selectStandaloneItem 标题行 | 调用一次选择器时，先写 stdout | 正文上方一行标题，如 `Select what to cleanse:` | 立即滚入 scrollback，不重绘 | packages/tui/src/apps/standalone-picker.ts:126 |
| omp | StandaloneSelect 表单列表（ANSI） | 终端无 picker 能力时，一次性选择 | 单列 items：label + description；默认最多 10 行（cleanse 12） | 选中或 esc 后整屏拆除 | packages/tui/src/apps/standalone-picker.ts:78 |
| omp | SelectListSheet 选择面板（Tern picker） | Tern 支持 picker 时，同一提示换成 picker sheet | picker 面板：标题、副标题、搜索、图标、noun、确认词、当前项 | 确认或取消即关闭 | packages/tui/src/apps/standalone-picker.ts:95 |
| omp | promptStandaloneText 输入框 | 需要单行文本时 | 一个文本字段；回车提交 trim 后的值 | 提交或取消即拆屏 | packages/tui/src/apps/standalone-picker.ts:153 |
| omp | selectSetupModel 模型选择器 | `omp setup speech` 选 STT/TTS 模型 | 标题 + 单列模型项（最多 10），icon=model、noun=models、预选当前（注：omp setup 里选 STT/TTS 模型的 picker） | 选中返回；取消返回 null | packages/tui/src/apps/setup-model-picker.ts:15 |
| jcode | Model picker（走 palette 浮层，不占高） | PickerKind::Model 且 inline_interactive_state 存在 | MODEL/PROVIDER/CONFIG 三列 + 过滤/计数 + 路由提示（注：doubt: 内联 picker；亦涉 S2 模型） | Esc/选定后关闭 | crates/jcode-tui/src/tui/ui_inline.rs:10-18; ui_input.rs:215-254; ui_inline_interactive.rs:358-494 |
| jcode | 非 Model 交互 picker（圆角框） | PickerKind::Account/Login/Usage | 表头行+行列表，行数+3 且 ≤20（注：doubt: Account/Login/Usage picker；亦涉 S9） | Esc/选定后关闭 | crates/jcode-tui/src/tui/ui_inline.rs:9-27; ui_inline_interactive.rs:496-720 |
| jcode | picker 热键 hint 行（框外上方） | Model picker（含 runtime 模型行）且区域高>3 | `keys: Ctrl+O set default · Ctrl+N favorite …` 斜体灰 | 窄/矮时省略 | crates/jcode-tui/src/tui/ui_inline_interactive.rs:178-207,552-577 |
| jcode | picker 表头行 + 计数 | picker 打开 | 列名(焦点列高亮)+`"filter" (n/total)`+提交提示(+`Ctrl-O=set default`) | picker 关闭 | crates/jcode-tui/src/tui/ui_inline_interactive.rs:623-701 |
| jcode | picker 选中路由提示行 | Model picker 选中行有 detail（× / ⚠ / ⓘ） | 第二行提示，warning 橙 / 普通 dim 斜体 | 换行/无 detail 时不画 | crates/jcode-tui/src/tui/ui_inline_interactive.rs:148-176,717-724 |
| jcode | picker 行标记 ▸ / × / ⚠ | 每行 | 不可用 ×(红)、受限 ⚠、选中 ▸ | — | crates/jcode-tui/src/tui/ui_inline_interactive.rs:724-736,1124-1132 |
| jcode | picker "no matches" | 过滤后 filtered 为空 | `   no matches` dim 斜体 | 有匹配即替换 | crates/jcode-tui/src/tui/ui_inline_interactive.rs:729-736 |
| jcode | 被动内联视图 InlineView（圆角框） | 【用户看不到】[未核实] 生产无写入点，仅测试构造 | title + status + lines，高=行数+3 且 ≤10（注：【用户看不到】死路径(未核实); doubt: 【未核实】死路径；归内联块） | [未核实] | crates/jcode-tui/src/tui/ui_inline.rs:20-27,41-94 |
| jcode | 交互块与输入的间隔行 | inline_block_height>0 | 空 1 行，避免贴合 | 块关闭 | crates/jcode-tui/src/tui/ui.rs:3014,3196 |
| jcode | plan 卡（```plan 块）——transcript 而非侧栏页 | /plan 或模型输出 ```plan fenced block | 圆角卡（最多 100 宽），标题取首个 markdown 标题否则 ⛭ Plan；体内 markdown 正文 | 随 transcript 滚动；窄时按宽折行不截断 | crates/jcode-tui/src/tui/ui_messages.rs:213,221,254 |
| jcode | Session picker·Claude 接管确认模态 | 对 live Claude 会话按 T 后 | 居中框“ Explicit Claude takeover ”：被截12字的 session_id + 两行说明 +“Enter/Y confirm · Esc/N cancel”（注：doubt: 确认模态） | Enter/Y 确认；Esc/N 取消 | crates/jcode-tui/src/tui/session_picker.rs:2284 |
| jcode | 模型联想行（复用 palette 面） | inline picker kind=Model（/model 快速输入） | 顶部 hint + 逐行 marker + 模型名 + “ current” + “provider@method”列；无匹配→“No matching models for X” | 受输入框上方可用高度与 8 行限制 | crates/jcode-tui/src/tui/ui_inline_interactive.rs:361 |
| jcode | Remote·模型 picker（服务端目录） | 远程 /model；服务端尚未推 catalog（awaiting initial） | 路由来自服务端 available models（客户端补齐缺失 route，SSH 下不推断）；目录未到时显示等待（注：doubt: 内联模型 picker；亦涉 S2） | catalog 到达即刷新 | crates/jcode-tui/src/tui/app/inline_interactive.rs:1162/1254 |
| jcode | ```plan 卡片 | assistant 正文含 ```plan 围栏块 | 紫色圆角边框卡（宽 clamp 28..100），内嵌 markdown | 未闭合围栏（流式中）也按卡渲染 | crates/jcode-tui/src/tui/ui_messages.rs:221 |
