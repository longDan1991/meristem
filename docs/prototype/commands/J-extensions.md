# 命令 · J 扩展与集成

> **这一块是什么**：把它接到我自己的东西上：插件与市场、扩展与 hooks、用户自建命令。
> **用户什么时候来**：用户有现成的东西想接进来。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §J 的分册，**同一条不多不少**（这一块 omp 19 条 · jcode 1 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| J1 | 插件 · 市场 | 17 | 0 | 17 |
| J2 | 扩展 · hooks · ACP | 2 | 1 | 3 |
| **合计** | | **19** | **1** | **20** |

## 两家的命令（先例原样）

### J1 插件 · 市场

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/marketplace` | 管理市场插件源与已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:45` |
| omp | TUI | `/plugins`（别名 `plugin`） | 查看并管理已安装插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:425` |
| omp | TUI | `/marketplace add` | 添加一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:51` |
| omp | TUI | `/marketplace remove` | 移除一个 marketplace 源 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:52` |
| omp | TUI | `/marketplace update` | 更新 marketplace catalog | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:53` |
| omp | TUI | `/marketplace list` | 列出已配置的 marketplace | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:54` |
| omp | TUI | `/marketplace discover` | 浏览可安装的插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:55` |
| omp | TUI | `/marketplace install` | 安装一个插件（无参走交互浏览器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:57（4-tab 多行项）` |
| omp | TUI | `/marketplace uninstall` | 卸载一个插件（无参走选择器） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:61` |
| omp | TUI | `/marketplace installed` | 列出已安装的 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:62` |
| omp | TUI | `/marketplace upgrade` | 升级过期插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:63` |
| omp | TUI | `/marketplace help` | 显示用法指南 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:64` |
| omp | TUI | `/plugins list` | 列出全部已装插件（npm+marketplace） | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:432` |
| omp | TUI | `/plugins enable` | 启用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:433` |
| omp | TUI | `/plugins disable` | 停用一个 marketplace 插件 | `packages/coding-agent/src/slash-commands/builtin-marketplace.ts:434` |
| omp | CLI | `omp plugin`（别名 `plugins`） | 管理插件 | `packages/coding-agent/src/cli-commands.ts:169` |
| omp | CLI | `omp install` | 安装/链接扩展包 [归类存疑] | `packages/coding-agent/src/cli-commands.ts:149` |

### J2 扩展 · hooks · ACP

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | TUI | `/extensions`（别名 `status`） | 打开扩展控制中心面板 | `packages/coding-agent/src/slash-commands/builtin-session.ts:553` |
| omp | CLI | `omp acp` | 以 ACP 协议 over stdio 运行 | `packages/coding-agent/src/cli-commands.ts:36` |
| jcode | CLI | `jcode acp` | 作为 Agent Client Protocol 适配器接入守护进程 | `src/cli/args.rs:164` |

## 口径与存疑（事实，不是决策）

- **J3（用户自建命令）两家都没有「命令」行**：omp 有机制（文件型 markdown 命令 / prompt 模板 / 项目 TS 命令）但那是运行时来源、不是命令表里的一条。
- **`[归类存疑]` 1 条**（该条不完全贴叶，正文对应行末尾已标）：``omp install``（omp，J1）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
