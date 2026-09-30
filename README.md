# meristem

> 人的工作树：**人递归，模型在一条线里干活。**

[English](README.en.md) · 中文

> **状态：alpha。** 结构与协议仍在演进；按应用运行（`private: true`，不发包）。

---

## 这是什么

一个跑在终端里的 agent 运行时。任务**不是**自动递归拆出来的：拆与收都是人做的。

- **人负责拆和收**：说一句开一条线（`enter`）、从某条线分叉（`ctrl+b`）、收手（`ctrl+x`）。
- **每条线是一个角度**：线上是一段对话，模型带着这个角度的角色（提示词 + 工具）去做；人随时进去接着说。
- **分叉是一条新线**：上下文从分叉点长出来，不是把整段历史复制一份。
- **写账只有一个出口**：说一句 / 分叉 / 停 —— 界面碰不到别的地方。
- **账就是成果**：append-only 的 JSONL，写入即账；不另建成果库、不另建索引。

为什么要人来做递归（而不是让模型自己拆完）：旧实现的实测判决书在 `docs/DESIGN.md` §1
——一晚 2443 个节点、86% 从未完工，自报字段被 game 到 69%，根以下只有 3% 的判据还提到最初的目标。

## 三个设计取舍

**1. 人是递归的主体，模型是执行的主体。**
漂移发生在中间每一次自动分配里，而人的介入只有两头时粒度太粗。所以分叉由人做，注意力在分叉时分开。

**2. system 提示词是命名分节的数据结构，不是拼出来的字符串。**
每节一个同名 XML 标签，节恒在、生命周期内不变；工具 schema 是工具语义的唯一来源（模型的每只手都从 schema 与描述长出来，没有第二份定义要同步）。

**3. 屏幕、Loop、能力、账，各归各的包。**
`tui` 只画屏幕（按**格**数、贴底、宽字符不许只露一半），`harness` 只管唯一的 Loop 与传输，
`roles` 管角色与手（含作业机制），`atree` 管账（append-only + 可 resume）。装配是 `terminal` 的事。

## 代码地图

```
packages/
  atree/      账：节点形状 + append-only 的 JSONL 账本（写入即账，能 resume）
  harness/    唯一的 Loop + 传输（把模型的话与手的结果接上）+ 缺陷节点
  roles/      角色（一个 xml 一个角色）、手（工具）、技能、作业表、MCP（未接）
  tui/        屏幕：五区组件各一文件（树条带 / 消息流 / 实时卡片 / 状态条 / 输入行）
  terminal/   装配与交互：配置（.env）→ 账 → 角色 → 传输 → 树 → 界面
docs/DESIGN.md    这棵树的设计（为什么长这样、哪些是不变量）
AGENTS.md         本仓库的硬约束禁令清单
```

## 跑起来

`.env` 放在**仓库根**（键名与格式见 `.env.example`；`.env` 不进版本控制）：

```bash
export MERISTEM_BASE_URL='https://…'    # OpenAI 兼容端点（不给就用 provider 自带的）
export MERISTEM_API_KEY='…'             # 钥匙值本身
export MERISTEM_MODEL='provider/model'
export MERISTEM_WORKSPACE='/abs/path'   # agent 的做事目录；账落 <它>/.tree/ledger.jsonl
```

```bash
bun install
bun start            # 真跑。空账也能起：连根都没有时，第一句话就是第一条线
bun start --at <id>  # 直接站到某个节点那条线上
```

`.env` 只从**起进程的目录**加载（Bun 不往上找），所以别处的目录起就要先把变量放进环境；
缺必填项会在入口带着变量名报错退出——不兜底、不静默换假模型。

## 测试

```bash
bun run typecheck    # 两套 tsconfig
bun test             # 无头用例（要真进程的那条自带子进程夹具）
```

## License

MIT
