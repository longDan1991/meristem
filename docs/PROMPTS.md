# 树作为宿主：系统提示词 = 命名分节结构（pi 范式）

> 这份文档只写**本质**：节点的 system 消息为什么长这样、哪些是不变量。
> 实现步骤在 §6；进度与交接在 `HANDOVER.md`。

---

## 0. 一句话

> **system 不是"拼好的字符串"，是命名分节的数据结构（`Record<节名, 内容>`）：**
> 每节一个同名 XML 标签，按节点出生时已知的静态属性决定哪些节在场。
> 工具语义的唯一来源是工具 schema；rules 从工具清单推导；skills 是"已激活的节"。
> 这是成熟宿主 pi（`pi-coding-agent`）的范式，不向现有 `.md` 拼接妥协。

---

## 1. 设计基准：pi 的 system prompt 范式

从 `pi/packages/coding-agent/src/core/system-prompt.ts`（成熟实现）提炼，它直接决定本设计：

```typescript
// system prompt 是命名分节结构，不是字符串拼接
export type SystemPromptSections = Record<string, string>;
sections[name] = `<${name}>\n${content}\n</${name}>`;   // 每节包同名 XML 标签
const SYSTEM_PROMPT_SECTION_NAME = /^[a-z][a-z0-9_-]*$/;  // 节名机器校验
diffSystemPromptSections(previous, current)               // 按节 diff：只重放变化的节
```

**pi 的节**（每节独立、可替换）：`preamble`（无标签）/ `tools`（一行一个工具片段）/
`rules`（**从 selectedTools 推导** + 工具贡献的 guidelines + 全局纪律）/ `docs` /
`addendum`（用户配置）/ `project_context`（AGENTS.md 分层，包 `<project_instructions path>`）/
`skills`（`<available_skills>` 清单，模型按需读全文）/ `cwd` / custom sections。

**本设计从此范式的推论：**

1. **节是数据，不是文件**：system 组装 = 构造 `dict[节名 → 内容]`，不是 `join` 字符串。
   节名 = XML 标签名（模型靠它解析、靠它匹配增量更新）。
2. **按节可测 / 按节可 diff**：哪节在、哪节不在、每节内容——独立断言；未来某节要
   动态化（如带当前回合信息），只重放该节，其余节不变（KV 缓存按节命中）。
3. **rules 从工具推导**：工具清单决定操作纪律，不是手写死。
4. **skills = 已激活的节**：树系统的 skill 触发条件是宿主已知的静态事实
   （`node.gate`），宿主以"节"为单位注入 = 激活，模型不需要
   "按需读文件"（那是给模型自主选 skill 的场景用的；树的触发者是宿主）。

---

## 2. 背景：为什么不能那样（重构前的问题）

重构前的三个整块散文 `prompts/alloc.md` / `leaf.md` / `intake.md` 有三个问题：

**W1 · 无结构。** 使命 / 流程 / 工具描述 / 规则 / 动态说明全混一个 blob，没有
可供模型稳定解析的分段（pi / Anthropic 都是 XML 分段 + 命名节）。

**W2 · 工具语义重复。** `leaf.md` 里"run_code —— 写一段代码……"和当时的 `tool_specs.py` 里
`@mcp.tool run_code` 的 docstring 是同一语义两处实现；
`bash`/`read`/`write` 当时只有 leaf.md 一份（沙箱内置函数），工具化后同样只能有
schema 一份。MCP 协议对 `instructions` 明文禁止重复："Should not duplicate
information already in tool descriptions"（`mcp_types/_types.py:601`）。

**W3 · 无关内容常驻。** 每个叶子不管是否门槛，都背整段 gate 规则。
pi 的做法是条件拼接片段；本设计按"节在场性"做同样的事。

---

## 3. 命名分节结构：树的 system 由哪些节组成

### 3.1 节点回合的 system 节清单

| 节名 | 内容 | 在场规则 | 来源 |
|---|---|---|---|
| `preamble` | 节点使命（无标签的一段话） | 恒在 | 手写 prose |
| `process` | 步骤（两件事） | 恒在 | 手写 prose |
| `tools` | 一行一个工具片段 + 何时用哪个（可一次调多个） | 恒在 | 代码生成（从作用域声明） |
| `rules` | 操作纪律（推导）+ 协议规则（对应 gate.py） | 恒在 | 推导 + 手写 |
| `skills` | 已注册技能清单（name + description 检索面，一行一个） | 恒在 | 代码生成（扫描 `SKILLS_DIRS`，`tools.skills.discovered()`） |
| `input` | user 消息格式说明（7 键 / 意图链 / 观测历史） | 恒在 | 手写 prose |
| `skill_gate` | 你是门槛：不成立整个分支作废、兄弟不启动 | `node.gate` | 手写 prose |

> 注：没有 pi 的 `skills` 元节之外的多余机制 —— 清单节只放 name + description
> （检索面，对齐 oh-my-pi 的 skills 范式），正文按需经 `read_skill` 读
> `skill://<名字>/...`，不整节注入（skill 随版本换代漂移，注入 = 每个节点白背无关内容）。
> 触发者是任务文本：模型看清单判断用哪个，再读全文；`agent-reach` 只是注册进来的
> 一个 skill，机制对它没有任何特殊分支。

### 3.2 每个节点类型的 system 组成（出生时定死，生命周期内不变）

| 节点类型 | 恒在节 | 条件节 |
|---|---|---|
| `alloc` | preamble / process / tools / rules / skills / input | `skill_gate`（若 `node.gate`） |
| `leaf` | preamble / process / tools / rules / skills / input | `skill_gate`（若 `node.gate`） |
| `intake` | preamble / process / tools / rules / skills / input | 无 |

### 3.3 节渲染规则

- 每节渲染成 `<节名>\n内容\n</节名>`；`preamble` 无标签、放在最前。
- 节名必须匹配 `[a-z][a-z0-9_-]*`（违反当场报错，§2 不掩盖）。
- 节在 system 里的**渲染顺序固定**（按 3.1 表自上而下），保证 KV 缓存按节命中稳定。

---

## 4. 内容来源与去重规则

1. **工具语义唯一来源 = schema，无例外**（`@mcp.tool` 函数的 pydantic description，
   provider 原样喂模型）。`tools` 节只生成"一行一个工具片段 + 何时用哪个"的
   **决策指导**，不重复工具描述；工具**在哪些层**由声明处的 `tags`（`scope:<层>`）说一次，
   清单由 fastmcp 的可见性功能算出来（`tools/specs.py` 把定义表挂成只读视图 + `enable(tags=…, only=True)`
   + `list_tools()`），`scope_names` 是唯一出口：`tools` 节、发送边界的校验、
   发送给 provider 的 `tools=` 全从它派生。`bash`/`read`/`write` 是叶子的**直接工具**：
   三个工具各自注册、各自 schema description 承载签名 / 超时 / 语义，与其它工具完全同构。
2. **`rules` 节 = 操作纪律（从工具推导）+ 协议规则（手写）**：
   - 推导部分：有 `bash`/`read`/`write` → 文件与命令操作走它们（pi 的
     `buildRules` 同构）；有 `conclude` → "判定满足必须指得出证据"；有
     `create_children` → "除 notes / gate 外必填、带父的可测物理量、最多一个门槛"……
     **工具清单变 → 纪律跟着变**。
   - 手写部分：协议级不变量（gate 语义、阻塞要说清 external），因
     `gate.py` 变。一次回复可以调**多个**工具（并行执行）—— 那是协议允许的，
     不是"必须且只能调一个"。
   - 工具**内部行为**（bash 超时、read 的 offset/limit）归各工具 schema，
     rules 只放"何时用哪个"的决策纪律，不重复。
3. **条件节的触发同源**：`node.gate`（Node 字段）一处。
4. **gate 双语义区分**：`alloc` 的"一次最多一个门槛"是分配节点检查子任务的协议规则，
   **常驻 alloc 的 `rules` 节**；"你是门槛"才抽进 `skill_gate` 条件节。根不给 gate
   （根没有兄弟，`validate_root` 会拒）。

---

## 5. 不变量（改代码前看）

1. **system = 命名分节 `Record<节名, 内容>`**，节名 = XML 标签名，节名通过正则校验。
2. **节组成 = f(节点出生时静态属性)**（kind / gate），节点生命周期内
   不变 → system 字节稳定 → KV 缓存按前缀/按节命中。
3. **工具语义唯一来源 = schema，无例外**（`bash`/`read`/`write` 是叶子的直接工具，
   各住各的 schema description）；**工具在哪些层**也只有一处（声明处的 `scope:<层>` 标签）。
4. **rules 的操作纪律部分从工具清单推导**，不手写死；协议规则因 `gate.py` 变。
5. **每节独立可测**：节在场性（哪节在/不在）+ 每节内容独立断言。
6. **双向核对**：文档点名的节 == 真渲染的节 —— `test_protocol.py` I 段真读本文件
   （节名以反引号形式出现在这里）并在真渲染的 system 里核对。
7. **节渲染顺序固定**（3.3），条件节触发同源（§4.3）。

---

## 6. 实现落点（设计住在哪）

| 设计元素 | 代码 |
|---|---|
| 节组装（`Record<节名,内容>` / `render_system` / `render_turn`） | `core/prompts/__init__.py` |
| 散文节（preamble / process / input） | `core/prompts/prose.py`（每节一个函数，`lines` + join） |
| 条件节（`skill_gate`）/ `skills` 清单节 | `core/prompts/skills.py`，在场规则在 `core/prompts/__init__.py` |
| 通用 skill 加载（扫描 `SKILLS_DIRS` + read_skill 桥） | `tools/skills.py`；根目录 = `core/config.py` 的 `SKILLS_DIRS` |
| `tools` 节（一行一个 + 何时用哪个） | `core/prompts/tools.py`，清单来自 `tools.specs.scope_names` |
| `rules` 节（推导 + 手写） | `core/prompts/rules.py` |
| 任务 / 下层结论消息（7 键、意图链） | `core/protocol/messages.py`，键清单 = `core/protocol/fields.FORM_FIELDS` |
| 工具的作用域声明（哪层能调哪些） | 各工具定义处的 `tags={scope_tag(…)}`（`tools/defs.py` / `tools/bash.py`）；清单 = fastmcp 的可见性视图（`tools/specs.py` 的 `load` / `scope_names`） |
| 硬性要求的机器检查（与 rules 对照） | `core/protocol/gate.py`（必填项 / 锚点继承 / 门槛 / 证据降级 / 根校验） |
| 词表与形式字段 | `core/protocol/fields.py` |

守住这份设计的断言全在 `tests/test_protocol.py`（I 段同构 + 文档 ↔ 节名、K2 节在场性与
字节稳定、M 段作用域声明与注册表一致）；改设计与改代码，两边要同时绿。

---

## 7. 不做的事（YAGNI 边界）

- **user 消息不加 XML 定界**：任务的形状是"行首是字段名"的平铺文本（`base_user`），
  与模型写出去的键同构，不套一层 `<task>`。
- **模型按需读 skill 文件**（Claude Code 的"取 skill"工具）：树的触发条件是宿主已知
  的静态事实，宿主以节为单位注入 = 激活，模型不需要判断——引入取回工具是过度设计。
- **按节 diff / 增量重放**：pi 用它是为会话恢复时省 token；树的 system 在节点生命周期
  内不变，没有动态节，diff 机制不引入（节结构天然支持，需要时再加）。
- **prompt 版本管理平台 / agent 框架**：无需求，不引入。
- **skill 再多切**：只有 `gate` 一个真条件节，其余全部恒在。
