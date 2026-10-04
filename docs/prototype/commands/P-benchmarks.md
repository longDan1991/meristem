# 命令 · P 基准与实验（CLI 为主）

> **这一块是什么**：跑基准、造实验——拿数字，不是干活。
> **用户什么时候来**：用户想知道「哪个模型快、哪个听话」。
> **状态**：骨架 —— 只列「模块 + 旗下命令」，**还没做决策**。这是 [`../reference/commands.md`](../reference/commands.md) §P 的分册，**同一条不多不少**（这一块 omp 3 条 · jcode 0 条）。
> 「面」这一列 = 用户从哪儿碰到它：`TUI` = 敲 `/` 或在界面里；`CLI` = 在命令行敲 `omp …` / `jcode …`。

## 子模块（这一块分成哪几叶）

| 叶 | 是什么 | omp | jcode | 合计 |
|---|---|---|---|---|
| P | 基准与实验（CLI 为主） | 3 | 0 | 3 |
| **合计** | | **3** | **0** | **3** |

## 两家的命令（先例原样）

### P 基准与实验（CLI 为主）

| 家 | 面 | 命令 | 一句话 | 出处 |
|---|---|---|---|---|
| omp | CLI | `omp bench` | 模型 TTFT/吞吐基准 | `packages/coding-agent/src/cli-commands.ts:56` |
| omp | CLI | `omp if-bench` | 指令遵循与工作记忆基准 | `packages/coding-agent/src/cli-commands.ts:144` |
| omp | CLI | `omp predict` | 对比各补全引擎 ghost text [归类存疑] | `packages/coding-agent/src/cli-commands.ts:175` |

## 口径与存疑（事实，不是决策）

- **`[归类存疑]` 1 条**（该条不完全贴叶，正文对应行末尾已标）：``omp predict``（omp，P）
- 别名折叠规则与折掉的别名清单：见 [`../reference/commands.md`](../reference/commands.md) 附录（只此一处，不两说）。
