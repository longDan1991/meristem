# 命令 · D 工具与权限

> **这一块是什么**：模型能伸出哪些手、伸出去要不要先问人、接哪些外部服务与别的机器。
> **用户什么时候来**：用户想改「它能碰到什么」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §D 的分册，**同一条不多不少**（这一块 omp 52 条 · jcode 12 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| D1 | 工具开关 | 2 | 0 | 2 |
| D2 | 审批 · 沙箱 · 安全检查 | 12 | 3 | 15 |
| D3 | MCP server | 18 | 0 | 18 |
| D4 | 远端机器（ssh / 远端会话） | 6 | 2 | 8 |
| D5 | 别的"手"（浏览器 · 计算机 · 图 · 搜索 …） | 14 | 7 | 21 |
| **合计** | | **52** | **12** | **64** |

## 两家的命令（先例原样）

### D1 工具开关

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/force`（别名 `force:`） | 强制下一轮使用指定工具 | `packages/coding-agent/src/slash-commands/builtin-control.ts:9` |
| omp | TUI | `/tools` | 显示 agent 当前可见工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:505` |

### D2 审批 · 沙箱 · 安全检查

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/security` | 规划/运行/查看/导入/比对原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:275` |
| omp | TUI | `/security plan` | 创建一次不可变的安全扫描计划 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:281` |
| omp | TUI | `/security scan` | 开始计划内或新建的原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:282` |
| omp | TUI | `/security status` | 显示原生扫描任务状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:283` |
| omp | TUI | `/security cancel` | 取消运行中的原生扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:284` |
| omp | TUI | `/security scans` | 列出项目已存的安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:285` |
| omp | TUI | `/security show` | 渲染某次扫描或 security:// 资源 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:286` |
| omp | TUI | `/security import` | 导入 SARIF 或 Codex 安全包 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:287` |
| omp | TUI | `/security export` | 导出规范包 / SARIF / 报告 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:288` |
| omp | TUI | `/security validate` | 用原生工具校验单条 finding | `packages/coding-agent/src/slash-commands/builtin-modes.ts:289` |
| omp | TUI | `/security compare` | 比较两次扫描的 finding 血缘 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:290` |
| omp | TUI | `/security disposition` | 为 finding 设置处置与理由 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:291` |
| jcode | CLI | `jcode permissions` | 处理待定的 ambient 权限请求 | `src/cli/args.rs:363` |
| jcode | TUI | `/permissions` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:31` |
| jcode | TUI | `/permission` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:32` |

### D3 MCP server

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/mcp` | 管理 MCP 服务器（add/list/remove/test 等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:696` |
| omp | TUI | `/mcp add` | 新增一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:703（4-tab 多行项）` |
| omp | TUI | `/mcp list` | 列出全部已配置 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:707` |
| omp | TUI | `/mcp remove` | 移除一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:708` |
| omp | TUI | `/mcp test` | 测试到某 server 的连接 | `packages/coding-agent/src/slash-commands/builtin-session.ts:709` |
| omp | TUI | `/mcp reauth` | 为某 server 重新授权 OAuth | `packages/coding-agent/src/slash-commands/builtin-session.ts:710` |
| omp | TUI | `/mcp unauth` | 移除某 server 的 OAuth 授权 | `packages/coding-agent/src/slash-commands/builtin-session.ts:711` |
| omp | TUI | `/mcp enable` | 启用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:712` |
| omp | TUI | `/mcp disable` | 停用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:713` |
| omp | TUI | `/mcp smithery-search` | 搜索 Smithery 并部署一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:715（4-tab 多行项）` |
| omp | TUI | `/mcp smithery-login` | 登录 Smithery 并缓存 API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:719` |
| omp | TUI | `/mcp smithery-logout` | 移除已缓存的 Smithery API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:720` |
| omp | TUI | `/mcp reconnect` | 重连到指定 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:721` |
| omp | TUI | `/mcp reload` | 强制重载 MCP 运行时工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:722` |
| omp | TUI | `/mcp resources` | 列出已连 server 的可用资源 | `packages/coding-agent/src/slash-commands/builtin-session.ts:723` |
| omp | TUI | `/mcp prompts` | 列出已连 server 的 prompts | `packages/coding-agent/src/slash-commands/builtin-session.ts:724` |
| omp | TUI | `/mcp notifications` | 显示通知能力与订阅状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:725` |
| omp | TUI | `/mcp help` | 显示 /mcp 帮助 | `packages/coding-agent/src/slash-commands/builtin-session.ts:726` |

### D4 远端机器（ssh / 远端会话）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/ssh` | 管理 SSH 主机（add/list/remove） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:153` |
| omp | TUI | `/ssh add` | 新增一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:160（4-tab 多行项）` |
| omp | TUI | `/ssh list` | 列出全部已配置 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:164` |
| omp | TUI | `/ssh remove` | 移除一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:165` |
| omp | TUI | `/ssh help` | 显示 /ssh 帮助 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:166` |
| omp | CLI | `omp ssh` | 管理 SSH 主机配置 | `packages/coding-agent/src/cli-commands.ts:231` |
| jcode | TUI | `/ssh` | 用系统 SSH 连接远程机器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:63` |
| jcode | TUI | `/exit` | 仅 SSH 登录取消语境，未登记 [归类存疑] | `crates/jcode-tui/src/tui/app/auth_remote.rs:447` |

### D5 别的"手"（浏览器 · 计算机 · 图 · 搜索 …）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/computer` | 切换本会话计算机使用 eval 前奏 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:685` |
| omp | TUI | `/browser` | 切换浏览器 eval 前奏无头/可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:475` |
| omp | TUI | `/open` | 用浏览器打开会话中最后的链接 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:597` |
| omp | TUI | `/live` | 启动 Codex 实时语音模式 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-control.ts:59` |
| omp | TUI | `/computer on` | 本会话启用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:691` |
| omp | TUI | `/computer off` | 本会话停用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:692` |
| omp | TUI | `/computer status` | 显示 computer use 状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:693` |
| omp | TUI | `/browser headless` | 切换到无头模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:480` |
| omp | TUI | `/browser visible` | 切换到可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:481` |
| omp | CLI | `omp browser-relay` | 本地 CDP relay 驱动自有 Chrome [归类存疑] | `packages/coding-agent/src/cli-commands.ts:61` |
| omp | CLI | `omp find` | 语义搜索行为到文件/行范围 | `packages/coding-agent/src/cli-commands.ts:108` |
| omp | CLI | `omp images`（别名 `img`） | 图片发布后端检查/诊断/清理 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:138` |
| omp | CLI | `omp say` | 本地 TTS 合成并播放 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:185` |
| omp | CLI | `omp search`（别名 `q` `web-search`） | 测试 web 搜索 provider | `packages/coding-agent/src/cli-commands.ts:282` |
| jcode | TUI | `/voice` | 语音输入：说，然后发送（Ctrl+Space） [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:141` |
| jcode | TUI | `/dictate`（别名 `/dictation`） | 运行配置的外部听写命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:142` |
| jcode | CLI | `jcode dictate` | 运行配置的听写（--type 直接键入） | `src/cli/args.rs:377` |
| jcode | CLI | `jcode browser <action> [browser]` | 浏览器自动化 setup/status/detect | `src/cli/args.rs:407` |
| jcode | TUI | `/open` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:59` |
| jcode | TUI | `/file` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:60` |
| jcode | TUI | `/new-terminal` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:62` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 10 条**（该条不完全贴叶，正文对应行末尾已标）：`/exit`（jcode，D4）、`/open`（omp，D5）、`/live`（omp，D5）、``omp browser-relay``（omp，D5）、``omp images``（omp，D5）、``omp say``（omp，D5）、`/voice`（jcode，D5）、`/open`（jcode，D5）、`/file`（jcode，D5）、`/new-terminal`（jcode，D5）
- **`[未核实]` 5 条**（源里读不出确切语义，原样保留）：`/permissions`（jcode，D2）、`/permission`（jcode，D2）、`/open`（jcode，D5）、`/file`（jcode，D5）、`/new-terminal`（jcode，D5）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
