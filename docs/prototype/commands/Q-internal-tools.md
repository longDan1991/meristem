# 命令 · Q 其它内部工具（CLI 为主，兜底）

> **这一块是什么**：兜底：两家里那些不属于上面任何一块的内部工具（配置读写、GC、分词计数、REPL …）。
> **用户什么时候来**：用户要动「零件」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §Q 的分册，**同一条不多不少**（这一块 omp 5 条 · jcode 2 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| Q | 其它内部工具（CLI 为主，兜底） | 5 | 2 | 7 |
| **合计** | | **5** | **2** | **7** |

## 两家的命令（先例原样）

### Q 其它内部工具（CLI 为主，兜底）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp config` | 管理配置项 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:98` |
| omp | CLI | `omp gc` | 存储垃圾回收 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:113` |
| omp | CLI | `omp shell` | 交互式 shell 控制台 | `packages/coding-agent/src/cli-commands.ts:210` |
| omp | CLI | `omp read` | 预览 read 工具结果 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:215` |
| omp | CLI | `omp toks` | 用各离线分词器计数 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:266` |
| jcode | TUI | `/config` | 显示或编辑配置 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:173` |
| jcode | CLI | `jcode repl` | 无 TUI 的简单 REPL 模式 [归类存疑] | `src/cli/args.rs:272` |

## 口径与存疑（事实，不是决策）

- **兜底叶**：`omp config` 与 jcode 的 `/config` 都是「配置读写」——与 G 的待定口径同一条。
- **`[归类存疑]` 6 条**（该条不完全贴叶，正文对应行末尾已标）：``omp config``（omp，Q）、``omp gc``（omp，Q）、``omp read``（omp，Q）、``omp toks``（omp，Q）、`/config`（jcode，Q）、``jcode repl``（jcode，Q）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
