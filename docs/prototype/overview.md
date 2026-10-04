# 总体 · 三个面（屏幕 / 组件 / 命令）—— 两家的全貌 + 功能模块优先级

> 这一份是原型档的总体：产品按**三个面**描述 —— **屏幕**（用户会"在"那里的整块）· **组件**（用户在**什么时候**看到了什么）· **命令**（用户"敲"出来的功能）。
> **这一步只做一件事：把两家的全貌摆清楚** —— 他们有什么、什么时候看到什么、怎么做、代价是什么。我们的判断与决策不是这一份的事；**第二步按 §三 的优先级逐块对比两家、做决策、写原型**。
> 逐条证据：命令在 [`reference/`](reference/)（注册表级，472 条按意图归位）；界面在 [`screens/`](screens/) 与 [`components/`](components/)（每条带"什么时候看到 / 看到什么 / 什么时候消失"与出处）。
> 依据 `docs/DESIGN.md` §2 / §3 / §5 / §7 / §9。

---

# 一、三个面（模块清单）

判据（沿用前几轮）：
- **屏幕** = 一屏一屏地看产品：**主屏**（默认待着的那一屏）+ **其余那些"会进去"的屏**（一个键进去、一个键出来，通常顶掉正文或压在正文上）。
- **组件** = 出现在某个时刻的块（带 / 卡 / 徽标 / 提示 / 内联控件）—— **不要求跨屏复用**，只要"用户在那个时刻看到了它"。
- **命令** = 用户"敲"出来的功能，按**用户想干什么**分 17 类。

## 1.1 屏幕面（S0 + S1–S12）

**主屏（S0）是特殊的第一个**：它不是"要进去"的屏 —— 人打开就待在那里（95% 的时间）。S1–S12 是**其余**的屏：一个键/一条命令进去、一个键出来。

| id | 它是什么 | omp | jcode | 文档 |
|---|---|---|---|---|
| **S0** | **主屏**：默认待着的那一屏 —— **从上到下有哪些区、谁固定谁滚、每个区几行、空屏长什么样** | 26 | 16 | [`screens/S0-main.md`](screens/S0-main.md) |
| **S1** | 会话与历史：选择器 / 树 / 分叉回退 / 收藏命名 / 导出 / 历史搜索 | 22 | 11 | [`screens/S1-sessions.md`](screens/S1-sessions.md) |
| **S2** | 模型与给养：模型选择 / 思考档 / 档位传输 / provider / 记忆技能 / 压缩 | 10 | 1 | [`screens/S2-model.md`](screens/S2-model.md) |
| **S3** | 这一轮：审批 / 计划 / 队列模式 / 暂停 | 9 | 1 | [`screens/S3-turn.md`](screens/S3-turn.md) |
| **S4** | 工具与权限：工具开关 / MCP / 远端 / 别的"手" | 2 | 1 | [`screens/S4-tools.md`](screens/S4-tools.md) |
| **S5** | 仓库：git / diff / 提交 / worktree / issue | 21 | 2 | [`screens/S5-repo.md`](screens/S5-repo.md) |
| **S6** | 多 agent 与自主：agent hub / swarm / 目标 / 自评 / 日程 | 19 | 7 | [`screens/S6-agents.md`](screens/S6-agents.md) |
| **S7** | 界面与外观：主题 / 颜色 / 形态 / 布局 / 键位 / 显示开关 | 12 | 3 | [`screens/S7-look.md`](screens/S7-look.md) |
| **S8** | 协作与多端：云 / 分享 / workspace / 协作 | 0 | 2 | [`screens/S8-collab.md`](screens/S8-collab.md) |
| **S9** | 账号与计费：登录 / 账号 / 用量 / 订阅 | 13 | 7 | [`screens/S9-account.md`](screens/S9-account.md) |
| **S10** | 扩展与生态：插件 / 市场 / 扩展 / hooks | 16 | 10 | [`screens/S10-extensions.md`](screens/S10-extensions.md) |
| **S11** | 诊断与调试：日志 / 探针 / 性能 / 统计 / 自检 | 39 | 2 | [`screens/S11-diagnostics.md`](screens/S11-diagnostics.md) |
| **S12** | 首启与帮助：向导 / 启动 / 终端接入 / 帮助 / 键位表 / 关于 | 15 | 16 | [`screens/S12-setup-help.md`](screens/S12-setup-help.md) |
| **合计** | （含 S0 主屏 26 / 16） | **204** | **79** | |

## 1.2 组件面（M1–M12，用户在什么时候看到了什么）

| id | 它是什么（什么时候） | omp | jcode | 文档 |
|---|---|---|---|---|
| **M1** | 开场与空闲：第一次打开 / 空会话 / 欢迎与建议 | 6 | 6 | [`components/M1-open.md`](components/M1-open.md) |
| **M2** | 打字的时候：输入框 / 光标 / 补全 / 提及附件 / 前缀 | 49 | 26 | [`components/M2-typing.md`](components/M2-typing.md) |
| **M3** | 排队与待发：排队条 / pending / 取回 | 8 | 8 | [`components/M3-queued.md`](components/M3-queued.md) |
| **M4** | 它在说话：流式 / 思考 / markdown·diff·图 / 消息角色 | 27 | 18 | [`components/M4-streaming.md`](components/M4-streaming.md) |
| **M5** | 它伸手：工具行与卡 / 行数降级 / 输出 / 后台 | 41 | 16 | [`components/M5-tools.md`](components/M5-tools.md) |
| **M6** | 它在动：活动行 / loader / tps / 阶段 / 限流 / 计时 | 19 | 18 | [`components/M6-activity.md`](components/M6-activity.md) |
| **M7** | 要我做决定：审批 / 询问 / 内联 picker / 确认 | 16 | 14 | [`components/M7-decisions.md`](components/M7-decisions.md) |
| **M8** | 完事的时候：结果 / 摘要 / recap / 通知卡 / 徽标 | 30 | 16 | [`components/M8-done.md`](components/M8-done.md) |
| **M9** | 出问题的时候：错误 / 失败 / 重试 / 断开 / 缓存失效 | 11 | 10 | [`components/M9-errors.md`](components/M9-errors.md) |
| **M10** | 我站在哪、花了多少：状态带 / 事实带 / 段位 / 阶梯 | 68 | 22 | [`components/M10-status.md`](components/M10-status.md) |
| **M11** | 会话层面的东西：待办 / 目标 / 记忆 / 子 agent / 后台任务 | 34 | 19 | [`components/M11-session.md`](components/M11-session.md) |
| **M12** | 系统与视觉：更新 / 系统消息 / 鼠标滚动 / 动画 | 17 | 36 | [`components/M12-system.md`](components/M12-system.md) |
| **合计** | | **326** | **209** | |

## 1.3 命令面（A–Q，用户"敲"出来的功能）

| id | 它是什么 | omp | jcode | 文档 |
|---|---|---|---|---|
| **A** | 会话：这条线 / 这段对话本身 | 19 | 20 | [`commands/A-session.md`](commands/A-session.md) |
| **B** | 模型与给养：用哪个脑子、哪套注意力、多少上下文 | 60 | 24 | [`commands/B-model.md`](commands/B-model.md) |
| **C** | 对话进行时：控制此刻这一轮 | 18 | 5 | [`commands/C-turn.md`](commands/C-turn.md) |
| **D** | 工具与权限：能伸出哪些手、要不要先问人 | 52 | 12 | [`commands/D-tools.md`](commands/D-tools.md) |
| **E** | 代码与仓库：分支 / 提交 / 评审 / issue | 5 | 9 | [`commands/E-repo.md`](commands/E-repo.md) |
| **F** | 自主与自动化：目标 / 循环 / swarm / 自裁判 | 22 | 19 | [`commands/F-autonomy.md`](commands/F-autonomy.md) |
| **G** | 界面与外观：主题 / 状态条 / 键位 / 显示开关 | 1 | 13 | [`commands/G-interface.md`](commands/G-interface.md) |
| **H** | 协作与分享：多端 / 云 / 分享 / workspace | 17 | 23 | [`commands/H-collab.md`](commands/H-collab.md) |
| **I** | 账号与计费：登录 / 多账号 / 用量 / 订阅 | 14 | 21 | [`commands/I-account.md`](commands/I-account.md) |
| **J** | 扩展与集成：插件 / 市场 / 扩展 / 自建命令 | 19 | 1 | [`commands/J-extensions.md`](commands/J-extensions.md) |
| **K** | 诊断与调试：日志 / 调试面板 / 遥测 / 自检 | 10 | 19 | [`commands/K-diagnostics.md`](commands/K-diagnostics.md) |
| **L** | 系统与自维护：更新 / 重启 / 发布 / 首启 | 8 | 21 | [`commands/L-system.md`](commands/L-system.md) |
| **M** | 帮助与元：帮助 / 版本 / 反馈 / 隐藏命令 | 6 | 9 | [`commands/M-meta.md`](commands/M-meta.md) |
| **N** | 特殊输入前缀（不是命令，不计数） | — | — | [`commands/N-input-prefixes.md`](commands/N-input-prefixes.md) |
| **O** | 进程与服务：服务端 / 桥接 / 后台进程 | 4 | 11 | [`commands/O-processes.md`](commands/O-processes.md) |
| **P** | 基准与实验 | 3 | 0 | [`commands/P-benchmarks.md`](commands/P-benchmarks.md) |
| **Q** | 其它内部工具（兜底） | 5 | 2 | [`commands/Q-internal-tools.md`](commands/Q-internal-tools.md) |
| **合计** | | **263** | **209** | |

---

# 二、两家的对照（只讲他们）

## 2.1 用户视角原样（各自打开后看到什么）

### omp

1. **打开** → 顶上出现一张"身份卡"：omp 大字 + `Welcome back!` + `?` 快捷键 / `/` 命令 / `!` 跑 bash + 本机已连的 LSP + **最近会话 4 条**。屏幕一满，这张卡**第一个退场**（`packages/tui/src/prompt/composer.ts:635-636`）。
2. **说一句话** → 这句话**立刻画在正文末尾**，不等模型（乐观提交；原话：`Optimistic user submissions call renderNow() before agent dispatch so synchronous startup/model work cannot delay the visible user row.`，`docs/tui-runtime-internals.md:39`）。模型还在答时打的字先排在一块 pending 区里（`interactive-mode.ts:1710`）。
3. **模型在干活的这一段时间** → 编辑器上方出现一行 working loader（官方截图里是 `⣿ Working... (esc to interrupt)`）；想打断按 `esc`。
4. **想看给养** → 最底一行状态条：**段位可配置**（预设：`pi / vim / hostname / model / mode / path / git / pr / subagents`），某段没数据就不画（`status-line/presets.ts:37`、`segments.ts:517-525`）；它还可以贴在编辑器顶边框上、或做成独立底栏（`docs/extensions.md:837-839`）。
5. **模型伸手调工具** → 正文里多一张工具卡；**这张卡自己会按屏幕还剩几行变形**：≥3 行画全、2 行折成摘要卡、1 行只剩活动行、0 行直接隐藏（`docs/tui-runtime-internals.md:63-66`）；`Ctrl+O` 展开。
6. **在跑的活多起来** → 编辑器上方出现钉住的 `Subagents` 块（**默认折叠 3 行** + `… N more — expand`），状态条上多一个计数徽标（**0 时不画**）；点某一行、或按 `Alt+A` → 全屏 **Agent Hub**：一行一个 agent（状态 `running/idle/parked/aborted`、身份、父、模型、年龄、任务、成本/时长/token；缺数据写 `usage —` 不估），`t` 切平铺 / 父子树，`Enter` 把主界面**切到那个 agent 的会话**，`Esc` 回来（`docs/agent-hub.md:26-42,44-67`）。
7. **想回到历史某个点继续** → `/tree` 打开 **Session Tree**：它**换掉输入框那一格**（不是弹层、不常驻）；`•` 标出当前活跃路径、`[label]` 是标签；五档过滤 + 模糊搜索；行数只有屏幕高的一半（`docs/tree.md:3,38-40,55-57`）。选中一句人说的话 → **把那条话回填到输入框**、位置退回它的父节点（`docs/tree.md:129-159`）。
8. **想换会话** → `/resume` 全屏选择器（字段比欢迎屏那份多得多）。
9. **想少看点噪音** → `Ctrl+O` 展开 / 收起、`Ctrl+Shift+O` 隐藏工具活动、`Ctrl+T` 思考。
10. **屏幕被填满** → 顶上的行**滚进终端自己的回看缓冲**；应用不接管滚动、也**不探测**用户滚到哪，所以主屏**没有翻页键**（`docs/tui-core-renderer.md:107-109`）。

### jcode

1. **打开** → 空屏不是留白：一张 header（身份 / 模型 / 鉴权）+ **建议卡**（新用户给 3 条示例），末尾 `Press 1-N or type anything to start`；首次引导会整屏接管，但停在建议页时**输入框还在**（`ui_prepare.rs:844-912`）。
2. **说一句话** → `Enter` **立刻插话**（模型正在答也能插）；`Shift+Enter` 是**排队**：输入上方出现排队预览（≤3 行，带 `↻ / ⚡ / ⏳` 标记），`Ctrl+Up` 能把排队的话**取回输入框**改。
3. **模型在答** → 输入上方一条**活动行**：`sending / connecting / thinking / streaming`（带 tps、`↑in ↓out`、传输）/ `RunningTool`（带 `<alt+B> bg`）/ 网络断了在重试 / 被限流；某阶段超 10 秒变黄；空闲时改成一句提示（`ui_input.rs:774-1075`）。
4. **想看自己在哪、烧了多少** → 最底一行**事实行**：目录 / 分支 / git / 上下文 / 鉴权 / provider / 模型 / 思考档；窄了按写死的 **10 级阶梯**（`OVERSCROLL_LADDER`）一步步压到放得下，其中**目录、模型、上下文用量永不隐藏、只变短**（`ui_input.rs:2020-2040`）。
5. **屏幕右边空着** → 自动挂 **info widgets**（15 种：待办 / 记忆 / swarm dock / 后台任务 / 配额 / KV 缓存 / 变更文件 / 最近提交 / 工作区图 / 图 …）；**没数据不画、没空间也不画**，`Alt+I` 一个总开关；每个挂件的边框四角都用来放标题 / 统计 / 溢出计数 / 进度条（`info_widget.rs:1263-1265`）。
6. **想边读边看别的** → 右侧分栏（三选一，互斥）：agent 写的 Markdown / PDF（`Alt+M` 循环 分栏 / 全屏 / 隐藏，`Ctrl+1..4` 调宽）/ 文件 diff / 图（`Alt+T` 换上下或左右）。**全屏时顶掉正文区，状态行与输入还在**（`ui.rs:2814-2815`）。
7. **想看谁在跑** → 状态行上方一条 **swarm 条**。**同一块东西有三个尺寸**，一个键（默认 `Alt+N`）循环：**Chat**（未聚焦）＝**一行一只 agent 的短名单**（默认 vertical；最多 4 行，超了折 `+N more`；每行 `<字形> <图标/名字>[ · 当前任务][ 待办 d/t]`，首行左 `🐝 `、右 `M/N active · Alt+N controls`；**不画选中**）→ **Controls**（聚焦）＝**同一份名单**，只多三样：选中行前 `▸ ` 且加粗、**选中那行下面就地插入详情卡**（待办滑动窗 4 条，正在做的那条下面嵌最近 3 条工具活动；没有待办时退化成该 agent 的现场尾巴）、末尾一行键位提示；预算 `(聊天高/3).clamp(3,16)` → **整个消息区被替换成 swarm 全页**（`🐝 swarm · N agents · M active` + 键位行 + **按 report_back 归属的嵌套 agent 树** + 选中 agent 的 live 卡；FullPage）（`tui_state.rs:2075-2115` 三档枚举与循环 · `swarm_gallery.rs:891+`（strip 三档共用这一处渲染）· `jcode-tui-render/src/swarm_gallery.rs:1119`（accordion 就地插入）· `info_widget_swarm_gallery.rs:152`（全页）· `ui.rs:2969-2993`（条的唯一调用点））。
8. **想对某个 agent 做事** → 只有 4 个键：选、在新终端打开、改路由 prompt、退出；**普通打字照样进输入框**（`tui_state.rs:2185-2192`）。
9. **让长命令别挡路** → `Alt+B` 把正在跑的工具丢进后台；后台任务出现在 pinned 一行（6 格进度条，**只留最近 2 条**）+ 正文里一张卡（退出码 / 时长 / 最多 4 行预览 / `… +N more lines`）。
10. **换会话 / 同时开一堆** → `/resume` 全屏双栏（列表 + 预览；`Space` 多选、`Enter` 就地、`Ctrl+Enter` 新终端、`s/S` 循环过滤、`/` 搜索）；`/active` 只看活着的，并把"可以输入了"排在"还在跑"前面；workspace 用 `Alt+H/J/K/L` 平移，**整个界面换成那个会话**（正在处理时**拒绝移动**）。
11. **别人 / 别的 agent 找它** → 消息以**卡片**进正文（`DM from` / `Task ·` / `#channel` / `Broadcast` / `Plan`…，标题前缀决定图标与配色）；长的折成 tldr + `▸ expand`。
12. **屏幕被填满** → 应用**自己滚**（视口边缘 `↑N` / `↓N`，可选滚动条）；`Ctrl+L` 清屏但历史还在。

## 2.2 屏幕面：同一件事，两家放在哪个屏

**先看主屏本身**（它是容器，所有其它屏都是从这里进出的）：两家主屏从上到下的**逐区清单**（omp 26 区 / jcode 16 区）、谁固定谁滚、有没有行数总账、滚动归谁、空屏长什么样、主屏独占哪些键 → [`screens/S0-main.md`](screens/S0-main.md)。**两边最锋利的一条差异**：omp 把滚动交给**终端回看缓冲**（应用不探测滚动位置、主屏无翻页键），jcode 是**应用自管滚动**（alternate screen + `PageUp/PageDown`）。

下面这张表是**其余 12 个屏**：

| | omp | jcode |
|---|---|---|
| 常驻的屏 | **1 个**（主屏） | **1 个**（主屏） |
| 压在主屏上的层 | **约 42 个真面板**（overlays 目录 63 个文件里 21 个是纯 helper / 类型）+ 整屏 app（含 git / debug 子应用）+ 向导 4 | **23**（overlay / 整屏页 14 + 侧栏页 9）+ 远端那一套 |
| 进出的形状 | 居中弹层 / 全屏 app（统一 `hub-frame.ts` 外框）；进去后主屏基本让位 | **两档**：侧栏页（可与正文并存、能分栏）· 全屏页（顶掉正文区，**保留状态行与输入框**） |

| 用户想干的事 | omp（屏） | jcode（屏） |
|---|---|---|
| 挑模型 | `model-picker` / `model-hub` / `model-browser` **三档** + `thinking-selector` | 模型状态 overlay + 内联 picker（`Ctrl+O` 设默认 / `Ctrl+N` 收藏 / `Shift+Tab` 轮收藏） |
| 换会话 | `session-selector` overlay + `apps/session-picker`（整屏）两档 | 会话选择器 overlay（全屏双栏：列表 + 预览） |
| 看结构 / 树 | `tree-selector` —— **塞进输入框那一格** | swarm 全页（`Alt+N` 第三档：整块消息区换成 swarm 页，里面是**嵌套 agent 树** + 选中 agent 的 live 卡）+ 侧栏页 |
| 回到某一点 | `rewind-selector` | `/rewind` 直接回上一条；`/fork` 分叉到新窗口 |
| 看用量 / 配额 | `usage-dashboard`（网格 + 热力图 + 明细表）+ `reset-usage-selector` | `usage overlay` + `UsageLimits` 挂件 |
| 键位 | `?` 的键位表（`hotkeys-markdown`）+ `/help` | `help overlay` + `/keys`（还能报**你的终端吞了哪些键**） |
| 主题 / 外观 | `theme-selector`、`composer-shape-preview` | 走命令（`/colors` / `/theme`），**没有独立的选择器面板** |
| 调试 | `apps/debug/`：log-viewer · raw-sse · protocol-probe · terminal-info | `debug overlay`（`jcode debug`）+ 侧栏 |
| 后台作业 | `jobs-panel` | `BackgroundTasks` 挂件 + pinned 行（只留最近 2 条） |
| 计划 | `plan-review-overlay` / `plan-save-overlay` / `PlanToc` | plan 页（侧栏） |
| 复制 / 选中 | `copy-selector` | copy / selection mode |
| 找历史 | `history-search` | prompt history 搜索 overlay |
| 首次打开 | `setup/wizard-overlay` + `startup-splash`（场景：composer / glyph / model / sign-in / theme） | onboarding welcome（建议卡 + `Press 1-N`） |
| 看进程 / 服务 | `ps-top`（btop 风整屏监视）· `jobs-panel` | `jcode server` 系列（CLI）+ 通知卡 |
| 诊断数据 | `autoresearch-dashboard` · `if-bench-board` · `cleanse-board` | （无独立整屏） |

**三条形状差异**：① **压在主屏上的方式不同** —— omp 几乎都是"居中弹层 / 全屏 app"，jcode 分"侧栏页（可并存）"与"全屏页（顶掉正文但保留状态行与输入）"两档；② **同一件事常有多个档** —— 两家的模型选择、会话选择都是两三种不同的屏（同一个动作、不同的信息量）；③ **键位纪律不同** —— omp 的面板键是**每个面板自己写死**的（面板内部键 **545 条**，逐面板逐键），jcode 的 overlay 走**统一的 `handle_overlay_key`**。

## 2.3 组件面：同一时刻，两家露出什么

| 时刻 | omp | jcode |
|---|---|---|
| 开场 | 身份卡（屏一满**第一个退场**）+ 启动画面 | header + 建议卡（首次引导整屏接管） |
| 打字时 | 输入框（8 种 composer 形态 / 顶边框状态串）+ 统一补全弹窗（`@` 文件 / `^` 模型 / `#` / emoji）+ 附件 chips 带 + pending 区 | 输入框（多行 ≤10 行 / 彩虹编号 / prompt 前缀 `> … $ »`）+ 排队条 + hint 行 + palette 联想 |
| 它在说话 | 流式正文 + 思考块（展开 / 折叠 `Thought for Ns`）+ emoji 反应徽标 | 正文 markdown + `tool:` 行 + ```plan 卡 + reasoning 折叠行 + sticky 上一条预览 |
| 它伸手 | 工具卡**四级降级**（≥3 / 2 / 1 / 0 行，0 行隐藏不取消）+ 输出按类型渲染 + 超长截断 | 工具行（`dimmed 技术细节` 可显隐）+ 结果 ≤4 行预览 + 后台任务卡 |
| 它在动 | 编辑器上方 working loader + 状态条 `subagents` 徽标 + 共享时钟脉冲 | 输入上方**活动行**（七种文案 / tps / 限流 / 网络重试 / 超 10s 变黄） |
| 要我做决定 | approval 模式 + hook-input + plan-review | 内联交互块（inline picker）+ Claude 接管确认模态 |
| 完事的时候 | 一轮用量行 `prompt→yield` + recap / 压缩摘要 / 分支摘要分隔条 + 通知卡 | 通知行（多来源 `·` 拼接，各带 TTL）+ 聊天内联通知卡（`DM from` / `Task ·` / `Broadcast`…） |
| 出问题的时候 | 固定 `errorBanner` 条 + 回合内联错误块（≤8 行 + `ctrl+o` 展开）+ cache 失效分隔条 | 断线卡 / 重试文案 / 限流提示 / File conflict 卡 |
| 我站在哪、花了多少 | **状态条**（27 段位 / 7 preset / 7 分隔符 / 4 种贴法；没数据不画） | **事实行**（8 字段 + **10 级压缩阶梯**，`dir/model/上下文` 永不消失只变短） |
| 会话层面 | todo HUD + Subagents HUD（3 行 + 展开器）+ 协作二维码 | 顶部 pinned todo 带 + swarm strip（`d/t` 计数）+ **15 种 info widget 抢槽位** |
| 系统与视觉 | 扩展挂件区（`setWidget` above/below editor）+ vim 光标 + 终端回看缓冲滚动 | 滚动条（native / 自绘）+ idle donut + 过渡动画 + `^N / vN` 视口边缘 |

**三条共同形状**：① 两家的块都是**条件出现 + 抢空间**，并且都把「**没数据就不画**」写成纪律；② 抢空间的策略不同 —— omp 交给「按可用行数降级 + 段位可配」，jcode 交给「优先级 + 最小高度 + 写死的压缩阶梯」；③ 两家都只有**一个**「该我说话的地方」，看别的东西时手还在输入框上。

## 2.4 命令面：17 类的分布

| | omp | jcode | 说明 |
|---|---|---|---|
| 合计 | **263** | **209** | 含别名折叠后；CLI 子命令也在内（omp 50 / jcode 88） |
| 两家都重的类 | B 60 · D 52 · F 22 · H 17 · I 14 | B 24 · H 23 · I 21 · L 21 · F 19 | 给养 / 工具 / 自主 / 协作 / 账号 —— **这类产品的公共必修** |
| 只有 omp 重的类 | **D3 MCP 18** · J 19（插件市场 17）· H2 分享 10 · C3 队列 · D1 工具开关 7 | — | omp 的重心在**扩展生态** |
| 只有 jcode 重的类 | — | **K 19（遥测 5 / 调试）** · L2 自构建 5 · G 13（界面开关）· E 9（评审测试） | jcode 的重心在**自维护与诊断** |
| 两家都薄的类 | E 5 · G 1 · P 3 | J 1 · P 0 | omp 几乎没有"界面开关"命令（都进设置项）；jcode 几乎没有插件生态 |

**两家都没有落进的叶**：`G5 动画 · 滚动 · 视觉特效`（都只散在键位与设置里）、`J3 用户自建命令`（omp 有机制但不在命令表里，jcode 无）。

## 2.5 数字总表（两家）

| 面 | omp | jcode |
|---|---|---|
| 命令 | 84 内置 + 129 子命令 + 16 参数补全 + 6 类运行时来源 + CLI 50 | 133（含 16 条隐藏）+ 14 条未登记 + CLI 88 |
| 屏幕 | 主屏 1 屏（26 个区）+ **约 42 个真面板**（overlays 目录 63 个文件里 21 个是纯 helper / 类型，不是屏）+ 整屏 app（25 个文件，含 git / debug 子应用，其中 8 个是纯内部）+ 向导 4 | 主屏 1 屏（16 个区）+ 23 个（overlay / 全屏页 14 + 侧栏页 9）+ 远端一套 |
| 面板内部的键 | **545**（逐面板逐键） | —（统一 `handle_overlay_key`，见各类键位表） |
| 组件（用户在什么时候看到什么） | **326**（12 个时刻） | **209** |
| 挂件 / 带 | 27 段位 + 7 preset + 7 分隔符 + 4 贴法；挂件 22 + 一套扩展点 | 事实行 8 字段 + 10 级阶梯；15 个 info widget |
| 设置 | **529** 项（35 个域） | **478**（config.toml 键 280 + env 覆盖 171 + `/config` 4） |
| 模式与开关 | 42（approval 3 / magic keyword 4 / 其余 35） | 19 |
| 特殊输入 | 12 种前缀 | 语音 / 听写 / 图片占位 |
| 鼠标与视觉 | 20 + 10 | 15 + 10 |
| CLI | 313（子命令 50 + 自有 flag 261 + 全局 2） | 322（子命令 35 + 嵌套 53 + 全局 26 + 自有 flag 186 + 位置参数 22） |
| TUI 源码逐文件（判用户可见性） | 181 个文件 | —（散在上述各节） |
| 会话与历史 | `/resume` `/tree` `/handoff` `/fork` `/export` … | `/resume` `/catchup` `/rewind` `/fork` `/transfer` … |

**这张表说明什么**：两家的功能面都在**同一个数量级**，而且大头在**命令面与组件面**上 —— 它们都把"敲一个命令"和"此刻这一块"当成第一类交互面。这不是要抄；是要求**每做一块，先到这里查两家有没有先例、它什么时候出现、代价是什么**。

---

# 三、功能模块优先级（**唯一的决策**）

## 3.1 判据

两条，缺一不可：

1. **立身之本**：没有它，这个产品就不是它了（不是"少个功能"，而是设计塌一角）。
2. **碰它的频次 × 有没有替代路径**：一天里用几次；以及有没有别的路走到同一个结果。

> 优先级只决定「**先做哪个 / 要不要做**」，不决定「做成什么样」—— 后者是第二步逐块对比、决策的事。
> 优先级对**功能模块**排，不是对命令排：命令是**先例**。

## 3.2 屏幕面

| 模块 | 优先级 | 为什么 |
|---|---|---|
| **S0 主屏** | **P0（第一个）** | 人 95% 的时间待在这一屏；**它的空间结构（哪几个区、谁固定谁滚、谁吃剩下的行）是所有其它模块的容器** —— 这一屏不先定下来，别的模块没有地方可放。26 / 16 个区的对照见 [`screens/S0-main.md`](screens/S0-main.md) |
| **S1 会话与历史** | **P0** | 换线 / 分叉 / 命名就是树的日常动作；没有它，树只是看得见摸不着 |
| **S2 模型与给养** | **P0** | 选模型与角色是立身的两条 |
| **S7 界面与外观** | P1 | 键位表与显示开关是操作面本身；主题后置 |
| **S12 首启与帮助** | P1 | 每个新用户的第一屏（空态 / 建议卡 / 帮助表） |
| **S3 这一轮** | P1 | 打断在键位里已有；计划模式待商 |
| **S4 工具与权限** | P1 | "跑之前要不要问人"每天碰；MCP / 远端不是立身 |
| **S5 仓库** | P2 | 模型自己带着 git 的手；一句话就能代替敲命令 |
| **S11 诊断与调试** | P2 | 出问题要能看 |
| **S6 多 agent 与自主** | **P3 —— 且需要明确反对** | 旧设计的判决书：让模型自己拆完跑完 → 2443 节点 / 86% 从未完工 |
| **S8 协作与多端** | P3 | 设计里只有"一个人、一棵树" |
| **S9 账号与计费** | P3 | 没有账号体系（用量除外，见 M10） |
| **S10 扩展与生态** | P3 | 插件市场是另一回事 |

## 3.3 组件面

| 模块 | 优先级 | 为什么 |
|---|---|---|
| **M4 它在说话** | **P0** | 正文流是一屏的主体 |
| **M5 它伸手** | **P0** | 作业卡片在流尾——§9 的可见面 |
| **M6 它在动** | **P0** | "它还在干活吗"是用户最常问的 |
| **M9 出问题的时候** | **P0** | 接口失败与重试是设计里已经写死的（§9.8） |
| **M10 我站在哪、花了多少** | **P0** | "我在哪 / 烧了多少"的唯一出口 |
| **M2 打字的时候** | P1 | 一屏唯一入口；补全 / 提及 / 前缀未定 |
| **M3 排队与待发** | P1 | 插话与排队每天碰，两家做法不同 |
| **M1 开场与空闲** | P1 | 空态与建议卡是新用户第一印象 |
| **M7 要我做决定** | P1 | 审批要不要做待定 |
| **M8 完事的时候** | P1 | 通知与交代的形态 |
| **M11 会话层面的东西** | P2 | 待办 / 名册有用但不是立身 |
| **M12 系统与视觉** | P3 | 动画 / 滚动条后置；鼠标 P2 |

## 3.4 命令面

| 类 | 优先级 | 内部叶 | 为什么 |
|---|---|---|---|
| **A 会话** | **P0** | A1 P0 · A3 P0 · A4 P1 · A2 P2 · A5 P2 | 开线 / 换线 / 分叉是树的日常动作 |
| **B 模型与给养** | **P0** | B1 P0 · B2 P0 · B3 P1 · B4 P3 · B5 P3 | 选模型与角色是立身；压缩是"上下文满了"的必答；记忆 / 技能可后 |
| **C 对话进行时** | **P0** | C1 P0 · C2 P0 · C3 P1 · C4 P2 | 打断与重试已在设计里；插话排队每天碰 |
| **D 工具与权限** | **P0** | D1 P0 · D2 P1 · D3 P3 · D4 P3 · D5 P2 | "角色 = 注意力 + 手"；审批得答；MCP / 远端不是立身 |
| **G 界面与外观** | P1 | G3 P0 · G2 P0 · G4 P1 · G1 P3 · G5 P3 | 键位就是操作面（与 S7 同一条） |
| **L 系统与自维护** | P1 | L3 P1 · L1 P2 · L2 P3 | 首启 / 更新 |
| **N 特殊输入前缀** | P2 | — | `!` / `@` 便宜但绕开"一句话就是这一轮" |
| **E 代码与仓库** | P2 | E1 P2 · E2 P2 · E3 P2 · E4 P3 | 模型自己带 git 的手 |
| **J 扩展与集成** | P2 | J3 P2 · J1 P3 · J2 P3 | "角色是数据"是同源的路；插件市场是另一回事 |
| **K 诊断与调试** | P2 | K1 P2 · K5 P2 · K2 P3 · K3 P3 · K4 P3 | 日志与自检 |
| **M 帮助与元** | P2 | M1 P2 · M2 P2 · M3 P3 · M4 P3 | 帮助表是键位的可见面 |
| **O 进程与服务** | P3 | O2 P2 · O1 P3 | 本地单人；只有"后台作业可见面"与 §9 相关 |
| **I 账号与计费** | P3 | I2 P1 · I1 P3 · I3 P3 | 没有账号体系；用量已显示在 M10 |
| **F 自主与自动化** | **P3 —— 且需要明确反对** | F1 P3 · F2 P3 · F3 P3 · F4 P3 | 判决书：2443 节点 / 86% 从未完工；"人不在场，树就在休息" |
| **H 协作与分享** | P3 | H1 P3 · H2 P3 · H3 P3 | 设计里只有一个人 |
| **P 基准与实验** | P3 | — | 开发者自用 |
| **Q 其它内部工具** | P3 | Q（配置读写叶待定） | 兜底 |

## 3.5 下一步顺序（把上面拉成一条线）

1. **P0 —— 不做就不是这个产品**：先进**屏幕 `S0 主屏`**（所有东西的容器：哪几个区、谁固定谁滚）；它定下来之后，往里装 组件 `M4 它在说话`、`M5 它伸手`、`M6 它在动`、`M9 出问题的时候`、`M10 我站在哪、花了多少`，以及从它上面出去的 屏幕 `S1 会话与历史`、`S2 模型与给养`；命令面同批：`A 会话`、`B 模型与给养`、`C 对话进行时`、`D 工具与权限`（D1）、`G 键位`。
2. **P1 —— 补上就完整**：屏幕 `S3`/`S4`/`S7`/`S12`；组件 `M1`/`M2`/`M3`/`M7`/`M8`；命令 `B3 压缩`、`C3 排队插话`、`D2 审批`、`G4 显示开关`、`I2 用量`、`L3 首启`。
3. **P2 —— 有用但不是立身**：屏幕 `S5`/`S11`；组件 `M11`；命令 `A2`/`A4`/`A5`、`C4`、`D5`、`E`、`J3`、`K1/K5`、`M`、`N`、`O2`。
4. **P3 —— 后置或需要明确反对**：屏幕 `S6`（**反对**）/`S8`/`S9`/`S10`；组件 `M12`；命令 `F`（**反对**）、`H`、`I`、`J1/J2`、`K2/K3/K4`、`L2`、`P`、`Q`、`G1 主题`、`G5 动画`。

**我们已经定到哪儿**：**骨架**（八屏 + 进屏三条路 · 壳 + 内容区 + 侧边 · 内容区三档 · 侧边三态与页面 · 切换 · 产品级不做）→ [`ours/P0.md`](ours/P0.md)；每一屏**内部**的细节还没有第二份，按上面 §3.5 的顺序往下走。
