# 先例原样 · jcode（无损清单）

> 这一份是**证据**，不是需求：把 jcode 在 TUI 里用户能碰到的功能逐条列全，一行一条（≤40 字），带出处。
> 用法：我们的原型每加/减一个东西，都先来这里查"有没有先例、它怎么做的、代价是什么"。
> 出处根目录：`/Users/wxlong/MYCode/learn/ai-agent/jcode`。
> 覆盖基线：每组表头的"共 N 条"来自代码里的注册表/枚举；**该组的行数必须等于 N**。

> 数法：斜杠注册表用正则数 `RegisteredCommand::(public|hidden|remote)("...")`（=113/16/4）；SSH 清单数 `ssh_unsupported_command` 的 `matches!` 字面量（=88，另有 2 条前缀特殊规则）；分派链数 `dispatch_single_local_command` 的 `||` 链（=22）；解析规则数 `scan_slash_tokens` 的状态机规则（=10）；CLI 数 `src/cli/args.rs` 的 clap 变体/标志（=35/53/26）；压缩阶梯数 `OVERSCROLL_LADDER` 数组元素（=10）。

## 目录

- §0 覆盖表
- §1 斜杠命令·注册表 —— 共 133 条
- §2 commands.rs 处理函数 —— 共 43 条
- §3 共享本地分派链 —— 共 22 条
- §4 SSH 阻断清单 —— 共 88 条
- §5 斜杠命令解析规则 —— 共 10 条
- §6 CLI 顶层子命令 —— 共 35 条
- §7 CLI 嵌套子命令 —— 共 53 条
- §8 CLI 全局标志 —— 共 26 条
- §9 可触碰但未登记的命令 —— 共 14 条
- §10 键位—可配置（keybindings.*） —— 共 32 条
- §11 键位—内置不可配置 —— 共 43 条
- §12 面板与选择器（overlay / picker / 全屏页） —— 共 14 条
- §13 侧栏页面（side panel pages） —— 共 9 条
- §14 info widget（15 种） —— 共 15 条
- §15 输入带 / 状态带 —— 共 9 条
- §16 状态条字段与压缩阶梯（事实行） —— 共 9 条
- §17 模式与开关 —— 共 19 条
- §18 鼠标与终端交互 —— 共 5 条
- §19 文档与实现的漂移 —— 共 14 条
- §20 CLI 子命令自己的 flag —— 共 208 条
- §21 command_accepts_args 白名单 —— 共 55 条
- §22 远端专属键位与界面 —— 共 85 条
- §23 account picker / login picker 键位表 —— 共 24 条
- §24 侧栏页面 id —— 共 9 条
- §25 两处 [未核实] 的定论 —— 共 2 条
- §26 纯视觉件与动画 —— 共 10 条
- §27 鼠标交互 —— 共 15 条
- §28 设置 · config.toml 与运行时开关 —— 共 478 条
- 附 没查完的 / 已知缺口

## 0. 覆盖表

| 面 | 注册表（文件:行） | 共 N 条 | 本文档行数 | 对不对得上 | 备注 |
|---|---|---|---|---|---|
| 斜杠命令·注册表（public+hidden+remote） | state_ui_input_helpers.rs:39-239 | 133 | 133 | ✅ | — |
| 斜杠命令·可见 public（供 /help 与补全） | state_ui_input_helpers.rs:245-250 | 113 | 113 | ✅ | registered_command_entries() 过滤 hidden |
| commands.rs 处理函数（handle_*） | commands.rs | 43 | 43 | ✅ | 另 4 个 parse_* 辅助未计入 |
| 共享本地分派链 | commands_dispatch.rs:221-244 | 22 | 22 | ✅ | 21 handler + 1 个 SSH 兜底分支 |
| SSH 阻断清单 | commands_dispatch.rs:26-113 | 88 | 88 | ✅ | matches! 字面量 88；另有 !<cmd>、/fast default 两条前缀规则见 §4 注 |
| 斜杠命令解析规则 | slash_command_parser.rs | 10 | 10 | ✅ | — |
| CLI 顶层子命令 | src/cli/args.rs | 35 | 35 | ✅ | — |
| CLI 嵌套子命令 | src/cli/args.rs | 53 | 53 | ✅ | payload 摘要曾报 51，其分解式相加实为 53；代码实计 53 |
| CLI 全局标志 | src/cli/args.rs:34-143 | 26 | 26 | ✅ | Args 26 个标志；其中 24 个 global=true（--onboarding-sim/--update-sim 未标） |
| 键位—可配置（keybindings.*） | lib.rs:1001-1077 | 32 | 32 | ✅ | 33 个 pub 字段=32 键位串+1 策略字段 session_picker_enter；表下另注 |
| 键位默认值表 KEYBINDING_DEFAULTS | keybindings.rs:195-350 | 23 | 23 | ✅ | 权威默认；缺 9 个 toggle 项（默认只在 KeybindingsConfig::default() 的 get() 回退） |
| 键位—内置不可配置 | input.rs / keybind.rs | 43 | 43 | ✅ | payload 组头记 45，因多键组合并成一行、与文件记法不同 |
| 面板与选择器（overlay / picker / 全屏页） | ui_overlays.rs / ui.rs | 14 | 14 | ✅ | payload 组头记 13，多出组件层 usage overlay（payload note 亦称 14） |
| 侧栏页面（side panel pages） | app/{split_view,todos_view,observe,catchup,navigation}.rs | 9 | 9 | ✅ | payload 组头记 8，多出 file diff 视图 |
| info widget（15 种） | info_widget.rs:87-224 | 15 | 15 | ✅ | — |
| 输入带 / 状态带 | ui_input.rs / ui.rs | 9 | 9 | ✅ | payload 组头记 8，多出聊天内联 todo card |
| 状态条字段与压缩阶梯（事实行） | ui_input.rs:1946-2060 / :2016-2027 | 9 | 9 | ✅ | payload 组头记 8，实为 8 字段+阶梯 1 行；阶梯 OVERSCROLL_LADDER 自身 10 步 |
| 模式与开关 | app/input.rs 等 | 19 | 19 | ✅ | payload 组头记 18，多出 theme/emoji/输出样式 一行 |
| 鼠标与终端交互 | navigation.rs 等 | 5 | 5 | ✅ | — |
| 文档与实现的漂移 cross_check | payload §19 | 14 | 14 | ✅ | 三段：10+2+2 行 |
| CLI 子命令自己的 flag | src/cli/args.rs | 208 | 208 | ✅ | 186 flag（顶层 65+嵌套 121）+ 22 位置参数（顶层 11+嵌套 11）；不含 §8 的 26 全局标志；见 §20 |
| command_accepts_args 白名单 | state_ui_input_helpers.rs:1759-1818 | 55 | 55 | ✅ | bool 白名单，不编码 per-command 参数形状；见 §21 |
| 远端专属键位与界面 | remote/key_handling.rs:269-2758 / remote.rs:1956-2130 / server_events.rs | 85 | 85 | ✅ | G1 63+G1b 11+G1c 11；payload 组头记 58/12/11；见 §22 |
| account / login picker 键位 | jcode-tui-account-picker/src/overlay.rs:305-373 / login_picker.rs:227-269 | 24 | 24 | ✅ | 各 12；见 §23 |
| 侧栏页面 id | tool/side_panel.rs:62-80 / goal.rs / generated_image.rs | 9 | 9 | ✅ | 8 固定类+1 开放类（Managed 不可穷举）；见 §24 |
| 纯视觉件与动画 | ui_animations.rs / display.rs / ui.rs | 10 | 10 | ✅ | 见 §26 |
| 鼠标交互 | app/navigation.rs:1368-1762 + overlay 鼠标 | 15 | 15 | ✅ | 见 §27 |
| config.toml 设置项（顶层 25 段 + 叶子 255） | crates/jcode-base/src/config.rs:485-573 等 | 280 | 280 | ✅ | 顶层段 25 + 各段叶子键 255；见 §28 |
| 环境变量覆盖 JCODE_* | crates/jcode-base/src/config/env_overrides.rs | 171 | 171 | ✅ | 170 个 JCODE_* + GOOGLE_CLOUD_PROJECT/_ID；见 §28 |
| /config 分支 | crates/jcode-tui/src/tui/app/commands.rs:3581-3675 | 4 | 4 | ✅ | 无 config get/set；读=display_string()，写=直接改 config.toml；见 §28 |

## 1. 斜杠命令·注册表（共 133 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/help` | 显示帮助与键盘快捷键 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:40` |
| `/?` | 同 /help（别名） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:41` |
| `/commands` | /help 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:42` |
| `/model` | 列出或切换模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:43` |
| `/models` | /model 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:44` |
| `/provider-test-coverage` | 显示当前 provider/model 的实机测试证据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:45` |
| `/model-status`（hidden 别名） | /provider-test-coverage 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:49` |
| `/refresh-model-list` | 刷新 provider 模型目录 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:50` |
| `/agents` | 配置 agent 角色的模型 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:51` |
| `/swarm-prompt` | 在编辑器打开 swarm 路由提示词 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:52` |
| `/subagent` | 手动启动 subagent | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:56` |
| `/observe` | 侧栏显示最新工具上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:57` |
| `/todos` | 在聊天以卡片显示会话 todo 列表 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:58` |
| `/todo`（hidden 别名） | /todos 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:59` |
| `/splitview` | 侧栏镜像当前聊天 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:60` |
| `/split-view` | /splitview 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:61` |
| `/btw` | 在侧栏问一个旁路问题 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:62` |
| `/ssh` | 用系统 SSH 连接远程机器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:63` |
| `/git` | 显示会话工作目录的 git 状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:64` |
| `/colors` | 列出/配置/评分所有 TUI 颜色 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:65` |
| `/color`（hidden 别名） | /colors 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:66` |
| `/hotkeys` | 列出热键及个人使用统计 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:67` |
| `/terminal-setup` | 修复 Shift+Enter 换行 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:68` |
| `/commit` | 从当前改动生成逻辑提交 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:69` |
| `/merge` | 合入 main/master 并切过去（不推送） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:70` |
| `/commit-push` | 逻辑提交后推送 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:74` |
| `/commit-and-push`（hidden 别名） | /commit-push 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:78` |
| `/fast-release` | 从 selfdev 缓存立即发布 Linux | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:79` |
| `/fast-macos-release` | 立即发布已备好的 macOS arm64 构建 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:83` |
| `/remote` | 从另一台机器接入本会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:87` |
| `/merge-remote-release` | 合入/验证/推送并远程发布 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:88` |
| `/remote-release` | 立即推送发布 tag，CI 全平台构建发布 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:92` |
| `/cut-release`（hidden 别名） | /fast-release 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:96` |
| `/commit-push-release`（hidden 别名） | /cut-release 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:97` |
| `/triage` | 分诊新 GitHub issue 并自主修复安全的 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:98` |
| `/transcript` | 打开当前会话 transcript 文件 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:102` |
| `/subagent-model` | 显示/修改子代理模型策略 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:103` |
| `/autoreview` | 显示/切换回合末自动 review | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:104` |
| `/autojudge` | 显示/切换回合末自动 judge | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:105` |
| `/review` | 启动一次性 review 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:106` |
| `/judge` | 启动一次性 judge 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:107` |
| `/effort` | 显示/修改推理力度 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:108` |
| `/fast` | 切换 fast mode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:109` |
| `/transport` | 显示/修改连接传输 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:110` |
| `/alignment` | 显示/修改默认文本对齐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:111` |
| `/compact-notifications` | 单行 swarm/文件活动通知显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:112` |
| `/show-agentgrep-output` | 聊天内全文 agentgrep 输出显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:116` |
| `/tool-call-details` | 工具行 dimmed 技术细节显隐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:120` |
| `/thinking-display` | 模型思维文本显隐（off/full/current） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:124` |
| `/thinking`（hidden 别名） | /thinking-display 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:128` |
| `/reasoning`（hidden 别名） | /thinking-display 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:129` |
| `/cancel` | 取消当前 prompt/操作 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:130` |
| `/clear` | 清空会话历史 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:131` |
| `/cls` | 仅清屏，保留上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:132` |
| `/clear-view`（hidden 别名） | /cls 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:133` |
| `/rewind` | 回退到上一条消息 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:134` |
| `/poke` | 催促模型续跑未完成 todo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:135` |
| `/plan` | 生成仅计划的 plan 卡 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:136` |
| `/improve` | 自主改进仓库 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:137` |
| `/refactor` | 运行安全重构循环 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:138` |
| `/compact` | 压缩上下文 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:139` |
| `/fix` | 模型无法继续时恢复 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:140` |
| `/voice` | 语音输入：说，然后发送（Ctrl+Space） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:141` |
| `/dictate` | 运行配置的外部听写命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:142` |
| `/dictation` | /dictate 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:143` |
| `/memory` | 切换 memory 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:144` |
| `/test` | 用分层测试验证论断/当前改动 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:145` |
| `/initiatives` | 打开 initiative 总览/续跑 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:146` |
| `/goals` | /initiatives 的旧别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:150` |
| `/swarm` | 切换 swarm 功能 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:151` |
| `/overnight` | 运行受监督的 overnight 协调器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:152` |
| `/context` | 显示完整会话上下文快照 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:153` |
| `/skills` | 显示已加载 skills 与推荐 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:154` |
| `/version` | 显示当前版本 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:158` |
| `/changelog` | 显示本构建的近期变更 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:159` |
| `/info` | 显示会话信息与 token | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:160` |
| `/reset` | 复核并确认 banked OpenAI 用量重置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:161` |
| `/usage` | 显示已连接 provider 的用量限额 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:162` |
| `/productivity` | 生成可分享的用量报告+仪表盘图 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:163` |
| `/wrapped` | /productivity 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:167` |
| `/feedback` | 发送关于 jcode 的反馈 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:168` |
| `/telemetry` | 显示/修改 jcode 发送的数据 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:169` |
| `/support` | 预填诊断信息发邮件给支持 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:170` |
| `/subscription` | 显示 jcode 订阅状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:171` |
| `/subscribe` | 为何/如何订阅 jcode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:172` |
| `/config` | 显示或编辑配置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:173` |
| `/log` | 在 jcode 日志中标记当前位置 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:174` |
| `/keys` | 显示与终端/系统的键位冲突（/keys refresh 重扫） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:175` |
| `/keybindings`（hidden 别名） | /keys 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:179` |
| `/diff` | 循环/设置 diff 显示模式（off/inline/full/file） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:180` |
| `/onboarding-preview` | 预览首启引导屏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:184` |
| `/onboarding-sim` | 走遍每个首启屏（Alt+5 重置/Cmd+5 切换） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:188` |
| `/reload` | 重载到最新可用二进制 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:192` |
| `/restart` | 用当前二进制重启 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:193` |
| `/rebuild` | 后台重建并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:194` |
| `/selfdev` | 打开新的 self-dev 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:195` |
| `/update` | 后台更新并自动重载 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:196` |
| `/update-sim` | 安全预览更新 UI（Alt+_） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:197` |
| `/resume` | 打开会话选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:198` |
| `/sessions` | /resume 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:199` |
| `/session` | /resume 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:200` |
| `/active` | 管理活动会话（working/ready） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:201` |
| `/catchup` | 打开 Catch Up 选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:202` |
| `/back` | 回到上一个 Catch Up 会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:203` |
| `/save` | 收藏会话便于访问 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:204` |
| `/unsave` | 移除会话收藏 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:205` |
| `/rename` | 重命名当前会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:206` |
| `/fork` | 把会话分叉到新窗口（可选 prompt） | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:207` |
| `/split`（hidden 别名） | /fork 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:208` |
| `/transfer` | 把上下文压缩进新的交接会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:209` |
| `/cloud` | 把本会话迁到云主机继续 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:210` |
| `/local` | 把云会话接回本机 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:214` |
| `/workspace` | Niri 风格会话工作区 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:215` |
| `/quit` | 退出 jcode | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:216` |
| `/auth` | 显示鉴权状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:217` |
| `/login` | 登录 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:218` |
| `/logout` | 登出 provider | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:219` |
| `/account` | 打开合并账户选择器 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:220` |
| `/accounts` | /account 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:221` |
| `/cache` | 显示缓存统计；extend/5m 省 Anthropic TTL | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:222` |
| `/debug-visual` | 切换可视化调试覆盖层 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:223` |
| `/screenshot-mode` | 切换截图捕获模式 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:224` |
| `/screenshot` | 捕获一个截图调试状态 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:225` |
| `/record` | 录制一段 demo | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:226` |
| `/client-reload`（remote） | 强制重载客户端二进制 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:227` |
| `/server-reload`（remote） | 强制重载服务端二进制 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:228` |
| `/continue`（remote） | 继续每个本会自动恢复的中断会话 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:229` |
| `/resumeall`（remote） | /continue 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:233` |
| `/resume-all`（hidden 别名） | /continue 的别名 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:234` |
| `/z`（hidden 别名） | 秘密 premium 模式命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:235` |
| `/zz`（hidden 别名） | 秘密 premium 模式命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:236` |
| `/zzz`（hidden 别名） | 秘密 premium 模式命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:237` |
| `/zstatus`（hidden 别名） | 秘密 premium 模式状态命令 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:238` |

## 2. commands.rs 处理函数（共 43 条）

> commands.rs 里**没有命令表**，只有 43 个 `handle_*` 函数（另 4 个 `parse_*` 辅助：parse_poke_command:66、parse_manual_subagent_spec:592、parse_diff_mode_name:957、parse_agents_target:3058，未计入）。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `handle_transfer_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:524` |
| `handle_subagent_model_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:753` |
| `handle_subagent_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:799` |
| `handle_cancel_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:837` |
| `handle_help_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:869` |
| `handle_keys_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:897` |
| `handle_model_status_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:925` |
| `handle_diff_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:978` |
| `handle_log_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1007` |
| `handle_ssh_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1076` |
| `handle_pending_ssh_remote_target` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1133` |
| `handle_btw_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1323` |
| `handle_fork_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1340` |
| `handle_catchup_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1387` |
| `handle_back_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1445` |
| `handle_git_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1565` |
| `handle_transcript_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1601` |
| `handle_git_status_completed` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1649` |
| `handle_session_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:1663` |
| `handle_triage_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2288` |
| `handle_merge_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2311` |
| `handle_commit_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2374` |
| `handle_commit_push_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2389` |
| `handle_fast_release_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2404` |
| `handle_fast_macos_release_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2419` |
| `handle_merge_remote_release_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2436` |
| `handle_remote_release_command_local` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2453` |
| `handle_selfdev_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2468` |
| `handle_goals_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2563` |
| `handle_disabled_mission_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2668` |
| `handle_test_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2681` |
| `handle_dictation_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2865` |
| `handle_compact_notifications_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2922` |
| `handle_tool_call_details_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:2967` |
| `handle_show_agentgrep_output_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3013` |
| `handle_swarm_prompt_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3105` |
| `handle_agents_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3291` |
| `handle_alignment_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3313` |
| `handle_reasoning_display_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3359` |
| `handle_config_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3414` |
| `handle_usage_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3692` |
| `handle_feedback_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3712` |
| `handle_telemetry_command` | （按 Main 要求只列名字） | `crates/jcode-tui/src/tui/app/commands.rs:3736` |

## 3. 共享本地分派链（共 22 条）

> `dispatch_single_local_command` 顺序试扣；commands_dispatch.rs:221-244 的 `||` 链共 21 个 handler + 1 个 SSH 本地兜底分支(210-212 三个 handler) = 22 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `handle_cancel_command` | 取消当前操作（本地链首） | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:221` |
| `handle_help_command` | 帮助覆盖层 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:222` |
| `handle_keys_command` | 键位冲突报告 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:223` |
| `handle_ssh_command` | SSH 连接 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:224` |
| `handle_session_command` | 会话/仓库/发布/plan/improve 等大链 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:227` |
| `handle_dictation_command` | 语音/听写 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:228` |
| `handle_config_command` | 配置与显示类开关 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:229` |
| `commands_colors::handle_colors_command` | /colors、/color | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:230` |
| `handle_log_command` | /log | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:231` |
| `handle_diff_command` | /diff | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:232` |
| `handle_model_status_command` | /provider-test-coverage、/model-status | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:233` |
| `debug::handle_debug_command` | 调试命令 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:234` |
| `model_context::handle_model_command` | /model、/models、/effort、/fast、/transport、/refresh-model-list | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:235` |
| `app.handle_usage_reset_command` | /reset [usage limits openai [confirm/cancel]] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:236` |
| `handle_usage_command` | /usage | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:237` |
| `productivity::handle_productivity_command` | /productivity、/wrapped、/stats | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:238` |
| `handle_feedback_command` | /feedback | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:239` |
| `handle_telemetry_command` | /telemetry | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:240` |
| `support::handle_support_command` | /support | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:241` |
| `state_ui::handle_info_command` | /skills、/version、/changelog、/cache、/info、/context | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:242` |
| `auth::handle_auth_command` | /auth、/login、/logout、/account(s)、/hosted、/subscribe、/subscription | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:243` |
| `tui_lifecycle_runtime::handle_dev_command` | /reload、/restart、/rebuild、/update、/update-sim、/onboarding-sim、/onboarding-preview、/z /zz /zzz /zstatus | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:244` |

## 4. SSH 阻断清单（共 88 条）

> `ssh_unsupported_command`（commands_dispatch.rs:11-137）：SSH 远程模式下这些本地动作被阻断，提示"本机未改动"，需登录远端主机执行。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/logout` | SSH 模式本地动作阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:26` |
| `/auth` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:27` |
| `/account` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:28` |
| `/accounts` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:29` |
| `/config` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:30` |
| `/permissions` | 阻断；无本地 handler | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:31` |
| `/permission` | 阻断；无本地 handler | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:32` |
| `/agents` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:33` |
| `/swarm-prompt` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:34` |
| `/keys` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:35` |
| `/keybindings` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:36` |
| `/alignment` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:37` |
| `/reasoning` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:38` |
| `/thinking` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:39` |
| `/thinking-display` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:40` |
| `/compact-notifications` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:41` |
| `/show-agentgrep-output` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:42` |
| `/tool-call-details` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:43` |
| `/colors` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:44` |
| `/theme` | 阻断；未找到本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:45` |
| `/telemetry` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:46` |
| `/ssh` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:47` |
| `/remote` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:48` |
| `/resume` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:49` |
| `/sessions` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:50` |
| `/session` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:51` |
| `/active` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:52` |
| `/catchup` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:53` |
| `/back` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:54` |
| `/save` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:55` |
| `/unsave` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:56` |
| `/transcript` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:57` |
| `/git` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:58` |
| `/open` | 阻断；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:59` |
| `/file` | 阻断；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:60` |
| `/selfdev` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:61` |
| `/new-terminal` | 阻断；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:62` |
| `/reload` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:63` |
| `/client-reload` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:64` |
| `/restart` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:65` |
| `/rebuild` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:66` |
| `/update` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:67` |
| `/update-sim` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:68` |
| `/onboarding-sim` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:69` |
| `/onboarding-preview` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:70` |
| `/usage` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:71` |
| `/reset` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:72` |
| `/subscription` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:73` |
| `/fix` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:74` |
| `/support` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:75` |
| `/feedback` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:76` |
| `/productivity` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:77` |
| `/wrapped` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:78` |
| `/stats` | 阻断；productivity.rs:17 处理 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:79` |
| `/log` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:80` |
| `/cache` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:81` |
| `/initiatives` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:82` |
| `/goals` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:83` |
| `/dictate` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:84` |
| `/dictation` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:85` |
| `/voice` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:86` |
| `/debug-fixture` | 阻断；debug.rs:581 处理 gmail-draft | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:87` |
| `/debug-visual` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:88` |
| `/screenshot` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:89` |
| `/record` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:90` |
| `/subagent-model` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:91` |
| `/continue` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:92` |
| `/resumeall` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:93` |
| `/resume-all` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:94` |
| `/z` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:95` |
| `/zz` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:96` |
| `/zzz` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:97` |
| `/zstatus` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:98` |
| `/autoreview` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:99` |
| `/autojudge` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:100` |
| `/todo` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:101` |
| `/todos` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:102` |
| `/observe` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:103` |
| `/splitview` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:104` |
| `/split-view` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:105` |
| `/review` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:106` |
| `/judge` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:107` |
| `/subagent` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:108` |
| `/fork` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:109` |
| `/split` | 阻断(别名) | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:110` |
| `/btw` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:111` |
| `/transfer` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:112` |
| `/workspace` | 阻断 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:113` |

> 另 2 条前缀特殊规则（非字面量，但同属阻断逻辑）：`!<cmd>`（以 `!` 开头一律判为本地动作，:19）；`/fast default`（/fast 后跟 default 亦判本地，:21）。

## 5. 斜杠命令解析规则（共 10 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| find_known_commands | 扫描输入，返回所有命中已知命令名的 token 区间 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:13` |
| active_token_before_cursor | 返回光标前正在编辑的 token 区间，供补全 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:28-38` |
| scan_slash_tokens | 主扫描器：逐字符状态机 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:43-121` |
| 单引号状态 | 在 '...' 内不识别命令 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:92` |
| 双引号状态 | 在 "..." 内不识别命令 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:97` |
| 反引号状态 | 在 `...` 内不识别命令 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:76,88` |
| 围栏代码块 | 行首 ``` 起止之间的内容整段忽略 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:53,77` |
| 反斜杠转义 | 反斜杠跳过下一个字符，使其不被当作语法 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:70` |
| '/' 位置约束 | 仅当 index==0 或前一字符为空白时 '/' 才算命令起始（URL/路径/散文不识别） | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:103-110` |
| token 边界 | 命令名延伸到下一个空白；参数即其后文本 | `crates/jcode-tui/src/tui/app/slash_command_parser.rs:111-115` |

## 6. CLI 顶层子命令（共 35 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `jcode serve` | 启动 agent 后台守护进程（可选 --server-name/隐藏参数） | `src/cli/args.rs:148` |
| `jcode acp` | 作为 Agent Client Protocol 适配器接入守护进程 | `src/cli/args.rs:164` |
| `jcode server <action>` | 管理后台守护进程 | `src/cli/args.rs:174` |
| `jcode connect` | 连接已在运行的 server | `src/cli/args.rs:181` |
| `jcode run <message>` | 发一条消息后退出（--json/--ndjson） | `src/cli/args.rs:184` |
| `jcode login [PROVIDER]` | OAuth/API key 登录 provider（--account/--no-browser/--print-auth-url/--callback-url/--auth-code/--json/--complete/--flow-id/--cancel/--no-validate/--google-access-tier/--api-base/--api-key/--api-key-env） | `src/cli/args.rs:198` |
| `jcode account <action>` | 登录并管理 Jcode 账号 | `src/cli/args.rs:265` |
| `jcode repl` | 无 TUI 的简单 REPL 模式 | `src/cli/args.rs:272` |
| `jcode update` | 升级 jcode 到最新版 | `src/cli/args.rs:275` |
| `jcode version` | 显示版本/构建信息（--json） | `src/cli/args.rs:278` |
| `jcode usage` | 显示已连接 provider 的用量额度（--json） | `src/cli/args.rs:284` |
| `jcode telemetry <action>` | 查看/修改匿名遥测设置 | `src/cli/args.rs:290` |
| `jcode self-dev (alias selfdev)` | self-development canary 会话（--build） | `src/cli/args.rs:294` |
| `jcode debug <command> [arg]` | 调试 socket CLI（--session/--socket/--wait） | `src/cli/args.rs:302` |
| `jcode auth <action>` | 认证状态与校验助手 | `src/cli/args.rs:325` |
| `jcode provider <action>` | provider 发现与选择助手 | `src/cli/args.rs:329` |
| `jcode memory <action>` | 记忆管理命令 | `src/cli/args.rs:333` |
| `jcode session <action>` | 会话管理命令 | `src/cli/args.rs:337` |
| `jcode ambient <action>` | ambient 模式管理 | `src/cli/args.rs:341` |
| `jcode cloud <action>` | Jcode Cloud/Jade 集成 | `src/cli/args.rs:345` |
| `jcode pair` | 生成 iOS/web 配对码（--list/--revoke） | `src/cli/args.rs:349` |
| `jcode permissions` | 处理待定的 ambient 权限请求 | `src/cli/args.rs:363` |
| `jcode transcript [text]` | 把外部转录文本注入活动 TUI（--mode/--session） | `src/cli/args.rs:366` |
| `jcode dictate` | 运行配置的听写（--type 直接键入） | `src/cli/args.rs:377` |
| `jcode setup-hotkey` | 配置平台全局热键启动 jcode（隐藏参数/--uninstall） | `src/cli/args.rs:384` |
| `jcode setup-launcher` | 安装平台启动器集成 | `src/cli/args.rs:404` |
| `jcode browser <action> [browser]` | 浏览器自动化 setup/status/detect | `src/cli/args.rs:407` |
| `jcode replay <session>` | 在 TUI 重放会话（--swarm/--export/--speed/--timeline/--auto-edit/--video/--cols/--rows/--fps/--centered/--no-centered） | `src/cli/args.rs:418` |
| `jcode model <action>` | 模型管理命令 | `src/cli/args.rs:467` |
| `jcode provider-test-coverage (alias model-status)` | 显示实机验证覆盖（PROVIDER/MODEL/--coverage-file/--coverage-limit） | `src/cli/args.rs:472` |
| `jcode provider-doctor (alias provider-strict-e2e)` | 按严格 E2E 关卡诊断 provider/model（--tier/--json） | `src/cli/args.rs:493` |
| `jcode auth-test` | 端到端测试认证（--login/--all-configured/--no-smoke/--no-tool-smoke/--prompt/--json/--output/--coverage/--context-audit/--coverage-file/--coverage-limit） | `src/cli/args.rs:510` |
| `jcode restart <action>` | 跨重启保存/恢复打开的 jcode 窗口 | `src/cli/args.rs:557` |
| `jcode menubar (aliases menu-bar,statusbar)` | macOS 菜单栏实时指示器（--once/--json） | `src/cli/args.rs:563` |
| `jcode api-bridge (alias api)` | 在 Unix socket 上提供 SDK 稳定 API（--api-socket/--stdio） | `src/cli/args.rs:581` |

## 7. CLI 嵌套子命令（共 53 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `jcode server stdio` | 内部：ssh attach 的原生客户端协议桥（隐藏） | `src/cli/args.rs:638` |
| `jcode server start` | 若未运行则启动后台 server（--json） | `src/cli/args.rs:641` |
| `jcode server keepalive` | 内部：保持轻量连接到 stdin 关闭（隐藏） | `src/cli/args.rs:649` |
| `jcode server promote [version]` | 把共享 server 通道钉到某个已安装版本（--json） | `src/cli/args.rs:652` |
| `jcode server reload` | 优雅地把运行中的 server 重载到最新二进制（--force/--json） | `src/cli/args.rs:665` |
| `jcode server stop` | 停止后台 server 并清理 socket（--force/--json） | `src/cli/args.rs:681` |
| `jcode account login` | 浏览器设备授权并等待套餐激活（--no-browser） | `src/cli/args.rs:609` |
| `jcode account status` | 显示 /v1/me 的账号/套餐/用量状态（--json） | `src/cli/args.rs:616` |
| `jcode account manage` | 打开 Jcode 账号管理页 | `src/cli/args.rs:627` |
| `jcode account logout` | 吊销当前 key 并安全清除本地状态 | `src/cli/args.rs:630` |
| `jcode telemetry status` | 显示当前遥测状态，不创建匿名 ID（--json） | `src/cli/args.rs:600` |
| `jcode telemetry enable` | 启用匿名用量遥测 | `src/cli/args.rs:607` |
| `jcode telemetry disable` | 持久禁用所有遥测 | `src/cli/args.rs:609` |
| `jcode auth import` | 从受信客户端导入一条 OAuth 登录（--stdin 必填/--json） | `src/cli/args.rs:844` |
| `jcode auth status` | 显示模型/工具 provider 的认证状态（--json） | `src/cli/args.rs:853` |
| `jcode auth doctor [PROVIDER]` | 诊断 provider 认证问题（--validate/--json） | `src/cli/args.rs:859` |
| `jcode provider list` | 列出可传给 -p/--provider 的 ID（--json） | `src/cli/args.rs:706` |
| `jcode provider current` | 显示当前请求与实际解析出的 provider 选择（--json） | `src/cli/args.rs:713` |
| `jcode provider add <name>` | 新增命名 OpenAI 兼容 profile（--base-url/--model/--context-window/--api-key-env/--api-key/--api-key-stdin/--no-api-key/--auth/--auth-header/--env-file/--set-default/--overwrite/--provider-routing/--model-catalog/--json） | `src/cli/args.rs:718` |
| `jcode memory list` | 列出全部记忆（--scope/--tag） | `src/cli/args.rs:1146` |
| `jcode memory search <query>` | 按查询检索记忆（--semantic） | `src/cli/args.rs:1160` |
| `jcode memory export <output>` | 导出记忆到 JSON（--scope） | `src/cli/args.rs:1173` |
| `jcode memory import <input>` | 从 JSON 导入记忆（--scope/--overwrite） | `src/cli/args.rs:1183` |
| `jcode memory stats` | 显示记忆统计 | `src/cli/args.rs:1200` |
| `jcode memory clear-test` | 清理测试记忆存储（调试会话用） | `src/cli/args.rs:1203` |
| `jcode session rename <session> [name]` | 重命名已保存会话（--clear/--json） | `src/cli/args.rs:1044` |
| `jcode ambient status` | 显示 ambient 模式状态 | `src/cli/args.rs:838` |
| `jcode ambient log` | 显示近期 ambient 活动日志 | `src/cli/args.rs:840` |
| `jcode ambient trigger` | 手动触发一轮 ambient 周期 | `src/cli/args.rs:842` |
| `jcode ambient stop` | 停止 ambient 模式 | `src/cli/args.rs:844` |
| `jcode ambient run-visible` | 内部：在可见 TUI 中跑一轮 ambient（隐藏） | `src/cli/args.rs:847` |
| `jcode cloud sessions <action>` | 上传/列出/校验/查看云端同步会话 | `src/cli/args.rs:701` |
| `jcode cloud move` | 把活动会话迁到云主机继续（--session/--host/--remote-binary/--allow-active/--dry-run/--attach/--json） | `src/cli/args.rs:707` |
| `jcode cloud return` | 把迁出的会话拉回本地并三方合并 git（--session/--refs-only/--attach/--json） | `src/cli/args.rs:730` |
| `jcode cloud where` | 显示迁出会话所在与仓库分叉（--session/--json） | `src/cli/args.rs:746` |
| `jcode cloud attach` | 把本终端接到云主机上的会话（--session） | `src/cli/args.rs:754` |
| `jcode cloud receive` | 内部：cloud move 远端侧，读 stdin tar（隐藏，--json） | `src/cli/args.rs:760` |
| `jcode cloud activate` | 内部：cloud move 提交阶段远端侧（隐藏，--session/--epoch） | `src/cli/args.rs:767` |
| `jcode cloud export` | 内部：cloud return 远端侧，写 stdout tar（隐藏，--session/--epoch） | `src/cli/args.rs:776` |
| `jcode cloud sessions configure` | 配置本机 Jade API 默认值（--api-base/--api-token/--api-token-env/--api-token-id/--user-id/--helper/--clear） | `src/cli/args.rs:805` |
| `jcode cloud sessions status` | 显示已保存 Jade 默认值且不泄露密钥（--json） | `src/cli/args.rs:834` |
| `jcode cloud sessions upload <session_file>` | 上传指定本地会话 JSON 到 Jade（--raw + jade 选项） | `src/cli/args.rs:843` |
| `jcode cloud sessions upload-latest` | 上传最新本地会话（--sessions-dir/--raw + jade） | `src/cli/args.rs:854` |
| `jcode cloud sessions sync` | 增量同步本地会话到 Jade（--sessions-dir/--since-days/--all/--max/--min-interval-mins/--raw/--dry-run/--force/--json + jade） | `src/cli/args.rs:869` |
| `jcode cloud sessions list` | 列出云端已上传会话（--limit/--json + jade） | `src/cli/args.rs:911` |
| `jcode cloud sessions verify <session_id>` | 校验云元数据与 S3 blob 均存在（+ jade） | `src/cli/args.rs:925` |
| `jcode cloud sessions dashboard` | 渲染云端会话 HTML 面板（--limit/--output/--open/--with-view + jade） | `src/cli/args.rs:933` |
| `jcode cloud sessions view <session_id>` | 下载并查看云端会话（--format/--output/--open + jade） | `src/cli/args.rs:957` |
| `jcode restart save` | 保存当前打开 jcode 窗口的重启快照（--auto-restore） | `src/cli/args.rs:1015` |
| `jcode restart restore` | 恢复最近保存的重启快照 | `src/cli/args.rs:1021` |
| `jcode restart status` | 显示当前保存的重启快照 | `src/cli/args.rs:1023` |
| `jcode restart clear` | 删除当前重启快照 | `src/cli/args.rs:1025` |
| `jcode model list` | 列出可传给 -m/--model 的模型名（--json/--verbose） | `src/cli/args.rs:1030` |

## 8. CLI 全局标志（共 26 条）

> `Args` 结构上的 26 个标志；其中 24 个标 `global = true`（`--onboarding-sim`、`--update-sim` 未标 global）。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-p/--provider` | 初始 provider（默认 auto） | `src/cli/args.rs:35` |
| `-C/--cwd` | 本地客户端进程工作目录 | `src/cli/args.rs:39` |
| `--remote-working-dir` | --socket 远端工作目录 | `src/cli/args.rs:43` |
| `--ssh <HOST>` | 本地 UI 连接该 SSH 主机上的持久 server | `src/cli/args.rs:47` |
| `--ssh-binary <PATH>` | 远端 jcode 可执行名/路径（需 --ssh） | `src/cli/args.rs:51` |
| `--ssh-server-socket <PATH>` | 远端守护 socket 覆盖（需 --ssh） | `src/cli/args.rs:55` |
| `--no-update` | 跳过自动更新检查 | `src/cli/args.rs:59` |
| `--auto-update` | 有新版本时自动更新（默认 true） | `src/cli/args.rs:63` |
| `--trace` | 把工具输入输出与 token 用量打到 stderr | `src/cli/args.rs:67` |
| `--quiet` | 抑制非错误 CLI/状态输出（脚本用） | `src/cli/args.rs:71` |
| `--resume [ID]` | 按 ID 恢复会话，无 ID 则列出会话 | `src/cli/args.rs:75` |
| `--fresh-spawn` | 内部：新窗口启动，跳过重型 resume 引导（隐藏） | `src/cli/args.rs:79` |
| `--spawn-hotkey <CHORD>` | 内部：启动本进程的全局热键（隐藏） | `src/cli/args.rs:83` |
| `--no-selfdev` | 禁用 jcode 仓库自动检测与 self-dev 模式 | `src/cli/args.rs:87` |
| `--onboarding-sim` | 启动时运行 onboarding 模拟器 | `src/cli/args.rs:93` |
| `--update-sim` | 启动时自动播放更新安装重启模拟 | `src/cli/args.rs:98` |
| `--socket <PATH>` | server/client 通信自定义 socket | `src/cli/args.rs:102` |
| `--debug-socket` | 开启 debug socket（广播全部 TUI 状态） | `src/cli/args.rs:106` |
| `-m/--model` | 使用模型 | `src/cli/args.rs:110` |
| `--provider-profile` | config.toml 中 [providers.<name>] 命名 profile | `src/cli/args.rs:115` |
| `--tool-profile` | 暴露给模型的工具档位 full/minimal/none | `src/cli/args.rs:119` |
| `--tools` | 逗号分隔工具白名单（* / all 为全量） | `src/cli/args.rs:123` |
| `--disabled-tools` | 逗号分隔要隐藏的工具 | `src/cli/args.rs:127` |
| `--disable-base-tools` | 隐藏所有内置工具 | `src/cli/args.rs:131` |
| `--mcp-tools` | MCP 工具暴露模式 auto/eager/deferred | `src/cli/args.rs:135` |
| `--mcp-tools-token-threshold <TOKENS>` | auto 模式切到 deferred 的 token 阈值 | `src/cli/args.rs:139` |

## 9. 可触碰但未登记的命令（共 14 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/theme` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:45` |
| `/open` | 阻断表出现；wire-backed，无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:59` |
| `/file` | 阻断表出现；wire-backed，无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:60` |
| `/new-terminal` | 阻断表出现；wire-backed，无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:62` |
| `/permissions` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:31` |
| `/permission` | 阻断表出现；无本地 handler[未核实] | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:32` |
| `/debug-fixture` | debug.rs:581 处理 gmail-draft | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:87` |
| `/stats` | productivity.rs:17 处理 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:79` |
| `/hosted` | auth 侧实现，未登记 | `auth_account_commands.rs:78,84` |
| `/exit` | 仅 SSH 登录取消语境 | `crates/jcode-tui/src/tui/app/auth_remote.rs:447` |
| `/mission` | disabled 占位（与已登记项不同） | `crates/jcode-tui/src/tui/app/commands.rs:2669` |
| `/goal` | disabled 占位，与 /goals 不同 | `crates/jcode-tui/src/tui/app/commands.rs:2670` |
| `/stop` | /cancel 的别名，未登记 | `crates/jcode-tui/src/tui/app/commands.rs:838` |
| `/ambient` | 仅文档；TUI 无此斜杠命令，只有 CLI `jcode ambient` | `docs/AMBIENT_MODE.md:606` |

## 10. 键位—可配置（keybindings.*）（共 32 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `scroll_up` | 聊天记录上滚一行 | `crates/jcode-config-types/src/keybindings.rs:196；默认 ctrl+shift+k` |
| `scroll_down` | 聊天记录下滚一行 | `keybindings.rs:203；ctrl+shift+j` |
| `scroll_page_up` | 上翻一页 | `keybindings.rs:209；alt+u` |
| `scroll_page_down` | 下翻一页 | `keybindings.rs:215；alt+d` |
| `model_switch_next` | 切下一个模型 | `keybindings.rs:221；ctrl+tab` |
| `model_switch_prev` | 切上一个模型 | `keybindings.rs:227；ctrl+shift+tab` |
| `fallback_switch` | 接受错误后的备用模型/鉴权重发提议 | `keybindings.rs:233；ctrl+y` |
| `effort_increase` | 提高推理力度 | `keybindings.rs:239；cmd+right / alt+right` |
| `effort_decrease` | 降低推理力度 | `keybindings.rs:246；cmd+left / alt+left` |
| `centered_toggle` | 切换居中布局 | `keybindings.rs:253；alt+c` |
| `scroll_prompt_up` | 跳到上一条用户 prompt | `keybindings.rs:260；ctrl+k` |
| `scroll_prompt_down` | 跳到下一条用户 prompt | `keybindings.rs:267；ctrl+j` |
| `scroll_bookmark` | 切换滚动书签 | `keybindings.rs:273；ctrl+g` |
| `auto_poke_toggle` | 开/关 auto-poke(未完成 todo 自动续跑) | `keybindings.rs:279；ctrl+p` |
| `scroll_up_fallback` | 可选备用上滚键 | `keybindings.rs:285；默认 unbound` |
| `scroll_down_fallback` | 可选备用下滚键 | `keybindings.rs:293；默认 unbound` |
| `workspace_left` | Niri 风格：焦点移到左工作区(仅 remote/client 派发) | `keybindings.rs:299；alt+h` |
| `workspace_down` | Niri 风格：焦点移到下工作区(仅 remote/client 派发) | `keybindings.rs:305；alt+j` |
| `workspace_up` | Niri 风格：焦点移到上工作区(仅 remote/client 派发) | `keybindings.rs:311；alt+k` |
| `workspace_right` | Niri 风格：焦点移到右工作区(仅 remote/client 派发) | `keybindings.rs:317；alt+l` |
| `new_terminal` | 在新终端窗口开一个 fresh jcode 会话 | `keybindings.rs:323；表里 cmd+shift+; / alt+shift+;，但 lib.rs:1065 注释与 keybind.rs:628 都称默认 unbound[实现/注释漂移]` |
| `open_resume` | 打开 /resume 会话选择器 | `keybindings.rs:334；cmd+b / alt+r` |
| `voice_input` | 启动/停止内置语音输入(Nari) | `keybindings.rs:342；ctrl+space` |
| `side_panel_toggle` | 循环侧栏(分屏/全屏/隐藏) | `lib.rs:1044；alt+m（不在 KEYBINDING_DEFAULTS）` |
| `copy_selection_toggle` | 切换选择/复制模式 | `lib.rs:1046；alt+y` |
| `diagram_pane_toggle` | 切换图表面板位置(侧/顶) | `lib.rs:1048；alt+t` |
| `diagram_pane_visibility_toggle` | 显示/隐藏图表面板 | `lib.rs:1050；alt+shift+m` |
| `typing_scroll_lock_toggle` | 锁定打字时自动滚动 | `lib.rs:1052；alt+s` |
| `diff_mode_cycle` | 循环 diff 显示模式(Off/Inline/Pinned/File) | `lib.rs:1054；alt+g` |
| `info_widget_toggle` | 开/关 info widget | `lib.rs:1056；alt+i` |
| `todo_card_toggle` | 在聊天里显示/收起 todo 卡 | `lib.rs:1059；alt+x` |
| `swarm_panel_focus` | 聚焦 inline swarm 面板(仅 swarm_spawn_mode=inline 且本会话管 swarm 时) | `lib.rs:1064；alt+n` |

> 两个非键位串字段，另列（不计入上面 32 条）：`session_picker_enter`（会话选择器 Enter 语义：current-terminal(默认)/new-terminal；Ctrl+Enter 走另一支，`lib.rs:1076`——这是 `KeybindingsConfig` 的第 33 个 pub 字段、策略枚举，不是键位串）；`[dictation].key`（外部听写命令热键(可选)，属 `[dictation]` config 段，`crates/jcode-tui/src/tui/keybind.rs:612-626`）。

## 11. 键位—内置不可配置（共 43 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `Ctrl+K/J（mod+K/J 回退）` | 上一个/下一个用户 prompt；mod+[ / mod+] 同义 | `crates/jcode-tui-core/src/keybind.rs:397-427` |
| `mod+Shift+K / mod+Shift+J` | 内置逐行上/下滚(mod=Ctrl/Cmd/Alt) | `crates/jcode-tui-core/src/keybind.rs:378-388` |
| `Cmd+K / Cmd+J / Cmd+[ / Cmd+] / Ctrl+[` | macOS 内置 prompt 跳转回退 | `crates/jcode-setup-hints/src/keymap/conflicts.rs:200-210` |
| `Ctrl+Enter / Cmd+Enter` | alternate send：与 Enter 相反地排队或插队 | `crates/jcode-config-types/src/keybindings.rs:225-231(conflicts.rs:262-276)；input.rs:1344` |
| `Shift+Enter / Alt+Enter` | 输入中插入换行 | `crates/jcode-tui/src/tui/app/hotkey_feedback.rs:405-412` |
| `尾随 \ + Enter` | 插入换行回退(Shift+Enter 不被终端识别时) | `crates/jcode-tui/src/tui/ui_overlays.rs:577-580` |
| `Ctrl+C / Ctrl+D` | 处理中=中断；空闲且有输入=清空输入；再按=退出 | `crates/jcode-tui/src/tui/app/input.rs:2780-2805` |
| `Ctrl+D（有文本时）` | 前向删除一个字符(readline 语义) | `crates/jcode-tui/src/tui/app/input.rs:2190-2216` |
| `Ctrl+R` | 跨会话搜索 prompt 历史 | `crates/jcode-tui/src/tui/app/input.rs:2806-2809` |
| `Ctrl+A（输入为空）` | 复制可见聊天视口+上下文 | `crates/jcode-tui/src/tui/app/input.rs:2810-2813` |
| `Alt+A（输入为空）` | 同上快捷复制 | `crates/jcode-tui/src/tui/app/input.rs:2253-2256` |
| `Ctrl+L / Cmd+L` | 终端式清屏(历史推入 scrollback) | `crates/jcode-tui/src/tui/app/input.rs:2819-2823；2182-2185` |
| `Ctrl+U` | 删除光标前全部输入 | `crates/jcode-tui/src/tui/app/input.rs:2049-2052` |
| `Ctrl+K（有草稿时）` | 删除光标后到行尾 | `crates/jcode-tui/src/tui/app/input.rs:2403-2408` |
| `Ctrl+Z` | 撤销输入编辑 | `crates/jcode-tui/src/tui/app/input.rs:2057-2060` |
| `Ctrl+X` | 剪切整行输入到剪贴板 | `crates/jcode-tui/src/tui/app/input.rs:2061-2064` |
| `Ctrl+S` | 暂存/取回输入草稿 | `crates/jcode-tui/src/tui/app/input.rs:2089-2092` |
| `Ctrl+Tab / Ctrl+T` | 切换 queue mode | `crates/jcode-tui/src/tui/app/input.rs:2097-2106` |
| `Ctrl+V / Alt+V / Cmd+V` | 粘贴剪贴板(文本或图片) | `crates/jcode-tui/src/tui/app/input.rs:2093-2096；211；2249` |
| `Ctrl+A / Ctrl+E` | 光标到输入首/尾 | `crates/jcode-tui/src/tui/app/input.rs:2065-2072` |
| `Ctrl+B / Ctrl+F / Ctrl+Left / Ctrl+Right` | 按词左/右移动 | `crates/jcode-tui/src/tui/app/input.rs:2073-2084；2107-2118` |
| `Ctrl+W / Ctrl+Backspace / Ctrl+H` | 删除前一个词 | `crates/jcode-tui/src/tui/app/input.rs:2085-2088` |
| `Ctrl+Up` | 取回待发消息进行编辑 / prompt 历史 | `crates/jcode-tui/src/tui/app/input.rs:2119-2122；3169` |
| `Ctrl+Down` | prompt 历史向下走 | `crates/jcode-tui/src/tui/app/input.rs:3179` |
| `Up/Down（输入为空）` | 滚动历史 | `crates/jcode-tui/src/tui/ui_overlays.rs:475` |
| `PageUp/PageDown` | 滚动历史(Up/Down 各 ±1，PageUp/Down ±10) | `crates/jcode-tui/src/tui/app/input.rs:2901-2910` |
| `Ctrl+1..4` | 侧栏宽度预设 25/50/75/100% | `crates/jcode-tui/src/tui/app/navigation.rs:1319-1334` |
| `Ctrl+5..9` | 按 recency 跳到第 5..9 近的 prompt | `crates/jcode-tui/src/tui/app/navigation.rs:1306-1317` |
| `Shift+Tab (BackTab)` | 循环收藏模型 | `crates/jcode-tui/src/tui/app/input.rs:3107-3110` |
| `Alt+Space / Cmd+Space` | 下一条 prompt 路由到新会话 | `crates/jcode-tui/src/tui/app/input.rs:1975-1986` |
| `Alt+B / Alt+F / Alt+D / Alt+Backspace` | 按词后/前移、删后一词、删前一词 | `crates/jcode-tui/src/tui/app/input.rs:2226-2248` |
| `Cmd+Backspace/Delete` | 删前一词 | `crates/jcode-tui/src/tui/app/input.rs:2155-2158` |
| `Cmd+Left/Right/Home/End/Cmd+A/Cmd+E` | 光标到输入首/尾 | `crates/jcode-tui/src/tui/app/input.rs:2159-2166` |
| `Cmd+5` | 切换 onboarding 模拟器(dev) | `crates/jcode-tui/src/tui/app/input.rs:2148-2151` |
| `Alt+Shift+I` | 显示/隐藏内联图片(持久化) | `crates/jcode-tui/src/tui/ui_overlays.rs:520；input.rs:2622` |
| `Alt+E` | 展开/编辑 badge 快捷 | `crates/jcode-tui/src/tui/app/input.rs:2635` |
| `Ctrl+H / Ctrl+L（面板有焦点时）` | 焦点切回聊天 | `crates/jcode-tui/src/tui/app/navigation.rs:1285-1300` |
| `Ctrl+Left/Right（图表聚焦时）` | 循环切换图表 | `crates/jcode-tui/src/tui/app/input.rs:2374-2388` |
| `h/j/k/l、←↑↓→、+/-、[/]、o、Esc（图表聚焦）` | 平移/缩放/调整/弹出/退出图表 | `crates/jcode-tui/src/tui/app/navigation.rs:1340-1364` |
| `j/k/d/u/g/G/+/=/-/0/Esc（diff 面板聚焦）` | 滚动与缩放 diff 面板 | `crates/jcode-tui/src/tui/app/input.rs:2328-2348` |
| `Tab/BackTab、h/l、Esc、j/k/d/u（侧栏聚焦）` | 切换侧栏页、横向平移、退出焦点 | `crates/jcode-tui/src/tui/app/navigation.rs:560-615` |
| `Alt+Shift+P` | 打开 swarm 路由 prompt 编辑器 | `crates/jcode-tui/src/tui/app/tui_state.rs:2240-2250` |
| `⌨ 未知 chord 提示` | 未绑定修饰键 → 提示最近绑定(nearest_hotkey) | `crates/jcode-tui/src/tui/app/hotkey_feedback.rs:640-660` |

## 12. 面板与选择器（overlay / picker / 全屏页）（共 14 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `changelog overlay` | /changelog 全屏列出本构建的变更分组，可滚动/选择复制 | `crates/jcode-tui/src/tui/ui_overlays.rs:22；ui.rs:2714` |
| `help overlay` | /help 全屏：命令+键位清单+技能，Esc/q 关 | `crates/jcode-tui/src/tui/ui_overlays.rs:138；ui.rs:2726` |
| `model status overlay（/provider-test-coverage）` | 显示该 provider/model 的 live 验证证据，c 复制 | `crates/jcode-tui/src/tui/ui_overlays.rs:665；ui.rs:2738` |
| `session picker overlay` | /resume /catchup /save：搜索/多选/预览并恢复会话，可弹新终端或接管 live Claude | `crates/jcode-tui/src/tui/session_picker.rs:1210；ui.rs:2750` |
| `login picker overlay` | /login 选 provider 并走 OAuth/API key 流程 | `crates/jcode-tui/src/tui/login_picker.rs；ui.rs:2763` |
| `account picker overlay` | /account 内联账户中心：列出已存账户 + 新增/替换/切换/删除 | `crates/jcode-tui/src/tui/app/auth_account_picker.rs:1248；ui.rs:2776` |
| `panel image preview` | 点击聊天里的图片放大预览，Esc/Enter/q/点击关闭 | `crates/jcode-tui/src/tui/ui_panel_image_preview.rs:31；ui.rs:2702` |
| `onboarding welcome` | 首启引导(导入登录/telemetry/模型选择/建议)，占满聊天列 | `crates/jcode-tui/src/tui/ui_onboarding.rs；ui.rs:3048-3320` |
| `prompt history 搜索 overlay` | Ctrl+R：模糊搜索跨会话历史，Enter 采纳 | `crates/jcode-tui/src/tui/ui_input.rs:132；app/prompt_history.rs:326` |
| `命令联想 overlay (palette)` | 输入 `/` 时浮层给出命令建议+描述，Tab 补全 | `crates/jcode-tui/src/tui/ui_input.rs:215` |
| `inline interactive picker` | 模型选择器/命令面板/其它选择器的内联交互层 | `crates/jcode-tui/src/tui/ui_inline_interactive.rs；app/inline_interactive.rs:3294` |
| `copy/selection mode` | Alt+Y 进入的选择复制模式，Enter/Y 复制、Esc 退出 | `crates/jcode-tui/src/tui/app/input.rs:2713-2745` |
| `swarm 全屏页 / inline 控件` | Alt+N 循环 chat→inline 控件→全屏 swarm 页，↑/↓选择、o 弹出、Alt+Shift+P 改 prompt | `crates/jcode-tui/src/tui/info_widget_swarm_gallery.rs:152,499；ui.rs:2795,3324` |
| `usage overlay 组件` | 连接 provider 的用量窗口展示组件 | `crates/jcode-tui-usage-overlay/src/lib.rs；crates/jcode-tui/src/tui/usage_overlay.rs:1` |

### swarm 三档（Chat / Controls / FullPage）实测

`Alt+N`（`keybindings.swarm_panel_focus`）只在 `swarm_spawn_mode = inline` **且本会话管着一支 swarm** 时起作用；否则按下去什么也不发生（`tui_state.rs:2074-2115`）。三档**只改尺寸，不换主体**：一直是这支队的名册 + 名册里选中的那一位。

**位置**：聊天列的竖排分块是 `0 消息 / 1 排队 / 2 swarm 条 / 3 状态行 / 4 通知 / 5 inline UI / 6 间隙 / 7 输入 / 8 overscroll / 9 donut`（`ui.rs:3186-3204`）—— 条就在**转录下面、状态行上面**。（`┃` 右侧是注解，不是屏幕内容。）

```text
─ ① Chat（未聚焦） ───────────────────────────────────────────────────────────────────────────────
… 转录（唯一滚动盒；条一出现它就往上顶）                             条只长在状态行正上方（ui.rs:3192）
🐝 ⠙ researcher · 梳理 DESIGN      3/4 active · Alt+N controls       首行：🐝 打头；右端「计数 · 入口提示」
   ⠙ reviewer · 读源码                                               一行一只（默认 vertical，最多 4 行）
   ✓ planner · 定接口                                                行尾可带待办 d/t（swarm_gallery.rs:1017）
   +2 more                                                           超过 4 只 → 折成一行（:1090）
状态行（恒 1 行）                                                    ★ 这一档不画选中（marker = ""）
┃ 输入行（焦点永远在它身上）                                         裸打字照旧进输入框

─ ② Controls（聚焦） ─────────────────────────────────────────────────────────────────────────────
… 转录（被这块挤短）                                                 同一份名单，只是聚焦了
🐝 ⠙ researcher · 梳理 DESIGN      3/4 active                        入口提示消失（已经在里面）
▸ ⠙ reviewer · 读源码                                                ★ 选中行：前加 ▸、加粗
   ├─ ● 正在做：对齐 P1 的档位表                                     ★ 详情卡就地插在选中行下面
   │     └─ ● read · P0/04-tiers.md                                    （accordion，不是另开一块）
   ├─ ○ 改 overview.md                                               待办滑动窗 4 条
   └─ ○ 复核全树链接                                                 正在做那条下面嵌最近 3 条工具活动
   ✓ planner · 定接口                                                名单其余各行照旧都在 = 「其他条」
alt+n page · alt+↑/↓ select · alt+o open · esc exit                  末尾一行键位提示（:1116）
状态行（恒 1 行）／ 输入行                                           

─ ③ FullPage ─────────────────────────────────────────────────────────────────────────────────────
🐝 swarm · 4 agents · 3 active                                       ★ 整块转录被替换，不是叠加
alt+n chat · alt+↑/↓ select · alt+o open · esc chat                  键位行：esc chat = 直接回对话
▸ 🐝 ⠙ researcher · 梳理 DESIGN        6/16                          ★ 树：按 report_back 归属；▸ 画选中
  ├─ ⠙ reviewer · 读源码                                             兄弟按同一份 rank 排（:259）
  │  └─ ⠙ checker · 复核链接                                         嵌套子树
  └─ ✓ planner · 定接口                                              
──────────────────────────────────────                               分隔线
（下半部 = 选中那位的 live card：现场 + 待办 + 工具）                下半部把选中的现场铺开
状态行（恒 1 行）／ 输入行                                           壳不动（ui.rs:3324）
```

**三档的全部差别** —— ①② 是**同一处渲染**，`focused` 是唯一开关（`ui.rs:2967-2993`）：

| | ① Chat | ② Controls | ③ FullPage |
|---|---|---|---|
| 渲染器 | `render_swarm_strip_lines(focused=false)` | 同一个，`focused=true` | `render_swarm_page_lines`（`info_widget_swarm_gallery.rs:152`） |
| 占哪块 | 转录下面那一格（`swarm_gallery.rs:891`） | 同上一格，预算 `(聊天高/3).clamp(3,16)`（`ui.rs:2981`） | **替换整块消息区**（`clear_area` 后重画，`ui.rs:3324`） |
| 名单 | 一行一只，最多 4 行，超了 `+N more`，窗口跟着选中滚（`:921`） | 同一份名单 | 同一批成员，改按 `report_back_to_session_id` 画成**树**（`:259`） |
| 选中 | **不画**（`marker = ""`） | 行首 `▸ ` + 加粗 | 行首 `▸ ` + 加粗（树行，`:356`） |
| 详情 | 无 | **选中行下面就地插入**（accordion，`:1117` 注释原话 *"expands in place … instead of jumping to a detached pane below"*） | 分隔线下面铺开选中那位的 live card |
| 末尾 | 无 | 一行键位提示（`:1116`） | 无（键位行在头部第 2 行） |

**两条不在图里、但必须知道的事**：

1. **选中用 `Alt+↑/↓`（也收 `Alt+k/j`），不是裸 `↑↓`** —— `swarm_panel_action_for_key` 只认 `Esc` 与 `Alt` 组合，注释写明理由：面板是 **overlay 不是 modal**，裸打字要继续流进输入框（`tui_state.rs:2225-2250`）。
2. **`Esc` 从 ② 和 ③ 都直接回 ①**（`Exit → focused=false, full_page=false`），**不是"退一档"**（`tui_state.rs:2165-2170`）。③ 的键位行写的也是 `esc chat`。

**为什么上下切不会懵**：名册在**每一档都把选中画出来**，而且**窗口跟着选中滚** —— 条是 `start = selected + 1 - shown`（`swarm_gallery.rs:921`），树是 `selected_tree_index - list_budget/2`（`info_widget_swarm_gallery.rs:215`）。选中是同一个索引 `swarm_panel_selected`，③ 用 `session_id` 把它**投影**到树上（`:164-172`，弹窗复用同一份顺序见 `:607`），所以跨档不漂。

## 13. 侧栏页面（side panel pages）（共 9 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `split_view（Split View）` | /splitview 镜像当前聊天并独立滚动 | `crates/jcode-tui/src/tui/app/split_view.rs:8-47` |
| `todos_view（Todos）` | /todos panel 在侧栏显示完整 todo 屏 | `crates/jcode-tui/src/tui/app/todos_view.rs:257` |
| `observe（Observe）` | /observe 只显示最近一次进入上下文的工具调用/结果 | `crates/jcode-tui/src/tui/app/observe.rs:208` |
| `catchup（Catch Up）` | /catchup 展示需关注的已完成会话简报 | `crates/jcode-tui/src/tui/app/catchup.rs:95` |
| `linked-markdown` | 链接/打开的本地 md 文件页 | `crates/jcode-tui/src/tui/app/navigation.rs:314` |
| `plan 页` | /plan 生成的计划卡落为侧栏页 | `side_panel 快照(测试 fixture) crates/jcode-tui/src/tui/ui_pinned_tests.rs；commands_plan.rs:112` |
| `goals 页` | /goals 目标总览与单个 goal 详情 | `jcode-base/src/goal.rs:384,414；/goals 命令` |
| `diagram 面板（pinned diagram）` | pinned 模式下的图表侧栏/顶部面板 | `crates/jcode-tui/src/tui/ui_diagram_pane.rs:779；ui.rs:3374` |
| `file diff 视图` | diff 模式=File 时并排显示文件 diff | `crates/jcode-tui/src/tui/ui_file_diff.rs；ui.rs:3410` |

## 14. info widget（15 种）（共 15 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `Diagrams` | 聊天里的 mermaid/图表预览(右侧,img) | `crates/jcode-tui/src/tui/info_widget.rs:125,1230；ui_diagram_pane.rs:779` |
| `WorkspaceMap` | Niri 风格工作区地图 + 会话瓦片(右侧) | `info_widget.rs:126,189,1247；workspace_map_widget.rs:88` |
| `Overview` | 合并多个小节的一体化概览卡(可分页) | `info_widget.rs:127,1286` |
| `Todos` | 当前会话 todo 列表(可展开,N more) | `info_widget.rs:128；info_widget_todos.rs:519` |
| `UsageLimits` | 订阅额度条(5h/7d/成本) | `info_widget.rs:129；info_widget_usage.rs:9` |
| `KvCache` | KV cache 命中率/读写/tokens | `info_widget.rs:130；info_widget.rs:1577` |
| `MemoryActivity` | memory 管线活动与条目 | `info_widget.rs:131；info_widget_memory_render.rs:5` |
| `ModelInfo` | 运行时模型/provider/effort/tps 行 | `info_widget.rs:132；info_widget_model.rs:26` |
| `Compaction` | 上下文压缩状态卡 | `info_widget.rs:133；info_widget.rs:1546` |
| `BackgroundTasks` | 后台任务行(最多 3 行 + N more) | `info_widget.rs:134；info_widget_swarm_background.rs:50` |
| `GitStatus / changed files` | 改动文件/分支状态 | `info_widget.rs:135；info_widget_git.rs:143` |
| `Commits` | 最近提交 | `info_widget.rs:136；info_widget_commits.rs:59` |
| `SwarmStatus` | swarm 会话坞/成员列表 | `info_widget.rs:137；info_widget_swarm_background.rs:8` |
| `AmbientMode` | 定时/ambient 计划状态(默认禁用) | `info_widget.rs:138,820；info_widget.rs:1795` |
| `Tips` | 「Did you know」提示(默认禁用) | `info_widget.rs:139,828；info_widget_tips.rs:107` |

## 15. 输入带 / 状态带（共 9 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `active/status line（活动行）` | 转圈+当前状态(sending/thinking/streaming/running tool/rate-limited/waiting network/Session token 总量) | `crates/jcode-tui/src/tui/ui_input.rs:774` |
| `queued bar（排队条）` | 逐条列 queued/interleave 待发消息并编号 | `crates/jcode-tui/src/tui/ui_input.rs:509；ui.rs:3191` |
| `swarm strip（swarm 条）` | 侧栏坞占位时上方一行/一列显示成员 chips；聚焦时展开详情 | `crates/jcode-tui/src/tui/ui.rs:2967-2997,3218-3222；info_widget_swarm_gallery.rs:499` |
| `notification line（通知卡）` | 键控/状态通知文字行，多来源拼接 | `crates/jcode-tui/src/tui/ui_input.rs:1647,1939；ui.rs:3194` |
| `inline UI（内联交互块）` | 内联 picker/交互区高度块 | `crates/jcode-tui/src/tui/ui.rs:3195(Constraint inline_block_height)` |
| `input box（输入框）` | 多行输入 + prompt 前缀(>, $, ssh) + send-mode 指示 | `crates/jcode-tui/src/tui/ui_input.rs:415,2444` |
| `facts line（事实行/overscroll）` | 输入框下方右对齐的目录/分支/git/上下文/鉴权/provider/模型/effort | `crates/jcode-tui/src/tui/ui_input.rs:1946；ui.rs:3461` |
| `pinned todos / background task rows` | 顶部钉住的 todo 带 + 其下最多两行后台任务 | `crates/jcode-tui/src/tui/ui_viewport.rs:1393；app/state_ui_messages.rs:207-217；app.rs:1426` |
| `todo card（聊天内联 todo 卡）` | Alt+X / /todos 在聊天追加可实时更新的 todo 卡 | `crates/jcode-tui/src/tui/app/todos_view.rs:20；ui_messages.rs(role=todos)` |

## 16. 状态条字段与压缩阶梯（事实行）（共 9 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `dir` | 工作目录(~ 相对,末 2 段) | `crates/jcode-tui/src/tui/ui_input.rs:1988,2330` |
| `branch` | git 分支(>24 字符截断) | `ui_input.rs:1989,2230` |
| `git status` | ~改 +暂 ?未跟踪 ↑前 ↓后 | `ui_input.rs:1990,2245` |
| `context usage` | used/limit + 色条 + 百分比 | `ui_input.rs:1991,2060-2100` |
| `auth` | OAuth / API key 标签 | `ui_input.rs:1992,2102` |
| `provider` | provider 显示名(去凭据字样) | `ui_input.rs:1993,2106` |
| `model` | 模型名(粉色加粗) | `ui_input.rs:1994,2110` |
| `effort` | 推理力度短标签 | `ui_input.rs:1995,2115` |
| `OVERSCROLL_LADDER (10 级)` | 隐藏 auth→压 git→压 context→截 branch→隐藏 provider→context 仅%→隐藏 git→隐藏 branch→去 effort→dir 仅末段；dir/model/context 永不隐藏只缩短 | `crates/jcode-tui/src/tui/ui_input.rs:2016-2050` |

## 17. 模式与开关（共 19 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `centered mode（对齐）` | Alt+C 切换居中布局；/alignment 持久化 | `crates/jcode-tui/src/tui/keybind.rs:305；commands(alignment)` |
| `queue mode` | Ctrl+Tab/Ctrl+T 切换；决定 Enter/alternate-Enter 是排队还是插队 | `crates/jcode-tui/src/tui/app/input.rs:2097` |
| `copy/selection mode` | Alt+Y 切换选择复制 | `crates/jcode-tui/src/tui/app/input.rs:2713` |
| `typing scroll lock` | Alt+S 锁定打字时滚动 | `crates/jcode-tui/src/tui/app/input.rs:2472-2476` |
| `auto-poke` | Ctrl+P 开/关未完成 todo 自动续跑 | `crates/jcode-tui/src/tui/app/input.rs:2421-2425` |
| `diff display mode` | Alt+G 循环 Off/Inline/Pinned/File | `crates/jcode-tui/src/tui/app/navigation.rs:1246-1252` |
| `diagram display mode / 位置` | Alt+T 侧/顶；Alt+Shift+M 显示隐藏 | `crates/jcode-tui/src/tui/app/input.rs:2461,2455` |
| `side panel 三态` | Alt+M 循环 split/fullscreen/hidden；/splitview 亦影响 | `crates/jcode-tui/src/tui/app/input.rs:2465；ui.rs:2815` |
| `info widget 开关` | Alt+I 整组 widget 开/关 | `crates/jcode-tui/src/tui/app/input.rs:2478-2486` |
| `swarm panel view` | Alt+N 循环 Chat/Controls/FullPage(仅 inline spawn 模式) | `crates/jcode-tui/src/tui/app/tui_state.rs:2075；app/input.rs:2506` |
| `observe mode` | /observe 开/关 transient 侧栏 observe 页(不落盘) | `crates/jcode-tui/src/tui/app/observe.rs:38-47` |
| `split view mode` | /splitview 开/关聊天镜像页 | `crates/jcode-tui/src/tui/app/split_view.rs:12-22` |
| `todos view mode` | /todos on/off/panel/pin 侧栏 todo 屏 / 顶部钉住 | `crates/jcode-tui/src/tui/app/todos_view.rs:16,147` |
| `voice input（Nari）` | Ctrl+Space 开始/停止录音，再按发送，Esc 取消；转写裹 <transcription> | `crates/jcode-tui/src/tui/app/voice_input.rs；keybind.rs:646` |
| `dictation（外部听写）` | [dictation].key 触发外部命令并把转写注入 | `crates/jcode-tui/src/tui/app/dictation.rs；keybind.rs:612` |
| `image placeholder` | 粘贴/拖入图片插入 `[image N]` 占位并挂 pending_images，Enter 提交时并入 | `crates/jcode-tui/src/tui/app/input.rs:2984-2993,784-863` |
| `telemetry 级别` | 三档 everything/no-prompts(nothing)；/telemetry 改，onboarding 页设 | `crates/jcode-tui/src/tui/app/onboarding_flow.rs:57-97；app/commands.rs:3736` |
| `fast mode / transport / 每个 widget 可见性` | /fast service_tier=priority；/transport auto/https/websocket；widget per-kind 开关 | `crates/jcode-tui/src/tui/info_widget.rs:926,973；handler 在 app/commands*` |
| `theme / emoji 偏好 / 输出样式` | /theme 与 emoji 偏好改写渲染样式 | `crates/jcode-tui/src/tui/ui_theme.rs；ui/output_style.rs` |

## 18. 鼠标与终端交互（共 5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `滚轮滚动` | 按目标(changelog/help/model-status/session-picker-preview/list/聊天)路由的滚轮 | `crates/jcode-tui/src/tui/app/navigation.rs:1393-1462` |
| `拖拽选择 + 松开复制` | 选择高亮并复制到剪贴板(overlay 与聊天视口共用) | `crates/jcode-tui/src/tui/ui/copy_selection.rs；ui_overlays.rs:100` |
| `点击图片预览关闭` | 鼠标左键抬起关闭预览 | `crates/jcode-tui/src/tui/app/navigation.rs:1404` |
| `修饰键徽标(macOS Option/Shift)` | 按下 Option/Shift 时显示 [⌥][⇧][key] 复制徽标 | `crates/jcode-tui/src/tui/app/input.rs:3326-3378` |
| `终端键位冲突诊断(/keys)` | 对比机器上终端/系统热键与 jcode 绑定报冲突 | `crates/jcode-setup-hints/src/keymap/{conflicts.rs:282,report.rs:12}` |

## 19. 文档与实现的漂移（payload cross_check 原样抄录）（共 14 条）

### 代码里有、文档未说明（code_only_unspecified，10 条）

| 名字 | 一句话 | 出处 |
|---|---|---|
| `/stop` | /cancel 别名，未登记 | `crates/jcode-tui/src/tui/app/commands.rs:838` |
| `/mission` | disabled | `crates/jcode-tui/src/tui/app/commands.rs:2669` |
| `/goal` | disabled；与已登记的 /goals 不同 | `crates/jcode-tui/src/tui/app/commands.rs:2670` |
| `/hosted` | 未登记 | `auth_account_commands.rs:78/84` |
| `/exit` | 仅 SSH 登录取消语境 | `crates/jcode-tui/src/tui/app/auth_remote.rs:447` |
| `/theme` | 只在 SSH 阻断表；未找到本地 handler | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:45` |
| `/open /file /new-terminal` | 只在阻断表；未找到本地 handler | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:59/60/62` |
| `/permissions /permission` | 只在阻断表；未找到本地 handler | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:31/32` |
| `/debug-fixture` | debug.rs:581 处理 debug-fixture gmail-draft | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:87` |
| `/stats` | productivity.rs:17 处理 | `crates/jcode-tui/src/tui/app/commands_dispatch.rs:79` |

### 文档里有、代码里没有（docs_without_code，2 条）

| 名字 | 一句话 | 出处 |
|---|---|---|
| `/ambient` | AMBIENT_MODE.md 称显式 `/ambient` 命令；TUI 无此斜杠命令，仅 CLI `jcode ambient` | `docs/AMBIENT_MODE.md:606` |
| `/account claude`、`/account switch`、`/account openai`、`/account default-provider`、`/account default-model`、`/initiatives show`、`/goals show` 等 | `command_accepts_args` 中列出的子串形式，非独立命令 | `state_ui_input_helpers.rs:1760-1818` |

### 代码里有、文档没写（hidden 别名，code_without_docs，1 类）

| 名字 | 一句话 | 出处 |
|---|---|---|
| `/model-status /todo /color /commit-and-push /cut-release /commit-push-release /thinking /reasoning /clear-view /keybindings /split /resume-all` | hidden 别名不在 `/help` 手写段（由自动 More commands 段兜底） | `ui_overlays.rs:420-440` |
| `/z /zz /zzz /zstatus` | secret premium 命令，完全不出现 | `state_ui_input_helpers.rs:235-238` |

## 20. CLI 子命令自己的 flag（共 208 条）

> 数法：`src/cli/args.rs` 是唯一 clap 定义处（grep `#[arg(` 在 `src/cli/` 仅命中 args.rs），逐 `#[arg(long/short)]` 与所属 enum variant 配对：186 flag（顶层 35 子命令中 17 个有自有 flag=65；嵌套 53 子命令中 35 个有自有 flag=121）+ 22 位置参数（顶层 11 + 嵌套 11）= 208。不含 §8 已列的 26 条全局标志。payload groups 因 `jcode browser` 无自有 flag 未成组，其 2 条位置参数（action/browser）按 `src/cli/args.rs:407-416` 补入。flatten 结构 CloudMoveTarget(host/remote_binary/transport)、JadeCloudOptions(user_id/profile/region/helper) 在使用它们的每个子命令下各展开一次。隐藏 flag（hide=true）在 what 标注：serve 3 条、setup-hotkey 3 条、cloud receive/activate/export 各指出的 flag 等；仍计入 186。**不重复** §8 的 26 个全局标志。

### jcode serve（自有 flag 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--temporary-server` | 内部：把本 server 标为临时，owner 退出即自清（隐藏） | `src/cli/args.rs:151` |
| `--owner-pid <PID>` | 内部：临时 server 的属主进程 pid（隐藏） | `src/cli/args.rs:155` |
| `--temp-idle-timeout-secs <SECS>` | 内部：临时 server 空闲关机超时秒数（隐藏） | `src/cli/args.rs:159` |
| `--server-name <NAME>` | 给 server 设稳定显示名，连接端与 session 选择器可见 | `src/cli/args.rs:166` |

### jcode run [message]（自有 flag 2 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出机器可读 JSON 结果而非流式文本（与 --ndjson 互斥） | `src/cli/args.rs:185` |
| `--ndjson` | 流式期间输出逐行 JSON 事件（与 --json 互斥） | `src/cli/args.rs:189` |
| `<message>（位置参数）` | 要发送的消息 | `src/cli/args.rs:192` |

### jcode login [PROVIDER]（自有 flag 14 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-a/--account <LABEL>` | 多账号标签（已存标签自动编号） | `src/cli/args.rs:207` |
| `--no-browser（别名 --headless）` | 不开本地浏览器，显示二维码供另一设备登录（SSH 用） | `src/cli/args.rs:211` |
| `--print-auth-url` | 打印脚本友好授权 URL 并暂存登录态待后续完成 | `src/cli/args.rs:215` |
| `--callback-url <URL>` | 用完整回调 URL/查询串完成已打印的授权流程 | `src/cli/args.rs:219` |
| `--auth-code <CODE>` | 用 provider 授权码完成已打印的授权流程 | `src/cli/args.rs:223` |
| `--json` | 输出机器可读 JSON（脚本化登录流程） | `src/cli/args.rs:227` |
| `--complete` | 续跑无需回调/码输入的脚本化登录流程 | `src/cli/args.rs:231` |
| `--flow-id <ID>` | 用 1-64 位 ASCII 隔离临时登录状态 | `src/cli/args.rs:235` |
| `--cancel` | 仅取消该 provider 待定流程，不删已存凭证（需 --flow-id） | `src/cli/args.rs:239` |
| `--no-validate` | 保存凭证后跳过登录后实机校验（离线/CI 用） | `src/cli/args.rs:244` |
| `--google-access-tier <TIER>` | 非交互流程 Google 访问档位 full/readonly（默认 full） | `src/cli/args.rs:248` |
| `--api-base <URL>` | OpenAI 兼容 API base URL（配合兼容 provider/profile） | `src/cli/args.rs:252` |
| `--api-key <KEY>` | OpenAI 兼容 API key；缺省时安全提示输入 | `src/cli/args.rs:256` |
| `--api-key-env <VAR>` | 存放/读取 OpenAI 兼容 API key 的环境变量名 | `src/cli/args.rs:260` |
| `<PROVIDER>（位置参数，clap id=login_provider）` | 要登录的 provider（等价本命令的 --provider） | `src/cli/args.rs:203` |

### jcode version（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出构建/版本信息 | `src/cli/args.rs:279` |

### jcode usage（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出用量额度 | `src/cli/args.rs:286` |

### jcode self-dev（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--build` | 启动前先构建并测试新的 canary 版本 | `src/cli/args.rs:298` |

### jcode debug [command] [arg]（自有 flag 3 条 + 位置参数 2）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-S/--session <ID>` | 指定目标 session | `src/cli/args.rs:313` |
| `-s/--socket <PATH>` | 连接指定 server socket 路径 | `src/cli/args.rs:317` |
| `-w/--wait` | 等待响应完成（message 命令用） | `src/cli/args.rs:321` |
| `<command>（位置参数，默认 help）` | 要跑的 debug 命令（list/start/sessions/message/tool/state/history 等） | `src/cli/args.rs:305` |
| `[arg]（位置参数，默认空）` | 该 debug 命令的可选参数 | `src/cli/args.rs:309` |

### jcode pair（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--list` | 列出已配对设备而非生成配对码 | `src/cli/args.rs:352` |
| `--revoke <NAME\|ID>` | 按名字/ID 吊销已配对设备 | `src/cli/args.rs:356` |

### jcode transcript [text]（自有 flag 2 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--mode <MODE>` | 转录在 Jcode 内的应用方式 insert/append/replace/send（默认 send） | `src/cli/args.rs:369` |
| `-S/--session <ID>` | 指定 live session 而非活动 TUI | `src/cli/args.rs:373` |
| `[text]（位置参数）` | 转录文本；省略则从 stdin 读 | `src/cli/args.rs:367` |

### jcode dictate（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--type` | 把转录键入当前焦点 app 而非发给 jcode | `src/cli/args.rs:380` |

### jcode setup-hotkey（自有 flag 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--listen-macos-hotkey` | 内部：作为 macOS 热键监听进程运行（隐藏） | `src/cli/args.rs:387` |
| `--notify-cli-launch <CLI>` | 内部：CLI SessionStart hook 显示限流快捷键提醒（隐藏） | `src/cli/args.rs:391` |
| `--listen-windows-hotkey` | 内部：作为 Windows 热键监听进程运行（隐藏） | `src/cli/args.rs:395` |
| `--uninstall` | 移除已安装的平台全局热键监听器 | `src/cli/args.rs:399` |

### jcode browser <action> [browser]（位置参数 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `<action>（位置参数，默认 setup）` | 浏览器自动化动作：setup/status/detect | `src/cli/args.rs:409` |
| `[browser]（位置参数）` | 目标浏览器：auto/firefox/chrome/chromium/edge/brave/safari | `src/cli/args.rs:414` |

### jcode replay <session>（自有 flag 11 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--swarm` | 同步多窗格一起重放相关 swarm 会话 | `src/cli/args.rs:423` |
| `--export` | 导出时间线为 JSON 而非播放 | `src/cli/args.rs:427` |
| `--speed <F>` | 播放速度倍率（默认 1.0） | `src/cli/args.rs:431` |
| `--timeline <PATH>` | 用编辑过的 timeline JSON 覆盖 session 时序 | `src/cli/args.rs:435` |
| `--auto-edit` | 自动压缩工具等待与提示之间的间隔 | `src/cli/args.rs:439` |
| `--video [PATH]` | 导出视频文件（无路径则自动命名） | `src/cli/args.rs:443` |
| `--cols <N>` | 视频宽度列数（默认 120） | `src/cli/args.rs:447` |
| `--rows <N>` | 视频高度行数（默认 40） | `src/cli/args.rs:451` |
| `--fps <N>` | 视频帧率（默认 60） | `src/cli/args.rs:455` |
| `--centered` | 强制居中布局（覆盖配置；与 --no-centered 互斥） | `src/cli/args.rs:459` |
| `--no-centered` | 强制左对齐布局（覆盖配置；与 --centered 互斥） | `src/cli/args.rs:463` |
| `<session>（位置参数）` | session ID/名或 session JSON 文件路径 | `src/cli/args.rs:419` |

### jcode provider-test-coverage [PROVIDER] [MODEL]（自有 flag 2 条 + 位置参数 2）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--coverage-file <PATH>` | 从该 JSON 文件读覆盖而非默认实机台账 | `src/cli/args.rs:483` |
| `--coverage-limit <N>` | 全量摘要最多列出的 provider/model 对数（0=全部） | `src/cli/args.rs:487` |
| `[PROVIDER]（位置参数）` | 要查询的 provider；省略则打印全量覆盖摘要 | `src/cli/args.rs:475` |
| `[MODEL]（位置参数）` | 要查询的模型；仅在给了 PROVIDER 时用 | `src/cli/args.rs:479` |

### jcode provider-doctor <PROVIDER>（自有 flag 2 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--tier <TIER>` | 检查深度 offline/catalog/full（默认 catalog） | `src/cli/args.rs:501` |
| `--json` | 输出 JSON 报告（脚本用） | `src/cli/args.rs:505` |
| `<PROVIDER>（位置参数，clap id=doctor_provider）` | 要诊断的 OpenAI 兼容 provider id | `src/cli/args.rs:496` |

### jcode auth-test（自有 flag 11 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--login` | 校验前先跑 provider 登录流程（交互/浏览器） | `src/cli/args.rs:512` |
| `--all-configured` | 测所有已配置的受支持 provider 而非仅 --provider | `src/cli/args.rs:516` |
| `--no-smoke` | 跳过 provider 运行时 smoke 提示 | `src/cli/args.rs:520` |
| `--no-tool-smoke` | 跳过带工具的运行时 smoke 提示 | `src/cli/args.rs:524` |
| `--prompt <TEXT>` | 自定义 smoke 提示（默认要 AUTH_TEST_OK） | `src/cli/args.rs:528` |
| `--json` | 输出 JSON 报告而非人读文本 | `src/cli/args.rs:532` |
| `--output <PATH>` | 把完整 auth-test 报告 JSON 写入文件 | `src/cli/args.rs:536` |
| `--coverage` | 显示严格实机 provider/model E2E 覆盖而非跑测试 | `src/cli/args.rs:540` |
| `--context-audit` | 拉实机模型目录并校验各模型 context window | `src/cli/args.rs:544` |
| `--coverage-file <PATH>` | 从该 JSON 文件读覆盖（需 --coverage） | `src/cli/args.rs:548` |
| `--coverage-limit <N>` | 文本覆盖报告最多显示的未覆盖对数（默认 50） | `src/cli/args.rs:552` |

### jcode menubar（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--once` | 打印一次当前计数后退出（不建菜单栏项） | `src/cli/args.rs:566` |
| `--json` | 以 JSON 输出当前计数后退出（与 --once 互斥） | `src/cli/args.rs:570` |

### jcode api-bridge（自有 flag 2 条；variant 标 cfg(unix)）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--api-socket <PATH>` | API socket 监听路径（默认 $XDG_RUNTIME_DIR/jcode-api.sock） | `src/cli/args.rs:589` |
| `--stdio` | 在 stdin/stdout 上服务单个 API 连接（SSH SDK 用；与 --api-socket 互斥） | `src/cli/args.rs:594` |

### jcode telemetry status（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非人读文本输出遥测状态 | `src/cli/args.rs:604` |

### jcode account login（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--no-browser（别名 --headless）` | 不自动开浏览器，改为打印公开审批 URL | `src/cli/args.rs:618` |

### jcode server start（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:643` |

### jcode server promote [version]（自有 flag 1 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:660` |
| `[version]（位置参数）` | 要 promote 的已安装版本（默认当前通道） | `src/cli/args.rs:654` |

### jcode server reload（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--force` | 即使已是最新二进制也重载 | `src/cli/args.rs:673` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:677` |

### jcode server stop（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--force` | 确认要终止 daemon（会丢 live session） | `src/cli/args.rs:689` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:693` |

### jcode cloud move（自有 flag 5 条 + flatten CloudMoveTarget 3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 指定会话 ID/名（默认本命令所在会话） | `src/cli/args.rs:711` |
| `--host <HOST>` | (flatten) 云主机 SSH 别名（默认 [cloud] host 或 $JCODE_CLOUD_HOST） | `src/cli/args.rs:789` |
| `--remote-binary <BIN>` | (flatten) 远端 jcode 二进制名/路径（默认 jcode） | `src/cli/args.rs:792` |
| `--transport <CMD>` | (flatten) 替代 `ssh <host>` 的本地命令（测试/自定义传输，隐藏） | `src/cli/args.rs:797` |
| `--allow-active` | 允许会话进行中迁移（agent 自身跑 /cloud 时） | `src/cli/args.rs:716` |
| `--dry-run` | 只准备并校验，不把所有权交给云主机 | `src/cli/args.rs:719` |
| `--attach` | 迁移成功后把本终端接到云会话 | `src/cli/args.rs:722` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:724` |

### jcode cloud return（自有 flag 4 条 + flatten CloudMoveTarget 3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 指定会话 | `src/cli/args.rs:731` |
| `--host <HOST>` | (flatten) 云主机 SSH 别名 | `src/cli/args.rs:789` |
| `--remote-binary <BIN>` | (flatten) 远端 jcode 二进制名/路径 | `src/cli/args.rs:792` |
| `--transport <CMD>` | (flatten) 替代 ssh 的本地命令（隐藏） | `src/cli/args.rs:797` |
| `--refs-only` | 只带回 refs（refs/jcode-cloud/<session>/*）不动工作树 | `src/cli/args.rs:736` |
| `--attach` | 返回后在本终端恢复该会话 | `src/cli/args.rs:739` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:741` |

### jcode cloud where（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 指定会话 | `src/cli/args.rs:747` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:749` |

### jcode cloud attach（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 指定云主机上的会话 | `src/cli/args.rs:755` |

### jcode cloud receive（自有 flag 1 条；隐藏）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:762` |

### jcode cloud activate（自有 flag 2 条；隐藏）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 会话 ID | `src/cli/args.rs:769` |
| `--epoch <N>` | 提交 epoch | `src/cli/args.rs:771` |

### jcode cloud export（自有 flag 2 条；隐藏）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--session <ID>` | 会话 ID | `src/cli/args.rs:779` |
| `--epoch <N>` | epoch | `src/cli/args.rs:781` |

### jcode cloud sessions configure（自有 flag 7 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--api-base <URL>` | Jade Session API base URL | `src/cli/args.rs:806` |
| `--api-token <TOKEN>` | Jade API bearer token（建议改用 --api-token-env） | `src/cli/args.rs:810` |
| `--api-token-env <VAR>` | 从该环境变量读 Jade token（与 --api-token 互斥） | `src/cli/args.rs:814` |
| `--api-token-id <ID>` | 可选 Jade token id，如 dev-admin | `src/cli/args.rs:818` |
| `--user-id <ID>` | 未传 --user-id 命令的默认 Jade 用户 id | `src/cli/args.rs:822` |
| `--helper <PATH>` | 默认私有 Jade session helper 路径 | `src/cli/args.rs:826` |
| `--clear` | 删除已保存的 cloud sessions 配置 | `src/cli/args.rs:830` |

### jcode cloud sessions status（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非人读文本输出（不打印密钥） | `src/cli/args.rs:837` |

### jcode cloud sessions upload <session_file>（自有 flag 1 + jade 4 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--raw` | 不经 Jade 脱敏直传 | `src/cli/args.rs:847` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id（默认 dev） | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |
| `<session_file>（位置参数）` | 本地 Jcode session JSON 文件路径 | `src/cli/args.rs:843` |

### jcode cloud sessions upload-latest（自有 flag 2 + jade 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--sessions-dir <DIR>` | 本地会话 JSON 目录（默认 ~/.jcode/sessions） | `src/cli/args.rs:857` |
| `--raw` | 不经 Jade 脱敏直传 | `src/cli/args.rs:861` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |

### jcode cloud sessions sync（自有 flag 9 + jade 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--sessions-dir <DIR>` | 本地会话目录（默认 ~/.jcode/sessions） | `src/cli/args.rs:871` |
| `--since-days <N>` | 只考虑近 N 天修改的会话（--all 时忽略） | `src/cli/args.rs:875` |
| `--all` | 不限时间同步所有匹配会话 | `src/cli/args.rs:879` |
| `--max <N>` | 本次最多上传会话数（默认 50） | `src/cli/args.rs:883` |
| `--min-interval-mins <N>` | 上次同步距今不足 N 分钟则跳过（cron/定时器） | `src/cli/args.rs:887` |
| `--raw` | 不经 Jade 脱敏直传 | `src/cli/args.rs:891` |
| `--dry-run` | 只显示将上传内容，不真传不记状态 | `src/cli/args.rs:895` |
| `--force` | 即使本地状态称未变更也重传 | `src/cli/args.rs:899` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:903` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |

### jcode cloud sessions list（自有 flag 2 + jade 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--limit <N>` | 最多显示的会话数（默认 25） | `src/cli/args.rs:913` |
| `--json` | 用 JSON 而非人读文本输出 | `src/cli/args.rs:917` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |

### jcode cloud sessions verify <session_id>（jade 4 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |
| `<session_id>（位置参数）` | 要校验的会话 ID | `src/cli/args.rs:925` |

### jcode cloud sessions dashboard（自有 flag 4 + jade 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--limit <N>` | 最多包含的会话数（默认 100） | `src/cli/args.rs:936` |
| `--output <PATH>` | 写出 dashboard HTML 的路径（默认临时文件） | `src/cli/args.rs:940` |
| `--open` | 用默认浏览器打开生成的 dashboard | `src/cli/args.rs:944` |
| `--with-view` | 额外下载各会话并把行链到本地单会话查看器 | `src/cli/args.rs:948` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |

### jcode cloud sessions view <session_id>（自有 flag 3 + jade 4 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--format <FMT>` | 输出格式 summary/json/html（默认 summary） | `src/cli/args.rs:961` |
| `--output <PATH>` | --format html 时的输出路径 | `src/cli/args.rs:965` |
| `--open` | --format html 时打开生成文件 | `src/cli/args.rs:969` |
| `--user-id <ID>` | (jade) 传给 dev helper 的 Jade 用户 id | `src/cli/args.rs:980` |
| `--profile <P>` | (jade) 私有 helper 用的 AWS CLI profile | `src/cli/args.rs:984` |
| `--region <R>` | (jade) 私有 helper 用的 AWS region | `src/cli/args.rs:988` |
| `--helper <PATH>` | (jade) 私有 Jade session helper 路径 | `src/cli/args.rs:992` |
| `<session_id>（位置参数）` | 要查看的会话 ID | `src/cli/args.rs:957` |

### jcode restart save（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--auto-restore` | 下次裸 `jcode` 启动时自动恢复该重启快照 | `src/cli/args.rs:1018` |

### jcode model list（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出 | `src/cli/args.rs:1034` |
| `--verbose` | 列表前显示 provider/选择摘要 | `src/cli/args.rs:1038` |

### jcode session rename <session> [name]（自有 flag 2 条 + 位置参数 2）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--clear` | 清除自定义会话名/标题（与 name 互斥） | `src/cli/args.rs:1055` |
| `--json` | 用 JSON 而非人读输出 | `src/cli/args.rs:1059` |
| `<session>（位置参数）` | 会话 ID 或可记短名（如 fox） | `src/cli/args.rs:1046` |
| `[name]（位置参数，--clear 时非必填）` | 新的会话名/标题 | `src/cli/args.rs:1051` |

### jcode provider list（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出 | `src/cli/args.rs:1069` |

### jcode provider current（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出 | `src/cli/args.rs:1076` |

### jcode provider add <name>（自有 flag 15 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--base-url <URL>（别名 --api-base）` | OpenAI 兼容 API base URL | `src/cli/args.rs:1086` |
| `-m/--model <ID>` | 该 profile 的默认模型 id | `src/cli/args.rs:1090` |
| `--context-window <N>` | 可选模型 context window（tokens） | `src/cli/args.rs:1094` |
| `--api-key-env <VAR>` | 含 API key 的环境变量名（与 --no-api-key 互斥） | `src/cli/args.rs:1098` |
| `--api-key <KEY>` | 存入 jcode 私有 provider env 文件的 API key | `src/cli/args.rs:1102` |
| `--api-key-stdin` | 从 stdin 读 API key 并存入私有 env 文件 | `src/cli/args.rs:1106` |
| `--no-api-key` | 配置为无 API key/无认证的 provider | `src/cli/args.rs:1110` |
| `--auth <STYLE>` | API key 认证风格 bearer/api-key/none | `src/cli/args.rs:1114` |
| `--auth-header <NAME>` | --auth api-key 时用的 header 名（默认 api-key） | `src/cli/args.rs:1118` |
| `--env-file <NAME>` | 存 API key 的私有 env 文件名 | `src/cli/args.rs:1122` |
| `--set-default（别名 --default）` | 把该 profile 设为启动默认 provider/model | `src/cli/args.rs:1126` |
| `--overwrite` | 覆盖同名已存在的 profile | `src/cli/args.rs:1130` |
| `--provider-routing` | 允许 OpenRouter 式网关的 provider 路由特性 | `src/cli/args.rs:1134` |
| `--model-catalog` | 从 provider /models 端点拉取/列出模型 | `src/cli/args.rs:1138` |
| `--json` | 用 JSON 而非人读设置输出 | `src/cli/args.rs:1142` |
| `<name>（位置参数）` | profile 名（配合 --provider-profile 与 config 默认） | `src/cli/args.rs:1082` |

### jcode auth import（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--stdin（required）` | 从 stdin（绝不用命令行参数）读私有凭证信封 | `src/cli/args.rs:1152` |
| `--json` | 输出不含密钥的 JSON 确认 | `src/cli/args.rs:1156` |

### jcode auth status（自有 flag 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 用 JSON 而非纯文本输出 | `src/cli/args.rs:1162` |

### jcode auth doctor [PROVIDER]（自有 flag 2 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--validate` | 诊断时对已配置 provider 跑登录后实机校验 | `src/cli/args.rs:1172` |
| `--json` | 用 JSON 而非纯文本输出 | `src/cli/args.rs:1176` |
| `[PROVIDER]（位置参数，clap id=auth_provider）` | 可选：聚焦诊断某个 provider id/别名 | `src/cli/args.rs:1168` |

### jcode memory list（自有 flag 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-s/--scope <SCOPE>` | 按 scope 过滤 project/global/all（默认 all） | `src/cli/args.rs:1201` |
| `-t/--tag <TAG>` | 按 tag 过滤 | `src/cli/args.rs:1205` |

### jcode memory search <query>（自有 flag 1 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-s/--semantic` | 用 Jev 相关性判定替代本地关键词搜索（需 Jev 权限） | `src/cli/args.rs:1215` |
| `<query>（位置参数）` | 搜索查询 | `src/cli/args.rs:1209` |

### jcode memory export <output>（自有 flag 1 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-s/--scope <SCOPE>` | 导出 scope project/global/all（默认 all） | `src/cli/args.rs:1225` |
| `<output>（位置参数）` | 输出文件路径 | `src/cli/args.rs:1220` |

### jcode memory import <input>（自有 flag 2 条 + 位置参数 1）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-s/--scope <SCOPE>` | 导入 scope project/global（默认 project） | `src/cli/args.rs:1235` |
| `--overwrite` | 覆盖同 ID 的已有记忆 | `src/cli/args.rs:1239` |
| `<input>（位置参数）` | 输入文件路径 | `src/cli/args.rs:1230` |

## 21. command_accepts_args 白名单（共 55 条）

> 数法：`crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1759-1818` 的 `matches!(cmd.trim(), ...)`，条目 1762-1816 共 55 条（42 单 token + 13 多 token）。**重要澄清**：该函数是纯 **bool 白名单**，**不编码任何 per-command 参数形状**；它只决定 Tab 补全唯一命中后是否追加尾空格（调用点 :1633/1652/1693/1710）。因按整串 trim 后全等比较（1759-1761），输入 `/account claude foo` 不命中；故「命令→参数形状」无法从本函数静态读出，只能读出「该命令接受参数(yes)」。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/help` | 接受参数：补全该命令后自动追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1762` |
| `/?` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1763` |
| `/btw` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1764` |
| `/fork` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1765` |
| `/git` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1766` |
| `/transcript` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1767` |
| `/observe` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1768` |
| `/todos` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1769` |
| `/splitview` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1770` |
| `/split-view` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1771` |
| `/model` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1772` |
| `/agents` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1773` |
| `/effort` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1774` |
| `/fast` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1775` |
| `/transport` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1776` |
| `/login` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1777` |
| `/auth` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1778` |
| `/account` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1779` |
| `/account claude（多 token 形式）` | 接受参数：整串全等才命中，补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1780` |
| `/account switch（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1781` |
| `/account openai（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1782` |
| `/account openai-compatible（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1783` |
| `/account default-provider（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1784` |
| `/account default-model（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1785` |
| `/account claude switch（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1786` |
| `/account claude remove（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1787` |
| `/account openai switch（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1788` |
| `/account openai remove（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1789` |
| `/usage` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1790` |
| `/reset` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1791` |
| `/subscription` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1792` |
| `/poke` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1793` |
| `/memory` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1794` |
| `/test` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1795` |
| `/initiatives` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1796` |
| `/initiatives show（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1797` |
| `/goals` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1798` |
| `/goals show（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1799` |
| `/swarm` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1800` |
| `/plan` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1801` |
| `/improve` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1802` |
| `/refactor` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1803` |
| `/rewind` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1804` |
| `/compact` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1805` |
| `/compact mode（多 token 形式）` | 接受参数：整串全等才命中 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1806` |
| `/alignment` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1807` |
| `/compact-notifications` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1808` |
| `/show-agentgrep-output` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1809` |
| `/reasoning` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1810` |
| `/thinking` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1811` |
| `/thinking-display` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1812` |
| `/config` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1813` |
| `/save` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1814` |
| `/rename` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1815` |
| `/cache` | 接受参数：补全后追加尾空格 | `crates/jcode-tui/src/tui/app/state_ui_input_helpers.rs:1816` |

## 22. 远端专属键位与界面（共 85 条）

> 数法：G1 = `crates/jcode-tui/src/tui/app/remote/key_handling.rs` 的 `handle_remote_key_internal`(:269-2758) 内逐分支（payload 组头记 58，实列 63）；G1b = `crates/jcode-tui/src/tui/app/remote.rs` 的 `handle_disconnected_key_internal`(:1956-2130) 逐分支（payload 组头记 12，实列 11）；G1c = `crates/jcode-tui/src/tui/app/remote/server_events.rs` 中直接影响 UI 的远程分支代表性抽取（11）。远端两条互斥键位路径：在线主路径 G1 / 断线路径 G1b；G1c 为 server 事件驱动的远端专属界面。

### G1. 远端(remote)专属键位 · 在线主路径（63 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| SSH 登录键 / 原生 /login Enter | 远端 SSH 会话中捕获登录流程按键与输入 /login | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:280,284` |
| Alt+5(或 Cmd+5) 重置 onboarding 模拟 | 重置首启模拟器状态 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:296` |
| 更新模拟快捷键 | 触发更新模拟(自测用) | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:299` |
| onboarding 模拟键 / 继续提示键 | 模拟器激活时独占全部按键；继续提示 y/n | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:305,311` |
| prompt history search 键 | 打开并操作历史搜索浮层 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:314` |
| scroll overlay 键 | 滚动全屏 overlay(/help、changelog 等) | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:317` |
| session picker overlay 键 | /resume 会话选择器浮层按键；SSH 下被拦截 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:321` |
| login picker overlay 键 | 登录选择器浮层按键 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:325` |
| account picker overlay 键 | 账号选择器浮层按键(路由到 remote) | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:329` |
| inline interactive picker 键(+subagent 模型 Enter) | 内联选择器导航/提交；Enter 可设子代理模型 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:336-348` |
| inline interactive preview 键(Up/Down/PgUp/PgDn) | 模型选择器预览态上下翻 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:352,930` |
| Ctrl+O / Ctrl+N(模型 picker 预览) | 预览态设默认模型 / 切换收藏 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:368` |
| 可见选区复制快捷键(Ctrl+A 复制视口) | 复制聊天视口附近内容 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:375` |
| 下一提示路由到新会话键 | 切换下条 prompt 在分会话运行 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:378` |
| 听写(dictation)键 | 触发外部语音转写注入 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:384` |
| new_terminal 键(SSH 下禁用) | 新开终端 jcode 会话 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:398` |
| fallback_switch 键(接接受错误回退) | 切换模型/鉴权方式并重发失败回合 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:411` |
| merge offer 键 | 接受分叉更新合并提议 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:418` |
| open_resume 键(SSH 下禁用) | 打开 /resume 会话选择器 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:428` |
| workspace 导航键(Alt+H/J/K/L) | 按方向切到相邻 workspace 会话 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:434` |
| auto_poke 开关(Ctrl+P) | 开/关自动催办 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:438` |
| copy_selection 模式开关(Alt+Y) | 进入鼠标划选复制模式 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:475` |
| diagram pane 显隐(Alt+Shift+M) | 显示/隐藏图表面板 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:480` |
| side panel 开关(Alt+M) | 开/关/全屏侧栏 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:485` |
| info widget 开关(Alt+I) | 开/关信息小部件 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:490` |
| swarm panel 视图循环(Alt+N) | chat→内联控制→全页 swarm 循环 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:513` |
| swarm panel 内键 | swarm 焦点态选择/弹出/提示/Esc | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:531` |
| diagram pane 位置切换(Alt+T) | 侧/顶切换图表面板 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:536` |
| 模型切换键(Ctrl+Tab / Ctrl+Shift+Tab) | 远程切下一/上一个模型 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:541` |
| 推理强度切换键 | 远程升降 reasoning effort | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:546` |
| macOS Option+方向 强度备用键 | RunningTool 外的 Option+箭头调强度 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:551` |
| typing scroll lock 开关(Alt+S) | 打字时锁定滚动 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:558` |
| todo card 开关(Alt+X) | 显示/收起会话待办卡 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:562` |
| centered 模式开关 | 切换居中布局 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:569,696` |
| diagram 焦点键 | 聚焦/操作图表面板 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:576` |
| diff pane 焦点键 | 聚焦/操作 diff 窗格 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:579` |
| Alt+B(运行工具时后台化/否则退词) | 把运行中工具转后台，或光标退一个词 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:589` |
| Alt/Option+Left、Alt+F/Right | 输入行按词移动光标 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:599,603` |
| Alt+D | 前向删一个词 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:607` |
| Alt+Backspace/Delete | 后向删一个词 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:615` |
| Alt+V | 从剪贴板粘贴 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:619` |
| Cmd/Super 组合(Backspace/←/→/Z/X/V/L) | 词删除、行首尾、撤销、剪切、粘贴、清屏 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:627-661` |
| 命令建议键 | slash 命令候选导航 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:665` |
| Ctrl+K(杀到行尾) | 删除光标到行尾(保留 Ctrl+Shift+K 给滚动) | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:669` |
| 滚动键(Ctrl+Shift+K/J, Alt+U/D) | 逐步/整页滚动transcript | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:673` |
| prompt 跳转键(Ctrl+K/J) | 跳上一/下一条用户 prompt | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:682` |
| Ctrl+数字 侧栏比例预设 / prompt 名次 | 设置侧栏宽度、跳到第 N 条 prompt | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:688,691` |
| scroll bookmark 键(Ctrl+G) | 打/取消滚动书签 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:701` |
| Shift+Tab(BackTab) | 循环收藏模型 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:710` |
| diff mode 循环键(Alt+G) | Off/Inline/Pinned/File 循环 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:715` |
| Ctrl+Down | 历史/prompt 导航 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:725,844` |
| Ctrl+B / Ctrl+C / Ctrl+D | 后台化工具、中断(remote.cancel)或退出 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:735,746,749` |
| Ctrl+R / Ctrl+L / Ctrl+U / Ctrl+K / Ctrl+Z / Ctrl+X / Ctrl+A / Ctrl+E / Ctrl+F | 历史搜索、清屏、编辑行首尾/剪切/撤销、退词 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:758,762,771,775,779,783,787,791,795` |
| Ctrl+Left/Right | 按词移动光标 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:801,807` |
| Ctrl+W/Backspace | 删除前一个词 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:813` |
| Ctrl+S / Ctrl+V | 暂存输入 / 粘贴 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:817,821` |
| Ctrl+Tab 或 Ctrl+T | 切换队列模式(等响应完再发) | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:825` |
| Ctrl+Up | 取回待发消息编辑并取消软中断 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:835` |
| Alt+Enter(或 Shift/Cmd+Enter) | 发送/排队/插话，或在新会话启动 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:852` |
| 带修饰 Enter(换行键) | 在输入框插入换行 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:908` |
| 多行/历史导航键 | 输入框内上下导航与历史 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:911` |
| 可打印字符/Backspace/Delete/←/→/Home/End/Tab/Enter | 常规文本编辑、自动补全、提交 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:917-966` |
| Up/PageUp、Down/PageDown、Esc | 滚动 transcript；Esc 关选择器/清输入 | `crates/jcode-tui/src/tui/app/remote/key_handling.rs:2719-2727` |

### G1b. 远端断线(disconnected)键位（11 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| Ctrl+C / Ctrl+D | 断线态退出 | `crates/jcode-tui/src/tui/app/remote.rs:1984` |
| Ctrl+L | 断线态终端式清屏 | `crates/jcode-tui/src/tui/app/remote.rs:1988` |
| 其余 Ctrl 组合 | 交由 handle_control_key 处理 | `crates/jcode-tui/src/tui/app/remote.rs:1994` |
| Alt 组合 / macOS Option 快捷 | 交由 handle_alt_key 处理 | `crates/jcode-tui/src/tui/app/remote.rs:2002,2006` |
| Cmd/Super 组合(Backspace/←/→/Z/X/V/L) | 断线态编辑与清屏 | `crates/jcode-tui/src/tui/app/remote.rs:2013-2042` |
| Alt+Enter | 把输入排入重连队列 | `crates/jcode-tui/src/tui/app/remote.rs:2045,2113` |
| new_terminal / open_resume 键 | 新终端会话 / 打开 resume 选择器 | `crates/jcode-tui/src/tui/app/remote.rs:2052,2058` |
| 可打印字符/Backspace/Delete/←/→/Home/End/Tab | 断线态输入框编辑与补全 | `crates/jcode-tui/src/tui/app/remote.rs:2078-2111` |
| Up/PageUp、Down/PageDown | 断线态滚动 transcript | `crates/jcode-tui/src/tui/app/remote.rs:2116-2123` |
| Esc | 回到底部并清空输入 | `crates/jcode-tui/src/tui/app/remote.rs:2124` |
| 滚轮/键滚动增量 | key_scroll_delta / mouse_scroll_delta | `crates/jcode-tui/src/tui/app/remote.rs:581-598` |

### G1c. 远端 server 事件驱动的专属界面（11 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| 服务器更新可用 | 提示并可自动 reload 服务端 | `crates/jcode-tui/src/tui/app/remote/server_events.rs:1838` |
| 模型/端点不匹配 | 提示并用下一个可用路由重发(回退提议) | `crates/jcode-tui/src/tui/app/remote/server_events.rs:1395` |
| SidePanelState 事件 | 应用服务端侧栏快照(更新侧栏页) | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2183` |
| History 事件 | 应用 side_panel/skills/sessions 并刷新模型 picker | `crates/jcode-tui/src/tui/app/remote/server_events.rs:1764-1789` |
| SwarmStatus 事件 | 更新 swarm 成员状态(驱动 swarm 视图) | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2187` |
| 协调者要求关闭会话 | 收到后退出客户端 | `crates/jcode-tui/src/tui/app/remote/server_events.rs:1459` |
| reload 完成 | 提示 "Reload complete - prompt preserved" | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2006` |
| Plan proposal 事件 | 提示 "Plan proposal received" | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2281` |
| 压缩完成/失败 | 提示 Compacting / Compaction failed | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2927-2930` |
| 恢复全部会话 | 提示 "Resuming N sessions" | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2939-2943` |
| StdinRequest 事件 | 提示检测到交互式终端(会超时) | `crates/jcode-tui/src/tui/app/remote/server_events.rs:2948` |

## 23. account picker / login picker 键位表（共 24 条）

> 数法：account picker = `crates/jcode-tui-account-picker/src/overlay.rs` 的 `handle_overlay_key`(:305-373) 逐 match 臂（12，另鼠标 :374-397）；login picker = `crates/jcode-tui/src/tui/login_picker.rs` 的 `handle_overlay_key`(:227-269) 逐 match 臂（12，另鼠标 :271-290）。App 侧路由 account=app/auth_account_picker.rs:1248-1278、login=app/auth_account_picker_saved_accounts.rs:4-30。

### G2a. account picker 键位表（12 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| Esc | 有过滤词则清过滤，否则关闭选择器 | `crates/jcode-tui-account-picker/src/overlay.rs:311` |
| q(无 Ctrl) | 关闭选择器 | `crates/jcode-tui-account-picker/src/overlay.rs:319` |
| Ctrl+C | 关闭选择器 | `crates/jcode-tui-account-picker/src/overlay.rs:322` |
| Up / k | 选中项上移 | `crates/jcode-tui-account-picker/src/overlay.rs:325` |
| Down / j | 选中项下移 | `crates/jcode-tui-account-picker/src/overlay.rs:328` |
| Left / Right | 按 provider 分组跳到上一/下一组 | `crates/jcode-tui-account-picker/src/overlay.rs:332,335` |
| PageUp / K、PageDown / J | 上/下翻 6 项 | `crates/jcode-tui-account-picker/src/overlay.rs:338,341` |
| Home / g、End / G | 跳到首项/末项 | `crates/jcode-tui-account-picker/src/overlay.rs:345,348` |
| Backspace | 删除过滤字符并重过滤 | `crates/jcode-tui-account-picker/src/overlay.rs:351` |
| Enter | 执行选中账号动作(切换/重登/删除等) | `crates/jcode-tui-account-picker/src/overlay.rs:356` |
| 可打印字符(无 Ctrl/Alt) | 追加过滤词 | `crates/jcode-tui-account-picker/src/overlay.rs:362` |
| 鼠标:滚轮/左键点击行 | 滚轮选项移动、点击选中对应行 | `crates/jcode-tui-account-picker/src/overlay.rs:374-397` |

### G2b. login picker 键位表（12 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| Esc | 有过滤词则清过滤，否则关闭 | `crates/jcode-tui/src/tui/login_picker.rs:228` |
| q(无 Ctrl) | 关闭 | `crates/jcode-tui/src/tui/login_picker.rs:235` |
| Ctrl+C | 关闭 | `crates/jcode-tui/src/tui/login_picker.rs:238` |
| Up / k | 选中项上移 | `crates/jcode-tui/src/tui/login_picker.rs:241` |
| Down / j | 选中项下移 | `crates/jcode-tui/src/tui/login_picker.rs:244` |
| PageUp / K、PageDown / J | 上/下翻 6 项 | `crates/jcode-tui/src/tui/login_picker.rs:248,252` |
| Home / g、End / G | 跳到首项/末项 | `crates/jcode-tui/src/tui/login_picker.rs:256,259` |
| Backspace | 删除过滤字符并重过滤 | `crates/jcode-tui/src/tui/login_picker.rs:262` |
| Enter | 执行选中 provider 登录(无选中则关闭) | `crates/jcode-tui/src/tui/login_picker.rs:266` |
| 可打印字符(无 Ctrl/Alt) | 追加过滤词(支持数字索引/别名) | `crates/jcode-tui/src/tui/login_picker.rs:270` |
| 鼠标:滚轮/左键点击行 | 滚轮选项移动、点击选中对应 provider | `crates/jcode-tui/src/tui/login_picker.rs:271-289` |
| App 路由 handle_login_picker_key | 把上述动作转为关闭/start_login_provider | `crates/jcode-tui/src/tui/app/auth_account_picker_saved_accounts.rs:4-30` |

## 24. 侧栏页面 id（共 9 条）

> 数法：grep 全仓 `SidePanelPage{` 构造与 `write_markdown_page` 调用，剔除测试 fixture；8 个固定类 + 1 个开放类。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| split_view | /split 显示当前聊天镜像页 | `crates/jcode-tui/src/tui/app/split_view.rs:8,117` |
| observe | /observe 显示最新上下文页 | `crates/jcode-tui/src/tui/app/observe.rs:7,208` |
| session_todos | /todos 显示当前会话待办页 | `crates/jcode-tui/src/tui/app/todos_view.rs:10,257` |
| catchup | 跨会话 catchup 摘要页 | `crates/jcode-tui/src/tui/app/catchup.rs:6,95` |
| linked-markdown:<path> | 链接外部 markdown 文件为只读页 | `crates/jcode-tui/src/tui/app/navigation.rs:314-322` |
| goals | 目标总览页(goal 工具/命令 upsert) | `crates/jcode-base/src/goal.rs:259-263` |
| goal.<sanitized-id> | 单个目标的详情页 | `crates/jcode-base/src/goal.rs:342-354` |
| image.<safe-id> | 生成图片的预览页(前缀 image.) | `crates/jcode-base/src/generated_image.rs:5-16,215` |
| <任意 page_id>（开放类，不可穷举） | 模型经 side_panel/panel 工具 write/append/load/focus/delete 任意 id | `crates/jcode-app-core/src/tool/side_panel.rs:62-80,94-153` |

> **Managed 页 id 不可静态穷举的结论与依据**：`side_panel/panel` 工具的 page_id 是自由字符串参数（`crates/jcode-app-core/src/tool/side_panel.rs:62-80` 的 `SidePanelInput.page_id` 为自由 String），模型可写入任意 id，经 `jcode-base/src/side_panel.rs:22-40` 的 `write/append_markdown_page` 落盘，故不存在封闭枚举；只有固定来源的 id（goals / goal.<id> / image.<id> / catchup / observe / split_view / session_todos / linked-markdown:<path>）可列全。另：swarm「图」**不是**侧栏页——它由 inline swarm panel（Chat/Controls/FullPage，`tui_state.rs:2074-2112`）与 info widget 渲染，全仓无 `id="swarm"` 的 SidePanelPage 写入。

## 25. 两处 [未核实] 的定论（共 2 条）

| 名字 | 定论 | 出处 |
|---|---|---|
| `inline picker 收藏热键` | 收藏 = **Ctrl+N**（Ctrl+O = set default）；文档里的 Ctrl+D 是旧名/误记，picker 内无该分支；Shift+Tab(BackTab) = 循环收藏 | `crates/jcode-tui/src/tui/app/inline_interactive.rs:2251-2276,3514-3517；crates/jcode-tui/src/tui/ui_overlays.rs:531-536；crates/jcode-tui/src/tui/app/tests/remote_model_picker_hotkeys.rs:40-118` |
| `new_terminal 默认` | 有默认绑定：macOS `cmd+shift+;` / Windows·Linux `alt+shift+;`；**非 unbound** | `crates/jcode-config-types/src/keybindings.rs:323-333；crates/jcode-config-types/src/lib.rs:1118；crates/jcode-tui/src/tui/keybind.rs:629-640` |

> 依据链 (4a)：处理函数 `inline_interactive.rs:2251-2276`（model_picker_preview_hotkey：Ctrl+O=set default，Ctrl+N=toggle favorite）与 `:3514-3517`（toggle_selected_model_favorite）；帮助文本 `ui_overlays.rs:531-536`（Ctrl+O 设默认 / Ctrl+N 收藏）；回归测试 `app/tests/remote_model_picker_hotkeys.rs:40-118`（Ctrl+N 收藏、Ctrl+O 设默认，远程路径同样生效）。Ctrl+D 在 picker 中无任何分支：它只出现在输入行前向删除/退出（`remote/key_handling.rs:746/749`），故文档里的 Ctrl+D 是旧名/误记。
> 依据链 (4b)：注册表 `keybindings.rs:323-333`（id="new_terminal"，macos dev("cmd+shift+;")，other dev("alt+shift+;")）→ `KeybindingsConfig::default()` `lib.rs:1118` 走 `default_binding(id,platform)` 命中注册表（fallback `""` 只在 id 缺失时使用，此处不触发）→ 示例配置该行是注释 `crates/jcode-base/src/config/default_file.rs:97-98`，不生效 → 运行时 `keybind.rs:629-640` 只在 raw 为空/disabled 时判为未绑定。结论：`keybind.rs:627-628` 与 `lib.rs:1064-1065` 的「unbound 默认」注释是过时描述；env `JCODE_NEW_TERMINAL_KEY` 可覆盖（`crates/jcode-base/src/config/env_overrides.rs:93-95`）。

## 26. 纯视觉件与动画（共 10 条）

> 数法：按 scrollbar / idle animation / transition-smoothness 三类 grep 定位实现与配置。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| native scrollbar(chat/side_panel) | 聊天/侧栏原生滚动条(默认开) | `crates/jcode-config-types/src/lib.rs:1135-1145` |
| render_native_scrollbar / split_native_scrollbar_area / native_scrollbar_visible | 滚动条绘制与占位/可见判定 | `crates/jcode-tui/src/tui/ui.rs:3626,3644,3652` |
| handterm 原生滚动桥 | 把宿主机原生滚动条事件回灌为 chat/side pane 滚动 | `crates/jcode-tui/src/tui/app/handterm_native_scroll.rs:152-200` |
| session picker 自绘滚动条 | 会话选择器列表溢出时显示滚动条 | `crates/jcode-tui/src/tui/session_picker.rs:1414,1936` |
| idle donut 动画变体 | 空屏装饰动画 donut/orbit_rings(另有 gyroscope/black_hole 采样器) | `crates/jcode-tui/src/tui/ui_animations.rs:8,524-528` |
| idle donut 预留高度/渲染 | 输入越长动画越矮；空闲时占据底部 no negative space | `crates/jcode-tui/src/tui/ui_animations.rs:281;crates/jcode-tui/src/tui/ui.rs:39-43,3464` |
| prompt_entry_animation | 用户 prompt 首次滚入视口时的入场动画 | `crates/jcode-config-types/src/display.rs:60;crates/jcode-tui/src/tui/ui.rs:765,821` |
| diagram pane 比例平滑过渡 | 调整图表面板宽度时缓动过渡 | `crates/jcode-tui/src/tui/app.rs:1369-1372` |
| 鼠标滚轮动量缓动 | 滚轮速度加速+缓出，模拟顺滑滚动 | `crates/jcode-tui/src/tui/app/navigation.rs:725,814` |
| 流式文本平滑揭示(smoothness) | 缓冲流式输出按节拍平滑揭示而非突发 | `crates/jcode-tui/src/tui/app/remote.rs:151` |

## 27. 鼠标交互（共 15 条）

> 数法：`crates/jcode-tui/src/tui/app/navigation.rs` 的 `handle_mouse_event`(:1368-1762) 逐分支 + overlay 各自的 `handle_overlay_mouse`。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| 聊天区滚轮 | 上下滚动 transcript | `crates/jcode-tui/src/tui/app/navigation.rs:1754-1760` |
| 侧栏滚轮 | 滚动侧栏页 | `crates/jcode-tui/src/tui/app/navigation.rs:1682-1686` |
| 侧栏横向滚轮 | 左右平移侧栏(diff/图) | `crates/jcode-tui/src/tui/app/navigation.rs:1688` |
| help overlay 滚轮 | 滚动 /help 浮层 | `crates/jcode-tui/src/tui/app/navigation.rs:1418-1424` |
| changelog overlay 滚轮 | 滚动 changelog 浮层 | `crates/jcode-tui/src/tui/app/navigation.rs:1395-1400` |
| model status overlay 滚轮 | 滚动模型状态浮层 | `crates/jcode-tui/src/tui/app/navigation.rs:1432-1438` |
| session picker 滚轮 | 预览区/列表滚动或切换选择 | `crates/jcode-tui/src/tui/app/navigation.rs:1462-1466` |
| 拖动选区复制 | 按住拖选、松手自动复制并保留高亮 | `crates/jcode-tui/src/tui/app/copy_selection.rs:519-640` |
| 点击输入行 | 把光标定位到点击处 | `crates/jcode-tui/src/tui/app/navigation.rs:1555-1571` |
| 点击图片展开徽标 | 循环切换内联图片展开级别 | `crates/jcode-tui/src/tui/app/navigation.rs:1714;:179` |
| 点击 pinned todo "more" | 展开置顶待办的更多条目 | `crates/jcode-tui/src/tui/app/navigation.rs:1542-1546` |
| diagram 边框拖拽 | 拖动改变图表面板宽度 | `crates/jcode-tui/src/tui/app/navigation.rs:1524,1582-1618` |
| 点击主聊天区 | 取消 diff 窗格焦点 | `crates/jcode-tui/src/tui/app/navigation.rs:1534-1539` |
| login picker 浮层鼠标 | 滚轮移动、点击选中 provider | `crates/jcode-tui/src/tui/login_picker.rs:271-289` |
| account picker 浮层鼠标 | 滚轮移动、点击选中账号动作行 | `crates/jcode-tui-account-picker/src/overlay.rs:374-397` |

## 28. 设置 · config.toml 与运行时开关（共 478 条）

> 数法：`crates/jcode-base/src/config.rs` 的 `Config` 结构体（顶层 25 段，:485-573）逐字段；各段叶子键逐 `pub struct` 字段数（jcode-config-types/src/lib.rs 206 + display.rs 34 + jcode-base/src/config.rs 40，见本目录 registry 对账）；环境变量逐 `apply_env_overrides`（env_overrides.rs）的赋值分支；`/config` 逐 `commands.rs` 分支；`KEYBINDING_DEFAULTS` 逐常量表元素（keybindings.rs:195-350）。子节行数之和 = 25+33+36+186+171+4+23 = 478。

### 28.1 顶层段（config.toml 顶层表，25 段）（共 25 条）

> 数法：config.toml 顶层段 (Config struct, crates/jcode-base/src/config.rs:485-573) — 共 25 条。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| [server] | 守护进程自主唤醒行为段。默认 internal | `crates/jcode-base/src/config.rs:488` |
| [keybindings] | 键位绑定段（33 项，见下组） | `crates/jcode-base/src/config.rs:491` |
| [dictation] | 外部语音转写段 | `crates/jcode-base/src/config.rs:494` |
| [display] | TUI/CLI 呈现段（34 项） | `crates/jcode-base/src/config.rs:497` |
| [features] | 运行时功能开关段 | `crates/jcode-base/src/config.rs:500` |
| [websearch] | websearch 工具段 | `crates/jcode-base/src/config.rs:503` |
| [tools] | 内置工具暴露段 | `crates/jcode-base/src/config.rs:506` |
| [acp] | Agent Client Protocol 适配器段 | `crates/jcode-base/src/config.rs:509` |
| [auth] | 外部认证来源信任段 | `crates/jcode-base/src/config.rs:512` |
| [provider] | 默认 provider/model 与请求行为段 | `crates/jcode-base/src/config.rs:515` |
| [providers.<name>] | 自定义 provider profile 映射（每 profile 18 项） | `crates/jcode-base/src/config.rs:524` |
| [agents] | swarm/subagent 默认与 memory 段 | `crates/jcode-base/src/config.rs:527` |
| [terminal] | 终端窗口/pane 启动段 | `crates/jcode-base/src/config.rs:530` |
| [hooks] | 生命周期外部命令钩子段 | `crates/jcode-base/src/config.rs:533` |
| [ambient] | ambient 后台模式段 | `crates/jcode-base/src/config.rs:536` |
| [safety] | 通知/远程通道段（30 项） | `crates/jcode-base/src/config.rs:539` |
| [notifications] | 交互会话桌面通知段 | `crates/jcode-base/src/config.rs:542` |
| [gateway] | WebSocket 网关段 | `crates/jcode-base/src/config.rs:545` |
| [compaction] | 上下文压缩段（11 项） | `crates/jcode-base/src/config.rs:548` |
| [power] | 电源管理段 | `crates/jcode-base/src/config.rs:551` |
| [autoreview] | 回合结束自动代码审查段 | `crates/jcode-base/src/config.rs:554` |
| [autojudge] | 回合结束自动执行评判段 | `crates/jcode-base/src/config.rs:557` |
| [sponsors] | 第三方集成发现段（旧段落名，默认值时不写入文件） | `crates/jcode-base/src/config.rs:563` |
| [launch_hotkeys] | 全局启动热键段（macOS/Linux/Windows） | `crates/jcode-base/src/config.rs:566` |
| [desktop.*] | Jcode Desktop 拥有的不透明表，CLI 只做 round-trip [未核实 schema] | `crates/jcode-base/src/config.rs:572` |

### 28.2 [keybindings]（33 项可配置键）（共 33 条）

> 数法：[keybindings] (KeybindingsConfig, crates/jcode-config-types/src/lib.rs:1001-1077) — 共 33 条。默认值取自常量表 KEYBINDING_DEFAULTS (crates/jcode-config-types/src/keybindings.rs:195-350)；平台分 macOS / 其他。与 §10 的 32 条键位串互参；本节按 `KeybindingsConfig` 全 33 个 pub 字段逐条列（含策略字段 session_picker_enter）。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| keybindings.scroll_up | 向上滚动一档。默认 ctrl+shift+k（doc 注释误写 ctrl+k） | `crates/jcode-config-types/src/lib.rs:1003` |
| keybindings.scroll_down | 向下滚动一档。默认 ctrl+shift+j（doc 注释误写 ctrl+j） | `crates/jcode-config-types/src/lib.rs:1005` |
| keybindings.scroll_page_up | 向上翻页。默认 alt+u | `crates/jcode-config-types/src/lib.rs:1007` |
| keybindings.scroll_page_down | 向下翻页。默认 alt+d | `crates/jcode-config-types/src/lib.rs:1009` |
| keybindings.model_switch_next | 切换到下一个模型。默认 ctrl+tab | `crates/jcode-config-types/src/lib.rs:1011` |
| keybindings.model_switch_prev | 切换到上一个模型。默认 ctrl+shift+tab | `crates/jcode-config-types/src/lib.rs:1013` |
| keybindings.fallback_switch | 接受错误后 fallback 提议（换模型/认证并重发）。默认 ctrl+y | `crates/jcode-config-types/src/lib.rs:1016` |
| keybindings.effort_increase | 提高 reasoning effort。默认 macOS cmd+right / 其他 alt+right | `crates/jcode-config-types/src/lib.rs:1018` |
| keybindings.effort_decrease | 降低 reasoning effort。默认 macOS cmd+left / 其他 alt+left | `crates/jcode-config-types/src/lib.rs:1020` |
| keybindings.centered_toggle | 切换居中模式。默认 alt+c | `crates/jcode-config-types/src/lib.rs:1022` |
| keybindings.scroll_prompt_up | 跳到上一条用户 prompt。默认 ctrl+k | `crates/jcode-config-types/src/lib.rs:1024` |
| keybindings.scroll_prompt_down | 跳到下一条用户 prompt。默认 ctrl+j | `crates/jcode-config-types/src/lib.rs:1026` |
| keybindings.scroll_bookmark | 滚动书签开关（暂存位置/回到底部/返回）。默认 ctrl+g | `crates/jcode-config-types/src/lib.rs:1028` |
| keybindings.auto_poke_toggle | 切换 auto-poke。默认 ctrl+p；"" 禁用 | `crates/jcode-config-types/src/lib.rs:1030` |
| keybindings.scroll_up_fallback | 向上滚动备用键。默认未绑定 | `crates/jcode-config-types/src/lib.rs:1032` |
| keybindings.scroll_down_fallback | 向下滚动备用键。默认未绑定 | `crates/jcode-config-types/src/lib.rs:1034` |
| keybindings.workspace_left | 工作区左移。默认 alt+h（可逗号分隔多别名） | `crates/jcode-config-types/src/lib.rs:1036` |
| keybindings.workspace_down | 工作区下移。默认 alt+j | `crates/jcode-config-types/src/lib.rs:1038` |
| keybindings.workspace_up | 工作区上移。默认 alt+k | `crates/jcode-config-types/src/lib.rs:1040` |
| keybindings.workspace_right | 工作区右移。默认 alt+l | `crates/jcode-config-types/src/lib.rs:1042` |
| keybindings.side_panel_toggle | 侧栏开关。默认 alt+m（无注册表条目，走 fallback） | `crates/jcode-config-types/src/lib.rs:1044` |
| keybindings.copy_selection_toggle | 复制/选择模式开关。默认 alt+y | `crates/jcode-config-types/src/lib.rs:1046` |
| keybindings.diagram_pane_toggle | 图表面板位置切换。默认 alt+t | `crates/jcode-config-types/src/lib.rs:1048` |
| keybindings.diagram_pane_visibility_toggle | 固定图表面板显隐。默认 alt+shift+m | `crates/jcode-config-types/src/lib.rs:1050` |
| keybindings.typing_scroll_lock_toggle | 输入时滚动锁开关。默认 alt+s | `crates/jcode-config-types/src/lib.rs:1052` |
| keybindings.diff_mode_cycle | 循环 inline diff 显示模式。默认 alt+g | `crates/jcode-config-types/src/lib.rs:1054` |
| keybindings.info_widget_toggle | info widget 开关。默认 alt+i | `crates/jcode-config-types/src/lib.rs:1056` |
| keybindings.todo_card_toggle | 会话 todo 卡片显隐。默认 alt+x | `crates/jcode-config-types/src/lib.rs:1059` |
| keybindings.swarm_panel_focus | 聚焦 inline swarm 面板。默认 alt+n（仅 swarm_spawn_mode=inline 且管理 swarm 时生效） | `crates/jcode-config-types/src/lib.rs:1064` |
| keybindings.new_terminal | 在新终端窗口开新 jcode 会话。默认 macOS cmd+shift+; / 其他 alt+shift+; | `crates/jcode-config-types/src/lib.rs:1067` |
| keybindings.open_resume | 打开 /resume 会话选择器。默认 macOS cmd+b / 其他 alt+r；"" 禁用 | `crates/jcode-config-types/src/lib.rs:1070` |
| keybindings.voice_input | 内置语音输入起停（Nari 转写）。默认 ctrl+space；"" 禁用 | `crates/jcode-config-types/src/lib.rs:1073` |
| keybindings.session_picker_enter | 会话选择器 Enter 行为：current-terminal(默认) \| new-terminal；Ctrl+Enter 走另一个 | `crates/jcode-config-types/src/lib.rs:1076` |

### 28.3 [display]（34 项 + native_scrollbars 子表 2 项）（共 36 条）

> 数法：[display] (DisplayConfig, crates/jcode-config-types/src/display.rs:11-122) — 共 34 条 + [display.native_scrollbars] (NativeScrollbarConfig, crates/jcode-config-types/src/lib.rs:1135-1140) — 共 2 条。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| display.diff_mode | diff 显示：off \| inline(默认) \| full-inline \| file（别名 full_inline/fullinline/inline-full/...） | `crates/jcode-config-types/src/display.rs:15` |
| display.show_diffs | 旧字段(Option<bool>)，true→inline false→off，载入后并入 diff_mode。默认 None | `crates/jcode-config-types/src/display.rs:18` |
| display.queue_mode | 队列模式：等助手完成再发下一条。默认 false | `crates/jcode-config-types/src/display.rs:20` |
| display.auto_server_reload | 检测到更新 server 二进制时自动重载远端 server。默认 true | `crates/jcode-config-types/src/display.rs:22` |
| display.mouse_capture | 捕获鼠标事件（滚轮可用但禁终端选择）。默认 true | `crates/jcode-config-types/src/display.rs:24` |
| display.debug_socket | 启用外部控制调试 socket。默认 false | `crates/jcode-config-types/src/display.rs:26` |
| display.emoji | TUI/CLI 输出渲染 emoji。默认 true | `crates/jcode-config-types/src/display.rs:28` |
| display.centered | 内容居中。默认 false | `crates/jcode-config-types/src/display.rs:30` |
| display.show_thinking | 显示 reasoning 内容（reasoning_display 未设时的回退）。默认 true | `crates/jcode-config-types/src/display.rs:32` |
| display.reasoning_display | reasoning 显示：off \| full \| current。默认 Some(full) | `crates/jcode-config-types/src/display.rs:39` |
| display.diagram_mode | mermaid 图显示：none(默认,仍内联) \| margin \| pinned（别名 inline/off→none） | `crates/jcode-config-types/src/display.rs:44` |
| display.markdown_spacing | markdown 块间距：compact(默认) \| document | `crates/jcode-config-types/src/display.rs:47` |
| display.latex_rendering | LaTeX 渲染：none \| unicode \| image(默认)（别名 raw/off/terminal/text/png） | `crates/jcode-config-types/src/display.rs:50` |
| display.pin_images | 把读入的图片固定到侧栏。默认 true | `crates/jcode-config-types/src/display.rs:52` |
| display.pin_todos | todo 列表滚动时固定在会话顶部。默认 true | `crates/jcode-config-types/src/display.rs:56` |
| display.idle_animation | 首条 prompt 前显示 idle 动画。默认 false | `crates/jcode-config-types/src/display.rs:58` |
| display.prompt_entry_animation | 用户 prompt 行进入视口时短暂动画。默认 true | `crates/jcode-config-types/src/display.rs:60` |
| display.disabled_animations | 按名称禁用的动画变体（如 ["donut","orbit_rings"]）。默认 [] | `crates/jcode-config-types/src/display.rs:62` |
| display.performance | 性能档：auto(默认,空串即 auto) \| full \| reduced \| minimal | `crates/jcode-config-types/src/display.rs:64` |
| display.animation_fps | 动画帧率 1-120。默认 60 | `crates/jcode-config-types/src/display.rs:66` |
| display.redraw_fps | 活动重绘帧率 1-120。默认 60（doc 注释误写 30） | `crates/jcode-config-types/src/display.rs:68` |
| display.prompt_preview | 上一条 prompt 滚出视口时在顶部显示截断预览。默认 true | `crates/jcode-config-types/src/display.rs:70` |
| display.compact_notifications | swarm/文件活动通知用单行紧凑形式。默认 false | `crates/jcode-config-types/src/display.rs:73` |
| display.copy_badge_alt_label | 复制徽标里 Alt/Option 的显示名；空=自动(⌥/Alt)。默认 "" | `crates/jcode-config-types/src/display.rs:75` |
| display.show_agentgrep_output | agentgrep 工具完整输出内联显示。默认 false | `crates/jcode-config-types/src/display.rs:79` |
| display.show_bash_output | 工具摘要下显示最多三行 bash 输出。默认 false | `crates/jcode-config-types/src/display.rs:83` |
| display.tool_call_details | 工具行在 intent 后显示暗色技术细节。默认 false | `crates/jcode-config-types/src/display.rs:89` |
| display.native_scrollbars | 原生终端滚动条子表（chat/side_panel） | `crates/jcode-config-types/src/display.rs:91` |
| display.keybinding_hints | 偶尔提示「学这个快捷键」的 nudge。默认 true | `crates/jcode-config-types/src/display.rs:96` |
| display.theme | 配色主题：auto(默认,空串即 auto) \| dark \| light | `crates/jcode-config-types/src/display.rs:101` |
| display.colors | 按角色覆盖颜色（如 user="#8ab4f8"），BTreeMap<role,hex>。默认 {} | `crates/jcode-config-types/src/display.rs:107` |
| display.active_sessions_manager | 空输入按左方向键打开活动会话选择器。默认 false（/active 始终可用） | `crates/jcode-config-types/src/display.rs:113` |
| display.external_sessions | 会话选择器纳入其他 agent CLI 的 transcript（Claude Code/Codex/Pi/OpenCode/Cursor）。默认 true | `crates/jcode-config-types/src/display.rs:119` |
| display.usage_display | 用量百分比措辞：left(默认) \| used | `crates/jcode-config-types/src/display.rs:121` |
| display.native_scrollbars.chat | chat 视口显示原生终端滚动条。默认 true | `crates/jcode-config-types/src/lib.rs:1137` |
| display.native_scrollbars.side_panel | 侧栏显示原生终端滚动条。默认 true | `crates/jcode-config-types/src/lib.rs:1139` |

### 28.4 其余各段的叶子键（共 186 条）

> 数法：以下各段的 `pub struct` 字段逐条，节序：[server]；[dictation]；[features]；[websearch]；[tools]；[acp]；[auth]；[provider]；[providers.<name>]；[providers.<name>.models[]]；[agents]；[terminal]；[hooks]；[compaction]；[ambient]；[notifications]；[safety]；[gateway]；[power]；[autoreview]；[autojudge]；[sponsors]；[launch_hotkeys]；[launch_hotkeys.entries[]]。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| server.wake_mode | 自主 wake 请求的归属：internal(守护进程自己起/打断回合) \| external(只发 wake_requested 事件)。默认 internal | `crates/jcode-base/src/config.rs:600` |
| dictation.command | 外部语音转写 shell 命令，须把最终 transcript 打到 stdout。默认 ""(禁用) | `crates/jcode-base/src/config.rs:819` |
| dictation.mode | transcript 应用方式：insert \| append \| replace \| send (枚举 TranscriptMode, crates/jcode-protocol/src/lib.rs:39)。默认 send | `crates/jcode-base/src/config.rs:821` |
| dictation.key | 应用内听写热键。默认 "off"(禁用) | `crates/jcode-base/src/config.rs:823` |
| dictation.timeout_secs | 等待听写命令的最长秒数，0=不限。默认 90 | `crates/jcode-base/src/config.rs:825` |
| dictation.vocabulary | 追加给内置语音转写的专有名词表。默认 [] | `crates/jcode-base/src/config.rs:829` |
| dictation.recorder | 内置语音输入的录音命令，须输出 mono 16kHz s16le PCM；空=自动探测。默认 "" | `crates/jcode-base/src/config.rs:833` |
| features.check_updates | 启动时检查/安装 jcode 更新（--no-update 的持久等价）。默认 true | `crates/jcode-config-types/src/lib.rs:1159` |
| features.memory | 启用 memory 检索/抽取。默认 true | `crates/jcode-config-types/src/lib.rs:1161` |
| features.swarm | 启用 swarm 协调。默认 true | `crates/jcode-config-types/src/lib.rs:1163` |
| features.mermaid | 启用 Mermaid 渲染与模型提示。默认 true | `crates/jcode-config-types/src/lib.rs:1165` |
| features.auto_poke | auto-poke 默认状态（todos 未完成时自动追问）。默认 true | `crates/jcode-config-types/src/lib.rs:1169` |
| features.message_timestamps | 向模型发送的用户消息/工具结果注入时间戳。默认 true | `crates/jcode-config-types/src/lib.rs:1171` |
| features.persist_memory_injections | 自动回忆的 memory 注入写入会话历史而非仅本次请求。默认 false | `crates/jcode-config-types/src/lib.rs:1174` |
| features.kv_cache_miss_notices | harness 导致 KV cache miss 时在聊天里告警。默认 true | `crates/jcode-config-types/src/lib.rs:1181` |
| features.update_channel | 更新通道：stable(默认) \| main（别名 release/nightly/edge；未知值 lenient 回退） | `crates/jcode-config-types/src/lib.rs:1183` |
| websearch.engine | 首选引擎：duckduckgo(默认) \| bing \| searxng \| native（别名 ddg/searx/provider） | `crates/jcode-config-types/src/lib.rs:1254` |
| websearch.fallback_engines | 首选失败后尝试的无 key HTML 引擎列表。默认 [bing] | `crates/jcode-config-types/src/lib.rs:1256` |
| websearch.bing_api_key | Bing API key（仅主 Bing 搜索用）。默认 None | `crates/jcode-config-types/src/lib.rs:1258` |
| websearch.bing_api_key_env | 存 Bing API key 的环境变量名。默认 "JCODE_BING_API_KEY" | `crates/jcode-config-types/src/lib.rs:1260` |
| websearch.bing_market | Bing 市场/区域，如 en-US、zh-CN。默认 "en-US" | `crates/jcode-config-types/src/lib.rs:1262` |
| websearch.searxng_url | SearXNG 实例 base URL。默认 None（回退 searxng_url_env） | `crates/jcode-config-types/src/lib.rs:1266` |
| websearch.searxng_url_env | 存 SearXNG base URL 的环境变量名。默认 "JCODE_SEARXNG_URL" | `crates/jcode-config-types/src/lib.rs:1268` |
| websearch.prefer_native | 优先 provider 侧原生搜索（Anthropic/OpenAI）。默认 true | `crates/jcode-config-types/src/lib.rs:1274` |
| websearch.native_max_uses | 每次请求原生搜索上限（Anthropic 计费保护）。默认 Some(5)（常量 DEFAULT_NATIVE_WEB_SEARCH_MAX_USES=5） | `crates/jcode-config-types/src/lib.rs:1278` |
| websearch.native_allowed_domains | 原生搜索白名单域（与 blocked 互斥）。默认 [] | `crates/jcode-config-types/src/lib.rs:1281` |
| websearch.native_blocked_domains | 原生搜索黑名单域（仅 Anthropic）。默认 [] | `crates/jcode-config-types/src/lib.rs:1283` |
| websearch.native_anthropic_tool_version | Anthropic server 搜索工具版本。默认 "web_search_20250305"（常量 DEFAULT_ANTHROPIC_WEB_SEARCH_TOOL） | `crates/jcode-config-types/src/lib.rs:1288` |
| tools.profile | 工具档：full(默认,空串即 full) \| acp \| minimal/lite \| none/off | `crates/jcode-base/src/config.rs:663` |
| tools.enabled | 显式白名单；"*"/"all" 表示全部。默认 [] | `crates/jcode-base/src/config.rs:666` |
| tools.disabled | 在 profile/enabled 之后移除的工具。默认 [] | `crates/jcode-base/src/config.rs:668` |
| tools.disable_base_tools | 除非 enabled，否则禁用所有内置工具。默认 false | `crates/jcode-base/src/config.rs:670` |
| tools.mcp_tools | MCP 工具暴露：auto(默认) \| eager \| deferred（枚举 McpToolsMode） | `crates/jcode-base/src/config.rs:672` |
| tools.mcp_tools_token_threshold | 已忽略的旧阈值(仅为兼容解析)，别名 mcp_tools_threshold 等。默认 8000 | `crates/jcode-base/src/config.rs:681` |
| acp.profile | ACP 兼容档：standard(默认) \| extended \| full | `crates/jcode-base/src/config.rs:608` |
| acp.tool_profile | jcode acp 自行起 daemon 时请求的工具档。默认 "acp" | `crates/jcode-base/src/config.rs:610` |
| auth.trusted_external_sources | 已批准读取的外部认证来源 id 列表。默认 [] | `crates/jcode-config-types/src/lib.rs:551` |
| auth.trusted_external_source_paths | 外部认证来源的路径级批准（含 '\|' 形式）。默认 [] | `crates/jcode-config-types/src/lib.rs:554` |
| provider.default_model | 默认模型。默认 None | `crates/jcode-config-types/src/lib.rs:1326` |
| provider.default_provider | 默认 provider（claude\|anthropic-api\|openai\|copilot\|openrouter\|...）。默认 None | `crates/jcode-config-types/src/lib.rs:1328` |
| provider.openai_reasoning_effort | OpenAI Responses reasoning effort：none\|minimal\|low\|medium\|high\|xhigh\|max。默认 Some("low") | `crates/jcode-config-types/src/lib.rs:1330` |
| provider.anthropic_reasoning_effort | Anthropic Messages output_config effort：none\|low\|medium\|high\|xhigh\|max。默认 None（按模型） | `crates/jcode-config-types/src/lib.rs:1332` |
| provider.anthropic_cache_ttl_1h | Anthropic 提示缓存用 1 小时而非 5 分钟。默认 true | `crates/jcode-config-types/src/lib.rs:1334` |
| provider.openai_transport | OpenAI 传输：auto\|websocket\|https。默认 None | `crates/jcode-config-types/src/lib.rs:1336` |
| provider.openai_service_tier | OpenAI service tier：priority\|flex\|off/standard。默认 Some("priority") | `crates/jcode-config-types/src/lib.rs:1338` |
| provider.openai_native_compaction_mode | OpenAI 原生压缩：auto(默认) \| explicit \| off | `crates/jcode-config-types/src/lib.rs:1340` |
| provider.openai_native_compaction_threshold_tokens | 触发 OpenAI 原生压缩的 token 阈值。默认 200000 | `crates/jcode-config-types/src/lib.rs:1342` |
| provider.preserve_reasoning_context | 为后续回合保留 provider 原生 reasoning/thinking。默认 true | `crates/jcode-config-types/src/lib.rs:1344` |
| provider.cross_provider_failover | 跨 provider 重发行为：countdown(默认,3 秒倒计时) \| manual（别名 off/false/none） | `crates/jcode-config-types/src/lib.rs:1346` |
| provider.same_provider_account_failover | 换 provider 前先试同 provider 其他账号。默认 true | `crates/jcode-config-types/src/lib.rs:1349` |
| provider.copilot_premium | Copilot premium 模式：normal(默认,None) \| one \| zero | `crates/jcode-config-types/src/lib.rs:1352` |
| provider.gemini_force_oauth | 即使有 Gemini API key 也强制 Code Assist OAuth。默认 false | `crates/jcode-config-types/src/lib.rs:1357` |
| provider.gemini_project | Gemini Code Assist OAuth 的 GCP project。默认 None | `crates/jcode-config-types/src/lib.rs:1362` |
| provider.model_picker_providers | 限制 /model 只列这些 provider/route/profile。默认 None(全列) | `crates/jcode-config-types/src/lib.rs:1368` |
| provider.stream_idle_timeout_secs | 流式无数据超时基准秒数（高 effort 自动放大）。默认 180 | `crates/jcode-config-types/src/lib.rs:1373` |
| provider.max_retries | 瞬时错误最大请求尝试数（含首次）。默认 8 | `crates/jcode-config-types/src/lib.rs:1376` |
| provider.retry_backoff_cap_secs | 重试指数退避上限秒数。默认 30 | `crates/jcode-config-types/src/lib.rs:1379` |
| providers.<name>.type | provider 类型（serde rename=type）：openai-compatible(默认) \| anthropic-compatible \| openrouter | `crates/jcode-config-types/src/lib.rs:475` |
| providers.<name>.base_url | API base URL。默认 "" | `crates/jcode-config-types/src/lib.rs:476` |
| providers.<name>.api | API 方法标识。默认 None | `crates/jcode-config-types/src/lib.rs:477` |
| providers.<name>.auth | 认证方式：bearer(默认) \| header \| none（别名大小写形式） | `crates/jcode-config-types/src/lib.rs:478` |
| providers.<name>.auth_header | 自定义认证 header 名。默认 None | `crates/jcode-config-types/src/lib.rs:479` |
| providers.<name>.headers | 每次请求附带的额外 HTTP header 表。默认 {} | `crates/jcode-config-types/src/lib.rs:482` |
| providers.<name>.api_key_env | 取 API key 的环境变量名。默认 None | `crates/jcode-config-types/src/lib.rs:483` |
| providers.<name>.api_key | 内联 API key。默认 None | `crates/jcode-config-types/src/lib.rs:484` |
| providers.<name>.env_file | key 所在 env 文件。默认 None | `crates/jcode-config-types/src/lib.rs:485` |
| providers.<name>.default_model | 该 profile 默认模型。默认 None | `crates/jcode-config-types/src/lib.rs:486` |
| providers.<name>.requires_api_key | 是否强制需要 API key。默认 None | `crates/jcode-config-types/src/lib.rs:487` |
| providers.<name>.provider_routing | 启用 OpenRouter provider routing。默认 false | `crates/jcode-config-types/src/lib.rs:489` |
| providers.<name>.model_catalog | 启用模型目录。默认 false | `crates/jcode-config-types/src/lib.rs:491` |
| providers.<name>.allow_provider_pinning | 允许 provider pinning。默认 false | `crates/jcode-config-types/src/lib.rs:493` |
| providers.<name>.models | 该 profile 的模型列表（见下组）。默认 [] | `crates/jcode-config-types/src/lib.rs:495` |
| providers.<name>.extra_body | 合并进每次请求 body 的额外 JSON 字段（别名 extra-body）。默认 None | `crates/jcode-config-types/src/lib.rs:502` |
| providers.<name>.supports_reasoning_effort | 端点是否接受顶层 reasoning_effort（别名 supports-reasoning-effort/reasoning_effort）。默认 None(自动探测) | `crates/jcode-config-types/src/lib.rs:514` |
| providers.<name>.disable_reasoning_heuristics | 禁用按模型名推理探测（别名 disable-reasoning-heuristics）。默认 false | `crates/jcode-config-types/src/lib.rs:518` |
| providers.<name>.models[].id | 模型 id。默认 "" | `crates/jcode-config-types/src/lib.rs:445` |
| providers.<name>.models[].reasoning | 显式启停该模型 /effort。默认 None | `crates/jcode-config-types/src/lib.rs:449` |
| providers.<name>.models[].reasoning_effort | 该模型激活时的 reasoning effort（别名 reasoning-effort）。默认 None | `crates/jcode-config-types/src/lib.rs:457` |
| providers.<name>.models[].context_window | 上下文窗口（别名 context_limit/context-length/context-window/context_length）。默认 None | `crates/jcode-config-types/src/lib.rs:466` |
| providers.<name>.models[].input | 该模型支持的输入模态列表。默认 [] | `crates/jcode-config-types/src/lib.rs:468` |
| agents.swarm_model | swarm/subagent 会话默认模型（可 inherit/coordinator）。默认 None | `crates/jcode-config-types/src/lib.rs:567` |
| agents.swarm_effort | swarm worker 默认 reasoning effort。默认 None | `crates/jcode-config-types/src/lib.rs:572` |
| agents.swarm_root_effort | light swarm 根推理档（none\|minimal\|low\|medium\|high\|xhigh\|max）。默认 None→max | `crates/jcode-config-types/src/lib.rs:575` |
| agents.swarm_deep_root_effort | deep swarm 根推理档。默认 None→max | `crates/jcode-config-types/src/lib.rs:577` |
| agents.swarm_spawn_mode | swarm agent 启动：inline(默认) \| visible/headed \| headless \| auto | `crates/jcode-config-types/src/lib.rs:579` |
| agents.swarm_gallery_max_pct | inline swarm gallery 占聊天高度上限 %(1-90)。默认 None→40 | `crates/jcode-config-types/src/lib.rs:584` |
| agents.swarm_strip_layout | inline swarm 条布局：vertical(默认) \| horizontal（别名 list/chips/strip） | `crates/jcode-config-types/src/lib.rs:590` |
| agents.memory_jev_provider | Jev 回忆 provider：auto(默认) \| jcode \| openrouter \| typesafe \| aimlapi | `crates/jcode-config-types/src/lib.rs:594` |
| agents.memory_jev_threshold | Jev 相关性概率下限。默认 0.8 | `crates/jcode-config-types/src/lib.rs:597` |
| agents.memory_model | 仅 extraction 用的模型覆盖（recall 不用）。默认 None | `crates/jcode-config-types/src/lib.rs:599` |
| agents.memory_sidecar_enabled | 允许可选自动 memory 抽取 sidecar。默认 true | `crates/jcode-config-types/src/lib.rs:603` |
| agents.memory_rerank_cadence | 旧设置，保留兼容，Jev recall 忽略。默认 3 | `crates/jcode-config-types/src/lib.rs:606` |
| agents.memory_rerank_votes | 旧设置，保留兼容。默认 2 | `crates/jcode-config-types/src/lib.rs:609` |
| agents.memory_rerank_min_agree | 旧设置，保留兼容。默认 2 | `crates/jcode-config-types/src/lib.rs:612` |
| agents.memory_embedding_backend | 旧/调试 embedding 后端，Jev recall 不用。默认 "local" | `crates/jcode-config-types/src/lib.rs:615` |
| agents.memory_embedding_model | backend=openai 时的 embedding 模型。默认 None→text-embedding-3-small | `crates/jcode-config-types/src/lib.rs:619` |
| agents.memory_embedding_base_url | embedding API base URL 覆盖。默认 None→https://api.openai.com/v1 | `crates/jcode-config-types/src/lib.rs:624` |
| agents.memory_embedding_dim | 远程 embedding 维度覆盖。默认 None(按模型推断) | `crates/jcode-config-types/src/lib.rs:628` |
| agents.swarm_max_concurrent_agents | 单 swarm 活跃 worker 上限(RAM 预算)，0=关闭该护栏。默认 32 | `crates/jcode-config-types/src/lib.rs:636` |
| terminal.spawn_hook | 接管 headed 会话启动的外部命令（配 JCODE_SPAWN_* 元数据）。默认 None | `crates/jcode-config-types/src/lib.rs:805` |
| terminal.focus_hook | 聚焦/唤起已存在会话窗口的外部命令（配 JCODE_FOCUS_*）。默认 None | `crates/jcode-config-types/src/lib.rs:816` |
| terminal.preferred | macOS Cmd+; 启动热键用的终端：ghostty\|iterm2\|wezterm\|warp\|alacritty\|vscode\|terminal。默认 None | `crates/jcode-config-types/src/lib.rs:826` |
| hooks.pre_tool_transform | 工具调用前同步输入变换器（stdin 收 tool input JSON，stdout 替换），单条或多条。默认 None | `crates/jcode-config-types/src/lib.rs:900` |
| hooks.pre_tool_transform_timeout_ms | 每个输入变换器超时毫秒。默认 500 | `crates/jcode-config-types/src/lib.rs:902` |
| hooks.turn_start | 回合开始时运行的钩子命令。默认 None | `crates/jcode-config-types/src/lib.rs:908` |
| hooks.turn_end | 回合结束时运行。默认 None | `crates/jcode-config-types/src/lib.rs:912` |
| hooks.session_start | 会话创建/恢复时运行。默认 None | `crates/jcode-config-types/src/lib.rs:916` |
| hooks.session_end | 会话正常关闭时运行。默认 None | `crates/jcode-config-types/src/lib.rs:919` |
| hooks.pre_tool | 每次工具调用前 gate 钩子（exit 2 阻止，stderr 回给模型）。默认 None | `crates/jcode-config-types/src/lib.rs:924` |
| hooks.post_tool | 每次工具调用后运行。默认 None | `crates/jcode-config-types/src/lib.rs:928` |
| hooks.pre_tool_timeout_ms | pre_tool gate 等待超时毫秒（fail open）。默认 5000 | `crates/jcode-config-types/src/lib.rs:931` |
| compaction.mode | 压缩模式：reactive(默认) \| proactive \| semantic | `crates/jcode-config-types/src/lib.rs:361` |
| compaction.lookahead_turns | [proactive] 预测 token 增长的向前回合数。默认 15 | `crates/jcode-config-types/src/lib.rs:364` |
| compaction.ewma_alpha | [proactive] token 增长平滑 EWMA alpha(0.0-1.0)。默认 0.3 | `crates/jcode-config-types/src/lib.rs:367` |
| compaction.proactive_floor | [proactive/semantic] 触发前最低上下文填充率。默认 0.40 | `crates/jcode-config-types/src/lib.rs:370` |
| compaction.min_samples | [proactive/semantic] 最少 token 快照数。默认 3 | `crates/jcode-config-types/src/lib.rs:373` |
| compaction.stall_window | [proactive/semantic] 无增长稳定回合数后抑制。默认 5 | `crates/jcode-config-types/src/lib.rs:376` |
| compaction.min_turns_between_compactions | [proactive/semantic] 两次压缩最小间隔回合。默认 10 | `crates/jcode-config-types/src/lib.rs:379` |
| compaction.topic_shift_threshold | [semantic] 话题切换余弦相似度阈值。默认 0.45 | `crates/jcode-config-types/src/lib.rs:382` |
| compaction.relevance_keep_threshold | [semantic] 逐字保留消息的余弦相似度。默认 0.65 | `crates/jcode-config-types/src/lib.rs:385` |
| compaction.goal_window_turns | [semantic] 构建当前目标 embedding 的最近回合数。默认 5 | `crates/jcode-config-types/src/lib.rs:388` |
| compaction.max_context_tokens | 压缩计量的 token 硬上限，0=用模型窗口。默认 0 | `crates/jcode-config-types/src/lib.rs:398` |
| ambient.enabled | 启用 ambient 模式。默认 false | `crates/jcode-config-types/src/lib.rs:1413` |
| ambient.provider | provider 覆盖。默认 None(自动) | `crates/jcode-config-types/src/lib.rs:1415` |
| ambient.model | 模型覆盖。默认 None(provider 最强) | `crates/jcode-config-types/src/lib.rs:1417` |
| ambient.allow_api_keys | 允许用 API key（否则仅 OAuth）。默认 false | `crates/jcode-config-types/src/lib.rs:1419` |
| ambient.api_daily_budget | 用 API key 时每日 token 预算。默认 None | `crates/jcode-config-types/src/lib.rs:1421` |
| ambient.min_interval_minutes | 循环最小间隔分钟。默认 5 | `crates/jcode-config-types/src/lib.rs:1423` |
| ambient.max_interval_minutes | 循环最大间隔分钟。默认 120 | `crates/jcode-config-types/src/lib.rs:1425` |
| ambient.pause_on_active_session | 用户有活跃会话时暂停。默认 true | `crates/jcode-config-types/src/lib.rs:1427` |
| ambient.proactive_work | 允许主动开发工作（vs 仅 garden）。默认 true | `crates/jcode-config-types/src/lib.rs:1429` |
| ambient.work_branch_prefix | 主动工作分支前缀。默认 "ambient/" | `crates/jcode-config-types/src/lib.rs:1431` |
| ambient.visible | 在终端窗口显示 ambient 循环。默认 true | `crates/jcode-config-types/src/lib.rs:1433` |
| notifications.turn_complete | 回合完成时发桌面通知。默认 true | `crates/jcode-config-types/src/lib.rs:1465` |
| notifications.turn_complete_min_secs | 通知的最短回合秒数。默认 120 | `crates/jcode-config-types/src/lib.rs:1468` |
| notifications.turn_complete_todo_min_secs | 有 todos 时的较低秒数阈值。默认 30 | `crates/jcode-config-types/src/lib.rs:1471` |
| notifications.turn_complete_only_when_unfocused | 仅终端窗口失焦时通知。默认 true | `crates/jcode-config-types/src/lib.rs:1474` |
| notifications.turn_complete_sound | macOS 完成提示音名，空=静音。默认 "Glass" | `crates/jcode-config-types/src/lib.rs:1478` |
| safety.ntfy_topic | ntfy.sh topic（push 通知需要）。默认 None | `crates/jcode-config-types/src/lib.rs:1498` |
| safety.ntfy_server | ntfy.sh 服务器 URL。默认 https://ntfy.sh | `crates/jcode-config-types/src/lib.rs:1500` |
| safety.desktop_notifications | 启用 notify-send 桌面通知。默认 true | `crates/jcode-config-types/src/lib.rs:1502` |
| safety.email_enabled | 启用邮件通知。默认 false | `crates/jcode-config-types/src/lib.rs:1504` |
| safety.email_to | 邮件收件人。默认 None | `crates/jcode-config-types/src/lib.rs:1506` |
| safety.email_smtp_host | SMTP 主机。默认 None | `crates/jcode-config-types/src/lib.rs:1508` |
| safety.email_smtp_port | SMTP 端口。默认 587 | `crates/jcode-config-types/src/lib.rs:1510` |
| safety.email_from | 邮件发件人。默认 None | `crates/jcode-config-types/src/lib.rs:1512` |
| safety.email_password | SMTP 密码（首选 JCODE_SMTP_PASSWORD）。默认 None | `crates/jcode-config-types/src/lib.rs:1514` |
| safety.email_imap_host | 接收回信的 IMAP 主机。默认 None | `crates/jcode-config-types/src/lib.rs:1516` |
| safety.email_imap_port | IMAP 端口。默认 993 | `crates/jcode-config-types/src/lib.rs:1518` |
| safety.email_reply_enabled | 启用邮件回复→agent 指令。默认 false | `crates/jcode-config-types/src/lib.rs:1520` |
| safety.telegram_enabled | 启用 Telegram 通知。默认 false | `crates/jcode-config-types/src/lib.rs:1522` |
| safety.telegram_bot_token | Telegram bot token。默认 None | `crates/jcode-config-types/src/lib.rs:1524` |
| safety.telegram_chat_id | Telegram chat ID。默认 None | `crates/jcode-config-types/src/lib.rs:1526` |
| safety.telegram_reply_enabled | 启用 Telegram 回复→指令。默认 false | `crates/jcode-config-types/src/lib.rs:1528` |
| safety.discord_enabled | 启用 Discord 通知。默认 false | `crates/jcode-config-types/src/lib.rs:1530` |
| safety.discord_bot_token | Discord bot token。默认 None | `crates/jcode-config-types/src/lib.rs:1532` |
| safety.discord_channel_id | Discord channel ID。默认 None | `crates/jcode-config-types/src/lib.rs:1534` |
| safety.discord_bot_user_id | Discord bot 用户 ID（过滤自身消息）。默认 None | `crates/jcode-config-types/src/lib.rs:1536` |
| safety.discord_reply_enabled | 启用 Discord 回复→指令。默认 false | `crates/jcode-config-types/src/lib.rs:1538` |
| safety.jade_relay_enabled | 启用 Jade 云 relay 通道（云邮箱远程控制）。默认 false | `crates/jcode-config-types/src/lib.rs:1540` |
| safety.jade_relay_api_base | Jade relay API base URL。默认 None | `crates/jcode-config-types/src/lib.rs:1542` |
| safety.jade_relay_token | Jade relay bearer token。默认 None | `crates/jcode-config-types/src/lib.rs:1544` |
| safety.jade_relay_token_id | Jade relay token id header（x-jade-token-id）。默认 None | `crates/jcode-config-types/src/lib.rs:1546` |
| safety.jade_relay_user_id | Jade relay user id（channel 作用域）。默认 None | `crates/jcode-config-types/src/lib.rs:1548` |
| safety.jade_relay_session_id | Jade relay 绑定的本机 session id。默认 None | `crates/jcode-config-types/src/lib.rs:1550` |
| safety.jade_relay_reply_enabled | 启用 Jade relay prompt→agent 指令。默认 false | `crates/jcode-config-types/src/lib.rs:1552` |
| safety.jade_relay_launch_enabled | 允许云设备命令开启本地 headed 会话。默认 false | `crates/jcode-config-types/src/lib.rs:1554` |
| safety.jade_relay_launch_working_dir | 远程启动 headed 会话的默认工作目录。默认 None | `crates/jcode-config-types/src/lib.rs:1556` |
| gateway.enabled | 启用 WebSocket 网关（iOS/web）。默认 false | `crates/jcode-config-types/src/lib.rs:1601` |
| gateway.port | 网关监听端口。默认 7643 | `crates/jcode-config-types/src/lib.rs:1603` |
| gateway.bind_addr | 绑定地址。默认 "0.0.0.0" | `crates/jcode-config-types/src/lib.rs:1605` |
| power.prevent_sleep_while_streaming | 有会话流式工作时阻止系统自动睡眠。默认 true（JCODE_DISABLE_POWER_INHIBIT 可强制关） | `crates/jcode-config-types/src/lib.rs:1630` |
| power.block_lid_close | macOS/Windows 合盖时仍继续工作。默认 true | `crates/jcode-config-types/src/lib.rs:1639` |
| autoreview.enabled | 新/恢复会话默认启用 autoreview。默认 false | `crates/jcode-config-types/src/lib.rs:955` |
| autoreview.model | autoreview reviewer 会话的模型覆盖。默认 None | `crates/jcode-config-types/src/lib.rs:957` |
| autojudge.enabled | 新/恢复会话默认启用 autojudge。默认 false | `crates/jcode-config-types/src/lib.rs:993` |
| autojudge.model | autojudge 会话的模型覆盖。默认 None | `crates/jcode-config-types/src/lib.rs:995` |
| sponsors.enabled | 启用第三方集成发现（discover_tools）。默认 true；false 时完全离线 | `crates/jcode-config-types/src/lib.rs:974` |
| sponsors.endpoint | 发现服务 base URL。默认 https://api.jcode.sh/v1/discovery（旧默认 api.solosystems.dev 也识别） | `crates/jcode-config-types/src/lib.rs:976` |
| launch_hotkeys.enabled | 是否安装全局启动热键。默认 None(未决定) | `crates/jcode-config-types/src/lib.rs:1689` |
| launch_hotkeys.entries | 显式 chord→目录 映射；空=内置默认（Cmd+;/Cmd+'/Cmd+Shift+'）。默认 [] | `crates/jcode-config-types/src/lib.rs:1691` |
| launch_hotkeys.imported | 自动导入是否已写入 entries（只 bake 一次）。默认 false | `crates/jcode-config-types/src/lib.rs:1694` |
| launch_hotkeys.entries[].chord | jcode 风格 chord，如 cmd+;、cmd+[ 。默认 "" | `crates/jcode-config-types/src/lib.rs:1664` |
| launch_hotkeys.entries[].dir | 打开的目录（绝对路径或 $HOME/$LAST_DIR/$LAST_REPO）。默认 "" | `crates/jcode-config-types/src/lib.rs:1667` |
| launch_hotkeys.entries[].label | 人类可读短标签（用于提示）。默认 "" | `crates/jcode-config-types/src/lib.rs:1670` |
| launch_hotkeys.entries[].self_dev | 以 self-dev 会话打开该目录。默认 false | `crates/jcode-config-types/src/lib.rs:1673` |

### 28.5 环境变量覆盖（JCODE_*）（共 171 条）

> 数法：环境变量覆盖项 (crates/jcode-base/src/config/env_overrides.rs, apply_env_overrides) — 共 171 条（170 个 JCODE_* + GOOGLE_CLOUD_PROJECT/_ID）。env 覆盖对应文件键，进程内生效。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| JCODE_WAKE_MODE | → server.wake_mode（internal\|external；默认 internal） | `crates/jcode-base/src/config/env_overrides.rs:11` |
| JCODE_SCROLL_UP_KEY | → keybindings.scroll_up | `crates/jcode-base/src/config/env_overrides.rs:18` |
| JCODE_SCROLL_DOWN_KEY | → keybindings.scroll_down | `crates/jcode-base/src/config/env_overrides.rs:21` |
| JCODE_SCROLL_PAGE_UP_KEY | → keybindings.scroll_page_up | `crates/jcode-base/src/config/env_overrides.rs:24` |
| JCODE_SCROLL_PAGE_DOWN_KEY | → keybindings.scroll_page_down | `crates/jcode-base/src/config/env_overrides.rs:27` |
| JCODE_MODEL_SWITCH_KEY | → keybindings.model_switch_next | `crates/jcode-base/src/config/env_overrides.rs:30` |
| JCODE_MODEL_SWITCH_PREV_KEY | → keybindings.model_switch_prev | `crates/jcode-base/src/config/env_overrides.rs:33` |
| JCODE_EFFORT_INCREASE_KEY | → keybindings.effort_increase | `crates/jcode-base/src/config/env_overrides.rs:36` |
| JCODE_EFFORT_DECREASE_KEY | → keybindings.effort_decrease | `crates/jcode-base/src/config/env_overrides.rs:39` |
| JCODE_CENTERED_TOGGLE_KEY | → keybindings.centered_toggle | `crates/jcode-base/src/config/env_overrides.rs:42` |
| JCODE_SCROLL_PROMPT_UP_KEY | → keybindings.scroll_prompt_up | `crates/jcode-base/src/config/env_overrides.rs:45` |
| JCODE_SCROLL_PROMPT_DOWN_KEY | → keybindings.scroll_prompt_down | `crates/jcode-base/src/config/env_overrides.rs:48` |
| JCODE_SCROLL_BOOKMARK_KEY | → keybindings.scroll_bookmark | `crates/jcode-base/src/config/env_overrides.rs:51` |
| JCODE_SCROLL_UP_FALLBACK_KEY | → keybindings.scroll_up_fallback | `crates/jcode-base/src/config/env_overrides.rs:54` |
| JCODE_SCROLL_DOWN_FALLBACK_KEY | → keybindings.scroll_down_fallback | `crates/jcode-base/src/config/env_overrides.rs:57` |
| JCODE_WORKSPACE_LEFT_KEY | → keybindings.workspace_left | `crates/jcode-base/src/config/env_overrides.rs:60` |
| JCODE_WORKSPACE_DOWN_KEY | → keybindings.workspace_down | `crates/jcode-base/src/config/env_overrides.rs:63` |
| JCODE_WORKSPACE_UP_KEY | → keybindings.workspace_up | `crates/jcode-base/src/config/env_overrides.rs:66` |
| JCODE_WORKSPACE_RIGHT_KEY | → keybindings.workspace_right | `crates/jcode-base/src/config/env_overrides.rs:69` |
| JCODE_SIDE_PANEL_TOGGLE_KEY | → keybindings.side_panel_toggle | `crates/jcode-base/src/config/env_overrides.rs:72` |
| JCODE_COPY_SELECTION_TOGGLE_KEY | → keybindings.copy_selection_toggle | `crates/jcode-base/src/config/env_overrides.rs:75` |
| JCODE_DIAGRAM_PANE_TOGGLE_KEY | → keybindings.diagram_pane_toggle | `crates/jcode-base/src/config/env_overrides.rs:78` |
| JCODE_DIAGRAM_PANE_VISIBILITY_TOGGLE_KEY | → keybindings.diagram_pane_visibility_toggle | `crates/jcode-base/src/config/env_overrides.rs:81` |
| JCODE_TYPING_SCROLL_LOCK_TOGGLE_KEY | → keybindings.typing_scroll_lock_toggle | `crates/jcode-base/src/config/env_overrides.rs:84` |
| JCODE_DIFF_MODE_CYCLE_KEY | → keybindings.diff_mode_cycle | `crates/jcode-base/src/config/env_overrides.rs:87` |
| JCODE_INFO_WIDGET_TOGGLE_KEY | → keybindings.info_widget_toggle | `crates/jcode-base/src/config/env_overrides.rs:90` |
| JCODE_NEW_TERMINAL_KEY | → keybindings.new_terminal | `crates/jcode-base/src/config/env_overrides.rs:93` |
| JCODE_VOICE_INPUT_KEY | → keybindings.voice_input | `crates/jcode-base/src/config/env_overrides.rs:96` |
| JCODE_DICTATION_RECORDER | → dictation.recorder | `crates/jcode-base/src/config/env_overrides.rs:99` |
| JCODE_DICTATION_COMMAND | → dictation.command | `crates/jcode-base/src/config/env_overrides.rs:104` |
| JCODE_DICTATION_MODE | → dictation.mode（insert\|append\|replace\|send） | `crates/jcode-base/src/config/env_overrides.rs:107` |
| JCODE_DICTATION_KEY | → dictation.key | `crates/jcode-base/src/config/env_overrides.rs:115` |
| JCODE_DICTATION_TIMEOUT_SECS | → dictation.timeout_secs（默认 90） | `crates/jcode-base/src/config/env_overrides.rs:118` |
| JCODE_TOOL_PROFILE | → tools.profile | `crates/jcode-base/src/config/env_overrides.rs:125` |
| JCODE_TOOLS | → tools.enabled（逗号/换行分隔） | `crates/jcode-base/src/config/env_overrides.rs:128` |
| JCODE_DISABLED_TOOLS | → tools.disabled | `crates/jcode-base/src/config/env_overrides.rs:131` |
| JCODE_DISABLE_BASE_TOOLS | → tools.disable_base_tools | `crates/jcode-base/src/config/env_overrides.rs:134` |
| JCODE_MCP_TOOLS | → tools.mcp_tools（auto\|eager\|deferred） | `crates/jcode-base/src/config/env_overrides.rs:139` |
| JCODE_MCP_TOOLS_TOKEN_THRESHOLD | → tools.mcp_tools_token_threshold（默认 8000） | `crates/jcode-base/src/config/env_overrides.rs:144` |
| JCODE_ACP_PROFILE | → acp.profile（仅 standard\|extended\|full） | `crates/jcode-base/src/config/env_overrides.rs:151` |
| JCODE_ACP_TOOL_PROFILE | → acp.tool_profile | `crates/jcode-base/src/config/env_overrides.rs:157` |
| JCODE_DIFF_MODE | → display.diff_mode | `crates/jcode-base/src/config/env_overrides.rs:165` |
| JCODE_SHOW_DIFFS | → display.diff_mode（旧布尔，true=inline false=off） | `crates/jcode-base/src/config/env_overrides.rs:176` |
| JCODE_PIN_IMAGES | → display.pin_images | `crates/jcode-base/src/config/env_overrides.rs:185` |
| JCODE_PIN_TODOS | → display.pin_todos | `crates/jcode-base/src/config/env_overrides.rs:190` |
| JCODE_DISPLAY_CENTERED | → display.centered | `crates/jcode-base/src/config/env_overrides.rs:195` |
| JCODE_QUEUE_MODE | → display.queue_mode | `crates/jcode-base/src/config/env_overrides.rs:200` |
| JCODE_AUTO_SERVER_RELOAD | → display.auto_server_reload | `crates/jcode-base/src/config/env_overrides.rs:205` |
| JCODE_MOUSE_CAPTURE | → display.mouse_capture | `crates/jcode-base/src/config/env_overrides.rs:210` |
| JCODE_DEBUG_SOCKET | → display.debug_socket | `crates/jcode-base/src/config/env_overrides.rs:215` |
| JCODE_NO_EMOJI | → display.emoji（取反） | `crates/jcode-base/src/config/env_overrides.rs:220` |
| JCODE_SHOW_THINKING | → display.show_thinking | `crates/jcode-base/src/config/env_overrides.rs:225` |
| JCODE_REASONING_DISPLAY | → display.reasoning_display（off\|full\|current） | `crates/jcode-base/src/config/env_overrides.rs:230` |
| JCODE_DEFAULT_REASONING_DISPLAY | → display.reasoning_display（仅当用户未显式设置时的前端默认） | `crates/jcode-base/src/config/env_overrides.rs:239` |
| JCODE_MARKDOWN_SPACING | → display.markdown_spacing（compact\|document） | `crates/jcode-base/src/config/env_overrides.rs:244` |
| JCODE_IDLE_ANIMATION | → display.idle_animation | `crates/jcode-base/src/config/env_overrides.rs:253` |
| JCODE_PROMPT_ENTRY_ANIMATION | → display.prompt_entry_animation | `crates/jcode-base/src/config/env_overrides.rs:258` |
| JCODE_DISABLED_ANIMATIONS | → display.disabled_animations | `crates/jcode-base/src/config/env_overrides.rs:263` |
| JCODE_ACTIVE_SESSIONS_MANAGER | → display.active_sessions_manager | `crates/jcode-base/src/config/env_overrides.rs:266` |
| JCODE_EXTERNAL_SESSIONS | → display.external_sessions | `crates/jcode-base/src/config/env_overrides.rs:271` |
| JCODE_PERFORMANCE | → display.performance（auto\|full\|reduced\|minimal） | `crates/jcode-base/src/config/env_overrides.rs:276` |
| JCODE_ANIMATION_FPS | → display.animation_fps（clamp 1-120） | `crates/jcode-base/src/config/env_overrides.rs:282` |
| JCODE_REDRAW_FPS | → display.redraw_fps（clamp 1-120） | `crates/jcode-base/src/config/env_overrides.rs:287` |
| JCODE_COPY_BADGE_ALT_LABEL | → display.copy_badge_alt_label | `crates/jcode-base/src/config/env_overrides.rs:292` |
| JCODE_COMPACT_NOTIFICATIONS | → display.compact_notifications | `crates/jcode-base/src/config/env_overrides.rs:295` |
| JCODE_SHOW_AGENTGREP_OUTPUT | → display.show_agentgrep_output | `crates/jcode-base/src/config/env_overrides.rs:300` |
| JCODE_SHOW_BASH_OUTPUT | → display.show_bash_output | `crates/jcode-base/src/config/env_overrides.rs:305` |
| JCODE_TOOL_CALL_DETAILS | → display.tool_call_details | `crates/jcode-base/src/config/env_overrides.rs:310` |
| JCODE_LATEX_RENDERING | → display.latex_rendering（none\|unicode\|image） | `crates/jcode-base/src/config/env_overrides.rs:315` |
| JCODE_CHAT_NATIVE_SCROLLBAR | → display.native_scrollbars.chat | `crates/jcode-base/src/config/env_overrides.rs:320` |
| JCODE_SIDE_PANEL_NATIVE_SCROLLBAR | → display.native_scrollbars.side_panel | `crates/jcode-base/src/config/env_overrides.rs:325` |
| JCODE_MEMORY_ENABLED | → features.memory | `crates/jcode-base/src/config/env_overrides.rs:332` |
| JCODE_SWARM_ENABLED | → features.swarm | `crates/jcode-base/src/config/env_overrides.rs:337` |
| JCODE_ENABLE_MERMAID | → features.mermaid | `crates/jcode-base/src/config/env_overrides.rs:342` |
| JCODE_CHECK_UPDATES | → features.check_updates | `crates/jcode-base/src/config/env_overrides.rs:347` |
| JCODE_AUTO_POKE | → features.auto_poke | `crates/jcode-base/src/config/env_overrides.rs:352` |
| JCODE_MESSAGE_TIMESTAMPS | → features.message_timestamps | `crates/jcode-base/src/config/env_overrides.rs:357` |
| JCODE_PERSIST_MEMORY_INJECTIONS | → features.persist_memory_injections | `crates/jcode-base/src/config/env_overrides.rs:362` |
| JCODE_KV_CACHE_MISS_NOTICES | → features.kv_cache_miss_notices | `crates/jcode-base/src/config/env_overrides.rs:367` |
| JCODE_UPDATE_CHANNEL | → features.update_channel（stable\|main） | `crates/jcode-base/src/config/env_overrides.rs:372` |
| JCODE_SWARM_MODEL | → agents.swarm_model（空=None） | `crates/jcode-base/src/config/env_overrides.rs:379` |
| JCODE_SWARM_EFFORT | → agents.swarm_effort（空=None） | `crates/jcode-base/src/config/env_overrides.rs:387` |
| JCODE_SWARM_ROOT_EFFORT | → agents.swarm_root_effort（空=None） | `crates/jcode-base/src/config/env_overrides.rs:397` |
| JCODE_SWARM_DEEP_ROOT_EFFORT | → agents.swarm_deep_root_effort（空=None） | `crates/jcode-base/src/config/env_overrides.rs:401` |
| JCODE_SWARM_SPAWN_MODE | → agents.swarm_spawn_mode（visible\|headless\|inline\|auto） | `crates/jcode-base/src/config/env_overrides.rs:410` |
| JCODE_SWARM_STRIP_LAYOUT | → agents.swarm_strip_layout（vertical\|horizontal） | `crates/jcode-base/src/config/env_overrides.rs:415` |
| JCODE_SWARM_MAX_CONCURRENT_AGENTS | → agents.swarm_max_concurrent_agents | `crates/jcode-base/src/config/env_overrides.rs:420` |
| JCODE_MEMORY_JEV_PROVIDER | → agents.memory_jev_provider | `crates/jcode-base/src/config/env_overrides.rs:425` |
| JCODE_MEMORY_MODEL | → agents.memory_model（空=None） | `crates/jcode-base/src/config/env_overrides.rs:428` |
| JCODE_MEMORY_SIDECAR_ENABLED | → agents.memory_sidecar_enabled | `crates/jcode-base/src/config/env_overrides.rs:436` |
| JCODE_MEMORY_EMBEDDING_BACKEND | → agents.memory_embedding_backend | `crates/jcode-base/src/config/env_overrides.rs:441` |
| JCODE_MEMORY_EMBEDDING_MODEL | → agents.memory_embedding_model（空=None） | `crates/jcode-base/src/config/env_overrides.rs:447` |
| JCODE_MEMORY_EMBEDDING_BASE_URL | → agents.memory_embedding_base_url（空=None） | `crates/jcode-base/src/config/env_overrides.rs:455` |
| JCODE_MEMORY_EMBEDDING_DIM | → agents.memory_embedding_dim | `crates/jcode-base/src/config/env_overrides.rs:463` |
| JCODE_SPAWN_HOOK | → terminal.spawn_hook（空=禁用配置钩子） | `crates/jcode-base/src/config/env_overrides.rs:470` |
| JCODE_FOCUS_HOOK | → terminal.focus_hook（空=禁用配置钩子） | `crates/jcode-base/src/config/env_overrides.rs:479` |
| JCODE_HOOK_TURN_START | → hooks.turn_start（空=禁用；"[...]" 解析为命令数组） | `crates/jcode-base/src/config/env_overrides.rs:510` |
| JCODE_HOOK_TURN_END | → hooks.turn_end | `crates/jcode-base/src/config/env_overrides.rs:511` |
| JCODE_HOOK_SESSION_START | → hooks.session_start | `crates/jcode-base/src/config/env_overrides.rs:512` |
| JCODE_HOOK_SESSION_END | → hooks.session_end | `crates/jcode-base/src/config/env_overrides.rs:513` |
| JCODE_HOOK_PRE_TOOL | → hooks.pre_tool | `crates/jcode-base/src/config/env_overrides.rs:514` |
| JCODE_HOOK_PRE_TOOL_TRANSFORM | → hooks.pre_tool_transform | `crates/jcode-base/src/config/env_overrides.rs:515` |
| JCODE_HOOK_PRE_TOOL_TRANSFORM_TIMEOUT_MS | → hooks.pre_tool_transform_timeout_ms（默认 500） | `crates/jcode-base/src/config/env_overrides.rs:519` |
| JCODE_HOOK_POST_TOOL | → hooks.post_tool | `crates/jcode-base/src/config/env_overrides.rs:524` |
| JCODE_HOOK_PRE_TOOL_TIMEOUT_MS | → hooks.pre_tool_timeout_ms（默认 5000） | `crates/jcode-base/src/config/env_overrides.rs:525` |
| JCODE_WEBSEARCH_ENGINE | → websearch.engine | `crates/jcode-base/src/config/env_overrides.rs:532` |
| JCODE_WEBSEARCH_FALLBACK_ENGINES | → websearch.fallback_engines | `crates/jcode-base/src/config/env_overrides.rs:537` |
| JCODE_BING_API_KEY | → websearch.bing_api_key | `crates/jcode-base/src/config/env_overrides.rs:546` |
| JCODE_BING_API_KEY_ENV | → websearch.bing_api_key_env | `crates/jcode-base/src/config/env_overrides.rs:551` |
| JCODE_BING_MARKET | → websearch.bing_market | `crates/jcode-base/src/config/env_overrides.rs:556` |
| JCODE_SEARXNG_URL | → websearch.searxng_url | `crates/jcode-base/src/config/env_overrides.rs:561` |
| JCODE_WEBSEARCH_PREFER_NATIVE | → websearch.prefer_native | `crates/jcode-base/src/config/env_overrides.rs:566` |
| JCODE_WEBSEARCH_NATIVE_MAX_USES | → websearch.native_max_uses（0=None 无上限） | `crates/jcode-base/src/config/env_overrides.rs:571` |
| JCODE_WEBSEARCH_NATIVE_ALLOWED_DOMAINS | → websearch.native_allowed_domains | `crates/jcode-base/src/config/env_overrides.rs:576` |
| JCODE_WEBSEARCH_NATIVE_BLOCKED_DOMAINS | → websearch.native_blocked_domains | `crates/jcode-base/src/config/env_overrides.rs:579` |
| JCODE_TRUSTED_EXTERNAL_AUTH_SOURCES | → auth.trusted_external_sources / trusted_external_source_paths（含 '\|' 归入 paths） | `crates/jcode-base/src/config/env_overrides.rs:583` |
| JCODE_AUTOREVIEW_ENABLED | → autoreview.enabled | `crates/jcode-base/src/config/env_overrides.rs:602` |
| JCODE_AUTOREVIEW_MODEL | → autoreview.model（空=None） | `crates/jcode-base/src/config/env_overrides.rs:607` |
| JCODE_AUTOJUDGE_ENABLED | → autojudge.enabled | `crates/jcode-base/src/config/env_overrides.rs:617` |
| JCODE_AUTOJUDGE_MODEL | → autojudge.model（空=None） | `crates/jcode-base/src/config/env_overrides.rs:622` |
| JCODE_AMBIENT_ENABLED | → ambient.enabled | `crates/jcode-base/src/config/env_overrides.rs:632` |
| JCODE_AMBIENT_PROVIDER | → ambient.provider | `crates/jcode-base/src/config/env_overrides.rs:637` |
| JCODE_AMBIENT_MODEL | → ambient.model | `crates/jcode-base/src/config/env_overrides.rs:640` |
| JCODE_AMBIENT_MIN_INTERVAL | → ambient.min_interval_minutes | `crates/jcode-base/src/config/env_overrides.rs:643` |
| JCODE_AMBIENT_MAX_INTERVAL | → ambient.max_interval_minutes | `crates/jcode-base/src/config/env_overrides.rs:648` |
| JCODE_AMBIENT_PROACTIVE | → ambient.proactive_work | `crates/jcode-base/src/config/env_overrides.rs:653` |
| JCODE_NTFY_TOPIC | → safety.ntfy_topic | `crates/jcode-base/src/config/env_overrides.rs:660` |
| JCODE_NTFY_SERVER | → safety.ntfy_server | `crates/jcode-base/src/config/env_overrides.rs:663` |
| JCODE_SMTP_PASSWORD | → safety.email_password | `crates/jcode-base/src/config/env_overrides.rs:666` |
| JCODE_EMAIL_TO | → safety.email_to（并置 email_enabled=true） | `crates/jcode-base/src/config/env_overrides.rs:669` |
| JCODE_IMAP_HOST | → safety.email_imap_host | `crates/jcode-base/src/config/env_overrides.rs:673` |
| JCODE_EMAIL_REPLY_ENABLED | → safety.email_reply_enabled | `crates/jcode-base/src/config/env_overrides.rs:676` |
| JCODE_TELEGRAM_BOT_TOKEN | → safety.telegram_bot_token（并置 telegram_enabled=true） | `crates/jcode-base/src/config/env_overrides.rs:681` |
| JCODE_TELEGRAM_CHAT_ID | → safety.telegram_chat_id | `crates/jcode-base/src/config/env_overrides.rs:685` |
| JCODE_TELEGRAM_REPLY_ENABLED | → safety.telegram_reply_enabled | `crates/jcode-base/src/config/env_overrides.rs:688` |
| JCODE_DISCORD_BOT_TOKEN | → safety.discord_bot_token（并置 discord_enabled=true） | `crates/jcode-base/src/config/env_overrides.rs:693` |
| JCODE_DISCORD_CHANNEL_ID | → safety.discord_channel_id | `crates/jcode-base/src/config/env_overrides.rs:697` |
| JCODE_DISCORD_BOT_USER_ID | → safety.discord_bot_user_id | `crates/jcode-base/src/config/env_overrides.rs:700` |
| JCODE_DISCORD_REPLY_ENABLED | → safety.discord_reply_enabled | `crates/jcode-base/src/config/env_overrides.rs:703` |
| JCODE_JADE_RELAY_API_BASE | → safety.jade_relay_api_base | `crates/jcode-base/src/config/env_overrides.rs:709` |
| JCODE_JADE_RELAY_TOKEN | → safety.jade_relay_token（并置 jade_relay_enabled=true） | `crates/jcode-base/src/config/env_overrides.rs:712` |
| JCODE_JADE_RELAY_TOKEN_ID | → safety.jade_relay_token_id | `crates/jcode-base/src/config/env_overrides.rs:716` |
| JCODE_JADE_RELAY_USER_ID | → safety.jade_relay_user_id | `crates/jcode-base/src/config/env_overrides.rs:719` |
| JCODE_JADE_RELAY_SESSION_ID | → safety.jade_relay_session_id | `crates/jcode-base/src/config/env_overrides.rs:722` |
| JCODE_JADE_RELAY_ENABLED | → safety.jade_relay_enabled | `crates/jcode-base/src/config/env_overrides.rs:725` |
| JCODE_JADE_RELAY_REPLY_ENABLED | → safety.jade_relay_reply_enabled | `crates/jcode-base/src/config/env_overrides.rs:730` |
| JCODE_JADE_RELAY_LAUNCH_ENABLED | → safety.jade_relay_launch_enabled | `crates/jcode-base/src/config/env_overrides.rs:735` |
| JCODE_JADE_RELAY_LAUNCH_WORKING_DIR | → safety.jade_relay_launch_working_dir | `crates/jcode-base/src/config/env_overrides.rs:740` |
| JCODE_AMBIENT_VISIBLE | → ambient.visible | `crates/jcode-base/src/config/env_overrides.rs:746` |
| JCODE_GATEWAY_ENABLED | → gateway.enabled | `crates/jcode-base/src/config/env_overrides.rs:753` |
| JCODE_GATEWAY_PORT | → gateway.port | `crates/jcode-base/src/config/env_overrides.rs:758` |
| JCODE_GATEWAY_BIND_ADDR | → gateway.bind_addr | `crates/jcode-base/src/config/env_overrides.rs:763` |
| JCODE_PREVENT_SLEEP_WHILE_STREAMING | → power.prevent_sleep_while_streaming | `crates/jcode-base/src/config/env_overrides.rs:771` |
| JCODE_BLOCK_LID_CLOSE | → power.block_lid_close | `crates/jcode-base/src/config/env_overrides.rs:776` |
| JCODE_MODEL | → provider.default_model | `crates/jcode-base/src/config/env_overrides.rs:783` |
| JCODE_PROVIDER | → provider.default_provider（小写化） | `crates/jcode-base/src/config/env_overrides.rs:786` |
| JCODE_OPENAI_REASONING_EFFORT | → provider.openai_reasoning_effort | `crates/jcode-base/src/config/env_overrides.rs:792` |
| JCODE_ANTHROPIC_REASONING_EFFORT | → provider.anthropic_reasoning_effort | `crates/jcode-base/src/config/env_overrides.rs:798` |
| JCODE_OPENAI_TRANSPORT | → provider.openai_transport | `crates/jcode-base/src/config/env_overrides.rs:804` |
| JCODE_OPENAI_SERVICE_TIER | → provider.openai_service_tier | `crates/jcode-base/src/config/env_overrides.rs:810` |
| JCODE_OPENAI_NATIVE_COMPACTION_MODE | → provider.openai_native_compaction_mode | `crates/jcode-base/src/config/env_overrides.rs:816` |
| JCODE_OPENAI_NATIVE_COMPACTION_THRESHOLD_TOKENS | → provider.openai_native_compaction_threshold_tokens（>0 才应用） | `crates/jcode-base/src/config/env_overrides.rs:822` |
| JCODE_PRESERVE_REASONING_CONTEXT | → provider.preserve_reasoning_context | `crates/jcode-base/src/config/env_overrides.rs:829` |
| JCODE_CROSS_PROVIDER_FAILOVER | → provider.cross_provider_failover（countdown\|manual） | `crates/jcode-base/src/config/env_overrides.rs:834` |
| JCODE_SAME_PROVIDER_ACCOUNT_FAILOVER | → provider.same_provider_account_failover | `crates/jcode-base/src/config/env_overrides.rs:839` |
| JCODE_STREAM_IDLE_TIMEOUT_SECS | → provider.stream_idle_timeout_secs（>0） | `crates/jcode-base/src/config/env_overrides.rs:844` |
| JCODE_MAX_RETRIES | → provider.max_retries（>0） | `crates/jcode-base/src/config/env_overrides.rs:851` |
| JCODE_RETRY_BACKOFF_CAP_SECS | → provider.retry_backoff_cap_secs（>0） | `crates/jcode-base/src/config/env_overrides.rs:857` |
| JCODE_COPILOT_PREMIUM | → provider.copilot_premium（也做 config→env 方向传播） | `crates/jcode-base/src/config/env_overrides.rs:866` |
| JCODE_GEMINI_FORCE_OAUTH | → provider.gemini_force_oauth | `crates/jcode-base/src/config/env_overrides.rs:881` |
| GOOGLE_CLOUD_PROJECT | → provider.gemini_project（旧别名 GOOGLE_CLOUD_PROJECT_ID 可回退） | `crates/jcode-base/src/config/env_overrides.rs:885` |

### 28.6 /config 分支（共 4 条）

> 数法：/config 命令可读写项 (crates/jcode-tui/src/tui/app/commands.rs) — 共 4 条；无 config get/set，读=display_string()，写=直接改 config.toml。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| /config | 只读：打印 config().display_string()（键集合见 crates/jcode-base/src/config/display_summary.rs） | `crates/jcode-tui/src/tui/app/commands.rs:3581` |
| /config init \| /config create | 写默认配置文件（default_file.rs 模板）到 ~/.jcode/config.toml | `crates/jcode-tui/src/tui/app/commands.rs:3592` |
| /config edit | 用 $EDITOR 打开 config.toml（不存在则先创建默认文件） | `crates/jcode-tui/src/tui/app/commands.rs:3620` |
| /config <其他子命令> | 报用法错误：Usage: /config (show), /config init (create), /config edit (open in editor) | `crates/jcode-tui/src/tui/app/commands.rs:3675` |

### 28.7 KEYBINDING_DEFAULTS 默认值表（共 23 条）

> 数法：[keybindings] (KeybindingsConfig, crates/jcode-config-types/src/lib.rs:1001-1077) — 共 33 条；权威默认常量表 `crates/jcode-config-types/src/keybindings.rs:195-350` 逐 `KeybindingDefault` 元素（前 23 个 id，:197-343）；与 §10 互参，本节保留自己的行。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `scroll_up` | 向上滚动一档。默认 macOS/其他 ctrl+shift+k | `crates/jcode-config-types/src/keybindings.rs:197` |
| `scroll_down` | 向下滚动一档。默认 macOS/其他 ctrl+shift+j | `crates/jcode-config-types/src/keybindings.rs:204` |
| `scroll_page_up` | 向上翻一页。默认 macOS/其他 alt+u | `crates/jcode-config-types/src/keybindings.rs:210` |
| `scroll_page_down` | 向下翻一页。默认 macOS/其他 alt+d | `crates/jcode-config-types/src/keybindings.rs:216` |
| `model_switch_next` | 切换到下一个模型。默认 ctrl+tab | `crates/jcode-config-types/src/keybindings.rs:222` |
| `model_switch_prev` | 切换到上一个模型。默认 ctrl+shift+tab | `crates/jcode-config-types/src/keybindings.rs:228` |
| `fallback_switch` | 接受错误后 fallback 提议（换模型/认证并重发）。默认 ctrl+y | `crates/jcode-config-types/src/keybindings.rs:234` |
| `effort_increase` | 提高 reasoning effort。默认 macOS cmd+right / 其他 alt+right | `crates/jcode-config-types/src/keybindings.rs:240` |
| `effort_decrease` | 降低 reasoning effort。默认 macOS cmd+left / 其他 alt+left | `crates/jcode-config-types/src/keybindings.rs:247` |
| `centered_toggle` | 切换居中模式。默认 alt+c | `crates/jcode-config-types/src/keybindings.rs:254` |
| `scroll_prompt_up` | 跳到上一条用户 prompt。默认 ctrl+k | `crates/jcode-config-types/src/keybindings.rs:260` |
| `scroll_prompt_down` | 跳到下一条用户 prompt。默认 ctrl+j | `crates/jcode-config-types/src/keybindings.rs:268` |
| `scroll_bookmark` | 滚动书签开关（暂存位置/回到底部/返回）。默认 ctrl+g | `crates/jcode-config-types/src/keybindings.rs:274` |
| `auto_poke_toggle` | 切换 auto-poke。默认 ctrl+p；空串禁用 | `crates/jcode-config-types/src/keybindings.rs:280` |
| `scroll_up_fallback` | 可选备用上滚键。默认 unbound（各平台） | `crates/jcode-config-types/src/keybindings.rs:286` |
| `scroll_down_fallback` | 可选备用下滚键。默认 unbound（各平台） | `crates/jcode-config-types/src/keybindings.rs:294` |
| `workspace_left` | 工作区左移。默认 alt+h（可逗号分隔多别名） | `crates/jcode-config-types/src/keybindings.rs:300` |
| `workspace_down` | 工作区下移。默认 alt+j | `crates/jcode-config-types/src/keybindings.rs:306` |
| `workspace_up` | 工作区上移。默认 alt+k | `crates/jcode-config-types/src/keybindings.rs:312` |
| `workspace_right` | 工作区右移。默认 alt+l | `crates/jcode-config-types/src/keybindings.rs:318` |
| `new_terminal` | 新终端窗口开新 jcode 会话。默认 macOS cmd+shift+; / 其他 alt+shift+; | `crates/jcode-config-types/src/keybindings.rs:324` |
| `open_resume` | 打开 /resume 会话选择器。默认 macOS cmd+b / 其他 alt+r；空串禁用 | `crates/jcode-config-types/src/keybindings.rs:335` |
| `voice_input` | 内置语音输入起停（Nari 转写）。默认 ctrl+space；空串禁用 | `crates/jcode-config-types/src/keybindings.rs:343` |
## 附. 没查完的 / 已知缺口

> 已在 §20–§27 清掉的条目：CLI 子命令内标志未逐 flag 成行、`command_accepts_args` 未逐条展开、远端键位未逐条枚举、account/login picker 键位未列、侧栏 page id 未穷举、两处 [未核实]（inline picker 收藏热键 / `new_terminal` 默认）、纯视觉件未单列。以下为仍未清 / 新并入的缺口。

界面的缺口（payload gaps 原样抄录）：

- 权限/审批模式：omp 有 permission-mode，jcode 全仓 grep 无 PermissionMode/permission_mode/approval_mode/sandbox_mode —— 判定 jcode 无此 UI（非漏查）。
- KEYBINDING_DEFAULTS(keybindings.rs:230-345) 只有 23 条 id，而 KeybindingsConfig 有 32 个键位字段；缺口 9 条(side_panel_toggle/copy_selection_toggle/diagram_pane_toggle/diagram_pane_visibility_toggle/typing_scroll_lock_toggle/diff_mode_cycle/info_widget_toggle/todo_card_toggle/swarm_panel_focus) 不在任何注册表内，其默认值只以硬编码 fallback 参数存在于 lib.rs:1109-1117 —— 无单一注册表可穷举，需读 default() 字面量。
- remote/key_handling.rs 的 Enter 分支内嵌约 60+ 个 slash 命令(/rewind /reload /update /client-reload /server-reload /continue /rebuild /quit /model /models /effort /fast /transport /subagent /subagent-model /account /autoreview /autojudge /workspace 等)，属命令面而非键位面，本次未逐条展开。
- Managed 侧栏页 id 无法静态穷举：side_panel/panel 工具的 page_id 是自由字符串参数(crates/jcode-app-core/src/tool/side_panel.rs:62-80)，模型可写入任意 id；只有固定来源的 id(goals/goal.<id>/image.<id>/catchup/observe/split_view/session_todos/linked-markdown:<path>) 可列全。
- session picker 完整键位表未逐行展开(入口 crates/jcode-tui/src/tui/app/inline_interactive.rs:3063 → crates/jcode-tui/src/tui/session_picker.rs handle_overlay_key)，超出本次 account/login 范围；已知其中 KeyCode::Char('d') 仅切换测试会话显示(:1258)。
- server_events.rs(2967 行) 未逐条穷举全部 ServerEvent 分支的界面效果；G1c 只列了远程专属且直接影响 UI 的代表性分支。

命令 / CLI 面的缺口（payload gaps 原样抄录）：

- gap①（CLI 子命令自己的 flag 未逐 flag 成行）：**已清**。结论=列全 186 条（顶层 65 + 嵌套 121），逐 flag 一行给出 name/what/所属子命令/src。依据 = src/cli/args.rs 是唯一 clap 定义处（grep `#[arg(` 在 src/cli/ 仅命中 args.rs；dispatch.rs 只做 routing，无 flag 定义）。
- gap②（command_accepts_args 未逐条展开）：**已清**。结论=55 条全部列出（1762-1816）。但必须注明代码事实：该函数是纯 bool 白名单（`matches!(cmd.trim(), ...)`，1759-1761），**不编码任何 per-command 参数形状**；它只决定 tab 补全命中后是否追加尾空格（调用点 1633/1652/1693/1710）。因此“命令→参数形状”无法从本函数静态读出，只能读出“该命令接受参数(yes)”。
- 55 条中 13 条是多 token 形式（/account claude、/account switch、/account openai、/account openai-compatible、/account default-provider、/account default-model、/account claude switch、/account claude remove、/account openai switch、/account openai remove、/initiatives show、/goals show、/compact mode），其余 42 条是单 token 基础命令；因按整串 trim 后全等比较（1759-1761），输入 '/account claude foo' 不命中。
- 位置参数 22 条（顶层 11：run message、login PROVIDER、debug command+arg、transcript text、browser action+browser、replay session、provider-test-coverage PROVIDER+MODEL、provider-doctor PROVIDER；嵌套 11：server promote version、session rename session+name、provider add name、auth doctor PROVIDER、memory search query、memory export output、memory import input、cloud sessions upload session_file、verify session_id、view session_id）——其中 8 条在源码里也带 #[arg(...)]（如 login provider 的 value_enum/id、provider-doctor 的 id=doctor_provider、memory rename name 的 required_unless_present），已按位置参数而非 flag 计。
- jcode api-bridge 整个 variant 标 #[cfg(unix)]（args.rs:577-596）：非 unix 构建下该子命令及其 --api-socket/--stdio 不存在。
- src/bin/ 下 harness.rs、session_memory_bench.rs、tui_bench.rs 各自的 clap `#[arg]`（如 --cwd/--include-network、--scenario/--session、--frames/--width…）属独立二进制、不是 `jcode` 子命令，按 gap① 范围未计入（依据 grep：这些 #[arg] 位于 src/bin/ 而非 src/cli/args.rs）。
- 隐藏 flag（hide=true）已在 what 标注：serve 3 条、setup-hotkey 3 条、cloud receive/activate/export 各指出的 flag 等；它们仍计入 186。
- 全局 flag 里 --provider/-p、-C/--cwd 等 24 个 global=true 在任意子命令均可传，但已在 §8 的“CLI 全局标志（共 26 条）”列过，按任务要求未在 §20 重复。
- payload `agent://JcodeCommands/report` 首次投递被输出上限截断（只到 `/triage`），本文件命令面清单改由源码逐条重抽（见 §0 数法）。

设置面的缺口（payload gaps 原样抄录）：

- 去重说明：上面「界面的缺口」已有一条「KEYBINDING_DEFAULTS(keybindings.rs:230-345) 只有 23 条 id，而 KeybindingsConfig 有 32 个键位字段；缺口 9 条……」。按新 payload 更新为：KeybindingsConfig 共 **33** 个 pub 字段，KEYBINDING_DEFAULTS 注册表 **23** 条，缺 **10** 个 id（上述 9 个键位串 + 策略字段 session_picker_enter），这 10 个的默认值只在 `KeybindingsConfig::default()` 的 `get()` 回退字面量里（lib.rs:1109-1117）；`validate_keybinding_defaults` 也漏检这 10 个 id。
- ✅已核实（默认值不一致 ①）：`display.redraw_fps` 的 doc 注释写 default **30**，但 `Default` impl 与 default_file 模板均为 **60**；实际生效以 Default impl 为准（`crates/jcode-config-types/src/display.rs:161`）。
- ✅已核实（默认值不一致 ②）：`keybindings.scroll_up` 的 doc 注释写 `ctrl+k`，KEYBINDING_DEFAULTS 实际为 `ctrl+shift+k`；`keybindings.scroll_down` 注释写 `ctrl+j`，实际为 `ctrl+shift+j`（`crates/jcode-config-types/src/keybindings.rs:196-208`）。
- `[desktop.*]` 是 opaque `Option<toml::Table>`（`crates/jcode-base/src/config.rs:572`），由 Jcode Desktop 拥有，CLI 不解释、无 schema，字段不可枚举 [未核实：仓库内无该表 schema]。
- `providers` 是 `BTreeMap<String, NamedProviderConfig>`（`crates/jcode-base/src/config.rs:524`），profile 名为任意 map key；每个 profile 的字段模板即 `NamedProviderConfig` 的 18 个 + `models[]` 的 5 个，按 profile 数可重复出现。
- `env_overrides.rs` 之外另有若干环境变量被 config 之外消费，不由 `apply_env_overrides` 覆盖，未列入：JCODE_HOME、JCODE_TERMINAL、JCODE_SPAWN_*、JCODE_FOCUS_*、JCODE_HOOK_*（hook 进程侧）、JCODE_HOOKS_DISABLED、JCODE_DISABLE_POWER_INHIBIT、JCODE_DISABLE_AUTOUPDATE、NARI_API_KEY、GEMINI_API_KEY、ANTHROPIC_API_KEY、OPENROUTER_API_KEY、TYPESAFE_API_KEY、AIMLAPI_API_KEY 等 [已见注释/旁证，未逐一定位消费点]。
- `default_file.rs` 模板中 87 个未注释 key 已由对应 struct 字段覆盖（value 只是实例化示例）；模板内注释形式的 key（约数十个）同样是这些 struct 字段的文档化示例，未单列。
- `/config` 无 config get/set 写子命令：读=display_string()，写=用户/AI 直接改 config.toml，改动由 `jcode-app-core/src/tool/config_edit_notice.rs` 的 diff 报告回显（键级 before/after + liveness）。
- 内部常量/运行时状态已排除，不属用户可设：`ToolSelection`（`crates/jcode-base/src/config.rs:698`）、`McpToolsMode` 的 internal/as_str、`ConfigCache`/`ConfigCacheFingerprint`、`WakeMode::parse`、`change_report::liveness_for_key` 等。
