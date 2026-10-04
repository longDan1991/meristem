# 命令 · M 帮助与元

> **这一块是什么**：想起来某个东西叫什么：帮助与命令表、版本与变更、反馈、隐藏命令。
> **用户什么时候来**：用户卡在「我记得有这么个东西」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §M 的分册，**同一条不多不少**（这一块 omp 6 条 · jcode 9 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| M1 | 帮助 · 命令表 · 键位表 | 1 | 2 | 3 |
| M2 | 版本 · 变更日志 | 3 | 3 | 6 |
| M3 | 反馈 · 支持 | 1 | 2 | 3 |
| M4 | 隐藏 / 彩蛋命令 | 1 | 2 | 3 |
| **合计** | | **6** | **9** | **15** |

## 两家的命令（先例原样）

### M1 帮助 · 命令表 · 键位表

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/hotkeys` | 显示所有键盘快捷键 | `packages/coding-agent/src/slash-commands/builtin-session.ts:496` |
| jcode | TUI | `/help`（别名 `/?` `/commands`） | 显示帮助与键盘快捷键 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:40` |
| jcode | TUI | `/hotkeys` | 列出热键及个人使用统计 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:67` |

### M2 版本 · 变更日志

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/changelog` | 显示变更日志条目 | `packages/coding-agent/src/slash-commands/builtin-session.ts:467` |
| omp | TUI | `/changelog full` | 显示完整 changelog | `packages/coding-agent/src/slash-commands/builtin-session.ts:473` |
| omp | TUI | `/changelog last` | 显示最近 N 个 release（默认 1） | `packages/coding-agent/src/slash-commands/builtin-session.ts:474` |
| jcode | TUI | `/version` | 显示当前版本 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:158` |
| jcode | TUI | `/changelog` | 显示本构建的近期变更 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:159` |
| jcode | CLI | `jcode version` | 显示版本/构建信息（--json） | `src/cli/args.rs:278` |

### M3 反馈 · 支持

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp grievances` | 查看/清理/上报工具问题 | `packages/coding-agent/src/cli-commands.ts:133` |
| jcode | TUI | `/feedback` | 发送关于 jcode 的反馈 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:168` |
| jcode | TUI | `/support` | 预填诊断信息发邮件给支持 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:170` |

### M4 隐藏 / 彩蛋命令

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp __complete（隐藏）` | 内部补全辅助 | `packages/coding-agent/src/cli-commands.ts:88` |
| jcode | TUI | `/z`（别名 `/zz` `/zzz`） | 秘密 premium 模式命令（hidden） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:235` |
| jcode | TUI | `/zstatus` | 秘密 premium 模式状态命令（hidden） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:238` |

## 口径与存疑（事实，不是决策）

- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
