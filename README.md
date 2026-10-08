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
`tui` 只放**通用零件**（名单 / 状态条 / 键的形状 / 渲染器生命周期 / 一处配色）：换一个应用也照样用，
而且 **opentui 已有的就不自己写**（编辑器用它自带的、滚动与折行也用它自带的）；一屏怎么摆、业务词
（手 / 思考 / 线）怎么画住 `terminal`。`harness` 只管唯一的 Loop 与传输，`roles` 管角色与手
（含作业机制），`atree` 管账（append-only + 可 resume）。装配是 `terminal` 的事。

## 代码地图

```
packages/
  atree/      账：节点形状 + append-only 的 JSONL 账本（写入即账，能 resume）
  harness/    唯一的 Loop + 传输（把模型的话与手的结果接上）+ 缺陷节点
  roles/      角色（一个 xml 一个角色）、手（工具）、技能、作业表、MCP（未接）
  tui/        通用零件与两个功能模块：command/（命令模块：一份 yaml 当表 + 唯一的按键监听 +
              订阅原语；**各层只订命令，不碰按键**）、router/（一屏怎么进怎么出）、
              名单 / 状态条 / 渲染器与终端还原 / 一处配色
  terminal/   装配与交互：配置（.env）→ 账 → 角色 → 传输 → 树 → 界面。界面按"变的快慢"分四处：
              layout/（壳：只给屏留一格 + 接全界面共用的那几条命令，一行都不画）、
              screens/（八屏：每一屏自带它自己那几行 —— 主屏带内容区、侧边、状态行、事实行、
              输入行与键行，并且连那条线的状态与动作一起写在 screens/main.tsx 里）、
              components/（页面里的零件：吃 props，不自己去取状态）、
              lib/（树的算法、档与侧边的词表、键行的提示，以及本应用的命令表位置与作用面词表 registry.ts）
docs/DESIGN.md    这棵树的设计（为什么长这样、哪些是不变量）
docs/prototype/   原型档（线框）：三个面描述产品 —— 屏幕（screens/）· 组件（components/）· 命令（commands/）+ 两家先例清单（reference/）；我们自己的原型住 ours/
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

## 设计（dev）

两份技能（`.agents/skills/prototype-design` / `ui-visual-design`）各管一档，产物**零代码关系**：

| 路径 | 是什么 |
|---|---|
| `docs/prototype/` | **原型**（线框）：三个面描述产品 —— **屏幕**（`screens/S0…S12`）· **组件**（`components/M1…M12`）· **命令**（`commands/A…Q`），三处都只写**两家**（先例原样）。`overview.md` = 总体（41 个模块 + 两家对照 + **功能模块优先级**）。**我们自己的原型**住 `ours/`：`P0.md` = **总体规划的索引**（七个承重决策 + 九节目录），细节在 `P0/`（`01-stories` 用户故事 · `02-screens` 屏幕清单与进屏三条路 · `03-layout` 全局布局 · `04-tiers` 内容区三档 · `05-side` 侧边 · `06-switching` 切换 · `07-rules` 全局规则 · `08-handoff` 交接 · `09-open` 待定）。逐条证据住 `reference/` |
| `packages/tui/dev/visual/` | **视觉**：同一个屏画成什么样（参看原型那份 md，自己从零写；不 import 它） |

视觉那一档要真帧 —— 帧由**真渲染器**画出来、经终端模拟器读回格子，就是"这棵树在终端里长什么样"：

```bash
bun run packages/tui/dev/preview/serve.ts packages/tui/dev/visual/five-regions.tsx --cols 120 --rows 40   # 浏览器，改文件即刷新，按 w 切线框
bun run packages/tui/dev/preview/frame.ts packages/tui/dev/visual/five-regions.tsx --cols 120 --rows 40    # 打进真终端：最终真相
```

## License

MIT
