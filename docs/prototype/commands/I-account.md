# 命令 · I 账号与计费

> **这一块是什么**：让服务认识我是谁、还剩多少：登录与多账号、用量与配额、订阅。
> **用户什么时候来**：用户撞到身份与额度。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §I 的分册，**同一条不多不少**（这一块 omp 14 条 · jcode 21 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| I1 | 登录 · 登出 · 多账号 | 9 | 13 | 22 |
| I2 | 用量 · 配额 · 重置 | 5 | 6 | 11 |
| I3 | 订阅 · 计费 | 0 | 2 | 2 |
| **合计** | | **14** | **21** | **35** |

## 两家的命令（先例原样）

### I1 登录 · 登出 · 多账号

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/login` | 用 OAuth provider 登录 | `packages/coding-agent/src/slash-commands/builtin-session.ts:620` |
| omp | TUI | `/logout` | 登出 OAuth provider | `packages/coding-agent/src/slash-commands/builtin-session.ts:673` |
| omp | TUI | `/setup`（别名 `providers`） | 打开 provider 设置向导 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:305` |
| omp | TUI | `/setup providers` | 配置登录与联网搜索 provider | `packages/coding-agent/src/slash-commands/builtin-modes.ts:310` |
| omp | TUI | `/session pin` | 把当前 provider 固定到某个 OAuth 账号 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:255（4-tab 多行项）` |
| omp | CLI | `omp login` | 登录模型 provider（`/login` 终端版） | `packages/coding-agent/src/cli-commands.ts:159` |
| omp | CLI | `omp token` | 取某 provider 的 API key/OAuth token | `packages/coding-agent/src/cli-commands.ts:261` |
| omp | CLI | `omp auth-broker` | 管理凭据 vault auth-broker | `packages/coding-agent/src/cli-commands.ts:41` |
| omp | CLI | `omp dry-balance` | OAuth 账号均衡干跑 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:103` |
| jcode | TUI | `/auth` | 显示鉴权状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:217` |
| jcode | TUI | `/login` | 登录 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:218` |
| jcode | TUI | `/logout` | 登出 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:219` |
| jcode | TUI | `/account`（别名 `/accounts`） | 打开合并账户选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:220` |
| jcode | CLI | `jcode login [PROVIDER]` | OAuth/API key 登录 provider | `src/cli/args.rs:198` |
| jcode | CLI | `jcode account <action>` | 登录并管理 Jcode 账号 | `src/cli/args.rs:265` |
| jcode | CLI | `jcode auth <action>` | 认证状态与校验助手 | `src/cli/args.rs:325` |
| jcode | CLI | `jcode account login` | 浏览器设备授权并等待套餐激活 | `src/cli/args.rs:609` |
| jcode | CLI | `jcode account manage` | 打开 Jcode 账号管理页 | `src/cli/args.rs:627` |
| jcode | CLI | `jcode account logout` | 吊销当前 key 并安全清除本地状态 | `src/cli/args.rs:630` |
| jcode | CLI | `jcode auth import` | 从受信客户端导入一条 OAuth 登录 | `src/cli/args.rs:844` |
| jcode | CLI | `jcode auth status` | 显示模型/工具 provider 的认证状态 | `src/cli/args.rs:853` |
| jcode | TUI | `/hosted` | auth 侧实现，未登记 [归类存疑] | `auth_account_commands.rs:78,84` |

### I2 用量 · 配额 · 重置

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/usage` | 显示 provider 用量与限额 (show/reset) | `packages/coding-agent/src/slash-commands/builtin-session.ts:385` |
| omp | TUI | `/usage show` | 显示 provider 用量与限额 | `packages/coding-agent/src/slash-commands/builtin-session.ts:391` |
| omp | TUI | `/usage reset` | 消耗一次已保存的限流重置 | `packages/coding-agent/src/slash-commands/builtin-session.ts:393（4-tab 多行项）` |
| omp | CLI | `omp usage` | 显示各账号 provider 限额 | `packages/coding-agent/src/cli-commands.ts:251` |
| omp | CLI | `omp stats` | 查看使用统计 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:236` |
| jcode | TUI | `/reset` | 复核并确认 banked OpenAI 用量重置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:161` |
| jcode | TUI | `/usage` | 显示已连接 provider 的用量限额 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:162` |
| jcode | TUI | `/productivity`（别名 `/wrapped`） | 生成可分享的用量报告+仪表盘图 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:163` |
| jcode | CLI | `jcode usage` | 显示已连接 provider 的用量额度（--json） | `src/cli/args.rs:284` |
| jcode | CLI | `jcode account status` | 显示 /v1/me 的账号/套餐/用量状态（--json） [归类存疑] | `src/cli/args.rs:616` |
| jcode | TUI | `/stats` | productivity.rs:17 处理，未登记 [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:79` |

### I3 订阅 · 计费

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/subscription` | 显示 jcode 订阅状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:171` |
| jcode | TUI | `/subscribe` | 为何/如何订阅 jcode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:172` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 6 条**（该条不完全贴叶，正文对应行末尾已标）：`/session pin`（omp，I1）、``omp dry-balance``（omp，I1）、`/hosted`（jcode，I1）、``omp stats``（omp，I2）、``jcode account status``（jcode，I2）、`/stats`（jcode，I2）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
