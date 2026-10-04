# 命令 · E 代码与仓库

> **这一块是什么**：在仓库上做成一件事：分支与 worktree、提交与推送、评审与测试、issue 分诊。
> **用户什么时候来**：用户想把「这条线上的活」落到仓库里。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §E 的分册，**同一条不多不少**（这一块 omp 5 条 · jcode 9 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| E1 | git · 分支 · worktree | 4 | 1 | 5 |
| E2 | 提交 · 推送 · 合入 | 1 | 3 | 4 |
| E3 | 评审 · 测试 · 重构 · 改进 | 0 | 4 | 4 |
| E4 | issue · 分诊 | 0 | 1 | 1 |
| **合计** | | **5** | **9** | **14** |

## 两家的命令（先例原样）

### E1 git · 分支 · worktree

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/git` | 打开 git UI（diff/暂存/提交） | `packages/coding-agent/src/slash-commands/builtin-session.ts:572` |
| omp | TUI | `/wt`（别名 `worktree`） | 把会话移入新 worktree（含改动） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:740` |
| omp | CLI | `omp git` | 全屏 git UI | `packages/coding-agent/src/cli-commands.ts:128` |
| omp | CLI | `omp worktree`（别名 `wt`） | 增/列/清 git worktree | `packages/coding-agent/src/cli-commands.ts:276` |
| jcode | TUI | `/git` | 显示会话工作目录的 git 状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:64` |

### E2 提交 · 推送 · 合入

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp commit` | 生成提交信息并更新 changelog | `packages/coding-agent/src/cli-commands.ts:78` |
| jcode | TUI | `/commit` | 从当前改动生成逻辑提交 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:69` |
| jcode | TUI | `/merge` | 合入 main/master 并切过去（不推送） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:70` |
| jcode | TUI | `/commit-push`（别名 `/commit-and-push`） | 逻辑提交后推送 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:74` |

### E3 评审 · 测试 · 重构 · 改进

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/review` | 启动一次性 review 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:106` |
| jcode | TUI | `/judge` | 启动一次性 judge 会话 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:107` |
| jcode | TUI | `/refactor` | 运行安全重构循环 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:138` |
| jcode | TUI | `/test` | 用分层测试验证论断/当前改动 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:145` |

### E4 issue · 分诊

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/triage` | 分诊新 GitHub issue 并自主修复安全的 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:98` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 1 条**（该条不完全贴叶，正文对应行末尾已标）：`/judge`（jcode，E3）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
