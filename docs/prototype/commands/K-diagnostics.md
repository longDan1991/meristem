# 命令 · K 诊断与调试

> **这一块是什么**：看它内部出了什么事：日志与追踪、调试面板与性能、遥测与隐私、截图与演示、自检。
> **用户什么时候来**：用户怀疑「不是我用错了，是它坏了」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §K 的分册，**同一条不多不少**（这一块 omp 10 条 · jcode 19 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| K1 | 日志 · 追踪 | 2 | 1 | 3 |
| K2 | 调试面板 · 性能 · 可视化 | 4 | 3 | 7 |
| K3 | 遥测 · 隐私 | 0 | 5 | 5 |
| K4 | 截图 · 录制 · 演示 | 2 | 4 | 6 |
| K5 | 自检（按键冲突 · provider 测试覆盖 · 版本自检） | 2 | 6 | 8 |
| **合计** | | **10** | **19** | **29** |

## 两家的命令（先例原样）

### K1 日志 · 追踪

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/trace` | 在统计面板打开本会话 trace | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:203` |
| omp | TUI | `/dump` | 复制会话记录并写 LLM 请求 JSON [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:230` |
| jcode | TUI | `/log` | 在 jcode 日志中标记当前位置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:174` |

### K2 调试面板 · 性能 · 可视化

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/stats` | 启动本地统计面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:432` |
| omp | TUI | `/debug` | 打开调试工具选择器 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:534` |
| omp | CLI | `omp gallery` | 预览渲染器视觉画廊 | `packages/coding-agent/src/cli-commands.ts:123` |
| omp | CLI | `omp render` | 用生产管线渲染会话线程 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:220` |
| jcode | TUI | `/debug-visual` | 切换可视化调试覆盖层 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:223` |
| jcode | CLI | `jcode debug <command> [arg]` | 调试 socket CLI（--session/--socket/--wait） [归类存疑] | `src/cli/args.rs:302` |
| jcode | TUI | `/debug-fixture` | debug.rs:581 处理 gmail-draft，未登记 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:87` |

### K3 遥测 · 隐私

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| jcode | TUI | `/telemetry` | 显示/修改 jcode 发送的数据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:169` |
| jcode | CLI | `jcode telemetry <action>` | 查看/修改匿名遥测设置 | `src/cli/args.rs:290` |
| jcode | CLI | `jcode telemetry status` | 显示当前遥测状态，不创建匿名 ID | `src/cli/args.rs:600` |
| jcode | CLI | `jcode telemetry enable` | 启用匿名用量遥测 | `src/cli/args.rs:607` |
| jcode | CLI | `jcode telemetry disable` | 持久禁用所有遥测 | `src/cli/args.rs:609` |

### K4 截图 · 录制 · 演示

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/record` | 开始/停止录制本屏到可回放文件 | `packages/coding-agent/src/slash-commands/builtin-control.ts:68` |
| omp | CLI | `omp play` | 回放 `/record` 录屏 | `packages/coding-agent/src/cli-commands.ts:195` |
| jcode | TUI | `/screenshot-mode` | 切换截图捕获模式 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:224` |
| jcode | TUI | `/screenshot` | 捕获一个截图调试状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:225` |
| jcode | TUI | `/record` | 录制一段 demo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:226` |
| jcode | CLI | `jcode replay <session>` | 在 TUI 重放会话 | `src/cli/args.rs:418` |

### K5 自检（按键冲突 · provider 测试覆盖 · 版本自检）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp grep` | 测试 grep 工具 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:118` |
| omp | CLI | `omp ttsr` | 检查/测试 TTSR 规则 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:271` |
| jcode | TUI | `/provider-test-coverage`（别名 `/model-status`） | 显示当前 provider/model 的实机测试证据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:45` |
| jcode | TUI | `/keys`（别名 `/keybindings`） | 显示与终端/系统的键位冲突（/keys refresh 重扫） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:175` |
| jcode | CLI | `jcode provider-test-coverage`（别名 `model-status`） | 显示实机验证覆盖 | `src/cli/args.rs:472` |
| jcode | CLI | `jcode provider-doctor`（别名 `provider-strict-e2e`） | 按严格 E2E 关卡诊断 provider/model | `src/cli/args.rs:493` |
| jcode | CLI | `jcode auth-test` | 端到端测试认证 [归类存疑] | `src/cli/args.rs:510` |
| jcode | CLI | `jcode auth doctor [PROVIDER]` | 诊断 provider 认证问题（--validate/--json） [归类存疑] | `src/cli/args.rs:859` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 7 条**（该条不完全贴叶，正文对应行末尾已标）：`/dump`（omp，K1）、``omp render``（omp，K2）、``jcode debug <command> [arg]``（jcode，K2）、``omp grep``（omp，K5）、``omp ttsr``（omp，K5）、``jcode auth-test``（jcode，K5）、``jcode auth doctor [PROVIDER]``（jcode，K5）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
