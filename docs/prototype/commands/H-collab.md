# 命令 · H 协作与分享

> **这一块是什么**：别的人在别的屏幕上跟进来：多端与云、回到本机、分享与录屏、workspace 平移。
> **用户什么时候来**：用户想让「不止我一个人在这棵树上」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §H 的分册，**同一条不多不少**（这一块 omp 17 条 · jcode 23 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| H1 | 多端 · 远端接入 · 云 · 回本机 | 3 | 22 | 25 |
| H2 | 分享 · 录屏 · 广播 | 10 | 0 | 10 |
| H3 | workspace（多会话平移） | 4 | 1 | 5 |
| **合计** | | **17** | **23** | **40** |

## 两家的命令（先例原样）

### H1 多端 · 远端接入 · 云 · 回本机

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/join` | 加入共享的 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:418` |
| omp | TUI | `/leave` | 离开 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:450` |
| omp | CLI | `omp join` | 加入共享 collab 会话（同 `/join`） | `packages/coding-agent/src/cli-commands.ts:154` |
| jcode | TUI | `/remote` | 从另一台机器接入本会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:87` |
| jcode | TUI | `/cloud` | 把本会话迁到云主机继续 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:210` |
| jcode | TUI | `/local` | 把云会话接回本机 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:214` |
| jcode | CLI | `jcode pair` | 生成 iOS/web 配对码（--list/--revoke） | `src/cli/args.rs:349` |
| jcode | CLI | `jcode cloud <action>` | Jcode Cloud/Jade 集成 | `src/cli/args.rs:345` |
| jcode | CLI | `jcode cloud sessions <action>` | 上传/列出/校验/查看云端同步会话 | `src/cli/args.rs:701` |
| jcode | CLI | `jcode cloud move` | 把活动会话迁到云主机继续 | `src/cli/args.rs:707` |
| jcode | CLI | `jcode cloud return` | 把迁出的会话拉回本地并三方合并 git | `src/cli/args.rs:730` |
| jcode | CLI | `jcode cloud where` | 显示迁出会话所在与仓库分叉 | `src/cli/args.rs:746` |
| jcode | CLI | `jcode cloud attach` | 把本终端接到云主机上的会话（--session） | `src/cli/args.rs:754` |
| jcode | CLI | `jcode cloud receive` | 内部：cloud move 远端侧，读 stdin tar（隐藏） | `src/cli/args.rs:760` |
| jcode | CLI | `jcode cloud activate` | 内部：cloud move 提交阶段远端侧（隐藏） | `src/cli/args.rs:767` |
| jcode | CLI | `jcode cloud export` | 内部：cloud return 远端侧，写 stdout tar（隐藏） | `src/cli/args.rs:776` |
| jcode | CLI | `jcode cloud sessions configure` | 配置本机 Jade API 默认值 | `src/cli/args.rs:805` |
| jcode | CLI | `jcode cloud sessions status` | 显示已保存 Jade 默认值且不泄露密钥 | `src/cli/args.rs:834` |
| jcode | CLI | `jcode cloud sessions upload <session_file>` | 上传指定本地会话 JSON 到 Jade | `src/cli/args.rs:843` |
| jcode | CLI | `jcode cloud sessions upload-latest` | 上传最新本地会话 | `src/cli/args.rs:854` |
| jcode | CLI | `jcode cloud sessions sync` | 增量同步本地会话到 Jade | `src/cli/args.rs:869` |
| jcode | CLI | `jcode cloud sessions list` | 列出云端已上传会话 | `src/cli/args.rs:911` |
| jcode | CLI | `jcode cloud sessions verify <session_id>` | 校验云元数据与 S3 blob 均存在 | `src/cli/args.rs:925` |
| jcode | CLI | `jcode cloud sessions dashboard` | 渲染云端会话 HTML 面板 | `src/cli/args.rs:933` |
| jcode | CLI | `jcode cloud sessions view <session_id>` | 下载并查看云端会话 | `src/cli/args.rs:957` |

### H2 分享 · 录屏 · 广播

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/share` | 通过加密链接分享会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:263` |
| omp | TUI | `/collab` | 通过 relay 直播分享本会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:289` |
| omp | TUI | `/collab view` | 分享只读链接（访客可看不可提问） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:294` |
| omp | TUI | `/collab list` | 列出本机活跃 Collab host | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:295` |
| omp | TUI | `/collab status` | 显示链接与参与者 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:296` |
| omp | TUI | `/collab stop` | 停止分享 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:297` |
| omp | CLI | `omp collab` | 列出本地 Collab 主机/取链接 | `packages/coding-agent/src/cli-commands.ts:71` |
| omp | CLI | `omp clip` | 上传 `/record` 录屏为公开 clip | `packages/coding-agent/src/cli-commands.ts:190` |
| omp | CLI | `omp share` | 分享已保存会话（同 `/share`） | `packages/coding-agent/src/cli-commands.ts:200` |
| omp | CLI | `omp stream` | 广播本机会话屏到公开频道 | `packages/coding-agent/src/cli-commands.ts:241` |

### H3 workspace（多会话平移）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/move` | 把当前会话移到别的目录 [归类存疑] | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:710` |
| omp | TUI | `/add-dir` | 添加工作区目录（多根） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:775` |
| omp | TUI | `/remove-dir` | 移除工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:807` |
| omp | TUI | `/dirs` | 列出本会话工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:836` |
| jcode | TUI | `/workspace` | Niri 风格会话工作区 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:215` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 1 条**（该条不完全贴叶，正文对应行末尾已标）：`/move`（omp，H3）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
