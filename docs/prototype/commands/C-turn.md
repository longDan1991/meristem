# 命令 · C 对话进行时（控制当前这一轮）

> **这一块是什么**：控制**此刻这一轮**：打断、取消、重试、把话排到后面、让它先规划再动手。
> **用户什么时候来**：用户看着它跑，想改这一轮的走向。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §C 的分册，**同一条不多不少**（这一块 omp 18 条 · jcode 5 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| C1 | 打断 · 取消 · 暂停 · 继续 | 1 | 2 | 3 |
| C2 | 重试 · 修复 · 催促 | 1 | 2 | 3 |
| C3 | 排队 · 后台 · 插入 | 2 | 0 | 2 |
| C4 | 计划模式（先规划再动手） | 14 | 1 | 15 |
| **合计** | | **18** | **5** | **23** |

## 两家的命令（先例原样）

### C1 打断 · 取消 · 暂停 · 继续

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/pause` | 冻结所有 agent 直到恢复 | `packages/coding-agent/src/slash-commands/builtin-control.ts:77` |
| jcode | TUI | `/cancel`（别名 `/stop`） | 取消当前 prompt/操作 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:130` |
| jcode | TUI | `/continue`（别名 `/resumeall` `/resume-all`） | 继续每个本会自动恢复的中断会话（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:229` |

### C2 重试 · 修复 · 催促

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/retry` | 重试上次失败的 agent 轮次 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:499` |
| jcode | TUI | `/poke` | 催促模型续跑未完成 todo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:135` |
| jcode | TUI | `/fix` | 模型无法继续时恢复 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:140` |

### C3 排队 · 后台 · 插入

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/queue` | 排队一条消息到 agent yield 后发送 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:438` |
| omp | TUI | `/btw` | 提问侧问题或浏览 BTW 历史 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:451` |

### C4 计划模式（先规划再动手）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/plan` | 切换 plan 模式（先规划后执行） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:323` |
| omp | TUI | `/plan-review` | 重新打开最新计划的评审 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:344` |
| omp | TUI | `/todo` | 查看或修改 agent 的 todo 列表 | `packages/coding-agent/src/slash-commands/builtin-session.ts:208` |
| omp | TUI | `/todo edit` | 在 $EDITOR 打开 todos（Markdown 往返） | `packages/coding-agent/src/slash-commands/builtin-session.ts:214` |
| omp | TUI | `/todo copy` | 把 todos 以 Markdown 复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:215` |
| omp | TUI | `/todo expand` | 在 HUD 显示全部阶段与任务 | `packages/coding-agent/src/slash-commands/builtin-session.ts:216` |
| omp | TUI | `/todo collapse` | 恢复 HUD 的有界预览 | `packages/coding-agent/src/slash-commands/builtin-session.ts:217` |
| omp | TUI | `/todo export` | 把 todos 写为 Markdown 文件 | `packages/coding-agent/src/slash-commands/builtin-session.ts:218` |
| omp | TUI | `/todo import` | 从 Markdown 文件替换 todos | `packages/coding-agent/src/slash-commands/builtin-session.ts:219` |
| omp | TUI | `/todo append` | 追加一条任务（阶段模糊匹配/自动建） | `packages/coding-agent/src/slash-commands/builtin-session.ts:221（4-tab 多行项）` |
| omp | TUI | `/todo start` | 把任务标记为 in_progress | `packages/coding-agent/src/slash-commands/builtin-session.ts:225` |
| omp | TUI | `/todo done` | 把任务/阶段/全部标记完成 | `packages/coding-agent/src/slash-commands/builtin-session.ts:226` |
| omp | TUI | `/todo drop` | 把任务/阶段/全部标记放弃 | `packages/coding-agent/src/slash-commands/builtin-session.ts:227` |
| omp | TUI | `/todo rm` | 移除任务/阶段/全部 | `packages/coding-agent/src/slash-commands/builtin-session.ts:228` |
| jcode | TUI | `/plan` | 生成仅计划的 plan 卡 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:136` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 1 条**（该条不完全贴叶，正文对应行末尾已标）：`/btw`（omp，C3）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
