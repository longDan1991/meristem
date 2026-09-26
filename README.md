# meristem

> 一棵递归工作的 LLM 树：节点自己决定要不要分叉，根节点负责收敛成结论。

[English](README.en.md) · 中文

> **状态：alpha。** 系统提示词结构与协议仍在演进，不承诺稳定；未发布到 PyPI（`[tool.uv] package = false`），按应用运行。

---

## 这是什么

一个跑在终端里的 agent 运行时。任务**不是**预先编排成 DAG，而是模型在树上递归展开：

- 一个节点用 `create_children` 派生子节点，子节点各自是一段独立对话；
- 每个节点的对话是平的，有自己的账本（`core/runtime/dialogue.py`）；
- 根节点用 `submit_root` 收敛成结论，普通节点用 `conclude` 收尾；
- **唯一的控制流是一个 Loop**（`core/runtime/loop.py`）——一棵树只由它推进；
- 一场会话 = 一棵树 + 一份 append-only 记录（`core/runtime/store.py`），**写入即账**；
- 验收**不采信模型自报**：`core/protocol/gate.py` 对形式字段做机械校验，只核对指得到的东西。

## 三个设计取舍

**1. system 提示词不是拼好的字符串，是命名分节的数据结构。**

`system = Record<节名, 内容>`：每节一个同名 XML 标签，哪些节在场由节点**出生时**已知的静态属性决定，生命周期内不再变。散文、纪律、条件 skill、工具清单各成一个节（`core/prompts/`）。不变量写在 `docs/PROMPTS.md`。

**2. 工具 schema 是工具语义的唯一来源。**

`rules` 节从工具清单推导，`tools` 节一行一个工具（`core/prompts/tools.py`），清单本身从工具的 scope 声明派生。工具就是 `@mcp.tool` 函数——schema 与实现一体，没有第二份需要同步的定义（`tools/defs.py`）。

**3. bash 工具不 fork / exec。**

命令跑在 [`llmbash`](https://pypi.org/project/llmbash/) 上——本仓库之外的一个进程内 bash 兼容 shell（Rust 实现，50+ 常用命令不依赖系统二进制），输出进上下文前先按命令类型瘦身（`tools/bash.py`）。

## 代码地图

```
cli.py              唯一可执行入口：解析参数
main.py             初始化（工作区 / API key / 记录根）后派发给终端会话

core/
  config.py         部署配置：工作区在哪、历史会话扫哪里
  events.py         事件出口：把 (type, payload) 按注册顺序分发给消费者
  llm.py            LLM 适配层：给 messages，返回 Message（文本 + 工具调用）
  prompts/          system 的命名分节结构（prose / rules / skills / tools）
  protocol/         形式字段（fields）+ 机械闸门（gate）+ 节点消息渲染（messages）
  runtime/          唯一的 Loop + 协议操作（ops）+ 调度纯规则（plan）+ 会话存储（store）
tools/              模型与程序之间唯一的通道
  defs.py           @mcp.tool 函数：schema 与实现一体
  bash.py           命令跑在 llmbash 进程内 shell 上
  skills.py         SKILLS_DIRS 下 */SKILL.md → fastmcp 资源，模型按需 read_skill
terminal/           Textual 应用：左树右流五区（docs/TERMINAL.md）
```

## 跑起来

`.env` 里给四项：

```bash
export TREE_BASE_URL='...'        # 模型端点（OpenAI 兼容）
export TREE_API_KEY='...'
export TREE_MODEL='...'
export TREE_WORKSPACE='/path/to/workspace'   # 跑出来的东西全落这里
```

```bash
uv run python cli.py        # 真跑：任务与验收标准在终端里谈定
uv run python cli.py -r     # 接着上次的会话：列表选一个加载成当前会话
```

不给 `TREE_API_KEY` 会直接在入口报错退出——不会静默换假模型。

## 测试

```bash
uv run python tests/test_<module>.py     # cli / intake / llm / protocol / resume / terminal_pty / tools / tty
uv run ruff check                        # 代码纪律，见 AGENTS.md §12
```

测试用假模型（`FakeLLM`）驱动，不需要真实 API key。

## 文档

| 文档 | 写什么 |
|---|---|
| `docs/PROMPTS.md` | 系统提示词的设计与**不变量** |
| `docs/TERMINAL.md` | 终端布局的设计与**不变量** |
| `AGENTS.md` | 本仓库的硬约束禁令清单，能机器判定的部分由 ruff 执行 |

## License

MIT
