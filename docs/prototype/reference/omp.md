# 先例原样 · omp（无损清单）

> 这一份是**证据**，不是需求：把 omp 在 TUI 里用户能碰到的功能逐条列全，一行一条（≤40 字），带出处。
> 用法：我们的原型每加/减一个东西，都先来这里查"有没有先例、它怎么做的、代价是什么"。
> 出处根目录：`/Users/wxlong/MYCode/oh-my-pi`。
> 覆盖基线：每组表头的"共 N 条"来自代码里的注册表/枚举；**该组的行数必须等于 N**。src 已归一为仓根相对路径。
> 自核计数方式：内置斜杠命令 `grep -cP '^\t\tname: "' builtin-*.ts`（只计 2 个 tab 缩进的顶层 `name`，3/4 tab 行是子命令名不计）→ 20+11+19+25+3+1+5 = **84**；键位 `KEYBINDINGS`（`packages/tui/src/app-keybindings.ts:86`）= `TUI_KEYBINDINGS`（`keybindings.ts:58-144`）**32** + app **38** = **70**。
> 两条 payload 的 coverage 断言与本文件一致；未发现 payload 之间"93"之类的数字冲突。

## 目录

- §0 覆盖表 —— 原有 32 节 + 新增 13 节的面
- §1 斜杠命令 · 内置 · 模式/模型类 —— 共 20 条
- §2 斜杠命令 · 内置 · 协作/输出类 —— 共 11 条
- §3 斜杠命令 · 内置 · 会话/信息类 —— 共 19 条
- §4 斜杠命令 · 内置 · 生命周期/工作区类 —— 共 25 条
- §5 斜杠命令 · 内置 · 市场/插件类 —— 共 3 条
- §6 斜杠命令 · 内置 · 技能类 —— 共 1 条
- §7 斜杠命令 · 内置 · 控制类 —— 共 5 条
- §8 斜杠命令 · 内置 · 别名表 —— 共 8 条
- §9 斜杠命令 · 非注册表来源 · 文件型 markdown 命令 —— 共 8 条
- §10 斜杠命令 · 非注册表来源 · prompt 模板与内置 TS 自定义 —— 共 4 条
- §11 斜杠命令 · 非注册表来源 · 扩展 / MCP / skill 动态命令 —— 共 4 条
- §12 斜杠命令 · 控制器识别的命令 / verb —— 共 36 条
- §13 斜杠命令 · 可用性门控 —— 共 4 条
- §14 键位 · 全局/应用 —— 共 38 条
- §15 键位 · 编辑器/输入/列表导航 —— 共 32 条
- §16 状态条 · 段位 —— 共 27 条
- §17 状态条 · preset —— 共 7 条
- §18 状态条 · 分隔符 —— 共 7 条
- §19 状态条 · contextLine 模式 —— 共 4 条
- §20 面板与选择器 · overlays 顶层 —— 共 63 条
- §21 面板与选择器 · overlays/extensions 仪表盘 —— 共 4 条
- §22 面板与选择器 · 整屏应用/调试器/向导 —— 共 21 条
- §23 挂件与扩展点 · HUD/卡片 —— 共 22 条
- §24 模式与开关 · approval —— 共 3 条
- §25 模式与开关 · magic keyword —— 共 4 条
- §26 模式与开关 · 其余开关 —— 共 35 条
- §27 可扩展/可配置项 —— 共 6 条
- §28 特殊输入 · 前缀 —— 已被 §35 取代（不重复计数）
- §29 CLI · 子命令 —— 共 50 条
- §30 CLI · launch 标志 —— 共 51 条
- §31 CLI · flag-tables 独有标志 —— 共 6 条
- §32 CLI · 全局标志 —— 共 2 条
- §33 内置命令 · 子命令 —— 共 129 条
- §34 内置命令 · 参数补全项 —— 共 16 条
- §35 内置命令 · 特殊输入前缀 —— 共 12 条
- §36 内置命令 · 动态命令来源机制 —— 共 7 条
- §37 内置命令 · COLLAB 允许表不一致定论 —— 共 1 条
- §38 CLI · 各子命令自有 flag —— 共 261 条
- §39 设置 · modes/settings.ts —— 共 83 条
- §40 设置 · 其余 35 个设置域 —— 共 446 条
- §41 面板与 overlay · 内部键 —— 共 545 条
- §42 vim 与编辑器动作 —— 共 133 条
- §43 首启向导 · setup/ 按键与鼠标路由 —— 共 63 条
- §44 TUI 源码目录 · 逐文件 —— 共 181 条
- §45 鼠标与终端交互 —— 共 20 条
- 附. 没查完的 / 已知缺口 —— 共 37 条

## 0. 覆盖表

| 面 | 注册表（文件:行） | 共 N 条 | 本文档行数 | 对不对得上 |
|---|---|---|---|---|
| 斜杠命令 · 内置注册表 | `packages/coding-agent/src/slash-commands/builtin-registry.ts:36-44` | 84 | 84 | ✅ |
| ↳ builtin-modes | `packages/coding-agent/src/slash-commands/builtin-modes.ts:273-874` | 20 | 20 | ✅ |
| ↳ builtin-collaboration | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:60-621` | 11 | 11 | ✅ |
| ↳ builtin-session | `packages/coding-agent/src/slash-commands/builtin-session.ts:206-734` | 19 | 19 | ✅ |
| ↳ builtin-lifecycle | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:151-870` | 25 | 25 | ✅ |
| ↳ builtin-marketplace | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:43-620` | 3 | 3 | ✅ |
| ↳ builtin-skills | `packages/coding-agent/src/slash-commands/builtin-skills.ts:64-173` | 1 | 1 | ✅ |
| ↳ builtin-control | `packages/coding-agent/src/slash-commands/builtin-control.ts:7-91` | 5 | 5 | ✅ |
| 斜杠命令 · 别名 | `builtin-*.ts`（lookup 另有别名 token） | 8 | 8 | ✅ |
| 斜杠命令 · 文件型 markdown | `packages/coding-agent/src/extensibility/slash-commands.ts:72-121` | 0（动态） | 8 来源行 | ✅ 目录清单，非枚举 |
| 斜杠命令 · prompt 模板 | `packages/coding-agent/src/config/prompt-templates.ts:165-183` | 0（动态） | 1 来源行 | ✅ |
| 斜杠命令 · 内置 TS 自定义 | `packages/coding-agent/src/extensibility/custom-commands/loader.ts:155-172` | 3 | 3 | ✅ |
| 斜杠命令 · 扩展命令 | `packages/coding-agent/src/extensibility/extensions/get-commands-handler.ts:35-45` | 0（动态） | 1 来源行 | ✅ |
| 斜杠命令 · MCP prompt | `packages/coding-agent/src/sdk.ts:1462-1465` | 0（动态） | 1 来源行 | ✅ |
| 斜杠命令 · skill | `packages/coding-agent/src/extensibility/skills.ts:609-611` | 0（动态） | 1 来源行 | ✅ |
| 斜杠命令 · 控制器 verb | `packages/coding-agent/src/modes/controllers/*.ts` | 7 文件 | 36 | ✅ 7 文件全覆盖 |
| 斜杠命令 · 可用性门控 | `packages/coding-agent/src/collab/guest.ts`、`packages/coding-agent/src/slash-commands/acp-builtins.ts`、`packages/coding-agent/src/modes/controllers/input-controller.ts` | 4 | 4 | ✅ |
| 键位 · 合计 | `packages/tui/src/app-keybindings.ts:85-248` | 70 | 70 | ✅ |
| 键位 · TUI 基座 | `packages/tui/src/keybindings.ts:58-144` | 32 | 32 | ✅ |
| 键位 · app | `packages/tui/src/app-keybindings.ts:88-247` | 38 | 38 | ✅ |
| 状态条 · 段位 | `packages/tui/src/status-line/schema.ts:2-29` | 27 | 27 | ✅ |
| 状态条 · preset | `packages/tui/src/status-line/presets.ts:4` | 7 | 7 | ✅ |
| 状态条 · 分隔符 | `packages/tui/src/status-line/schema.ts:48-56` | 7 | 7 | ✅ |
| 状态条 · contextLine | `packages/tui/src/status-line/schema.ts:44` | 4 | 4 | ✅ |
| 面板 · composer 形状 | `packages/tui/src/overlays/composer-shape-registry.ts:8` | 8 | 8 | ✅ |
| 面板 · overlays 顶层 | `packages/tui/src/overlays/*.ts` | 63 | 63 | ✅ |
| 面板 · overlays/extensions | `packages/tui/src/overlays/extensions/` | payload 组内 4 行 | 4 | ⚠️ 由 payload 同组拆出（见附注） |
| 面板 · apps/setup/tools | `packages/tui/src/apps/`、`packages/tui/src/setup/`、`packages/tui/src/tools/` | 无枚举 | 21 | ✅（无声明 N） |
| 挂件与扩展点 · HUD/卡片 | `packages/coding-agent/src/modes/types.ts`、`packages/coding-agent/src/extensibility/extensions/types.ts` 等 | 无枚举 | 22 | ✅（无声明 N） |
| 模式 · approval | `packages/coding-agent/src/tools/approval.ts:17` | 3 | 3 | ✅ |
| 模式 · magic keyword | `packages/coding-agent/src/modes/magic-keywords.ts` | 4 | 4 | ✅ |
| 模式 · 其余开关 | `packages/coding-agent/src/modes/settings.ts` 等 | 无枚举 | 35 | ✅（无声明 N） |
| 可扩展/可配置项 | `packages/coding-agent/src/extensibility/extensions/types.ts`、`packages/coding-agent/src/modes/settings.ts` 等 | 无枚举 | 6 | ✅（无声明 N） |
| 特殊输入 · 前缀（旧表） | 同上 | 8 | — | 已被 §35 取代（内容全部包含在 §35 的 12 条里） |
| CLI · 子命令 | `packages/coding-agent/src/cli-commands.ts:28-286` | 50 | 50 | ✅ |
| CLI · launch 标志 | `packages/coding-agent/src/commands/launch-help.ts:17-114` | 51 | 51 | ✅ |
| CLI · flag-tables 独有 | `packages/coding-agent/src/cli/flag-tables.ts:139-300` | 6 | 6 | ✅ |
| CLI · 全局标志 | `packages/coding-agent/src/cli/flag-tables.ts:290-291` | 2 | 2 | ✅ |
| 内置命令 · 子命令 | `packages/coding-agent/src/slash-commands/builtin-*.ts` 各 `subcommands:` + `packages/coding-agent/src/session/compact-modes.ts:41` | 129 | 129 | ✅ |
| 内置命令 · 参数补全项 | `packages/coding-agent/src/slash-commands/builtin-registry.ts:75-99`、`packages/coding-agent/src/slash-commands/builtin-completions.ts` | 16 | 16 | ✅（payload 标题声明 15） |
| 特殊输入 · 前缀（精确解析点） | `packages/coding-agent/src/modes/controllers/input-controller.ts` 等 | 12 | 12 | ✅ |
| 动态命令来源机制 | `packages/coding-agent/src/slash-commands/available-commands.ts`、`packages/coding-agent/src/modes/interactive-mode.ts#buildPendingSlashCommands` | 7 | 7 | ✅ |
| 内置命令 · COLLAB 允许表定论 | `packages/coding-agent/src/slash-commands/builtin-registry.ts:143`、`packages/coding-agent/src/collab/guest.ts:43-58` | 1 | 1 | ✅ |
| CLI · 各子命令自有 flag | `packages/coding-agent/src/cli-commands.ts:27` 各 Command `static flags` | 318 | 261 | ✅（去掉 57 行与 §30/§31 重复的 launch flag，见 §38 数法行） |
| 设置 · modes/settings.ts | `packages/coding-agent/src/modes/settings.ts` register | 83 | 83 | ✅ |
| 设置 · 其余 35 个域 | `packages/coding-agent/src/config/all-settings.ts` DOMAINS 各文件 register | 446 | 446 | ✅ |
| 面板与 overlay · 内部键 | `packages/tui/src/overlays/**`、`packages/tui/src/apps/**`、`packages/tui/src/components/**` grep matchesKey/handleInput | 545 | 545 | ✅ |
| ↳ 无键位文件 | 同上（三组 grep 全空） | 42 | 42 | ✅ |
| vim 与编辑器动作 | `packages/tui/src/vim.ts`、`packages/tui/src/components/editor.ts` | 133 | 133 | ✅ |
| 首启向导 · setup/ 键与鼠标 | `packages/tui/src/setup/**` + `packages/tui/src/chrome/selector-helpers.ts` | 63 | 63 | ✅ |
| TUI 源码目录 · 逐文件 | `packages/tui/src/chrome/**`、`chat/**`、`prompt/**`、`components/**`、`render/**`、`native/**`、`theme/**` | 181 | 181 | ✅ |
| 鼠标与终端交互 | `packages/tui/src/**`（`MOUSE_TRACKING` + SGR 解析） | 20 | 20 | ✅ |

## 1. 斜杠命令 · 内置 · 模式/模型类（共 20 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `security` | 规划/运行/查看/导入/比对原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:275` |
| `settings` | 打开设置菜单 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:296` |
| `setup`（别名 providers） | 打开 provider 设置向导 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:305` |
| `plan` | 切换 plan 模式（先规划后执行） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:323` |
| `plan-review` | 重新打开最新计划的评审 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:344` |
| `vibe` | 切换 vibe 模式（只读快好 worker 会话） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:355` |
| `goal` | 切换 goal 模式（持久自主目标） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:373` |
| `guided-goal` | 让 agent 访谈你后设置 goal 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:399` |
| `loop` | 切换 loop 模式（每次 yield 重发提示） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:411` |
| `queue` | 排队一条消息到 agent yield 后发送 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:438` |
| `model`（别名 models） | 切换本会话模型 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:451` |
| `switch` | 切换模型（同 alt+p，支持模糊/@role） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:495` |
| `fast` | 切换快速服务档 (priority/ultrafast) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:546` |
| `slow` | 切换慢速档 (flex/低优先级) | `packages/coding-agent/src/slash-commands/builtin-modes.ts:574` |
| `skillful` | 切换系统提示中列出可用技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:602` |
| `extended-context` | 切换扩展上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:658` |
| `computer` | 切换本会话计算机使用 eval 前奏 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:685` |
| `ratchet` | 为 LLM 流程建/复用 eval 并无人值守爬山 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:730` |
| `prewalk` | 布置/重启一次性模型交接 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:764` |
| `modelpreset` | 保存并切换模型预设（角色+思考档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:814` |

## 2. 斜杠命令 · 内置 · 协作/输出类（共 11 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `advisor` | 切换 advisor（第二个模型每轮评审并注入笔记） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:62` |
| `export` | 导出会话为 HTML 文件 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:179` |
| `trace` | 在统计面板打开本会话 trace | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:203` |
| `dump` | 复制会话记录并写 LLM 请求 JSON | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:230` |
| `share` | 通过加密链接分享会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:263` |
| `collab` | 通过 relay 直播分享本会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:289` |
| `join` | 加入共享的 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:418` |
| `leave` | 离开 collab 会话 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:450` |
| `browser` | 切换浏览器 eval 前奏无头/可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:475` |
| `copy` | 选取会话中的文本或代码复制 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:545` |
| `open` | 用浏览器打开会话中最后的链接 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:597` |

## 3. 斜杠命令 · 内置 · 会话/信息类（共 19 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `todo` | 查看或修改 agent 的 todo 列表 | `packages/coding-agent/src/slash-commands/builtin-session.ts:208` |
| `session` | 会话管理命令 | `packages/coding-agent/src/slash-commands/builtin-session.ts:246` |
| `jobs` | 显示异步后台任务状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:324` |
| `usage` | 显示 provider 用量与限额 (show/reset) | `packages/coding-agent/src/slash-commands/builtin-session.ts:385` |
| `stats` | 启动本地统计面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:432` |
| `changelog` | 显示变更日志条目 | `packages/coding-agent/src/slash-commands/builtin-session.ts:467` |
| `hotkeys` | 显示所有键盘快捷键 | `packages/coding-agent/src/slash-commands/builtin-session.ts:496` |
| `tools` | 显示 agent 当前可见工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:505` |
| `context` | 显示上下文用量估算明细 | `packages/coding-agent/src/slash-commands/builtin-session.ts:534` |
| `extensions`（别名 status） | 打开扩展控制中心面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:553` |
| `agents` | 打开 agents hub（每 agent 模型等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:563` |
| `git` | 打开 git UI（diff/暂存/提交） | `packages/coding-agent/src/slash-commands/builtin-session.ts:572` |
| `hub` | 打开实时 Agent Hub | `packages/coding-agent/src/slash-commands/builtin-session.ts:583` |
| `branch`（别名 rewind） | 回退到旧消息并保留旧路径为分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:592` |
| `fork` | 从旧消息创建新分支 | `packages/coding-agent/src/slash-commands/builtin-session.ts:602` |
| `tree` | 浏览会话树（切换分支） | `packages/coding-agent/src/slash-commands/builtin-session.ts:611` |
| `login` | 用 OAuth provider 登录 | `packages/coding-agent/src/slash-commands/builtin-session.ts:620` |
| `logout` | 登出 OAuth provider | `packages/coding-agent/src/slash-commands/builtin-session.ts:673` |
| `mcp` | 管理 MCP 服务器（add/list/remove/test 等） | `packages/coding-agent/src/slash-commands/builtin-session.ts:696` |

## 4. 斜杠命令 · 内置 · 生命周期/工作区类（共 25 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ssh` | 管理 SSH 主机（add/list/remove） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:153` |
| `new` | 开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:176` |
| `fresh` | 重置 provider 流状态，保留记录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:185` |
| `clear` | 原地清空会话上下文，保留会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:207` |
| `delete` | 删除当前会话并开始新会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:218` |
| `compact` | 手动压缩会话上下文 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:227` |
| `shake` | 丢弃上下文中重内容（工具结果等） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:293` |
| `handoff` | 总结为交接文档并原地压缩 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:322` |
| `resume` | 恢复另一个会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:389` |
| `pin` | 在恢复列表顶部固定/取消固定会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:420` |
| `btw` | 提问侧问题或浏览 BTW 历史 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:451` |
| `tan` | 在切向工作上跑后台 agent | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:463` |
| `omfg` | 从抱怨生成 TTSR 规则 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:475` |
| `cleanse` | 用加权并行子 agent 检测修复诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:487` |
| `retry` | 重试上次失败的 agent 轮次 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:499` |
| `debug` | 打开调试工具选择器 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:534` |
| `memory` | 检查并操作记忆维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:543` |
| `rename` | 重命名当前会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:632` |
| `move` | 把当前会话移到别的目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:710` |
| `wt`（别名 worktree） | 把会话移入新 worktree（含改动） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:740` |
| `add-dir` | 添加工作区目录（多根） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:775` |
| `remove-dir` | 移除工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:807` |
| `dirs` | 列出本会话工作区目录 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:836` |
| `exit` | 退出应用 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:845` |
| `restart` | 用相同启动参数重启并恢复会话 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:850` |

## 5. 斜杠命令 · 内置 · 市场/插件类（共 3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `marketplace` | 管理市场插件源与已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:45` |
| `plugins`（别名 plugin） | 查看并管理已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:425` |
| `reload-plugins` | 重载所有插件（技能/命令/钩子等） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:557` |

## 6. 斜杠命令 · 内置 · 技能类（共 1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `skills` | 从 skills.omp.sh 搜索/安装/更新技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:66` |

## 7. 斜杠命令 · 内置 · 控制类（共 5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `force`（别名 force:） | 强制下一轮使用指定工具 | `packages/coding-agent/src/slash-commands/builtin-control.ts:9` |
| `live` | 启动 Codex 实时语音模式 | `packages/coding-agent/src/slash-commands/builtin-control.ts:59` |
| `record` | 开始/停止录制本屏到可回放文件 | `packages/coding-agent/src/slash-commands/builtin-control.ts:68` |
| `pause` | 冻结所有 agent 直到恢复 | `packages/coding-agent/src/slash-commands/builtin-control.ts:77` |
| `quit`（别名 q） | 退出应用 | `packages/coding-agent/src/slash-commands/builtin-control.ts:86` |

## 8. 斜杠命令 · 内置 · 别名表（共 8 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `force:` → `force` | `/force:<tool>` 简写形式 | `packages/coding-agent/src/slash-commands/builtin-control.ts:12` |
| `q` → `quit` | 退出别名 | `packages/coding-agent/src/slash-commands/builtin-control.ts:87` |
| `providers` → `setup` | provider 设置别名 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:306` |
| `models` → `model` | 模型切换别名 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:452` |
| `status` → `extensions` | 扩展面板别名 | `packages/coding-agent/src/slash-commands/builtin-session.ts:554` |
| `plugin` → `plugins` | 插件管理别名 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:426` |
| `rewind` → `branch` | 回退分支别名 | `packages/coding-agent/src/slash-commands/builtin-session.ts:593` |
| `worktree` → `wt` | worktree 迁移别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:741` |

## 9. 斜杠命令 · 非注册表来源 · 文件型 markdown 命令（共 8 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `<任意>.md（.omp）` | `~/.omp/agent/commands` 与 `<cwd>/.omp/commands` 下的 md | `packages/coding-agent/src/discovery/builtin.ts:345-365` |
| `<任意>.md（.claude）` | `~/.claude/commands` + `<cwd>/.claude/commands`（递归，带命名空间别名） | `packages/coding-agent/src/discovery/claude.ts:326-368` |
| `<任意>.md（.codex）` | `~/.codex/commands` + `<cwd>/.codex/commands` | `packages/coding-agent/src/discovery/codex.ts:317-350` |
| `<任意>.md（opencode）` | `~/.config/opencode/commands` + `<cwd>/.opencode/commands` | `packages/coding-agent/src/discovery/opencode.ts:421-465` |
| `<任意>.md（plugin 根）` | 各插件根目录的 `commands/` 下 md | `packages/coding-agent/src/discovery/omp-plugins.ts:88-103` |
| `<plugin>:<cmd>` | claude-plugins 清单 commands/slash-commands 目录，带插件前缀 | `packages/coding-agent/src/discovery/claude-plugins.ts:288-320` |
| `<cwd 向上>.agent[s]/commands` | agents provider 的项目向上 + 用户 home 命令目录 | `packages/coding-agent/src/discovery/agents.ts:243-270` |
| `init`（内置 md） | 打包内置的 `/init` 命令模板 | `packages/coding-agent/src/task/commands.ts:10-34` |

## 10. 斜杠命令 · 非注册表来源 · prompt 模板与内置 TS 自定义（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `<模板名>` | `agentDir/prompts` 与 `<cwd>/.omp/prompts` 的模板可 `/<name>` 调用 | `packages/coding-agent/src/config/prompt-templates.ts:165-183` |
| `green` | 生成迭代 CI 直到分支变绿的提示 | `packages/coding-agent/src/extensibility/custom-commands/bundled/ci-green/index.ts:47` |
| `review` | 启动交互式代码审查 | `packages/coding-agent/src/extensibility/custom-commands/bundled/review/index.ts:380` |
| `annotate` | 对 diff/文本/文件/会话做标注 | `packages/coding-agent/src/extensibility/custom-commands/bundled/annotate/index.ts:312` |

## 11. 斜杠命令 · 非注册表来源 · 扩展 / MCP / skill 动态命令（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `<扩展注册名>` | 扩展 `api.registerCommand` 注册的命令，TUI 与 ACP 均可发现 | `packages/coding-agent/src/extensibility/extensions/loader.ts:117` |
| `<server>:<prompt>` | 已连接 MCP 服务器提供的 prompt 变成斜杠命令 | `packages/coding-agent/src/sdk.ts:1462-1465` |
| `skill:<name>` | 启用的 skill 以 `/skill:<name>` 调用 | `packages/coding-agent/src/extensibility/skills.ts:609-611` |
| `<extension root>/commands` | `--plugin-dir`/扩展根目录下的 md 命令 | `packages/coding-agent/src/discovery/omp-plugins.ts:88` |

## 12. 斜杠命令 · 控制器识别的命令 / verb（共 36 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `CommandController: export` | 导出当前视图会话为 HTML 并打开 | `packages/coding-agent/src/modes/controllers/command-controller.ts:168` |
| `CommandController: trace` | 打开 trace 统计面板链接 | `packages/coding-agent/src/modes/controllers/command-controller.ts:185` |
| `CommandController: dump` | 复制会话记录到剪贴板 + 写 JSON | `packages/coding-agent/src/modes/controllers/command-controller.ts:204` |
| `CommandController: advisor dump` | 复制 advisor 历史 | `packages/coding-agent/src/modes/controllers/command-controller.ts:233` |
| `CommandController: debug-transcript` | 写渲染后的对话到 tmp 文件 | `packages/coding-agent/src/modes/controllers/command-controller.ts:253` |
| `CommandController: share` | 分享会话（自定义 share 脚本优先） | `packages/coding-agent/src/modes/controllers/command-controller.ts:272` |
| `CommandController: session` | 展示会话统计信息 | `packages/coding-agent/src/modes/controllers/command-controller.ts:356` |
| `CommandController: advisor status` | 展示 advisor 状态 | `packages/coding-agent/src/modes/controllers/command-controller.ts:487` |
| `CommandController: jobs` | 展示后台任务面板 | `packages/coding-agent/src/modes/controllers/command-controller.ts:604` |
| `CommandController: usage` | 展示 provider 用量 | `packages/coding-agent/src/modes/controllers/command-controller.ts:655` |
| `CommandController: changelog` | 展示变更日志 | `packages/coding-agent/src/modes/controllers/command-controller.ts:673` |
| `CommandController: hotkeys` | 展示快捷键表 | `packages/coding-agent/src/modes/controllers/command-controller.ts:708` |
| `CommandController: tools` | 展示当前可见工具 | `packages/coding-agent/src/modes/controllers/command-controller.ts:725` |
| `CommandController: context` | 展示上下文用量卡片 | `packages/coding-agent/src/modes/controllers/command-controller.ts:733` |
| `CommandController: memory view\|reset\|clear\|enqueue\|rebuild\|queue\|sync\|stats\|diagnose\|mm` | 记忆查看/清理/入队/统计，mm 子动词 list\|show\|refresh\|history\|seed\|reload\|delete | `packages/coding-agent/src/modes/controllers/command-controller.ts:760-903` |
| `CommandController: clear`（=new 会话流） | 走新会话流程 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1128` |
| `CommandController: fresh` | 重置 provider 流状态 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1132` |
| `CommandController: reset-context`（/clear） | 原地清空上下文 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1144` |
| `CommandController: delete` | 删除当前会话 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1175` |
| `CommandController: fork` | 创建会话分支 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1183` |
| `CommandController: move` | 移动会话到其他目录 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1233` |
| `CommandController: worktree` | 创建/进入 git worktree | `packages/coding-agent/src/modes/controllers/command-controller.ts:1311` |
| `CommandController: rename` | 重命名会话 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1403` |
| `CommandController: bash`（`!` / `!!`） | 执行 shell 命令（`!!` 不入上下文） | `packages/coding-agent/src/modes/controllers/command-controller.ts:1432` |
| `CommandController: python`（`$` / `$$`） | 执行 python 代码（`$$` 不入上下文） | `packages/coding-agent/src/modes/controllers/command-controller.ts:1532` |
| `CommandController: compact` | 压缩会话 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1574` |
| `CommandController: shake` | 丢弃重内容 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1612` |
| `CommandController: handoff` | 生成交接文档 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1719` |
| `TodoCommandController: 无参\|expand\|collapse\|edit\|copy\|export\|import\|help\|?\|append\|start\|done\|drop\|rm` | `/todo` 的子动词集合 | `packages/coding-agent/src/modes/controllers/todo-command-controller.ts:147-190` |
| `SSHCommandController: add\|list\|remove\|rm\|help` | `/ssh` 的子命令 | `packages/coding-agent/src/modes/controllers/ssh-command-controller.ts:31-55` |
| `MCPCommandController: add\|list\|remove\|rm\|test\|reauth\|unauth\|enable\|disable\|resources\|prompts\|notifications\|smithery-search\|smithery-login\|smithery-logout\|reconnect\|reload\|help` | `/mcp` 的子命令 | `packages/coding-agent/src/modes/controllers/mcp-command-controller.ts:444-494` |
| `CleanseCommandController: [request] --all/-a --tests/-t --agents/-n --model/-m` | `/cleanse` 的参数 | `packages/coding-agent/src/modes/controllers/cleanse-command-controller.ts:159-180` |
| `TanCommandController: <work>` | `/tan` 启动后台切向 agent | `packages/coding-agent/src/modes/controllers/tan-command-controller.ts:45` |
| `LiveCommandController: 切换` | `/live` 启动/停止实时语音 | `packages/coding-agent/src/modes/controllers/live-command-controller.ts:65` |
| `OmfgController: <complaint>` | `/omfg` 生成 TTSR 规则 | `packages/coding-agent/src/modes/controllers/omfg-controller.ts:67` |
| `BtwController: <question>` | `/btw` 侧问 | `packages/coding-agent/src/modes/controllers/btw-controller.ts:349` |

## 13. 斜杠命令 · 可用性门控（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `COLLAB_GUEST_ALLOWED_COMMANDS` | collab guest 仅允许 dump/export/copy/open/help/hotkeys/theme/settings/leave/collab/exit/quit，其余 host-only | `packages/coding-agent/src/collab/guest.ts:43-58` |
| `FOCUSED_VIEW_COMMANDS` | 聚焦子 agent 视图仅可跑 `/btw`、`/export`、`/usage show` | `packages/coding-agent/src/modes/controllers/input-controller.ts:170-176` |
| `ACP_BUILTIN_RESERVED_NAMES` | ACP 侧保留内置名+别名，屏蔽同名扩展命令 | `packages/coding-agent/src/slash-commands/acp-builtins.ts:25-27` |
| `isAcpBuiltinShadowedName` | 冒号命名空间若前缀是内置命令也视为被遮蔽 | `packages/coding-agent/src/slash-commands/acp-builtins.ts:40-44` |

## 14. 键位 · 全局/应用（共 38 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `app.interrupt` | 中断当前操作（escape） | `packages/tui/src/app-keybindings.ts:88` |
| `app.clear` | 清屏或取消（ctrl+c） | `packages/tui/src/app-keybindings.ts:92` |
| `app.exit` | 退出应用（ctrl+d） | `packages/tui/src/app-keybindings.ts:96` |
| `app.suspend` | 挂起应用（ctrl+z） | `packages/tui/src/app-keybindings.ts:100` |
| `app.display.reset` | 重置终端显示（alt+l） | `packages/tui/src/app-keybindings.ts:104` |
| `app.thinking.cycle` | 循环 thinking 档位（shift+tab） | `packages/tui/src/app-keybindings.ts:108` |
| `app.thinking.toggle` | 切换 thinking 显示（ctrl+t） | `packages/tui/src/app-keybindings.ts:112` |
| `app.model.cycleForward` | 切到下一个模型（ctrl+p） | `packages/tui/src/app-keybindings.ts:116` |
| `app.model.cycleBackward` | 切到上一个模型（shift+ctrl+p） | `packages/tui/src/app-keybindings.ts:120` |
| `app.model.select` | 选择模型（alt+m） | `packages/tui/src/app-keybindings.ts:124` |
| `app.model.selectTemporary` | 选会话临时模型（alt+p） | `packages/tui/src/app-keybindings.ts:128` |
| `app.tools.expand` | 展开工具卡片（ctrl+o） | `packages/tui/src/app-keybindings.ts:132` |
| `app.tools.toggleVisibility` | 显隐工具活动（ctrl+shift+o） | `packages/tui/src/app-keybindings.ts:136` |
| `app.editor.external` | 打开外部编辑器（ctrl+g） | `packages/tui/src/app-keybindings.ts:140` |
| `app.message.followUp` | 发送跟进消息（ctrl+q / ctrl+enter） | `packages/tui/src/app-keybindings.ts:144` |
| `app.retry` | 重试上一失败回合（f5 / alt+r） | `packages/tui/src/app-keybindings.ts:151` |
| `app.message.dequeue` | 取回排队消息（alt+up / shift+up） | `packages/tui/src/app-keybindings.ts:158` |
| `app.clipboard.pasteImage` | 粘贴图片/文本（win ctrl+v,alt+v；mac ctrl+v,super+v；linux ctrl+v） | `packages/tui/src/app-keybindings.ts:164` |
| `app.clipboard.pasteTextRaw` | 原样粘贴文本（ctrl+shift+v / alt+shift+v） | `packages/tui/src/app-keybindings.ts:168` |
| `app.clipboard.copyLine` | 复制当前行（alt+shift+l） | `packages/tui/src/app-keybindings.ts:172` |
| `app.clipboard.copyPrompt` | 复制提示词（alt+shift+c） | `packages/tui/src/app-keybindings.ts:176` |
| `app.session.new` | 新建会话（默认未绑定） | `packages/tui/src/app-keybindings.ts:180` |
| `app.session.tree` | 会话树（默认未绑定） | `packages/tui/src/app-keybindings.ts:184` |
| `app.session.fork` | 分叉会话（默认未绑定） | `packages/tui/src/app-keybindings.ts:188` |
| `app.session.resume` | 恢复会话（默认未绑定） | `packages/tui/src/app-keybindings.ts:192` |
| `app.agents.hub` | 打开 agent hub（alt+a） | `packages/tui/src/app-keybindings.ts:196` |
| `app.session.observe` | 打开 agent hub（ctrl+s） | `packages/tui/src/app-keybindings.ts:200` |
| `app.session.togglePath` | 切换会话路径显示（ctrl+p） | `packages/tui/src/app-keybindings.ts:204` |
| `app.session.toggleSort` | 切换会话排序（ctrl+s） | `packages/tui/src/app-keybindings.ts:208` |
| `app.session.rename` | 重命名会话（ctrl+r） | `packages/tui/src/app-keybindings.ts:212` |
| `app.session.delete` | 删除会话（ctrl+d） | `packages/tui/src/app-keybindings.ts:216` |
| `app.session.deleteNoninvasive` | 非侵入删除会话（ctrl+backspace） | `packages/tui/src/app-keybindings.ts:220` |
| `app.tree.foldOrUp` | 折叠/上移（ctrl+left / alt+left） | `packages/tui/src/app-keybindings.ts:224` |
| `app.tree.unfoldOrDown` | 展开/下移（ctrl+right / alt+right） | `packages/tui/src/app-keybindings.ts:228` |
| `app.plan.toggle` | 切换 plan 模式（alt+shift+p） | `packages/tui/src/app-keybindings.ts:232` |
| `app.history.search` | 搜索历史（ctrl+r） | `packages/tui/src/app-keybindings.ts:236` |
| `app.stt.toggle` | 切换语音转写（默认按住 Space） | `packages/tui/src/app-keybindings.ts:240` |
| `app.live.toggle` | 启停 live 语音模式（ctrl+l） | `packages/tui/src/app-keybindings.ts:244` |

## 15. 键位 · 编辑器/输入/列表导航（共 32 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tui.editor.cursorUp` | 光标上移（up） | `packages/tui/src/keybindings.ts:59` |
| `tui.editor.cursorDown` | 光标下移（down） | `packages/tui/src/keybindings.ts:60` |
| `tui.editor.cursorLeft` | 光标左移（left / ctrl+b） | `packages/tui/src/keybindings.ts:61` |
| `tui.editor.cursorRight` | 光标右移（right / ctrl+f） | `packages/tui/src/keybindings.ts:65` |
| `tui.editor.cursorWordLeft` | 按词左移（alt+left/ctrl+left/alt+b） | `packages/tui/src/keybindings.ts:69` |
| `tui.editor.cursorWordRight` | 按词右移（alt+right/ctrl+right/alt+f） | `packages/tui/src/keybindings.ts:73` |
| `tui.editor.cursorLineStart` | 行首（home / ctrl+a） | `packages/tui/src/keybindings.ts:77` |
| `tui.editor.cursorLineEnd` | 行尾（end / ctrl+e） | `packages/tui/src/keybindings.ts:81` |
| `tui.editor.jumpForward` | 向前跳字符（ctrl+]） | `packages/tui/src/keybindings.ts:85` |
| `tui.editor.jumpBackward` | 向后跳字符（ctrl+alt+]） | `packages/tui/src/keybindings.ts:89` |
| `tui.editor.pageUp` | 上翻页（pageUp） | `packages/tui/src/keybindings.ts:93` |
| `tui.editor.pageDown` | 下翻页（pageDown） | `packages/tui/src/keybindings.ts:94` |
| `tui.editor.deleteCharBackward` | 退格删字符（backspace） | `packages/tui/src/keybindings.ts:95` |
| `tui.editor.deleteCharForward` | 前向删字符（delete / ctrl+d） | `packages/tui/src/keybindings.ts:99` |
| `tui.editor.deleteWordBackward` | 前向删词（ctrl+w/alt+backspace/ctrl+backspace/super+alt+backspace） | `packages/tui/src/keybindings.ts:103` |
| `tui.editor.deleteWordForward` | 后向删词（alt+delete/alt+d/super+alt+delete/super+alt+d） | `packages/tui/src/keybindings.ts:107` |
| `tui.editor.deleteToLineStart` | 删到行首（ctrl+u） | `packages/tui/src/keybindings.ts:111` |
| `tui.editor.deleteToLineEnd` | 删到行尾（ctrl+k） | `packages/tui/src/keybindings.ts:115` |
| `tui.editor.yank` | 粘贴(kill-ring)（ctrl+y） | `packages/tui/src/keybindings.ts:119` |
| `tui.editor.yankPop` | yank 循环（alt+y） | `packages/tui/src/keybindings.ts:120` |
| `tui.editor.undo` | 撤销（ctrl+- / ctrl+_） | `packages/tui/src/keybindings.ts:121` |
| `tui.editor.spellingSuggestions` | 拼写替换建议（ctrl+.） | `packages/tui/src/keybindings.ts:122` |
| `tui.input.newLine` | 插入换行（shift+enter / ctrl+j） | `packages/tui/src/keybindings.ts:126` |
| `tui.input.submit` | 提交输入（enter） | `packages/tui/src/keybindings.ts:127` |
| `tui.input.tab` | Tab/自动补全（tab） | `packages/tui/src/keybindings.ts:128` |
| `tui.input.copy` | 复制选中（ctrl+c） | `packages/tui/src/keybindings.ts:129` |
| `tui.select.up` | 选择上移（up） | `packages/tui/src/keybindings.ts:130` |
| `tui.select.down` | 选择下移（down） | `packages/tui/src/keybindings.ts:131` |
| `tui.select.pageUp` | 选择上翻页（pageUp） | `packages/tui/src/keybindings.ts:132` |
| `tui.select.pageDown` | 选择下翻页（pageDown） | `packages/tui/src/keybindings.ts:133` |
| `tui.select.confirm` | 确认选择（enter） | `packages/tui/src/keybindings.ts:138` |
| `tui.select.cancel` | 取消选择（escape / ctrl+c） | `packages/tui/src/keybindings.ts:139` |

## 16. 状态条 · 段位（共 27 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `pi` | 会话/幽灵图标段 | `packages/tui/src/status-line/segments.ts:203` |
| `status` | hook 状态累积文本 | `packages/tui/src/status-line/segments.ts:248` |
| `model` | 模型名+thinking 档 | `packages/tui/src/status-line/segments.ts:338` |
| `mode` | 当前模式（plan/pause 等） | `packages/tui/src/status-line/segments.ts:486` |
| `path` | 当前工作路径 | `packages/tui/src/status-line/segments.ts:564` |
| `git` | git 分支/暂存/未暂存/未跟踪 | `packages/tui/src/status-line/segments.ts:627` |
| `pr` | PR 编号/状态 | `packages/tui/src/status-line/segments.ts:697` |
| `subagents` | 子智能体计数 | `packages/tui/src/status-line/segments.ts:714` |
| `token_in` | 输入 token 数 | `packages/tui/src/status-line/segments.ts:729` |
| `token_out` | 输出 token 数 | `packages/tui/src/status-line/segments.ts:731` |
| `token_total` | token 累计（不含 cacheRead） | `packages/tui/src/status-line/segments.ts:733` |
| `token_rate` | tok/s | `packages/tui/src/status-line/segments.ts:758` |
| `cost` | 花费 | `packages/tui/src/status-line/segments.ts:818` |
| `context_pct` | 上下文占用百分比 | `packages/tui/src/status-line/segments.ts:832` |
| `context_total` | 上下文窗口总量 | `packages/tui/src/status-line/segments.ts:889` |
| `time_spent` | 活跃时长 | `packages/tui/src/status-line/segments.ts:913` |
| `time` | 当前时钟 | `packages/tui/src/status-line/segments.ts:945` |
| `session` | 会话 id | `packages/tui/src/status-line/segments.ts:955` |
| `hostname` | 主机名 | `packages/tui/src/status-line/segments.ts:970` |
| `cache_read` | cache read 计数 | `packages/tui/src/status-line/segments.ts:984` |
| `cache_write` | cache write 计数 | `packages/tui/src/status-line/segments.ts:986` |
| `cache_hit` | 缓存命中率 | `packages/tui/src/status-line/segments.ts:993` |
| `session_name` | 会话名/预览标题 | `packages/tui/src/status-line/segments.ts:1021` |
| `usage` | 额度用量（5h/日/7d/月/重置） | `packages/tui/src/status-line/segments.ts:1189` |
| `collab` | 协作参与人数 | `packages/tui/src/status-line/segments.ts:1039` |
| `stream` | LIVE 观看数徽标 | `packages/tui/src/status-line/segments.ts:1055` |
| `vim` | vim 模式显示 | `packages/tui/src/status-line/segments.ts:1104` |

## 17. 状态条 · preset（共 7 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `default` | pi…cost 左 / session_name 右 | `packages/tui/src/status-line/presets.ts:5` |
| `minimal` | vim/path/git + session_name/mode/context_pct | `packages/tui/src/status-line/presets.ts:17` |
| `compact` | vim/model/mode/git/pr | `packages/tui/src/status-line/presets.ts:28` |
| `full` | 最全左段+10 右段 | `packages/tui/src/status-line/presets.ts:40` |
| `nerd` | 含 Nerd 图标的全量 | `packages/tui/src/status-line/presets.ts:59` |
| `ascii` | 无 Nerd Font 依赖 | `packages/tui/src/status-line/presets.ts:80` |
| `custom` | 用户自定义左右段 | `packages/tui/src/status-line/presets.ts:96` |

## 18. 状态条 · 分隔符（共 7 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `powerline` | 实心 powerline 分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `powerline-thin` | 细线 powerline 分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `slash` | 斜杠分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `pipe` | 竖线分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `block` | 方块分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `none` | 无分隔符 | `packages/tui/src/status-line/schema.ts:53` |
| `ascii` | ASCII 兼容分隔符 | `packages/tui/src/status-line/schema.ts:53` |

## 19. 状态条 · contextLine 模式（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `off` | 不显示 context line | `packages/tui/src/status-line/schema.ts:44` |
| `percentage` | 仅显示百分比 | `packages/tui/src/status-line/schema.ts:44` |
| `annotated` | 带注解的 context line | `packages/tui/src/status-line/schema.ts:44` |
| `embedded` | 嵌入到状态条 | `packages/tui/src/status-line/schema.ts:44` |

## 20. 面板与选择器 · overlays 顶层（共 63 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `usage-dashboard.ts` | `/usage` 用量仪表盘 | `packages/tui/src/overlays/usage-dashboard.ts:535` |
| `usage-row.ts` | 每回合用量行 | `packages/tui/src/overlays/usage-row.ts` |
| `tree-selector.ts` | `/tree` 会话树选择 | `packages/tui/src/overlays/tree-selector.ts` |
| `thinking-selector.ts` | thinking 档位选择 | `packages/tui/src/overlays/thinking-selector.ts` |
| `theme-selector.ts` | 主题选择（预览） | `packages/tui/src/overlays/theme-selector.ts` |
| `snapcompact-shape-preview.ts` | snapcompact 形状预览 | `packages/tui/src/overlays/snapcompact-shape-preview.ts` |
| `stats-notice.ts` | `/stats` 仪表盘结果通知 | `packages/tui/src/overlays/stats-notice.ts` |
| `settings-selector.ts` | `/settings` 全屏设置编辑 | `packages/tui/src/overlays/settings-selector.ts` |
| `show-images-selector.ts` | 图片显示方式选择 | `packages/tui/src/overlays/show-images-selector.ts` |
| `settings-defs.ts` | 设置面板选项/渲染定义（helper） | `packages/tui/src/overlays/settings-defs.ts` |
| `session-selector.ts` | `/resume` 会话选择（含路径/排序/重命名/删除键） | `packages/tui/src/overlays/session-selector.ts` |
| `session-info-overlay.ts` | `/session` 信息浮层 | `packages/tui/src/overlays/session-info-overlay.ts` |
| `session-account-selector.ts` | 会话账号选择 | `packages/tui/src/overlays/session-account-selector.ts` |
| `rewind-selector.ts` | `/rewind` 或双击 Esc 回退 | `packages/tui/src/overlays/rewind-selector.ts` |
| `reset-usage-selector.ts` | 重置用量额度选择 | `packages/tui/src/overlays/reset-usage-selector.ts` |
| `plugin-settings.ts` | 插件设置编辑 | `packages/tui/src/overlays/plugin-settings.ts` |
| `queue-mode-selector.ts` | 排队消息模式选择 | `packages/tui/src/overlays/queue-mode-selector.ts` |
| `plugin-selector.ts` | `/plugin` 安装/卸载 | `packages/tui/src/overlays/plugin-selector.ts` |
| `plan-save-overlay.ts` | plan 保存路径确认 | `packages/tui/src/overlays/plan-save-overlay.ts` |
| `plan-review-overlay.ts` | plan 审批（批准/继续） | `packages/tui/src/overlays/plan-review-overlay.ts` |
| `omfg-panel.ts` | `/omfg` 规则生成面板 | `packages/tui/src/overlays/omfg-panel.ts` |
| `pause-screen.ts` | `/pause` 暂停屏 | `packages/tui/src/overlays/pause-screen.ts` |
| `oauth-selector.ts` | `/login` `/logout` 提供方选择 | `packages/tui/src/overlays/oauth-selector.ts` |
| `move-overlay.ts` | `/move` 移动目录 | `packages/tui/src/overlays/move-overlay.ts` |
| `model-picker.ts` | Alt+P 临时模型选择 | `packages/tui/src/overlays/model-picker.ts` |
| `model-hub.ts` | `/model` 模型中枢 | `packages/tui/src/overlays/model-hub.ts` |
| `model-browser.ts` | 模型列表控件（被 hub/picker/advisor 复用） | `packages/tui/src/overlays/model-browser.ts` |
| `mcp-add-wizard.ts` | `/mcp add` 添加服务器向导 | `packages/tui/src/overlays/mcp-add-wizard.ts` |
| `logout-account-selector.ts` | `/logout` 账号选择 | `packages/tui/src/overlays/logout-account-selector.ts` |
| `login-dialog.ts` | 登录对话框 | `packages/tui/src/overlays/login-dialog.ts` |
| `hub-frame.ts` | hub 通用外框（helper） | `packages/tui/src/overlays/hub-frame.ts` |
| `jobs-panel.ts` | `/jobs` 后台任务面板 | `packages/tui/src/overlays/jobs-panel.ts` |
| `hook-selector.ts` | 扩展 `ctx.ui.select` | `packages/tui/src/overlays/hook-selector.ts` |
| `hook-input.ts` | 扩展 `ctx.ui.input` | `packages/tui/src/overlays/hook-input.ts` |
| `hook-editor.ts` | 扩展 `ctx.ui.editor` | `packages/tui/src/overlays/hook-editor.ts` |
| `history-search.ts` | Ctrl+R 历史搜索 | `packages/tui/src/overlays/history-search.ts` |
| `error-banner.ts` | 编辑器上方固定错误条 | `packages/tui/src/overlays/error-banner.ts` |
| `copy-selector.ts` | `/copy` 复制选择器（时间线/代码块下钻） | `packages/tui/src/overlays/copy-selector.ts` |
| `composer-shape-preview.ts` | 设置里的输入框形状预览 | `packages/tui/src/overlays/composer-shape-preview.ts` |
| `cleanse-panel.ts` | `/cleanse` 运行面板 | `packages/tui/src/overlays/cleanse-panel.ts` |
| `codex-reset-fireworks.ts` | Codex 额度重置庆祝动画 | `packages/tui/src/overlays/codex-reset-fireworks.ts:400` |
| `btw-panel.ts` | `/btw` 旁问答案面板 | `packages/tui/src/overlays/btw-panel.ts` |
| `bordered-loader.ts` | hook 带边框加载器 | `packages/tui/src/overlays/bordered-loader.ts:10` |
| `btw-history-panel.ts` | `/btw` 历史（复制/跟进/取消） | `packages/tui/src/overlays/btw-history-panel.ts` |
| `ask-dialog.ts` | ask 工具多问题对话框（推荐项/自定义/Review 标签页） | `packages/tui/src/overlays/ask-dialog.ts:530` |
| `annotation-overlay.ts` | `/annotate` 全屏 diff 批注 | `packages/tui/src/overlays/annotation-overlay.ts:148` |
| `agents-hub.ts` | `/agents` 智能体配置 hub | `packages/tui/src/overlays/agents-hub.ts:197` |
| `agent-transcript-viewer.ts` | 查看子智能体会话记录 | `packages/tui/src/overlays/agent-transcript-viewer.ts:165` |
| `agent-hub.ts` | Alt+A / Ctrl+S 智能体 hub（agents/activity 两个 tab） | `packages/tui/src/overlays/agent-hub.ts:320` |
| `agent-hub-renderer.ts` | hub 渲染 helper（非界面） | `packages/tui/src/overlays/agent-hub-renderer.ts` |
| `agent-hub-projection.ts` | hub 投影 helper | `packages/tui/src/overlays/agent-hub-projection.ts` |
| `agent-hub-types.ts` | hub 类型 | `packages/tui/src/overlays/agent-hub-types.ts` |
| `agent-activity.ts` | 活动索引类型 | `packages/tui/src/overlays/agent-activity.ts` |
| `advisor-config.ts` | `/advisor` 配置 WATCHDOG.yml | `packages/tui/src/overlays/advisor-config.ts:285` |
| `usage-display.ts` | 用量显示 helper | `packages/tui/src/overlays/usage-display.ts` |
| `copy-targets.ts` | 可复制内容抽取 helper | `packages/tui/src/overlays/copy-targets.ts` |
| `annotation-types.ts` | 批注类型 | `packages/tui/src/overlays/annotation-types.ts` |
| `session-observer-registry.ts` | observer 注册表（非界面） | `packages/tui/src/overlays/session-observer-registry.ts` |
| `running-subagent-badge.ts` | 运行中子智能体徽标 | `packages/tui/src/overlays/running-subagent-badge.ts` |
| `plan-toc.ts` | plan 目录 | `packages/tui/src/overlays/plan-toc.ts` |
| `model-selector.ts` | 旧模型选择器 | `packages/tui/src/overlays/model-selector.ts` |
| `composer-shape-registry.ts` | composer 形状注册表（数据） | `packages/tui/src/overlays/composer-shape-registry.ts` |
| `btw-history.ts` | btw 历史 helper | `packages/tui/src/overlays/btw-history.ts` |

## 21. 面板与选择器 · overlays/extensions 仪表盘（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `extensions/extension-dashboard.ts` | `/extensions` 扩展仪表盘 | `packages/tui/src/overlays/extensions/extension-dashboard.ts` |
| `extensions/extension-list.ts` | 扩展列表子面板 | `packages/tui/src/overlays/extensions/extension-list.ts` |
| `extensions/inspector-panel.ts` | 扩展检查器面板 | `packages/tui/src/overlays/extensions/inspector-panel.ts` |
| `extensions/state-manager.ts / mcp-runtime.ts / live-tool-session.ts / types.ts / inspector-model.ts / display-text.ts` | 扩展 dashboard 内部件（非独立界面） | `packages/tui/src/overlays/extensions/` |

## 22. 面板与选择器 · 整屏应用/调试器/向导（共 21 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `apps/standalone-picker.ts` | 独立选择器宿主 | `packages/tui/src/apps/standalone-picker.ts` |
| `apps/setup-model-picker.ts` | 首启选模型 | `packages/tui/src/apps/setup-model-picker.ts` |
| `apps/session-picker.ts` | 启动时挑会话（`--resume`） | `packages/tui/src/apps/session-picker.ts` |
| `apps/ps-top.ts` | `omp ps` 进程表（j/k/a/i/l/s/x/q） | `packages/tui/src/apps/ps-top.ts:76` |
| `apps/live-visualizer.ts` | live 语音可视化（Esc/Ctrl+C 停，Space 静音） | `packages/tui/src/apps/live-visualizer.ts:62` |
| `apps/cleanse-picker.ts` | cleanse 检查器选择 | `packages/tui/src/apps/cleanse-picker.ts` |
| `apps/cleanse-board.ts` | `/cleanse` 棋盘模型 | `packages/tui/src/apps/cleanse-board.ts:98` |
| `apps/autoresearch-dashboard.ts` | autoresearch 仪表盘（q/Esc 关，jk/g/G 滚动） | `packages/tui/src/apps/autoresearch-dashboard.ts:153` |
| `apps/if-bench-board.ts` | if-bench 面板 | `packages/tui/src/apps/if-bench-board.ts` |
| `apps/git/git-tui.ts` | `/git` 或 `omp git` 全屏 diff（tab 切焦点、q 退、v 选择、s/u 暂存） | `packages/tui/src/apps/git/git-tui.ts:614` |
| `apps/git/sidebar.ts` | git 侧栏（jk/hl/g/G/space/t/delete） | `packages/tui/src/apps/git/sidebar.ts:876` |
| `apps/git/help.ts` | git 快捷键表（?/q/Esc） | `packages/tui/src/apps/git/help.ts:69` |
| `apps/git/diff-pane.ts / avatar.ts / state.ts / colors.ts` | git TUI 内部件 | `packages/tui/src/apps/git/` |
| `apps/debug/log-viewer.ts` | 调试日志查看器 | `packages/tui/src/apps/debug/log-viewer.ts:560` |
| `apps/debug/raw-sse.ts` | 原始 SSE 流查看器 | `packages/tui/src/apps/debug/raw-sse.ts:79` |
| `apps/debug/protocol-probe.ts` | 终端能力探针 | `packages/tui/src/apps/debug/protocol-probe.ts:186` |
| `apps/debug/terminal-info.ts / viewer-frame.ts / log-formatting.ts / raw-sse-buffer.ts` | 调试内部件 | `packages/tui/src/apps/debug/` |
| `tools/bash-interactive.ts` | Console 全屏覆盖（原生 `omp.overlay.console`） | `packages/tui/src/tools/bash-interactive.ts:91` |
| `setup/wizard-overlay.ts + wizard.ts + scenes/*` | 首启设置向导各步（splash/sign-in/model/theme/glyph/composer/outro） | `packages/tui/src/setup/` |
| `setup/startup-splash.ts` | 启动 splash | `packages/tui/src/setup/startup-splash.ts` |
| `hotkeys-markdown.ts` | `/hotkeys` 快捷键表（?/Esc/q 关） | `packages/tui/src/hotkeys-markdown.ts:221` |

## 23. 挂件与扩展点 · HUD/卡片（共 22 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `hookWidgetContainerAbove/Below` | 扩展 `setWidget(aboveEditor/belowEditor)` 的挂载区 | `packages/coding-agent/src/modes/interactive-mode.ts:1867-1869` |
| `ctx.ui.setWidget(key, lines\|factory, {placement})` | 扩展挂件 API（最多 MAX_WIDGET_LINES 行，超出截断） | `packages/coding-agent/src/extensibility/extensions/types.ts:300` |
| `ctx.ui.setFooter/setHeader/setTitle` | 扩展替换页脚/页眉/终端标题 | `packages/coding-agent/src/extensibility/extensions/types.ts` |
| `ctx.ui.setEditorComponent` | 扩展自定义编辑器组件 | `packages/coding-agent/src/modes/interactive-mode.ts:7022` |
| `statusContainer` | 工作指示/临时状态区 | `packages/coding-agent/src/modes/types.ts:116` |
| `todoContainer` | 待办 HUD（可展开 todoExpanded） | `packages/coding-agent/src/modes/types.ts:119` |
| `subagentContainer + SubagentHudComponent` | 子智能体 HUD（onOpen→agent hub） | `packages/coding-agent/src/modes/types.ts:120` |
| `btwContainer` | 旁问面板槽 | `packages/coding-agent/src/modes/types.ts:121` |
| `omfgContainer / cleanseContainer` | omfg、cleanse 面板槽 | `packages/coding-agent/src/modes/types.ts:122-123` |
| `errorBannerContainer` | 固定错误条槽 | `packages/coding-agent/src/modes/types.ts:124` |
| `modelCycleContainer + segment-track` | 模型循环轨道显示 | `packages/coding-agent/src/modes/types.ts:125` |
| `deferredCommandContainer` | 延迟命令输出预览 | `packages/coding-agent/src/modes/types.ts:126` |
| `attachmentChipsContainer + AttachmentChipsBand` | 附件图片 chips 带 | `packages/coding-agent/src/modes/interactive-mode.ts:1871` |
| `pendingMessagesContainer` | 排队消息显示 | `packages/coding-agent/src/modes/types.ts:115` |
| `editorTopGap` | 编辑器上方空隙（band composer 时折叠） | `packages/tui/src/prompt/editor-top-gap.ts` |
| `TodoReminderComponent` | todo 提醒卡片 | `packages/tui/src/chat/todo-reminder.ts` |
| `TtsrNotificationComponent` | TTSR 规则触发通知卡片 | `packages/tui/src/chat/ttsr-notification.ts` |
| `PlanToc` | plan 目录挂件 | `packages/tui/src/overlays/plan-toc.ts` |
| `statusLine`（StatusLineComponent） | 底部状态条本体 | `packages/coding-agent/src/modes/interactive-mode.ts:1880` |
| `running-subagent-badge` | 运行中子智能体徽标 | `packages/tui/src/overlays/running-subagent-badge.ts` |
| `ChatBlock / StreamingPanel / MessageNotice / StatusNotice / TranscriptStatus` | 会话内提示/流式面板 | `packages/tui/src/chrome/` |
| `RecapNotice / LateDiagnosticsMessage / CompactionSummaryMessage / BranchSummaryMessage / CacheInvalidationMarker / BackgroundTanMessage / AdvisorMessage / CollabPromptMessage / SkillMessage / HookMessage / CustomMessage / ServedModelMarker / Reaction / StrippedToolCallsPlaceholder` | 各类会话卡片 | `packages/tui/src/chat/` |

## 24. 模式与开关 · approval（共 3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `always-ask` | 每次工具调用都询问 | `packages/coding-agent/src/tools/approval.ts:17` |
| `write` | 写操作询问，其余放行 | `packages/coding-agent/src/tools/approval.ts:17` |
| `yolo` | 自动批准所有工具调用 | `packages/coding-agent/src/tools/approval.ts:17` |

## 25. 模式与开关 · magic keyword（共 4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ultrathink` | 触发额外深思的特殊输入词 | `packages/coding-agent/src/modes/magic-keywords.ts` |
| `orchestrate` | 触发编排流程的特殊输入词 | `packages/coding-agent/src/modes/magic-keywords.ts` |
| `workflowz` | 触发工作流流程的特殊输入词 | `packages/coding-agent/src/modes/magic-keywords.ts` |
| `jevify` | 触发 jevify 行为的特殊输入词 | `packages/coding-agent/src/modes/magic-keywords.ts` |

## 26. 模式与开关 · 其余开关（共 35 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| plan mode | Alt+Shift+P 切换，plan 审批浮层 | `packages/tui/src/app-keybindings.ts:232` |
| goal mode（含 paused） | 目标续跑模式 | `packages/coding-agent/src/modes/types.ts:194-195` |
| loop mode（prompt/compact/reset）+ conditionTimeout | `/loop` 循环 | `packages/coding-agent/src/modes/types.ts:196` |
| vibe mode | vibeModeEnabled | `packages/coding-agent/src/modes/types.ts:193` |
| TTSR（规则触发/重写） | ttsr_triggered 通知 + TtsrManager | `packages/coding-agent/src/export/ttsr.ts` |
| `/omfg` 规则生成 | 自然语言生成 TTSR 规则 | `packages/coding-agent/src/modes/controllers/omfg-controller.ts` |
| skills / skillful | skills 列表、skill 提示卡片 | `packages/coding-agent/src/extensibility/skills.ts` |
| voice input：STT 按住 Space | push-to-talk（app.stt.toggle） | `packages/coding-agent/src/stt/push-to-talk.ts` |
| live voice（Ctrl+L） | `/live` 实时语音会话 + visualizer | `packages/coding-agent/src/modes/controllers/live-command-controller.ts:58` |
| TTS 朗读 | tts/settings.ts、speech.mode | `packages/coding-agent/src/tts/settings.ts` |
| 图片粘贴（Ctrl+V / Super+V） | 贴图 chip 处理 | `packages/coding-agent/src/modes/controllers/input-controller.ts:2345` |
| 原始文本粘贴 Ctrl+Shift+V | 原样粘贴路径 | `packages/coding-agent/src/modes/controllers/input-controller.ts:2463` |
| 大段粘贴菜单 | paste.largeMenuThreshold | `packages/coding-agent/src/modes/controllers/input-controller.ts:2485` |
| 记忆 memory | `/memory view\|queue\|stats\|diag` + mental models | `packages/coding-agent/src/modes/controllers/command-controller.ts:760` |
| mnemopi / hindsight 记忆后端 | 两套记忆后端 | `mnemopi/*, hindsight/*` |
| 压缩 compact（auto/manual，Esc 取消） | 自动/手动压缩 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1648` |
| handoff 交接 | 生成交接文档 | `packages/coding-agent/src/modes/controllers/command-controller.ts:1747` |
| ssh | 连接与管理 | `packages/coding-agent/src/modes/controllers/ssh-command-controller.ts` |
| extension / plugin / hook / MCP | 扩展/插件/钩子/MCP 接入 | `packages/coding-agent/src/modes/controllers/extension-ui-controller.ts` |
| 协作 collab（host/guest 会话） | 主机/访客协作 | `packages/coding-agent/src/collab/host.ts` |
| 会话 focus/observe 子智能体 | 聚焦/观察子智能体 | `packages/coding-agent/src/modes/controllers/session-focus-controller.ts` |
| vim 模式 | tui.vimMode / vimModeDisplay text\|icon\|none | `packages/tui/src/vim.ts` |
| thinking 显示与档位 | hideThinkingBlock，Ctrl+T / Shift+Tab | `packages/coding-agent/src/modes/interactive-mode.ts:202` |
| 工具输出展开/隐藏 | Ctrl+O / Ctrl+Shift+O | `packages/tui/src/app-keybindings.ts:132` |
| 队列/steering/followUp 模式 | all\|one-at-a-time | `packages/coding-agent/src/modes/settings.ts:694` |
| interruptMode | immediate\|wait | `packages/coding-agent/src/modes/settings.ts:720` |
| tree filter mode | TREE_FILTER_MODES | `packages/coding-agent/src/modes/settings.ts:867` |
| doubleEscapeAction | rewind\|tree\|none | `packages/coding-agent/src/modes/settings.ts:826` |
| readonly / plan-mode guard 工具限制 | 工具限制 | `packages/coding-agent/src/tools/plan-mode-guard.ts` |
| 命令审批 ACX/ACP 权限门 | 权限门 | `packages/coding-agent/src/session/acp-permission-gate.ts` |
| speculation（预执行） | 投机预执行 | `packages/coding-agent/src/speculation/host.ts` |
| 屏幕录制 `/record`、stream 直播 | 录制与直播 | `packages/coding-agent/src/modes/types.ts:465` |
| 外部编辑器 Ctrl+G | 打开外部编辑器 | `packages/tui/src/app-keybindings.ts:140` |
| composer 形状 8 种 | band/box/claude/pi/borderless/rule/field/rail | `packages/tui/src/overlays/composer-shape-registry.ts:8` |
| 特殊输入类型 | `!` bash、`/` 斜杠、`@` 文件/内部 URL、`:` 模型提及、`#` 记忆 | `packages/coding-agent/src/modes/controllers/input-controller.ts` |

## 27. 可扩展/可配置项（共 6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| keybindings.yml/yaml | 旧 keybindings.json 自动迁移 | `packages/tui/src/app-keybindings.ts:355-430` |
| ExtensionUIContext 扩展点 | widget/footer/header/title/editor/custom/select/input/editor/confirm/notify/setStatus/terminal input | `packages/coding-agent/src/extensibility/extensions/types.ts:266` |
| composer shape 扩展注册 | installExtensionComposerShape | `packages/tui/src/overlays/composer-shape-registry.ts:64` |
| status line 自定义段 | statusLine.leftSegments/rightSegments/segmentOptions | `packages/coding-agent/src/modes/settings.ts:276-292` |
| 主题 dark/light/symbolPreset/colorBlindMode | 主题与图标预设 | `packages/coding-agent/src/modes/settings.ts:58` |
| diff/符号/图标按 symbolPreset | unicode/nerd/ascii | `packages/coding-agent/src/modes/settings.ts:86` |

## 28. 特殊输入 · 前缀 —— 已被 §35 取代

> 本节是第一轮扫描留下的 8 条（`!` `!!` `$` `$$` `@<path>` `/skill:<name>` `/<prompt-template>` `/<file-command>`），第二轮逐条定位后**补全为 12 条并给出确切解析位置**，见 §35 —— **以 §35 为准**。
> 两者的关系：原 8 条里的 `!` `!!` `$` `$$` `@` `/` 都在 §35 里；原表把 `skill:` / prompt 模板 / 文件命令当成“前缀”，其实它们是 `/` 之下的三种命令来源（见 §9–§11）。

## 29. CLI · 子命令（共 50 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `launch` | 默认入口：交互/打印模式运行 assistant | `packages/coding-agent/src/cli-commands.ts:29` |
| `acp` | 以 ACP 协议 over stdio 运行 | `packages/coding-agent/src/cli-commands.ts:36` |
| `auth-broker` | 管理凭据 vault auth-broker | `packages/coding-agent/src/cli-commands.ts:41` |
| `auth-gateway` | 运行基于 broker 的转发代理 | `packages/coding-agent/src/cli-commands.ts:46` |
| `agents` | 管理内置任务 agent | `packages/coding-agent/src/cli-commands.ts:51` |
| `bench` | 模型 TTFT/吞吐基准 | `packages/coding-agent/src/cli-commands.ts:56` |
| `browser-relay` | 本地 CDP relay 驱动自有 Chrome | `packages/coding-agent/src/cli-commands.ts:61` |
| `cleanse` | 并行子 agent 检测修复诊断 | `packages/coding-agent/src/cli-commands.ts:66` |
| `collab` | 列出本地 Collab 主机/取链接 | `packages/coding-agent/src/cli-commands.ts:71` |
| `commit` | 生成提交信息并更新 changelog | `packages/coding-agent/src/cli-commands.ts:78` |
| `completions` | 打印 shell 补全脚本 | `packages/coding-agent/src/cli-commands.ts:83` |
| `__complete`（隐藏） | 内部补全辅助 | `packages/coding-agent/src/cli-commands.ts:88` |
| `compress` | 把文本改写为稠密 prompt 寄存器 | `packages/coding-agent/src/cli-commands.ts:93` |
| `config` | 管理配置项 | `packages/coding-agent/src/cli-commands.ts:98` |
| `dry-balance` | OAuth 账号均衡干跑 | `packages/coding-agent/src/cli-commands.ts:103` |
| `find` | 语义搜索行为到文件/行范围 | `packages/coding-agent/src/cli-commands.ts:108` |
| `gc` | 存储垃圾回收 | `packages/coding-agent/src/cli-commands.ts:113` |
| `grep` | 测试 grep 工具 | `packages/coding-agent/src/cli-commands.ts:118` |
| `gallery` | 预览渲染器视觉画廊 | `packages/coding-agent/src/cli-commands.ts:123` |
| `git` | 全屏 git UI | `packages/coding-agent/src/cli-commands.ts:128` |
| `grievances` | 查看/清理/上报工具问题 | `packages/coding-agent/src/cli-commands.ts:133` |
| `images`（别名 img） | 图片发布后端检查/诊断/清理 | `packages/coding-agent/src/cli-commands.ts:138` |
| `if-bench` | 指令遵循与工作记忆基准 | `packages/coding-agent/src/cli-commands.ts:144` |
| `install` | 安装/链接扩展包 | `packages/coding-agent/src/cli-commands.ts:149` |
| `join` | 加入共享 collab 会话（同 `/join`） | `packages/coding-agent/src/cli-commands.ts:154` |
| `login` | 登录模型 provider（`/login` 终端版） | `packages/coding-agent/src/cli-commands.ts:159` |
| `models` | 列出/搜索/刷新可用模型 | `packages/coding-agent/src/cli-commands.ts:164` |
| `plugin`（别名 plugins） | 管理插件 | `packages/coding-agent/src/cli-commands.ts:169` |
| `predict` | 对比各补全引擎 ghost text | `packages/coding-agent/src/cli-commands.ts:175` |
| `ps` | 列管守护进程后台进程 | `packages/coding-agent/src/cli-commands.ts:180` |
| `say` | 本地 TTS 合成并播放 | `packages/coding-agent/src/cli-commands.ts:185` |
| `clip` | 上传 `/record` 录屏为公开 clip | `packages/coding-agent/src/cli-commands.ts:190` |
| `play` | 回放 `/record` 录屏 | `packages/coding-agent/src/cli-commands.ts:195` |
| `share` | 分享已保存会话（同 `/share`） | `packages/coding-agent/src/cli-commands.ts:200` |
| `setup` | 引导设置或安装可选依赖 | `packages/coding-agent/src/cli-commands.ts:205` |
| `shell` | 交互式 shell 控制台 | `packages/coding-agent/src/cli-commands.ts:210` |
| `read` | 预览 read 工具结果 | `packages/coding-agent/src/cli-commands.ts:215` |
| `render` | 用生产管线渲染会话线程 | `packages/coding-agent/src/cli-commands.ts:220` |
| `skill`（别名 skills） | Skillshare 技能安装/搜索/发布 | `packages/coding-agent/src/cli-commands.ts:225` |
| `ssh` | 管理 SSH 主机配置 | `packages/coding-agent/src/cli-commands.ts:231` |
| `stats` | 查看使用统计 | `packages/coding-agent/src/cli-commands.ts:236` |
| `stream` | 广播本机会话屏到公开频道 | `packages/coding-agent/src/cli-commands.ts:241` |
| `update` | 检查并安装更新 | `packages/coding-agent/src/cli-commands.ts:246` |
| `usage` | 显示各账号 provider 限额 | `packages/coding-agent/src/cli-commands.ts:251` |
| `tiny-models` | 下载本地 tiny 模型 | `packages/coding-agent/src/cli-commands.ts:256` |
| `token` | 取某 provider 的 API key/OAuth token | `packages/coding-agent/src/cli-commands.ts:261` |
| `toks` | 用各离线分词器计数 | `packages/coding-agent/src/cli-commands.ts:266` |
| `ttsr` | 检查/测试 TTSR 规则 | `packages/coding-agent/src/cli-commands.ts:271` |
| `worktree`（别名 wt） | 增/列/清 git worktree | `packages/coding-agent/src/cli-commands.ts:276` |
| `search`（别名 q, web-search） | 测试 web 搜索 provider | `packages/coding-agent/src/cli-commands.ts:282` |

## 30. CLI · launch 标志（共 51 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--model` | 选择模型（模糊匹配） | `packages/coding-agent/src/commands/launch-help.ts:18` |
| `--smol` | 轻量任务快速模型 | `packages/coding-agent/src/commands/launch-help.ts:21` |
| `--slow` | 深度分析慢模型 | `packages/coding-agent/src/commands/launch-help.ts:22` |
| `--plan` | 架构规划模型 | `packages/coding-agent/src/commands/launch-help.ts:23` |
| `--prewalk` | 首次编辑后切换到快模型 | `packages/coding-agent/src/commands/launch-help.ts:24` |
| `--no-prewalk` | 禁用 prewalk | `packages/coding-agent/src/commands/launch-help.ts:28` |
| `--prewalk-into` | prewalk 目标模型 | `packages/coding-agent/src/commands/launch-help.ts:29` |
| `--plan-yolo` | 先只读规划并自动批准后实施 | `packages/coding-agent/src/commands/launch-help.ts:30` |
| `--plan-yolo-into` | plan-yolo 执行目标模型 | `packages/coding-agent/src/commands/launch-help.ts:34` |
| `--provider` | 指定 provider（旧式） | `packages/coding-agent/src/commands/launch-help.ts:35` |
| `--api-key` | API key | `packages/coding-agent/src/commands/launch-help.ts:36` |
| `--system-prompt` | 自定义系统提示 | `packages/coding-agent/src/commands/launch-help.ts:37` |
| `--system-prompt-template` | Handlebars 系统提示模板 | `packages/coding-agent/src/commands/launch-help.ts:38` |
| `--append-system-prompt` | 追加文本/文件到系统提示 | `packages/coding-agent/src/commands/launch-help.ts:41` |
| `--allow-home` | 允许在 ~ 启动 | `packages/coding-agent/src/commands/launch-help.ts:42` |
| `--profile` | 使用隔离 profile | `packages/coding-agent/src/commands/launch-help.ts:43` |
| `--alias` | 为 profile 建 shell 快捷方式并退出 | `packages/coding-agent/src/commands/launch-help.ts:44` |
| `--cwd` | 启动目录 | `packages/coding-agent/src/commands/launch-help.ts:45` |
| `--mode` | 输出模式 text/json/rpc/acp/rpc-ui | `packages/coding-agent/src/commands/launch-help.ts:46` |
| `--config` | 加载额外 config.yml 覆盖（可重复） | `packages/coding-agent/src/commands/launch-help.ts:50` |
| `--add-dir` | 追加工作区目录（可重复） | `packages/coding-agent/src/commands/launch-help.ts:54` |
| `--print (-p)` | 非交互处理提示后退出 | `packages/coding-agent/src/commands/launch-help.ts:58` |
| `--continue (-c)` | 继续上个会话 | `packages/coding-agent/src/commands/launch-help.ts:59` |
| `--resume (-r)` | 恢复会话（ID 前缀/路径/选择器） | `packages/coding-agent/src/commands/launch-help.ts:60` |
| `--from-claude` | 导入 Claude Code 会话 | `packages/coding-agent/src/commands/launch-help.ts:61` |
| `--from-codex` | 导入 Codex 会话 | `packages/coding-agent/src/commands/launch-help.ts:62` |
| `--session-dir` | 会话存储/查找目录 | `packages/coding-agent/src/commands/launch-help.ts:63` |
| `--no-session` | 不保存会话（临时） | `packages/coding-agent/src/commands/launch-help.ts:64` |
| `--models` | ctrl+p 循环的模型模式列表 | `packages/coding-agent/src/commands/launch-help.ts:65` |
| `--no-tools` | 禁用所有内置工具 | `packages/coding-agent/src/commands/launch-help.ts:66` |
| `--no-lsp` | 禁用 LSP 工具/格式化/诊断 | `packages/coding-agent/src/commands/launch-help.ts:67` |
| `--no-pty` | 禁用 PTY 交互式 bash | `packages/coding-agent/src/commands/launch-help.ts:68` |
| `--tools` | 启用工具列表（逗号分隔） | `packages/coding-agent/src/commands/launch-help.ts:69` |
| `--thinking` | 设置思考等级 | `packages/coding-agent/src/commands/launch-help.ts:70` |
| `--service-tier` | OpenAI 服务档 | `packages/coding-agent/src/commands/launch-help.ts:74` |
| `--hide-thinking` | TUI 隐藏思考块（仅显示） | `packages/coding-agent/src/commands/launch-help.ts:78` |
| `--advisor` | 启用 advisor 运行时 | `packages/coding-agent/src/commands/launch-help.ts:81` |
| `--external-thinking` | 私有草稿本+禁用推理 | `packages/coding-agent/src/commands/launch-help.ts:84` |
| `--hook` | 加载 hook/扩展文件（可重复） | `packages/coding-agent/src/commands/launch-help.ts:88` |
| `--extension (-e)` | 加载扩展文件（可重复） | `packages/coding-agent/src/commands/launch-help.ts:89` |
| `--no-extensions` | 禁用扩展发现 | `packages/coding-agent/src/commands/launch-help.ts:94` |
| `--no-skills` | 禁用技能发现/加载 | `packages/coding-agent/src/commands/launch-help.ts:97` |
| `--skills` | 技能 glob 过滤 | `packages/coding-agent/src/commands/launch-help.ts:98` |
| `--no-rules` | 禁用规则发现/加载 | `packages/coding-agent/src/commands/launch-help.ts:99` |
| `--export` | 导出会话文件为 HTML 并退出 | `packages/coding-agent/src/commands/launch-help.ts:100` |
| `--no-title` | 禁用标题自动生成 | `packages/coding-agent/src/commands/launch-help.ts:101` |
| `--no-ui` | rpc 模式下无头运行扩展 | `packages/coding-agent/src/commands/launch-help.ts:102` |
| `--print-thoughts` | 打印模式包含思考块 | `packages/coding-agent/src/commands/launch-help.ts:105` |
| `--max-time` | 超过时长后停止会话 | `packages/coding-agent/src/commands/launch-help.ts:106` |
| `--auto-approve`（别名 yolo） | 自动批准所有工具调用 | `packages/coding-agent/src/commands/launch-help.ts:107` |
| `--approval-mode` | 覆盖审批模式 always-ask/write/yolo | `packages/coding-agent/src/commands/launch-help.ts:111` |

## 31. CLI · flag-tables 独有标志（共 6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--fork` | 从指定会话 fork 出新会话 | `packages/coding-agent/src/cli/flag-tables.ts:161-163` |
| `--provider-session-id` | provider 侧会话 id | `packages/coding-agent/src/cli/flag-tables.ts:213-215` |
| `--prompt-cache-key` | provider prompt 缓存键 | `packages/coding-agent/src/cli/flag-tables.ts:216-218` |
| `--session` | 恢复会话（`--resume` 的另一写法） | `packages/coding-agent/src/cli/flag-tables.ts:279` |
| `--trusted-extension` | 标记受信扩展（可重复） | `packages/coding-agent/src/cli/flag-tables.ts:246-249` |
| `--plugin-dir` | 追加插件目录（可重复） | `packages/coding-agent/src/cli/flag-tables.ts:250-253` |

## 32. CLI · 全局标志（共 2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--help / -h` | 全局帮助 | `packages/coding-agent/src/cli/flag-tables.ts:290` |
| `--version / -v` | 全局版本 | `packages/coding-agent/src/cli/flag-tables.ts:291` |

## 33. 内置命令 · 子命令（共 129 条）

> 数法（payload 原文）：子命令 subcommands（共 129 条）—— 数法：builtin-*.ts 各 `subcommands:` 数组内的 name 项，加 /compact 引用的 COMPACT_MODES 表（session/compact-modes.ts:41）。标「4-tab 多行项」的 9 条即上一轮漏掉的那 9 行。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/security plan` | 创建一次不可变的安全扫描计划 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:281` |
| `/security scan` | 开始计划内或新建的原生安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:282` |
| `/security status` | 显示原生扫描任务状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:283` |
| `/security cancel` | 取消运行中的原生扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:284` |
| `/security scans` | 列出项目已存的安全扫描 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:285` |
| `/security show` | 渲染某次扫描或 security:// 资源 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:286` |
| `/security import` | 导入 SARIF 或 Codex 安全包 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:287` |
| `/security export` | 导出规范包 / SARIF / 报告 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:288` |
| `/security validate` | 用原生工具校验单条 finding | `packages/coding-agent/src/slash-commands/builtin-modes.ts:289` |
| `/security compare` | 比较两次扫描的 finding 血缘 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:290` |
| `/security disposition` | 为 finding 设置处置与理由 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:291` |
| `/setup providers` | 配置登录与联网搜索 provider | `packages/coding-agent/src/slash-commands/builtin-modes.ts:310` |
| `/goal set` | 设置或替换当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:377` |
| `/goal show` | 显示当前目标详情 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:378` |
| `/goal pause` | 暂停当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:379` |
| `/goal resume` | 恢复已暂停的目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:380` |
| `/goal drop` | 丢弃当前目标 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:381` |
| `/goal budget` | 调整目标的 token 预算 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:382` |
| `/fast on` | 启用 fast 模式（priority 档） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:553` |
| `/fast ultra` | 启用 Ultrafast（OpenAI/部分 Codex） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:554` |
| `/fast off` | 关闭 fast 模式 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:555` |
| `/fast status` | 显示 fast 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:556` |
| `/slow on` | 启用 slow（flex / Anthropic 低优先级） | `packages/coding-agent/src/slash-commands/builtin-modes.ts:581` |
| `/slow off` | 关闭 slow，回到标准服务 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:582` |
| `/slow status` | 显示 slow 模式状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:583` |
| `/skillful on` | 本会话在提示中列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:608` |
| `/skillful off` | 本会话不列出技能 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:609` |
| `/skillful status` | 显示技能列举状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:610` |
| `/extended-context on` | 启用更大的上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:664` |
| `/extended-context off` | 使用默认/标准价上下文窗口 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:665` |
| `/extended-context status` | 显示扩展上下文状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:666` |
| `/computer on` | 本会话启用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:691` |
| `/computer off` | 本会话停用 computer use | `packages/coding-agent/src/slash-commands/builtin-modes.ts:692` |
| `/computer status` | 显示 computer use 状态 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:693` |
| `/prewalk restart` | 回到 @default 并重新武装到 @smol 的交接 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:770` |
| `/modelpreset list` | 列出已保存的模型预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:821` |
| `/modelpreset save` | 保存当前角色模型与思考级别 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:822` |
| `/modelpreset switch` | 应用一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:823` |
| `/modelpreset delete` | 删除一个已保存的预设 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:824` |
| `/todo edit` | 在 $EDITOR 打开 todos（Markdown 往返） | `packages/coding-agent/src/slash-commands/builtin-session.ts:214` |
| `/todo copy` | 把 todos 以 Markdown 复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:215` |
| `/todo expand` | 在 HUD 显示全部阶段与任务 | `packages/coding-agent/src/slash-commands/builtin-session.ts:216` |
| `/todo collapse` | 恢复 HUD 的有界预览 | `packages/coding-agent/src/slash-commands/builtin-session.ts:217` |
| `/todo export` | 把 todos 写为 Markdown 文件 | `packages/coding-agent/src/slash-commands/builtin-session.ts:218` |
| `/todo import` | 从 Markdown 文件替换 todos | `packages/coding-agent/src/slash-commands/builtin-session.ts:219` |
| `/todo append` | 追加一条任务（阶段模糊匹配/自动建） | `packages/coding-agent/src/slash-commands/builtin-session.ts:221（4-tab 多行项）` |
| `/todo start` | 把任务标记为 in_progress | `packages/coding-agent/src/slash-commands/builtin-session.ts:225` |
| `/todo done` | 把任务/阶段/全部标记完成 | `packages/coding-agent/src/slash-commands/builtin-session.ts:226` |
| `/todo drop` | 把任务/阶段/全部标记放弃 | `packages/coding-agent/src/slash-commands/builtin-session.ts:227` |
| `/todo rm` | 移除任务/阶段/全部 | `packages/coding-agent/src/slash-commands/builtin-session.ts:228` |
| `/session info` | 显示当前会话信息与统计 | `packages/coding-agent/src/slash-commands/builtin-session.ts:252` |
| `/session delete` | 删除当前会话并回到选择器 | `packages/coding-agent/src/slash-commands/builtin-session.ts:253` |
| `/session pin` | 把当前 provider 固定到某个 OAuth 账号 | `packages/coding-agent/src/slash-commands/builtin-session.ts:255（4-tab 多行项）` |
| `/jobs full` | 显示完整未截断的命令行 | `packages/coding-agent/src/slash-commands/builtin-session.ts:329` |
| `/usage show` | 显示 provider 用量与限额 | `packages/coding-agent/src/slash-commands/builtin-session.ts:391` |
| `/usage reset` | 消耗一次已保存的限流重置 | `packages/coding-agent/src/slash-commands/builtin-session.ts:393（4-tab 多行项）` |
| `/changelog full` | 显示完整 changelog | `packages/coding-agent/src/slash-commands/builtin-session.ts:473` |
| `/changelog last` | 显示最近 N 个 release（默认 1） | `packages/coding-agent/src/slash-commands/builtin-session.ts:474` |
| `/mcp add` | 新增一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:703（4-tab 多行项）` |
| `/mcp list` | 列出全部已配置 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:707` |
| `/mcp remove` | 移除一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:708` |
| `/mcp test` | 测试到某 server 的连接 | `packages/coding-agent/src/slash-commands/builtin-session.ts:709` |
| `/mcp reauth` | 为某 server 重新授权 OAuth | `packages/coding-agent/src/slash-commands/builtin-session.ts:710` |
| `/mcp unauth` | 移除某 server 的 OAuth 授权 | `packages/coding-agent/src/slash-commands/builtin-session.ts:711` |
| `/mcp enable` | 启用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:712` |
| `/mcp disable` | 停用一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:713` |
| `/mcp smithery-search` | 搜索 Smithery 并部署一个 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:715（4-tab 多行项）` |
| `/mcp smithery-login` | 登录 Smithery 并缓存 API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:719` |
| `/mcp smithery-logout` | 移除已缓存的 Smithery API key | `packages/coding-agent/src/slash-commands/builtin-session.ts:720` |
| `/mcp reconnect` | 重连到指定 MCP server | `packages/coding-agent/src/slash-commands/builtin-session.ts:721` |
| `/mcp reload` | 强制重载 MCP 运行时工具 | `packages/coding-agent/src/slash-commands/builtin-session.ts:722` |
| `/mcp resources` | 列出已连 server 的可用资源 | `packages/coding-agent/src/slash-commands/builtin-session.ts:723` |
| `/mcp prompts` | 列出已连 server 的 prompts | `packages/coding-agent/src/slash-commands/builtin-session.ts:724` |
| `/mcp notifications` | 显示通知能力与订阅状态 | `packages/coding-agent/src/slash-commands/builtin-session.ts:725` |
| `/mcp help` | 显示 /mcp 帮助 | `packages/coding-agent/src/slash-commands/builtin-session.ts:726` |
| `/ssh add` | 新增一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:160（4-tab 多行项）` |
| `/ssh list` | 列出全部已配置 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:164` |
| `/ssh remove` | 移除一个 SSH host | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:165` |
| `/ssh help` | 显示 /ssh 帮助 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:166` |
| `/compact soft` | 本地用当前模型压缩（跳过服务端压缩） | `packages/coding-agent/src/session/compact-modes.ts:42（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射为子命令）` |
| `/compact remote` | 走服务端压缩，失败回退本地摘要 | `packages/coding-agent/src/session/compact-modes.ts:47（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| `/compact snapcompact` | 把历史归档成位图图片（不调 LLM） | `packages/coding-agent/src/session/compact-modes.ts:52（表由 packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:231 映射）` |
| `/shake elide` | 剥离工具结果与大块（默认） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:298` |
| `/shake images` | 剥离图片块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:299` |
| `/shake thinking` | 丢弃所有 thinking 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:300` |
| `/memory view` | 显示当前记忆注入 payload | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:549` |
| `/memory stats` | 显示记忆后端统计 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:550` |
| `/memory diagnose` | 运行记忆后端诊断 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:551` |
| `/memory queue` | 显示待合并的记忆增量 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:552` |
| `/memory sync` | 立即运行记忆合并 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:553` |
| `/memory clear` | 清除持久化记忆数据与产物 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:554` |
| `/memory reset` | clear 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:555` |
| `/memory enqueue` | 入队记忆合并维护 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:556` |
| `/memory rebuild` | enqueue 的别名 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:557` |
| `/memory mm list` | 列出当前 bank 的心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:558` |
| `/memory mm show` | 显示单个心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:559` |
| `/memory mm refresh` | 整库刷新自动刷新模型，或按 id 刷一个 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:561（4-tab 多行项）` |
| `/memory mm history` | 查看某心智模型的变更历史 diff | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:564` |
| `/memory mm seed` | 创建缺失的内置心智模型 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:565` |
| `/memory mm delete` | 从 bank 删除心智模型（需 id） | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:566` |
| `/memory mm reload` | 重新拉取缓存的 <mental_models> 块 | `packages/coding-agent/src/slash-commands/builtin-lifecycle.ts:567` |
| `/marketplace add` | 添加一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:51` |
| `/marketplace remove` | 移除一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:52` |
| `/marketplace update` | 更新 marketplace catalog | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:53` |
| `/marketplace list` | 列出已配置的 marketplace | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:54` |
| `/marketplace discover` | 浏览可安装的插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:55` |
| `/marketplace install` | 安装一个插件（无参走交互浏览器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:57（4-tab 多行项）` |
| `/marketplace uninstall` | 卸载一个插件（无参走选择器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:61` |
| `/marketplace installed` | 列出已安装的 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:62` |
| `/marketplace upgrade` | 升级过期插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:63` |
| `/marketplace help` | 显示用法指南 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:64` |
| `/plugins list` | 列出全部已装插件（npm+marketplace） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:432` |
| `/plugins enable` | 启用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:433` |
| `/plugins disable` | 停用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:434` |
| `/advisor on` | 启用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:68` |
| `/advisor off` | 停用 advisor | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:69` |
| `/advisor status` | 显示 advisor 状态 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:70` |
| `/advisor dump` | 把 advisor 记录复制到剪贴板 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:71` |
| `/advisor configure` | 打开 advisor 配置编辑器（TUI） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:72` |
| `/collab view` | 分享只读链接（访客可看不可提问） | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:294` |
| `/collab list` | 列出本机活跃 Collab host | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:295` |
| `/collab status` | 显示链接与参与者 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:296` |
| `/collab stop` | 停止分享 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:297` |
| `/browser headless` | 切换到无头模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:480` |
| `/browser visible` | 切换到可见模式 | `packages/coding-agent/src/slash-commands/builtin-collaboration.ts:481` |
| `/skills search` | 搜索技能注册表 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:70` |
| `/skills install` | 安装注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:71` |
| `/skills installed` | 列出已安装的注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:72` |
| `/skills update` | 在声明范围内更新注册表技能 | `packages/coding-agent/src/slash-commands/builtin-skills.ts:74（4-tab 多行项）` |

## 34. 内置命令 · 参数补全项（共 16 条）

> 数法（payload 原文）：参数补全项 argument completions（共 15 条）—— 数法：builtin-registry.ts:75-99 materializeTuiBuiltinSlashCommand 的分支 + builtin-completions.ts 导出的 builder + interactive-mode.ts 中 custom/extension 命令补全挂接点。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `buildArgumentCompletions（通用子命令补全）` | 由 subcommands 表生成：前缀过滤子命令名+usage 提示 | `packages/coding-agent/src/slash-commands/builtin-completions.ts:16` |
| `buildSubcommandInlineHint（子命令 ghost 提示）` | 补全子命令剩余字符与 usage 参数 | `packages/coding-agent/src/slash-commands/builtin-completions.ts:154` |
| `/marketplace 参数补全` | 补全 add/remove/update/list/discover/install/uninstall/installed/upgrade/help | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:50 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86` |
| `/mcp 参数补全（子命令层）` | 补全 17 个子命令名 | `packages/coding-agent/src/slash-commands/builtin-session.ts:701 → packages/coding-agent/src/slash-commands/builtin-registry.ts:85（buildMcpArgumentCompletions）` |
| `/mcp enable\|disable\|test\|remove\|reconnect\|reauth\|unauth <server>` | 补全已配置 MCP server 名（含 disabled） | `packages/coding-agent/src/slash-commands/builtin-completions.ts:33-47,72-104（collectMcpServerNames）` |
| `/mcp remove <name> [--scope user]` | 只补 config 文件中的 server；仅 user 配置项自动补 --scope user | `packages/coding-agent/src/slash-commands/builtin-completions.ts:118-150` |
| `/skills 参数补全` | 补全 search/install/installed/update | `packages/coding-agent/src/slash-commands/builtin-skills.ts:69 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86` |
| `/goal 参数补全` | 补全 set/show/pause/resume/drop/budget | `packages/coding-agent/src/slash-commands/builtin-modes.ts:376 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86` |
| `/prewalk 参数补全` | 补全 restart | `packages/coding-agent/src/slash-commands/builtin-modes.ts:770 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86` |
| `/modelpreset 参数补全` | 补全 list/save/switch/delete；无参时另弹预设名选择器 | `packages/coding-agent/src/slash-commands/builtin-modes.ts:820 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86；选择器 packages/coding-agent/src/slash-commands/builtin-modes.ts:849` |
| `/security 参数补全` | 补全 plan/scan/status/cancel/scans/show/import/export/validate/compare/disposition | `packages/coding-agent/src/slash-commands/builtin-modes.ts:280 → packages/coding-agent/src/slash-commands/builtin-registry.ts:83-86` |
| `/switch <model> 参数补全` | 先 @role 再 session 范围内 provider/id，保留 :level 后缀 | `packages/coding-agent/src/slash-commands/builtin-registry.ts:91-93；builder packages/coding-agent/src/slash-commands/builtin-completions.ts:197-227` |
| `/move <dir> 参数补全` | 按当前项目目录补全子目录（支持 ~/ 与相对） | `packages/coding-agent/src/slash-commands/builtin-registry.ts:88-90；builder packages/coding-agent/src/slash-commands/builtin-completions.ts:234-300` |
| `扩展命令 getArgumentCompletions` | 扩展经 api.registerCommand 提供的参数补全 | `packages/coding-agent/src/extensibility/extensions/types.ts:1331；挂接 packages/coding-agent/src/modes/interactive-mode.ts:2558-2564` |
| `自定义 TS 命令 getArgumentCompletions` | 项目/内置 TS 命令自带的参数补全（含 bundled annotate） | `packages/coding-agent/src/extensibility/custom-commands/types.ts:94；挂接 packages/coding-agent/src/modes/interactive-mode.ts:2568-2575；例 packages/coding-agent/src/extensibility/custom-commands/bundled/annotate/index.ts:319` |
| `autoresearch（内置扩展）参数补全` | 补全 off / clear | `packages/coding-agent/src/autoresearch/index.ts:127-143` |

## 35. 内置命令 · 特殊输入前缀（共 12 条）

> 数法（payload 原文）：特殊输入前缀（共 12 条）—— 数法：input-controller.ts / tui/src/prompt/* / editor.ts 中的前缀判定点。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `/（slash 命令）` | 行首 / 触发内置/文件/扩展/技能/模板命令解析与菜单 | `packages/coding-agent/src/slash-commands/helpers/parse.ts:26；派发 packages/coding-agent/src/modes/controllers/input-controller.ts:1060/1448/1894` |
| `!（bash 命令）` | 本地执行 bash，结果计入上下文 | `packages/coding-agent/src/modes/controllers/input-controller.ts:1138-1153` |
| `!!（bash，排除上下文）` | 本地执行 bash，结果不进入上下文 | `packages/coding-agent/src/modes/controllers/input-controller.ts:1139-1140` |
| `$（Python 执行）` | 在共享内核里运行 Python，结果计入上下文 | `packages/coding-agent/src/modes/controllers/input-controller.ts:194-206,1159` |
| `$$（Python，排除上下文）` | 在共享内核运行 Python，结果不入上下文 | `packages/coding-agent/src/modes/controllers/input-controller.ts:196,1159` |
| `@（文件提及）` | 补全/附加文件路径为附件；@role 也是模型别名写法 | `packages/tui/src/components/editor.ts:3108-3127；packages/tui/src/autocomplete.ts:116,842` |
| `^（模型提及）` | 把 ^provider/id 记为可委派模型，发送时展开为 agent 标记 | `packages/tui/src/prompt/model-mention-autocomplete.ts:33-35；packages/coding-agent/src/session/model-mentions.ts:92-94` |
| `:（emoji 补全）` | 输入 :name 弹出 emoji 建议并内联替换 | `packages/tui/src/prompt/emoji-autocomplete.ts:249-251` |
| `:（slash 名/参分隔符）` | /foo:bar 被解析为 name=foo args=bar（/skill:x、/force:x 同机制） | `packages/coding-agent/src/slash-commands/helpers/parse.ts:26-38` |
| `#（prompt actions）` | 补全 copy/undo/移动光标等提示词动作 | `packages/tui/src/prompt/prompt-action-autocomplete.ts:69-79；触发 packages/tui/src/components/editor.ts:3128-3131` |
| `#<number>（GitHub PR/issue）` | 把 #123 改写为 pr://123 或 issue://123 由 read 解析 | `packages/tui/src/prompt/github-ref-autocomplete.ts:41-46,58-77` |
| `-> / =>（yield 队列简写）` | 把该行作为 agent yield 后可队列消化的消息 | `packages/tui/src/prompt/queue-input.ts:1,25-28` |

## 36. 内置命令 · 动态命令来源机制（共 7 条）

> 数法（payload 原文）：动态命令来源（共 7 类）—— 数法：命令装配点 available-commands.ts / interactive-mode.ts#buildPendingSlashCommands + 各 loader。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `文件型 markdown 命令（FileSlashCommand）` | 目录：.omp/commands、~/.omp/agent/commands、.claude/commands(含子目录别名 sub:dir:name)、.codex/commands、.opencode/commands、.agent\|.agents/commands、插件包 commands/、Claude marketplace 插件 commands\|slash-commands；名字=文件名去 .md（claude 嵌套再加 : 命名别名）。本仓静态清单：.omp/commands/{cleanup,fix-issues,release,review-prs,triage}.md | `packages/coding-agent/src/extensibility/slash-commands.ts:72-111；packages/coding-agent/src/discovery/builtin.ts:347-355；packages/coding-agent/src/discovery/claude.ts:303-323；config/prompts 目录见 packages/coding-agent/src/config.ts:128` |
| `内嵌 bundled markdown 命令` | 构建期内嵌；仓库内静态清单仅 1 个：init | `packages/coding-agent/src/task/commands.ts:14；packages/coding-agent/src/extensibility/slash-commands.ts:95-110` |
| `prompt 模板（prompt template）` | 目录：~/.omp/agent/prompts/ 与 <cwd>/.omp/prompts/（递归）；名字=文件名去 .md；.github/prompts/*.prompt.md 经 prompt capability 也作为命令（名字=frontmatter.name 或 basename 去 .prompt.md） | `packages/coding-agent/src/config/prompt-templates.ts:70-110,148-165；packages/coding-agent/src/discovery/github.ts:244-270` |
| `项目/用户 TS 自定义命令（CustomCommand）` | 目录：<cwd>/.omp/commands/<name>/index.{ts,js,mjs,cjs} 与 ~/.omp/agent/commands/<name>/index.*（外加 getConfigDirs 其他源）；名字由模块 export 的 command.name 决定。仓库内 bundled 静态清单 3 个：green/review/annotate | `packages/coding-agent/src/extensibility/custom-commands/loader.ts:87-140,183-216；bundled 名 packages/coding-agent/src/extensibility/custom-commands/bundled/ci-green/index.ts:47、packages/coding-agent/src/extensibility/custom-commands/bundled/review/index.ts:380、packages/coding-agent/src/extensibility/custom-commands/bundled/annotate/index.ts:312` |
| `扩展 api.registerCommand` | 名字完全由扩展运行时注册；无静态清单。出货源码里唯一内置注册名=autoresearch（另有 ctrl+x 快捷键）。加载源：.omp/.pi extension-modules、已装插件、CLI -e、settings 配置路径 | `packages/coding-agent/src/extensibility/extensions/types.ts:1516-1524；packages/coding-agent/src/extensibility/extensions/loader.ts:555-640；唯一出货注册点 packages/coding-agent/src/autoresearch/index.ts:125` |
| `MCP prompt 命令` | 命名规则固定为 `<serverName>:<prompt.name>`；prompts 变化时重建 | `packages/coding-agent/src/sdk.ts:1455-1470；刷新 packages/coding-agent/src/sdk.ts:5149` |
| `skill 命令（skill:<name>）` | 名字=各 provider 发现的 SKILL.md 的 frontmatter.name（缺省用目录名），前缀 skill:；仓库内静态清单 3 个：tool-prompt-optimization/semantic-compression/system-prompts | `packages/coding-agent/src/extensibility/skills.ts:609-611；packages/coding-agent/src/discovery/helpers.ts:487-499；native 目录 packages/coding-agent/src/discovery/builtin.ts:287-311；本仓 .omp/skills/*/SKILL.md:2` |

## 37. 内置命令 · COLLAB 允许表不一致定论（共 1 条）

> 数法（payload 原文）：全仓检索 `COLLAB_GUEST_ALLOWED_COMMANDS` 的唯一消费点，再对 `name: "help"`/`name: "theme"` 命令注册、CLI 顶层词与 `registerCommand(` 静态命中逐一核验。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `help` / `theme`（COLLAB 允许表） | 陈旧 allowlist 死键：非 TUI 内置、非扩展、非文件命令 | `packages/coding-agent/src/slash-commands/builtin-registry.ts:143`；`packages/coding-agent/src/collab/guest.ts:43-58`；`packages/coding-agent/src/autoresearch/index.ts:125` |

> 依据：(a) `COLLAB_GUEST_ALLOWED_COMMANDS` 全仓只在 `packages/coding-agent/src/slash-commands/builtin-registry.ts:143` 被消费，且只在 `BUILTIN_SLASH_COMMAND_LOOKUP.get(parsed.name)` 命中后生效（同文件 :135-146），即只对已注册内置命令生效。
> (b) 全仓 `name: "help"` / `name: "theme"` 在任何命令注册表零命中；出货源码 `registerCommand(` 仅 `packages/coding-agent/src/autoresearch/index.ts:125` 一处（名字 "autoresearch"）。
> (c) CLI 顶层词、文件型命令、prompt 模板亦无 `help`/`theme`。

## 38. CLI · 各子命令自有 flag（共 261 条）

### launch —— 其余 57 条见 §30 与 §31（不重复列）（共 1 条）
> 数法：launch 的 flag 已在上一轮的 §30（51 条）与 §31（6 条）逐条列过，本节只补那两节没有的 1 条（payload 的 launch 组共 58 行，其中 57 行与 §30/§31 重复）。

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--acp-terminal-auth` | ACP 终端登录模式切换（launch 与 acp 均接受） | `packages/coding-agent/src/modes/acp/terminal-auth.ts:1` |

### acp（无自有 flag；strict=false，透传 launch flag 面）（共 2 条）
> 数法（payload 原文）：acp（无自有 flag；strict=false，透传 launch flag 面）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--acp-terminal-auth` | 打开交互 TUI 并去掉强制 acp 模式 | `packages/coding-agent/src/modes/acp/terminal-auth.ts:1` |
| `（继承 launch 全部 flag）` | acp 走 parseArgs，与 launch 共享 flag 面 | `packages/coding-agent/src/commands/acp.ts:15` |

### auth-broker（共 10 条）
> 数法（payload 原文）：auth-broker（10 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/auth-broker.ts:31` |
| `-b/--bind` | serve 的绑定地址 host:port | `packages/coding-agent/src/commands/auth-broker.ts:32` |
| `--regenerate` | 重新生成 bearer token | `packages/coding-agent/src/commands/auth-broker.ts:33` |
| `--via` | login 经 SSH user@host 远程登录 | `packages/coding-agent/src/commands/auth-broker.ts:34` |
| `--provider` | import 时覆盖 provider id | `packages/coding-agent/src/commands/auth-broker.ts:37` |
| `--include-disabled` | import 时也导入 disabled:true 的凭证 | `packages/coding-agent/src/commands/auth-broker.ts:40` |
| `--from-local` | migrate 源：本地 SQLite+环境变量（必填） | `packages/coding-agent/src/commands/auth-broker.ts:43` |
| `--include-env` | migrate 时采集环境变量 API key | `packages/coding-agent/src/commands/auth-broker.ts:46` |
| `--include-oauth` | migrate 时同时上传本地 OAuth | `packages/coding-agent/src/commands/auth-broker.ts:49` |
| `--dry-run` | import/login --via/migrate 只打印不执行 | `packages/coding-agent/src/commands/auth-broker.ts:52` |

### auth-gateway（共 6 条）
> 数法（payload 原文）：auth-gateway（6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | token/status/check 输出 JSON | `packages/coding-agent/src/commands/auth-gateway.ts:26` |
| `-b/--bind` | serve 的绑定地址 host:port | `packages/coding-agent/src/commands/auth-gateway.ts:27` |
| `--regenerate` | 重新生成网关 bearer token | `packages/coding-agent/src/commands/auth-gateway.ts:28` |
| `--no-auth` | serve 关闭入站 bearer 鉴权 | `packages/coding-agent/src/commands/auth-gateway.ts:29` |
| `--trust-proxy-headers` | serve 信任反代的转发 IP 头 | `packages/coding-agent/src/commands/auth-gateway.ts:33` |
| `--strict` | check 额外向 provider 端点探测凭证 | `packages/coding-agent/src/commands/auth-gateway.ts:36` |

### agents（共 5 条）
> 数法（payload 原文）：agents（5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-f/--force` | 覆盖已存在的 agent 文件 | `packages/coding-agent/src/commands/agents.ts:23` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/agents.ts:24` |
| `--dir` | 指定输出目录（覆盖 --user/--project） | `packages/coding-agent/src/commands/agents.ts:25` |
| `--user` | 写入 ~/.omp/agent/agents（默认） | `packages/coding-agent/src/commands/agents.ts:26` |
| `--project` | 写入 ./.omp/agents | `packages/coding-agent/src/commands/agents.ts:27` |

### bench（共 14 条）
> 数法（payload 原文）：bench（14 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--runs` | 每模型请求数（--detailed 为每阶段） | `packages/coding-agent/src/commands/bench.ts:17` |
| `--max-tokens` | 每请求最大输出 token | `packages/coding-agent/src/commands/bench.ts:21` |
| `--prompt` | 自定义提示词（chat/generation） | `packages/coding-agent/src/commands/bench.ts:24` |
| `--profile` | 工作负载 chat/prefill/generation/mix | `packages/coding-agent/src/commands/bench.ts:25` |
| `--prefill-bytes` | prefill 合成输入字节数 | `packages/coding-agent/src/commands/bench.ts:30` |
| `--detailed` | 跑单用户/并行/prefill 三阶段 | `packages/coding-agent/src/commands/bench.ts:33` |
| `--service-tier` | 按模型族应用 service tier | `packages/coding-agent/src/commands/bench.ts:37` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/bench.ts:41` |
| `--par` | 并行查询/请求数 | `packages/coding-agent/src/commands/bench.ts:42` |
| `--cache` | 独立冷/热 prompt-cache 对 | `packages/coding-agent/src/commands/bench.ts:45` |
| `--cache-prefix-file` | --cache 用的稳定前缀文件 | `packages/coding-agent/src/commands/bench.ts:48` |
| `--cache-prefix-bytes` | --cache 稳定前缀字节预算 | `packages/coding-agent/src/commands/bench.ts:49` |
| `--cache-pairs` | --cache 每模型冷/热对数量 | `packages/coding-agent/src/commands/bench.ts:50` |
| `--cache-concurrency` | --cache 并发对数 | `packages/coding-agent/src/commands/bench.ts:51` |

### browser-relay（共 5 条）
> 数法（payload 原文）：browser-relay（5 条，action: serve/install）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-p/--port` | 中继监听端口 | `packages/coding-agent/src/commands/browser-relay.ts:24` |
| `--token` | 要求扩展携带的令牌 | `packages/coding-agent/src/commands/browser-relay.ts:25` |
| `--dir` | 扩展安装目录（install） | `packages/coding-agent/src/commands/browser-relay.ts:26` |
| `--no-group` | 不把可控标签归入 omp 标签组 | `packages/coding-agent/src/commands/browser-relay.ts:29` |
| `-v/--verbose` | 向 stderr 打印中继流量摘要 | `packages/coding-agent/src/commands/browser-relay.ts:33` |

### cleanse（共 4 条）
> 数法（payload 原文）：cleanse（4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-n/--agents` | 文件不相交子代理上限 | `packages/coding-agent/src/commands/cleanse.ts:16` |
| `-m/--model` | 子代理模型选择器 | `packages/coding-agent/src/commands/cleanse.ts:21` |
| `-t/--tests` | 同时跑项目测试套件 | `packages/coding-agent/src/commands/cleanse.ts:26` |
| `-a/--all` | 跳过选择器跑全部检查器 | `packages/coding-agent/src/commands/cleanse.ts:31` |

### clip（共 3 条）
> 数法（payload 原文）：clip（3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-t/--title` | Clip 标题 | `packages/coding-agent/src/commands/clip.ts:21` |
| `-d/--description` | 播放器下方 Clip 描述 | `packages/coding-agent/src/commands/clip.ts:22` |
| `--server` | Stream 服务器基址 | `packages/coding-agent/src/commands/clip.ts:23` |

### collab（共 2 条）
> 数法（payload 原文）：collab（2 条，action: list/link）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--view` | link 只请求只读链接 | `packages/coding-agent/src/commands/collab.ts:22` |
| `-j/--json` | 输出确定性 JSON | `packages/coding-agent/src/commands/collab.ts:26` |

### commit（共 6 条）
> 数法（payload 原文）：commit（6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--push` | 提交后推送 | `packages/coding-agent/src/commands/commit.ts:15` |
| `--dry-run` | 仅预览不提交 | `packages/coding-agent/src/commands/commit.ts:16` |
| `--no-changelog` | 跳过 changelog 更新 | `packages/coding-agent/src/commands/commit.ts:17` |
| `--legacy` | 使用旧式确定性流程 | `packages/coding-agent/src/commands/commit.ts:18` |
| `-c/--context` | 给模型的额外上下文 | `packages/coding-agent/src/commands/commit.ts:19` |
| `-m/--model` | 覆盖模型选择 | `packages/coding-agent/src/commands/commit.ts:20` |

### completions（无 flag；位置参数 shell=bash/zsh/fish）（共 1 条）
> 数法（payload 原文）：completions（无 flag；位置参数 shell=bash/zsh/fish）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 仅需位置参数 <bash\|zsh\|fish> | `packages/coding-agent/src/commands/completions.ts:35` |

### __complete（无 flag；隐藏，strict=false）（共 1 条）
> 数法（payload 原文）：__complete（无 flag；隐藏，strict=false）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 位置参数 <kind> [-- <prefix>] 动态补全 | `packages/coding-agent/src/commands/complete.ts:17` |

### compress（共 5 条）
> 数法（payload 原文）：compress（5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-o/--out` | 单文件时输出到指定路径 | `packages/coding-agent/src/commands/compress.ts:13` |
| `-i/--inPlace` | 原地覆盖每个源文件 | `packages/coding-agent/src/commands/compress.ts:14` |
| `-r/--rounds` | 每文件最大改写轮数 | `packages/coding-agent/src/commands/compress.ts:15` |
| `-n/--agents` | 并发压缩文件数 | `packages/coding-agent/src/commands/compress.ts:16` |
| `-m/--model` | 模型选择器 | `packages/coding-agent/src/commands/compress.ts:17` |

### config（共 1 条）
> 数法（payload 原文）：config（1 条，action: list/get/set/reset/path/init-xdg）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/config.ts:32` |

### dry-balance（共 5 条）
> 数法（payload 原文）：dry-balance（5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--model` | 模型选择器 | `packages/coding-agent/src/commands/dry-balance.ts:15` |
| `--count` | 尝试的随机 session id 数 | `packages/coding-agent/src/commands/dry-balance.ts:16` |
| `--concurrency` | 并发凭证解析数 | `packages/coding-agent/src/commands/dry-balance.ts:17` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/dry-balance.ts:18` |
| `--bench` | 每个 OAuth 账号发一次基准请求 | `packages/coding-agent/src/commands/dry-balance.ts:19` |

### find（共 4 条）
> 数法（payload 原文）：find（4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-k/--keyword` | 额外词法关键词（可重复/逗号） | `packages/coding-agent/src/commands/find.ts:17` |
| `--hidden` | 包含点文件/点目录 | `packages/coding-agent/src/commands/find.ts:22` |
| `--json` | 输出完整 JSON 结果 | `packages/coding-agent/src/commands/find.ts:23` |
| `-q/--quiet` | 抑制 stderr 进度 | `packages/coding-agent/src/commands/find.ts:24` |

### gc（共 12 条）
> 数法（payload 原文）：gc（12 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--apply` | 实际应用变更（默认 dry-run） | `packages/coding-agent/src/commands/gc.ts:12` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/gc.ts:13` |
| `--agent-dir` | 要维护的 agent 目录 | `packages/coding-agent/src/commands/gc.ts:14` |
| `--blobs` | 清扫无引用 blob | `packages/coding-agent/src/commands/gc.ts:15` |
| `--archive` | 归档冷会话 | `packages/coding-agent/src/commands/gc.ts:16` |
| `--wal` | checkpoint history/model 数据库 WAL | `packages/coding-agent/src/commands/gc.ts:17` |
| `--stale` | 清理残留标记/旧调试报告/collab 副本 | `packages/coding-agent/src/commands/gc.ts:18` |
| `--cold-archive-after-days` | 归档前最小会话年龄 | `packages/coding-agent/src/commands/gc.ts:21` |
| `--retain-newest-global` | 全局保留最新 N 个会话 | `packages/coding-agent/src/commands/gc.ts:22` |
| `--retain-newest-per-cwd` | 每 cwd 保留最新 N 个会话 | `packages/coding-agent/src/commands/gc.ts:23` |
| `--stale-retain-newest` | 保留最新 N 个调试报告/collab 副本 | `packages/coding-agent/src/commands/gc.ts:24` |
| `--stale-retain-days` | 调试报告/collab 副本最小年龄 | `packages/coding-agent/src/commands/gc.ts:27` |

### grep（共 6 条）
> 数法（payload 原文）：grep（6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-g/--glob` | 按 glob 过滤文件 | `packages/coding-agent/src/commands/grep.ts:19` |
| `-l/--limit` | 最大匹配数 | `packages/coding-agent/src/commands/grep.ts:20` |
| `-C/--context` | 上下文行数 | `packages/coding-agent/src/commands/grep.ts:21` |
| `-f/--files` | 只输出文件名 | `packages/coding-agent/src/commands/grep.ts:22` |
| `-c/--count` | 输出每文件匹配计数 | `packages/coding-agent/src/commands/grep.ts:23` |
| `--no-gitignore` | 包含被 .gitignore 排除的文件 | `packages/coding-agent/src/commands/grep.ts:24` |

### gallery（共 12 条）
> 数法（payload 原文）：gallery（12 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--surface` | 只渲染 tool/composer/segment 面（可重复） | `packages/coding-agent/src/commands/gallery.ts:20` |
| `-t/--tool` | 按名渲染单个工具 | `packages/coding-agent/src/commands/gallery.ts:25` |
| `--composer` | 按名渲染单个 composer 形态 | `packages/coding-agent/src/commands/gallery.ts:26` |
| `--segment` | 按名渲染单个状态栏 segment | `packages/coding-agent/src/commands/gallery.ts:27` |
| `-s/--state` | 只渲染指定生命周期状态（可重复） | `packages/coding-agent/src/commands/gallery.ts:28` |
| `-w/--width` | 渲染宽度（列） | `packages/coding-agent/src/commands/gallery.ts:34` |
| `-e/--expanded` | 渲染展开变体 | `packages/coding-agent/src/commands/gallery.ts:35` |
| `--plain` | 去掉 ANSI 样式 | `packages/coding-agent/src/commands/gallery.ts:40` |
| `--screenshot` | 经 VHS 截图 PNG 而非打印 ANSI | `packages/coding-agent/src/commands/gallery.ts:41` |
| `-o/--out` | 截图输出路径 | `packages/coding-agent/src/commands/gallery.ts:46` |
| `--font` | 截图字体族 | `packages/coding-agent/src/commands/gallery.ts:50` |
| `--font-size` | 截图字号（pt） | `packages/coding-agent/src/commands/gallery.ts:51` |

### git（共 1 条）
> 数法（payload 原文）：git（1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-C/--dir` | 在另一目录运行 | `packages/coding-agent/src/commands/git.ts:26` |

### grievances（共 5 条）
> 数法（payload 原文）：grievances（5 条，action: list/clean/push）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-n/--limit` | 显示最近 issue 数（list） | `packages/coding-agent/src/commands/grievances.ts:24` |
| `-t/--tool` | 按工具名过滤（list/clean） | `packages/coding-agent/src/commands/grievances.ts:25` |
| `-j/--json` | 输出 JSON | `packages/coding-agent/src/commands/grievances.ts:26` |
| `--id` | 按 id 删除单条（clean） | `packages/coding-agent/src/commands/grievances.ts:27` |
| `--all` | 删除全部（clean） | `packages/coding-agent/src/commands/grievances.ts:28` |

### images（别名 img；5 条，action: status/doctor/probe/purge）（共 5 条）
> 数法（payload 原文）：images（别名 img；5 条，action: status/doctor/probe/purge）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出单个 JSON 文档 | `packages/coding-agent/src/commands/images.ts:18` |
| `--apply` | 实际执行 purge 删除 | `packages/coding-agent/src/commands/images.ts:19` |
| `--all` | purge 全部而非仅过期项 | `packages/coding-agent/src/commands/images.ts:20` |
| `--dir` | 项目目录 | `packages/coding-agent/src/commands/images.ts:21` |
| `--timeout` | 外部健康探测超时（秒） | `packages/coding-agent/src/commands/images.ts:22` |

### if-bench（共 6 条）
> 数法（payload 原文）：if-bench（6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--turns` | 每模型最大轮数 | `packages/coding-agent/src/commands/if-bench.ts:16` |
| `--length` | 字符数组长度（偶数 8-26） | `packages/coding-agent/src/commands/if-bench.ts:17` |
| `--max-tokens` | 每轮最大输出 token | `packages/coding-agent/src/commands/if-bench.ts:18` |
| `--nya-max` | nya{1,N} 最长猫叫 | `packages/coding-agent/src/commands/if-bench.ts:19` |
| `--par` | 并发模型数 | `packages/coding-agent/src/commands/if-bench.ts:20` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/if-bench.ts:21` |

### install（共 7 条）
> 数法（payload 原文）：install（4 条 + 目标分类；install 是 plugin install/link 的便捷入口）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/install.ts:55` |
| `--force` | 强制安装 | `packages/coding-agent/src/commands/install.ts:56` |
| `--dry-run` | 只显示将执行的动作 | `packages/coding-agent/src/commands/install.ts:57` |
| `--scope` | 安装范围 user(默认)/project（仅市场安装） | `packages/coding-agent/src/commands/install.ts:58` |
| `target=本地路径` | 走 plugin link 软链到插件集（.//~//盘符/存在的目录） | `packages/coding-agent/src/cli/classify-install-target.ts:60` |
| `target=name@marketplace` | 走市场安装（右侧为已知市场名时） | `packages/coding-agent/src/cli/classify-install-target.ts:80` |
| `target=npm spec` | 其余按 npm 包安装（含 @scope/pkg、pkg@1.2.3） | `packages/coding-agent/src/cli/classify-install-target.ts:83` |

### join（无 flag；位置参数 link）（共 1 条）
> 数法（payload 原文）：join（无 flag；位置参数 link）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 仅需位置参数 <collab link> | `packages/coding-agent/src/commands/join.ts:14` |

### login（无 flag；位置参数 provider）（共 1 条）
> 数法（payload 原文）：login（无 flag；位置参数 provider）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 仅需位置参数 [provider]，省略则交互选择 | `packages/coding-agent/src/commands/login.ts:14` |

### models（共 5 条）
> 数法（payload 原文）：models（5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/models.ts:27` |
| `--kind` | 目录类别（chat 等 / all） | `packages/coding-agent/src/commands/models.ts:28` |
| `-e/--extension` | 列出前加载扩展文件（可重复） | `packages/coding-agent/src/commands/models.ts:33` |
| `--no-extensions` | 禁用扩展发现 | `packages/coding-agent/src/commands/models.ts:38` |
| `--config` | 额外 config 覆盖（可重复） | `packages/coding-agent/src/commands/models.ts:41` |

### plugin（别名 plugins；9 flag + 12 action + marketplace 5 子动作 + config 5 子动作）（共 27 条）
> 数法（payload 原文）：plugin（别名 plugins；9 flag + 12 action + marketplace 5 子动作 + config 5 子动作）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/plugin.ts:42` |
| `--fix` | doctor 尝试修复问题 | `packages/coding-agent/src/commands/plugin.ts:43` |
| `--force` | 强制安装 | `packages/coding-agent/src/commands/plugin.ts:44` |
| `--dry-run` | 只显示将执行的动作 | `packages/coding-agent/src/commands/plugin.ts:45` |
| `-l/--local` | 操作本地插件目录 | `packages/coding-agent/src/commands/plugin.ts:46` |
| `--enable` | 启用 feature（逗号分隔） | `packages/coding-agent/src/commands/plugin.ts:47` |
| `--disable` | 禁用 feature（逗号分隔） | `packages/coding-agent/src/commands/plugin.ts:48` |
| `--set` | 整体设置 plugin config key=value | `packages/coding-agent/src/commands/plugin.ts:49` |
| `--scope` | 安装范围 user(默认)/project | `packages/coding-agent/src/commands/plugin.ts:50` |
| `action: install` | 安装插件（npm/git/市场/本地） | `packages/coding-agent/src/commands/plugin.ts:11` |
| `action: uninstall` | 卸载插件 | `packages/coding-agent/src/commands/plugin.ts:12` |
| `action: list` | 列出已安装插件（默认动作） | `packages/coding-agent/src/commands/plugin.ts:13` |
| `action: link` | 软链本地插件目录进插件集 | `packages/coding-agent/src/commands/plugin.ts:14` |
| `action: doctor` | 检查插件健康（--fix 修复） | `packages/coding-agent/src/commands/plugin.ts:15` |
| `action: features` | 查看/改插件可选 feature | `packages/coding-agent/src/commands/plugin.ts:16` |
| `action: config` | 读写插件配置 | `packages/coding-agent/src/commands/plugin.ts:17` |
| `action: enable` | 启用插件 | `packages/coding-agent/src/commands/plugin.ts:18` |
| `action: disable` | 禁用插件 | `packages/coding-agent/src/commands/plugin.ts:19` |
| `action: marketplace` | 管理市场（见下 5 子动作） | `packages/coding-agent/src/commands/plugin.ts:20` |
| `action: discover` | 浏览市场可用插件 [marketplace] | `packages/coding-agent/src/commands/plugin.ts:21` |
| `action: upgrade` | 升级插件（指定或用全部） | `packages/coding-agent/src/commands/plugin.ts:22` |
| `marketplace add <source>` | 添加市场源 | `packages/coding-agent/src/cli/plugin-cli.ts:214` |
| `marketplace remove\|rm <name>` | 移除市场 | `packages/coding-agent/src/cli/plugin-cli.ts:229` |
| `marketplace update [name]` | 更新一个或全部市场 | `packages/coding-agent/src/cli/plugin-cli.ts:245` |
| `marketplace list` | 列出已配置市场（默认子动作） | `packages/coding-agent/src/cli/plugin-cli.ts:210` |
| `config list\|get\|set\|delete\|validate` | 插件设置子动作（validate 无需插件名） | `packages/coding-agent/src/cli/plugin-cli.ts:866` |
| `features <plugin> [--enable\|--disable\|--set]` | 查看并改插件 feature（位置参数=插件名） | `packages/coding-agent/src/cli/plugin-cli.ts:772` |

### predict（无 flag）（共 1 条）
> 数法（payload 原文）：predict（无 flag）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 交互式比较各补全引擎幽灵文本 | `packages/coding-agent/src/commands/predict.ts:8` |

### ps（共 10 条）
> 数法（payload 原文）：ps（10 条，action: list/info/logs/stop/kill/restart）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-a/--all` | 列出其他项目与已退出的全局服务 | `packages/coding-agent/src/commands/ps.ts:27` |
| `-j/--json` | 输出机器可读 JSON | `packages/coding-agent/src/commands/ps.ts:28` |
| `--plain` | 静态列表而非交互监视器 | `packages/coding-agent/src/commands/ps.ts:29` |
| `--dir` | 指定另一项目目录 | `packages/coding-agent/src/commands/ps.ts:30` |
| `--global` | 指定机器级服务域（如 browser-relay） | `packages/coding-agent/src/commands/ps.ts:31` |
| `-f/--follow` | 持续流式输出日志 | `packages/coding-agent/src/commands/ps.ts:32` |
| `--head` | 从头读日志而非尾部 | `packages/coding-agent/src/commands/ps.ts:33` |
| `-n/--lines` | 日志行数（最多 1000） | `packages/coding-agent/src/commands/ps.ts:34` |
| `--grep` | 日志行正则过滤 | `packages/coding-agent/src/commands/ps.ts:35` |
| `--timeout` | stop 硬杀前宽限秒数 | `packages/coding-agent/src/commands/ps.ts:36` |

### say（共 4 条）
> 数法（payload 原文）：say（4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--voice` | 语音 id | `packages/coding-agent/src/commands/say.ts:35` |
| `--model` | 本地 TTS 模型 key | `packages/coding-agent/src/commands/say.ts:36` |
| `-f/--file` | 从文件读取要朗读的文本 | `packages/coding-agent/src/commands/say.ts:37` |
| `-o/--out` | 写 WAV 到路径而非播放 | `packages/coding-agent/src/commands/say.ts:38` |

### play（共 2 条）
> 数法（payload 原文）：play（2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-s/--speed` | 回放倍速 | `packages/coding-agent/src/commands/play.ts:16` |
| `-i/--idle-limit` | 帧间隙上限（秒） | `packages/coding-agent/src/commands/play.ts:17` |

### share（共 1 条）
> 数法（payload 原文）：share（1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--gist` | 上传到私密 GitHub gist 而非分享服务器 | `packages/coding-agent/src/commands/share.ts:31` |

### setup（共 2 条）
> 数法（payload 原文）：setup（2 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-c/--check` | 仅检查依赖是否安装 | `packages/coding-agent/src/commands/setup.ts:44` |
| `--json` | 输出状态 JSON | `packages/coding-agent/src/commands/setup.ts:45` |

### shell（共 3 条）
> 数法（payload 原文）：shell（3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-C/--cwd` | 命令工作目录 | `packages/coding-agent/src/commands/shell.ts:13` |
| `-t/--timeout` | 每命令超时（毫秒） | `packages/coding-agent/src/commands/shell.ts:14` |
| `--no-snapshot` | 不从用户 shell 取快照 | `packages/coding-agent/src/commands/shell.ts:15` |

### read（无 flag；位置参数 path，支持 :sel 语法）（共 1 条）
> 数法（payload 原文）：read（无 flag；位置参数 path，支持 :sel 语法）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `（无 flag）` | 展示 read 工具对 path/URL/内部 URI 的返回 | `packages/coding-agent/src/commands/read.ts:14` |

### render（共 6 条）
> 数法（payload 原文）：render（6 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-w/--width` | 渲染宽度（列） | `packages/coding-agent/src/commands/render.ts:17` |
| `--height` | 视口高度（行） | `packages/coding-agent/src/commands/render.ts:18` |
| `-t/--timing` | 打印阶段耗时与字节数到 stderr | `packages/coding-agent/src/commands/render.ts:19` |
| `--repaint` | 额外整屏重绘 N 次做基准 | `packages/coding-agent/src/commands/render.ts:20` |
| `--plain` | 去掉 ANSI 样式 | `packages/coding-agent/src/commands/render.ts:23` |
| `-q/--quiet` | 抑制 transcript 输出 | `packages/coding-agent/src/commands/render.ts:24` |

### skill（别名 skills；12 flag + 14 action）（共 13 条）
> 数法（payload 原文）：skill（别名 skills；12 flag + 14 action）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-g/--global` | 使用用户级 skills.json（install/update/uninstall） | `packages/coding-agent/src/commands/skill.ts:23` |
| `-y/--yes` | 对带脚本的 skill 免确认安装/更新 | `packages/coding-agent/src/commands/skill.ts:24` |
| `--json` | 输出 JSON（search/info/token/list） | `packages/coding-agent/src/commands/skill.ts:25` |
| `--sort` | 搜索排序 relevance/downloads/recent | `packages/coding-agent/src/commands/skill.ts:26` |
| `--scope` | 发布 scope（默认 Stencil 用户名） | `packages/coding-agent/src/commands/skill.ts:27` |
| `--tag` | 发布版本的 dist-tag | `packages/coding-agent/src/commands/skill.ts:28` |
| `--dry-run` | 打包校验但不发布 | `packages/coding-agent/src/commands/skill.ts:29` |
| `--allow-secrets` | 发现疑似凭证仍发布 | `packages/coding-agent/src/commands/skill.ts:30` |
| `--registry` | Registry 基址（覆盖 skills.registryUrl） | `packages/coding-agent/src/commands/skill.ts:31` |
| `--undo` | 撤销 yank 或弃用 | `packages/coding-agent/src/commands/skill.ts:32` |
| `--package` | token 限定到某包（可重复） | `packages/coding-agent/src/commands/skill.ts:33` |
| `--expires` | token 有效期（天） | `packages/coding-agent/src/commands/skill.ts:34` |
| `action: publish\|version\|tag\|yank\|deprecate\|owner\|token\|import\|install\|update\|uninstall\|search\|info\|list` | 14 个位置动作（SKILL_ACTIONS 枚举） | `packages/coding-agent/src/cli/skill-cli.ts:27` |

### ssh（共 8 条）
> 数法（payload 原文）：ssh（8 条，action: add/remove/list）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/ssh.ts:28` |
| `--host` | 主机地址 | `packages/coding-agent/src/commands/ssh.ts:29` |
| `--user` | 用户名 | `packages/coding-agent/src/commands/ssh.ts:30` |
| `--port` | 端口 | `packages/coding-agent/src/commands/ssh.ts:31` |
| `--key` | 身份密钥路径 | `packages/coding-agent/src/commands/ssh.ts:32` |
| `--desc` | 主机描述 | `packages/coding-agent/src/commands/ssh.ts:33` |
| `--compat` | 启用兼容模式 | `packages/coding-agent/src/commands/ssh.ts:34` |
| `--scope` | 配置范围 project/user | `packages/coding-agent/src/commands/ssh.ts:35` |

### stats（共 4 条）
> 数法（payload 原文）：stats（4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-p/--port` | 仪表盘服务端口 | `packages/coding-agent/src/commands/stats.ts:14` |
| `--host` | 绑定主机 | `packages/coding-agent/src/commands/stats.ts:15` |
| `-j/--json` | 以 JSON 输出统计 | `packages/coding-agent/src/commands/stats.ts:16` |
| `-s/--summary` | 向控制台打印摘要 | `packages/coding-agent/src/commands/stats.ts:17` |

### stream（共 3 条）
> 数法（payload 原文）：stream（3 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--title` | 直播标题（默认目录名） | `packages/coding-agent/src/commands/stream.ts:15` |
| `--server` | Stream 服务器基址 | `packages/coding-agent/src/commands/stream.ts:16` |
| `--no-tui` | 用行式控制台替代交互 TUI | `packages/coding-agent/src/commands/stream.ts:17` |

### update（共 5 条）
> 数法（payload 原文）：update（5 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-f/--force` | 强制更新 | `packages/coding-agent/src/commands/update.ts:15` |
| `-c/--check` | 仅检查不安装 | `packages/coding-agent/src/commands/update.ts:16` |
| `-l/--plugins` | 更新已安装插件 | `packages/coding-agent/src/commands/update.ts:17` |
| `--canary` | 切到 canary 通道并更新 | `packages/coding-agent/src/commands/update.ts:18` |
| `--stable` | 切回 stable 通道 | `packages/coding-agent/src/commands/update.ts:19` |

### usage（共 7 条）
> 数法（payload 原文）：usage（7 条，action: invalidate/clients）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-j/--json` | 以 JSON 输出用量报告 | `packages/coding-agent/src/commands/usage.ts:20` |
| `-p/--provider` | 只看指定 provider id | `packages/coding-agent/src/commands/usage.ts:21` |
| `-r/--redact` | 遮蔽账号邮箱/id 便于截图 | `packages/coding-agent/src/commands/usage.ts:22` |
| `--history` | 显示用量历史快照 | `packages/coding-agent/src/commands/usage.ts:27` |
| `-d/--days` | 历史窗口天数 | `packages/coding-agent/src/commands/usage.ts:31` |
| `-e/--extension` | 抓取前加载扩展文件（可重复） | `packages/coding-agent/src/commands/usage.ts:32` |
| `--no-extensions` | 禁用扩展发现 | `packages/coding-agent/src/commands/usage.ts:37` |

### tiny-models（共 1 条）
> 数法（payload 原文）：tiny-models（1 条，action: download/list）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/tiny-models.ts:22` |

### token（共 4 条）
> 数法（payload 原文）：token（4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--raw` | 输出原始凭证值不解析嵌套 JSON | `packages/coding-agent/src/commands/token.ts:59` |
| `--force-refresh` | 即使未过期也强制刷新 OAuth token | `packages/coding-agent/src/commands/token.ts:63` |
| `-a/--account` | 选第 N 个 OAuth 账号（1 基） | `packages/coding-agent/src/commands/token.ts:67` |
| `-l/--list` | 列出该 provider 的 OAuth 账号后退出 | `packages/coding-agent/src/commands/token.ts:71` |

### toks（共 1 条）
> 数法（payload 原文）：toks（1 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/toks.ts:70` |

### ttsr（共 10 条）
> 数法（payload 原文）：ttsr（10 条，action: test/list/scan）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--file` | 片段文件路径或 - 读 stdin（test） | `packages/coding-agent/src/commands/ttsr.ts:37` |
| `-r/--rule` | 单独测试某规则文件 | `packages/coding-agent/src/commands/ttsr.ts:38` |
| `--source` | 匹配源 text/thinking/tool | `packages/coding-agent/src/commands/ttsr.ts:42` |
| `--tool` | source=tool 时的工具名 | `packages/coding-agent/src/commands/ttsr.ts:46` |
| `-p/--path` | 候选文件路径（scope/glob/AST 推断） | `packages/coding-agent/src/commands/ttsr.ts:49` |
| `--agent` | 按某 agent 评估 agents 作用域（test） | `packages/coding-agent/src/commands/ttsr.ts:53` |
| `-v/--verbose` | 显示所有被评估规则 | `packages/coding-agent/src/commands/ttsr.ts:56` |
| `--json` | 输出 JSON | `packages/coding-agent/src/commands/ttsr.ts:57` |
| `--no-gitignore` | 包含被 .gitignore 排除的文件（scan） | `packages/coding-agent/src/commands/ttsr.ts:58` |
| `--max-bytes` | 扫描文件大小上限，0 不限（scan） | `packages/coding-agent/src/commands/ttsr.ts:59` |

### worktree（别名 wt；8 条，action: list/clear/add）（共 8 条）
> 数法（payload 原文）：worktree（别名 wt；8 条，action: list/clear/add）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `-C/--cwd` | 仓库/基目录（add） | `packages/coding-agent/src/commands/worktree.ts:34` |
| `-b/--branch` | 新建分支（add，与 --force-branch 互斥） | `packages/coding-agent/src/commands/worktree.ts:38` |
| `-B/--force-branch` | 新建或重置分支（add，与 --branch 互斥） | `packages/coding-agent/src/commands/worktree.ts:43` |
| `-d/--detach` | 分离 HEAD（add） | `packages/coding-agent/src/commands/worktree.ts:48` |
| `-q/--quiet` | 抑制 add 输出 | `packages/coding-agent/src/commands/worktree.ts:53` |
| `--all` | clear 时一并清除活跃 PR worktree | `packages/coding-agent/src/commands/worktree.ts:58` |
| `-n/--dry-run` | 只打印将删除的项（clear） | `packages/coding-agent/src/commands/worktree.ts:62` |
| `-j/--json` | 输出机器可读 JSON | `packages/coding-agent/src/commands/worktree.ts:67` |

### search（别名 q/web-search；4 条）（共 4 条）
> 数法（payload 原文）：search（别名 q/web-search；4 条）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `--model` | 目录模型选择器 | `packages/coding-agent/src/commands/web-search.ts:20` |
| `--recency` | 时效过滤 day/week/month/year | `packages/coding-agent/src/commands/web-search.ts:21` |
| `-l/--limit` | 返回结果上限 | `packages/coding-agent/src/commands/web-search.ts:22` |
| `--compact` | 渲染精简输出 | `packages/coding-agent/src/commands/web-search.ts:23` |

## 39. 设置 · modes/settings.ts（共 83 条）

### 常规（无 UI 设置）（共 3 条）
> 数法（payload 原文）：常规（无 UI 设置） 共 3 条（数法：settings.ts 顶部 'General settings (no UI)' 段的 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `setupVersion（cfgSetupVersion）` | 内部 setup 版本号，无 UI。默认 0 | `packages/coding-agent/src/modes/settings.ts:27` |
| `autoResume（cfgAutoResume）` | 启动时自动恢复当前目录最近会话。默认 false | `packages/coding-agent/src/modes/settings.ts:29` |
| `git.enabled（cfgGitEnabled）` | TUI 显示 git 分支/状态/PR 并监视仓库元数据。默认 true | `packages/coding-agent/src/modes/settings.ts:41` |

### 外观 · 主题（Appearance/Theme）（共 4 条）
> 数法（payload 原文）：外观 · 主题（Appearance/Theme） 共 4 条（数法：settings.ts 'Theme' 段 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `theme.dark（cfgThemeDark）` | 深色终端背景所用主题；值取自运行时主题注册表。默认 titanium | `packages/coding-agent/src/modes/settings.ts:58` |
| `theme.light（cfgThemeLight）` | 浅色终端背景所用主题；值取自运行时主题注册表。默认 light | `packages/coding-agent/src/modes/settings.ts:72` |
| `symbolPreset（cfgSymbolPreset）` | 图标/符号字形集：unicode \| nerd \| ascii。默认 unicode | `packages/coding-agent/src/modes/settings.ts:86` |
| `colorBlindMode（cfgColorBlindMode）` | diff 新增用蓝色代替绿色。默认 false | `packages/coding-agent/src/modes/settings.ts:109` |

### 外观 · 输入框（Composer）（共 2 条）
> 数法（payload 原文）：外观 · 输入框（Composer） 共 2 条（数法：settings.ts 'Composer' 段 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `composer.shape（cfgComposerShape）` | 输入编辑器与状态栏的视觉布局；取值运行时提供。默认 band | `packages/coding-agent/src/modes/settings.ts:123` |
| `composer.tokenRate（cfgComposerTokenRate）` | 工作行显示实时生成 tok/s（会话标题右侧）。默认 false | `packages/coding-agent/src/modes/settings.ts:137` |

### 外观 · 状态栏（Status Line）（共 10 条）
> 数法（payload 原文）：外观 · 状态栏（Status Line） 共 10 条（数法：settings.ts 'Status line' 段 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `statusLine.preset（cfgStatusLinePreset）` | 状态栏预置：default\|minimal\|compact\|full\|nerd\|ascii\|custom。默认 default | `packages/coding-agent/src/modes/settings.ts:151` |
| `statusLine.separator（cfgStatusLineSeparator）` | 段间分隔符：powerline\|powerline-thin\|slash\|pipe\|block\|none\|ascii。默认 powerline-thin | `packages/coding-agent/src/modes/settings.ts:173` |
| `statusLine.contextLine（cfgStatusLineContextLine）` | 中线段反映上下文用量：off\|percentage\|annotated\|embedded。默认 embedded | `packages/coding-agent/src/modes/settings.ts:195` |
| `statusLine.sessionAccent（cfgStatusLineSessionAccent）` | 用会话名颜色作编辑器边框与状态栏间隙。默认 true | `packages/coding-agent/src/modes/settings.ts:226` |
| `statusLine.transparent（cfgStatusLineTransparent）` | 状态栏用终端默认背景而非主题底色。默认 false | `packages/coding-agent/src/modes/settings.ts:238` |
| `statusLine.compactThinkingLevel（cfgStatusLineCompactThinkingLevel）` | 思考等级以单图标显示在模型名上。默认 true | `packages/coding-agent/src/modes/settings.ts:251` |
| `statusLine.showHookStatus（cfgStatusLineShowHookStatus）` | 在状态栏下方显示 hook 状态消息。默认 true | `packages/coding-agent/src/modes/settings.ts:264` |
| `statusLine.leftSegments（cfgStatusLineLeftSegments）` | 自定义左侧段列表（数组）。默认 CUSTOM_STATUS_LINE_DEFAULTS.left | `packages/coding-agent/src/modes/settings.ts:276` |
| `statusLine.rightSegments（cfgStatusLineRightSegments）` | 自定义右侧段列表（数组）。默认 CUSTOM_STATUS_LINE_DEFAULTS.right | `packages/coding-agent/src/modes/settings.ts:283` |
| `statusLine.segmentOptions（cfgStatusLineSegmentOptions）` | 各状态栏段的选项（record）。默认 {}（EMPTY_UNKNOWN_RECORD） | `packages/coding-agent/src/modes/settings.ts:290` |

### 外观 · 图片（Images）（共 3 条）
> 数法（payload 原文）：外观 · 图片（Images） 共 3 条（数法：settings.ts 'Images' 组 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `terminal.showImages（cfgTerminalShowImages）` | 终端内联渲染图片（需图片协议）。默认 true | `packages/coding-agent/src/modes/settings.ts:297` |
| `images.autoResize（cfgImagesAutoResize）` | 大图缩到 2000x2000 以兼容模型。默认 true | `packages/coding-agent/src/modes/settings.ts:310` |
| `images.blockImages（cfgImagesBlockImages）` | 阻止图片发送给 LLM provider。默认 false | `packages/coding-agent/src/modes/settings.ts:322` |

### 外观 · 终端显示与内联图尺寸（tui.* / display.*）（共 25 条）
> 数法（payload 原文）：外观 · 终端显示与内联图尺寸（tui.* / display.*） 共 25 条（数法：settings.ts 从 tui.maxInlineImageColumns 到 tui.imeSafeCursor 的 register 逐行计数）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tui.maxInlineImageColumns（cfgTuiMaxInlineImageColumns）` | 内联图最大列宽；0=不限。默认 100 | `packages/coding-agent/src/modes/settings.ts:334` |
| `tui.maxInlineImageRows（cfgTuiMaxInlineImageRows）` | 内联图最大行高；0=仅视口限制。默认 20 | `packages/coding-agent/src/modes/settings.ts:343` |
| `tui.maxInlineImages（cfgTuiMaxInlineImages）` | 保留为终端图形的最大图片数；0=不限。默认 8 | `packages/coding-agent/src/modes/settings.ts:352` |
| `tui.resizeScrollback（cfgTuiResizeScrollback）` | 终端 resize 后回滚缓冲刷新：append\|rebuild\|preserve。默认 rebuild | `packages/coding-agent/src/modes/settings.ts:360` |
| `terminal.showProgress（cfgTerminalShowProgress）` | 运行中发 OSC 9;4 原生进度。默认 false | `packages/coding-agent/src/modes/settings.ts:390` |
| `tui.textSizing（cfgTuiTextSizing）` | Kitty 下 H1 标题 2x 渲染（OSC 66）。默认 false | `packages/coding-agent/src/modes/settings.ts:403` |
| `tui.renderMermaid（cfgTuiRenderMermaid）` | Mermaid 代码块渲染为 ASCII 图。默认 true | `packages/coding-agent/src/modes/settings.ts:416` |
| `tui.reactions（cfgTuiReactions）` | 让 agent 用 emoji 徽章回应你的消息。默认 true | `packages/coding-agent/src/modes/settings.ts:428` |
| `tui.codexResetFireworks（cfgTuiCodexResetFireworks）` | Codex 周用量重置/存储重置时放烟花。默认 false | `packages/coding-agent/src/modes/settings.ts:440` |
| `tui.titleState（cfgTuiTitleState）` | 终端标题分隔符显示运行状态。默认 true | `packages/coding-agent/src/modes/settings.ts:454` |
| `tui.titleSpinner（cfgTuiTitleSpinner）` | 标题 spinner 字形：braille\|pulse\|dots\|line。默认 braille | `packages/coding-agent/src/modes/settings.ts:467` |
| `tui.hyperlinks（cfgTuiHyperlinks）` | OSC 8 可点链接：off\|auto\|always。默认 auto | `packages/coding-agent/src/modes/settings.ts:487` |
| `tui.mouse（cfgTuiMouse）` | 捕获鼠标点击以聚焦卡片/HUD 行。默认 false | `packages/coding-agent/src/modes/settings.ts:504` |
| `tui.tight（cfgTuiTight）` | 去除输出左右各 1 字符内边距。默认 false | `packages/coding-agent/src/modes/settings.ts:519` |
| `display.shimmer（cfgDisplayShimmer）` | 工作/加载动画：classic\|kitt\|disabled。默认 classic | `packages/coding-agent/src/modes/settings.ts:531` |
| `display.pinnedAgents（cfgDisplayPinnedAgents）` | 编辑器上方固定 live-agent 列表：off\|collapsed\|full。默认 collapsed | `packages/coding-agent/src/modes/settings.ts:550` |
| `display.subagentLivePreview（cfgDisplaySubagentLivePreview）` | 每个固定 subagent 行下显示当前工具调用。默认 false | `packages/coding-agent/src/modes/settings.ts:569` |
| `display.smoothStreaming（cfgDisplaySmoothStreaming）` | 平滑显示流式文本与工具输入。默认 true | `packages/coding-agent/src/modes/settings.ts:581` |
| `display.hideToolActivity（cfgDisplayHideToolActivity）` | 从记录里隐藏工具调用与结果。默认 false | `packages/coding-agent/src/modes/settings.ts:593` |
| `display.showTokenUsage（cfgDisplayShowTokenUsage）` | 助手消息显示每轮 token 用量。默认 false | `packages/coding-agent/src/modes/settings.ts:605` |
| `display.showTurnTime（cfgDisplayShowTurnTime）` | 显示 prompt 到 yield 总耗时。默认 false | `packages/coding-agent/src/modes/settings.ts:617` |
| `display.cacheMissMarker（cfgDisplayCacheMissMarker）` | 缓存未命中的回合后显示分隔线。默认 false | `packages/coding-agent/src/modes/settings.ts:629` |
| `display.collapseCompacted（cfgDisplayCollapseCompacted）` | 把压缩前历史折叠到摘要分隔线后。默认 true | `packages/coding-agent/src/modes/settings.ts:652` |
| `showHardwareCursor（cfgShowHardwareCursor）` | 显示终端光标以支持 IME。默认 true（平台可覆盖） | `packages/coding-agent/src/modes/settings.ts:665` |
| `tui.imeSafeCursor（cfgTuiImeSafeCursor）` | IME 安全布局：prompt 底边框另起一行。默认 false | `packages/coding-agent/src/modes/settings.ts:677` |

### 交互 · 输入（Interaction/Input）（共 18 条）
> 数法（payload 原文）：交互 · 输入（Interaction/Input） 共 18 条（数法：settings.ts 从 steeringMode 到 paste.largeMenuThreshold 的 register 逐行计数）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `steeringMode（cfgSteeringMode）` | agent 工作时排队消息处理：all\|one-at-a-time。默认 one-at-a-time | `packages/coding-agent/src/modes/settings.ts:694` |
| `followUpMode（cfgFollowUpMode）` | 回合结束后 follow-up 排空：all\|one-at-a-time。默认 one-at-a-time | `packages/coding-agent/src/modes/settings.ts:707` |
| `interruptMode（cfgInterruptMode）` | 转向消息何时打断工具：immediate\|wait。默认 immediate | `packages/coding-agent/src/modes/settings.ts:720` |
| `tui.vimMode（cfgTuiVimMode）` | 模态 Vim prompt 编辑。默认 false | `packages/coding-agent/src/modes/settings.ts:733` |
| `tui.vimModeDisplay（cfgTuiVimModeDisplay）` | Vim 模式指示：text\|icon\|none。默认 text | `packages/coding-agent/src/modes/settings.ts:747` |
| `loop.mode（cfgLoopMode）` | /loop 迭代间动作：prompt\|compact\|reset。默认 prompt | `packages/coding-agent/src/modes/settings.ts:766` |
| `loop.conditionTimeoutMs（cfgLoopConditionTimeoutMs）` | /loop 条件命令最大等待 ms；0=无限。默认 30000 | `packages/coding-agent/src/modes/settings.ts:792` |
| `composer.recallClearedDrafts（cfgComposerRecallClearedDrafts）` | 保留 ctrl+c 清除的草稿到退出。默认 true | `packages/coding-agent/src/modes/settings.ts:812` |
| `doubleEscapeAction（cfgDoubleEscapeAction）` | 空编辑器连按 Esc 动作：rewind\|tree\|none。默认 rewind | `packages/coding-agent/src/modes/settings.ts:826` |
| `input.bareExitOnEmptySession（cfgBareExitOnEmptySession）` | 首条消息前输入 exit/quit/q 即退出。默认 true | `packages/coding-agent/src/modes/settings.ts:841` |
| `input.bareSlashCommands（cfgBareSlashCommands）` | 输入无斜杠命令名即执行该命令。默认 false | `packages/coding-agent/src/modes/settings.ts:854` |
| `treeFilterMode（cfgTreeFilterMode）` | 会话树默认过滤模式；值来自外部 TREE_FILTER_MODES。默认 default | `packages/coding-agent/src/modes/settings.ts:867` |
| `autocompleteMaxVisible（cfgAutocompleteMaxVisible）` | 自动补全最大可见项（3-20）。默认 10 | `packages/coding-agent/src/modes/settings.ts:880` |
| `spelling.typoDetection（cfgSpellingTypoDetection）` | 用 macOS 词典标记拼写错误。默认 true | `packages/coding-agent/src/modes/settings.ts:900` |
| `spelling.autocomplete（cfgSpellingAutocomplete）` | 内联词补全：off\|auto\|ngram\|smollm（darwin 加 apple）。默认 auto | `packages/coding-agent/src/modes/settings.ts:913` |
| `spelling.autocorrect（cfgSpellingAutocorrect）` | 完成词后应用 macOS 拼写纠正。默认 false | `packages/coding-agent/src/modes/settings.ts:945` |
| `emojiAutocomplete（cfgEmojiAutocomplete）` | 补全 :name: 表情与文字 emoticon。默认 true | `packages/coding-agent/src/modes/settings.ts:958` |
| `paste.largeMenuThreshold（cfgPasteLargeMenuThreshold）` | 粘贴达到此行数时给出处理菜单；0=关。默认 100 | `packages/coding-agent/src/modes/settings.ts:971` |

### 交互 · 启动与更新（Startup & Updates）（共 7 条）
> 数法（payload 原文）：交互 · 启动与更新（Startup & Updates） 共 7 条（数法：settings.ts 'Startup & Updates' 组 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `startup.quiet（cfgStartupQuiet）` | 跳过欢迎屏与启动状态消息。默认 false | `packages/coding-agent/src/modes/settings.ts:991` |
| `startup.showSplash（cfgStartupShowSplash）` | 正常启动显示完整动画 splash。默认 false | `packages/coding-agent/src/modes/settings.ts:1003` |
| `startup.setupWizard（cfgStartupSetupWizard）` | 每个 setup 版本显示一次新引导步骤。默认 true | `packages/coding-agent/src/modes/settings.ts:1016` |
| `startup.checkUpdate（cfgStartupCheckUpdate）` | 启动时检查 omp 更新。默认 true | `packages/coding-agent/src/modes/settings.ts:1028` |
| `update.channel（cfgUpdateChannel）` | omp update/启动检查所用渠道：stable\|canary。默认 stable | `packages/coding-agent/src/modes/settings.ts:1040` |
| `marketplace.autoUpdate（cfgMarketplaceAutoUpdate）` | 启动检查插件更新：off\|notify\|auto。默认 notify | `packages/coding-agent/src/modes/settings.ts:1057` |
| `startup.changelogMode（cfgStartupChangelogMode）` | 启动更新说明：summary\|expanded\|hidden。默认 summary | `packages/coding-agent/src/modes/settings.ts:1075` |

### 交互 · 魔法关键词（Magic Keywords）（共 5 条）
> 数法（payload 原文）：交互 · 魔法关键词（Magic Keywords） 共 5 条（数法：settings.ts 1 个总开关 register + MAGIC_KEYWORDS.map 循环内 1 个 register × 4 个关键词）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `magicKeywords.enabled（cfgMagicKeywordsEnabled）` | 启用独立魔法关键词的隐藏通知。默认 true | `packages/coding-agent/src/modes/settings.ts:1105` |
| `magicKeywords.ultrathink（cfgMagicKeyword.ultrathink，循环注册）` | 独立 ultrathink 请求最大自动思考并附隐藏通知。默认 true | `packages/coding-agent/src/modes/settings.ts:1118-1129` |
| `magicKeywords.orchestrate（cfgMagicKeyword.orchestrate，循环注册）` | 独立 orchestrate 附多 agent 编排通知（需 task 工具）。默认 true | `packages/coding-agent/src/modes/settings.ts:1118-1129` |
| `magicKeywords.workflow（cfgMagicKeyword.workflow，循环注册）` | 独立 workflowz 附 eval 工作流通知（需 task+eval）。默认 true | `packages/coding-agent/src/modes/settings.ts:1118-1129` |
| `magicKeywords.jevify（cfgMagicKeyword.jevify，循环注册）` | 独立 jevify 附批量判类通知（需 eval）。默认 true | `packages/coding-agent/src/modes/settings.ts:1118-1129` |

### 交互 · 通知（Notifications & Recap）（共 6 条）
> 数法（payload 原文）：交互 · 通知（Notifications & Recap） 共 6 条（数法：settings.ts 'Notifications' 段 register）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `completion.notify（cfgCompletionNotify）` | agent 完成回合时通知：on\|off。默认 on | `packages/coding-agent/src/modes/settings.ts:1131` |
| `error.notify（cfgErrorNotify）` | agent 出错停止时通知：on\|off。默认 off | `packages/coding-agent/src/modes/settings.ts:1144` |
| `ask.timeout（cfgAskTimeout）` | ask 等多少秒后自动选推荐项；0=禁用。默认 0 | `packages/coding-agent/src/modes/settings.ts:1157` |
| `ask.notify（cfgAskNotify）` | ask 工具等待输入时通知：on\|off。默认 on | `packages/coding-agent/src/modes/settings.ts:1176` |
| `recap.enabled（cfgRecapEnabled）` | 终端空闲后生成简要 LLM 回顾。默认 true | `packages/coding-agent/src/modes/settings.ts:1189` |
| `recap.idleSeconds（cfgRecapIdleSeconds）` | 空闲多少秒后显示回顾。默认 240 | `packages/coding-agent/src/modes/settings.ts:1201` |

## 40. 设置 · 其余 35 个设置域（共 446 条）

### config (model-settings)（共 12 条）
> 数法（payload 原文）：config (model-settings) — 共 12 条 (grep -c 'register({' = 12)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `auth.broker.url` | 远程 omp auth-broker 主机地址；默认 undefined（env OMP_AUTH_BROKER_URL 优先） | `packages/coding-agent/src/config/model-settings.ts:43` |
| `auth.broker.token` | auth-broker 令牌（凭据）；默认 undefined（env OMP_AUTH_BROKER_TOKEN） | `packages/coding-agent/src/config/model-settings.ts:50` |
| `auth.accountPolicies` | 账户策略数组；默认 [] | `packages/coding-agent/src/config/model-settings.ts:58` |
| `enabledModels` | 启用模型白名单（可按路径作用域）；默认 [] | `packages/coding-agent/src/config/model-settings.ts:64` |
| `enabledProviders` | 启用 provider 白名单；默认 [] | `packages/coding-agent/src/config/model-settings.ts:71` |
| `disabledProviders` | 禁用 provider 列表；默认 [] | `packages/coding-agent/src/config/model-settings.ts:78` |
| `modelRoleStorage` | 角色模型保存位置 global\|project；默认 "global" | `packages/coding-agent/src/config/model-settings.ts:85` |
| `modelRoles` | 角色→模型记录；默认 {} | `packages/coding-agent/src/config/model-settings.ts:109` |
| `modelPresets` | 命名模型预设（无面板 UI，/modelpreset 管理）；默认 {} | `packages/coding-agent/src/config/model-settings.ts:113` |
| `modelTags` | 模型标签定义记录；默认 {} | `packages/coding-agent/src/config/model-settings.ts:118` |
| `modelProviderOrder` | provider 轮换顺序；默认 [] | `packages/coding-agent/src/config/model-settings.ts:120` |
| `cycleOrder` | 模型循环顺序；默认 ["smol","default","slow"] | `packages/coding-agent/src/config/model-settings.ts:122` |

### session/settings.ts（共 79 条）
> 数法（payload 原文）：session/settings.ts — 共 79 条 (grep -c 'register({' = 79)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `power.sleepPrevention` | 活跃会话阻止系统睡眠，枚举 off\|idle\|display\|system；默认 "idle" | `packages/coding-agent/src/session/settings.ts:37` |
| `prewalk.enabled` | 强模型规划后首次编辑/写入时切换到 smol 快速模型；默认 false | `packages/coding-agent/src/session/settings.ts:74` |
| `providers.maxInFlightRequests` | 每 provider 并发 LLM 请求上限（记录）；默认 {}（省略=无限） | `packages/coding-agent/src/session/settings.ts:122` |
| `providers.openai-codex.codeMode` | Codex code_mode 模型经 eval 路由 off\|on\|auto；默认 "off" | `packages/coding-agent/src/session/settings.ts:140` |
| `providers.openai-codex.codeModeDirectTools` | Code Mode 附加直连工具；默认 [] | `packages/coding-agent/src/session/settings.ts:154` |
| `images.describeForTextModels` | 无视觉模型收到图片时用视觉模型生成描述；默认 true | `packages/coding-agent/src/session/settings.ts:178` |
| `defaultThinkingLevel` | 推理深度（THINKING_EFFORTS+AUTO）；默认 "high" | `packages/coding-agent/src/session/settings.ts:196` |
| `hideThinkingBlock` | 隐藏助手 thinking 块；默认 false | `packages/coding-agent/src/session/settings.ts:210` |
| `proseOnlyThinking` | 思考摘要省略代码块（替换为省略号）；默认 true | `packages/coding-agent/src/session/settings.ts:222` |
| `omitThinking` | 让上游 provider 完全省略 thinking 摘要；默认 false | `packages/coding-agent/src/session/settings.ts:234` |
| `externalThinking` | 私有草稿本，不展示；禁用受支持的 GPT/Claude/Gemini 推理；默认 false | `packages/coding-agent/src/session/settings.ts:246` |
| `model.loopGuard.enabled` | 流循环检测（env PI_NO_THINKING_LOOP_GUARD=1 关闭）；默认 true | `packages/coding-agent/src/session/settings.ts:259` |
| `model.loopGuard.checkAssistantContent` | 循环守卫同时扫描助手正文；默认 true | `packages/coding-agent/src/session/settings.ts:273` |
| `model.loopGuard.toolCallReminder` | Gemini 连续规划头无工具调用时中断并注入提醒；默认 true | `packages/coding-agent/src/session/settings.ts:285` |
| `model.toolCallLoopGuard.enabled` | 跨轮相同工具调用检测并注入纠正；默认 true | `packages/coding-agent/src/session/settings.ts:298` |
| `model.toolCallLoopGuard.threshold` | 触发纠正的连续相同工具调用次数；默认 5 | `packages/coding-agent/src/session/settings.ts:310` |
| `model.toolCallLoopGuard.exemptTools` | 可重复不触发守卫的工具名；默认 ["wait"] | `packages/coding-agent/src/session/settings.ts:322` |
| `inlineToolDescriptors` | 系统提示内联完整工具描述 auto\|on\|off；默认 "auto"（Gemini 启用） | `packages/coding-agent/src/session/settings.ts:334` |
| `includeModelInPrompt` | 系统提示中带上当前模型 id；默认 true | `packages/coding-agent/src/session/settings.ts:357` |
| `includeWorkspaceTree` | 系统提示渲染工作区目录树（可能破坏提示缓存）；默认 false | `packages/coding-agent/src/session/settings.ts:369` |
| `skillful` | 系统提示列出可用 skills；默认 true | `packages/coding-agent/src/session/settings.ts:382` |
| `personality` | 沟通风格块 default\|friendly\|pragmatic\|none；默认 "default" | `packages/coding-agent/src/session/settings.ts:398` |
| `temperature` | 采样温度（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:430` |
| `topP` | 核采样（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:450` |
| `topK` | top-K 采样（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:470` |
| `minP` | 最小概率阈值（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:489` |
| `presencePenalty` | 存在惩罚（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:507` |
| `repetitionPenalty` | 重复惩罚（-1=provider 默认）；默认 -1 | `packages/coding-agent/src/session/settings.ts:526` |
| `textVerbosity` | OpenAI Responses/Codex 冗长度 low\|medium\|high；默认 "medium" | `packages/coding-agent/src/session/settings.ts:570` |
| `tier.openai` | OpenAI 服务层级（SERVICE_TIER_OPENAI_VALUES）；默认 "none" | `packages/coding-agent/src/session/settings.ts:588` |
| `tier.anthropic` | Anthropic 服务层级；默认 "none" | `packages/coding-agent/src/session/settings.ts:603` |
| `tier.google` | Google 服务层级；默认 "none" | `packages/coding-agent/src/session/settings.ts:618` |
| `tier.subagent` | 子代理服务层级；默认 "inherit" | `packages/coding-agent/src/session/settings.ts:633` |
| `tier.advisor` | advisor 服务层级；默认 "none" | `packages/coding-agent/src/session/settings.ts:648` |
| `retry.enabled` | 启用 API 错误重试；默认 true | `packages/coding-agent/src/session/settings.ts:666` |
| `retry.maxRetries` | 最大重试次数；默认 10 | `packages/coding-agent/src/session/settings.ts:668` |
| `retry.baseDelayMs` | 重试基础延迟（ms）；默认 500 | `packages/coding-agent/src/session/settings.ts:687` |
| `retry.maxDelayMs` | 重试最大等待（ms），0 禁用上限；默认 300000 | `packages/coding-agent/src/session/settings.ts:689` |
| `retry.waitForUsageReset` | 用量耗尽且给出重置时间时睡到重置；默认 false | `packages/coding-agent/src/session/settings.ts:702` |
| `retry.modelFallback` | 允许重试恢复切换到回退模型；默认 true | `packages/coding-agent/src/session/settings.ts:716` |
| `retry.usageAwareFallback` | 用量感知回退（同 provider 账户优先）；默认 false | `packages/coding-agent/src/session/settings.ts:728` |
| `retry.usageReservePct` | 剩余低于此百分比视为接近上限；默认 DEFAULT_USAGE_RESERVE_PCT（常量，pi-ai/auth-storage） | `packages/coding-agent/src/session/settings.ts:741` |
| `retry.usageReservePolicy` | 全部同 provider 账户进入保留边距时 confirm\|auto\|fail-closed；默认 "confirm" | `packages/coding-agent/src/session/settings.ts:762` |
| `retry.fallbackChains` | 角色/模型选择器/provider 通配符→有序回退选择器；默认 {} | `packages/coding-agent/src/session/settings.ts:793` |
| `retry.fallbackRevertPolicy` | 何时回主模型 cooldown-expiry\|never；默认 "cooldown-expiry" | `packages/coding-agent/src/session/settings.ts:806` |
| `providers.anthropic.serverSideFallback` | Claude Fable/Mythos 被安全分类器拦截时服务端回退 Opus；默认 false | `packages/coding-agent/src/session/settings.ts:843` |
| `providers.anthropic.slowMode` | Anthropic 订阅慢速模式 off\|auto（无 /settings UI，/slow 切换）；默认 "off" | `packages/coding-agent/src/session/settings.ts:863` |
| `providers.ollama-cloud.maxConcurrency` | Ollama Cloud 子代理并发上限，0 禁用；默认 3 | `packages/coding-agent/src/session/settings.ts:871` |
| `providers.webSearchTimeoutSeconds` | 每 provider 搜索传输硬超时（秒）；默认 DEFAULT_WEB_SEARCH_TIMEOUT_SECONDS（常量，web/search/types） | `packages/coding-agent/src/session/settings.ts:883` |
| `providers.antigravityEndpoint` | google-antigravity 端点路由 auto\|production\|sandbox；默认 "auto" | `packages/coding-agent/src/session/settings.ts:902` |
| `providers.fireworksTier` | Fireworks 服务路径 standard\|priority；默认 "standard" | `packages/coding-agent/src/session/settings.ts:932` |
| `providers.tinyModelDevice` | 本地 tiny 模型推理后端（env PI_TINY_DEVICE）；默认 TINY_MODEL_DEVICE_DEFAULT（常量，tiny/device） | `packages/coding-agent/src/session/settings.ts:954` |
| `providers.tinyModelDtype` | 本地 tiny 模型量化精度（env PI_TINY_DTYPE）；默认 TINY_MODEL_DTYPE_DEFAULT（常量，tiny/dtype） | `packages/coding-agent/src/session/settings.ts:973` |
| `providers.autoThinkingMaxEffort` | auto 思考分类器可解析的最高 effort xhigh\|max；默认 "xhigh" | `packages/coding-agent/src/session/settings.ts:992` |
| `features.unexpectedStopDetection` | 助手无可见信息停止时自动恢复 none\|mechanical\|smart；默认 "mechanical" | `packages/coding-agent/src/session/settings.ts:1011` |
| `providers.kimiApiFormat` | Kimi Code provider API 格式 auto\|openai\|anthropic；默认 "auto" | `packages/coding-agent/src/session/settings.ts:1038` |
| `providers.openaiWebsockets` | OpenAI Codex WebSocket 策略 auto\|off\|on；默认 "auto" | `packages/coding-agent/src/session/settings.ts:1056` |
| `providers.openaiLiveSteering` | 流式期间输入消息经 Codex WS 实时投递；默认 true | `packages/coding-agent/src/session/settings.ts:1074` |
| `providers.cacheRetention` | 提示缓存保留期 auto\|short\|long\|none；默认 "auto" | `packages/coding-agent/src/session/settings.ts:1087` |
| `providers.cacheWarming` | 缓存过期前重发请求续命 off\|streaming\|idle；默认 "idle" | `packages/coding-agent/src/session/settings.ts:1120` |
| `providers.streamFirstEventTimeoutSeconds` | 等待流首事件秒数（-1=provider/env 默认，0 关闭）；默认 -1 | `packages/coding-agent/src/session/settings.ts:1148` |
| `providers.streamIdleTimeoutSeconds` | 流事件间空闲超时秒数（-1=默认，0 关闭）；默认 -1 | `packages/coding-agent/src/session/settings.ts:1168` |
| `providers.openrouterVariant` | OpenRouter 路由变体后缀 default\|nitro\|floor\|online\|exacto；默认 "default" | `packages/coding-agent/src/session/settings.ts:1188` |
| `providers.fetch` | fetch/read URL 后端优先级；默认 "auto"（native>trafilatura>lynx>parallel>firecrawl>jina） | `packages/coding-agent/src/session/settings.ts:1213` |
| `codexResets.autoRedeem` | 自动花费保存的 Codex 重置 unset\|yes\|no；默认 "unset" | `packages/coding-agent/src/session/settings.ts:1240` |
| `codexResets.minBlockedMinutes` | 自然解除至少这么久才自动兑换；默认 60 | `packages/coding-agent/src/session/settings.ts:1263` |
| `codexResets.keepCredits` | 保留下限以下不自动花费；默认 0 | `packages/coding-agent/src/session/settings.ts:1276` |
| `codexResets.salvageHorizonHours` | 即将过期时抢救花费的时窗；默认 12 | `packages/coding-agent/src/session/settings.ts:1289` |
| `claudeResets.autoRedeem` | 自动花费 Claude Cedar/Juniper 重置 unset\|yes\|no；默认 "unset" | `packages/coding-agent/src/session/settings.ts:1314` |
| `claudeResets.minBlockedMinutes` | 自然解除至少这么久才自动兑换；默认 60 | `packages/coding-agent/src/session/settings.ts:1337` |
| `claudeResets.keepCredits` | 保留下限以下不自动花费；默认 0 | `packages/coding-agent/src/session/settings.ts:1350` |
| `claudeResets.salvageHorizonHours` | 即将过期时抢救花费的时窗；默认 12 | `packages/coding-agent/src/session/settings.ts:1363` |
| `provider.appendOnlyContext` | 仅追加上下文以最大化前缀缓存命中 auto\|on\|off；默认 "auto" | `packages/coding-agent/src/session/settings.ts:1384` |
| `thinkingBudgets.minimal` | minimal 思考级别 token 预算；默认 1024 | `packages/coding-agent/src/session/settings.ts:1403` |
| `thinkingBudgets.low` | low 思考级别 token 预算；默认 2048 | `packages/coding-agent/src/session/settings.ts:1405` |
| `thinkingBudgets.medium` | medium 思考级别 token 预算；默认 8192 | `packages/coding-agent/src/session/settings.ts:1407` |
| `thinkingBudgets.high` | high 思考级别 token 预算；默认 16384 | `packages/coding-agent/src/session/settings.ts:1409` |
| `thinkingBudgets.xhigh` | xhigh 思考级别 token 预算；默认 32768 | `packages/coding-agent/src/session/settings.ts:1411` |
| `thinkingBudgets.max` | max 思考级别 token 预算；默认 32768 | `packages/coding-agent/src/session/settings.ts:1413` |

### session/context-settings.ts（共 28 条）
> 数法（payload 原文）：session/context-settings.ts — 共 28 条 (grep -c 'register({' = 28)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `workspace.additionalDirectories` | 附加工作区根目录（多根工作区，/add-dir 管理）；默认 [] | `packages/coding-agent/src/session/context-settings.ts:7` |
| `contextPromotion.enabled` | 上下文溢出时提升到更大窗口模型而非压缩；默认 false | `packages/coding-agent/src/session/context-settings.ts:25` |
| `extendedContext` | 使用更大上下文窗口（可能高价）；默认 false | `packages/coding-agent/src/session/context-settings.ts:40` |
| `compaction.enabled` | 上下文过大时自动压缩；默认 true | `packages/coding-agent/src/session/context-settings.ts:54` |
| `compaction.experimentalContextManagement` | 笔记式持久上下文窗口（实验）；默认 false | `packages/coding-agent/src/session/context-settings.ts:66` |
| `compaction.midTurnEnabled` | 轮中安全边界检查压缩阈值；默认 true | `packages/coding-agent/src/session/context-settings.ts:78` |
| `compaction.methodOrder` | 自动维护的偏好回退顺序；默认 [...DEFAULT_COMPACTION_METHOD_ORDER] | `packages/coding-agent/src/session/context-settings.ts:91` |
| `compaction.thresholdPercent` | 压缩百分比阈值（-1=Default 旧式 reserve）；默认 -1 | `packages/coding-agent/src/session/context-settings.ts:106` |
| `compaction.thresholdTokens` | 固定 token 压缩阈值（覆盖百分比）；默认 -1 | `packages/coding-agent/src/session/context-settings.ts:133` |
| `compaction.handoffSaveToDisk` | 将生成的手递文档保存为 markdown；默认 false | `packages/coding-agent/src/session/context-settings.ts:155` |
| `compaction.remoteStreamingV2Enabled` | 兼容模型使用 Responses 流式压缩；默认 true | `packages/coding-agent/src/session/context-settings.ts:167` |
| `compaction.asyncEnabled` | 接近阈值时后台预摘要，跨阈值时拼接；默认 true | `packages/coding-agent/src/session/context-settings.ts:179` |
| `compaction.reserveTokens` | 上下文保留 token；默认 undefined（未设=用户未选择，可切换比例保留） | `packages/coding-agent/src/session/context-settings.ts:196` |
| `compaction.keepRecentTokens` | 压缩后保留的近期 token；默认 20000 | `packages/coding-agent/src/session/context-settings.ts:202` |
| `compaction.autoContinue` | 压缩后自动继续；默认 true | `packages/coding-agent/src/session/context-settings.ts:208` |
| `compaction.remoteEndpoint` | 远程压缩端点；默认 undefined | `packages/coding-agent/src/session/context-settings.ts:210` |
| `compaction.v2RetainedMessageBudget` | V2 保留消息 token 预算；默认 64000 | `packages/coding-agent/src/session/context-settings.ts:216` |
| `compaction.idleEnabled` | 空闲且超阈值时压缩；默认 false | `packages/coding-agent/src/session/context-settings.ts:223` |
| `compaction.idleThresholdTokens` | 空闲压缩触发的 token 阈值；默认 200000 | `packages/coding-agent/src/session/context-settings.ts:235` |
| `compaction.idleTimeoutSeconds` | 空闲多久后压缩（秒）；默认 300 | `packages/coding-agent/src/session/context-settings.ts:258` |
| `compaction.supersedeReads` | 同文件重读时清理旧 read 结果；默认 true | `packages/coding-agent/src/session/context-settings.ts:278` |
| `compaction.dropUseless` | 清理被标记无用的工具结果；默认 true | `packages/coding-agent/src/session/context-settings.ts:290` |
| `snapcompact.systemPrompt` | 实验：系统提示文本渲染为 PNG 附件 none\|agents-md\|all；默认 "none" | `packages/coding-agent/src/session/context-settings.ts:330` |
| `snapcompact.toolResults` | 实验：大历史工具结果渲染为 PNG；默认 false | `packages/coding-agent/src/session/context-settings.ts:357` |
| `tools.format` | 工具暴露方式 auto\|native\|glm\|hermes\|kimi\|xml\|anthropic\|deepseek\|harmony\|qwen3\|gemini\|gemma\|minimax；默认 "auto" | `packages/coding-agent/src/session/context-settings.ts:370` |
| `snapcompact.shape` | snapcompact 字形/版式 auto\|SHAPE_VARIANT_NAMES；默认 "auto" | `packages/coding-agent/src/session/context-settings.ts:417` |
| `branchSummary.enabled` | 离开分支时提示摘要；默认 false | `packages/coding-agent/src/session/context-settings.ts:527` |
| `branchSummary.reserveTokens` | 分支摘要保留 token；默认 16384 | `packages/coding-agent/src/session/context-settings.ts:539` |

### telemetry-settings.ts（共 1 条）
> 数法（payload 原文）：telemetry-settings.ts — 共 1 条 (grep -c 'register({' = 1)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `telemetry.otlpExportEnabled` | 允许经 OTEL_* 端点导出 traces/logs/metrics（下次启动生效）；默认 true | `packages/coding-agent/src/telemetry-settings.ts:8` |

### advisor/settings.ts（共 7 条）
> 数法（payload 原文）：advisor/settings.ts — 共 7 条 (grep -c 'register({' = 7)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `advisor.enabled` | 配第二模型（advisor 角色）被动审查每轮并注入笔记；默认 false | `packages/coding-agent/src/advisor/settings.ts:11` |
| `advisor.syncBacklog` | 暂停主代理直到 advisor 积压低于阈值 off\|数值\|strict；默认 "off"（取值 ADVISOR_SYNC_BACKLOG_MODES） | `packages/coding-agent/src/advisor/settings.ts:25` |
| `advisor.immuneTurns` | 中断后多少主轮内以非中断方式处理 concern/blocker；默认 3 | `packages/coding-agent/src/advisor/settings.ts:41` |
| `advisor.reviewMode` | 无 WATCHDOG 时的审查节奏 turn\|agent-end；默认 "turn"（取值 ADVISOR_REVIEW_MODES） | `packages/coding-agent/src/advisor/settings.ts:64` |
| `advisor.reviewInterval` | 每 Nth 次合格更新审查一次；默认 1 | `packages/coding-agent/src/advisor/settings.ts:84` |
| `advisor.maxNotesPerUpdate` | 每次 advisor 更新接受的非阻塞建议笔记上限；默认 ADVISOR_DEFAULT_BUDGET_PER_UPDATE（常量，advisor/emission-guard） | `packages/coding-agent/src/advisor/settings.ts:106` |
| `advisor.evictStaleResults` | 每次审查前替换旧审查的 read/grep/glob 输出为占位；默认 true | `packages/coding-agent/src/advisor/settings.ts:128` |

### memory-backend/settings.ts（共 1 条）
> 数法（payload 原文）：memory-backend/settings.ts — 共 1 条 (grep -c 'register({' = 1)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `memory.backend` | 记忆后端 off\|local\|hindsight\|mnemopi\|sharpshooter；默认 "off" | `packages/coding-agent/src/memory-backend/settings.ts:12` |

### memories/settings.ts（共 16 条）
> 数法（payload 原文）：memories/settings.ts — 共 16 条 (grep -c 'register({' = 16)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `memories.enabled` | 遗留本地记忆开关（仅迁移用，隐藏 UI，改用 memory.backend）；默认 false | `packages/coding-agent/src/memories/settings.ts:10` |
| `memories.maxRolloutsPerStartup` | 每次启动处理的最大 rollout 数；默认 64 | `packages/coding-agent/src/memories/settings.ts:17` |
| `memories.maxRolloutAgeDays` | rollout 最大年龄（天）；默认 30 | `packages/coding-agent/src/memories/settings.ts:23` |
| `memories.minRolloutIdleHours` | rollout 最小空闲小时数；默认 12 | `packages/coding-agent/src/memories/settings.ts:25` |
| `memories.threadScanLimit` | 线程扫描上限；默认 300 | `packages/coding-agent/src/memories/settings.ts:31` |
| `memories.maxRawMemoriesForGlobal` | 全局原始记忆上限；默认 200 | `packages/coding-agent/src/memories/settings.ts:33` |
| `memories.stage1Concurrency` | 阶段1并发；默认 8 | `packages/coding-agent/src/memories/settings.ts:39` |
| `memories.stage1LeaseSeconds` | 阶段1租约秒数；默认 120 | `packages/coding-agent/src/memories/settings.ts:41` |
| `memories.stage1RetryDelaySeconds` | 阶段1重试延迟秒数；默认 120 | `packages/coding-agent/src/memories/settings.ts:47` |
| `memories.phase2LeaseSeconds` | 阶段2租约秒数；默认 180 | `packages/coding-agent/src/memories/settings.ts:53` |
| `memories.phase2RetryDelaySeconds` | 阶段2重试延迟秒数；默认 180 | `packages/coding-agent/src/memories/settings.ts:59` |
| `memories.phase2HeartbeatSeconds` | 阶段2心跳秒数；默认 30 | `packages/coding-agent/src/memories/settings.ts:65` |
| `memories.rolloutPayloadPercent` | rollout 载荷比例；默认 0.7 | `packages/coding-agent/src/memories/settings.ts:71` |
| `memories.phase1InputTokenLimit` | 阶段1输入 token 上限；默认 4000 | `packages/coding-agent/src/memories/settings.ts:77` |
| `memories.fallbackTokenLimit` | 回退 token 上限；默认 16000 | `packages/coding-agent/src/memories/settings.ts:83` |
| `memories.summaryInjectionTokenLimit` | 摘要注入 token 上限；默认 5000 | `packages/coding-agent/src/memories/settings.ts:89` |

### sharpshooter/settings.ts（共 3 条）
> 数法（payload 原文）：sharpshooter/settings.ts — 共 3 条 (grep -c 'register({' = 3)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `sharpshooter.model` | 抽取/整合所用模型选择器，空=smol 角色；默认 undefined | `packages/coding-agent/src/sharpshooter/settings.ts:7` |
| `sharpshooter.intervalMinutes` | 后台整合间隔（分钟）；默认 5 | `packages/coding-agent/src/sharpshooter/settings.ts:19` |
| `sharpshooter.injectionTokenLimit` | 注入 token 上限；默认 15000 | `packages/coding-agent/src/sharpshooter/settings.ts:25` |

### autolearn/settings.ts（共 3 条）
> 数法（payload 原文）：autolearn/settings.ts — 共 3 条 (grep -c 'register({' = 3)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `autolearn.enabled` | 停止后 nudge 代理把经验沉淀为记忆/managed skills（实验）；默认 false | `packages/coding-agent/src/autolearn/settings.ts:10` |
| `autolearn.autoContinue` | 停止时自动跑一次私有采集轮（耗额外 token）；默认 false | `packages/coding-agent/src/autolearn/settings.ts:23` |
| `autolearn.minToolCalls` | 触发 autolearn 的最小工具调用数（仅配置文件）；默认 5 | `packages/coding-agent/src/autolearn/settings.ts:38` |

### mnemopi/settings.ts（共 23 条）
> 数法（payload 原文）：mnemopi/settings.ts — 共 23 条 (full read; grep context truncated tail)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `mnemopi.dbPath` | SQLite DB 路径，空=默认记忆目录；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:9` |
| `mnemopi.bank` | 共享 bank 基础名；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:22` |
| `mnemopi.scoping` | global\|per-project\|per-project-tagged；默认 "per-project" | `packages/coding-agent/src/mnemopi/settings.ts:35` |
| `mnemopi.embeddingVariant` | en\|multilingual 嵌入模型族（切换会重建嵌入）；默认 "en" | `packages/coding-agent/src/mnemopi/settings.ts:75` |
| `mnemopi.autoRecall` | 每会话首轮召回本地记忆；默认 true | `packages/coding-agent/src/mnemopi/settings.ts:102` |
| `mnemopi.autoRetain` | 把已完成轮次存入本地记忆；默认 true | `packages/coding-agent/src/mnemopi/settings.ts:115` |
| `mnemopi.polyphonicRecall` | 图/事实/向量/时间多声部融合召回；默认 false | `packages/coding-agent/src/mnemopi/settings.ts:128` |
| `mnemopi.enhancedRecall` | 缓存重复/相似查询的召回结果；默认 false | `packages/coding-agent/src/mnemopi/settings.ts:142` |
| `mnemopi.proactiveLinking` | 新记忆入库时接入情节图并链接相关实体；默认 false | `packages/coding-agent/src/mnemopi/settings.ts:156` |
| `mnemopi.noEmbeddings` | 强制纯 FTS 召回（不用向量）；默认 false | `packages/coding-agent/src/mnemopi/settings.ts:170` |
| `mnemopi.embeddingModel` | 显式嵌入模型 id（覆盖 variant，env MNEMOPI_EMBEDDING_MODEL）；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:183` |
| `mnemopi.embeddingApiUrl` | OpenAI 兼容嵌入端点；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:199` |
| `mnemopi.embeddingApiKey` | 嵌入 API key（凭据）；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:212` |
| `mnemopi.llmMode` | none\|smol\|remote LLM 抽取模式；默认 "smol" | `packages/coding-agent/src/mnemopi/settings.ts:226` |
| `mnemopi.llmBaseUrl` | 远程模式 LLM 端点；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:250` |
| `mnemopi.llmApiKey` | 远程模式 LLM API key（凭据）；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:263` |
| `mnemopi.llmModel` | 远程模式 LLM 模型名；默认 undefined | `packages/coding-agent/src/mnemopi/settings.ts:277` |
| `mnemopi.retainEveryNTurns` | 每 N 轮 retain 一次；默认 4 | `packages/coding-agent/src/mnemopi/settings.ts:290` |
| `mnemopi.recallLimit` | 召回条数上限；默认 8 | `packages/coding-agent/src/mnemopi/settings.ts:292` |
| `mnemopi.recallContextTurns` | 召回上下文轮数；默认 3 | `packages/coding-agent/src/mnemopi/settings.ts:294` |
| `mnemopi.recallMaxQueryChars` | 召回查询最大字符数；默认 4000 | `packages/coding-agent/src/mnemopi/settings.ts:296` |
| `mnemopi.injectionTokenLimit` | 注入 token 上限；默认 5000 | `packages/coding-agent/src/mnemopi/settings.ts:302` |
| `mnemopi.debug` | Mnemopi 调试日志；默认 false | `packages/coding-agent/src/mnemopi/settings.ts:307` |

### hindsight/settings.ts（共 26 条）
> 数法（payload 原文）：hindsight/settings.ts — 共 26 条 (full read; grep context truncated at line 220)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `hindsight.apiUrl` | Hindsight 服务 URL（env HINDSIGHT_API_URL）；默认 "http://localhost:8888" | `packages/coding-agent/src/hindsight/settings.ts:16` |
| `hindsight.apiToken` | Bearer token（凭据，env HINDSIGHT_API_TOKEN）；默认 undefined | `packages/coding-agent/src/hindsight/settings.ts:30` |
| `hindsight.bankId` | 记忆 bank 标识（默认项目名，env HINDSIGHT_BANK_ID）；默认 undefined | `packages/coding-agent/src/hindsight/settings.ts:45` |
| `hindsight.bankIdPrefix` | bank id 前缀；默认 undefined | `packages/coding-agent/src/hindsight/settings.ts:59` |
| `hindsight.scoping` | global\|per-project\|per-project-tagged（env HINDSIGHT_SCOPING）；默认 "per-project-tagged" | `packages/coding-agent/src/hindsight/settings.ts:61` |
| `hindsight.bankMission` | bank 使命（env HINDSIGHT_BANK_MISSION）；默认 undefined | `packages/coding-agent/src/hindsight/settings.ts:95` |
| `hindsight.retainMission` | retain 使命；默认 undefined | `packages/coding-agent/src/hindsight/settings.ts:102` |
| `hindsight.autoRecall` | 每会话首轮召回（env HINDSIGHT_AUTO_RECALL）；默认 true | `packages/coding-agent/src/hindsight/settings.ts:108` |
| `hindsight.autoRetain` | 每 N 轮及边界 retain（env HINDSIGHT_AUTO_RETAIN）；默认 true | `packages/coding-agent/src/hindsight/settings.ts:122` |
| `hindsight.retainMode` | full-session\|last-turn（env HINDSIGHT_RETAIN_MODE）；默认 "full-session" | `packages/coding-agent/src/hindsight/settings.ts:136` |
| `hindsight.retainEveryNTurns` | 每 N 轮 retain（env HINDSIGHT_RETAIN_EVERY_N_TURNS）；默认 3 | `packages/coding-agent/src/hindsight/settings.ts:159` |
| `hindsight.retainOverlapTurns` | retain 重叠轮数；默认 2 | `packages/coding-agent/src/hindsight/settings.ts:166` |
| `hindsight.retainContext` | retain 上下文标签；默认 "omp" | `packages/coding-agent/src/hindsight/settings.ts:172` |
| `hindsight.recallBudget` | 召回预算 low\|mid\|high（env HINDSIGHT_RECALL_BUDGET）；默认 "mid" | `packages/coding-agent/src/hindsight/settings.ts:174` |
| `hindsight.recallMaxTokens` | 召回最大 token（env HINDSIGHT_RECALL_MAX_TOKENS）；默认 1024 | `packages/coding-agent/src/hindsight/settings.ts:182` |
| `hindsight.recallContextTurns` | 召回上下文轮数（env HINDSIGHT_RECALL_CONTEXT_TURNS）；默认 1 | `packages/coding-agent/src/hindsight/settings.ts:189` |
| `hindsight.recallMaxQueryChars` | 召回查询最大字符（env HINDSIGHT_RECALL_MAX_QUERY_CHARS）；默认 800 | `packages/coding-agent/src/hindsight/settings.ts:196` |
| `hindsight.recallTypes` | 召回类型数组；默认 ["world","experience"] | `packages/coding-agent/src/hindsight/settings.ts:203` |
| `hindsight.debug` | 调试日志（env HINDSIGHT_DEBUG）；默认 false | `packages/coding-agent/src/hindsight/settings.ts:209` |
| `hindsight.requestTimeoutMs` | 请求超时 ms（env HINDSIGHT_REQUEST_TIMEOUT_MS）；默认 30000 | `packages/coding-agent/src/hindsight/settings.ts:216` |
| `hindsight.reflectTimeoutMs` | reflect 超时 ms（env HINDSIGHT_REFLECT_TIMEOUT_MS）；默认 120000 | `packages/coding-agent/src/hindsight/settings.ts:229` |
| `hindsight.recallTimeoutMs` | recall 超时 ms（env HINDSIGHT_RECALL_TIMEOUT_MS）；默认 30000 | `packages/coding-agent/src/hindsight/settings.ts:237` |
| `hindsight.retainTimeoutMs` | retain 超时 ms（env HINDSIGHT_RETAIN_TIMEOUT_MS）；默认 60000 | `packages/coding-agent/src/hindsight/settings.ts:245` |
| `hindsight.mentalModelsEnabled` | 启动时读取 curated reflect 摘要（mental models）；默认 true | `packages/coding-agent/src/hindsight/settings.ts:253` |
| `hindsight.mentalModelAutoSeed` | 会话开始时创建缺失的内置 mental models；默认 true | `packages/coding-agent/src/hindsight/settings.ts:267` |
| `hindsight.mentalModelMaxRenderChars` | mental model 渲染最大字符；默认 16000 | `packages/coding-agent/src/hindsight/settings.ts:273` |

### export/ttsr-settings.ts（共 8 条）
> 数法（payload 原文）：export/ttsr-settings.ts — 共 8 条 (grep -c 'register({' = 8)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ttsr.enabled` | 输出匹配规则时中途打断代理（Time-Traveling Stream Rules）；默认 true | `packages/coding-agent/src/export/ttsr-settings.ts:8` |
| `ttsr.judge` | judge 角色逐条判定 question 规则 auto\|on\|off；默认 "auto" | `packages/coding-agent/src/export/ttsr-settings.ts:20` |
| `ttsr.contextMode` | 触发时如何处理部分输出 discard\|keep；默认 "discard" | `packages/coding-agent/src/export/ttsr-settings.ts:43` |
| `ttsr.interruptMode` | 何时中途打断 never\|prose-only\|tool-only\|always；默认 "always" | `packages/coding-agent/src/export/ttsr-settings.ts:56` |
| `ttsr.repeatMode` | 规则重复 once\|after-gap；默认 "once" | `packages/coding-agent/src/export/ttsr-settings.ts:75` |
| `ttsr.repeatGap` | 规则再次触发前的消息间隔；默认 10 | `packages/coding-agent/src/export/ttsr-settings.ts:88` |
| `ttsr.builtinRules` | 加载内置规则；默认 true | `packages/coding-agent/src/export/ttsr-settings.ts:107` |
| `ttsr.disabledRules` | 完全忽略的规则名（含内置）；默认 [] | `packages/coding-agent/src/export/ttsr-settings.ts:119` |

### edit/settings.ts（共 10 条）
> 数法（payload 原文）：edit/settings.ts — 共 10 条 (grep -c 'register({' = 10)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `edit.mode` | 编辑工具变体 apply_patch\|hashline\|patch\|replace\|sloppy（env PI_EDIT_VARIANT）；默认 "hashline" | `packages/coding-agent/src/edit/settings.ts:36` |
| `edit.modelVariants` | 按模型选择器子串→编辑模式（仅配置文件）；默认 {} | `packages/coding-agent/src/edit/settings.ts:52` |
| `edit.fuzzyMatch` | 接受高置信模糊匹配（空白差异，env PI_EDIT_FUZZY）；默认 true | `packages/coding-agent/src/edit/settings.ts:68` |
| `edit.fuzzyThreshold` | 模糊匹配相似度阈值 0-1（env PI_EDIT_FUZZY_THRESHOLD）；默认 0.95 | `packages/coding-agent/src/edit/settings.ts:81` |
| `edit.streamingAbort` | 补丁预览失败时中止流式编辑调用；默认 false | `packages/coding-agent/src/edit/settings.ts:106` |
| `edit.recoverInlineEdits` | 把模型以纯文本输出的编辑载荷转为编辑工具调用执行；默认 true | `packages/coding-agent/src/edit/settings.ts:118` |
| `edit.blockAutoGenerated` | 阻止编辑疑似自动生成的文件（protoc/sqlc/swagger 等）；默认 true | `packages/coding-agent/src/edit/settings.ts:130` |
| `edit.enforceSeenLines` | 拒绝锚定在未完整展示行上的编辑；默认 true | `packages/coding-agent/src/edit/settings.ts:142` |
| `edit.blackbox.enabled` | 编辑引入 AST 解析失败时记录完整前后源码；默认 false | `packages/coding-agent/src/edit/settings.ts:154` |
| `edit.autoRepair.enabled` | 编辑破坏 AST 解析时让 smol 模型修复破损区（重解析校验）；默认 false | `packages/coding-agent/src/edit/settings.ts:166` |

### tools/settings.ts（共 65 条）
> 数法（payload 原文）：tools/settings.ts — 共 65 条 (grep -c 'register({' = 65)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tools.artifactSpillThreshold` | 输出超过此大小（KB）存为 artifact，尾部内联；默认 50 | `packages/coding-agent/src/tools/settings.ts:12` |
| `tools.artifactTailBytes` | 内联保留的尾部大小（KB）；默认 20 | `packages/coding-agent/src/tools/settings.ts:38` |
| `tools.artifactHeadBytes` | 内联保留的头部大小（KB，0 禁用=仅尾部）；默认 20 | `packages/coding-agent/src/tools/settings.ts:60` |
| `tools.outputMaxColumns` | 流式工具输出每行字节上限（0 禁用）；默认 768 | `packages/coding-agent/src/tools/settings.ts:84` |
| `tools.artifactTailLines` | 内联尾部最大行数；默认 500 | `packages/coding-agent/src/tools/settings.ts:106` |
| `tools.artifactMaxBytes` | artifact 文件大小上限 MB（0 无限）；默认 16 | `packages/coding-agent/src/tools/settings.ts:127` |
| `readLineNumbers` | read 输出默认加行号；默认 false | `packages/coding-agent/src/tools/settings.ts:148` |
| `read.defaultLimit` | read 无 limit 时默认行数；默认 300 | `packages/coding-agent/src/tools/settings.ts:160` |
| `read.renderMarkdown` | read Markdown 结果渲染为终端 Markdown 预览；默认 false | `packages/coding-agent/src/tools/settings.ts:179` |
| `read.summarize.enabled` | 无显式选择器时返回结构摘要；默认 true | `packages/coding-agent/src/tools/settings.ts:191` |
| `read.summarize.prose` | Markdown/纯文本也返回结构摘要；默认 false | `packages/coding-agent/src/tools/settings.ts:203` |
| `read.summarize.minBodyLines` | 折叠多行体/字面量前的最小长度；默认 4 | `packages/coding-agent/src/tools/settings.ts:215` |
| `read.summarize.minCommentLines` | 折叠多行块注释前的最小长度；默认 6 | `packages/coding-agent/src/tools/settings.ts:227` |
| `read.summarize.minTotalLines` | 总行数更少的文件逐字读取；默认 100 | `packages/coding-agent/src/tools/settings.ts:239` |
| `read.summarize.unfoldUntil` | BFS 展开至至少这么多可见行（0 仅最外层折叠）；默认 50 | `packages/coding-agent/src/tools/settings.ts:251` |
| `read.summarize.unfoldLimit` | 摘要展开硬上限；默认 100 | `packages/coding-agent/src/tools/settings.ts:264` |
| `read.toolResultPreview` | read 结果在转录中内联渲染；默认 false | `packages/coding-agent/src/tools/settings.ts:277` |
| `tools.approval` | 每工具审批策略 allow\|prompt\|deny；默认 {} | `packages/coding-agent/src/tools/settings.ts:294` |
| `tools.approvalMode` | 默认工具审批 always-ask\|write\|yolo；默认 "yolo" | `packages/coding-agent/src/tools/settings.ts:311` |
| `todo.enabled` | 启用 todo 工具；默认 true | `packages/coding-agent/src/tools/settings.ts:347` |
| `todo.reminders` | 停止前提醒代理完成 todo；默认 true | `packages/coding-agent/src/tools/settings.ts:359` |
| `todo.remindersMax` | 放弃前的最大 todo 提醒次数；默认 3 | `packages/coding-agent/src/tools/settings.ts:371` |
| `todo.eager` | 首条消息后推动自动创建 todo 的强度 default\|preferred\|always；默认 "default" | `packages/coding-agent/src/tools/settings.ts:389` |
| `tasks.todoClearDelay` | 完成/放弃 todo 从控件移除的延迟秒（-1 永不）；默认 60 | `packages/coding-agent/src/tools/settings.ts:411` |
| `glob.enabled` | 启用 glob 工具；默认 true | `packages/coding-agent/src/tools/settings.ts:433` |
| `grep.enabled` | 启用 grep 工具；默认 true | `packages/coding-agent/src/tools/settings.ts:445` |
| `grep.contextBefore` | 每个匹配前的上下文行数；默认 1 | `packages/coding-agent/src/tools/settings.ts:457` |
| `grep.contextAfter` | 每个匹配后的上下文行数；默认 3 | `packages/coding-agent/src/tools/settings.ts:476` |
| `astGrep.enabled` | 启用 ast_grep 结构搜索；默认 false | `packages/coding-agent/src/tools/settings.ts:496` |
| `astEdit.enabled` | 启用 ast_edit 结构改写；默认 true | `packages/coding-agent/src/tools/settings.ts:508` |
| `find.enabled` | 语义化 find 工具 auto\|on\|off（依赖 judge 角色）；默认 "auto" | `packages/coding-agent/src/tools/settings.ts:520` |
| `debug.enabled` | 启用 DAP 调试工具；默认 true | `packages/coding-agent/src/tools/settings.ts:545` |
| `launch.enabled` | 启用命名 bash 服务与 proc:// 监管；默认 true | `packages/coding-agent/src/tools/settings.ts:557` |
| `speechgen.enabled` | 启用 tts 语音文件合成工具（Kokoro/xAI）；默认 false | `packages/coding-agent/src/tools/settings.ts:569` |
| `generate_image.enabled` | 启用 generate_image 工具；默认 false | `packages/coding-agent/src/tools/settings.ts:581` |
| `computer.enabled` | 启用桌面 eval prelude（截屏/输入/无障碍）；默认 false | `packages/coding-agent/src/tools/settings.ts:594` |
| `ratchet.enabled` | 启用 ratchet eval/hillclimb prelude；默认 false | `packages/coding-agent/src/tools/settings.ts:606` |
| `computer.display` | 合成全部显示或指定原生 display id；默认 "all" | `packages/coding-agent/src/tools/settings.ts:618` |
| `computer.maxWidth` | 合成截图最大宽度 px；默认 3840 | `packages/coding-agent/src/tools/settings.ts:630` |
| `computer.maxHeight` | 合成截图最大高度 px；默认 2400 | `packages/coding-agent/src/tools/settings.ts:642` |
| `images.questionTimeoutMs` | read ?q= 图片问题视觉调用超时 ms（0 禁用）；默认 300000 | `packages/coding-agent/src/tools/settings.ts:654` |
| `checkpoint.enabled` | 启用 checkpoint/rewind 工具；默认 false | `packages/coding-agent/src/tools/settings.ts:674` |
| `fetch.enabled` | 允许 read 抓取处理 URL；默认 true | `packages/coding-agent/src/tools/settings.ts:687` |
| `vault.enabled` | 启用 vault:// Obsidian 内部 URL；默认 false | `packages/coding-agent/src/tools/settings.ts:699` |
| `github.enabled` | 启用 github 工具（op 派发）；默认 false | `packages/coding-agent/src/tools/settings.ts:712` |
| `github.cache.enabled` | 缓存渲染的 issue/PR 视图；默认 true | `packages/coding-agent/src/tools/settings.ts:725` |
| `github.cache.softTtlSec` | 软 TTL 内直接返回缓存（秒）；默认 300 | `packages/coding-agent/src/tools/settings.ts:737` |
| `github.cache.hardTtlSec` | 超硬 TTL 丢弃缓存（秒）；默认 604800 | `packages/coding-agent/src/tools/settings.ts:749` |
| `web_search.enabled` | 启用 web_search 工具；默认 true | `packages/coding-agent/src/tools/settings.ts:762` |
| `security.enabled` | 启用安全扫描规划/执行与 security:// 资源；默认 false | `packages/coding-agent/src/tools/settings.ts:774` |
| `ask.enabled` | 启用交互式提问工具；默认 true | `packages/coding-agent/src/tools/settings.ts:787` |
| `tools.intentTracing` | 执行前让代理描述每次工具调用的意图（env PI_INTENT_TRACING）；默认 true | `packages/coding-agent/src/tools/settings.ts:800` |
| `tools.abortOnFabricatedResult` | 带内工具调用时模型伪造工具结果即停止；默认 true | `packages/coding-agent/src/tools/settings.ts:813` |
| `tools.speculativeExecution.enabled` | 启用实验性投机执行（已验证本地读取首片）；默认 false | `packages/coding-agent/src/tools/settings.ts:826` |
| `tools.speculativeExecution.maxInFlight` | 投机执行并发上限；默认 2 | `packages/coding-agent/src/tools/settings.ts:839` |
| `tools.maxTimeout` | 代理可为任意工具设置的最大超时秒（0 无限）；默认 0 | `packages/coding-agent/src/tools/settings.ts:857` |
| `async.enabled` | 启用异步 bash 与后台任务执行（protocolDefault rpc）；默认 true | `packages/coding-agent/src/tools/settings.ts:879` |
| `async.maxJobs` | 最大异步作业数（protocolDefault rpc）；默认 100 | `packages/coding-agent/src/tools/settings.ts:892` |
| `tools.xdev` | 把少用工具挂到 xd:// 设备 URL；默认 true | `packages/coding-agent/src/tools/settings.ts:899` |
| `tools.xdevDocs` | 哪些挂载设备文档内联 prompt inline\|builtins\|catalog；默认 "catalog" | `packages/coding-agent/src/tools/settings.ts:912` |
| `tools.xdevInlineDevices` | Built-ins Only 时按 glob 内联的动态设备名；默认 [] | `packages/coding-agent/src/tools/settings.ts:935` |
| `dev.autoqa` | 自动工具问题上报（env PI_AUTO_QA，首次询问同意）；默认 true | `packages/coding-agent/src/tools/settings.ts:948` |
| `dev.autoqaPush.endpoint` | 接收 Auto QA JSON 报告的完整 URL；默认 "https://qa.omp.sh/v1/grievances" | `packages/coding-agent/src/tools/settings.ts:962` |
| `dev.autoqaPush.token` | Auto QA push 令牌（凭据）；默认 undefined | `packages/coding-agent/src/tools/settings.ts:974` |
| `dev.autoqaConsent` | 分享 grievances 的同意状态 unset\|granted\|denied；默认 "unset" | `packages/coding-agent/src/tools/settings.ts:994` |

### lsp/settings.ts（共 7 条）
> 数法（payload 原文）：lsp/settings.ts — 共 7 条 (grep -c 'register({' = 7)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `lsp.enabled` | 启用 lsp 代码智能工具；默认 true | `packages/coding-agent/src/lsp/settings.ts:8` |
| `lsp.lazy` | 首次使用时才启动语言服务器；默认 true | `packages/coding-agent/src/lsp/settings.ts:20` |
| `lsp.shared` | 经 daemon broker 跨实例共享语言服务器；默认 true | `packages/coding-agent/src/lsp/settings.ts:33` |
| `lsp.formatOnWrite` | 写文件后经 LSP 自动格式化；默认 false | `packages/coding-agent/src/lsp/settings.ts:46` |
| `lsp.diagnosticsOnWrite` | 写文件后返回 LSP 诊断；默认 true | `packages/coding-agent/src/lsp/settings.ts:58` |
| `lsp.diagnosticsOnEdit` | 编辑后返回 LSP 诊断；默认 false | `packages/coding-agent/src/lsp/settings.ts:70` |
| `lsp.diagnosticsDeduplicate` | 抑制已展示的编辑后诊断，只给新增/变化；默认 true | `packages/coding-agent/src/lsp/settings.ts:82` |

### exec/settings.ts（共 17 条）
> 数法（payload 原文）：exec/settings.ts — 共 17 条 (grep -c 'register({' = 17)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `shellPath` | 自定义 shell 可执行路径；默认 undefined | `packages/coding-agent/src/exec/settings.ts:80` |
| `bash.enabled` | 启用 bash 工具；默认 true | `packages/coding-agent/src/exec/settings.ts:82` |
| `bash.allowCompoundCommands` | 逐条评估字面 && 链；默认 false | `packages/coding-agent/src/exec/settings.ts:94` |
| `bash.autoBackground.enabled` | 自动后台化长时间 bash 命令（protocolDefault rpc）；默认 true | `packages/coding-agent/src/exec/settings.ts:107` |
| `bash.patterns` | 有序 bash 命令审批规则；默认 [] | `packages/coding-agent/src/exec/settings.ts:120` |
| `bashInterceptor.enabled` | 拦截已有专用工具的 shell 命令；默认 false | `packages/coding-agent/src/exec/settings.ts:134` |
| `bashInterceptor.patterns` | 拦截规则集；默认 DEFAULT_BASH_INTERCEPTOR_RULES（内置 10 条） | `packages/coding-agent/src/exec/settings.ts:146` |
| `bash.direnv` | 自动加载 repo 的 direnv/devenv .envrc auto\|off；默认 "auto" | `packages/coding-agent/src/exec/settings.ts:152` |
| `bash.direnvLoadTimeoutMs` | 首次 direnv export 最大等待 ms；默认 30000 | `packages/coding-agent/src/exec/settings.ts:166` |
| `shellMinimizer.enabled` | 压缩冗长 shell 输出（git/npm/cargo 等）；默认 true | `packages/coding-agent/src/exec/settings.ts:180` |
| `shellMinimizer.settingsPath` | minimizer 设置文件路径；默认 undefined | `packages/coding-agent/src/exec/settings.ts:192` |
| `shellMinimizer.only` | 仅对这些命令启用；默认 [] | `packages/coding-agent/src/exec/settings.ts:198` |
| `shellMinimizer.except` | 对这些命令禁用；默认 [] | `packages/coding-agent/src/exec/settings.ts:204` |
| `shellMinimizer.maxCaptureBytes` | 捕获字节上限；默认 4194304 | `packages/coding-agent/src/exec/settings.ts:210` |
| `shellMinimizer.sourceOutlineLevel` | 源文件 outline 模式 default\|aggressive；默认 "default" | `packages/coding-agent/src/exec/settings.ts:216` |
| `shellMinimizer.legacyFilters` | 启用旧式过滤器（未配置时保持默认行为）；默认 undefined | `packages/coding-agent/src/exec/settings.ts:229` |
| `bash.autoBackground.thresholdMs` | 自动后台化阈值 ms（protocolDefault rpc）；默认 60000 | `packages/coding-agent/src/exec/settings.ts:249` |

### eval/settings.ts（共 9 条）
> 数法（payload 原文）：eval/settings.ts — 共 9 条 (grep -c 'register({' = 9)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `eval.py` | 允许 eval 把 Python 单元派发到 IPython（env PI_PY）；默认 true | `packages/coding-agent/src/eval/settings.ts:8` |
| `eval.js` | 允许 eval 把 JS 单元派发到进程内运行时（env PI_JS）；默认 true | `packages/coding-agent/src/eval/settings.ts:21` |
| `eval.autoProvision` | 首次安装时自动创建托管 JS eval 环境；默认 true | `packages/coding-agent/src/eval/settings.ts:34` |
| `eval.tools.enabled` | 允许 eval 单元定义可供子代理调用的工具；默认 true | `packages/coding-agent/src/eval/settings.ts:46` |
| `eval.workpool.freshAgents` | workpool 每项生成新子代理而非复用；默认 false | `packages/coding-agent/src/eval/settings.ts:59` |
| `eval.autoBackground.enabled` | 自动后台化长时间 eval 单元（protocolDefault rpc）；默认 false | `packages/coding-agent/src/eval/settings.ts:71` |
| `eval.autoBackground.thresholdMs` | 自动后台化阈值 ms（protocolDefault rpc）；默认 60000 | `packages/coding-agent/src/eval/settings.ts:84` |
| `python.kernelMode` | IPython 内核保持存活或每次新起 session\|per-call；默认 "session" | `packages/coding-agent/src/eval/settings.ts:92` |
| `python.interpreter` | 精确 Python 可执行路径（设置后跳过自动发现）；默认 "" | `packages/coding-agent/src/eval/settings.ts:105` |

### task/settings.ts（共 29 条）
> 数法（payload 原文）：task/settings.ts — 共 29 条 (full read; grep context truncated at line 300)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `task.isolation.enabled` | 子代理在隔离检出副本中运行并事后整合（protocolDefault rpc/acp）；默认 false | `packages/coding-agent/src/task/settings.ts:23` |
| `isolation.backend` | 隔离/克隆后端 auto\|apfs\|btrfs\|zfs\|reflink\|overlayfs\|projfs\|block-clone\|rcopy；默认 "auto" | `packages/coding-agent/src/task/settings.ts:36` |
| `worktree.clone` | 新 worktree 以 COW 克隆当前检出（携带被忽略的构建产物）；默认 true | `packages/coding-agent/src/task/settings.ts:73` |
| `worktree.cleanSource` | /wt 创建后重置原检出跟踪改动并清理未跟踪文件；默认 false | `packages/coding-agent/src/task/settings.ts:87` |
| `task.isolation.apply` | 自动把成功的隔离改动应用到父检出；默认 true | `packages/coding-agent/src/task/settings.ts:101` |
| `task.isolation.merge` | 整合方式 patch\|branch；默认 "patch" | `packages/coding-agent/src/task/settings.ts:115` |
| `task.isolation.commits` | 嵌套 repo 提交信息风格 generic\|ai；默认 "generic" | `packages/coding-agent/src/task/settings.ts:133` |
| `worktree.base` | worktree 基目录（env OMP_WORKTREE_DIR，未设 ~/.omp/wt）；默认 undefined | `packages/coding-agent/src/task/settings.ts:151` |
| `task.eager` | 推动委派子代理的强度 default\|preferred\|always；默认 "default" | `packages/coding-agent/src/task/settings.ts:172` |
| `task.batch` | task 工具用批量形态 {context,tasks[]}；默认 true | `packages/coding-agent/src/task/settings.ts:195` |
| `task.speculativeLaunch` | 批量项流式完成即启动子代理；默认 true | `packages/coding-agent/src/task/settings.ts:209` |
| `task.enableEffort` | task 生成暴露 effort 参数覆盖思考级别；默认 false | `packages/coding-agent/src/task/settings.ts:222` |
| `task.maxConcurrency` | 并发运行的最大子代理数（0 无限）；默认 32 | `packages/coding-agent/src/task/settings.ts:235` |
| `task.enableLsp` | 允许子代理使用 lsp 工具；默认 false | `packages/coding-agent/src/task/settings.ts:258` |
| `task.maxRecursionDepth` | 子代理可再生成子代理的深度（-1 无限）；默认 2 | `packages/coding-agent/src/task/settings.ts:271` |
| `task.maxRuntimeMs` | 每个子代理墙钟上限 ms（0 禁用）；默认 0 | `packages/coding-agent/src/task/settings.ts:291` |
| `task.completionProbeMs` | 询问工作子代理完成度的间隔 ms（0 禁用）；默认 120000 | `packages/coding-agent/src/task/settings.ts:311` |
| `task.agentIdleTtlMs` | 空闲子代理保留内存时长 ms（0 保持存活）；默认 420000 | `packages/coding-agent/src/task/settings.ts:330` |
| `task.softRequestBudget` | 每子代理软请求预算（1.5x 强制收尾，0 禁用）；默认 200 | `packages/coding-agent/src/task/settings.ts:343` |
| `task.softRequestBudgetNotice` | 超软预算时注入一次收尾方向盘通知；默认 true | `packages/coding-agent/src/task/settings.ts:362` |
| `task.maxEffort` | task 每次生成 effort 提示的上限（THINKING_EFFORTS）；默认 "max" | `packages/coding-agent/src/task/settings.ts:382` |
| `task.disabledAgents` | 禁用的代理名列表（protocolDefault rpc/acp）；默认 [] | `packages/coding-agent/src/task/settings.ts:396` |
| `task.agentModelOverrides` | 按代理覆盖模型；默认 {} | `packages/coding-agent/src/task/settings.ts:404` |
| `task.agentServiceTierOverrides` | 按代理覆盖服务层级；默认 {} | `packages/coding-agent/src/task/settings.ts:411` |
| `task.agentCompactionThresholdOverrides` | 按代理覆盖压缩阈值；默认 {} | `packages/coding-agent/src/task/settings.ts:419` |
| `task.agentPrewalk` | 按代理 prewalk 覆盖；默认 {} | `packages/coding-agent/src/task/settings.ts:428` |
| `task.agentAdvisor` | 按代理 advisor 覆盖；默认 {} | `packages/coding-agent/src/task/settings.ts:435` |
| `task.prewalk` | 为内置通用 task 子代理开启 prewalk；默认 false | `packages/coding-agent/src/task/settings.ts:442` |
| `task.showResolvedModelBadge` | 在 task 控件状态行显示每个子代理实际使用的模型 id；默认 false | `packages/coding-agent/src/task/settings.ts:453` |

### plan-mode/settings.ts（共 4 条）
> 数法（payload 原文）：plan-mode/settings.ts — 共 4 条 (grep -c 'register({' = 4)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `plan.enabled` | 启用计划模式（执行前只读探索与规划）；默认 true | `packages/coding-agent/src/plan-mode/settings.ts:12` |
| `plan.defaultOnStartup` | 每个新会话自动进入计划模式；默认 false | `packages/coding-agent/src/plan-mode/settings.ts:24` |
| `plan.autosave` | 计划模式完成时自动保存已批准计划；默认 false | `packages/coding-agent/src/plan-mode/settings.ts:37` |
| `plan.autosaveDir` | 计划自动保存目录（空=<project>/.omp/plans/）；默认 undefined | `packages/coding-agent/src/plan-mode/settings.ts:50` |

### goals/settings.ts（共 4 条）
> 数法（payload 原文）：goals/settings.ts — 共 4 条 (grep -c 'register({' = 4)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `goal.enabled` | 启用每会话目标模式与隐藏 goal 工具；默认 true | `packages/coding-agent/src/goals/settings.ts:3` |
| `goal.statusInFooter` | 状态行目标指示旁显示 token 预算；默认 true | `packages/coding-agent/src/goals/settings.ts:15` |
| `goal.continuationModes` | 活跃目标可自动续接的运行模式；默认 ["interactive"] | `packages/coding-agent/src/goals/settings.ts:27` |
| `title.refreshOnReplan` | todo 重规划后刷新生成的会话标题（用户设定除外）；默认 true | `packages/coding-agent/src/goals/settings.ts:39` |

### extensibility/settings.ts（共 20 条）
> 数法（payload 原文）：extensibility/settings.ts — 共 20 条 (grep -c 'register({' = 20)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `extensions` | 启用的扩展列表；默认 [] | `packages/coding-agent/src/extensibility/settings.ts:10` |
| `disabledExtensions` | 禁用的扩展列表；默认 [] | `packages/coding-agent/src/extensibility/settings.ts:12` |
| `skills.registryUrl` | omp skill 使用的 Skillshare registry URL；默认 DEFAULT_SKILLS_URL（常量） | `packages/coding-agent/src/extensibility/settings.ts:15` |
| `skills.enabled` | 启用 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:29` |
| `skills.enableSkillCommands` | 把 skills 注册为 /skill:name 命令；默认 true | `packages/coding-agent/src/extensibility/settings.ts:31` |
| `skills.enableCodexUser` | 加载 ~/.codex 用户 skills；默认 false | `packages/coding-agent/src/extensibility/settings.ts:43` |
| `skills.enableClaudeUser` | 加载 ~/.claude 用户 skills；默认 false | `packages/coding-agent/src/extensibility/settings.ts:45` |
| `skills.enableClaudeProject` | 加载 .claude 项目 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:47` |
| `skills.enablePiUser` | 加载 ~/.omp 用户 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:53` |
| `skills.enablePiProject` | 加载 .omp 项目 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:55` |
| `skills.enableAgentsUser` | 加载 ~/.agents 用户 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:57` |
| `skills.enableAgentsProject` | 加载 .agents 项目 skills；默认 true | `packages/coding-agent/src/extensibility/settings.ts:59` |
| `skills.customDirectories` | 额外 skills 目录；默认 [] | `packages/coding-agent/src/extensibility/settings.ts:65` |
| `skills.ignoredSkills` | 忽略的 skills 名；默认 [] | `packages/coding-agent/src/extensibility/settings.ts:71` |
| `skills.includeSkills` | 只包含的 skills 名；默认 [] | `packages/coding-agent/src/extensibility/settings.ts:77` |
| `commands.enableClaudeUser` | 加载 ~/.claude/commands/；默认 false | `packages/coding-agent/src/extensibility/settings.ts:103` |
| `commands.enableClaudeProject` | 加载 .claude/commands/；默认 true | `packages/coding-agent/src/extensibility/settings.ts:115` |
| `commands.enableOpencodeUser` | 加载 ~/.config/opencode/commands/；默认 false | `packages/coding-agent/src/extensibility/settings.ts:127` |
| `commands.enableOpencodeProject` | 加载 .opencode/commands/；默认 true | `packages/coding-agent/src/extensibility/settings.ts:139` |
| `extensionHandlers.toolCallTimeoutMs` | 扩展 tool_call 处理器的活动超时 ms（无效值用 30000）；默认 30000 | `packages/coding-agent/src/extensibility/settings.ts:151` |

### web/settings.ts（共 10 条）
> 数法（payload 原文）：web/settings.ts — 共 10 条 (grep -c 'register({' = 10)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `exa.enabled` | 启用 Exa 网络搜索 provider；默认 true | `packages/coding-agent/src/web/settings.ts:8` |
| `exa.searchDelayMs` | Exa 搜索请求最小间隔 ms（0 关闭节流）；默认 1000 | `packages/coding-agent/src/web/settings.ts:20` |
| `searxng.endpoint` | 自建 SearXNG 实例基 URL（env SEARXNG_ENDPOINT）；默认 undefined | `packages/coding-agent/src/web/settings.ts:33` |
| `searxng.token` | SearXNG 令牌（凭据，env SEARXNG_TOKEN）；默认 undefined | `packages/coding-agent/src/web/settings.ts:46` |
| `searxng.basicUsername` | SearXNG Basic 用户名（env SEARXNG_BASIC_USERNAME）；默认 undefined | `packages/coding-agent/src/web/settings.ts:54` |
| `searxng.basicPassword` | SearXNG Basic 密码（凭据，env SEARXNG_BASIC_PASSWORD）；默认 undefined | `packages/coding-agent/src/web/settings.ts:62` |
| `searxng.categories` | SearXNG 搜索分类；默认 undefined | `packages/coding-agent/src/web/settings.ts:70` |
| `searxng.engines` | SearXNG 引擎；默认 undefined | `packages/coding-agent/src/web/settings.ts:72` |
| `searxng.language` | SearXNG 语言；默认 undefined | `packages/coding-agent/src/web/settings.ts:74` |
| `searxng.safesearch` | SearXNG 安全搜索级别；默认 undefined | `packages/coding-agent/src/web/settings.ts:76` |

### tools/browser/settings.ts（共 10 条）
> 数法（payload 原文）：tools/browser/settings.ts — 共 10 条 (grep -c 'register({' = 10)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `browser.enabled` | 启用浏览器 eval prelude（Puppeteer 脚本化 Chromium）；默认 true | `packages/coding-agent/src/tools/browser/settings.ts:7` |
| `browser.cdpUrl` | 默认 HTTP CDP 发现端点；默认 undefined | `packages/coding-agent/src/tools/browser/settings.ts:19` |
| `browser.relay` | 经 omp browser relay 驱动自己的 Chrome 标签（env PI_BROWSER_RELAY）；默认 false | `packages/coding-agent/src/tools/browser/settings.ts:32` |
| `browser.relayUrl` | relay 端点（默认 http://127.0.0.1:9224）；默认 undefined | `packages/coding-agent/src/tools/browser/settings.ts:45` |
| `browser.headless` | 无头模式启动浏览器；默认 true | `packages/coding-agent/src/tools/browser/settings.ts:57` |
| `browser.cmux` | 有 cmux socket 时用 cmux WKWebView 面（env PI_BROWSER_CMUX）；默认 true | `packages/coding-agent/src/tools/browser/settings.ts:69` |
| `browser.tern` | Tern pane 内以 PiP 开标签（env PI_BROWSER_TERN）；默认 true | `packages/coding-agent/src/tools/browser/settings.ts:82` |
| `browser.freezeOnTurnEnd` | 轮次结束时冻结 OMP 自有浏览器标签以省 CPU/GPU；默认 true | `packages/coding-agent/src/tools/browser/settings.ts:95` |
| `browser.idleCloseSec` | 空闲超过此秒数关闭自有标签/PiP（0 永不）；默认 1800 | `packages/coding-agent/src/tools/browser/settings.ts:108` |
| `browser.screenshotDir` | 截图保存目录（支持 ~；空则临时文件）；默认 undefined | `packages/coding-agent/src/tools/browser/settings.ts:127` |

### ida/settings.ts（共 5 条）
> 数法（payload 原文）：ida/settings.ts — 共 5 条 (grep -c 'register({' = 5)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ida.enabled` | read 打开的可执行文件在 IDA Pro 中打开并启用 ida 工具（无安装则惰性）；默认 true | `packages/coding-agent/src/ida/settings.ts:8` |
| `ida.python` | 能 import ida_domain/idapro 的 Python 解释器（空自动检测）；默认 "" | `packages/coding-agent/src/ida/settings.ts:22` |
| `ida.installDir` | 含 libidalib 的 IDA 安装目录（空自动检测）；默认 "" | `packages/coding-agent/src/ida/settings.ts:35` |
| `ida.maxOpen` | 每项目同时打开的 IDA 数据库上限（超额逐出最久未用）；默认 4 | `packages/coding-agent/src/ida/settings.ts:49` |
| `ida.idleCloseSec` | IDA 数据库空闲多少秒后保存并关闭（0 永不）；默认 900 | `packages/coding-agent/src/ida/settings.ts:69` |

### mcp/settings.ts（共 5 条）
> 数法（payload 原文）：mcp/settings.ts — 共 5 条 (grep -c 'register({' = 5)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `mcp.enableProjectConfig` | 加载项目根 .mcp.json/mcp.json；默认 true | `packages/coding-agent/src/mcp/settings.ts:9` |
| `mcp.startupTimeoutMs` | 初始 MCP 工具发现等待 ms（0 等到连接稳定）；默认 250 | `packages/coding-agent/src/mcp/settings.ts:21` |
| `mcp.renderMarkdownResults` | 非 JSON MCP 文本结果按 Markdown 渲染；默认 true | `packages/coding-agent/src/mcp/settings.ts:33` |
| `mcp.notifications` | 把 MCP 资源更新注入对话；默认 false | `packages/coding-agent/src/mcp/settings.ts:46` |
| `mcp.notificationDebounceMs` | MCP 资源更新注入前的去抖窗口 ms；默认 500 | `packages/coding-agent/src/mcp/settings.ts:58` |

### blob-broker/settings.ts (images.urls)（共 10 条）
> 数法（payload 原文）：blob-broker/settings.ts (images.urls) — 共 10 条 (grep -c 'register({' = 10)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `images.urls.enabled` | 经配置后端链把出图发布为 URL 而非内联 base64（失败自动回退内联）；默认 false | `packages/coding-agent/src/blob-broker/settings.ts:25` |
| `images.urls.backends` | 发布图片的有序后端链；默认 ["provider-files","tailscale","cloudflared","litterbox"] | `packages/coding-agent/src/blob-broker/settings.ts:38` |
| `images.urls.options` | 每后端选项记录；默认 {} | `packages/coding-agent/src/blob-broker/settings.ts:52` |
| `images.urls.credentials` | 每后端凭据记录（凭据）；默认 {} | `packages/coding-agent/src/blob-broker/settings.ts:58` |
| `images.urls.command` | command 后端 argv 模板（{file}/{mime}/{ext}）；默认 undefined | `packages/coding-agent/src/blob-broker/settings.ts:65` |
| `images.urls.publicBaseUrl` | 外部可达基 URL（ssh 必需）；默认 undefined | `packages/coding-agent/src/blob-broker/settings.ts:78` |
| `images.urls.ttlHours` | 本地托管图片 URL 的存活窗口小时（0 broker 运行期常驻）；默认 72 | `packages/coding-agent/src/blob-broker/settings.ts:90` |
| `images.urls.bindHost` | blob 服务器绑定主机；默认 "127.0.0.1" | `packages/coding-agent/src/blob-broker/settings.ts:103` |
| `images.urls.sshTarget` | ssh 反向转发目标 user@host；默认 undefined | `packages/coding-agent/src/blob-broker/settings.ts:115` |
| `images.urls.sshRemotePort` | ssh 反向转发远端监听端口；默认 8787 | `packages/coding-agent/src/blob-broker/settings.ts:127` |

### secrets/settings.ts（共 1 条）
> 数法（payload 原文）：secrets/settings.ts — 共 1 条 (grep -c 'register({' = 1)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `secrets.enabled` | 混淆已配置密钥并在发送给 provider 前脱敏凭据形 token；默认 false | `packages/coding-agent/src/secrets/settings.ts:13` |

### tts/settings.ts（共 5 条）
> 数法（payload 原文）：tts/settings.ts — 共 5 条 (grep -c 'register({' = 5)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tts.localVoice` | 本地 TTS 后端使用的 Kokoro 语音；默认 DEFAULT_TTS_VOICE（常量，tts/models） | `packages/coding-agent/src/tts/settings.ts:8` |
| `speech.enabled` | 助手输出流式朗读；默认 false | `packages/coding-agent/src/tts/settings.ts:22` |
| `speech.mode` | 朗读内容 all\|assistant\|yield；默认 "assistant" | `packages/coding-agent/src/tts/settings.ts:34` |
| `speech.enhanced` | 合成前用 tiny/smol 模型改写为口语化散文；默认 false | `packages/coding-agent/src/tts/settings.ts:53` |
| `speech.voice` | 朗读时使用的 Kokoro 语音；默认 DEFAULT_TTS_VOICE（常量） | `packages/coding-agent/src/tts/settings.ts:66` |

### stt/settings.ts（共 3 条）
> 数法（payload 原文）：stt/settings.ts — 共 3 条 (grep -c 'register({' = 3)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `stt.enabled` | 启用麦克风语音转文字输入；默认 false | `packages/coding-agent/src/stt/settings.ts:9` |
| `stt.language` | 识别语言；默认 "en" | `packages/coding-agent/src/stt/settings.ts:21` |
| `stt.submitTrigger` | 口述何时自动提交（STT_SUBMIT_TRIGGER_VALUES）；默认 "never" | `packages/coding-agent/src/stt/settings.ts:23` |

### live/settings.ts（共 1 条）
> 数法（payload 原文）：live/settings.ts — 共 1 条 (grep -c 'register({' = 1)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `live.voice` | Codex 实时语音会话所用语音（LIVE_VOICE_VALUES）；默认 DEFAULT_LIVE_VOICE="sol"（常量，live/voices） | `packages/coding-agent/src/live/settings.ts:8` |

### collab/settings.ts（共 4 条）
> 数法（payload 原文）：collab/settings.ts — 共 4 条 (grep -c 'register({' = 4)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `collab.relayUrl` | /collab 使用的 relay（wss://host[:port]）；默认 DEFAULT_RELAY_URL（常量，collab/protocol） | `packages/coding-agent/src/collab/settings.ts:9` |
| `collab.webUrl` | /collab 链接所用的浏览器 UI（空由 relayUrl 推导）；默认 "" | `packages/coding-agent/src/collab/settings.ts:21` |
| `collab.displayName` | 对其它协作者显示的昵称（默认 OS 用户名）；默认 "" | `packages/coding-agent/src/collab/settings.ts:34` |
| `collab.autoStart` | 每个交互会话启动时自动托管 off\|view\|control；默认 "off" | `packages/coding-agent/src/collab/settings.ts:46` |

### commands/settings.ts (share)（共 3 条）
> 数法（payload 原文）：commands/settings.ts (share) — 共 3 条 (grep -c 'register({' = 3)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `share.serverUrl` | /share 的查看/上传基（链接为 <base>/<id>#<key>）；默认 DEFAULT_SHARE_URL（常量，@oh-my-pi/pi-wire） | `packages/coding-agent/src/commands/settings.ts:8` |
| `share.store` | /share 上传加密 blob 的位置 blob\|gist；默认 "blob" | `packages/coding-agent/src/commands/settings.ts:21` |
| `share.redactSecrets` | 上传前对 /share 快照运行密钥混淆器；默认 true | `packages/coding-agent/src/commands/settings.ts:46` |

### stream/settings.ts（共 2 条）
> 数法（payload 原文）：stream/settings.ts — 共 2 条 (grep -c 'register({' = 2)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `stream.serverUrl` | omp stream 的直播服务器（https://host[:port]）；默认 DEFAULT_STREAM_URL（常量，@oh-my-pi/pi-wire） | `packages/coding-agent/src/stream/settings.ts:11` |
| `stream.redactPatterns` | 对每行直播额外脱敏的正则；默认 [] | `packages/coding-agent/src/stream/settings.ts:24` |

### commit/settings.ts（共 6 条）
> 数法（payload 原文）：commit/settings.ts — 共 6 条 (grep -c 'register({' = 6)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `commit.mapReduceEnabled` | 大 diff 用 map-reduce 生成提交信息；默认 true | `packages/coding-agent/src/commit/settings.ts:7` |
| `commit.mapReduceThreshold` | 触发 map-reduce 的 diff 阈值；默认 5000 | `packages/coding-agent/src/commit/settings.ts:9` |
| `commit.mapBatchTokenBudget` | 每 map 批次 token 预算；默认 16000 | `packages/coding-agent/src/commit/settings.ts:11` |
| `commit.cacheEnabled` | 提交信息缓存；默认 true | `packages/coding-agent/src/commit/settings.ts:17` |
| `commit.cacheTtlDays` | 缓存 TTL 天数；默认 14 | `packages/coding-agent/src/commit/settings.ts:19` |
| `commit.changelogMaxDiffChars` | changelog 最大 diff 字符；默认 120000 | `packages/coding-agent/src/commit/settings.ts:21` |

### cli/gc-settings.ts（共 9 条）
> 数法（payload 原文）：cli/gc-settings.ts — 共 9 条 (grep -c 'register({' = 9)

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `gc.blobs` | gc 回收 blob；默认 true | `packages/coding-agent/src/cli/gc-settings.ts:7` |
| `gc.archive` | gc 归档；默认 true | `packages/coding-agent/src/cli/gc-settings.ts:9` |
| `gc.wal` | gc 回收 WAL；默认 true | `packages/coding-agent/src/cli/gc-settings.ts:11` |
| `gc.coldArchiveAfterDays` | 多少天后冷归档；默认 30 | `packages/coding-agent/src/cli/gc-settings.ts:13` |
| `gc.retainNewestGlobal` | 全局保留最新数量；默认 20 | `packages/coding-agent/src/cli/gc-settings.ts:15` |
| `gc.retainNewestPerCwd` | 每 cwd 保留最新数量；默认 10 | `packages/coding-agent/src/cli/gc-settings.ts:17` |
| `gc.stale` | 清理用户可见文件（debug 报告/collab 副本，默认 opt-in）；默认 false | `packages/coding-agent/src/cli/gc-settings.ts:21` |
| `gc.staleRetainNewest` | stale 阶段保留最新数量；默认 20 | `packages/coding-agent/src/cli/gc-settings.ts:23` |
| `gc.staleRetainDays` | stale 阶段保留天数；默认 30 | `packages/coding-agent/src/cli/gc-settings.ts:25` |

## 41. 面板与 overlay · 内部键（共 545 条）

### overlays/agent-hub.ts — AgentHubOverlayComponent（Agent Hub，含 agents+activity 两分区）（共 20 条）
> 数法（payload 原文）：overlays/agent-hub.ts — AgentHubOverlayComponent（Agent Hub，含 agents+activity 两分区） 共 20 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `alt+a / ctrl+s` | 关闭 hub（hubKeys=app.agents.hub/app.session.observe） | `packages/tui/src/overlays/agent-hub.ts:581` |
| `1` | 切到 agents 分区 | `packages/tui/src/overlays/agent-hub.ts:591` |
| `2` | 切到 activity 分区 | `packages/tui/src/overlays/agent-hub.ts:595` |
| `/` | 进入活动/agent 过滤搜索输入 | `packages/tui/src/overlays/agent-hub.ts:2301,2404` |
| `space` | 切换 activity 跟随最新 | `packages/tui/src/overlays/agent-hub.ts:2306` |
| `f` | 循环 activity 过滤器 | `packages/tui/src/overlays/agent-hub.ts:2310` |
| `s` | 循环 activity 作用域 | `packages/tui/src/overlays/agent-hub.ts:2316` |
| `j / ↓` | 选中下一行（activity/agents） | `packages/tui/src/overlays/agent-hub.ts:2320,2444` |
| `k / ↑` | 选中上一行（activity/agents） | `packages/tui/src/overlays/agent-hub.ts:2328,2451` |
| `enter` | 打开选中 agent 的聊天 | `packages/tui/src/overlays/agent-hub.ts:2336,2458` |
| `escape` | 清过滤词/退出过滤编辑 | `packages/tui/src/overlays/agent-hub.ts:2287,2391` |
| `pageUp` | 详情区向上翻页 | `packages/tui/src/overlays/agent-hub.ts:2415` |
| `pageDown` | 详情区向下翻页 | `packages/tui/src/overlays/agent-hub.ts:2419` |
| `tab` | 切换窄屏详情面板 | `packages/tui/src/overlays/agent-hub.ts:2409` |
| `left` | 回 agents 分区/关窄屏详情 | `packages/tui/src/overlays/agent-hub.ts:2297,2428` |
| `t` | 切换 agents 视图模式 | `packages/tui/src/overlays/agent-hub.ts:2424` |
| `r` | 复活选中 parked agent | `packages/tui/src/overlays/agent-hub.ts:2463` |
| `x` | 终止并释放选中 agent | `packages/tui/src/overlays/agent-hub.ts:2467` |
| `enter(编辑中)` | 提交/退出过滤编辑 | `packages/tui/src/overlays/agent-hub.ts:2272,2376` |
| `任何可打印键` | 转发给过滤 Input | `packages/tui/src/overlays/agent-hub.ts:2276,2381` |

### overlays/agent-transcript-viewer.ts — AgentTranscriptViewer（共 8 条）
> 数法（payload 原文）：overlays/agent-transcript-viewer.ts — AgentTranscriptViewer 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `alt+a / ctrl+s` | 整 hub 关闭（hubKeys） | `packages/tui/src/overlays/agent-transcript-viewer.ts:499` |
| `escape` | 清编辑器文本，再按则关本 viewer | `packages/tui/src/overlays/agent-transcript-viewer.ts:506` |
| `ctrl+o (app.tools.expand)` | 展开/折叠工具输出 | `packages/tui/src/overlays/agent-transcript-viewer.ts:516` |
| `j` | 向下滚动 | `packages/tui/src/overlays/agent-transcript-viewer.ts:541` |
| `k` | 向上滚动 | `packages/tui/src/overlays/agent-transcript-viewer.ts:543` |
| `g` | 滚到顶部 | `packages/tui/src/overlays/agent-transcript-viewer.ts:545` |
| `G` | 滚到底部 | `packages/tui/src/overlays/agent-transcript-viewer.ts:547` |
| `其他键` | 转发给输入 Editor | `packages/tui/src/overlays/agent-transcript-viewer.ts:530` |

### overlays/agents-hub.ts — AgentsHubComponent（agent 配置 hub）（共 18 条）
> 数法（payload 原文）：overlays/agents-hub.ts — AgentsHubComponent（agent 配置 hub） 共 18 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+r` | 重新加载 | `packages/tui/src/overlays/agents-hub.ts:731` |
| `tab / shift+tab` | 切换 focus（scope↔list） | `packages/tui/src/overlays/agents-hub.ts:736` |
| `left` | 焦点移到 scope 侧栏 | `packages/tui/src/overlays/agents-hub.ts:741` |
| `right` | 焦点移到列表 | `packages/tui/src/overlays/agents-hub.ts:746` |
| `↑ / 选上` | 侧栏/行上移 | `packages/tui/src/overlays/agents-hub.ts:753,774` |
| `↓ / 选下` | 侧栏/行下移 | `packages/tui/src/overlays/agents-hub.ts:758,779` |
| `enter/return` | 激活行/新建/提交 chip | `packages/tui/src/overlays/agents-hub.ts:763,784,838` |
| `space` | 启用/禁用选中 agent | `packages/tui/src/overlays/agents-hub.ts:789` |
| `escape/选取消` | 退分配/退 strip/退创建/关闭 | `packages/tui/src/overlays/agents-hub.ts:709,825,859,879` |
| `tab(创建中)` | 切换 project/user scope | `packages/tui/src/overlays/agents-hub.ts:863,888` |
| `r(创建中)` | 由描述生成 agent | `packages/tui/src/overlays/agents-hub.ts:870` |
| `ctrl+q/ctrl+enter` | 生成 agent（app.message.followUp） | `packages/tui/src/overlays/agents-hub.ts:884` |
| `enter(创建输入)` | 输入换行 | `packages/tui/src/overlays/agents-hub.ts:892` |
| `可打印键` | 编辑搜索/描述输入 | `packages/tui/src/overlays/agents-hub.ts:796,897` |
| `strip 移动键` | 左右/上下/tab 换 chip（hub-frame） | `packages/tui/src/overlays/agents-hub.ts:837` |
| `strip pattern enter` | 提交 pattern 输入 | `packages/tui/src/overlays/agents-hub.ts:830` |
| `strip 输入键` | 转发给 strip 输入框 | `packages/tui/src/overlays/agents-hub.ts:834` |
| `鼠标` | 见鼠标组（wheel/hover/click） | `packages/tui/src/overlays/agents-hub.ts:691` |

### overlays/annotation-overlay.ts — AnnotationOverlay（代码/文本标注审查）（共 22 条）
> 数法（payload 原文）：overlays/annotation-overlay.ts — AnnotationOverlay（代码/文本标注审查） 共 22 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 取消标注/完成退出 | `packages/tui/src/overlays/annotation-overlay.ts:305,312` |
| `ctrl+g (app.editor.external)` | 标注文本走外部编辑器 | `packages/tui/src/overlays/annotation-overlay.ts:301` |
| `A` | 开始标注（file/text） | `packages/tui/src/overlays/annotation-overlay.ts:316` |
| `[ / ]` | 上一个/下一个文件 | `packages/tui/src/overlays/annotation-overlay.ts:320,324` |
| `u` | 撤销上一条标注 | `packages/tui/src/overlays/annotation-overlay.ts:328` |
| `e` | 编辑当前标注 | `packages/tui/src/overlays/annotation-overlay.ts:332` |
| `tab / \t` | 焦点区域循环 +1 | `packages/tui/src/overlays/annotation-overlay.ts:336` |
| `shift+tab / \x1b[Z` | 焦点区域循环 -1 | `packages/tui/src/overlays/annotation-overlay.ts:340` |
| `files:a` | 标注整文件 | `packages/tui/src/overlays/annotation-overlay.ts:373` |
| `files/actions:k/j` | 上/下选择文件 | `packages/tui/src/overlays/annotation-overlay.ts:377,381` |
| `files:right/l/enter` | 焦点进 diff | `packages/tui/src/overlays/annotation-overlay.ts:385` |
| `diff:a` | 标注行 | `packages/tui/src/overlays/annotation-overlay.ts:391` |
| `diff:left/h` | 焦点回 files | `packages/tui/src/overlays/annotation-overlay.ts:395` |
| `diff:right/l/enter` | 焦点到 actions | `packages/tui/src/overlays/annotation-overlay.ts:399` |
| `diff:shift+up/down` | 源光标 ±5 行 | `packages/tui/src/overlays/annotation-overlay.ts:403,407` |
| `diff:k/j` | 源光标 ±1 行 | `packages/tui/src/overlays/annotation-overlay.ts:411,415` |
| `diff:pageUp/pageDown` | 源文本翻页 | `packages/tui/src/overlays/annotation-overlay.ts:419,429` |
| `diff:g/home, G/end` | 源首/尾 | `packages/tui/src/overlays/annotation-overlay.ts:439,442` |
| `actions:k/j` | 动作光标上/下 | `packages/tui/src/overlays/annotation-overlay.ts:455,459` |
| `actions:enter` | 确认动作 | `packages/tui/src/overlays/annotation-overlay.ts:467` |
| `chooser:up/down(或k/j)` | 标注选择器上/下 | `packages/tui/src/overlays/annotation-overlay.ts:727,731` |
| `chooser:cancel/enter` | 取消/打开所选项 | `packages/tui/src/overlays/annotation-overlay.ts:723,735` |

### overlays/ask-dialog.ts — AskDialogComponent（ask 工具问答模态）（共 13 条）
> 数法（payload 原文）：overlays/ask-dialog.ts — AskDialogComponent（ask 工具问答模态） 共 13 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/ctrl+c` | 取消问答 | `packages/tui/src/overlays/ask-dialog.ts:655` |
| `ctrl+o (app.tools.expand)` | 展开/折叠问题文本 | `packages/tui/src/overlays/ask-dialog.ts:661` |
| `tab / right` | 下一题 tab（handleTabSwitchKey） | `packages/tui/src/overlays/ask-dialog.ts:667` |
| `shift+tab / left` | 上一题 tab | `packages/tui/src/overlays/ask-dialog.ts:667` |
| `question:pageUp/pageDown` | 选项区翻页滚动 | `packages/tui/src/overlays/ask-dialog.ts:1173,1179` |
| `question:↑/↓` | 移动选项光标 | `packages/tui/src/overlays/ask-dialog.ts:1185,1191` |
| `question:n/N` | 给选中项加备注 | `packages/tui/src/overlays/ask-dialog.ts:1199` |
| `question:enter/return` | 提交当前答案 | `packages/tui/src/overlays/ask-dialog.ts:1205` |
| `question:space(多选)` | 切换多选项 | `packages/tui/src/overlays/ask-dialog.ts:1206` |
| `submit:↑/↓` | 审阅区滚动 | `packages/tui/src/overlays/ask-dialog.ts:1250,1255` |
| `submit:enter` | 提交全部答案 | `packages/tui/src/overlays/ask-dialog.ts:1261` |
| `inputGuard 键` | 被阻时转发给代理输入 | `packages/tui/src/overlays/ask-dialog.ts:666` |
| `鼠标/native` | 指针点击/cancel/submit 动作 | `packages/tui/src/overlays/ask-dialog.ts:918` |

### overlays/btw-history-panel.ts — BtwHistoryPanel（共 14 条）
> 数法（payload 原文）：overlays/btw-history-panel.ts — BtwHistoryPanel 共 14 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `composer 打开时全部键` | 转给 composer 输入（面板短路） | `packages/tui/src/overlays/btw-history-panel.ts:312` |
| `escape/选取消` | 取消运行中回合或关闭 | `packages/tui/src/overlays/btw-history-panel.ts:317` |
| `f / enter` | 打开 follow-up | `packages/tui/src/overlays/btw-history-panel.ts:322` |
| `c` | 复制答案文本 | `packages/tui/src/overlays/btw-history-panel.ts:326` |
| `tab/shift+tab/ctrl+//ctrl+_/0x1f` | 切换 focus list↔answer | `packages/tui/src/overlays/btw-history-panel.ts:332-336` |
| `right` | 焦点=answer | `packages/tui/src/overlays/btw-history-panel.ts:339` |
| `left` | 焦点=list | `packages/tui/src/overlays/btw-history-panel.ts:341` |
| `list:↑/↓` | 选中上/下一条 | `packages/tui/src/overlays/btw-history-panel.ts:345` |
| `list:pageUp/pageDown` | 按列表高度翻页 | `packages/tui/src/overlays/btw-history-panel.ts:347` |
| `list:home/end` | 首/末条 | `packages/tui/src/overlays/btw-history-panel.ts:349` |
| `answer:↑/↓` | 详情滚动 ±1 | `packages/tui/src/overlays/btw-history-panel.ts:353` |
| `answer:pageUp/pageDown` | 详情翻页 | `packages/tui/src/overlays/btw-history-panel.ts:355` |
| `answer:滚动键` | ScrollView 标准滚动 | `packages/tui/src/overlays/btw-history-panel.ts:357` |
| `answer:end` | 恢复跟随最新 | `packages/tui/src/overlays/btw-history-panel.ts:358` |

### overlays/codex-reset-fireworks.ts — CodexResetFireworksController（共 2 条）
> 数法（payload 原文）：overlays/codex-reset-fireworks.ts — CodexResetFireworksController 共 2 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/esc` | 关闭庆祝动画 | `packages/tui/src/overlays/codex-reset-fireworks.ts:373` |
| `native close` | 按钮关闭同 Esc | `packages/tui/src/overlays/codex-reset-fireworks.ts:377` |

### overlays/copy-selector.ts — CopySelectorComponent（共 12 条）
> 数法（payload 原文）：overlays/copy-selector.ts — CopySelectorComponent 共 12 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 逐级退出（清过滤/关闭） | `packages/tui/src/overlays/copy-selector.ts:449` |
| `ctrl+o (app.tools.expand)` | 展开/折叠输出 | `packages/tui/src/overlays/copy-selector.ts:453` |
| `↑ / 选上` | 上移 | `packages/tui/src/overlays/copy-selector.ts:459` |
| `↓ / 选下` | 下移 | `packages/tui/src/overlays/copy-selector.ts:463` |
| `right` | 进入代码块 | `packages/tui/src/overlays/copy-selector.ts:467` |
| `left` | 返回上层 | `packages/tui/src/overlays/copy-selector.ts:471` |
| `a / A` | 加载全量历史（非块内） | `packages/tui/src/overlays/copy-selector.ts:475` |
| `o / O` | 打开选中块 | `packages/tui/src/overlays/copy-selector.ts:479` |
| `enter/return` | 复制选中项 | `packages/tui/src/overlays/copy-selector.ts:483` |
| `滚动键` | 浏览滚动（不改选择） | `packages/tui/src/overlays/copy-selector.ts:488` |
| `鼠标` | wheel 滚动×3 / 左键点击 | `packages/tui/src/overlays/copy-selector.ts:436` |
| `native picker` | 指针动作同键位 | `packages/tui/src/overlays/copy-selector.ts:589` |

### overlays/history-search.ts — HistorySearchComponent（共 9 条）
> 数法（payload 原文）：overlays/history-search.ts — HistorySearchComponent 共 9 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `↑ / 选上` | 历史项上移 | `packages/tui/src/overlays/history-search.ts:229` |
| `↓ / 选下` | 历史项下移 | `packages/tui/src/overlays/history-search.ts:234` |
| `pageUp/pageDown` | 按 MAX_VISIBLE 翻页 | `packages/tui/src/overlays/history-search.ts:239,244` |
| `home` | 首条 | `packages/tui/src/overlays/history-search.ts:249` |
| `end` | 末条 | `packages/tui/src/overlays/history-search.ts:254` |
| `enter/return` | 选中该历史提示词 | `packages/tui/src/overlays/history-search.ts:259` |
| `app.interrupt` | 取消 | `packages/tui/src/overlays/history-search.ts:267` |
| `其他键` | 转发给搜索 Input | `packages/tui/src/overlays/history-search.ts:272` |
| `native insert/close` | 指针 insert/close 同键位 | `packages/tui/src/overlays/history-search.ts:381` |

### overlays/hook-editor.ts — HookEditorComponent（共 8 条）
> 数法（payload 原文）：overlays/hook-editor.ts — HookEditorComponent 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+q/ctrl+enter (app.message.followUp)` | 提交（两种风格均先判） | `packages/tui/src/overlays/hook-editor.ts:362,394` |
| `escape/esc/app.interrupt(prompt风格)` | 取消 | `packages/tui/src/overlays/hook-editor.ts:368` |
| `ctrl+g (app.editor.external)` | 打开外部编辑器 | `packages/tui/src/overlays/hook-editor.ts:374,412` |
| `enter/return(prompt风格)` | 提交 | `packages/tui/src/overlays/hook-editor.ts:380` |
| `enter/return(hook风格)` | 插入换行 | `packages/tui/src/overlays/hook-editor.ts:400` |
| `app.interrupt(hook风格)` | 取消 | `packages/tui/src/overlays/hook-editor.ts:406` |
| `其他键` | 转发给 Editor | `packages/tui/src/overlays/hook-editor.ts:386,418` |
| `bracketed paste` | 粘贴处理/图片附件 | `packages/tui/src/overlays/hook-editor.ts:240` |

### overlays/hook-input.ts + bordered-loader.ts（纯转发壳）（共 2 条）
> 数法（payload 原文）：overlays/hook-input.ts + bordered-loader.ts（纯转发壳） 共 2 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `HookInputComponent 全部键` | 转发给 Form（isCancel=app.interrupt） | `packages/tui/src/overlays/hook-input.ts:72` |
| `BorderedLoader 全部键` | 转发给 CancellableLoader（仅取消） | `packages/tui/src/overlays/bordered-loader.ts:52` |

### overlays/hook-selector.ts — HookSelectorComponent（共 10 条）
> 数法（payload 原文）：overlays/hook-selector.ts — HookSelectorComponent 共 10 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `1-9（无搜索词）` | 按编号快速选/确认选项 | `packages/tui/src/overlays/hook-selector.ts:620` |
| `escape/选取消` | 取消 | `packages/tui/src/overlays/hook-selector.ts:635` |
| `↑ / k(搜索关)` | 上移选项 | `packages/tui/src/overlays/hook-selector.ts:644` |
| `↓ / j(搜索关)` | 下移选项 | `packages/tui/src/overlays/hook-selector.ts:646` |
| `enter/return` | 确认选中项 | `packages/tui/src/overlays/hook-selector.ts:648` |
| `left / h(搜索关&slider)` | 滑块-1 或左回调 | `packages/tui/src/overlays/hook-selector.ts:652` |
| `right / l(搜索关&slider)` | 滑块+1 或右回调 | `packages/tui/src/overlays/hook-selector.ts:658` |
| `ctrl+g (app.editor.external)` | 外部编辑器回调 | `packages/tui/src/overlays/hook-selector.ts:663` |
| `其他键` | 转发给搜索 Input 并同步过滤 | `packages/tui/src/overlays/hook-selector.ts:666,606` |
| `native action/指针` | 选项/slider 同键位 | `packages/tui/src/overlays/hook-selector.ts:794` |

### overlays/jobs-panel.ts — JobsSheet（共 4 条）
> 数法（payload 原文）：overlays/jobs-panel.ts — JobsSheet 共 4 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 关闭面板 | `packages/tui/src/overlays/jobs-panel.ts:217` |
| `↑ / 选上` | 上一任务 | `packages/tui/src/overlays/jobs-panel.ts:218` |
| `↓ / 选下` | 下一任务 | `packages/tui/src/overlays/jobs-panel.ts:219` |
| `x` | 取消选中运行中任务 | `packages/tui/src/overlays/jobs-panel.ts:220` |

### overlays/login-dialog.ts — LoginDialogComponent（共 3 条）
> 数法（payload 原文）：overlays/login-dialog.ts — LoginDialogComponent 共 3 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tui.select.cancel` | 取消登录 | `packages/tui/src/overlays/login-dialog.ts:418` |
| `其他键` | 转发给输入字段 | `packages/tui/src/overlays/login-dialog.ts:424` |
| `native cancel/submit` | 按钮同 Esc/Enter | `packages/tui/src/overlays/login-dialog.ts:404` |

### overlays/logout-account-selector.ts — LogoutAccountSelectorComponent（共 6 条）
> 数法（payload 原文）：overlays/logout-account-selector.ts — LogoutAccountSelectorComponent 共 6 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 取消 | `packages/tui/src/overlays/logout-account-selector.ts:117` |
| `↑ / 选上` | 上一条账号 | `packages/tui/src/overlays/logout-account-selector.ts:122` |
| `↓ / 选下` | 下一条账号 | `packages/tui/src/overlays/logout-account-selector.ts:125` |
| `pageUp` | 上翻 MAX_VISIBLE | `packages/tui/src/overlays/logout-account-selector.ts:128` |
| `pageDown` | 下翻 MAX_VISIBLE | `packages/tui/src/overlays/logout-account-selector.ts:131` |
| `enter/return` | 确认登出该账号 | `packages/tui/src/overlays/logout-account-selector.ts:134` |

### overlays/mcp-add-wizard.ts — MCPAddWizard（共 8 条）
> 数法（payload 原文）：overlays/mcp-add-wizard.ts — MCPAddWizard 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `OAuth等待时 ctrl+c/app.interrupt` | 中止 OAuth 流程 | `packages/tui/src/overlays/mcp-add-wizard.ts:739` |
| `ctrl+c (\x03)` | 立即取消向导 | `packages/tui/src/overlays/mcp-add-wizard.ts:745` |
| `app.interrupt` | name 步取消，其余回上一步 | `packages/tui/src/overlays/mcp-add-wizard.ts:762` |
| `async 步其他键` | 忽略（仅 interrupt 生效） | `packages/tui/src/overlays/mcp-add-wizard.ts:759` |
| `enter/return` | 选择当前选项 | `packages/tui/src/overlays/mcp-add-wizard.ts:774` |
| `↑ / 选上` | 选项上移 | `packages/tui/src/overlays/mcp-add-wizard.ts:780` |
| `↓ / 选下` | 选项下移 | `packages/tui/src/overlays/mcp-add-wizard.ts:784` |
| `输入步全部键` | 转发给当前步骤 FormField | `packages/tui/src/overlays/mcp-add-wizard.ts:753` |

### overlays/model-browser.ts — ModelBrowser（共享内嵌浏览器）（共 9 条）
> 数法（payload 原文）：overlays/model-browser.ts — ModelBrowser（共享内嵌浏览器） 共 9 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 清查询，否则冒泡取消 | `packages/tui/src/overlays/model-browser.ts:1161` |
| `↑ / 选上` | 上移 | `packages/tui/src/overlays/model-browser.ts:1165` |
| `↓ / 选下` | 下移 | `packages/tui/src/overlays/model-browser.ts:1169` |
| `pageUp/pageDown` | 按 maxVisible 翻页（不环绕） | `packages/tui/src/overlays/model-browser.ts:1173,1177` |
| `home` | 跳到首项 | `packages/tui/src/overlays/model-browser.ts:1181` |
| `end` | 跳到末项 | `packages/tui/src/overlays/model-browser.ts:1185` |
| `enter/return` | 激活选中模型 | `packages/tui/src/overlays/model-browser.ts:1189` |
| `其他键` | 编辑查询（Input） | `packages/tui/src/overlays/model-browser.ts:1196` |
| `鼠标` | wheel 平移窗口/悬停/点击选+再点激活 | `packages/tui/src/overlays/model-browser.ts:1218` |

### overlays/model-hub.ts — ModelHubComponent（共 26 条）
> 数法（payload 原文）：overlays/model-hub.ts — ModelHubComponent 共 26 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `alt+a/ctrl+s 等取消键` | 取消阶梯：strip→分配→查询→关闭 | `packages/tui/src/overlays/model-hub.ts:1758` |
| `tab / shift+tab` | 切换 focus scope↔list | `packages/tui/src/overlays/model-hub.ts:1767` |
| `f5` | 强制刷新 provider 目录 | `packages/tui/src/overlays/model-hub.ts:1771` |
| `alt+left / alt+b` | 上一个角色/类型 tab | `packages/tui/src/overlays/model-hub.ts:1782` |
| `alt+right / alt+f` | 下一个角色/类型 tab | `packages/tui/src/overlays/model-hub.ts:1787` |
| `left` | 焦点=侧栏 | `packages/tui/src/overlays/model-hub.ts:1795` |
| `right` | 焦点=列表 | `packages/tui/src/overlays/model-hub.ts:1799` |
| `scope:↑/↓` | 侧栏上/下移 | `packages/tui/src/overlays/model-hub.ts:1809,1813` |
| `locked:enter` | 请求 provider 登录 | `packages/tui/src/overlays/model-hub.ts:1838` |
| `scope:enter` | 焦点进列表 | `packages/tui/src/overlays/model-hub.ts:1846` |
| `roles:scope enter/space` | 焦点进 Roles 行 | `packages/tui/src/overlays/model-hub.ts:1985` |
| `roles:↑/↓` | 角色行上/下移 | `packages/tui/src/overlays/model-hub.ts:1990,1994` |
| `roles:enter` | pick 当前行 | `packages/tui/src/overlays/model-hub.ts:1998` |
| `roles:backspace/delete` | 清除分配/回退 | `packages/tui/src/overlays/model-hub.ts:2002` |
| `roles:shift+↑` | 当前行前移（earlier） | `packages/tui/src/overlays/model-hub.ts:2008` |
| `roles:shift+↓` | 当前行后移（later） | `packages/tui/src/overlays/model-hub.ts:2013` |
| `roles:x` | 清除（clear） | `packages/tui/src/overlays/model-hub.ts:221,2017` |
| `roles:f` | 新增 fallback | `packages/tui/src/overlays/model-hub.ts:222,2017` |
| `roles:c` | 切换 cycle 成员 | `packages/tui/src/overlays/model-hub.ts:223,2017` |
| `roles:[ / ]` | cycle/链序前/后移 | `packages/tui/src/overlays/model-hub.ts:224,225,2017` |
| `roles:n` | 新建角色 | `packages/tui/src/overlays/model-hub.ts:226,2017` |
| `roles:t` | 设置 thinking | `packages/tui/src/overlays/model-hub.ts:227,2017` |
| `roles:s` | 保存 preset | `packages/tui/src/overlays/model-hub.ts:228,2017` |
| `strip:移动/enter/取消` | chip 选择/激活/关闭 strip | `packages/tui/src/overlays/model-hub.ts:1888,1901` |
| `name strip:enter` | 提交命名 strip | `packages/tui/src/overlays/model-hub.ts:1893` |
| `鼠标` | wheel 侧栏/行，hover，点击 | `packages/tui/src/overlays/model-hub.ts:1748` |

### overlays/model-picker.ts — ModelPickerComponent（alt+p / /switch 浮层）（共 3 条）
> 数法（payload 原文）：overlays/model-picker.ts — ModelPickerComponent（alt+p / /switch 浮层） 共 3 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `SGR 鼠标报告` | 丢弃（非全屏不开 mouse） | `packages/tui/src/overlays/model-picker.ts:276` |
| `taskModeKeys` | 切换 Task 子代理模式 | `packages/tui/src/overlays/model-picker.ts:261` |
| `其他键` | 转发给内嵌 ModelBrowser | `packages/tui/src/overlays/model-picker.ts:283` |

### overlays/move-overlay.ts — MoveOverlay（共 6 条）
> 数法（payload 原文）：overlays/move-overlay.ts — MoveOverlay 共 6 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/ctrl+c/选取消` | 取消 /move | `packages/tui/src/overlays/move-overlay.ts:96` |
| `enter/return` | 确认目录 | `packages/tui/src/overlays/move-overlay.ts:99` |
| `↑ / 选上` | 目录建议上移 | `packages/tui/src/overlays/move-overlay.ts:103` |
| `↓ / 选下` | 目录建议下移 | `packages/tui/src/overlays/move-overlay.ts:114` |
| `tab` | 接受高亮目录 | `packages/tui/src/overlays/move-overlay.ts:127` |
| `其他键` | 编辑路径输入 | `packages/tui/src/overlays/move-overlay.ts:137` |

### overlays/oauth-selector.ts — OAuthSelectorComponent（共 8 条）
> 数法（payload 原文）：overlays/oauth-selector.ts — OAuthSelectorComponent 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/ctrl+c/选取消` | 取消并停止校验 | `packages/tui/src/overlays/oauth-selector.ts:376` |
| `↑ / 选上` | provider 上移（环绕） | `packages/tui/src/overlays/oauth-selector.ts:385` |
| `↓ / 选下` | provider 下移（环绕） | `packages/tui/src/overlays/oauth-selector.ts:390` |
| `pageUp` | 上翻一页 | `packages/tui/src/overlays/oauth-selector.ts:394` |
| `pageDown` | 下翻一页 | `packages/tui/src/overlays/oauth-selector.ts:401` |
| `enter/return` | 确认选中 provider | `packages/tui/src/overlays/oauth-selector.ts:407` |
| `其他键` | 编辑搜索框 | `packages/tui/src/overlays/oauth-selector.ts:288` |
| `鼠标` | wheel ±1 / 点击确认 | `packages/tui/src/overlays/oauth-selector.ts:624` |

### overlays/pause-screen.ts — PauseScreenComponent（共 1 条）
> 数法（payload 原文）：overlays/pause-screen.ts — PauseScreenComponent 共 1 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `app.interrupt/enter/return/space/ctrl+c` | 恢复（结束暂停屏） | `packages/tui/src/overlays/pause-screen.ts:162-166` |

### overlays/plan-review-overlay.ts — PlanReviewOverlay（共 27 条）
> 数法（payload 原文）：overlays/plan-review-overlay.ts — PlanReviewOverlay 共 27 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `标注中:ctrl+g` | 外部编辑器编辑标注 | `packages/tui/src/overlays/plan-review-overlay.ts:540` |
| `标注中:escape/选取消` | 退出标注 | `packages/tui/src/overlays/plan-review-overlay.ts:546` |
| `escape/选取消` | 取消计划审查 | `packages/tui/src/overlays/plan-review-overlay.ts:553` |
| `u` | 撤销上一条标注 | `packages/tui/src/overlays/plan-review-overlay.ts:558` |
| `e` | 编辑当前标注 | `packages/tui/src/overlays/plan-review-overlay.ts:562` |
| `ctrl+g (app.editor.external)` | 打开外部编辑器 | `packages/tui/src/overlays/plan-review-overlay.ts:566` |
| `c` | 复制整份计划 | `packages/tui/src/overlays/plan-review-overlay.ts:570` |
| `tab / \t` | 区域循环 +1 | `packages/tui/src/overlays/plan-review-overlay.ts:574` |
| `shift+tab / \x1b[Z` | 区域循环 -1 | `packages/tui/src/overlays/plan-review-overlay.ts:578` |
| `actions:left/h` | 滑块-1 | `packages/tui/src/overlays/plan-review-overlay.ts:667` |
| `actions:right/l` | 滑块+1 | `packages/tui/src/overlays/plan-review-overlay.ts:668` |
| `actions:↑/k` | 动作上移/退到 body | `packages/tui/src/overlays/plan-review-overlay.ts:677` |
| `actions:↓/j` | 动作下移 | `packages/tui/src/overlays/plan-review-overlay.ts:682` |
| `actions:enter` | 确认当前动作 | `packages/tui/src/overlays/plan-review-overlay.ts:686` |
| `body:a` | 标注正文 | `packages/tui/src/overlays/plan-review-overlay.ts:694` |
| `body:left/h` | 焦点到 ToC | `packages/tui/src/overlays/plan-review-overlay.ts:698` |
| `body:right/l/enter` | 焦点到 actions | `packages/tui/src/overlays/plan-review-overlay.ts:703` |
| `body:↑/k` | 上滚/到顶转 ToC | `packages/tui/src/overlays/plan-review-overlay.ts:715` |
| `body:↓/j` | 下滚/到底转 actions | `packages/tui/src/overlays/plan-review-overlay.ts:724` |
| `body:滚动键` | ScrollView 键 + g/G | `packages/tui/src/overlays/plan-review-overlay.ts:743` |
| `toc:↑/k ↓/j` | 章节光标上/下移 | `packages/tui/src/overlays/plan-review-overlay.ts:759,763` |
| `toc:right/l/enter` | 焦点到 body | `packages/tui/src/overlays/plan-review-overlay.ts:770` |
| `toc:d/delete` | 删除选中章节 | `packages/tui/src/overlays/plan-review-overlay.ts:779` |
| `toc:a` | 标注章节 | `packages/tui/src/overlays/plan-review-overlay.ts:783` |
| `chooser:↑/↓` | 标注选择器上/下 | `packages/tui/src/overlays/plan-review-overlay.ts:968` |
| `chooser:enter` | 打开所选标注 | `packages/tui/src/overlays/plan-review-overlay.ts:975` |
| `鼠标` | wheel ×3、hover、点击选项/ToC/正文 | `packages/tui/src/overlays/plan-review-overlay.ts:604` |

### overlays/plan-save-overlay.ts — PlanSaveOverlay（共 1 条）
> 数法（payload 原文）：overlays/plan-save-overlay.ts — PlanSaveOverlay 共 1 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `全部键` | 转发给路径 Input（submit=enter,cancel=escape） | `packages/tui/src/overlays/plan-save-overlay.ts:56` |

### overlays/plugin-settings.ts — PluginSettingsComponent（含 PluginList/Detail/MarketplaceDetail）（共 4 条）
> 数法（payload 原文）：overlays/plugin-settings.ts — PluginSettingsComponent（含 PluginList/Detail/MarketplaceDetail） 共 4 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape (\x1b/\x1b\x1b)` | 列表未挂载时关闭面板 | `packages/tui/src/overlays/plugin-settings.ts:1029` |
| `其他键` | 转发给当前子视图 | `packages/tui/src/overlays/plugin-settings.ts:1033` |
| `escape/esc` | handleInputOrEscape：输入框取消 | `packages/tui/src/overlays/plugin-settings.ts:172` |
| `鼠标` | 路由给设置字段（顶边框-1,列-2） | `packages/tui/src/overlays/plugin-settings.ts:782` |

### overlays/reset-usage-selector.ts — ResetUsageSelectorComponent（共 5 条）
> 数法（payload 原文）：overlays/reset-usage-selector.ts — ResetUsageSelectorComponent 共 5 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 撤确认提示或取消 | `packages/tui/src/overlays/reset-usage-selector.ts:186` |
| `↑ / 选上` | 账号上移（环绕） | `packages/tui/src/overlays/reset-usage-selector.ts:195` |
| `↓ / 选下` | 账号下移（环绕） | `packages/tui/src/overlays/reset-usage-selector.ts:200` |
| `pageUp/pageDown` | 按 MAX_VISIBLE 翻页 | `packages/tui/src/overlays/reset-usage-selector.ts:206,211` |
| `enter/return` | 激活/二次确认花费 reset | `packages/tui/src/overlays/reset-usage-selector.ts:216` |

### overlays/rewind-selector.ts — RewindSelectorComponent（共 16 条）
> 数法（payload 原文）：overlays/rewind-selector.ts — RewindSelectorComponent 共 16 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 取消回退 | `packages/tui/src/overlays/rewind-selector.ts:359` |
| `f` | 打开分支过滤 | `packages/tui/src/overlays/rewind-selector.ts:363` |
| `ctrl+o (app.tools.expand)` | 展开/折叠工具输出 | `packages/tui/src/overlays/rewind-selector.ts:366` |
| `↑ / 选上` | 上移 | `packages/tui/src/overlays/rewind-selector.ts:372` |
| `↓ / 选下` | 下移 | `packages/tui/src/overlays/rewind-selector.ts:376` |
| `left` | 上一分支/用户回合 | `packages/tui/src/overlays/rewind-selector.ts:379` |
| `right` | 下一分支/用户回合 | `packages/tui/src/overlays/rewind-selector.ts:383` |
| `a / A` | 加载全量历史 | `packages/tui/src/overlays/rewind-selector.ts:387` |
| `enter/return` | 回退到高亮回合 | `packages/tui/src/overlays/rewind-selector.ts:391` |
| `滚动键` | 浏览滚动（不改选择） | `packages/tui/src/overlays/rewind-selector.ts:396` |
| `filter:escape/选取消` | 关闭过滤 | `packages/tui/src/overlays/rewind-selector.ts:458` |
| `filter:enter` | 回退到过滤选中 | `packages/tui/src/overlays/rewind-selector.ts:462` |
| `filter:↑/left` | 过滤结果上移 | `packages/tui/src/overlays/rewind-selector.ts:470` |
| `filter:↓/right` | 过滤结果下移 | `packages/tui/src/overlays/rewind-selector.ts:475` |
| `filter:ctrl+o` | 展开/折叠 | `packages/tui/src/overlays/rewind-selector.ts:468` |
| `filter:backspace(空)` | 关闭过滤 | `packages/tui/src/overlays/rewind-selector.ts:482` |

### overlays/session-info-overlay.ts — SessionInfoOverlay（共 1 条）
> 数法（payload 原文）：overlays/session-info-overlay.ts — SessionInfoOverlay 共 1 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/esc/选取消` | 关闭信息面板 | `packages/tui/src/overlays/session-info-overlay.ts:142` |

### overlays/session-selector.ts — SessionSelectorComponent / SessionList（共 11 条）
> 数法（payload 原文）：overlays/session-selector.ts — SessionSelectorComponent / SessionList 共 11 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `delete / backspace(空查询)` | 请求删除选中会话 | `packages/tui/src/overlays/session-selector.ts:1243` |
| `↑ / 选上` | 上移会话 | `packages/tui/src/overlays/session-selector.ts:1251` |
| `↓ / 选下` | 下移会话 | `packages/tui/src/overlays/session-selector.ts:1257` |
| `pageUp/pageDown` | 按 pageSize 翻页 | `packages/tui/src/overlays/session-selector.ts:1263,1269` |
| `enter/return` | 恢复选中会话 | `packages/tui/src/overlays/session-selector.ts:1275` |
| `app.interrupt` | 取消 | `packages/tui/src/overlays/session-selector.ts:1280` |
| `ctrl+c` | 退出进程 | `packages/tui/src/overlays/session-selector.ts:1287` |
| `tab` | 切换 project/全部项目 scope | `packages/tui/src/overlays/session-selector.ts:1292` |
| `其他键` | 编辑搜索框并过滤 | `packages/tui/src/overlays/session-selector.ts:1297` |
| `鼠标 wheel` | 滚动移动选择 | `packages/tui/src/overlays/session-selector.ts:1893` |
| `鼠标左键` | 点击行选中并确认 | `packages/tui/src/overlays/session-selector.ts:1897` |

### overlays/settings-selector.ts — SettingsSelectorComponent（共 12 条）
> 数法（payload 原文）：overlays/settings-selector.ts — SettingsSelectorComponent 共 12 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/选取消` | 退出搜索到结果所在 tab / 关闭 | `packages/tui/src/overlays/settings-selector.ts:1947` |
| `textInput 子菜单时全部键` | 转给搜索/列表（Tab 不切 tab） | `packages/tui/src/overlays/settings-selector.ts:1895` |
| `子菜单打开时全部键` | 由子菜单独占 | `packages/tui/src/overlays/settings-selector.ts:1903` |
| `tab / shift+tab(常规)` | section↔行 焦点或切 tab | `packages/tui/src/overlays/settings-selector.ts:1915` |
| `left / right(常规)` | 切 tab | `packages/tui/src/overlays/settings-selector.ts:1923` |
| `可打印字符(常规)` | 对全 tab 启动搜索 | `packages/tui/src/overlays/settings-selector.ts:1935` |
| `其他键(常规)` | 当前列表/插件面板处理 | `packages/tui/src/overlays/settings-selector.ts:1941` |
| `search:tab/shift+tab` | 在命中 tab 间跳转 | `packages/tui/src/overlays/settings-selector.ts:1952` |
| `search:选 up/down/page/confirm` | 结果列表导航/确认 | `packages/tui/src/overlays/settings-selector.ts:1958` |
| `search:其他键` | 编辑查询字符串 | `packages/tui/src/overlays/settings-selector.ts:1967` |
| `鼠标` | wheel/hover/click 命中列表项 | `packages/tui/src/overlays/settings-selector.ts:1224` |
| `包装层 routeMouse` | 转发给列表字段 | `packages/tui/src/overlays/settings-selector.ts:344,522` |

### overlays/tree-selector.ts — TreeSelectorComponent / TreeList / LabelInput（共 20 条）
> 数法（payload 原文）：overlays/tree-selector.ts — TreeSelectorComponent / TreeList / LabelInput 共 20 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `↑ / 选上` | 树上移 | `packages/tui/src/overlays/tree-selector.ts:1163` |
| `↓ / 选下` | 树下移 | `packages/tui/src/overlays/tree-selector.ts:1165` |
| `alt+↑/alt+↓` | 跳到上/下一条消息节点 | `packages/tui/src/overlays/tree-selector.ts:1178,1185` |
| `home/end` | 首/末行 | `packages/tui/src/overlays/tree-selector.ts:1192,1194` |
| `pageUp/left` | 上翻页 | `packages/tui/src/overlays/tree-selector.ts:1196` |
| `pageDown/right` | 下翻页 | `packages/tui/src/overlays/tree-selector.ts:1198` |
| `shift+enter/shift+return/LF/\x1b[13;2~` | 摘要式切换（summarize） | `packages/tui/src/overlays/tree-selector.ts:1201-1204` |
| `enter/return` | 切换到选中条目 | `packages/tui/src/overlays/tree-selector.ts:1208` |
| `app.interrupt` | 清搜索，否则关闭 | `packages/tui/src/overlays/tree-selector.ts:1211` |
| `ctrl+c` | 取消 | `packages/tui/src/overlays/tree-selector.ts:1212` |
| `shift+ctrl+o / ctrl+shift+o` | 过滤模式 -1 | `packages/tui/src/overlays/tree-selector.ts:1214` |
| `ctrl+o` | 过滤模式 +1 | `packages/tui/src/overlays/tree-selector.ts:1216` |
| `alt+d` | 过滤=default | `packages/tui/src/overlays/tree-selector.ts:1218` |
| `alt+t` | 过滤=no-tools | `packages/tui/src/overlays/tree-selector.ts:1221` |
| `alt+u` | 过滤=user-only | `packages/tui/src/overlays/tree-selector.ts:1224` |
| `alt+l` | 过滤=labeled-only | `packages/tui/src/overlays/tree-selector.ts:1227` |
| `alt+a` | 过滤=all | `packages/tui/src/overlays/tree-selector.ts:1230` |
| `shift+l(无搜索词)` | 编辑所选条目标签 | `packages/tui/src/overlays/tree-selector.ts:1233` |
| `其他键` | 编辑搜索框 | `packages/tui/src/overlays/tree-selector.ts:1235` |
| `LabelInput:enter/app.interrupt/其他` | 保存标签/取消/转发 Input | `packages/tui/src/overlays/tree-selector.ts:1315,1317,1319` |

### overlays/usage-dashboard.ts — UsageDashboardComponent（共 9 条）
> 数法（payload 原文）：overlays/usage-dashboard.ts — UsageDashboardComponent 共 9 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `wheel` | 滚动 ×2 | `packages/tui/src/overlays/usage-dashboard.ts:1369` |
| `escape/q` | detail→overview，再按关闭 | `packages/tui/src/overlays/usage-dashboard.ts:1377` |
| `r` | 刷新用量数据 | `packages/tui/src/overlays/usage-dashboard.ts:1386` |
| `return/tab/d(overview)` | 进入详情视图 | `packages/tui/src/overlays/usage-dashboard.ts:1392` |
| `↑ / 选上` | 上滚 1 行 | `packages/tui/src/overlays/usage-dashboard.ts:1399` |
| `↓ / 选下` | 下滚 1 行 | `packages/tui/src/overlays/usage-dashboard.ts:1400` |
| `pageUp/pageDown` | 按视口翻页 | `packages/tui/src/overlays/usage-dashboard.ts:1400` |
| `home` | 滚到顶 | `packages/tui/src/overlays/usage-dashboard.ts:1401` |
| `end` | 滚到底 | `packages/tui/src/overlays/usage-dashboard.ts:1404` |

### overlays/extensions/extension-dashboard.ts — ExtensionDashboard（共 8 条）
> 数法（payload 原文）：overlays/extensions/extension-dashboard.ts — ExtensionDashboard 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+c` | 立即关闭 | `packages/tui/src/overlays/extensions/extension-dashboard.ts:557` |
| `escape (app.interrupt)` | 清搜索，否则关闭 | `packages/tui/src/overlays/extensions/extension-dashboard.ts:563` |
| `ctrl+o (app.tools.expand)` | 展开/折叠 inspector | `packages/tui/src/overlays/extensions/extension-dashboard.ts:572` |
| `pageUp/pageDown` | inspector 翻页 | `packages/tui/src/overlays/extensions/extension-dashboard.ts:578` |
| `tab/shift+tab / left/right` | 切换 provider tab | `packages/tui/src/overlays/extensions/extension-dashboard.ts:588` |
| `其他键` | 转发给主列表 | `packages/tui/src/overlays/extensions/extension-dashboard.ts:593` |
| `鼠标` | wheel 列表/inspector、点击、hover | `packages/tui/src/overlays/extensions/extension-dashboard.ts:551,310` |
| `native picker` | 指针动作同键位 | `packages/tui/src/overlays/extensions/extension-dashboard.ts:760` |

### overlays/extensions/extension-list.ts — ExtensionList（共 4 条）
> 数法（payload 原文）：overlays/extensions/extension-list.ts — ExtensionList 共 4 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `↑ / 选上` | 上移（j/k 不导航，留给搜索） | `packages/tui/src/overlays/extensions/extension-list.ts:888` |
| `↓ / 选下` | 下移 | `packages/tui/src/overlays/extensions/extension-list.ts:893` |
| `space/enter/return` | 激活选中行（切换开关） | `packages/tui/src/overlays/extensions/extension-list.ts:899` |
| `其他键` | 编辑搜索框并过滤 | `packages/tui/src/overlays/extensions/extension-list.ts:906` |

### overlays/ — 委派型选择器（自身无 handleInput，键位=SelectList；均支持鼠标 routeMouse）（共 6 条）
> 数法（payload 原文）：overlays/ — 委派型选择器（自身无 handleInput，键位=SelectList；均支持鼠标 routeMouse） 共 6 面板，36 键行归到 select-list 组

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ThemeSelectorComponent` | 主题选择：SelectList 键 + routeMouse | `packages/tui/src/overlays/theme-selector.ts:29,89` |
| `ThinkingSelectorComponent` | 思考等级：SelectList 键 + routeMouse | `packages/tui/src/overlays/thinking-selector.ts:13,69` |
| `ShowImagesSelectorComponent` | 图片开关：SelectList 键 + routeMouse | `packages/tui/src/overlays/show-images-selector.ts:11,58` |
| `QueueModeSelectorComponent` | 队列模式：SelectList 键 + routeMouse | `packages/tui/src/overlays/queue-mode-selector.ts:11,70` |
| `PluginSelectorComponent` | 插件选择：SelectList 键 + routeMouse | `packages/tui/src/overlays/plugin-selector.ts:26,104` |
| `SessionAccountSelectorComponent` | 账号选择：handleInput 转发 SelectList + routeMouse | `packages/tui/src/overlays/session-account-selector.ts:23,65` |

### apps/ps-top.ts — PsTopComponent（omp ps 进程表）（共 12 条）
> 数法（payload 原文）：apps/ps-top.ts — PsTopComponent（omp ps 进程表） 共 12 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+c` | 退出 | `packages/tui/src/apps/ps-top.ts:249` |
| `escape/q(非 table 视图)` | 关闭详情/日志视图 | `packages/tui/src/apps/ps-top.ts:254` |
| `escape/q(table)` | 退出 | `packages/tui/src/apps/ps-top.ts:257` |
| `↑ / k` | 选中上移 | `packages/tui/src/apps/ps-top.ts:261` |
| `↓ / j` | 选中下移 | `packages/tui/src/apps/ps-top.ts:262` |
| `a` | 切换 current/all scope | `packages/tui/src/apps/ps-top.ts:263` |
| `enter / i` | 打开进程信息 | `packages/tui/src/apps/ps-top.ts:264` |
| `l` | 打开日志视图 | `packages/tui/src/apps/ps-top.ts:265` |
| `s` | 停止进程 | `packages/tui/src/apps/ps-top.ts:266` |
| `x` | 杀掉进程（立即） | `packages/tui/src/apps/ps-top.ts:267` |
| `r` | 重启进程 | `packages/tui/src/apps/ps-top.ts:268` |
| `native 指针` | 点击选择、双击 info、action bar（Kill 需确认） | `packages/tui/src/apps/ps-top.ts:288` |

### apps/live-visualizer.ts — LiveVisualizer（共 4 条）
> 数法（payload 原文）：apps/live-visualizer.ts — LiveVisualizer 共 4 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape` | 停止可视器 | `packages/tui/src/apps/live-visualizer.ts:138` |
| `ctrl+c` | 停止可视器 | `packages/tui/src/apps/live-visualizer.ts:139` |
| `stopKeys(宿主注入)` | 停止可视器 | `packages/tui/src/apps/live-visualizer.ts:140` |
| `space` | 切换静音 | `packages/tui/src/apps/live-visualizer.ts:143` |

### apps/autoresearch-dashboard.ts — 匿名 Dashboard 组件（共 5 条）
> 数法（payload 原文）：apps/autoresearch-dashboard.ts — 匿名 Dashboard 组件 共 5 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/esc/q` | 关闭面板 | `packages/tui/src/apps/autoresearch-dashboard.ts:218` |
| `↑ / k` | 向上滚动 | `packages/tui/src/apps/autoresearch-dashboard.ts:222` |
| `↓ / j` | 向下滚动 | `packages/tui/src/apps/autoresearch-dashboard.ts:224` |
| `pageUp/pageDown` | 翻页 | `packages/tui/src/apps/autoresearch-dashboard.ts:226,228` |
| `g` | 滚到顶部 | `packages/tui/src/apps/autoresearch-dashboard.ts:230` |

### apps/git/git-tui.ts — GitTuiComponent（git TUI）（共 24 条）
> 数法（payload 原文）：apps/git/git-tui.ts — GitTuiComponent（git TUI） 共 24 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+c` | 退出 | `packages/tui/src/apps/git/git-tui.ts:615` |
| `tab / shift+tab` | 切焦点 diff↔sidebar | `packages/tui/src/apps/git/git-tui.ts:620` |
| `escape` | 侧栏退编辑/清 diff 选择 | `packages/tui/src/apps/git/git-tui.ts:624` |
| `q` | 退出 | `packages/tui/src/apps/git/git-tui.ts:635` |
| `alt+↓ / super+alt+↓` | 下一个 hunk/文件 | `packages/tui/src/apps/git/git-tui.ts:640` |
| `alt+↑ / super+alt+↑` | 上一个 hunk/文件 | `packages/tui/src/apps/git/git-tui.ts:641` |
| `]` | 下一个文件 | `packages/tui/src/apps/git/git-tui.ts:642` |
| `[` | 上一个文件 | `packages/tui/src/apps/git/git-tui.ts:643` |
| `v` | 循环视图模式 | `packages/tui/src/apps/git/git-tui.ts:644` |
| `1/2/3/4` | file/split/inline/hunk 视图 | `packages/tui/src/apps/git/git-tui.ts:649` |
| `w` | 切换自动换行 | `packages/tui/src/apps/git/git-tui.ts:653` |
| `b` | 循环空白显示 | `packages/tui/src/apps/git/git-tui.ts:658` |
| `r` | 刷新 | `packages/tui/src/apps/git/git-tui.ts:659` |
| `?` | 帮助浮层 | `packages/tui/src/apps/git/git-tui.ts:660` |
| `c` | 聚焦提交表单 | `packages/tui/src/apps/git/git-tui.ts:661` |
| `diff:shift+↑/↓` | 选择光标 ±1（带选区） | `packages/tui/src/apps/git/git-tui.ts:667,668` |
| `diff:↑/k ↓/j` | 光标 ±1 | `packages/tui/src/apps/git/git-tui.ts:669,670` |
| `diff:pageUp/pageDown/space` | 光标翻页 | `packages/tui/src/apps/git/git-tui.ts:671,672` |
| `diff:left/h right/l` | 水平滚动 ±8 | `packages/tui/src/apps/git/git-tui.ts:674,675` |
| `diff:home/g, end/G` | 光标到首/尾 | `packages/tui/src/apps/git/git-tui.ts:676,677` |
| `diff:enter` | 跳到下一 hunk/文件 | `packages/tui/src/apps/git/git-tui.ts:678` |
| `diff:s/u` | 暂存/取消暂存（行或 hunk） | `packages/tui/src/apps/git/git-tui.ts:679` |
| `diff:x` | 丢弃（行或 hunk） | `packages/tui/src/apps/git/git-tui.ts:687` |
| `diff:delete` | 丢弃当前文件 | `packages/tui/src/apps/git/git-tui.ts:696` |

### apps/git/sidebar.ts — Sidebar（共 19 条）
> 数法（payload 原文）：apps/git/sidebar.ts — Sidebar 共 19 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `editing 字段时:↑/↓` | 移动选择而非改光标 | `packages/tui/src/apps/git/sidebar.ts:877,887,898` |
| `editing 字段时:其他键` | 转发给 aiInput/summary/description | `packages/tui/src/apps/git/sidebar.ts:880,890,901` |
| `↑ / k` | 上移 | `packages/tui/src/apps/git/sidebar.ts:907` |
| `↓ / j` | 下移 | `packages/tui/src/apps/git/sidebar.ts:908` |
| `left / h` | 折叠/父节点 | `packages/tui/src/apps/git/sidebar.ts:909` |
| `right / l` | 展开/打开 | `packages/tui/src/apps/git/sidebar.ts:910` |
| `home / g` | 到首 | `packages/tui/src/apps/git/sidebar.ts:911` |
| `end / G` | 到末 | `packages/tui/src/apps/git/sidebar.ts:912` |
| `pageUp/pageDown` | 翻页 | `packages/tui/src/apps/git/sidebar.ts:913,914` |
| `enter` | 打开文件（聚焦 diff）/激活 | `packages/tui/src/apps/git/sidebar.ts:915` |
| `space` | 暂存/取消暂存（文件/目录/段） | `packages/tui/src/apps/git/sidebar.ts:927` |
| `s` | 暂存 | `packages/tui/src/apps/git/sidebar.ts:929` |
| `u` | 取消暂存 | `packages/tui/src/apps/git/sidebar.ts:929` |
| `delete` | 丢弃文件/目录 | `packages/tui/src/apps/git/sidebar.ts:930` |
| `t` | 切换 tree/path 视图 | `packages/tui/src/apps/git/sidebar.ts:933` |
| `pageUp/pageDown(字段焦点)` | 字段内不拦截翻页 | `packages/tui/src/apps/git/sidebar.ts:879,889,900` |
| `wheel` | 滚轮（git-tui 路由） | `packages/tui/src/apps/git/sidebar.ts:713(git-tui)` |
| `handleClick` | 点击行（git-tui 路由） | `packages/tui/src/apps/git/sidebar.ts` |
| `editing 字段提交/取消` | 由 summary/description/aiInput 内部处理 | `packages/tui/src/apps/git/sidebar.ts:876-903` |

### apps/git/help.ts — GitHelpSheet（共 3 条）
> 数法（payload 原文）：apps/git/help.ts — GitHelpSheet 共 3 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `?` | 关闭快捷键浮层 | `packages/tui/src/apps/git/help.ts:79` |
| `q` | 关闭 | `packages/tui/src/apps/git/help.ts:79` |
| `escape/ctrl+c` | 关闭 | `packages/tui/src/apps/git/help.ts:79` |

### apps/debug/log-viewer.ts — DebugLogViewerComponent（共 15 条）
> 数法（payload 原文）：apps/debug/log-viewer.ts — DebugLogViewerComponent 共 15 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/esc` | 退出 | `packages/tui/src/apps/debug/log-viewer.ts:608` |
| `ctrl+c` | 复制选中行 | `packages/tui/src/apps/debug/log-viewer.ts:613` |
| `ctrl+p` | 切换进程过滤 | `packages/tui/src/apps/debug/log-viewer.ts:618` |
| `ctrl+a` | 全选可见行 | `packages/tui/src/apps/debug/log-viewer.ts:624` |
| `ctrl+o` | 加载更旧一批 | `packages/tui/src/apps/debug/log-viewer.ts:630` |
| `enter/return` | 加载更旧行 | `packages/tui/src/apps/debug/log-viewer.ts:636` |
| `shift+↑/↓` | 带选区的光标移动 | `packages/tui/src/apps/debug/log-viewer.ts:644,650` |
| `↑ / ↓` | 光标上/下移 | `packages/tui/src/apps/debug/log-viewer.ts:656,662` |
| `pageUp/pageDown` | 按正文高度跳转 | `packages/tui/src/apps/debug/log-viewer.ts:670,672` |
| `home/end` | 首/末行 | `packages/tui/src/apps/debug/log-viewer.ts:674,676` |
| `right` | 加载更旧/展开 | `packages/tui/src/apps/debug/log-viewer.ts:686` |
| `left` | 折叠当前行 | `packages/tui/src/apps/debug/log-viewer.ts:696` |
| `其他键` | 编辑过滤器 Input | `packages/tui/src/apps/debug/log-viewer.ts:704` |
| `鼠标 wheel` | 滚动 ×3 | `packages/tui/src/apps/debug/log-viewer.ts:713` |
| `鼠标左键` | 点击行切换展开/选择 | `packages/tui/src/apps/debug/log-viewer.ts:712` |

### apps/debug/raw-sse.ts — RawSseViewerComponent（共 8 条）
> 数法（payload 原文）：apps/debug/raw-sse.ts — RawSseViewerComponent 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `escape/esc` | 关闭 | `packages/tui/src/apps/debug/raw-sse.ts:147` |
| `ctrl+c` | 复制全部原始流 | `packages/tui/src/apps/debug/raw-sse.ts:152` |
| `↑ / ↓` | 行滚动 | `packages/tui/src/apps/debug/raw-sse.ts:157,159` |
| `pageUp/pageDown` | 翻页 | `packages/tui/src/apps/debug/raw-sse.ts:161,163` |
| `home` | 滚到开头 | `packages/tui/src/apps/debug/raw-sse.ts:165` |
| `end` | 跟随尾部 | `packages/tui/src/apps/debug/raw-sse.ts:167` |
| `鼠标 wheel` | 滚动 ×3 | `packages/tui/src/apps/debug/raw-sse.ts:204` |
| `鼠标左键(表头/正文)` | 表头切换跟随尾部/点击正文定位 | `packages/tui/src/apps/debug/raw-sse.ts:214` |

### components/select-list.ts — SelectList（共享选择器底座，被 6+ overlay 复用）（共 9 条）
> 数法（payload 原文）：components/select-list.ts — SelectList（共享选择器底座，被 6+ overlay 复用） 共 8 键行 + 鼠标

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `选取消 (escape/ctrl+c)` | 撤销待确认，否则 onCancel | `packages/tui/src/components/select-list.ts:491` |
| `可打印/搜索键` | 优先作为过滤搜索输入 | `packages/tui/src/components/select-list.ts:519` |
| `选上 (↑)` | 选择上移（可环绕） | `packages/tui/src/components/select-list.ts:509` |
| `选下 (↓)` | 选择下移 | `packages/tui/src/components/select-list.ts:511` |
| `pageUp/pageDown` | 按 maxVisible 翻页 | `packages/tui/src/components/select-list.ts:513,515` |
| `home/end` | 首/末项 | `packages/tui/src/components/select-list.ts:516,518` |
| `确认 (enter / LF)` | 激活选中项 | `packages/tui/src/components/select-list.ts:520` |
| `其他键` | 转发给搜索 Input | `packages/tui/src/components/select-list.ts:521` |
| `鼠标 wheel/click` | 滚轮移动±1；点击命中选中/激活 | `packages/tui/src/components/select-list.ts:276,289` |

### components/settings-list.ts — SettingsList / SettingsFormField（共 7 条）
> 数法（payload 原文）：components/settings-list.ts — SettingsList / SettingsFormField 共 7 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `子菜单打开` | 全部键交给子菜单 | `packages/tui/src/components/settings-list.ts:1002` |
| `选取消 (escape/ctrl+c)` | 清搜索→退段焦点→onCancel | `packages/tui/src/components/settings-list.ts:1013` |
| `搜索输入` | 优先编辑过滤查询 | `packages/tui/src/components/settings-list.ts:1027` |
| `选上/选下` | 段焦点跳段，否则移动选择 | `packages/tui/src/components/settings-list.ts:1035,1038` |
| `pageDown/pageUp` | 跳段（±1） | `packages/tui/src/components/settings-list.ts:1041,1043` |
| `确认 / space / LF` | 段焦点退出，否则激活项（开子菜单/循环值） | `packages/tui/src/components/settings-list.ts:1045` |
| `wheel` | 滚轮移动选择/回焦点到行 | `packages/tui/src/components/settings-list.ts:396,404` |

### components/input.ts — Input（共享单行输入）（共 16 条）
> 数法（payload 原文）：components/input.ts — Input（共享单行输入） 共 16 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `选取消` | 有 onEscape 才消费 | `packages/tui/src/components/input.ts:169` |
| `undo (ctrl+-/ctrl+_)` | 撤销 | `packages/tui/src/components/input.ts:176` |
| `submit (enter / LF)` | 提交（有 onSubmit 才消费） | `packages/tui/src/components/input.ts:182` |
| `deleteCharBackward` | 退格（含 shift+backspace） | `packages/tui/src/components/input.ts:189` |
| `deleteCharForward` | 前向删除 | `packages/tui/src/components/input.ts:193` |
| `deleteWordBackward/Forward` | 按词删除 | `packages/tui/src/components/input.ts:197,202` |
| `deleteToLineStart/End` | 删到行首/行尾 | `packages/tui/src/components/input.ts:206,211` |
| `yank / yankPop` | kill-ring 粘贴/循环 | `packages/tui/src/components/input.ts:216,220` |
| `cursorLeft/Right` | 光标按字素左右 | `packages/tui/src/components/input.ts:226,238` |
| `cursorLineStart/End` | 到行首/行尾 | `packages/tui/src/components/input.ts:250,256` |
| `cursorWordLeft/Right` | 按词左右 | `packages/tui/src/components/input.ts:262,267` |
| `space(spaceHold)` | 按住空格触发/停止 STT | `packages/tui/src/components/input.ts:158` |
| `可打印文本` | 插入字符 | `packages/tui/src/components/input.ts:273` |
| `bracketed paste` | 粘贴（去换行/控制符） | `packages/tui/src/components/input.ts:147` |
| `native edit` | 终端侧选择编辑 | `packages/tui/src/components/input.ts:293` |
| `其他键` | 返回 false 交给宿主 | `packages/tui/src/components/input.ts:274` |

### components/form.ts — Form / FormField / TextFormField / SelectFormField（共 4 条）
> 数法（payload 原文）：components/form.ts — Form / FormField / TextFormField / SelectFormField 共 4 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `取消（isCancel 或 tui.select.cancel）` | onCancel | `packages/tui/src/components/form.ts:579` |
| `tab / shift+tab（多字段）` | 字段焦点 ±1（环绕） | `packages/tui/src/components/form.ts:584` |
| `其他键` | 转发给当前字段 | `packages/tui/src/components/form.ts:590` |
| `鼠标点击` | 命中字段即改焦点并转发 | `packages/tui/src/components/form.ts:597` |

### components/scroll-view.ts — ScrollView.handleScrollKey（共享滚动）（共 8 条）
> 数法（payload 原文）：components/scroll-view.ts — ScrollView.handleScrollKey（共享滚动） 共 8 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `shift+↑/↓` | 快速滚动 fastScrollLines | `packages/tui/src/components/scroll-view.ts:369,373` |
| `↑ / ↓` | 滚动 1 行 | `packages/tui/src/components/scroll-view.ts:377,381` |
| `pageUp/pageDown` | 翻页 | `packages/tui/src/components/scroll-view.ts:385,389` |
| `home` | 滚到顶 | `packages/tui/src/components/scroll-view.ts:393` |
| `end` | 滚到底 | `packages/tui/src/components/scroll-view.ts:397` |
| `（上面两项按行计）` | handleScrollKey 返回是否消费 | `packages/tui/src/components/scroll-view.ts:368` |
| `（无键时）` | 返回 false 由宿主处理 | `packages/tui/src/components/scroll-view.ts:368` |
| `（鼠标）` | 无自身鼠标处理 | `packages/tui/src/components/scroll-view.ts` |

### components/tab-bar.ts — TabBar（共 2 条）
> 数法（payload 原文）：components/tab-bar.ts — TabBar 共 2 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tab / right` | 下一个 tab | `packages/tui/src/components/tab-bar.ts:211` |
| `shift+tab / left` | 上一个 tab | `packages/tui/src/components/tab-bar.ts:215` |

### components/cancellable-loader.ts — CancellableLoader（共 1 条）
> 数法（payload 原文）：components/cancellable-loader.ts — CancellableLoader 共 1 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `选取消 (escape/ctrl+c)` | abort 当前操作 | `packages/tui/src/components/cancellable-loader.ts:38` |

### components/editor.ts — Editor（重型共享编辑器，硬编码字面量）（共 30 条）
> 数法（payload 原文）：components/editor.ts — Editor（重型共享编辑器，硬编码字面量） 共 30 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `ctrl+c` | 保留给父组件（编辑器不消费） | `packages/tui/src/components/editor.ts:1830` |
| `ctrl+a` | 移到行首 | `packages/tui/src/components/editor.ts:2061` |
| `ctrl+e` | 移到行尾 | `packages/tui/src/components/editor.ts:2065` |
| `alt+enter` | onAltEnter 或插入换行 | `packages/tui/src/components/editor.ts:2069` |
| `ctrl+enter/\x1b\r/\x1b[13;2~` | 插入换行（受 submit 绑定门控） | `packages/tui/src/components/editor.ts:2084-2086` |
| `shift+backspace` | 退格 | `packages/tui/src/components/editor.ts:2140` |
| `deleteCharForward / shift+delete` | 前向删除 | `packages/tui/src/components/editor.ts:2159` |
| `shift+space` | 插入普通空格 | `packages/tui/src/components/editor.ts:2204` |
| `enter/\n（submit）` | 提交（disableSubmit 时禁用） | `packages/tui/src/components/editor.ts:3313,2084` |
| `tui.editor.undo` | 撤销 | `packages/tui/src/components/editor.ts:1840` |
| `tui.editor.spellingSuggestions` | 拼写建议 | `packages/tui/src/components/editor.ts:1845` |
| `tui.select.* / tui.input.*` | 自动补全弹窗导航/接受 | `packages/tui/src/components/editor.ts:1866-1960` |
| `tui.input.tab` | 上下文补全 | `packages/tui/src/components/editor.ts:2042` |
| `tui.editor.deleteToLineEnd/Start` | 删到行尾/行首 | `packages/tui/src/components/editor.ts:2012,2016` |
| `tui.editor.deleteWordBackward/Forward` | 按词删除 | `packages/tui/src/components/editor.ts:2024,2032` |
| `tui.editor.yank/yankPop` | kill-ring | `packages/tui/src/components/editor.ts:2036,2040` |
| `tui.editor.cursorLineStart/End` | 到行首/行尾 | `packages/tui/src/components/editor.ts:2143,2145` |
| `tui.editor.pageUp/pageDown` | 视口翻页（不取历史） | `packages/tui/src/components/editor.ts:2152,2154` |
| `tui.editor.cursorWordLeft/Right` | 按词移动 | `packages/tui/src/components/editor.ts:2165,2169` |
| `tui.editor.cursorUp` | 上：历史/光标/行首 | `packages/tui/src/components/editor.ts:2174` |
| `tui.editor.cursorDown` | 下：历史/光标/行尾 | `packages/tui/src/components/editor.ts:2191` |
| `tui.editor.cursorRight` | 右（先接受幽灵补全） | `packages/tui/src/components/editor.ts:2199` |
| `tui.editor.cursorLeft` | 左 | `packages/tui/src/components/editor.ts:2201` |
| `tui.editor.jumpForward/Backward` | 字符跳转模式 | `packages/tui/src/components/editor.ts:2208,2210` |
| `其他可打印` | 插入字符 | `packages/tui/src/components/editor.ts:2214` |
| `（Vim 模态）` | vim 命令优先于上方分发（src/vim.ts） | `packages/tui/src/components/editor.ts:1838,2222` |
| `bracketed paste` | 粘贴剩余回环处理 | `packages/tui/src/components/editor.ts:1800` |
| `批量纯文本快路径` | 多字符一次插入 | `packages/tui/src/components/editor.ts:1823` |
| `esc（Vim 模式）` | Insert→Normal/取消算子 | `packages/tui/src/components/editor.ts:2224` |
| `（提交键注册表）` | tui.input.submit 加 shift+enter 时判定 | `packages/tui/src/components/editor.ts:3313` |

### 无键位文件（纯渲染 / helper / 类型）（共 42 条）
> 数法（payload 原文）：无键位文件（纯渲染 / helper / 类型；判据：grep matchesKey|handleInput|kb.matches|startsWith(\x1b[<) 全空） 共列出 45 个

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `overlays/agent-activity.ts` | agent 活动聚合（无渲染交互） | `packages/tui/src/overlays/agent-activity.ts` |
| `overlays/agent-hub-projection.ts` | hub 数据投影 helper | `packages/tui/src/overlays/agent-hub-projection.ts` |
| `overlays/agent-hub-renderer.ts` | hub 行渲染 helper | `packages/tui/src/overlays/agent-hub-renderer.ts` |
| `overlays/agent-hub-types.ts` | 类型定义 | `packages/tui/src/overlays/agent-hub-types.ts` |
| `overlays/annotation-types.ts` | 标注类型 | `packages/tui/src/overlays/annotation-types.ts` |
| `overlays/btw-history.ts` | btw 历史 helper | `packages/tui/src/overlays/btw-history.ts` |
| `overlays/composer-shape-preview.ts` | 输入框形状预览渲染 | `packages/tui/src/overlays/composer-shape-preview.ts` |
| `overlays/composer-shape-registry.ts` | 形状注册表 | `packages/tui/src/overlays/composer-shape-registry.ts` |
| `overlays/copy-targets.ts` | 复制目标抽取 helper | `packages/tui/src/overlays/copy-targets.ts` |
| `overlays/plan-toc.ts` | 计划目录 helper | `packages/tui/src/overlays/plan-toc.ts` |
| `overlays/running-subagent-badge.ts` | 运行子代理徽标渲染 | `packages/tui/src/overlays/running-subagent-badge.ts` |
| `overlays/session-observer-registry.ts` | 会话观察注册表 | `packages/tui/src/overlays/session-observer-registry.ts` |
| `overlays/settings-defs.ts` | 设置项定义 | `packages/tui/src/overlays/settings-defs.ts` |
| `overlays/snapcompact-shape-preview.ts` | 快照压缩形状预览渲染 | `packages/tui/src/overlays/snapcompact-shape-preview.ts` |
| `overlays/stats-notice.ts` | /stats 提示（native Open 按钮） | `packages/tui/src/overlays/stats-notice.ts` |
| `overlays/usage-display.ts` | 用量展示 helper | `packages/tui/src/overlays/usage-display.ts` |
| `overlays/usage-row.ts` | TurnUsageTally 统计 helper | `packages/tui/src/overlays/usage-row.ts` |
| `overlays/model-selector.ts` | 模型串解析 helper（非面板） | `packages/tui/src/overlays/model-selector.ts` |
| `overlays/error-banner.ts` | 错误条：仅 native Details/Dismiss 动作，无键盘 | `packages/tui/src/overlays/error-banner.ts:84` |
| `overlays/btw-panel.ts` | btw 运行面板：仅 hint 文本（interrupt） | `packages/tui/src/overlays/btw-panel.ts:167` |
| `overlays/cleanse-panel.ts` | cleanse 运行面板：仅 hint 文本 | `packages/tui/src/overlays/cleanse-panel.ts:219` |
| `overlays/omfg-panel.ts` | omfg 运行面板：仅 hint 文本 | `packages/tui/src/overlays/omfg-panel.ts:159` |
| `overlays/extensions/display-text.ts` | 显示文本净化 helper | `packages/tui/src/overlays/extensions/display-text.ts` |
| `overlays/extensions/inspector-model.ts` | inspector 数据模型 | `packages/tui/src/overlays/extensions/inspector-model.ts` |
| `overlays/extensions/inspector-panel.ts` | inspector 渲染（toggleExpanded 由父调） | `packages/tui/src/overlays/extensions/inspector-panel.ts` |
| `overlays/extensions/live-tool-session.ts` | 工具运行时快照 helper | `packages/tui/src/overlays/extensions/live-tool-session.ts` |
| `overlays/extensions/mcp-runtime.ts` | MCP 运行时快照 helper | `packages/tui/src/overlays/extensions/mcp-runtime.ts` |
| `overlays/extensions/state-manager.ts` | 扩展状态管理 helper | `packages/tui/src/overlays/extensions/state-manager.ts` |
| `overlays/extensions/types.ts` | 类型定义 | `packages/tui/src/overlays/extensions/types.ts` |
| `apps/cleanse-board.ts` | cleanse 看板模型（渲染） | `packages/tui/src/apps/cleanse-board.ts` |
| `apps/if-bench-board.ts` | if-bench 看板渲染 | `packages/tui/src/apps/if-bench-board.ts` |
| `apps/ps-data.ts` | 进程数据 helper | `packages/tui/src/apps/ps-data.ts` |
| `apps/autoresearch-data.ts` | autoresearch 数据 helper | `packages/tui/src/apps/autoresearch-data.ts` |
| `apps/git/diff-pane.ts` | diff 渲染（键位在 git-tui） | `packages/tui/src/apps/git/diff-pane.ts` |
| `apps/git/{avatar,state,colors}.ts` | 头像/状态/颜色 helper | `packages/tui/src/apps/git/` |
| `apps/debug/{protocol-probe,raw-sse-buffer,terminal-info,viewer-frame,log-formatting}.ts` | 调试渲染/缓冲 helper | `packages/tui/src/apps/debug/` |
| `components/{text,truncated-text,spacer,section,table,tree-view,markdown,loader,progress-bar,metric,image,key-value-list,box,scroll-viewport}.ts` | 纯渲染/布局 helper | `packages/tui/src/components/` |
| `components/menu-selection.ts` | 选择模型（无键，键在宿主） | `packages/tui/src/components/menu-selection.ts` |
| `components/disclosure.ts` | 折叠：仅 native toggle | `packages/tui/src/components/disclosure.ts:170` |
| `components/wizard-step.ts` | 转发 content + routeMouse | `packages/tui/src/components/wizard-step.ts:149` |
| `components/layout/{stack,row,split-pane,geometry}.ts` | 布局 + 纯鼠标路由 | `packages/tui/src/components/layout/` |
| `components/composer/*.ts` | composer 形状定义/渲染 | `packages/tui/src/components/composer/` |

## 42. vim 与编辑器动作（共 133 条）

### ① vim.ts — 模式与完整命令表（共 76 条）
> 数法（payload 原文）：① vim.ts — 模式与完整命令表（共 79 条：4 模式 + 75 键/命令；按 handleKey → #resolveMotion → 模式分支 → #resolveTextObject → #operate 逐分支数）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `mode: insert` | 插入模式：vim.handleKey 对除 escape 外的所有键返回 null，全部交回宿主编辑器正常输入/编辑。 | `packages/tui/src/vim.ts:20,336` |
| `mode: normal` | 默认模式（reset/setVimMode 初始进入）；未知可打印键被吞掉而非写入缓冲区。 | `packages/tui/src/vim.ts:20,268-270,686-690` |
| `mode: visual` | 字符级可视选择；anchor 固定，光标为移动端。 | `packages/tui/src/vim.ts:20,629-634` |
| `mode: visual-line` | 行级可视选择（V 或 vip 提升而来）。 | `packages/tui/src/vim.ts:20,629-634,575-578` |
| `escape` | 有半成品命令时清空 pending；否则 visual→normal；否则 insert→normal 且光标退一个字形；normal 且空闲时返回 null 交宿主（中断/清草稿）。 | `packages/tui/src/vim.ts:335,378-399` |
| `1-9（count 前缀）` | 累加计数前缀，作为后续动作的 count。 | `packages/tui/src/vim.ts:339-342` |
| `0（续接 count）` | 仅当已在输入 count 时把 0 追加进 count，否则作为行首动作。 | `packages/tui/src/vim.ts:340,428` |
| `g` | 置 #pendingG 等待第二个 g；不是 g 则清空 pending。 | `packages/tui/src/vim.ts:593-594,349-354` |
| `gg / [count]gg` | 跳到第 1 行 / 第 count 行。 | `packages/tui/src/vim.ts:349-356` |
| `i / a（操作符后或 visual 中）` | 进入 text-object 前缀，等待下一个对象键（如 diw、vi"）。 | `packages/tui/src/vim.ts:362-366` |
| `h` | 光标左移 count 个字形。 | `packages/tui/src/vim.ts:409-413` |
| `l` | 光标右移 count 个字形。 | `packages/tui/src/vim.ts:414-418` |
| `space` | 等价于 l（右移）。 | `packages/tui/src/vim.ts:408` |
| `j` | 下移 count 行，记忆 desired column。 | `packages/tui/src/vim.ts:419-427` |
| `k` | 上移 count 行，记忆 desired column。 | `packages/tui/src/vim.ts:419-427` |
| `0` | 移到行首。 | `packages/tui/src/vim.ts:428-429` |
| `^` | 移到本行第一个非空白。 | `packages/tui/src/vim.ts:430-431` |
| `$` | 移到行尾（desired column 设为 Infinity，$j 每行都停行尾）。 | `packages/tui/src/vim.ts:432-435` |
| `w` | 前进 count 个词；operator 为 c 且站在非空白上时按 ce 语义停在词尾。 | `packages/tui/src/vim.ts:436-446` |
| `b` | 后退 count 个词。 | `packages/tui/src/vim.ts:447-451` |
| `e` | 移到 count 个词的词尾（inclusive 动作）。 | `packages/tui/src/vim.ts:452-456` |
| `G` | 有 count 跳第 count 行，否则跳最后一行。 | `packages/tui/src/vim.ts:457-464` |
| `i（normal，无操作符）` | 在光标前进入 insert。 | `packages/tui/src/vim.ts:596-599` |
| `a（normal，无操作符）` | 光标右移一个字形后进入 insert。 | `packages/tui/src/vim.ts:600-606` |
| `I（normal）` | 移到第一个非空白并进入 insert。 | `packages/tui/src/vim.ts:607-613` |
| `A（normal）` | 移到行尾并进入 insert。 | `packages/tui/src/vim.ts:614-620` |
| `o（normal）` | 在下方开新行并进入 insert。 | `packages/tui/src/vim.ts:621-628` |
| `O（normal）` | 在上方开新行并进入 insert。 | `packages/tui/src/vim.ts:621-628` |
| `v（normal）` | 进入字符级 visual，anchor=当前光标。 | `packages/tui/src/vim.ts:629-634` |
| `V（normal）` | 进入行级 visual（visual-line）。 | `packages/tui/src/vim.ts:629-634` |
| `x（normal）` | 删除光标起 count 个字形。 | `packages/tui/src/vim.ts:635-649` |
| `D（normal）` | 删除光标到行尾（count-1 个额外整行）。 | `packages/tui/src/vim.ts:650-662` |
| `C（normal）` | 改光标到行尾并进入 insert（count 同 D）。 | `packages/tui/src/vim.ts:650-662` |
| `d（normal）` | 操作符 d；再次按 d（dd）按 count 行 linewise 删除。 | `packages/tui/src/vim.ts:663-679` |
| `y（normal）` | 操作符 y；yy 按 count 行 linewise 复制。 | `packages/tui/src/vim.ts:664-679` |
| `c（normal）` | 操作符 c；cc 按 count 行 linewise 改并进入 insert。 | `packages/tui/src/vim.ts:665-679` |
| `p（normal）` | 在光标后粘贴 count 次。 | `packages/tui/src/vim.ts:680-682` |
| `P（normal）` | 在光标前粘贴 count 次。 | `packages/tui/src/vim.ts:680-682` |
| `u（normal）` | 撤销。 | `packages/tui/src/vim.ts:683-685` |
| `default（normal）` | 未知可打印键：清空 pending 并吞掉，不插入文本。 | `packages/tui/src/vim.ts:686-690` |
| `v（visual）` | 已在该模式则退回 normal，否则切到 visual。 | `packages/tui/src/vim.ts:698-711` |
| `V（visual）` | 已在 visual-line 则退回 normal，否则切到 visual-line。 | `packages/tui/src/vim.ts:698-711` |
| `o（visual）` | 交换选择的活动端/锚点（跳到 anchor）。 | `packages/tui/src/vim.ts:712-715` |
| `y（visual）` | 复制选区并回 normal。 | `packages/tui/src/vim.ts:716-729` |
| `d（visual）` | 删除选区并回 normal。 | `packages/tui/src/vim.ts:716-729` |
| `x（visual）` | 删除选区并回 normal。 | `packages/tui/src/vim.ts:716-729` |
| `c（visual）` | 改选区并进入 insert。 | `packages/tui/src/vim.ts:716-729` |
| `s（visual）` | 改选区并进入 insert（同 c）。 | `packages/tui/src/vim.ts:716-729` |
| `default（visual）` | 未识别键：清空 pending 并吞掉。 | `packages/tui/src/vim.ts:730-733` |
| `iw` | text object：光标所在词（word 对象）。 | `packages/tui/src/vim.ts:530-532` |
| `aw` | text object：光标所在词含尾随空白（word 对象）。 | `packages/tui/src/vim.ts:530-532` |
| `iW` | text object：光标所在 WORD（空白分隔）。 | `packages/tui/src/vim.ts:530-532` |
| `aW` | text object：光标所在 WORD 含尾随空白。 | `packages/tui/src/vim.ts:530-532` |
| `i"` | text object：光标所在双引号对内。 | `packages/tui/src/vim.ts:533-536` |
| `a"` | text object：双引号对含引号/尾随空白。 | `packages/tui/src/vim.ts:533-536` |
| `i'` | text object：单引号对内。 | `packages/tui/src/vim.ts:534-536` |
| `a'` | text object：单引号对含引号/尾随空白。 | `packages/tui/src/vim.ts:534-536` |
| i` | text object：反引号对内。 | `packages/tui/src/vim.ts:535-536` |
| a` | text object：反引号对含引号/尾随空白。 | `packages/tui/src/vim.ts:535-536` |
| `i( / i)` | text object：最内层圆括号对内（可跨行、计嵌套）。 | `packages/tui/src/vim.ts:537-539` |
| `a( / a)` | text object：最内层圆括号对含括号。 | `packages/tui/src/vim.ts:537-539` |
| `ib` | text object：同 i(（括号别名）。 | `packages/tui/src/vim.ts:539-540` |
| `ab` | text object：同 a(（括号别名）。 | `packages/tui/src/vim.ts:539-540` |
| `i[ / i]` | text object：最内层方括号对内。 | `packages/tui/src/vim.ts:541-543` |
| `a[ / a]` | text object：最内层方括号对含括号。 | `packages/tui/src/vim.ts:541-543` |
| `i{ / i}` | text object：最内层花括号对内。 | `packages/tui/src/vim.ts:544-546` |
| `a{ / a}` | text object：最内层花括号对含括号。 | `packages/tui/src/vim.ts:544-546` |
| `iB` | text object：同 i{（花括号别名）。 | `packages/tui/src/vim.ts:546-547` |
| `aB` | text object：同 a{（花括号别名）。 | `packages/tui/src/vim.ts:546-547` |
| `i<` | text object：最内层尖括号对内。 | `packages/tui/src/vim.ts:548-550` |
| `a>` | text object：最内层尖括号对含括号。 | `packages/tui/src/vim.ts:548-550` |
| `ip` | text object：光标所在段落（连续同空白性行，linewise）。 | `packages/tui/src/vim.ts:551-552` |
| `ap` | text object：段落含其后（或前）相邻段落（linewise）。 | `packages/tui/src/vim.ts:551-552` |
| `operator d + motion/object` | #operate 执行删除（可 linewise/charwise，c 会插入）。 | `packages/tui/src/vim.ts:496-509` |
| `operator y + motion/object` | #operate 执行复制并回光标起点。 | `packages/tui/src/vim.ts:496-505` |
| `operator c + motion/object` | #operate 执行改：删除范围并切 insert。 | `packages/tui/src/vim.ts:510-515` |

### ② editor.ts — 动作名全集（共 57 条）
> 数法（payload 原文）：② editor.ts — 动作名全集（注册表 canonical 30 + 硬编码/序列 26 + VIM_NAV_KEYS 9 = 65 条；数法：grep -o 'matchesCanonical(canonical, "[^"]*"' | sort -u = 30，grep 'matchesKey(data,' = 9，手读字面量）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tui.editor.cursorUp` | 上：编辑器空则翻历史（-1），否则光标上移。 | `packages/tui/src/components/editor.ts:2173` |
| `tui.editor.cursorDown` | 下：在最后可视行且历史中则前进历史，否则光标下移。 | `packages/tui/src/components/editor.ts:2185` |
| `tui.editor.cursorLeft` | 光标左移一位（自动补全可见时先走弹窗分支）。 | `packages/tui/src/components/editor.ts:2199` |
| `tui.editor.cursorRight` | 接受幽灵词补全或右移一位；在自动补全“已到行尾”时也充当接受键。 | `packages/tui/src/components/editor.ts:1858,2195` |
| `tui.editor.cursorWordLeft` | 重置 kill 序列后左移一个词。 | `packages/tui/src/components/editor.ts:2163` |
| `tui.editor.cursorWordRight` | 重置 kill 序列后右移一个词。 | `packages/tui/src/components/editor.ts:2167` |
| `tui.editor.cursorLineStart` | 移到本行行首。 | `packages/tui/src/components/editor.ts:2144` |
| `tui.editor.cursorLineEnd` | 移到本行行尾。 | `packages/tui/src/components/editor.ts:2146` |
| `tui.editor.jumpForward` | 进入“跳转模式”等待下一个字符并前跳；跳转模式中再按则取消。 | `packages/tui/src/components/editor.ts:1776,2208` |
| `tui.editor.jumpBackward` | 进入跳转模式反向跳；再按取消。 | `packages/tui/src/components/editor.ts:1777,2210` |
| `tui.editor.pageUp` | 编辑器视口上翻一页（不载入历史提示）。 | `packages/tui/src/components/editor.ts:2153` |
| `tui.editor.pageDown` | 编辑器视口下翻一页。 | `packages/tui/src/components/editor.ts:2155` |
| `tui.editor.deleteCharBackward` | 退格删除一个字符/选中区。 | `packages/tui/src/components/editor.ts:2140` |
| `tui.editor.deleteCharForward` | 前向删除一个字符。 | `packages/tui/src/components/editor.ts:2159` |
| `tui.editor.deleteWordBackward` | 删除前一个词。 | `packages/tui/src/components/editor.ts:2044` |
| `tui.editor.deleteWordForward` | 删除后一个词。 | `packages/tui/src/components/editor.ts:2049` |
| `tui.editor.deleteToLineStart` | 删除光标到行首。 | `packages/tui/src/components/editor.ts:2038` |
| `tui.editor.deleteToLineEnd` | 删除光标到行尾。 | `packages/tui/src/components/editor.ts:2034` |
| `tui.editor.yank` | 从 kill ring 粘贴。 | `packages/tui/src/components/editor.ts:2053` |
| `tui.editor.yankPop` | 在 kill ring 中循环替换刚粘贴内容。 | `packages/tui/src/components/editor.ts:2057` |
| `tui.editor.undo` | 撤销。 | `packages/tui/src/components/editor.ts:1835` |
| `tui.editor.spellingSuggestions` | 弹出拼写替换建议。 | `packages/tui/src/components/editor.ts:1840` |
| `tui.input.newLine` | 插入换行（与 Shift+Enter 等效）。 | `packages/tui/src/components/editor.ts:2087` |
| `tui.input.submit` | 提交；在自动补全中做接受/提交分派。 | `packages/tui/src/components/editor.ts:1862,2099` |
| `tui.input.tab` | 触发上下文补全；自动补全打开时接受选中项。 | `packages/tui/src/components/editor.ts:1864,2027` |
| `tui.select.up` | 自动补全列表上移。 | `packages/tui/src/components/editor.ts:1872-1887` |
| `tui.select.down` | 自动补全列表下移。 | `packages/tui/src/components/editor.ts:1873-1887` |
| `tui.select.pageUp` | 自动补全列表上翻页。 | `packages/tui/src/components/editor.ts:1874-1887` |
| `tui.select.pageDown` | 自动补全列表下翻页。 | `packages/tui/src/components/editor.ts:1875-1887` |
| `tui.select.cancel` | 关闭可见的自动补全/取消其状态。 | `packages/tui/src/components/editor.ts:1850` |
| `ctrl+c（硬编码，保留给宿主）` | 直接 return 不消费，留给父组件做应用级处理。 | `packages/tui/src/components/editor.ts:1830` |
| `ctrl+a（兜底）` | 未绑定 tui.editor.cursorLineStart 时的行首兜底。 | `packages/tui/src/components/editor.ts:2061` |
| `ctrl+e（兜底）` | 未绑定时行尾兜底。 | `packages/tui/src/components/editor.ts:2065` |
| `alt+enter` | 有 onAltEnter 回调则回调全文，否则插入换行。 | `packages/tui/src/components/editor.ts:2069` |
| `ctrl+enter` | 视作插入换行（Kitty/modifyOtherKeys，含锁定位）。 | `packages/tui/src/components/editor.ts:2084` |
| `\x1b\r（legacy Option+Enter）` | 插入换行。 | `packages/tui/src/components/editor.ts:2085` |
| `\x1b[13;2~（legacy Shift+Enter）` | 插入换行。 | `packages/tui/src/components/editor.ts:2086` |
| `charCodeAt(0)===10 && len>1` | 多字节 LF：带修饰键的 Ctrl+Enter，插入换行。 | `packages/tui/src/components/editor.ts:2083` |
| `含 ESC 与 CR 的多字节序列` | 通用 legacy 换行。 | `packages/tui/src/components/editor.ts:2088` |
| `"\n"（单字节 LF）` | iTerm2 映射的 Shift+Enter：插入换行；否则视为提交。 | `packages/tui/src/components/editor.ts:2089,2099` |
| `shift+backspace` | 退格删除。 | `packages/tui/src/components/editor.ts:2140` |
| `shift+delete` | 前向删除。 | `packages/tui/src/components/editor.ts:2159` |
| `shift+space` | 插入一个普通空格（Kitty 转义序列）。 | `packages/tui/src/components/editor.ts:2204` |
| `enter（反斜杠续行判定）` | #shouldSubmitOnBackslashEnter：草稿以反斜杠结尾且 submit 绑定含 shift+enter 时，Enter 退格反斜杠并续行。 | `packages/tui/src/components/editor.ts:2091,3313-3316` |
| `可打印文本` | 非控制字符逐字形插入；多标量纯文本走快路径直接插入。 | `packages/tui/src/components/editor.ts:2213-2226,1814-1818` |
| `跳转模式下一字符` | 等待的任意可打印字符被消费为跳转目标，不再插入。 | `packages/tui/src/components/editor.ts:1783-1791` |
| `bracketed paste` | \x1b[200~…~ 粘贴内容整体入缓冲区，不走按键分派。 | `packages/tui/src/components/editor.ts:1800-1807` |
| `vim escape→宿主` | vimConsumesEscape 为 false（normal 且无 pending）时 escape 交回宿主。 | `packages/tui/src/components/editor.ts:932-936,2236-2237` |
| `VIM_NAV_KEYS: up→k` | vim normal/visual 下上箭头当作 k 动作。 | `packages/tui/src/components/editor.ts:440-450,2241` |
| `VIM_NAV_KEYS: down→j` | 下箭头→j。 | `packages/tui/src/components/editor.ts:442` |
| `VIM_NAV_KEYS: left→h` | 左箭头→h。 | `packages/tui/src/components/editor.ts:443` |
| `VIM_NAV_KEYS: right→l` | 右箭头→l。 | `packages/tui/src/components/editor.ts:444` |
| `VIM_NAV_KEYS: home→0` | Home→行首动作 0。 | `packages/tui/src/components/editor.ts:445` |
| `VIM_NAV_KEYS: end→$` | End→行尾动作 $。 | `packages/tui/src/components/editor.ts:446` |
| `VIM_NAV_KEYS: backspace→h` | 退格→h（normal/visual 不删字）。 | `packages/tui/src/components/editor.ts:447` |
| `VIM_NAV_KEYS: delete→x` | Delete→x（删字符）。 | `packages/tui/src/components/editor.ts:448` |
| `VIM_NAV_KEYS: space→l` | 空格→l。 | `packages/tui/src/components/editor.ts:449` |

## 43. 首启向导 · setup/ 按键与鼠标路由（共 63 条）

> 数法（payload 原文）：③ setup/** + chrome/selector-helpers.ts — 按键与鼠标路由（共 69 条：wizard-overlay 11 + startup-splash 5 + scenes 16 + selector-helpers 2 + 被委托组件 35；数法：grep matchesKey/handleInput/routeMouse/event.act/leftClick/wheel 全 setup 目录 + 手读 4 个被委托组件）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `wizard-overlay: ctrl+c` | 任意 phase 下退出向导，转入 outro。 | `packages/tui/src/setup/wizard-overlay.ts:123-125` |
| `wizard-overlay splash: enter/return/space/escape` | 跳过 splash 进入第一个 scene。 | `packages/tui/src/setup/wizard-overlay.ts:128-136` |
| `wizard-overlay outro: enter/return/space/escape` | 结束向导（complete）。 | `packages/tui/src/setup/wizard-overlay.ts:139-147` |
| `wizard-overlay: 原始 SGR 鼠标输入` | 以 \x1b[< 开头的块走鼠标路由，绝不进入 scene 键盘。 | `packages/tui/src/setup/wizard-overlay.ts:117-121` |
| `wizard-overlay splash/outro: 左键点击` | splash 左键=beginScene，outro 左键=complete。 | `packages/tui/src/setup/wizard-overlay.ts:163-167` |
| `wizard-overlay scene: routeMouse 坐标换算` | 把屏幕坐标换算成 scene body 局部坐标（扣 #bodyRowStart 与 SCENE_MARGIN_X）。 | `packages/tui/src/setup/wizard-overlay.ts:170-173` |
| `wizard-overlay scene: 滚轮（无 routeMouse 时）` | 滚轮上/下合成 \x1b[A / \x1b[B（arrow up/down）交给 scene.handleInput。 | `packages/tui/src/setup/wizard-overlay.ts:175-177` |
| `wizard-overlay scene: 键盘转发` | 非 splash/outro 时把按键转交 activeScene.handleInput。 | `packages/tui/src/setup/wizard-overlay.ts:149` |
| `wizard-overlay 原生事件 skip` | splash 上 act=skip（点击 splash 描述节点）→ beginScene。 | `packages/tui/src/setup/wizard-overlay.ts:249-250` |
| `wizard-overlay 原生事件 continue` | outro 上 act=continue → complete。 | `packages/tui/src/setup/wizard-overlay.ts:250-251` |
| `wizard-overlay footer 提示常量` | 底部提示走 editorKeys(up/down)+editorKey(confirm/cancel)+ctrl+c（仅提示，不是新绑定）。 | `packages/tui/src/setup/wizard-overlay.ts:44-47` |
| `startup-splash: enter` | 结束独立 splash。 | `packages/tui/src/setup/startup-splash.ts:56` |
| `startup-splash: return` | 结束 splash。 | `packages/tui/src/setup/startup-splash.ts:57` |
| `startup-splash: space` | 结束 splash。 | `packages/tui/src/setup/startup-splash.ts:58` |
| `startup-splash: escape` | 结束 splash。 | `packages/tui/src/setup/startup-splash.ts:59` |
| `startup-splash 原生事件 skip` | splash 节点 click action=skip → 结束。 | `packages/tui/src/setup/startup-splash.ts:75-76` |
| `composer scene: 数字 1..N` | 单字符数字直选第 N 个 composer 形状并即时预览。 | `packages/tui/src/setup/scenes/composer.ts:64-71` |
| `composer scene: 其余键` | 交 WizardStep/SelectList（见共享项）。 | `packages/tui/src/setup/scenes/composer.ts:72-73` |
| `glyph scene: 数字 1..3` | 直选 nerd/unicode/ascii 预设并预览。 | `packages/tui/src/setup/scenes/glyph.ts:65-73` |
| `glyph scene: 其余键` | 交 WizardStep/SelectList。 | `packages/tui/src/setup/scenes/glyph.ts:74-75` |
| `theme scene: 数字 1..9` | 直选 curated 列表第 N 项并预览。 | `packages/tui/src/setup/scenes/theme.ts:172-178` |
| `theme scene: 其余键` | 交 SelectList；all 模式下取消键回 curated，否则跳过本步。 | `packages/tui/src/setup/scenes/theme.ts:179,310-320` |
| `theme scene 鼠标（loading 中）` | 加载全部主题时用 line=-Infinity 直投列表，使滚轮/hover/点击都落到列表区。 | `packages/tui/src/setup/scenes/theme.ts:183-189` |
| `model scene: 全部键` | 转发 ModelBrowser（见共享项）。 | `packages/tui/src/setup/scenes/model.ts:55-59` |
| `model scene 鼠标` | 选中/保存中屏蔽，否则转 WizardStep→ModelBrowser。 | `packages/tui/src/setup/scenes/model.ts:61-64` |
| `sign-in scene: alt+c（登录中）` | 有 authUrl 时重试复制授权 URL。 | `packages/tui/src/setup/scenes/sign-in.ts:132` |
| `sign-in scene: "c"（登录中、无 prompt）` | 同上，复制授权 URL。 | `packages/tui/src/setup/scenes/sign-in.ts:132` |
| `sign-in scene: escape（登录中）` | 中止 OAuth 登录（abort）。 | `packages/tui/src/setup/scenes/sign-in.ts:136-138` |
| `sign-in scene: ctrl+c（登录中）` | 同上中止登录。 | `packages/tui/src/setup/scenes/sign-in.ts:136-138` |
| `sign-in scene: 选择态其余键` | 转发 OAuthSelectorComponent（见共享项）。 | `packages/tui/src/setup/scenes/sign-in.ts:141` |
| `CopyablePromptInput: alt+c` | 代码/授权提示输入框内复制授权 URL，其余交 Input。 | `packages/tui/src/setup/scenes/sign-in.ts:62-67` |
| `sign-in 代码提示输入: Input onSubmit` | 回车提交粘贴的 code/redirect URL，解析 prompt。 | `packages/tui/src/setup/scenes/sign-in.ts:456-458` |
| `sign-in 代码提示输入: Input onEscape` | 转义中止登录并清空 prompt。 | `packages/tui/src/setup/scenes/sign-in.ts:459-462` |
| `selector-helpers handleTabSwitchKey: tab / right` | 调用 switchTab(1) 前进到下一个 tab，返回 true 表示已消费。 | `packages/tui/src/chrome/selector-helpers.ts:79-82` |
| `selector-helpers handleTabSwitchKey: shift+tab / left` | 调用 switchTab(-1) 后退到上一个 tab。 | `packages/tui/src/chrome/selector-helpers.ts:83-86` |
| `[共享] SelectList: cancel (escape/ctrl+c)` | 有确认中的删除则先取消确认，否则触发 onCancel（场景=跳过本步）。 | `packages/tui/src/components/select-list.ts:491-494` |
| `[共享] SelectList: up / down` | 选择上/下移一项（按 layout.wrapNavigation 决定是否循环）。 | `packages/tui/src/components/select-list.ts:501-504` |
| `[共享] SelectList: pageUp / pageDown` | 选择上/下移一屏（#maxVisible）。 | `packages/tui/src/components/select-list.ts:505-508` |
| `[共享] SelectList: home / end` | 选择跳到首/末项。 | `packages/tui/src/components/select-list.ts:509-512` |
| `[共享] SelectList: confirm (enter) 或 \n` | 激活当前项（onSelect：composer/glyph/theme = 保存并 finish done）。 | `packages/tui/src/components/select-list.ts:513-514,818-821` |
| `[共享] SelectList: 可打印文本` | 优先作为搜索过滤输入（先于导航绑定）。 | `packages/tui/src/components/select-list.ts:499,516` |
| `[共享] SelectList: 其余编辑键` | 交内部搜索 Input（退格/左右/词移动等）。 | `packages/tui/src/components/select-list.ts:516,771-773` |
| `[共享] SelectList 鼠标: 滚轮` | handleWheel：选择移动一个刻度并通知 onSelectionChange（=即时预览）。 | `packages/tui/src/components/select-list.ts:277-279,289-291` |
| `[共享] SelectList 鼠标: 移动（hover）` | setHoverIndex 高亮指针下条目（null 清除）。 | `packages/tui/src/components/select-list.ts:272-274` |
| `[共享] SelectList 鼠标: 左键点击` | clickItem：先选中该项（触发预览）再激活（=确认保存）。 | `packages/tui/src/components/select-list.ts:282-287` |
| `[共享] SelectList 鼠标路由入口` | routeMouse → routeSelectListMouse：滚轮→handleWheel，motion→setHoverIndex，leftClick→clickItem（hitTest 行映射）。 | `packages/tui/src/mouse.ts:85-99` |
| `[共享] ModelBrowser: cancel ladder` | 查询非空先清空查询，否则 onCancel（场景=跳过本步）。 | `packages/tui/src/overlays/model-browser.ts:1161-1163,1204-1210` |
| `[共享] ModelBrowser: up / down` | 选择上/下移一项。 | `packages/tui/src/overlays/model-browser.ts:1164-1171` |
| `[共享] ModelBrowser: pageUp / pageDown` | 选择上/下移一屏（不循环）。 | `packages/tui/src/overlays/model-browser.ts:1172-1180` |
| `[共享] ModelBrowser: home / end` | 选择跳到可见列表首/末项。 | `packages/tui/src/overlays/model-browser.ts:1181-1188` |
| `[共享] ModelBrowser: enter / return / \n` | 激活选中模型（onActivate：保存为默认模型）。 | `packages/tui/src/overlays/model-browser.ts:1189-1196` |
| `[共享] ModelBrowser: 其余键` | 交内部搜索 Input 编辑查询；查询变化重置选中前缀并刷新。 | `packages/tui/src/overlays/model-browser.ts:1197-1202` |
| `[共享] ModelBrowser 鼠标: 滚轮` | 平移窗口（#windowStart），不移动选择、不循环。 | `packages/tui/src/overlays/model-browser.ts:1220-1225` |
| `[共享] ModelBrowser 鼠标: 移动（hover）` | 更新 #hoveredIndex 高亮行。 | `packages/tui/src/overlays/model-browser.ts:1226-1229` |
| `[共享] ModelBrowser 鼠标: 左键点击` | 点未选中项=选中；点已选中项（再点）=激活。 | `packages/tui/src/overlays/model-browser.ts:1230-1243` |
| `[共享] OAuthSelector: cancel (escape/ctrl+c)` | stopValidation 并 onCancel（场景=跳过 sign-in）。 | `packages/tui/src/overlays/oauth-selector.ts:376-380` |
| `[共享] OAuthSelector: up / down` | provider 选择上/下移一项（循环）。 | `packages/tui/src/overlays/oauth-selector.ts:381-393` |
| `[共享] OAuthSelector: pageUp / pageDown` | provider 选择上/下移一屏（不循环）。 | `packages/tui/src/overlays/oauth-selector.ts:395-405` |
| `[共享] OAuthSelector: enter / return / \n` | 确认所选 provider：可用则发起 OAuth，否则提示不可用。 | `packages/tui/src/overlays/oauth-selector.ts:407-408,416-424` |
| `[共享] OAuthSelector: 其余键` | 编辑搜索字段过滤 provider（空时忽略 backspace/纯空白）。 | `packages/tui/src/overlays/oauth-selector.ts:411,297-306` |
| `[共享] OAuthSelector 鼠标: 滚轮` | handleWheel 移动选择（clamp，不循环）并刷新列表。 | `packages/tui/src/overlays/oauth-selector.ts:611-617,625-628` |
| `[共享] OAuthSelector 鼠标: 移动（hover）` | 更新 #hoveredIndex 悬停带并重绘。 | `packages/tui/src/overlays/oauth-selector.ts:629-637` |
| `[共享] OAuthSelector 鼠标: 左键点击` | 选中该 provider 行并立即确认（等同 Enter）。 | `packages/tui/src/overlays/oauth-selector.ts:638-645` |

## 44. TUI 源码目录 · 逐文件（共 181 条）

### chrome/（共 28 条）
> 数法（payload 原文）：chrome/（共 28 条；数法：glob packages/tui/src/chrome/* 全量，无子目录）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `chat-block.ts` | 会话块基类：生命周期/可折叠骨架 — 仅内部 | `packages/tui/src/chrome/chat-block.ts:28` |
| `collab-qrcode.ts` | 协作浏览器链接二维码卡片 — 用户可见 | `packages/tui/src/chrome/collab-qrcode.ts:34` |
| `context-thresholds.ts` | 上下文用量阈值/文案纯函数 — 仅内部 | `packages/tui/src/chrome/context-thresholds.ts:31` |
| `countdown-timer.ts` | 倒计时定时器（无渲染） — 仅内部 | `packages/tui/src/chrome/countdown-timer.ts:8` |
| `diff.ts` | 把 diff 文本渲成 ANSI/native 行 — 用户可见 | `packages/tui/src/chrome/diff.ts:172` |
| `dynamic-border.ts` | 跟主题色变的水平边框组件 — 仅内部 | `packages/tui/src/chrome/dynamic-border.ts:14` |
| `error-block.ts` | 格式化错误块文本（截断/清洗） — 用户可见 | `packages/tui/src/chrome/error-block.ts:34` |
| `form-theme.ts` | 表单字段共享主题常量 — 仅内部 | `packages/tui/src/chrome/form-theme.ts:5` |
| `format.ts` | provider/时长格式化 + ASCII 进度条 — 仅内部 | `packages/tui/src/chrome/format.ts:8` |
| `index.ts` | chrome 桶导出（barrel） — 仅内部 | `packages/tui/src/chrome/index.ts:1` |
| `keybinding-hints.ts` | 键位提示文本生成工具 — 仅内部 | `packages/tui/src/chrome/keybinding-hints.ts:18` |
| `live-board.ts` | 终端 live 重绘板（spinner 行） — 用户可见 | `packages/tui/src/chrome/live-board.ts:38` |
| `local-date.ts` | 本地日历日期/时区格式化 — 仅内部 | `packages/tui/src/chrome/local-date.ts:2` |
| `message-divider.ts` | 消息分隔标记行组件 — 用户可见 | `packages/tui/src/chrome/message-divider.ts:31` |
| `message-frame.ts` | 自定义消息外框组件 — 用户可见 | `packages/tui/src/chrome/message-frame.ts:60` |
| `message-notice.ts` | 通知卡片（头/图标/可折叠体） — 用户可见 | `packages/tui/src/chrome/message-notice.ts:59` |
| `overlay-box.ts` | overlay 边框/Panel 布局原语 — 仅内部 | `packages/tui/src/chrome/overlay-box.ts:218` |
| `qrcode.ts` | QR 编码 + 文本/半块渲染 — 仅内部 | `packages/tui/src/chrome/qrcode.ts:155` |
| `segment-track.ts` | 分段轨道 chip 渲染 — 用户可见 | `packages/tui/src/chrome/segment-track.ts:86` |
| `select-list-mouse-routing.ts` | 列表顶部边框鼠标路由 helper — 仅内部 | `packages/tui/src/chrome/select-list-mouse-routing.ts:4` |
| `selector-helpers.ts` | 列表窗口/选择/补白 helper — 仅内部 | `packages/tui/src/chrome/selector-helpers.ts:17` |
| `shared.ts` | 状态文本清洗 + 标签栏共享主题 — 仅内部 | `packages/tui/src/chrome/shared.ts:9` |
| `status-notice.ts` | 状态通知行组件 — 用户可见 | `packages/tui/src/chrome/status-notice.ts:17` |
| `streaming-panel.ts` | 流式面板内容容器（分区） — 用户可见 | `packages/tui/src/chrome/streaming-panel.ts:58` |
| `tool-activity.ts` | 工具活动可见性容器 — 仅内部 | `packages/tui/src/chrome/tool-activity.ts:12` |
| `transcript-container.ts` | 转录主容器（顺序/滚动/退休） — 用户可见 | `packages/tui/src/chrome/transcript-container.ts:170` |
| `transcript-status.ts` | 转录紧凑状态行块 — 用户可见 | `packages/tui/src/chrome/transcript-status.ts:23` |
| `visual-truncate.ts` | 按视觉行截断文本的工具 — 仅内部 | `packages/tui/src/chrome/visual-truncate.ts:43` |

### chat/（共 34 条）
> 数法（payload 原文）：chat/（共 34 条；数法：glob packages/tui/src/chat/* 全量，无子目录）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `advisor-message.ts` | advisor 卡片 — 用户可见 | `packages/tui/src/chat/advisor-message.ts:167` |
| `assistant-message.ts` | 助手消息块（含思考/速度表） — 用户可见 | `packages/tui/src/chat/assistant-message.ts:226` |
| `background-tan-message.ts` | /tan 后台派发面包屑卡片 — 用户可见 | `packages/tui/src/chat/background-tan-message.ts:21` |
| `bash-execution.ts` | bash(!)执行卡（PTY 输出） — 用户可见 | `packages/tui/src/chat/bash-execution.ts:55` |
| `cache-invalidation-marker.ts` | 缓存失效标记行 + 检测 — 用户可见 | `packages/tui/src/chat/cache-invalidation-marker.ts:78` |
| `chat-transcript-builder.ts` | 转录块装配构建器 — 仅内部 | `packages/tui/src/chat/chat-transcript-builder.ts:88` |
| `collab-prompt-message.ts` | 协作提示消息卡 — 用户可见 | `packages/tui/src/chat/collab-prompt-message.ts:15` |
| `compaction-summary-message.ts` | compaction/handoff/branch 汇总卡 — 用户可见 | `packages/tui/src/chat/compaction-summary-message.ts:195` |
| `custom-message.ts` | 通用自定义消息卡 — 用户可见 | `packages/tui/src/chat/custom-message.ts:10` |
| `display-preferences.ts` | 转录显示偏好全局状态 — 仅内部 | `packages/tui/src/chat/display-preferences.ts:2` |
| `eval-execution.ts` | python/js 执行卡 — 用户可见 | `packages/tui/src/chat/eval-execution.ts:31` |
| `execution-shared.ts` | 执行卡共享框架/描述 helper — 仅内部 | `packages/tui/src/chat/execution-shared.ts:51` |
| `extension-types.ts` | 扩展渲染回调类型 — 仅内部 | `packages/tui/src/chat/extension-types.ts:5` |
| `hook-message.ts` | hook 消息卡 — 用户可见 | `packages/tui/src/chat/hook-message.ts:12` |
| `image-loading.ts` | 图片输入校验/转码/缓存 — 仅内部 | `packages/tui/src/chat/image-loading.ts:4` |
| `late-diagnostics-message.ts` | 迟到 LSP 诊断卡 — 用户可见 | `packages/tui/src/chat/late-diagnostics-message.ts:69` |
| `messages.ts` | 消息类型常量与守卫 — 仅内部 | `packages/tui/src/chat/messages.ts:18` |
| `reaction.ts` | reaction 徽标目标/文本分割 helper — 仅内部 | `packages/tui/src/chat/reaction.ts:14` |
| `read-tool-group.ts` | 读取工具分组卡 — 用户可见 | `packages/tui/src/chat/read-tool-group.ts:346` |
| `recap-notice.ts` | recap 通知卡 — 用户可见 | `packages/tui/src/chat/recap-notice.ts:14` |
| `served-model-marker.ts` | 模型错配标记行 — 用户可见 | `packages/tui/src/chat/served-model-marker.ts:78` |
| `skill-message.ts` | skill 调用卡 — 用户可见 | `packages/tui/src/chat/skill-message.ts:33` |
| `skill-title-input.ts` | skill 标题模型输入/标题文本 — 仅内部 | `packages/tui/src/chat/skill-title-input.ts:2` |
| `stripped-tool-calls-placeholder.ts` | 被剥离工具调用占位行 — 用户可见 | `packages/tui/src/chat/stripped-tool-calls-placeholder.ts:11` |
| `thinking-display.ts` | thinking 文本格式化/可显示判定 — 仅内部 | `packages/tui/src/chat/thinking-display.ts:255` |
| `todo-reminder.ts` | todo 提醒卡 — 用户可见 | `packages/tui/src/chat/todo-reminder.ts:15` |
| `tool-execution.ts` | 工具执行卡主组件 — 用户可见 | `packages/tui/src/chat/tool-execution.ts:295` |
| `transcript-actions.ts` | 转录动作注册/派发 — 仅内部 | `packages/tui/src/chat/transcript-actions.ts:7` |
| `transcript-browser.ts` | 全屏转录浏览器组件 — 用户可见 | `packages/tui/src/chat/transcript-browser.ts:97` |
| `transcript-entry.ts` | 持久化条目解析 helper — 仅内部 | `packages/tui/src/chat/transcript-entry.ts:14` |
| `transcript-outline.ts` | 转录大纲行渲染 helper — 仅内部 | `packages/tui/src/chat/transcript-outline.ts:77` |
| `transcript-render-helpers.ts` | 各类卡片构建 helper — 仅内部 | `packages/tui/src/chat/transcript-render-helpers.ts:30` |
| `ttsr-notification.ts` | TTSR 规则触发通知卡 — 用户可见 | `packages/tui/src/chat/ttsr-notification.ts:30` |
| `user-message.ts` | 用户消息气泡 — 用户可见 | `packages/tui/src/chat/user-message.ts:121` |

### prompt/（共 32 条）
> 数法（payload 原文）：prompt/（共 32 条；数法：glob packages/tui/src/prompt/** 全量 = 30 .ts + tips.txt + data/emojis.json）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `attachment-chips.ts` | 编辑器附件 chip 带 — 用户可见 | `packages/tui/src/prompt/attachment-chips.ts:53` |
| `composer-attachments.ts` | 附件 token/标记处理工具 — 仅内部 | `packages/tui/src/prompt/composer-attachments.ts:7` |
| `composer-cache.ts` | composer 启动状态 SQLite 缓存 — 仅内部 | `packages/tui/src/prompt/composer-cache.ts:225` |
| `composer-hints.ts` | 空 composer 手势提示 — 用户可见 | `packages/tui/src/prompt/composer-hints.ts:42` |
| `composer.ts` | 主 composer（编辑器+转录+状态） — 用户可见 | `packages/tui/src/prompt/composer.ts:207` |
| `custom-editor.ts` | 输入编辑器（拼写/补全/附件） — 用户可见 | `packages/tui/src/prompt/custom-editor.ts:434` |
| `editor-top-gap.ts` | 编辑器上方空隙组件 — 仅内部 | `packages/tui/src/prompt/editor-top-gap.ts:25` |
| `emoji-autocomplete.ts` | emoji/shortcode 补全 — 仅内部 | `packages/tui/src/prompt/emoji-autocomplete.ts:131` |
| `github-ref-autocomplete.ts` | GitHub 引用(#)补全 — 仅内部 | `packages/tui/src/prompt/github-ref-autocomplete.ts:61` |
| `gradient-highlight.ts` | 渐变关键词高亮器工厂 — 仅内部 | `packages/tui/src/prompt/gradient-highlight.ts:38` |
| `image-format.ts` | 图片扩展名/MIME 工具 — 仅内部 | `packages/tui/src/prompt/image-format.ts:11` |
| `image-references.ts` | 图片引用链接/尺寸缓存 — 仅内部 | `packages/tui/src/prompt/image-references.ts:33` |
| `image-source.ts` | 图片来源标记类型/工具 — 仅内部 | `packages/tui/src/prompt/image-source.ts:16` |
| `interactive-context-helpers.ts` | 助手消息段构建 host helper — 仅内部 | `packages/tui/src/prompt/interactive-context-helpers.ts:102` |
| `internal-url-autocomplete.ts` | 内部 URL(local://等)补全 — 仅内部 | `packages/tui/src/prompt/internal-url-autocomplete.ts:87` |
| `macos-spelling.ts` | macOS 拼写/自动更正 provider — 仅内部 | `packages/tui/src/prompt/macos-spelling.ts:53` |
| `magic-keywords.ts` | 魔法关键词注册/高亮 — 仅内部 | `packages/tui/src/prompt/magic-keywords.ts:64` |
| `markdown-prose.ts` | 非正文掩码 helper — 仅内部 | `packages/tui/src/prompt/markdown-prose.ts:160` |
| `model-mention-autocomplete.ts` | 模型提及(^)补全 — 仅内部 | `packages/tui/src/prompt/model-mention-autocomplete.ts:38` |
| `model-mention-syntax.ts` | 模型提及语法/标签编解码 — 仅内部 | `packages/tui/src/prompt/model-mention-syntax.ts:21` |
| `prompt-action-autocomplete.ts` | 斜杠/动作补全 provider — 仅内部 | `packages/tui/src/prompt/prompt-action-autocomplete.ts:25` |
| `prose-gate.ts` | 正文词判定/ProseSource — 仅内部 | `packages/tui/src/prompt/prose-gate.ts:57` |
| `queue-input.ts` | 队列列表/简写解析 — 仅内部 | `packages/tui/src/prompt/queue-input.ts:21` |
| `queued-messages.ts` | 排队消息带 — 用户可见 | `packages/tui/src/prompt/queued-messages.ts:24` |
| `skill-tokens.ts` | skill token 正则/判定 — 仅内部 | `packages/tui/src/prompt/skill-tokens.ts:8` |
| `tools-markdown.ts` | 工具说明 markdown 生成 — 仅内部 | `packages/tui/src/prompt/tools-markdown.ts:14` |
| `usage-amounts.ts` | 用量额度格式化 — 仅内部 | `packages/tui/src/prompt/usage-amounts.ts:57` |
| `video.ts` | 视频路径/预览帧工具 — 仅内部 | `packages/tui/src/prompt/video.ts:17` |
| `welcome.ts` | 欢迎屏（logo/tips/最近会话） — 用户可见 | `packages/tui/src/prompt/welcome.ts:181` |
| `word-completion.ts` | 幽灵文本补全 provider — 仅内部 | `packages/tui/src/prompt/word-completion.ts:103` |
| `tips.txt` | 欢迎屏随机提示文案（数据） — 用户可见 | `packages/tui/src/prompt/tips.txt:1` |
| `data/emojis.json` | emoji 补全数据表（数据） — 仅内部 | `packages/tui/src/prompt/data/emojis.json:1` |

### components/（共 40 条）
> 数法（payload 原文）：components/（共 40 条；数法：glob components/*.ts = 25 顶层，另 composer/ 11、layout/ 4）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `box.ts` | 带边框/内边距的盒子容器 — 仅内部 | `packages/tui/src/components/box.ts:42` |
| `cancellable-loader.ts` | 可按 Esc 取消的 spinner 加载器 — 用户可见 | `packages/tui/src/components/cancellable-loader.ts:13` |
| `disclosure.ts` | 可折叠披露容器 — 用户可见 | `packages/tui/src/components/disclosure.ts:44` |
| `editor.ts` | 通用多行输入编辑器 — 用户可见 | `packages/tui/src/components/editor.ts:593` |
| `form.ts` | 表单字段/表单容器 — 用户可见 | `packages/tui/src/components/form.ts:122` |
| `image.ts` | 内联图片渲染 + 图片预算 — 用户可见 | `packages/tui/src/components/image.ts:717` |
| `input.ts` | 单行输入框 — 用户可见 | `packages/tui/src/components/input.ts:65` |
| `key-value-list.ts` | 键值对齐列表 — 用户可见 | `packages/tui/src/components/key-value-list.ts:33` |
| `loader.ts` | spinner/工作行列组件 — 用户可见 | `packages/tui/src/components/loader.ts:108` |
| `markdown.ts` | Markdown 渲染组件 — 用户可见 | `packages/tui/src/components/markdown.ts:1713` |
| `menu-selection.ts` | 菜单选择状态机（无渲染） — 仅内部 | `packages/tui/src/components/menu-selection.ts:80` |
| `metric.ts` | 内联指标行/格式化 — 用户可见 | `packages/tui/src/components/metric.ts:86` |
| `progress-bar.ts` | 进度条组件 — 用户可见 | `packages/tui/src/components/progress-bar.ts:89` |
| `scroll-view.ts` | 可滚动视图组件 — 用户可见 | `packages/tui/src/components/scroll-view.ts:112` |
| `scroll-viewport.ts` | 视口几何纯函数 — 仅内部 | `packages/tui/src/components/scroll-viewport.ts:35` |
| `section.ts` | 标题+分隔线区块容器 — 仅内部 | `packages/tui/src/components/section.ts:39` |
| `select-list.ts` | 可选择菜单列表 — 用户可见 | `packages/tui/src/components/select-list.ts:158` |
| `settings-list.ts` | 设置列表/设置表单字段 — 用户可见 | `packages/tui/src/components/settings-list.ts:171` |
| `spacer.ts` | 空白行占位容器 — 仅内部 | `packages/tui/src/components/spacer.ts:16` |
| `tab-bar.ts` | 标签栏组件 — 用户可见 | `packages/tui/src/components/tab-bar.ts:60` |
| `table.ts` | 定宽表格组件 — 用户可见 | `packages/tui/src/components/table.ts:94` |
| `text.ts` | 文本容器原语 — 仅内部 | `packages/tui/src/components/text.ts:26` |
| `tree-view.ts` | 可交互树视图 — 用户可见 | `packages/tui/src/components/tree-view.ts:216` |
| `truncated-text.ts` | 截断文本原语 — 仅内部 | `packages/tui/src/components/truncated-text.ts:10` |
| `wizard-step.ts` | 向导步骤容器 — 用户可见 | `packages/tui/src/components/wizard-step.ts:50` |
| `composer/band.ts` | band composer 形状样式表 — 仅内部 | `packages/tui/src/components/composer/band.ts:10` |
| `composer/borderless.ts` | borderless 形状样式表 — 仅内部 | `packages/tui/src/components/composer/borderless.ts:9` |
| `composer/box.ts` | box 形状样式表 — 仅内部 | `packages/tui/src/components/composer/box.ts:9` |
| `composer/claude.ts` | claude 形状样式表 — 仅内部 | `packages/tui/src/components/composer/claude.ts:11` |
| `composer/field.ts` | field 形状样式表 — 仅内部 | `packages/tui/src/components/composer/field.ts:12` |
| `composer/index.ts` | 形状桶导出（barrel） — 仅内部 | `packages/tui/src/components/composer/index.ts:1` |
| `composer/pi.ts` | pi 形状样式表 — 仅内部 | `packages/tui/src/components/composer/pi.ts:9` |
| `composer/rail.ts` | rail 形状样式表 — 仅内部 | `packages/tui/src/components/composer/rail.ts:11` |
| `composer/registry.ts` | composer 形状注册表/查询 — 仅内部 | `packages/tui/src/components/composer/registry.ts:44` |
| `composer/rule.ts` | rule 形状样式 + 顶栏渲染 — 仅内部 | `packages/tui/src/components/composer/rule.ts:27` |
| `composer/types.ts` | 形状类型/内置 id 列表 — 仅内部 | `packages/tui/src/components/composer/types.ts:15` |
| `layout/geometry.ts` | 布局几何/尺寸分配函数 — 仅内部 | `packages/tui/src/components/layout/geometry.ts:63` |
| `layout/row.ts` | 水平布局容器 — 仅内部 | `packages/tui/src/components/layout/row.ts:85` |
| `layout/split-pane.ts` | 左右分栏容器 — 仅内部 | `packages/tui/src/components/layout/split-pane.ts:80` |
| `layout/stack.ts` | 垂直布局容器 — 仅内部 | `packages/tui/src/components/layout/stack.ts:76` |

### render/（共 14 条）
> 数法（payload 原文）：render/（补充发现 · 共 14 条；数法：glob packages/tui/src/render/*.ts）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `code-cell.ts` | 代码/输出预览渲染 — 用户可见 | `packages/tui/src/render/code-cell.ts:130` |
| `file-list.ts` | 文件树列表渲染 — 用户可见 | `packages/tui/src/render/file-list.ts:59` |
| `hyperlink.ts` | OSC-8 超链接工具 — 仅内部 | `packages/tui/src/render/hyperlink.ts:53` |
| `index.ts` | render 桶导出（barrel） — 仅内部 | `packages/tui/src/render/index.ts:5` |
| `output-block.ts` | 带框输出块渲染 — 用户可见 | `packages/tui/src/render/output-block.ts:75` |
| `output-pane.ts` | 输出面板组件（截断/滚动） — 用户可见 | `packages/tui/src/render/output-pane.ts:155` |
| `render-utils.ts` | 渲染常量/工具（预览限长等） — 仅内部 | `packages/tui/src/render/render-utils.ts:35` |
| `sixel.ts` | SIXEL 序列检测/透传 — 仅内部 | `packages/tui/src/render/sixel.ts:29` |
| `status-line.ts` | 单行状态头渲染 — 用户可见 | `packages/tui/src/render/status-line.ts:33` |
| `tool-card.ts` | 工具卡组件/工厂 — 用户可见 | `packages/tui/src/render/tool-card.ts:130` |
| `tree-list.ts` | 树列表渲染 — 用户可见 | `packages/tui/src/render/tree-list.ts:42` |
| `types.ts` | 渲染状态/树类型 — 仅内部 | `packages/tui/src/render/types.ts:7` |
| `utils.ts` | 哈希/渲染缓存/树工具 — 仅内部 | `packages/tui/src/render/utils.ts:23` |
| `width-aware-text.ts` | 宽度感知文本组件原语 — 仅内部 | `packages/tui/src/render/width-aware-text.ts:21` |

### native/（共 15 条）
> 数法（payload 原文）：native/（补充发现 · 共 15 条；数法：glob packages/tui/src/native/*.ts）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `apply.ts` | TSP 文档应用/错误类型 — 仅内部 | `packages/tui/src/native/apply.ts:38` |
| `backend.ts` | 原生 TUI 渲染后端 — 仅内部 | `packages/tui/src/native/backend.ts:232` |
| `blobs.ts` | 图像 blob 注册/缓存 — 仅内部 | `packages/tui/src/native/blobs.ts:29` |
| `describe.ts` | 原生节点构造 helper — 仅内部 | `packages/tui/src/native/describe.ts:16` |
| `encode.ts` | TSP 协议编解码 — 仅内部 | `packages/tui/src/native/encode.ts:85` |
| `icons.ts` | PUA 图标 span 归一化 — 仅内部 | `packages/tui/src/native/icons.ts:40` |
| `memo.ts` | 记忆化（Memo/OwnerMemo） — 仅内部 | `packages/tui/src/native/memo.ts:26` |
| `node.ts` | 原生节点/事件类型 — 仅内部 | `packages/tui/src/native/node.ts:20` |
| `overlay.ts` | 原生 overlay 组件 helper — 仅内部 | `packages/tui/src/native/overlay.ts:42` |
| `picker.ts` | 原生 picker 描述/路由 helper — 仅内部 | `packages/tui/src/native/picker.ts:28` |
| `reconcile.ts` | 原生表面协调器 — 仅内部 | `packages/tui/src/native/reconcile.ts:207` |
| `settle.ts` | 组件最终化标记 — 仅内部 | `packages/tui/src/native/settle.ts:16` |
| `spans.ts` | ANSI 文本→span 转换 — 仅内部 | `packages/tui/src/native/spans.ts:239` |
| `state.ts` | 原生渲染开关状态 — 仅内部 | `packages/tui/src/native/state.ts:13` |
| `tone.ts` | 颜色→tone/role 映射 — 仅内部 | `packages/tui/src/native/tone.ts:11` |

### theme/（共 18 条）
> 数法（payload 原文）：theme/（补充发现 · 共 18 条；数法：glob packages/tui/src/theme/* = 17 顶层 + defaults/index.ts；另 defaults/ 下 100 个预设 JSON 见 registry）

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `tui-adapters.ts` | 主题→TUI 适配器（高亮/md/编辑器主题） — 仅内部 | `packages/tui/src/theme/tui-adapters.ts:103` |
| `theme.ts` | 活动主题单例/初始化/切换 — 仅内部 | `packages/tui/src/theme/theme.ts:93` |
| `theme-schema.json` | 主题 JSON schema（数据） — 仅内部 | `packages/tui/src/theme/theme-schema.json:1` |
| `theme-class.ts` | Theme 类（fg/bg/symbol 访问） — 仅内部 | `packages/tui/src/theme/theme-class.ts:163` |
| `shimmer.ts` | 微光扫过动画渲染 — 仅内部 | `packages/tui/src/theme/shimmer.ts:193` |
| `session-color.ts` | 会话强调色派生 — 仅内部 | `packages/tui/src/theme/session-color.ts:182` |
| `schema.ts` | 主题 JSON/颜色 token 类型 — 仅内部 | `packages/tui/src/theme/schema.ts:9` |
| `schema-validation.ts` | 主题 schema 校验 — 仅内部 | `packages/tui/src/theme/schema-validation.ts:122` |
| `mermaid-cache.ts` | mermaid→ASCII 渲染缓存 — 仅内部 | `packages/tui/src/theme/mermaid-cache.ts:103` |
| `light.json` | 基础浅色主题定义（数据） — 仅内部 | `packages/tui/src/theme/light.json:1` |
| `dark.json` | 基础深色主题定义（数据） — 仅内部 | `packages/tui/src/theme/dark.json:1` |
| `color.ts` | 颜色→ANSI/hex 工具 — 仅内部 | `packages/tui/src/theme/color.ts:29` |
| `symbols.ts` | 符号/glyph/spinner 表 — 仅内部 | `packages/tui/src/theme/symbols.ts:1461` |
| `glyph-bundle.json` | glyph 打包数据（数据） — 仅内部 | `packages/tui/src/theme/glyph-bundle.json:1` |
| `active-symbols.ts` | 活动主题符号查询 — 仅内部 | `packages/tui/src/theme/active-symbols.ts:18` |
| `index.ts` | theme 桶导出（barrel） — 仅内部 | `packages/tui/src/theme/index.ts:1` |
| `loader.ts` | 内置/自定义主题加载 — 仅内部 | `packages/tui/src/theme/loader.ts:109` |
| `defaults/index.ts` | 100 个内置主题预设的注册表 — 仅内部 | `packages/tui/src/theme/defaults/index.ts:102` |

## 45. 鼠标与终端交互（共 20 条）

> 数法（payload 原文）：鼠标 / 触控（MOUSE_TRACKING + SGR 解析） 共 20 条

| 名字 | 一句话（≤40 字） | 出处 |
|---|---|---|
| `MOUSE_TRACKING_ON/OFF` | ?1000h?1003h?1006h 开启/关闭 | `packages/tui/src/tui.ts:100,101` |
| `全屏 overlay 自动开鼠标` | fullscreen 且 options.mouseTracking!==false => full | `packages/tui/src/tui.ts:3359` |
| `inline 鼠标 provider(tui.mouse)` | 正常缓冲点击捕获由产品选项控制 | `packages/tui/src/tui.ts:956-957,3388` |
| `parseSgrMouse` | 解码 SGR：wheel/motion/leftClick | `packages/tui/src/mouse.ts:39` |
| `routeSgrMouseInput` | 转发给 handler，未处理返回 false | `packages/tui/src/mouse.ts:61` |
| `routeSelectListMouse` | wheel→handleWheel，点击→hitTest | `packages/tui/src/mouse.ts:85` |
| `agent-hub wheel/hover/click` | 侧栏/详情滚轮、行悬停、点击选+开 | `packages/tui/src/overlays/agent-hub.ts:568` |
| `agent-transcript-viewer wheel` | 滚轮 ×3 | `packages/tui/src/overlays/agent-transcript-viewer.ts:487` |
| `agents-hub wheel/click/hover` | 侧栏滚轮、body 行选择、chip 点击 | `packages/tui/src/overlays/agents-hub.ts:925` |
| `advisor-config wheel` | 右侧预览滚轮 | `packages/tui/src/overlays/advisor-config.ts:850` |
| `copy-selector wheel/click` | 滚轮 ×3、左键点击 | `packages/tui/src/overlays/copy-selector.ts:437` |
| `model-browser wheel/hover/click` | 滚轮平移窗口、悬停、点击选/再点激活 | `packages/tui/src/overlays/model-browser.ts:1218` |
| `model-hub wheel/hover/click` | 侧栏/行/浏览器滚轮，chip 点击 | `packages/tui/src/overlays/model-hub.ts:2079` |
| `oauth-selector wheel/click` | 滚轮 ±1、点击确认 | `packages/tui/src/overlays/oauth-selector.ts:624` |
| `plan-review wheel/hover/click` | 滚轮 ×3、悬停高亮、点击选项/ToC/正文 | `packages/tui/src/overlays/plan-review-overlay.ts:604` |
| `rewind-selector wheel` | 滚轮 ×3 | `packages/tui/src/overlays/rewind-selector.ts:344` |
| `session-selector wheel/click` | 滚轮移动、点击行选中确认 | `packages/tui/src/overlays/session-selector.ts:1892` |
| `settings-selector wheel/hover/click` | 滚轮/hover/点击命中项 | `packages/tui/src/overlays/settings-selector.ts:1224` |
| `usage-dashboard wheel` | 滚轮 ×2 | `packages/tui/src/overlays/usage-dashboard.ts:1369` |
| `extension-dashboard wheel/click/hover` | 列表/inspector 滚轮、点击、hover | `packages/tui/src/overlays/extensions/extension-dashboard.ts:310` |

## 附. 没查完的 / 已知缺口

- 运行时内容不可静态列全（设计如此）：各 provider 的 `commands/`、`prompts/`、插件 `commands/`、MCP server 与其 prompts、用户 skills —— 名字来自运行时文件系统/网络枚举（`packages/coding-agent/src/extensibility/extensions/loader.ts:117`、`packages/coding-agent/src/sdk.ts:1462-1465`、`packages/coding-agent/src/extensibility/skills.ts:609-611`）。
- 扩展/插件/MCP 经 `api.registerCommand` 注册的命令名只在运行时才能枚举（`packages/coding-agent/src/slash-commands/available-commands.ts:78-96`、`packages/coding-agent/src/modes/interactive-mode.ts:2558-2561`）；出货源码中仅 `autoresearch` 一处静态可列（`packages/coding-agent/src/autoresearch/index.ts:125`）。
- 文件型 markdown / prompt 模板 / 外部 provider（claude/codex/opencode/agents）的 `commands/` 目录名字取决于用户磁盘，无静态清单（`packages/coding-agent/src/discovery/claude.ts:303-323`、`packages/coding-agent/src/discovery/builtin.ts:349-355`）。
- MCP prompt 命令名 `<server>:<prompt>` 需连接服务器才知道（`packages/coding-agent/src/sdk.ts:1462`）。
- launch/acp/__complete 三处 `static strict=false`：未识别 token 透传给扩展运行时 flag 注册表（`packages/coding-agent/src/cli/extension-flags.ts:36` → `packages/coding-agent/src/cli/args.ts:206`），flag 面无法静态穷举（`packages/coding-agent/src/commands/launch.ts:24`、`packages/coding-agent/src/commands/acp.ts:16`、`packages/coding-agent/src/commands/complete.ts:18`）。
- launch help 只声明 51 个 flag，parseArgs 经 `flag-tables.ts` 还接受 6 个 help 未声明的 flag：`--fork(:131)`、`--provider-session-id(:178)`、`--prompt-cache-key(:181)`、`--trusted-extension(:220)`、`--plugin-dir(:224)`、`--session(:252)`（`packages/coding-agent/src/cli/flag-tables.ts`）。
- `--acp-terminal-auth` 是 `packages/coding-agent/src/modes/acp/terminal-auth.ts:1` 的 `ACP_TERMINAL_AUTH_FLAG`，由 `prepareAcpTerminalAuthArgs` 预先剥离，completions/help 均不显示。
- plugin 的 `marketplace <sub>` / `config <sub>` 二级子动作由运行时 switch 处理、无枚举约束（`packages/coding-agent/src/cli/plugin-cli.ts:213`、`:866`）；本表已据 switch 补全为 add/remove/rm/update/list 与 list/get/set/delete/validate。
- `RESERVED_TOP_LEVEL_WORDS`（`packages/coding-agent/src/cli-commands.ts:314`）的 9 个动词是拦错提示、不是子命令；参考文档若当作顶层命令会误列。
- 设置项 `theme.dark`/`theme.light`、`composer.shape` 的默认可读，但可选值是运行时主题注册表（`ui.options:"runtime"`），静态列不全（`packages/coding-agent/src/modes/settings.ts:63,77,127`）。
- `treeFilterMode` 值集在 `@oh-my-pi/pi-tui/overlays/tree-selector`（`packages/coding-agent/src/modes/settings.ts:870`）。
- `statusLine.leftSegments/rightSegments/segmentOptions` 值来自 `@oh-my-pi/pi-tui/status-line/schema`（`packages/coding-agent/src/modes/settings.ts:279,286,290-293`）。
- `spelling.autocomplete` 的 `values` 外部导入，darwin 追加 apple（`packages/coding-agent/src/modes/settings.ts:916,918-941`）。
- `magicKeywords.<id>` 的 key 动态生成，id 来自 `packages/coding-agent/src/modes/magic-keywords.ts:96-135`（`packages/coding-agent/src/modes/settings.ts:1118-1129`）。
- `setupVersion` 无 UI、无用户可见语义（`packages/coding-agent/src/modes/settings.ts:27`）。
- 枚举值来自导入常量数组、未展开字面量：ADVISOR_SYNC_BACKLOG_MODES/ADVISOR_REVIEW_MODES、SERVICE_TIER_*_VALUES、TINY_MODEL_DEVICE/DTYPE_SETTING_VALUES、TTS_LOCAL_VOICE_VALUES、LIVE_VOICE_VALUES、STT_SUBMIT_TRIGGER_VALUES、THINKING_EFFORTS（源在 pi-tui/pi-catalog 与兄弟常量模块）。
- 未解引用的常量：DEFAULT_USAGE_RESERVE_PCT、DEFAULT_WEB_SEARCH_TIMEOUT_SECONDS、TINY_MODEL_DEVICE_DEFAULT/DTYPE、ADVISOR_DEFAULT_BUDGET_PER_UPDATE、DEFAULT_SKILLS_URL、DEFAULT_RELAY_URL、DEFAULT_SHARE_URL、DEFAULT_STREAM_URL、DEFAULT_IMAGES_URLS_BACKENDS、DEFAULT_BASH_INTERCEPTOR_RULES、DEFAULT_COMPACTION_METHOD_ORDER、DEFAULT_TTS_VOICE、DEFAULT_LIVE_VOICE、HINDSIGHT_RECALL_TYPES_DEFAULT。
- 部分 no-UI 布尔/数字 register 只由 id/type 推断语义，标 `[未核实]`（`packages/coding-agent/src/*/settings.ts`）。
- combine() 容器（无新键，仅分组已列句柄）：`session/settings.ts` 6、`context-settings.ts` 1、`tools/settings.ts` 2、`exec/settings.ts` 1、`ttsr-settings.ts` 1、`extensibility/settings.ts` 1、`blob-broker/settings.ts` 1、`commit/settings.ts` 1。
- `packages/coding-agent/src/capability/settings.ts` 不是 register 设置表（是 capability 注册）；`packages/coding-agent/src/config/settings.ts` 与 `packages/coding-agent/src/config/all-settings.ts` 无 register 调用。
- `packages/tui/src/chrome/selector-helpers.ts:80` 的 handleTabSwitchKey 等属 `chrome/`，未纳入面板键表分组。
- 面板鼠标组只列显式解析 SGR 的面板；哪些 overlay 是 fullscreen 由各调用点 options 决定，无法仅凭目录静态列全（`packages/tui/src/tui.ts:3359`）。
- `packages/tui/src/components/editor.ts` 大部分动作走注册表 `kb.matchesCanonical` 与 `vim.ts`；本表只列其硬编码字面量与注册表动作名（详见 §42）。
- `packages/tui/src/apps/autoresearch-dashboard.ts:217` 的 handleInput 属函数内联匿名 Component，无导出类名。
- `packages/tui/src/apps/ps-top.ts:851` 显式 `mouseTracking:false`；`packages/tui/src/apps/git/git-tui.ts:1218` 显式 true 并有完整 SGR 处理。
- `packages/tui/src/overlays/model-hub.ts` 的 Roles 视图动作键 `ROLES_ACTION_KEYS`（:220-230）仅在 Roles 视图且 list 焦点生效。
- `packages/tui/src/theme/defaults/` 下 100 个 `*.json` 颜色预设属数据，仅记数不逐行。
- UI 目录逐文件的"用户可见/仅内部"是判定性分类，未逐文件回溯全部调用点，个别边界件可能互换（`packages/tui/src/chrome/**`、`packages/tui/src/chat/**`、`packages/tui/src/prompt/**`、`packages/tui/src/components/**`）。
- `packages/tui/src/vim.ts` 内部非按键机制（#desiredCol、#clampNormal、visualRange 端点归一化、count 展开）不计独立命令。
- `packages/tui/src/components/editor.ts` 动作名限定于本体；composer 层（`packages/tui/src/prompt/composer.ts`、`packages/tui/src/prompt/custom-editor.ts`）另绑定的键未覆盖。
- `tui.input.copy` 与 `tui.select.confirm` 已在 `packages/tui/src/keybindings.ts:35,41` 注册，但 editor.ts 无 `matchesCanonical` 消费（据实列为"未使用"）。
- 被委托组件（SelectList/ModelBrowser/OAuthSelector/WizardStep）位于 components|overlays 而非 setup/，标 `[共享]`；WizardStep 自身无按键（`packages/tui/src/components/wizard-step.ts:150-152`）。
- `@`文件提及的完整下游链路只确认到触发点与前缀解析，未逐行追踪附件消费端（`packages/tui/src/components/editor.ts:3108-3127`、`packages/tui/src/autocomplete.ts:116,842`、`packages/coding-agent/src/session/model-mentions.ts:92-94`）。
- help/theme 的历史意图未做 git 历史核实（当前工作树确证无 slash 实现，见 §37）。
- slash 命令触发的面板映射来自 controller 的 `show*` 方法，个别触发方式（键盘 vs 仅命令）未逐个回溯确认。
- 计数对不上（表头 X 一律取实际数据行数）：payload 参数补全项标题声明 15、实列 16；CLI `install` 标题声明 4 条、实列 7；无键位文件标题声明 45、实列 42；`components/select-list.ts` 标题"共 8 键行 + 鼠标"实列 9；vim ①声明 79 实列 76、editor ②声明 65 实列 57、setup ③声明 69 实列 63。
- （编者注）本文档把 payload（OmpUi）单组"面板与选择器（overlays/）共 63 文件"拆为 §20、§21 两节（顶层 63 + extensions/ 4 行），以保持"每组行数 = 表头 N"；合计 67 = payload 该组实际列出的行数（payload 声明 63 = overlays 顶层 .ts 数，另 4 行为 extensions/ 子目录）。
