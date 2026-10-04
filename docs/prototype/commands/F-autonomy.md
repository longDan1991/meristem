# 命令 · F 自主与自动化

> **这一块是什么**：让系统自己往前跑：目标与循环、过夜、子 agent 与 swarm、自动评审与自裁判、自我改进。
> **用户什么时候来**：用户想「不盯着它也能往前走」——这一块两家都做得很重。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §F 的分册，**同一条不多不少**（这一块 omp 22 条 · jcode 19 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| F1 | 目标 · 循环 · 棘轮 · 过夜 | 10 | 11 | 21 |
| F2 | 子 agent · swarm · 委派 | 5 | 3 | 8 |
| F3 | 自动评审 · 自动裁判 | 6 | 2 | 8 |
| F4 | 自我改进 / 自开发 | 1 | 3 | 4 |
| **合计** | | **22** | **19** | **41** |

## 两家的命令（先例原样）

### F1 目标 · 循环 · 棘轮 · 过夜

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/goal` | 切换 goal 模式（持久自主目标） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:373` |
| omp | TUI | `/guided-goal` | 让 agent 访谈你后设置 goal 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:399` |
| omp | TUI | `/loop` | 切换 loop 模式（每次 yield 重发提示） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:411` |
| omp | TUI | `/ratchet` | 为 LLM 流程建/复用 eval 并无人值守爬山 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:730` |
| omp | TUI | `/goal set` | 设置或替换当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:377` |
| omp | TUI | `/goal show` | 显示当前目标详情 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:378` |
| omp | TUI | `/goal pause` | 暂停当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:379` |
| omp | TUI | `/goal resume` | 恢复已暂停的目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:380` |
| omp | TUI | `/goal drop` | 丢弃当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:381` |
| omp | TUI | `/goal budget` | 调整目标的 token 预算 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:382` |
| jcode | TUI | `/initiatives`（别名 `/goals`） | 打开 initiative 总览/续跑 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:146` |
| jcode | TUI | `/overnight` | 运行受监督的 overnight 协调器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:152` |
| jcode | CLI | `jcode ambient <action>` | ambient 模式管理 | `src/cli/args.rs:341` |
| jcode | CLI | `jcode ambient status` | 显示 ambient 模式状态 | `src/cli/args.rs:838` |
| jcode | CLI | `jcode ambient log` | 显示近期 ambient 活动日志 | `src/cli/args.rs:840` |
| jcode | CLI | `jcode ambient trigger` | 手动触发一轮 ambient 周期 | `src/cli/args.rs:842` |
| jcode | CLI | `jcode ambient stop` | 停止 ambient 模式 | `src/cli/args.rs:844` |
| jcode | CLI | `jcode ambient run-visible` | 内部：在可见 TUI 中跑一轮 ambient（隐藏） | `src/cli/args.rs:847` |
| jcode | TUI | `/mission` | disabled 占位（与已登记项不同） [归类存疑] | `crates/jcode-tui/src/tui/app/commands.rs:2669` |
| jcode | TUI | `/goal` | disabled 占位，与 /goals 不同 [归类存疑] | `crates/jcode-tui/src/tui/app/commands.rs:2670` |
| jcode | TUI | `/ambient` | 仅文档；TUI 无此斜杠命令，只有 CLI `jcode ambient` [归类存疑] | `docs/AMBIENT_MODE.md:606` |

### F2 子 agent · swarm · 委派

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/tan` | 在切向工作上跑后台 agent | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:463` |
| omp | TUI | `/cleanse` | 用加权并行子 agent 检测修复诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:487` |
| omp | TUI | `/hub` | 打开实时 Agent Hub [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:583` |
| omp | CLI | `omp agents` | 管理内置任务 agent | `packages/coding-agent/src/cli-commands.ts:51` |
| omp | CLI | `omp cleanse` | 并行子 agent 检测修复诊断 | `packages/coding-agent/src/cli-commands.ts:66` |
| jcode | TUI | `/swarm-prompt` | 在编辑器打开 swarm 路由提示词 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:52` |
| jcode | TUI | `/subagent` | 手动启动 subagent | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:56` |
| jcode | TUI | `/swarm` | 切换 swarm 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:151` |

### F3 自动评审 · 自动裁判

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/advisor` | 切换 advisor（第二个模型每轮评审并注入笔记） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:62` |
| omp | TUI | `/advisor on` | 启用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:68` |
| omp | TUI | `/advisor off` | 停用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:69` |
| omp | TUI | `/advisor status` | 显示 advisor 状态 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:70` |
| omp | TUI | `/advisor dump` | 把 advisor 记录复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:71` |
| omp | TUI | `/advisor configure` | 打开 advisor 配置编辑器（TUI） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:72` |
| jcode | TUI | `/autoreview` | 显示/切换回合末自动 review | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:104` |
| jcode | TUI | `/autojudge` | 显示/切换回合末自动 judge | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:105` |

### F4 自我改进 / 自开发

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/omfg` | 从抱怨生成 TTSR 规则 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:475` |
| jcode | TUI | `/improve` | 自主改进仓库 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:137` |
| jcode | TUI | `/selfdev` | 打开新的 self-dev 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:195` |
| jcode | CLI | `jcode self-dev`（别名 `selfdev`） | self-development canary 会话（--build） | `src/cli/args.rs:294` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 4 条**（该条不完全贴叶，正文对应行末尾已标）：`/mission`（jcode，F1）、`/goal`（jcode，F1）、`/ambient`（jcode，F1）、`/hub`（omp，F2）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
