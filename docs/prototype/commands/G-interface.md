# 命令 · G 界面与外观

> **这一块是什么**：它看起来怎样、我按什么键：主题与符号、状态条与布局、键位与终端设置、各类显示开关、动画。
> **用户什么时候来**：用户想调「房子的装修与开关」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §G 的分册，**同一条不多不少**（这一块 omp 1 条 · jcode 13 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| G1 | 主题 · 颜色 · 符号 · 对齐 | 1 | 3 | 4 |
| G2 | 状态条 · 事实行 · 布局 | 0 | 3 | 3 |
| G3 | 键位 · 终端设置 · 按键冲突 | 0 | 2 | 2 |
| G4 | 显示开关（思考 / 工具详情 / 通知 / diff / 图片 / 滚动条） | 0 | 5 | 5 |
| **合计** | | **1** | **13** | **14** |

## 两家的命令（先例原样）

### G1 主题 · 颜色 · 符号 · 对齐

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/settings` | 打开设置菜单 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:296` |
| jcode | TUI | `/colors`（别名 `/color`） | 列出/配置/评分所有 TUI 颜色 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:65` |
| jcode | TUI | `/alignment` | 显示/修改默认文本对齐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:111` |
| jcode | TUI | `/theme` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:45` |

### G2 状态条 · 事实行 · 布局

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/splitview`（别名 `/split-view`） | 侧栏镜像当前聊天 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:60` |
| jcode | TUI | `/btw` | 在侧栏问一个旁路问题 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:62` |
| jcode | CLI | `jcode menubar`（别名 `menu-bar` `statusbar`） | macOS 菜单栏实时指示器（--once/--json） | `src/cli/args.rs:563` |

### G3 键位 · 终端设置 · 按键冲突

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/terminal-setup` | 修复 Shift+Enter 换行 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:68` |
| jcode | CLI | `jcode setup-hotkey` | 配置平台全局热键启动 jcode（隐藏参数/--uninstall） | `src/cli/args.rs:384` |

### G4 显示开关（思考 / 工具详情 / 通知 / diff / 图片 / 滚动条）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/compact-notifications` | 单行 swarm/文件活动通知显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:112` |
| jcode | TUI | `/show-agentgrep-output` | 聊天内全文 agentgrep 输出显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:116` |
| jcode | TUI | `/tool-call-details` | 工具行 dimmed 技术细节显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:120` |
| jcode | TUI | `/thinking-display`（别名 `/thinking` `/reasoning`） | 模型思维文本显隐（off/full/current） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:124` |
| jcode | TUI | `/diff` | 循环/设置 diff 显示模式（off/inline/full/file） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:180` |

## 口径与存疑（事实，不是决策）

- **一个口径待定**：omp 的 `/settings` 现在归在 G1，jcode 的 `/config` 归在 Q —— 要不要给「配置读写」单独立一个叶，待定（这一轮不做决策）。
- **`[归类存疑]` 2 条**（该条不完全贴叶，正文对应行末尾已标）：`/settings`（omp，G1）、`/btw`（jcode，G2）
- **`[未核实]` 1 条**（源里读不出确切语义，原样保留）：`/theme`（jcode，G1）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
