# 命令 · O 进程与服务（CLI 为主）

> **这一块是什么**：让某样东西在后台一直活着：服务端与桥接、后台与持久进程的查看与清理。
> **用户什么时候来**：用户要的是「一个进程」，不是「一轮对话」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §O 的分册，**同一条不多不少**（这一块 omp 4 条 · jcode 11 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| O1 | 服务端 · 连接 · 桥接 | 1 | 10 | 11 |
| O2 | 后台/持久进程的查看与清理 | 3 | 1 | 4 |
| **合计** | | **4** | **11** | **15** |

## 两家的命令（先例原样）

### O1 服务端 · 连接 · 桥接

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp auth-gateway` | 运行基于 broker 的转发代理 | `packages/coding-agent/src/cli-commands.ts:46` |
| jcode | CLI | `jcode serve` | 启动 agent 后台守护进程（可选 --server-name） | `src/cli/args.rs:148` |
| jcode | CLI | `jcode server <action>` | 管理后台守护进程 | `src/cli/args.rs:174` |
| jcode | CLI | `jcode connect` | 连接已在运行的 server | `src/cli/args.rs:181` |
| jcode | CLI | `jcode run <message>` | 发一条消息后退出（--json/--ndjson） | `src/cli/args.rs:184` |
| jcode | CLI | `jcode api-bridge`（别名 `api`） | 在 Unix socket 上提供 SDK 稳定 API | `src/cli/args.rs:581` |
| jcode | CLI | `jcode server stdio` | 内部：ssh attach 的原生客户端协议桥（隐藏） | `src/cli/args.rs:638` |
| jcode | CLI | `jcode server start` | 若未运行则启动后台 server（--json） | `src/cli/args.rs:641` |
| jcode | CLI | `jcode server keepalive` | 内部：保持轻量连接到 stdin 关闭（隐藏） | `src/cli/args.rs:649` |
| jcode | CLI | `jcode server promote [version]` | 把共享 server 通道钉到某个已安装版本（--json） | `src/cli/args.rs:652` |
| jcode | CLI | `jcode server reload` | 优雅地把运行中的 server 重载到最新二进制 | `src/cli/args.rs:665` |

### O2 后台/持久进程的查看与清理

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/jobs` | 显示异步后台任务状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:324` |
| omp | TUI | `/jobs full` | 显示完整未截断的命令行 | `packages/coding-agent/src/slash-commands/builtin-session.ts:329` |
| omp | CLI | `omp ps` | 列管守护进程后台进程 | `packages/coding-agent/src/cli-commands.ts:180` |
| jcode | CLI | `jcode server stop` | 停止后台 server 并清理 socket（--force/--json） | `src/cli/args.rs:681` |

## 口径与存疑（事实，不是决策）

- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
