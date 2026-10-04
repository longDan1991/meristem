# 命令 · A 会话（这条线/这段对话本身）

> **这一块是什么**：「这一条线 / 这段对话」本身：开一条、换一条、给它起名与收藏、从某段上下文分叉、交接与回退、清掉旧内容、看它的记录与用量。
> **用户什么时候来**：用户想改变「我站在哪条线上」，或者想收拾这条线的记录。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §A 的分册，**同一条不多不少**（这一块 omp 19 条 · jcode 20 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| A1 | 开一条新的 · 换一条 · 回上一条 | 3 | 5 | 8 |
| A2 | 命名 · 收藏 · 标记 · 归档 | 2 | 4 | 6 |
| A3 | 分叉 · 交接 · 回退（fork / handoff / rewind / transfer） | 3 | 3 | 6 |
| A4 | 清屏 · 清上下文 · 删除 · 导出 | 9 | 2 | 11 |
| A5 | 这条线的信息（token / 状态 / 记录文件） | 2 | 6 | 8 |
| **合计** | | **19** | **20** | **39** |

## 两家的命令（先例原样）

### A1 开一条新的 · 换一条 · 回上一条

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/new` | 开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:176` |
| omp | TUI | `/resume` | 恢复另一个会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:389` |
| omp | TUI | `/tree` | 浏览会话树（切换分支） [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:611` |
| jcode | TUI | `/resume`（别名 `/sessions` `/session`） | 打开会话选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:198` |
| jcode | TUI | `/active` | 管理活动会话（working/ready） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:201` |
| jcode | TUI | `/catchup` | 打开 Catch Up 选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:202` |
| jcode | TUI | `/back` | 回到上一个 Catch Up 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:203` |
| jcode | CLI | `jcode session <action>` | 会话管理命令 | `src/cli/args.rs:337` |

### A2 命名 · 收藏 · 标记 · 归档

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/pin` | 在恢复列表顶部固定/取消固定会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:420` |
| omp | TUI | `/rename` | 重命名当前会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:632` |
| jcode | TUI | `/save` | 收藏会话便于访问 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:204` |
| jcode | TUI | `/unsave` | 移除会话收藏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:205` |
| jcode | TUI | `/rename` | 重命名当前会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:206` |
| jcode | CLI | `jcode session rename <session> [name]` | 重命名已保存会话（--clear/--json） | `src/cli/args.rs:1044` |

### A3 分叉 · 交接 · 回退（fork / handoff / rewind / transfer）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/branch`（别名 `rewind`） | 回退到旧消息并保留旧路径为分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:592` |
| omp | TUI | `/fork` | 从旧消息创建新分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:602` |
| omp | TUI | `/handoff` | 总结为交接文档并原地压缩 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:322` |
| jcode | TUI | `/rewind` | 回退到上一条消息 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:134` |
| jcode | TUI | `/fork`（别名 `/split`） | 把会话分叉到新窗口（可选 prompt） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:207` |
| jcode | TUI | `/transfer` | 把上下文压缩进新的交接会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:209` |

### A4 清屏 · 清上下文 · 删除 · 导出

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/clear` | 原地清空会话上下文，保留会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:207` |
| omp | TUI | `/delete` | 删除当前会话并开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:218` |
| omp | TUI | `/shake` | 丢弃上下文中重内容（工具结果等） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:293` |
| omp | TUI | `/export` | 导出会话为 HTML 文件 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:179` |
| omp | TUI | `/copy` | 选取会话中的文本或代码复制 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:545` |
| omp | TUI | `/session delete` | 删除当前会话并回到选择器 | `packages/coding-agent/src/slash-commands/builtin-session.ts:253` |
| omp | TUI | `/shake elide` | 剥离工具结果与大块（默认） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:298` |
| omp | TUI | `/shake images` | 剥离图片块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:299` |
| omp | TUI | `/shake thinking` | 丢弃所有 thinking 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:300` |
| jcode | TUI | `/clear` | 清空会话历史 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:131` |
| jcode | TUI | `/cls`（别名 `/clear-view`） | 仅清屏，保留上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:132` |

### A5 这条线的信息（token / 状态 / 记录文件）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/session` | 会话管理命令 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:246` |
| omp | TUI | `/session info` | 显示当前会话信息与统计 | `packages/coding-agent/src/slash-commands/builtin-session.ts:252` |
| jcode | TUI | `/observe` | 侧栏显示最新工具上下文 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:57` |
| jcode | TUI | `/todos`（别名 `/todo`） | 在聊天以卡片显示会话 todo 列表 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:58` |
| jcode | TUI | `/transcript` | 打开当前会话 transcript 文件 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:102` |
| jcode | TUI | `/context` | 显示完整会话上下文快照 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:153` |
| jcode | TUI | `/info` | 显示会话信息与 token | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:160` |
| jcode | CLI | `jcode transcript [text]` | 把外部转录文本注入活动 TUI（--mode/--session） [归类存疑] | `src/cli/args.rs:366` |

## 口径与存疑（事实，不是决策）

- **跨接口的同义命令按两条算**：`omp /join` 与 `omp join`、`jcode /remote` 与 `jcode remote` 是两个入口，不折叠。
- **`[归类存疑]` 5 条**（该条不完全贴叶，正文对应行末尾已标）：`/tree`（omp，A1）、`/copy`（omp，A4）、`/session`（omp，A5）、`/observe`（jcode，A5）、``jcode transcript [text]``（jcode，A5）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
