# 命令 · B 模型与给养

> **这一块是什么**：这次干活用哪个脑子、哪套注意力（角色）、多少上下文、记不记得住、带哪些技能。
> **用户什么时候来**：用户想换「能力组合」——尤其是换角色，以及上下文快满的时候。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §B 的分册，**同一条不多不少**（这一块 omp 60 条 · jcode 24 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| B1 | 选模型 · 档位 · 服务级别 · 传输 | 14 | 11 | 25 |
| B2 | 角色 / 子 agent 的模型策略 | 9 | 2 | 11 |
| B3 | 上下文容量与压缩 | 10 | 2 | 12 |
| B4 | 记忆 | 17 | 8 | 25 |
| B5 | 技能 | 10 | 1 | 11 |
| **合计** | | **60** | **24** | **84** |

## 两家的命令（先例原样）

### B1 选模型 · 档位 · 服务级别 · 传输

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/model`（别名 `models`） | 切换本会话模型 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:451` |
| omp | TUI | `/switch` | 切换模型（同 alt+p，支持模糊/@role） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:495` |
| omp | TUI | `/fast` | 切换快速服务档 (priority/ultrafast) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:546` |
| omp | TUI | `/slow` | 切换慢速档 (flex/低优先级) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:574` |
| omp | TUI | `/fast on` | 启用 fast 模式（priority 档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:553` |
| omp | TUI | `/fast ultra` | 启用 Ultrafast（OpenAI/部分 Codex） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:554` |
| omp | TUI | `/fast off` | 关闭 fast 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:555` |
| omp | TUI | `/fast status` | 显示 fast 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:556` |
| omp | TUI | `/slow on` | 启用 slow（flex / Anthropic 低优先级） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:581` |
| omp | TUI | `/slow off` | 关闭 slow，回到标准服务 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:582` |
| omp | TUI | `/slow status` | 显示 slow 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:583` |
| omp | TUI | `/fresh` | 重置 provider 流状态，保留记录 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:185` |
| omp | CLI | `omp models` | 列出/搜索/刷新可用模型 | `packages/coding-agent/src/cli-commands.ts:164` |
| omp | CLI | `omp tiny-models` | 下载本地 tiny 模型 | `packages/coding-agent/src/cli-commands.ts:256` |
| jcode | TUI | `/model`（别名 `/models`） | 列出或切换模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:43` |
| jcode | TUI | `/refresh-model-list` | 刷新 provider 模型目录 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:50` |
| jcode | TUI | `/effort` | 显示/修改推理力度 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:108` |
| jcode | TUI | `/fast` | 切换 fast mode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:109` |
| jcode | TUI | `/transport` | 显示/修改连接传输 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:110` |
| jcode | CLI | `jcode provider <action>` | provider 发现与选择助手 | `src/cli/args.rs:329` |
| jcode | CLI | `jcode model <action>` | 模型管理命令 | `src/cli/args.rs:467` |
| jcode | CLI | `jcode provider list` | 列出可传给 -p/--provider 的 ID（--json） | `src/cli/args.rs:706` |
| jcode | CLI | `jcode provider current` | 显示当前请求与实际解析出的 provider 选择 | `src/cli/args.rs:713` |
| jcode | CLI | `jcode provider add <name>` | 新增命名 OpenAI 兼容 profile | `src/cli/args.rs:718` |
| jcode | CLI | `jcode model list` | 列出可传给 -m/--model 的模型名 | `src/cli/args.rs:1030` |

### B2 角色 / 子 agent 的模型策略

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/vibe` | 切换 vibe 模式（只读快好 worker 会话） [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:355` |
| omp | TUI | `/prewalk` | 布置/重启一次性模型交接 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:764` |
| omp | TUI | `/modelpreset` | 保存并切换模型预设（角色+思考档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:814` |
| omp | TUI | `/agents` | 打开 agents hub（每 agent 模型等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:563` |
| omp | TUI | `/prewalk restart` | 回到 @default 并重新武装到 @smol 的交接 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:770` |
| omp | TUI | `/modelpreset list` | 列出已保存的模型预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:821` |
| omp | TUI | `/modelpreset save` | 保存当前角色模型与思考级别 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:822` |
| omp | TUI | `/modelpreset switch` | 应用一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:823` |
| omp | TUI | `/modelpreset delete` | 删除一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:824` |
| jcode | TUI | `/agents` | 配置 agent 角色的模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:51` |
| jcode | TUI | `/subagent-model` | 显示/修改子代理模型策略 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:103` |

### B3 上下文容量与压缩

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/extended-context` | 切换扩展上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:658` |
| omp | TUI | `/compact` | 手动压缩会话上下文 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:227` |
| omp | TUI | `/context` | 显示上下文用量估算明细 | `packages/coding-agent/src/slash-commands/builtin-session.ts:534` |
| omp | TUI | `/extended-context on` | 启用更大的上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:664` |
| omp | TUI | `/extended-context off` | 使用默认/标准价上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:665` |
| omp | TUI | `/extended-context status` | 显示扩展上下文状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:666` |
| omp | TUI | `/compact soft` | 本地用当前模型压缩（跳过服务端压缩） | `packages/coding-agent/src/session/compact-modes.ts:42（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射为子命令）` |
| omp | TUI | `/compact remote` | 走服务端压缩，失败回退本地摘要 | `packages/coding-agent/src/session/compact-modes.ts:47（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| omp | TUI | `/compact snapcompact` | 把历史归档成位图图片（不调 LLM） | `packages/coding-agent/src/session/compact-modes.ts:52（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| omp | CLI | `omp compress` | 把文本改写为稠密 prompt 寄存器 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:93` |
| jcode | TUI | `/compact` | 压缩上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:139` |
| jcode | TUI | `/cache` | 显示缓存统计；extend/5m 省 Anthropic TTL [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:222` |

### B4 记忆

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/memory` | 检查并操作记忆维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:543` |
| omp | TUI | `/memory view` | 显示当前记忆注入 payload | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:549` |
| omp | TUI | `/memory stats` | 显示记忆后端统计 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:550` |
| omp | TUI | `/memory diagnose` | 运行记忆后端诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:551` |
| omp | TUI | `/memory queue` | 显示待合并的记忆增量 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:552` |
| omp | TUI | `/memory sync` | 立即运行记忆合并 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:553` |
| omp | TUI | `/memory clear` | 清除持久化记忆数据与产物 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:554` |
| omp | TUI | `/memory reset` | clear 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:555` |
| omp | TUI | `/memory enqueue` | 入队记忆合并维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:556` |
| omp | TUI | `/memory rebuild` | enqueue 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:557` |
| omp | TUI | `/memory mm list` | 列出当前 bank 的心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:558` |
| omp | TUI | `/memory mm show` | 显示单个心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:559` |
| omp | TUI | `/memory mm refresh` | 整库刷新自动刷新模型，或按 id 刷一个 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:561（4-tab 多行项）` |
| omp | TUI | `/memory mm history` | 查看某心智模型的变更历史 diff | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:564` |
| omp | TUI | `/memory mm seed` | 创建缺失的内置心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:565` |
| omp | TUI | `/memory mm delete` | 从 bank 删除心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:566` |
| omp | TUI | `/memory mm reload` | 重新拉取缓存的 <mental_models> 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:567` |
| jcode | TUI | `/memory` | 切换 memory 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:144` |
| jcode | CLI | `jcode memory <action>` | 记忆管理命令 | `src/cli/args.rs:333` |
| jcode | CLI | `jcode memory list` | 列出全部记忆（--scope/--tag） | `src/cli/args.rs:1146` |
| jcode | CLI | `jcode memory search <query>` | 按查询检索记忆（--semantic） | `src/cli/args.rs:1160` |
| jcode | CLI | `jcode memory export <output>` | 导出记忆到 JSON（--scope） | `src/cli/args.rs:1173` |
| jcode | CLI | `jcode memory import <input>` | 从 JSON 导入记忆（--scope/--overwrite） | `src/cli/args.rs:1183` |
| jcode | CLI | `jcode memory stats` | 显示记忆统计 | `src/cli/args.rs:1200` |
| jcode | CLI | `jcode memory clear-test` | 清理测试记忆存储（调试会话用） | `src/cli/args.rs:1203` |

### B5 技能

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/skillful` | 切换系统提示中列出可用技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:602` |
| omp | TUI | `/skills` | 从 skills.omp.sh 搜索/安装/更新技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:66` |
| omp | TUI | `/skillful on` | 本会话在提示中列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:608` |
| omp | TUI | `/skillful off` | 本会话不列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:609` |
| omp | TUI | `/skillful status` | 显示技能列举状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:610` |
| omp | TUI | `/skills search` | 搜索技能注册表 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:70` |
| omp | TUI | `/skills install` | 安装注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:71` |
| omp | TUI | `/skills installed` | 列出已安装的注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:72` |
| omp | TUI | `/skills update` | 在声明范围内更新注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:74（4-tab 多行项）` |
| omp | CLI | `omp skill`（别名 `skills`） | Skillshare 技能安装/搜索/发布 | `packages/coding-agent/src/cli-commands.ts:225` |
| jcode | TUI | `/skills` | 显示已加载 skills 与推荐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:154` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 5 条**（该条不完全贴叶，正文对应行末尾已标）：`/fresh`（omp，B1）、`/vibe`（omp，B2）、`/prewalk`（omp，B2）、``omp compress``（omp，B3）、`/cache`（jcode，B3）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
