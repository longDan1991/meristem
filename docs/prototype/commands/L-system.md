# 命令 · L 系统与自维护

> **这一块是什么**：把这个程序本身弄成我要的样子：更新与重启、自构建与发布、初始化与首次接上终端。
> **用户什么时候来**：用户跟「程序本身」打交道，而不是跟自己的活。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §L 的分册，**同一条不多不少**（这一块 omp 8 条 · jcode 21 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| L1 | 更新 · 重启 · 重载 | 5 | 13 | 18 |
| L2 | 自构建 · 发布 · 安装 | 0 | 5 | 5 |
| L3 | 初始化 · 首启 · 终端接入 | 3 | 3 | 6 |
| **合计** | | **8** | **21** | **29** |

## 两家的命令（先例原样）

### L1 更新 · 重启 · 重载

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/restart` | 用相同启动参数重启并恢复会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:850` |
| omp | TUI | `/reload-plugins` | 重载所有插件（技能/命令/钩子等） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:557` |
| omp | TUI | `/exit` | 退出应用 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:845` |
| omp | TUI | `/quit`（别名 `q`） | 退出应用 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-control.ts:86` |
| omp | CLI | `omp update` | 检查并安装更新 | `packages/coding-agent/src/cli-commands.ts:246` |
| jcode | TUI | `/reload` | 重载到最新可用二进制 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:192` |
| jcode | TUI | `/restart` | 用当前二进制重启 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:193` |
| jcode | TUI | `/update` | 后台更新并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:196` |
| jcode | TUI | `/update-sim` | 安全预览更新 UI（Alt+_） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:197` |
| jcode | TUI | `/client-reload` | 强制重载客户端二进制（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:227` |
| jcode | TUI | `/server-reload` | 强制重载服务端二进制（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:228` |
| jcode | TUI | `/quit` | 退出 jcode [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:216` |
| jcode | CLI | `jcode update` | 升级 jcode 到最新版 | `src/cli/args.rs:275` |
| jcode | CLI | `jcode restart <action>` | 跨重启保存/恢复打开的 jcode 窗口 | `src/cli/args.rs:557` |
| jcode | CLI | `jcode restart save` | 保存当前打开 jcode 窗口的重启快照 | `src/cli/args.rs:1015` |
| jcode | CLI | `jcode restart restore` | 恢复最近保存的重启快照 | `src/cli/args.rs:1021` |
| jcode | CLI | `jcode restart status` | 显示当前保存的重启快照 | `src/cli/args.rs:1023` |
| jcode | CLI | `jcode restart clear` | 删除当前重启快照 | `src/cli/args.rs:1025` |

### L2 自构建 · 发布 · 安装

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/fast-release`（别名 `/cut-release` `/commit-push-release`） | 从 selfdev 缓存立即发布 Linux | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:79` |
| jcode | TUI | `/fast-macos-release` | 立即发布已备好的 macOS arm64 构建 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:83` |
| jcode | TUI | `/merge-remote-release` | 合入/验证/推送并远程发布 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:88` |
| jcode | TUI | `/remote-release` | 立即推送发布 tag，CI 全平台构建发布 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:92` |
| jcode | TUI | `/rebuild` | 后台重建并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:194` |

### L3 初始化 · 首启 · 终端接入

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp launch` | 默认入口：交互/打印模式运行 assistant [归类存疑] | `packages/coding-agent/src/cli-commands.ts:29` |
| omp | CLI | `omp setup` | 引导设置或安装可选依赖 | `packages/coding-agent/src/cli-commands.ts:205` |
| omp | CLI | `omp completions` | 打印 shell 补全脚本 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:83` |
| jcode | TUI | `/onboarding-preview` | 预览首启引导屏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:184` |
| jcode | TUI | `/onboarding-sim` | 走遍每个首启屏（Alt+5 重置/Cmd+5 切换） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:188` |
| jcode | CLI | `jcode setup-launcher` | 安装平台启动器集成 [归类存疑] | `src/cli/args.rs:404` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 7 条**（该条不完全贴叶，正文对应行末尾已标）：`/exit`（omp，L1）、`/quit`（omp，L1）、`/quit`（jcode，L1）、`/merge-remote-release`（jcode，L2）、``omp launch``（omp，L3）、``omp completions``（omp，L3）、``jcode setup-launcher``（jcode，L3）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
