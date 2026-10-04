# 先例 · 命令分类（跨两家）

> 这一份是两份「先例原样」的**派生视图**：把两家的**命令**（不含 flag、不含设置项）按「用户想干什么」归位，**一条命令恰好出现一次**。
> 用途：设计我们自己的命令面时，按**意图**查“两家各叫什么、谁有谁没有、代价是什么”。
> 证据仍在 [`omp.md`](omp.md) / [`jcode.md`](jcode.md)；本文件只做归位与统计。
> 归类口径：斜杠命令 + 子命令 + CLI 子命令（名字写完整，如 `/security plan`、`omp plugin`、`jcode cloud sessions`）；真别名折进父行；`[归类存疑]` 表示该条不完全贴叶。

## 0. 总表

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| A1 | 开一条新的 · 换一条 · 回上一条 | 3 | 5 | 8 |
| A2 | 命名 · 收藏 · 标记 · 归档 | 2 | 4 | 6 |
| A3 | 分叉 · 交接 · 回退（fork / handoff / rewind / transfer） | 3 | 3 | 6 |
| A4 | 清屏 · 清上下文 · 删除 · 导出 | 9 | 2 | 11 |
| A5 | 这条线的信息（token / 状态 / 记录文件） | 2 | 6 | 8 |
| B1 | 选模型 · 档位 · 服务级别 · 传输 | 14 | 11 | 25 |
| B2 | 角色 / 子 agent 的模型策略 | 9 | 2 | 11 |
| B3 | 上下文容量与压缩 | 10 | 2 | 12 |
| B4 | 记忆 | 17 | 8 | 25 |
| B5 | 技能 | 10 | 1 | 11 |
| C1 | 打断 · 取消 · 暂停 · 继续 | 1 | 2 | 3 |
| C2 | 重试 · 修复 · 催促 | 1 | 2 | 3 |
| C3 | 排队 · 后台 · 插入 | 2 | 0 | 2 |
| C4 | 计划模式（先规划再动手） | 14 | 1 | 15 |
| D1 | 工具开关 | 2 | 0 | 2 |
| D2 | 审批 · 沙箱 · 安全检查 | 12 | 3 | 15 |
| D3 | MCP server | 18 | 0 | 18 |
| D4 | 远端机器（ssh / 远端会话） | 6 | 2 | 8 |
| D5 | 别的"手"（浏览器 · 计算机 · 图 · 搜索 …） | 14 | 7 | 21 |
| E1 | git · 分支 · worktree | 4 | 1 | 5 |
| E2 | 提交 · 推送 · 合入 | 1 | 3 | 4 |
| E3 | 评审 · 测试 · 重构 · 改进 | 0 | 4 | 4 |
| E4 | issue · 分诊 | 0 | 1 | 1 |
| F1 | 目标 · 循环 · 棘轮 · 过夜 | 10 | 11 | 21 |
| F2 | 子 agent · swarm · 委派 | 5 | 3 | 8 |
| F3 | 自动评审 · 自动裁判 | 6 | 2 | 8 |
| F4 | 自我改进 / 自开发 | 1 | 3 | 4 |
| G1 | 主题 · 颜色 · 符号 · 对齐 | 1 | 3 | 4 |
| G2 | 状态条 · 事实行 · 布局 | 0 | 3 | 3 |
| G3 | 键位 · 终端设置 · 按键冲突 | 0 | 2 | 2 |
| G4 | 显示开关（思考 / 工具详情 / 通知 / diff / 图片 / 滚动条） | 0 | 5 | 5 |
| H1 | 多端 · 远端接入 · 云 · 回本机 | 3 | 22 | 25 |
| H2 | 分享 · 录屏 · 广播 | 10 | 0 | 10 |
| H3 | workspace（多会话平移） | 4 | 1 | 5 |
| I1 | 登录 · 登出 · 多账号 | 9 | 13 | 22 |
| I2 | 用量 · 配额 · 重置 | 5 | 6 | 11 |
| I3 | 订阅 · 计费 | 0 | 2 | 2 |
| J1 | 插件 · 市场 | 17 | 0 | 17 |
| J2 | 扩展 · hooks · ACP | 2 | 1 | 3 |
| K1 | 日志 · 追踪 | 2 | 1 | 3 |
| K2 | 调试面板 · 性能 · 可视化 | 4 | 3 | 7 |
| K3 | 遥测 · 隐私 | 0 | 5 | 5 |
| K4 | 截图 · 录制 · 演示 | 2 | 4 | 6 |
| K5 | 自检（按键冲突 · provider 测试覆盖 · 版本自检） | 2 | 6 | 8 |
| L1 | 更新 · 重启 · 重载 | 5 | 13 | 18 |
| L2 | 自构建 · 发布 · 安装 | 0 | 5 | 5 |
| L3 | 初始化 · 首启 · 终端接入 | 3 | 3 | 6 |
| M1 | 帮助 · 命令表 · 键位表 | 1 | 2 | 3 |
| M2 | 版本 · 变更日志 | 3 | 3 | 6 |
| M3 | 反馈 · 支持 | 1 | 2 | 3 |
| M4 | 隐藏 / 彩蛋命令 | 1 | 2 | 3 |
| O1 | 服务端 · 连接 · 桥接 | 1 | 10 | 11 |
| O2 | 后台/持久进程的查看与清理 | 3 | 1 | 4 |
| P | 基准与实验（CLI 为主） | 3 | 0 | 3 |
| Q | 其它内部工具（CLI 为主，兜底） | 5 | 2 | 7 |
| **合计** | | **263** | **209** | **472** |

## A 会话（这条线/这段对话本身）

### A1 开一条新的 · 换一条 · 回上一条

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/new` | 开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:176` |
| omp | `/resume` | 恢复另一个会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:389` |
| omp | `/tree` | 浏览会话树（切换分支） [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:611` |
| jcode | `/resume`（别名 `/sessions` `/session`） | 打开会话选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:198` |
| jcode | `/active` | 管理活动会话（working/ready） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:201` |
| jcode | `/catchup` | 打开 Catch Up 选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:202` |
| jcode | `/back` | 回到上一个 Catch Up 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:203` |
| jcode | `jcode session <action>` | 会话管理命令 | `src/cli/args.rs:337` |

### A2 命名 · 收藏 · 标记 · 归档

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/pin` | 在恢复列表顶部固定/取消固定会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:420` |
| omp | `/rename` | 重命名当前会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:632` |
| jcode | `/save` | 收藏会话便于访问 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:204` |
| jcode | `/unsave` | 移除会话收藏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:205` |
| jcode | `/rename` | 重命名当前会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:206` |
| jcode | `jcode session rename <session> [name]` | 重命名已保存会话（--clear/--json） | `src/cli/args.rs:1044` |

### A3 分叉 · 交接 · 回退（fork / handoff / rewind / transfer）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/branch`（别名 `rewind`） | 回退到旧消息并保留旧路径为分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:592` |
| omp | `/fork` | 从旧消息创建新分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:602` |
| omp | `/handoff` | 总结为交接文档并原地压缩 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:322` |
| jcode | `/rewind` | 回退到上一条消息 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:134` |
| jcode | `/fork`（别名 `/split`） | 把会话分叉到新窗口（可选 prompt） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:207` |
| jcode | `/transfer` | 把上下文压缩进新的交接会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:209` |

### A4 清屏 · 清上下文 · 删除 · 导出

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/clear` | 原地清空会话上下文，保留会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:207` |
| omp | `/delete` | 删除当前会话并开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:218` |
| omp | `/shake` | 丢弃上下文中重内容（工具结果等） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:293` |
| omp | `/export` | 导出会话为 HTML 文件 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:179` |
| omp | `/copy` | 选取会话中的文本或代码复制 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:545` |
| omp | `/session delete` | 删除当前会话并回到选择器 | `packages/coding-agent/src/slash-commands/builtin-session.ts:253` |
| omp | `/shake elide` | 剥离工具结果与大块（默认） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:298` |
| omp | `/shake images` | 剥离图片块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:299` |
| omp | `/shake thinking` | 丢弃所有 thinking 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:300` |
| jcode | `/clear` | 清空会话历史 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:131` |
| jcode | `/cls`（别名 `/clear-view`） | 仅清屏，保留上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:132` |

### A5 这条线的信息（token / 状态 / 记录文件）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/session` | 会话管理命令 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:246` |
| omp | `/session info` | 显示当前会话信息与统计 | `packages/coding-agent/src/slash-commands/builtin-session.ts:252` |
| jcode | `/observe` | 侧栏显示最新工具上下文 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:57` |
| jcode | `/todos`（别名 `/todo`） | 在聊天以卡片显示会话 todo 列表 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:58` |
| jcode | `/transcript` | 打开当前会话 transcript 文件 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:102` |
| jcode | `/context` | 显示完整会话上下文快照 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:153` |
| jcode | `/info` | 显示会话信息与 token | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:160` |
| jcode | `jcode transcript [text]` | 把外部转录文本注入活动 TUI（--mode/--session） [归类存疑] | `src/cli/args.rs:366` |

## B 模型与给养

### B1 选模型 · 档位 · 服务级别 · 传输

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/model`（别名 `models`） | 切换本会话模型 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:451` |
| omp | `/switch` | 切换模型（同 alt+p，支持模糊/@role） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:495` |
| omp | `/fast` | 切换快速服务档 (priority/ultrafast) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:546` |
| omp | `/slow` | 切换慢速档 (flex/低优先级) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:574` |
| omp | `/fast on` | 启用 fast 模式（priority 档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:553` |
| omp | `/fast ultra` | 启用 Ultrafast（OpenAI/部分 Codex） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:554` |
| omp | `/fast off` | 关闭 fast 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:555` |
| omp | `/fast status` | 显示 fast 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:556` |
| omp | `/slow on` | 启用 slow（flex / Anthropic 低优先级） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:581` |
| omp | `/slow off` | 关闭 slow，回到标准服务 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:582` |
| omp | `/slow status` | 显示 slow 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:583` |
| omp | `/fresh` | 重置 provider 流状态，保留记录 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:185` |
| omp | `omp models` | 列出/搜索/刷新可用模型 | `packages/coding-agent/src/cli-commands.ts:164` |
| omp | `omp tiny-models` | 下载本地 tiny 模型 | `packages/coding-agent/src/cli-commands.ts:256` |
| jcode | `/model`（别名 `/models`） | 列出或切换模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:43` |
| jcode | `/refresh-model-list` | 刷新 provider 模型目录 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:50` |
| jcode | `/effort` | 显示/修改推理力度 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:108` |
| jcode | `/fast` | 切换 fast mode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:109` |
| jcode | `/transport` | 显示/修改连接传输 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:110` |
| jcode | `jcode provider <action>` | provider 发现与选择助手 | `src/cli/args.rs:329` |
| jcode | `jcode model <action>` | 模型管理命令 | `src/cli/args.rs:467` |
| jcode | `jcode provider list` | 列出可传给 -p/--provider 的 ID（--json） | `src/cli/args.rs:706` |
| jcode | `jcode provider current` | 显示当前请求与实际解析出的 provider 选择 | `src/cli/args.rs:713` |
| jcode | `jcode provider add <name>` | 新增命名 OpenAI 兼容 profile | `src/cli/args.rs:718` |
| jcode | `jcode model list` | 列出可传给 -m/--model 的模型名 | `src/cli/args.rs:1030` |

### B2 角色 / 子 agent 的模型策略

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/vibe` | 切换 vibe 模式（只读快好 worker 会话） [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:355` |
| omp | `/prewalk` | 布置/重启一次性模型交接 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:764` |
| omp | `/modelpreset` | 保存并切换模型预设（角色+思考档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:814` |
| omp | `/agents` | 打开 agents hub（每 agent 模型等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:563` |
| omp | `/prewalk restart` | 回到 @default 并重新武装到 @smol 的交接 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:770` |
| omp | `/modelpreset list` | 列出已保存的模型预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:821` |
| omp | `/modelpreset save` | 保存当前角色模型与思考级别 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:822` |
| omp | `/modelpreset switch` | 应用一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:823` |
| omp | `/modelpreset delete` | 删除一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:824` |
| jcode | `/agents` | 配置 agent 角色的模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:51` |
| jcode | `/subagent-model` | 显示/修改子代理模型策略 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:103` |

### B3 上下文容量与压缩

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/extended-context` | 切换扩展上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:658` |
| omp | `/compact` | 手动压缩会话上下文 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:227` |
| omp | `/context` | 显示上下文用量估算明细 | `packages/coding-agent/src/slash-commands/builtin-session.ts:534` |
| omp | `/extended-context on` | 启用更大的上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:664` |
| omp | `/extended-context off` | 使用默认/标准价上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:665` |
| omp | `/extended-context status` | 显示扩展上下文状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:666` |
| omp | `/compact soft` | 本地用当前模型压缩（跳过服务端压缩） | `packages/coding-agent/src/session/compact-modes.ts:42（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射为子命令）` |
| omp | `/compact remote` | 走服务端压缩，失败回退本地摘要 | `packages/coding-agent/src/session/compact-modes.ts:47（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| omp | `/compact snapcompact` | 把历史归档成位图图片（不调 LLM） | `packages/coding-agent/src/session/compact-modes.ts:52（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| omp | `omp compress` | 把文本改写为稠密 prompt 寄存器 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:93` |
| jcode | `/compact` | 压缩上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:139` |
| jcode | `/cache` | 显示缓存统计；extend/5m 省 Anthropic TTL [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:222` |

### B4 记忆

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/memory` | 检查并操作记忆维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:543` |
| omp | `/memory view` | 显示当前记忆注入 payload | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:549` |
| omp | `/memory stats` | 显示记忆后端统计 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:550` |
| omp | `/memory diagnose` | 运行记忆后端诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:551` |
| omp | `/memory queue` | 显示待合并的记忆增量 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:552` |
| omp | `/memory sync` | 立即运行记忆合并 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:553` |
| omp | `/memory clear` | 清除持久化记忆数据与产物 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:554` |
| omp | `/memory reset` | clear 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:555` |
| omp | `/memory enqueue` | 入队记忆合并维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:556` |
| omp | `/memory rebuild` | enqueue 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:557` |
| omp | `/memory mm list` | 列出当前 bank 的心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:558` |
| omp | `/memory mm show` | 显示单个心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:559` |
| omp | `/memory mm refresh` | 整库刷新自动刷新模型，或按 id 刷一个 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:561（4-tab 多行项）` |
| omp | `/memory mm history` | 查看某心智模型的变更历史 diff | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:564` |
| omp | `/memory mm seed` | 创建缺失的内置心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:565` |
| omp | `/memory mm delete` | 从 bank 删除心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:566` |
| omp | `/memory mm reload` | 重新拉取缓存的 <mental_models> 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:567` |
| jcode | `/memory` | 切换 memory 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:144` |
| jcode | `jcode memory <action>` | 记忆管理命令 | `src/cli/args.rs:333` |
| jcode | `jcode memory list` | 列出全部记忆（--scope/--tag） | `src/cli/args.rs:1146` |
| jcode | `jcode memory search <query>` | 按查询检索记忆（--semantic） | `src/cli/args.rs:1160` |
| jcode | `jcode memory export <output>` | 导出记忆到 JSON（--scope） | `src/cli/args.rs:1173` |
| jcode | `jcode memory import <input>` | 从 JSON 导入记忆（--scope/--overwrite） | `src/cli/args.rs:1183` |
| jcode | `jcode memory stats` | 显示记忆统计 | `src/cli/args.rs:1200` |
| jcode | `jcode memory clear-test` | 清理测试记忆存储（调试会话用） | `src/cli/args.rs:1203` |

### B5 技能

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/skillful` | 切换系统提示中列出可用技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:602` |
| omp | `/skills` | 从 skills.omp.sh 搜索/安装/更新技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:66` |
| omp | `/skillful on` | 本会话在提示中列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:608` |
| omp | `/skillful off` | 本会话不列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:609` |
| omp | `/skillful status` | 显示技能列举状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:610` |
| omp | `/skills search` | 搜索技能注册表 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:70` |
| omp | `/skills install` | 安装注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:71` |
| omp | `/skills installed` | 列出已安装的注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:72` |
| omp | `/skills update` | 在声明范围内更新注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:74（4-tab 多行项）` |
| omp | `omp skill`（别名 `skills`） | Skillshare 技能安装/搜索/发布 | `packages/coding-agent/src/cli-commands.ts:225` |
| jcode | `/skills` | 显示已加载 skills 与推荐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:154` |

## C 对话进行时（控制当前这一轮）

### C1 打断 · 取消 · 暂停 · 继续

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/pause` | 冻结所有 agent 直到恢复 | `packages/coding-agent/src/slash-commands/builtin-control.ts:77` |
| jcode | `/cancel`（别名 `/stop`） | 取消当前 prompt/操作 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:130` |
| jcode | `/continue`（别名 `/resumeall` `/resume-all`） | 继续每个本会自动恢复的中断会话（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:229` |

### C2 重试 · 修复 · 催促

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/retry` | 重试上次失败的 agent 轮次 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:499` |
| jcode | `/poke` | 催促模型续跑未完成 todo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:135` |
| jcode | `/fix` | 模型无法继续时恢复 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:140` |

### C3 排队 · 后台 · 插入

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/queue` | 排队一条消息到 agent yield 后发送 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:438` |
| omp | `/btw` | 提问侧问题或浏览 BTW 历史 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:451` |

### C4 计划模式（先规划再动手）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/plan` | 切换 plan 模式（先规划后执行） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:323` |
| omp | `/plan-review` | 重新打开最新计划的评审 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:344` |
| omp | `/todo` | 查看或修改 agent 的 todo 列表 | `packages/coding-agent/src/slash-commands/builtin-session.ts:208` |
| omp | `/todo edit` | 在 $EDITOR 打开 todos（Markdown 往返） | `packages/coding-agent/src/slash-commands/builtin-session.ts:214` |
| omp | `/todo copy` | 把 todos 以 Markdown 复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:215` |
| omp | `/todo expand` | 在 HUD 显示全部阶段与任务 | `packages/coding-agent/src/slash-commands/builtin-session.ts:216` |
| omp | `/todo collapse` | 恢复 HUD 的有界预览 | `packages/coding-agent/src/slash-commands/builtin-session.ts:217` |
| omp | `/todo export` | 把 todos 写为 Markdown 文件 | `packages/coding-agent/src/slash-commands/builtin-session.ts:218` |
| omp | `/todo import` | 从 Markdown 文件替换 todos | `packages/coding-agent/src/slash-commands/builtin-session.ts:219` |
| omp | `/todo append` | 追加一条任务（阶段模糊匹配/自动建） | `packages/coding-agent/src/slash-commands/builtin-session.ts:221（4-tab 多行项）` |
| omp | `/todo start` | 把任务标记为 in_progress | `packages/coding-agent/src/slash-commands/builtin-session.ts:225` |
| omp | `/todo done` | 把任务/阶段/全部标记完成 | `packages/coding-agent/src/slash-commands/builtin-session.ts:226` |
| omp | `/todo drop` | 把任务/阶段/全部标记放弃 | `packages/coding-agent/src/slash-commands/builtin-session.ts:227` |
| omp | `/todo rm` | 移除任务/阶段/全部 | `packages/coding-agent/src/slash-commands/builtin-session.ts:228` |
| jcode | `/plan` | 生成仅计划的 plan 卡 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:136` |

## D 工具与权限

### D1 工具开关

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/force`（别名 `force:`） | 强制下一轮使用指定工具 | `packages/coding-agent/src/slash-commands/builtin-control.ts:9` |
| omp | `/tools` | 显示 agent 当前可见工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:505` |

### D2 审批 · 沙箱 · 安全检查

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/security` | 规划/运行/查看/导入/比对原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:275` |
| omp | `/security plan` | 创建一次不可变的安全扫描计划 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:281` |
| omp | `/security scan` | 开始计划内或新建的原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:282` |
| omp | `/security status` | 显示原生扫描任务状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:283` |
| omp | `/security cancel` | 取消运行中的原生扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:284` |
| omp | `/security scans` | 列出项目已存的安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:285` |
| omp | `/security show` | 渲染某次扫描或 security:// 资源 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:286` |
| omp | `/security import` | 导入 SARIF 或 Codex 安全包 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:287` |
| omp | `/security export` | 导出规范包 / SARIF / 报告 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:288` |
| omp | `/security validate` | 用原生工具校验单条 finding | `packages/coding-agent/src/slash-commands/builtin-modes.ts:289` |
| omp | `/security compare` | 比较两次扫描的 finding 血缘 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:290` |
| omp | `/security disposition` | 为 finding 设置处置与理由 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:291` |
| jcode | `jcode permissions` | 处理待定的 ambient 权限请求 | `src/cli/args.rs:363` |
| jcode | `/permissions` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:31` |
| jcode | `/permission` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:32` |

### D3 MCP server

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/mcp` | 管理 MCP 服务器（add/list/remove/test 等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:696` |
| omp | `/mcp add` | 新增一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:703（4-tab 多行项）` |
| omp | `/mcp list` | 列出全部已配置 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:707` |
| omp | `/mcp remove` | 移除一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:708` |
| omp | `/mcp test` | 测试到某 server 的连接 | `packages/coding-agent/src/slash-commands/builtin-session.ts:709` |
| omp | `/mcp reauth` | 为某 server 重新授权 OAuth | `packages/coding-agent/src/slash-commands/builtin-session.ts:710` |
| omp | `/mcp unauth` | 移除某 server 的 OAuth 授权 | `packages/coding-agent/src/slash-commands/builtin-session.ts:711` |
| omp | `/mcp enable` | 启用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:712` |
| omp | `/mcp disable` | 停用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:713` |
| omp | `/mcp smithery-search` | 搜索 Smithery 并部署一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:715（4-tab 多行项）` |
| omp | `/mcp smithery-login` | 登录 Smithery 并缓存 API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:719` |
| omp | `/mcp smithery-logout` | 移除已缓存的 Smithery API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:720` |
| omp | `/mcp reconnect` | 重连到指定 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:721` |
| omp | `/mcp reload` | 强制重载 MCP 运行时工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:722` |
| omp | `/mcp resources` | 列出已连 server 的可用资源 | `packages/coding-agent/src/slash-commands/builtin-session.ts:723` |
| omp | `/mcp prompts` | 列出已连 server 的 prompts | `packages/coding-agent/src/slash-commands/builtin-session.ts:724` |
| omp | `/mcp notifications` | 显示通知能力与订阅状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:725` |
| omp | `/mcp help` | 显示 /mcp 帮助 | `packages/coding-agent/src/slash-commands/builtin-session.ts:726` |

### D4 远端机器（ssh / 远端会话）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/ssh` | 管理 SSH 主机（add/list/remove） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:153` |
| omp | `/ssh add` | 新增一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:160（4-tab 多行项）` |
| omp | `/ssh list` | 列出全部已配置 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:164` |
| omp | `/ssh remove` | 移除一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:165` |
| omp | `/ssh help` | 显示 /ssh 帮助 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:166` |
| omp | `omp ssh` | 管理 SSH 主机配置 | `packages/coding-agent/src/cli-commands.ts:231` |
| jcode | `/ssh` | 用系统 SSH 连接远程机器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:63` |
| jcode | `/exit` | 仅 SSH 登录取消语境，未登记 [归类存疑] | `crates/jcode-tui/src/tui/app/auth_remote.rs:447` |

### D5 别的"手"（浏览器 · 计算机 · 图 · 搜索 …）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/computer` | 切换本会话计算机使用 eval 前奏 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:685` |
| omp | `/browser` | 切换浏览器 eval 前奏无头/可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:475` |
| omp | `/open` | 用浏览器打开会话中最后的链接 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:597` |
| omp | `/live` | 启动 Codex 实时语音模式 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-control.ts:59` |
| omp | `/computer on` | 本会话启用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:691` |
| omp | `/computer off` | 本会话停用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:692` |
| omp | `/computer status` | 显示 computer use 状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:693` |
| omp | `/browser headless` | 切换到无头模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:480` |
| omp | `/browser visible` | 切换到可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:481` |
| omp | `omp browser-relay` | 本地 CDP relay 驱动自有 Chrome [归类存疑] | `packages/coding-agent/src/cli-commands.ts:61` |
| omp | `omp find` | 语义搜索行为到文件/行范围 | `packages/coding-agent/src/cli-commands.ts:108` |
| omp | `omp images`（别名 `img`） | 图片发布后端检查/诊断/清理 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:138` |
| omp | `omp say` | 本地 TTS 合成并播放 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:185` |
| omp | `omp search`（别名 `q` `web-search`） | 测试 web 搜索 provider | `packages/coding-agent/src/cli-commands.ts:282` |
| jcode | `/voice` | 语音输入：说，然后发送（Ctrl+Space） [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:141` |
| jcode | `/dictate`（别名 `/dictation`） | 运行配置的外部听写命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:142` |
| jcode | `jcode dictate` | 运行配置的听写（--type 直接键入） | `src/cli/args.rs:377` |
| jcode | `jcode browser <action> [browser]` | 浏览器自动化 setup/status/detect | `src/cli/args.rs:407` |
| jcode | `/open` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:59` |
| jcode | `/file` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:60` |
| jcode | `/new-terminal` | 阻断表出现；wire-backed，无本地 handler[未核实] [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:62` |

## E 代码与仓库

### E1 git · 分支 · worktree

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/git` | 打开 git UI（diff/暂存/提交） | `packages/coding-agent/src/slash-commands/builtin-session.ts:572` |
| omp | `/wt`（别名 `worktree`） | 把会话移入新 worktree（含改动） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:740` |
| omp | `omp git` | 全屏 git UI | `packages/coding-agent/src/cli-commands.ts:128` |
| omp | `omp worktree`（别名 `wt`） | 增/列/清 git worktree | `packages/coding-agent/src/cli-commands.ts:276` |
| jcode | `/git` | 显示会话工作目录的 git 状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:64` |

### E2 提交 · 推送 · 合入

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp commit` | 生成提交信息并更新 changelog | `packages/coding-agent/src/cli-commands.ts:78` |
| jcode | `/commit` | 从当前改动生成逻辑提交 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:69` |
| jcode | `/merge` | 合入 main/master 并切过去（不推送） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:70` |
| jcode | `/commit-push`（别名 `/commit-and-push`） | 逻辑提交后推送 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:74` |

### E3 评审 · 测试 · 重构 · 改进

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/review` | 启动一次性 review 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:106` |
| jcode | `/judge` | 启动一次性 judge 会话 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:107` |
| jcode | `/refactor` | 运行安全重构循环 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:138` |
| jcode | `/test` | 用分层测试验证论断/当前改动 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:145` |

### E4 issue · 分诊

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/triage` | 分诊新 GitHub issue 并自主修复安全的 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:98` |

## F 自主与自动化

### F1 目标 · 循环 · 棘轮 · 过夜

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/goal` | 切换 goal 模式（持久自主目标） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:373` |
| omp | `/guided-goal` | 让 agent 访谈你后设置 goal 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:399` |
| omp | `/loop` | 切换 loop 模式（每次 yield 重发提示） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:411` |
| omp | `/ratchet` | 为 LLM 流程建/复用 eval 并无人值守爬山 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:730` |
| omp | `/goal set` | 设置或替换当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:377` |
| omp | `/goal show` | 显示当前目标详情 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:378` |
| omp | `/goal pause` | 暂停当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:379` |
| omp | `/goal resume` | 恢复已暂停的目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:380` |
| omp | `/goal drop` | 丢弃当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:381` |
| omp | `/goal budget` | 调整目标的 token 预算 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:382` |
| jcode | `/initiatives`（别名 `/goals`） | 打开 initiative 总览/续跑 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:146` |
| jcode | `/overnight` | 运行受监督的 overnight 协调器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:152` |
| jcode | `jcode ambient <action>` | ambient 模式管理 | `src/cli/args.rs:341` |
| jcode | `jcode ambient status` | 显示 ambient 模式状态 | `src/cli/args.rs:838` |
| jcode | `jcode ambient log` | 显示近期 ambient 活动日志 | `src/cli/args.rs:840` |
| jcode | `jcode ambient trigger` | 手动触发一轮 ambient 周期 | `src/cli/args.rs:842` |
| jcode | `jcode ambient stop` | 停止 ambient 模式 | `src/cli/args.rs:844` |
| jcode | `jcode ambient run-visible` | 内部：在可见 TUI 中跑一轮 ambient（隐藏） | `src/cli/args.rs:847` |
| jcode | `/mission` | disabled 占位（与已登记项不同） [归类存疑] | `crates/jcode-tui/src/tui/app/commands.rs:2669` |
| jcode | `/goal` | disabled 占位，与 /goals 不同 [归类存疑] | `crates/jcode-tui/src/tui/app/commands.rs:2670` |
| jcode | `/ambient` | 仅文档；TUI 无此斜杠命令，只有 CLI `jcode ambient` [归类存疑] | `docs/AMBIENT_MODE.md:606` |

### F2 子 agent · swarm · 委派

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/tan` | 在切向工作上跑后台 agent | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:463` |
| omp | `/cleanse` | 用加权并行子 agent 检测修复诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:487` |
| omp | `/hub` | 打开实时 Agent Hub [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:583` |
| omp | `omp agents` | 管理内置任务 agent | `packages/coding-agent/src/cli-commands.ts:51` |
| omp | `omp cleanse` | 并行子 agent 检测修复诊断 | `packages/coding-agent/src/cli-commands.ts:66` |
| jcode | `/swarm-prompt` | 在编辑器打开 swarm 路由提示词 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:52` |
| jcode | `/subagent` | 手动启动 subagent | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:56` |
| jcode | `/swarm` | 切换 swarm 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:151` |

### F3 自动评审 · 自动裁判

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/advisor` | 切换 advisor（第二个模型每轮评审并注入笔记） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:62` |
| omp | `/advisor on` | 启用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:68` |
| omp | `/advisor off` | 停用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:69` |
| omp | `/advisor status` | 显示 advisor 状态 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:70` |
| omp | `/advisor dump` | 把 advisor 记录复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:71` |
| omp | `/advisor configure` | 打开 advisor 配置编辑器（TUI） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:72` |
| jcode | `/autoreview` | 显示/切换回合末自动 review | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:104` |
| jcode | `/autojudge` | 显示/切换回合末自动 judge | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:105` |

### F4 自我改进 / 自开发

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/omfg` | 从抱怨生成 TTSR 规则 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:475` |
| jcode | `/improve` | 自主改进仓库 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:137` |
| jcode | `/selfdev` | 打开新的 self-dev 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:195` |
| jcode | `jcode self-dev`（别名 `selfdev`） | self-development canary 会话（--build） | `src/cli/args.rs:294` |

## G 界面与外观

### G1 主题 · 颜色 · 符号 · 对齐

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/settings` | 打开设置菜单 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-modes.ts:296` |
| jcode | `/colors`（别名 `/color`） | 列出/配置/评分所有 TUI 颜色 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:65` |
| jcode | `/alignment` | 显示/修改默认文本对齐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:111` |
| jcode | `/theme` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:45` |

### G2 状态条 · 事实行 · 布局

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/splitview`（别名 `/split-view`） | 侧栏镜像当前聊天 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:60` |
| jcode | `/btw` | 在侧栏问一个旁路问题 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:62` |
| jcode | `jcode menubar`（别名 `menu-bar` `statusbar`） | macOS 菜单栏实时指示器（--once/--json） | `src/cli/args.rs:563` |

### G3 键位 · 终端设置 · 按键冲突

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/terminal-setup` | 修复 Shift+Enter 换行 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:68` |
| jcode | `jcode setup-hotkey` | 配置平台全局热键启动 jcode（隐藏参数/--uninstall） | `src/cli/args.rs:384` |

### G4 显示开关（思考 / 工具详情 / 通知 / diff / 图片 / 滚动条）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/compact-notifications` | 单行 swarm/文件活动通知显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:112` |
| jcode | `/show-agentgrep-output` | 聊天内全文 agentgrep 输出显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:116` |
| jcode | `/tool-call-details` | 工具行 dimmed 技术细节显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:120` |
| jcode | `/thinking-display`（别名 `/thinking` `/reasoning`） | 模型思维文本显隐（off/full/current） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:124` |
| jcode | `/diff` | 循环/设置 diff 显示模式（off/inline/full/file） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:180` |

## H 协作与分享

### H1 多端 · 远端接入 · 云 · 回本机

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/join` | 加入共享的 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:418` |
| omp | `/leave` | 离开 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:450` |
| omp | `omp join` | 加入共享 collab 会话（同 `/join`） | `packages/coding-agent/src/cli-commands.ts:154` |
| jcode | `/remote` | 从另一台机器接入本会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:87` |
| jcode | `/cloud` | 把本会话迁到云主机继续 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:210` |
| jcode | `/local` | 把云会话接回本机 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:214` |
| jcode | `jcode pair` | 生成 iOS/web 配对码（--list/--revoke） | `src/cli/args.rs:349` |
| jcode | `jcode cloud <action>` | Jcode Cloud/Jade 集成 | `src/cli/args.rs:345` |
| jcode | `jcode cloud sessions <action>` | 上传/列出/校验/查看云端同步会话 | `src/cli/args.rs:701` |
| jcode | `jcode cloud move` | 把活动会话迁到云主机继续 | `src/cli/args.rs:707` |
| jcode | `jcode cloud return` | 把迁出的会话拉回本地并三方合并 git | `src/cli/args.rs:730` |
| jcode | `jcode cloud where` | 显示迁出会话所在与仓库分叉 | `src/cli/args.rs:746` |
| jcode | `jcode cloud attach` | 把本终端接到云主机上的会话（--session） | `src/cli/args.rs:754` |
| jcode | `jcode cloud receive` | 内部：cloud move 远端侧，读 stdin tar（隐藏） | `src/cli/args.rs:760` |
| jcode | `jcode cloud activate` | 内部：cloud move 提交阶段远端侧（隐藏） | `src/cli/args.rs:767` |
| jcode | `jcode cloud export` | 内部：cloud return 远端侧，写 stdout tar（隐藏） | `src/cli/args.rs:776` |
| jcode | `jcode cloud sessions configure` | 配置本机 Jade API 默认值 | `src/cli/args.rs:805` |
| jcode | `jcode cloud sessions status` | 显示已保存 Jade 默认值且不泄露密钥 | `src/cli/args.rs:834` |
| jcode | `jcode cloud sessions upload <session_file>` | 上传指定本地会话 JSON 到 Jade | `src/cli/args.rs:843` |
| jcode | `jcode cloud sessions upload-latest` | 上传最新本地会话 | `src/cli/args.rs:854` |
| jcode | `jcode cloud sessions sync` | 增量同步本地会话到 Jade | `src/cli/args.rs:869` |
| jcode | `jcode cloud sessions list` | 列出云端已上传会话 | `src/cli/args.rs:911` |
| jcode | `jcode cloud sessions verify <session_id>` | 校验云元数据与 S3 blob 均存在 | `src/cli/args.rs:925` |
| jcode | `jcode cloud sessions dashboard` | 渲染云端会话 HTML 面板 | `src/cli/args.rs:933` |
| jcode | `jcode cloud sessions view <session_id>` | 下载并查看云端会话 | `src/cli/args.rs:957` |

### H2 分享 · 录屏 · 广播

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/share` | 通过加密链接分享会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:263` |
| omp | `/collab` | 通过 relay 直播分享本会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:289` |
| omp | `/collab view` | 分享只读链接（访客可看不可提问） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:294` |
| omp | `/collab list` | 列出本机活跃 Collab host | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:295` |
| omp | `/collab status` | 显示链接与参与者 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:296` |
| omp | `/collab stop` | 停止分享 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:297` |
| omp | `omp collab` | 列出本地 Collab 主机/取链接 | `packages/coding-agent/src/cli-commands.ts:71` |
| omp | `omp clip` | 上传 `/record` 录屏为公开 clip | `packages/coding-agent/src/cli-commands.ts:190` |
| omp | `omp share` | 分享已保存会话（同 `/share`） | `packages/coding-agent/src/cli-commands.ts:200` |
| omp | `omp stream` | 广播本机会话屏到公开频道 | `packages/coding-agent/src/cli-commands.ts:241` |

### H3 workspace（多会话平移）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/move` | 把当前会话移到别的目录 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:710` |
| omp | `/add-dir` | 添加工作区目录（多根） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:775` |
| omp | `/remove-dir` | 移除工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:807` |
| omp | `/dirs` | 列出本会话工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:836` |
| jcode | `/workspace` | Niri 风格会话工作区 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:215` |

## I 账号与计费

### I1 登录 · 登出 · 多账号

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/login` | 用 OAuth provider 登录 | `packages/coding-agent/src/slash-commands/builtin-session.ts:620` |
| omp | `/logout` | 登出 OAuth provider | `packages/coding-agent/src/slash-commands/builtin-session.ts:673` |
| omp | `/setup`（别名 `providers`） | 打开 provider 设置向导 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:305` |
| omp | `/setup providers` | 配置登录与联网搜索 provider | `packages/coding-agent/src/slash-commands/builtin-modes.ts:310` |
| omp | `/session pin` | 把当前 provider 固定到某个 OAuth 账号 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-session.ts:255（4-tab 多行项）` |
| omp | `omp login` | 登录模型 provider（`/login` 终端版） | `packages/coding-agent/src/cli-commands.ts:159` |
| omp | `omp token` | 取某 provider 的 API key/OAuth token | `packages/coding-agent/src/cli-commands.ts:261` |
| omp | `omp auth-broker` | 管理凭据 vault auth-broker | `packages/coding-agent/src/cli-commands.ts:41` |
| omp | `omp dry-balance` | OAuth 账号均衡干跑 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:103` |
| jcode | `/auth` | 显示鉴权状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:217` |
| jcode | `/login` | 登录 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:218` |
| jcode | `/logout` | 登出 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:219` |
| jcode | `/account`（别名 `/accounts`） | 打开合并账户选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:220` |
| jcode | `jcode login [PROVIDER]` | OAuth/API key 登录 provider | `src/cli/args.rs:198` |
| jcode | `jcode account <action>` | 登录并管理 Jcode 账号 | `src/cli/args.rs:265` |
| jcode | `jcode auth <action>` | 认证状态与校验助手 | `src/cli/args.rs:325` |
| jcode | `jcode account login` | 浏览器设备授权并等待套餐激活 | `src/cli/args.rs:609` |
| jcode | `jcode account manage` | 打开 Jcode 账号管理页 | `src/cli/args.rs:627` |
| jcode | `jcode account logout` | 吊销当前 key 并安全清除本地状态 | `src/cli/args.rs:630` |
| jcode | `jcode auth import` | 从受信客户端导入一条 OAuth 登录 | `src/cli/args.rs:844` |
| jcode | `jcode auth status` | 显示模型/工具 provider 的认证状态 | `src/cli/args.rs:853` |
| jcode | `/hosted` | auth 侧实现，未登记 [归类存疑] | `auth_account_commands.rs:78,84` |

### I2 用量 · 配额 · 重置

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/usage` | 显示 provider 用量与限额 (show/reset) | `packages/coding-agent/src/slash-commands/builtin-session.ts:385` |
| omp | `/usage show` | 显示 provider 用量与限额 | `packages/coding-agent/src/slash-commands/builtin-session.ts:391` |
| omp | `/usage reset` | 消耗一次已保存的限流重置 | `packages/coding-agent/src/slash-commands/builtin-session.ts:393（4-tab 多行项）` |
| omp | `omp usage` | 显示各账号 provider 限额 | `packages/coding-agent/src/cli-commands.ts:251` |
| omp | `omp stats` | 查看使用统计 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:236` |
| jcode | `/reset` | 复核并确认 banked OpenAI 用量重置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:161` |
| jcode | `/usage` | 显示已连接 provider 的用量限额 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:162` |
| jcode | `/productivity`（别名 `/wrapped`） | 生成可分享的用量报告+仪表盘图 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:163` |
| jcode | `jcode usage` | 显示已连接 provider 的用量额度（--json） | `src/cli/args.rs:284` |
| jcode | `jcode account status` | 显示 /v1/me 的账号/套餐/用量状态（--json） [归类存疑] | `src/cli/args.rs:616` |
| jcode | `/stats` | productivity.rs:17 处理，未登记 [归类存疑] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:79` |

### I3 订阅 · 计费

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/subscription` | 显示 jcode 订阅状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:171` |
| jcode | `/subscribe` | 为何/如何订阅 jcode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:172` |

## J 扩展与集成

### J1 插件 · 市场

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/marketplace` | 管理市场插件源与已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:45` |
| omp | `/plugins`（别名 `plugin`） | 查看并管理已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:425` |
| omp | `/marketplace add` | 添加一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:51` |
| omp | `/marketplace remove` | 移除一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:52` |
| omp | `/marketplace update` | 更新 marketplace catalog | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:53` |
| omp | `/marketplace list` | 列出已配置的 marketplace | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:54` |
| omp | `/marketplace discover` | 浏览可安装的插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:55` |
| omp | `/marketplace install` | 安装一个插件（无参走交互浏览器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:57（4-tab 多行项）` |
| omp | `/marketplace uninstall` | 卸载一个插件（无参走选择器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:61` |
| omp | `/marketplace installed` | 列出已安装的 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:62` |
| omp | `/marketplace upgrade` | 升级过期插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:63` |
| omp | `/marketplace help` | 显示用法指南 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:64` |
| omp | `/plugins list` | 列出全部已装插件（npm+marketplace） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:432` |
| omp | `/plugins enable` | 启用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:433` |
| omp | `/plugins disable` | 停用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:434` |
| omp | `omp plugin`（别名 `plugins`） | 管理插件 | `packages/coding-agent/src/cli-commands.ts:169` |
| omp | `omp install` | 安装/链接扩展包 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:149` |

### J2 扩展 · hooks · ACP

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/extensions`（别名 `status`） | 打开扩展控制中心面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:553` |
| omp | `omp acp` | 以 ACP 协议 over stdio 运行 | `packages/coding-agent/src/cli-commands.ts:36` |
| jcode | `jcode acp` | 作为 Agent Client Protocol 适配器接入守护进程 | `src/cli/args.rs:164` |

## K 诊断与调试

### K1 日志 · 追踪

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/trace` | 在统计面板打开本会话 trace | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:203` |
| omp | `/dump` | 复制会话记录并写 LLM 请求 JSON [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:230` |
| jcode | `/log` | 在 jcode 日志中标记当前位置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:174` |

### K2 调试面板 · 性能 · 可视化

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/stats` | 启动本地统计面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:432` |
| omp | `/debug` | 打开调试工具选择器 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:534` |
| omp | `omp gallery` | 预览渲染器视觉画廊 | `packages/coding-agent/src/cli-commands.ts:123` |
| omp | `omp render` | 用生产管线渲染会话线程 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:220` |
| jcode | `/debug-visual` | 切换可视化调试覆盖层 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:223` |
| jcode | `jcode debug <command> [arg]` | 调试 socket CLI（--session/--socket/--wait） [归类存疑] | `src/cli/args.rs:302` |
| jcode | `/debug-fixture` | debug.rs:581 处理 gmail-draft，未登记 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:87` |

### K3 遥测 · 隐私

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/telemetry` | 显示/修改 jcode 发送的数据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:169` |
| jcode | `jcode telemetry <action>` | 查看/修改匿名遥测设置 | `src/cli/args.rs:290` |
| jcode | `jcode telemetry status` | 显示当前遥测状态，不创建匿名 ID | `src/cli/args.rs:600` |
| jcode | `jcode telemetry enable` | 启用匿名用量遥测 | `src/cli/args.rs:607` |
| jcode | `jcode telemetry disable` | 持久禁用所有遥测 | `src/cli/args.rs:609` |

### K4 截图 · 录制 · 演示

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/record` | 开始/停止录制本屏到可回放文件 | `packages/coding-agent/src/slash-commands/builtin-control.ts:68` |
| omp | `omp play` | 回放 `/record` 录屏 | `packages/coding-agent/src/cli-commands.ts:195` |
| jcode | `/screenshot-mode` | 切换截图捕获模式 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:224` |
| jcode | `/screenshot` | 捕获一个截图调试状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:225` |
| jcode | `/record` | 录制一段 demo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:226` |
| jcode | `jcode replay <session>` | 在 TUI 重放会话 | `src/cli/args.rs:418` |

### K5 自检（按键冲突 · provider 测试覆盖 · 版本自检）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp grep` | 测试 grep 工具 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:118` |
| omp | `omp ttsr` | 检查/测试 TTSR 规则 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:271` |
| jcode | `/provider-test-coverage`（别名 `/model-status`） | 显示当前 provider/model 的实机测试证据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:45` |
| jcode | `/keys`（别名 `/keybindings`） | 显示与终端/系统的键位冲突（/keys refresh 重扫） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:175` |
| jcode | `jcode provider-test-coverage`（别名 `model-status`） | 显示实机验证覆盖 | `src/cli/args.rs:472` |
| jcode | `jcode provider-doctor`（别名 `provider-strict-e2e`） | 按严格 E2E 关卡诊断 provider/model | `src/cli/args.rs:493` |
| jcode | `jcode auth-test` | 端到端测试认证 [归类存疑] | `src/cli/args.rs:510` |
| jcode | `jcode auth doctor [PROVIDER]` | 诊断 provider 认证问题（--validate/--json） [归类存疑] | `src/cli/args.rs:859` |

## L 系统与自维护

### L1 更新 · 重启 · 重载

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/restart` | 用相同启动参数重启并恢复会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:850` |
| omp | `/reload-plugins` | 重载所有插件（技能/命令/钩子等） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:557` |
| omp | `/exit` | 退出应用 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:845` |
| omp | `/quit`（别名 `q`） | 退出应用 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-control.ts:86` |
| omp | `omp update` | 检查并安装更新 | `packages/coding-agent/src/cli-commands.ts:246` |
| jcode | `/reload` | 重载到最新可用二进制 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:192` |
| jcode | `/restart` | 用当前二进制重启 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:193` |
| jcode | `/update` | 后台更新并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:196` |
| jcode | `/update-sim` | 安全预览更新 UI（Alt+_） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:197` |
| jcode | `/client-reload` | 强制重载客户端二进制（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:227` |
| jcode | `/server-reload` | 强制重载服务端二进制（remote） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:228` |
| jcode | `/quit` | 退出 jcode [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:216` |
| jcode | `jcode update` | 升级 jcode 到最新版 | `src/cli/args.rs:275` |
| jcode | `jcode restart <action>` | 跨重启保存/恢复打开的 jcode 窗口 | `src/cli/args.rs:557` |
| jcode | `jcode restart save` | 保存当前打开 jcode 窗口的重启快照 | `src/cli/args.rs:1015` |
| jcode | `jcode restart restore` | 恢复最近保存的重启快照 | `src/cli/args.rs:1021` |
| jcode | `jcode restart status` | 显示当前保存的重启快照 | `src/cli/args.rs:1023` |
| jcode | `jcode restart clear` | 删除当前重启快照 | `src/cli/args.rs:1025` |

### L2 自构建 · 发布 · 安装

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| jcode | `/fast-release`（别名 `/cut-release` `/commit-push-release`） | 从 selfdev 缓存立即发布 Linux | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:79` |
| jcode | `/fast-macos-release` | 立即发布已备好的 macOS arm64 构建 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:83` |
| jcode | `/merge-remote-release` | 合入/验证/推送并远程发布 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:88` |
| jcode | `/remote-release` | 立即推送发布 tag，CI 全平台构建发布 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:92` |
| jcode | `/rebuild` | 后台重建并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:194` |

### L3 初始化 · 首启 · 终端接入

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp launch` | 默认入口：交互/打印模式运行 assistant [归类存疑] | `packages/coding-agent/src/cli-commands.ts:29` |
| omp | `omp setup` | 引导设置或安装可选依赖 | `packages/coding-agent/src/cli-commands.ts:205` |
| omp | `omp completions` | 打印 shell 补全脚本 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:83` |
| jcode | `/onboarding-preview` | 预览首启引导屏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:184` |
| jcode | `/onboarding-sim` | 走遍每个首启屏（Alt+5 重置/Cmd+5 切换） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:188` |
| jcode | `jcode setup-launcher` | 安装平台启动器集成 [归类存疑] | `src/cli/args.rs:404` |

## M 帮助与元

### M1 帮助 · 命令表 · 键位表

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/hotkeys` | 显示所有键盘快捷键 | `packages/coding-agent/src/slash-commands/builtin-session.ts:496` |
| jcode | `/help`（别名 `/?` `/commands`） | 显示帮助与键盘快捷键 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:40` |
| jcode | `/hotkeys` | 列出热键及个人使用统计 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:67` |

### M2 版本 · 变更日志

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/changelog` | 显示变更日志条目 | `packages/coding-agent/src/slash-commands/builtin-session.ts:467` |
| omp | `/changelog full` | 显示完整 changelog | `packages/coding-agent/src/slash-commands/builtin-session.ts:473` |
| omp | `/changelog last` | 显示最近 N 个 release（默认 1） | `packages/coding-agent/src/slash-commands/builtin-session.ts:474` |
| jcode | `/version` | 显示当前版本 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:158` |
| jcode | `/changelog` | 显示本构建的近期变更 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:159` |
| jcode | `jcode version` | 显示版本/构建信息（--json） | `src/cli/args.rs:278` |

### M3 反馈 · 支持

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp grievances` | 查看/清理/上报工具问题 | `packages/coding-agent/src/cli-commands.ts:133` |
| jcode | `/feedback` | 发送关于 jcode 的反馈 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:168` |
| jcode | `/support` | 预填诊断信息发邮件给支持 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:170` |

### M4 隐藏 / 彩蛋命令

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp __complete（隐藏）` | 内部补全辅助 | `packages/coding-agent/src/cli-commands.ts:88` |
| jcode | `/z`（别名 `/zz` `/zzz`） | 秘密 premium 模式命令（hidden） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:235` |
| jcode | `/zstatus` | 秘密 premium 模式状态命令（hidden） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:238` |

## N 特殊输入前缀

### N 特殊输入前缀（同一层的另一种输入，不是命令）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/ ! !! $ $$ @ ^ : # -> =>` | 行首特殊输入前缀：slash/bash/python/提及/emoji/PR/yield 队列各一层 | `packages/coding-agent/src/modes/controllers/input-controller.ts:1138-1153` |

## O 进程与服务（CLI 为主）

### O1 服务端 · 连接 · 桥接

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp auth-gateway` | 运行基于 broker 的转发代理 | `packages/coding-agent/src/cli-commands.ts:46` |
| jcode | `jcode serve` | 启动 agent 后台守护进程（可选 --server-name） | `src/cli/args.rs:148` |
| jcode | `jcode server <action>` | 管理后台守护进程 | `src/cli/args.rs:174` |
| jcode | `jcode connect` | 连接已在运行的 server | `src/cli/args.rs:181` |
| jcode | `jcode run <message>` | 发一条消息后退出（--json/--ndjson） | `src/cli/args.rs:184` |
| jcode | `jcode api-bridge`（别名 `api`） | 在 Unix socket 上提供 SDK 稳定 API | `src/cli/args.rs:581` |
| jcode | `jcode server stdio` | 内部：ssh attach 的原生客户端协议桥（隐藏） | `src/cli/args.rs:638` |
| jcode | `jcode server start` | 若未运行则启动后台 server（--json） | `src/cli/args.rs:641` |
| jcode | `jcode server keepalive` | 内部：保持轻量连接到 stdin 关闭（隐藏） | `src/cli/args.rs:649` |
| jcode | `jcode server promote [version]` | 把共享 server 通道钉到某个已安装版本（--json） | `src/cli/args.rs:652` |
| jcode | `jcode server reload` | 优雅地把运行中的 server 重载到最新二进制 | `src/cli/args.rs:665` |

### O2 后台/持久进程的查看与清理

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `/jobs` | 显示异步后台任务状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:324` |
| omp | `/jobs full` | 显示完整未截断的命令行 | `packages/coding-agent/src/slash-commands/builtin-session.ts:329` |
| omp | `omp ps` | 列管守护进程后台进程 | `packages/coding-agent/src/cli-commands.ts:180` |
| jcode | `jcode server stop` | 停止后台 server 并清理 socket（--force/--json） | `src/cli/args.rs:681` |

## P 基准与实验（CLI 为主）

### P 基准与实验（CLI 为主）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp bench` | 模型 TTFT/吞吐基准 | `packages/coding-agent/src/cli-commands.ts:56` |
| omp | `omp if-bench` | 指令遵循与工作记忆基准 | `packages/coding-agent/src/cli-commands.ts:144` |
| omp | `omp predict` | 对比各补全引擎 ghost text [归类存疑] | `packages/coding-agent/src/cli-commands.ts:175` |

## Q 其它内部工具（CLI 为主，兜底）

### Q 其它内部工具（CLI 为主，兜底）

| 家 | 命令 | 一句话 | 出处 |
|---|---|---|---|
| omp | `omp config` | 管理配置项 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:98` |
| omp | `omp gc` | 存储垃圾回收 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:113` |
| omp | `omp shell` | 交互式 shell 控制台 | `packages/coding-agent/src/cli-commands.ts:210` |
| omp | `omp read` | 预览 read 工具结果 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:215` |
| omp | `omp toks` | 用各离线分词器计数 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:266` |
| jcode | `/config` | 显示或编辑配置 [归类存疑] | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:173` |
| jcode | `jcode repl` | 无 TUI 的简单 REPL 模式 [归类存疑] | `src/cli/args.rs:272` |


## 附. 口径与边角

### 别名折叠规则与折掉的别名清单

- 规则：只有源里明确写 “Alias for X” / 「别名」的条目才折进父命令那一行；语义不同的一律不折（例：jcode `/clear`（清历史）与 `/cls`（只清视图、保留上下文）各自成行）。
- omp 源里已是折叠写法（别名写进父行同一格），本表沿用。omp 折进父行的别名：
- `/branch` ← `rewind`
- `/model` ← `models`
- `omp skill` ← `skills`
- `/force` ← `force:`
- `omp images` ← `img`
- `omp search` ← `q`、`web-search`
- `/wt` ← `worktree`
- `omp worktree` ← `wt`
- `/setup` ← `providers`
- `/plugins` ← `plugin`
- `omp plugin` ← `plugins`
- `/extensions` ← `status`
- `/quit` ← `q`
- jcode 折掉 26 个真别名（父 ← 别名）：
- `/help` ← `/?`、`/commands`
- `/model` ← `/models`
- `/provider-test-coverage` ← `/model-status`
- `/todos` ← `/todo`
- `/splitview` ← `/split-view`
- `/colors` ← `/color`
- `/commit-push` ← `/commit-and-push`
- `/fast-release` ← `/cut-release`、`/commit-push-release`
- `/thinking-display` ← `/thinking`、`/reasoning`
- `/cls` ← `/clear-view`
- `/dictate` ← `/dictation`
- `/initiatives` ← `/goals`
- `/productivity` ← `/wrapped`
- `/keys` ← `/keybindings`
- `/resume` ← `/sessions`、`/session`
- `/fork` ← `/split`
- `/account` ← `/accounts`
- `/continue` ← `/resumeall`、`/resume-all`
- `/cancel` ← `/stop`
- `/z` ← `/zz`、`/zzz`
- jcode CLI 子命令的自带别名（源里已写成同一行，计 1 行）：
- `jcode self-dev` ← `selfdev`
- `jcode menubar` ← `menu-bar`、`statusbar`
- `jcode provider-test-coverage` ← `model-status`
- `jcode provider-doctor` ← `provider-strict-e2e`
- `jcode api-bridge` ← `api`
- **边角 / 对不上的一处**：omp 片段里 `/memory reset`（`/memory clear` 的别名）、`/memory rebuild`（`/memory enqueue` 的别名）在源里明确标了「别名」。按折叠规则应再折 2 行（omp → 261）；但任务给定的 omp 口径是「已是折叠写法、263 行」，且该 263 恰等于片段 264 行减去 N 前缀行（见下）。本表按任务口径保留这两条为独立子命令行，特此标注供裁定。

### `[归类存疑]` 汇总（名字 + 放哪了 + 为何存疑）

存疑原因：该条不完全贴叶 / 归类时语义跨叶（每行的一句话原文见正文对应行）。共 57 条。
- `/tree`（omp，A1）
- `/copy`（omp，A4）
- `/session`（omp，A5）
- `/observe`（jcode，A5）
- `jcode transcript [text]`（jcode，A5）
- `/fresh`（omp，B1）
- `/vibe`（omp，B2）
- `/prewalk`（omp，B2）
- `omp compress`（omp，B3）
- `/cache`（jcode，B3）
- `/btw`（omp，C3）
- `/exit`（jcode，D4）
- `/open`（omp，D5）
- `/live`（omp，D5）
- `omp browser-relay`（omp，D5）
- `omp images`（omp，D5）
- `omp say`（omp，D5）
- `/voice`（jcode，D5）
- `/open`（jcode，D5）
- `/file`（jcode，D5）
- `/new-terminal`（jcode，D5）
- `/judge`（jcode，E3）
- `/mission`（jcode，F1）
- `/goal`（jcode，F1）
- `/ambient`（jcode，F1）
- `/hub`（omp，F2）
- `/settings`（omp，G1）
- `/btw`（jcode，G2）
- `/move`（omp，H3）
- `/session pin`（omp，I1）
- `omp dry-balance`（omp，I1）
- `/hosted`（jcode，I1）
- `omp stats`（omp，I2）
- `jcode account status`（jcode，I2）
- `/stats`（jcode，I2）
- `omp install`（omp，J1）
- `/dump`（omp，K1）
- `omp render`（omp，K2）
- `jcode debug <command> [arg]`（jcode，K2）
- `omp grep`（omp，K5）
- `omp ttsr`（omp，K5）
- `jcode auth-test`（jcode，K5）
- `jcode auth doctor [PROVIDER]`（jcode，K5）
- `/exit`（omp，L1）
- `/quit`（omp，L1）
- `/quit`（jcode，L1）
- `/merge-remote-release`（jcode，L2）
- `omp launch`（omp，L3）
- `omp completions`（omp，L3）
- `jcode setup-launcher`（jcode，L3）
- `omp predict`（omp，P）
- `omp config`（omp，Q）
- `omp gc`（omp，Q）
- `omp read`（omp，Q）
- `omp toks`（omp，Q）
- `/config`（jcode，Q）
- `jcode repl`（jcode，Q）

### `[未核实]` 条目（源里标「未核实」，原样保留）

- `/permissions`（jcode，D2）
- `/permission`（jcode，D2）
- `/open`（jcode，D5）
- `/file`（jcode，D5）
- `/new-terminal`（jcode，D5）
- `/theme`（jcode，G1）

### 没算进命令的东西

- 参数补全项、控制器 verb、flag/全局标志、设置项、handler/分派链、键位、面板与选择器内部键、鼠标路由、状态条字段、vim/编辑器动作。
- omp：§9–§11 文件型 markdown 命令与 prompt 模板、§12 控制器 verb、§13 可用性门控、§14–§19 键位与状态条、§20–§23 面板/选择器、§24–§27 模式与可配置项、§30–§32 launch/全局 flag、§34 参数补全、§36 动态命令来源、§38 各子命令自有 flag、§39–§40 设置项、§41 面板内部键、§42 vim、§43–§44 首启/源码目录、§45 鼠标。
- jcode：§2 处理函数、§3 共享分派链、§4 SSH 阻断清单、§5 解析规则、§8 CLI 全局标志、§10–§11 键位、§12–§19 面板/选择器/状态条/漂移、§20 CLI 自有 flag、§21 参数白名单、§22–§27 远端键位/动画/鼠标、§28 设置项与环境变量、§附 缺口。
- 输入前缀：omp 的 `/` `!` `!!` `$` `$$` `@` `^` `:` `#` `->` `=>` 是“另一层输入”，不是命令，只归 N 一行，**未计入 §0 合计**。
- 跨接口同义命令按两条算（例：omp `/join` 与 `omp join`、`/share` 与 `omp share`；jcode `/remote` 与 CLI、`/dictate` 与 `jcode dictate`）——两个不同入口，不折叠。

### 两家都没有落进的叶

- G5 动画 · 滚动 · 视觉特效（两者均无独立命令；相关只散在键位/设置里）
- J3 用户自建命令（文件型命令 / prompt 模板 / 自定义 TS）（omp 有机制但非“命令”行，jcode 无）

### 对不上的地方

- 行数：omp **263**、jcode **209**、合计 **472**，与任务给定一致。
- 唯一口径分歧见上「别名折叠」边角：若严格折叠 omp 的两条 memory 子命令别名，omp 为 261、合计 470。除此之外无对不上。
