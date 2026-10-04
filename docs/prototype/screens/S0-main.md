# 屏幕 · S0 主屏（两家）

> 这一面回答的是**主屏的空间结构**：从上到下有哪些区、谁固定谁滚、每个区几行、什么条件下出现、哪个区吃掉剩下的空间。
> 这是三面里唯一"人默认待着"的一屏（不是"进去"的屏）—— 三面里其余 12 个屏都是从这里进出的。
> 状态：两家的全貌（先例），**不含我们的判断**。逐条出处是仓根相对全路径。
> 相关但不同：`M1–M12` 是按「**什么时候**看到什么」切的（同一件事可能出现在主屏、也可能出现在别的屏）；本份只切**主屏这一块地方怎么分**。

## 0. 一句话对照

| | omp | jcode |
|---|---|---|
| 屏的拼法 | **一条竖着的流**：从顶到底 26 个区顺序排，正文区吃剩下的行 | **十段约束**：先算 `fixed_height` 总和，正文区吃剩下的行（`Min(3)`） |
| 行数总账 | **没有显式总账**：合成一个整屏后按 `drop = before + active + after - rows` **自顶裁掉溢出** | **有显式总账**：`fixed_height = 状态行 + 排队 + swarm + 通知 + 内联 + 间距 + 输入 + 事实行 + donut` |
| 滚动的归属 | **交给终端回看缓冲** —— 应用不接管滚动、**不探测**用户滚到哪，主屏**没有翻页键** | **应用自管**（alternate screen）—— `PageUp/PageDown` 一次 10 行；`Up/Down` 在输入为空时滚 1 行 |
| 顶上的头 | 身份卡在**正文流的最前头**，屏一满**它第一个被裁掉** | header 是**正文首部**（`chunks[0]`），跟着一起滚走；另有一条 sticky 行钉住**上一条 prompt** |
| 底下的带 | 状态条默认**嵌在输入框的顶边框上**（另有三种贴法） | 活动行 + 通知行 + 事实行**三条独立的行** |
| 边角空间 | 不用 | 15 种 info widget **只吃正文区的横向空白**（不占纵向行） |

---

## 1. omp 的区域清单（共 26 条）

| 次序 | 区 | 固定/条件/滚动 | 行预算 | 看到什么 | 出处 |
|---|---|---|---|---|---|
| 1 | 配置警告（header-before） | 条件 | 每条约 2 行（1 警告行 + 1 空行） | 配置有问题时的警告；默认不出现 | `packages/coding-agent/src/modes/interactive-mode.ts:2116` |
| 2 | 欢迎卡 / 身份卡（header 主体） | 固定 | 1（顶边框）+ max(左 11, 右) + 1（底边框）+ tip 行；开 LSP ≈20 行、关 LSP ≈14 行（随宽度与单双栏变） | 身份 + 版本 + 模型 + 提示 + 本机 LSP + 最近会话 4 条；**屏一满它第一个被裁掉** | `packages/tui/src/prompt/composer.ts:985` |
| 3 | What's New 卡（header-after） | 条件 | [未核实]（full 模式渲染整段 Markdown，行数不定） | 版本变更摘要 | `packages/coding-agent/src/modes/interactive-mode.ts:2116` |
| 4 | 正文 / 记录区 | **滚动** | **吃剩余行数**（`rows − 头部 − 下方 chrome 记账底线`） | 对话流；定稿的行一次性写进终端历史，视口只持有"活跃尾部" | `packages/tui/src/prompt/composer.ts:419` |
| 5 | 待发消息区（pending） | 条件 | 1 空行 + 组头 + 每条消息 1 行 + 编辑提示 1 行 | 模型在干活时你打的字排在这里 | `packages/tui/src/prompt/queued-messages.ts:1` |
| 6 | TODO HUD（完整形态） | 条件 | 1 空行 + `TODO` + 阶段块行 + 收尾轨行（折叠 `activeTaskCap=5`、`subsequentStageCap=4`） | 待办列表 | `packages/coding-agent/src/modes/interactive-mode.ts:4141` |
| 7 | Subagents 块 | 条件 | 2 头行 + 每 agent 1..2 行；折叠上限 `SUBAGENT_HUD_COLLAPSED_LIMIT=3` + 展开/收起行 | 在跑的 agent 名册 | `packages/coding-agent/src/modes/interactive-mode.ts:1076` |
| 8 | /btw 面板 | 条件 | [未核实]（面板自身行数） | 临时插入的旁枝对话 | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 9 | omfg 面板 | 条件 | [未核实]（面板自身行数） | 同上（另一种触发） | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 10 | cleanse 面板 | 条件 | [未核实]（面板自身行数） | 清理类任务的进度 | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 11 | 错误横幅 | 条件 | 组件自身行数 | 固定的错误条（钉住不滚） | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 12 | 模型循环轨道 | 条件 | 1 空行 + 1 行轨道 | 模型自动轮换的轨道指示 | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 13 | 延迟命令预览 | 条件 | 1 空行 + ≤maxRows(≥6 且 ≤视口 40%) + 1 提示行 | 延迟执行的那条命令的原样预览 | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 14 | 进度 HUD | 条件 | judgment-batch HUD 与 download HUD 各自行数之和 | 批量判断 / 下载的进度 | `packages/coding-agent/src/modes/interactive-mode.ts:1341` |
| 15 | 工作 loader 行（statusContainer·进行中） | 条件 | Loader 自带 1 空行 + 消息行数；右贴片同排 | `Working… (esc to interrupt)` 那一行 | `packages/coding-agent/src/modes/interactive-mode.ts:7389` |
| 16 | 空闲工作行（statusContainer·空闲） | 条件 | 2 行（空行 + 右对齐 trailer）；无 trailer 时 0 行 | 空闲时的 tok/s 等贴片 | `packages/coding-agent/src/modes/interactive-mode.ts:1341` |
| 17 | 重试提示行（statusContainer·重试） | 条件 | 1 行 | 接口失败后的重试提示 | `packages/coding-agent/src/modes/interactive-mode.ts:7549` |
| 18 | 紧凑 TODO 行（statusContainer·<18 行） | 条件 | 1 行（与工作行合并） | 屏幕很矮时待办压成一行 | `packages/coding-agent/src/modes/interactive-mode.ts:4345` |
| 19 | 附件贴片区 | 条件 | [未核实]（贴片带自身行数） | 粘贴的图片 / 文件贴片 | `packages/coding-agent/src/modes/interactive-mode.ts:1815` |
| 20 | 扩展挂件 · 编辑器上方 | 固定 | 空时 1 行；有挂件时 1 空行 + 挂件行（顶边框占用时那 1 空行塌缩为 0） | 扩展往这里挂东西（≤10 行） | `packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:348` |
| 21 | 输入框 | 固定 | 1..18 行（内容行 + 竖框 0/1/2 视形状） | 一屏唯一的文字入口 | `packages/coding-agent/src/modes/interactive-mode.ts:488` |
| 22 | 状态条 · 内嵌编辑器顶边框（默认形状） | 固定 | 1 行（占编辑器顶边框） | 段位串（模型 / 上下文 / git / 费用 …） | `packages/tui/src/status-line/component.ts:3168` |
| 23 | 状态条 · 顶规则芯片右组（另一种形状） | 条件 | 1 行（编辑器顶规则上，右侧） | 同上，换成顶规则上的右组芯片 | `packages/tui/src/status-line/component.ts:3588` |
| 24 | 扩展挂件 · 编辑器下方 | 条件 | 无挂件 0 行；有则挂件行数 | 扩展往这里挂东西 | `packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:348` |
| 25 | 状态条 · 独立底栏（另一种形状） | 条件 | 0..2 行（可选空行 + 1 栏行） | 同上，做成整屏最底一行 | `packages/tui/src/status-line/component.ts:3168` |
| 26 | 状态条 · hook 状态行 | 条件 | 每个 hook 状态 1 行 | 扩展 `setStatus` 写的状态 | `packages/coding-agent/src/modes/interactive-mode.ts:940` |

## 2. jcode 的区域清单（共 16 条）

| 次序 | 区 | 固定/条件/滚动 | 行预算 | 看到什么 | 出处 |
|---|---|---|---|---|---|
| 1 | Header（持久头 + 次级头） | **滚动** | ≥2（持久行 1..4 + 次级行 2..N，随 auth/mcp/skills/goal 变） | 身份 + 版本 + server/client + 模型 + `/login` provider 行 + mcp（≤4 + `N more`）+ skills（≤6 + `N more`）+ cwd(branch)；**是正文首部，跟着滚走** | `crates/jcode-tui/src/tui/ui_header.rs:632` |
| 2 | Sticky 上一个 prompt 预览 | 条件 | 1..2 行（超宽则 2 行） | 滚动离开顶部后，钉住"上一条我发的 prompt"首行 | `crates/jcode-tui/src/tui/ui_viewport.rs:1533` |
| 3 | Pinned todo 带 | 条件 | ≤1/3 视口，`clamp(2,12)` − 后台行数；溢出加 1 行 `… +N more (todo)` | 完整待办卡；宽度 <16 或视口 <3 时整段不画 | `crates/jcode-tui/src/tui/ui_viewport.rs:1384` |
| 4 | Pinned 后台任务行 | 条件 | 每任务 1 行，最多 2 行 | `◌/✓/× label [6 格进度条] 42%`；排在 todo 带下方、同一顶部带内 | `crates/jcode-tui/src/tui/ui_viewport.rs:1439` |
| 5 | 正文 transcript | **滚动** | **吃剩余行数**（`Min(3)`；装得下时按内容精确高度） | 应用自管的滚动窗口；可含锚定的内联图片；有原生滚动条时再让出右侧 1 列 | `crates/jcode-tui/src/tui/ui.rs:3203` |
| 6 | Info widgets 挂件（HUD） | 条件 | **0 行**（只吃正文区内的横向空白） | usage / todos / swarm / git 等挂件；不参与纵向排布、不挤压正文换行宽度 | `crates/jcode-tui/src/tui/info_widget_layout.rs:118` |
| 7 | 排队条 | 条件 | `min(3)` 行（0..3） | 最多 3 条待发 / 软打断 / 插入 / 排队；每条取前 100 字符；超过 3 条只显示前 3 | `crates/jcode-tui/src/tui/ui_input.rs:509` |
| 8 | Swarm strip | 条件 | `lines.len()`；竖排非聚焦上限 4 行（+`N more`），聚焦时 `clamp(正文高/3, 3, 16)` | 紧凑 agent 列表；聚焦时展开选中 agent 的实时尾巴与待办；正文宽 <24 时整条不画 | `crates/jcode-tui/src/tui/ui.rs:2996` |
| 9 | Status line（活动行） | **固定** | 1 行 | spinner + 当前活动；空闲为空 | `crates/jcode-tui/src/tui/ui_input.rs:774` |
| 10 | Notification line（通知行） | 条件 | 0/1 行（长提示按宽度换行后再 `min(正文高−4)`） | 警告 / 提示 / flicker / learn hint / 配额重置提示 | `crates/jcode-tui/src/tui/ui_input.rs:1928` |
| 11 | Inline UI 块 | 条件 | picker: `filtered+3` 最大 20；view: `lines+3` 最大 10 | 内联的选择器 / 视图（不是面板） | `crates/jcode-tui/src/tui/ui_inline.rs:9` |
| 12 | Inline UI / 输入 的间距 | 条件 | 1 行（仅内联块存在时） | —— | `crates/jcode-tui/src/tui/ui_inline.rs:9` |
| 13 | Input hint 行 | 条件 | 0/1 行 | 输入区顶部的一句提示（shell 模式 / 新会话路由 / `Ctrl+Enter` 语义） | `crates/jcode-tui/src/tui/ui_input.rs:394` |
| 14 | 输入框 | **固定** | 换行后的输入行数，上限 10 行 + hint | 一屏唯一的文字入口 | `crates/jcode-tui/src/tui/ui_input.rs:437` |
| 15 | 事实行 / session status line | **固定** | 1 行 | 目录 / 分支 / git / 上下文 / 鉴权 / provider / 模型 / 思考档 | `crates/jcode-tui/src/tui/ui_input.rs:1946` |
| 16 | Idle donut 动画 | 条件 | `14 − (输入高−1)` 行，否则不画 | 空闲时的动画 | `crates/jcode-tui/src/tui/ui_animations.rs:281` |

---

## 3. 五个"记账"问题（两家对照）

| 问题 | omp | jcode |
|---|---|---|
| **谁吃剩下的行** | 正文区（`rows − 头部 − 下方 chrome 底线`） | 正文区（`Constraint::Min(3)`；装得下时按内容精确高度） |
| **有没有行数总账** | **没有**：整屏合成后按 `drop = before + active + after − rows` **自顶裁掉溢出**（裁掉的可能是欢迎卡，也可能是正文头部） | **有**：`fixed_height = 1(状态) + 排队 + swarm + 通知 + 内联 + 间距 + 输入 + 事实行(1) + donut`，先扣固定的再给正文 |
| **滚动归谁** | 终端回看缓冲；应用**从不探测**用户滚到哪；**主屏无翻页键** | 应用自管（alternate screen）；`PageUp/PageDown` 10 行、`Up/Down` 输入空时 1 行 |
| **输入框的行数怎么定** | 独立预算：最大 18 / 最小 6，保留 `EDITOR_RESERVED_ROWS=12`、最小 chrome 4 行 | `基础输入高 + hint 行高`；输入框自身换行上限 10 行 |
| **多出来的东西往哪塞** | 往那条竖流里**插区**（26 个区里 20 个是条件区，从待发消息到 hook 状态行） | 往**三处**塞：正文区内的横向空白（挂件）、正文区内的纵向带（todo / 后台 / swarm）、输入区上下（排队 / 通知 / 内联 / hint） |

## 4. 空屏对照（还没有任何对话时）

| | omp | jcode |
|---|---|---|
| 顶 | 可选配置警告 → **欢迎卡**（身份 / 版本 / 模型 / 提示 / LSP / 最近会话 4 条，约 14–20 行）→ 可选 What's New | **顶部留白**（`pad_top = (高 − 5 − header 行数)/2`，可放 Updates 框）→ header 行 → 空行 → **建议项**（逐条 `[i] 标签`） |
| 中 | 空正文区 | 空正文区 |
| 底 | 输入框（1 行草稿）+ 状态条（默认嵌在输入框顶边框） | 输入框 + 事实行；空闲动画按剩余行数决定画不画 |
| 条件区 | 5–26 号条件区**全部不占位** | 条件区全部不占位 |
| 输入入口 | 输入行照旧 | 停在此页时**输入框还在**，可打字 |

## 5. 主屏独占的键（不含面板内部的键）

| | omp | jcode |
|---|---|---|
| 滚动 | **无**（交给终端） | `PageUp` / `PageDown` 10 行；`Up` / `Down` 输入空时 1 行；`Ctrl+L` 清屏（历史还在） |
| 说话 | `enter`（`esc` 打断当前这轮） | `enter` 立刻发；`Shift+Enter`/`Alt+Enter` 换行；处理中 `Ctrl+Enter` 反向发 |
| 展开 / 折叠 | `Ctrl+O` 展开收起、`Ctrl+Shift+O` 隐藏工具活动、`Ctrl+T` 思考 | 展开 / 折叠的键位见其键位表 |
| 名单 / 面板 | `?` 键位表、`/` 命令、`!` 跑 bash、`Alt+A` agent hub、`Alt+I` 挂件总开关 | `/` 命令、`Alt+I` 挂件总开关、`Alt+N` swarm 三档 |

## 6. 边角与分栏（占的是行还是列）

- **omp**：不用横向空白；**扩展挂件区**在输入框的上下各一条（≤10 行），是**纵向**占位。
- **jcode**：15 种 info widget **只吃正文区内的横向空白**（按每行渲染后的对齐算出的左/右空闲宽度放置），**不占纵向行、不挤压正文换行宽度**；`split_view` / diff / 图**只拿走左列的横向宽度**，纵向的行预算不变（换行随之变化）。
- **两家的共同点**：右下方向的"边角"都是**抢来的**，且都写成纪律 —— **没数据不画、没空间不画**。

## 7. 没查完的

- omp：`/btw` / omfg / cleanse / 错误横幅 / 附件贴片 / 进度 HUD 各区**内部**的行数与布局没展开（只给了定性范围）；What's New 在 full 模式下的行数不固定；原生（TSP）渲染下的 dock 次序与 ANSI 不同（挂件行被提到最前、待发消息被移到状态容器之后）。
- jcode：`server_events` 驱动的那部分界面效果没逐条穷举；分栏时各区的换行表现只给了规则、没有逐区实测。
- 两家都**没有在真实终端里跑过**（均为代码判读）。
