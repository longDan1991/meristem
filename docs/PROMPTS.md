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
   （`node.gate` / `cfg.COMPRESS`），宿主以"节"为单位注入 = 激活，模型不需要
   "按需读文件"（那是给模型自主选 skill 的场景用的；树的触发者是宿主）。

---

## 2. 背景：为什么现在这样不对

重构前的三个整块散文 `prompts/alloc.md` / `leaf.md` / `intake.md` 有三个问题：

**W1 · 无结构。** 使命 / 流程 / 工具描述 / 规则 / 动态说明全混一个 blob，没有
可供模型稳定解析的分段（pi / Anthropic 都是 XML 分段 + 命名节）。

**W2 · 工具语义重复。** `leaf.md` 里"run_code —— 写一段代码……"和
`tool_specs.py` 里 `@mcp.tool run_code` 的 docstring 是同一语义两处实现；
`bash`/`read`/`write` 现在只有 leaf.md 一份（沙箱内置函数），工具化后同样只能有
schema 一份。MCP 协议对 `instructions` 明文禁止重复："Should not duplicate
information already in tool descriptions"（`mcp_types/_types.py:601`）。

**W3 · 无关内容常驻。** 每个叶子不管是否门槛、不管压缩开关，都背整段 gate 规则和
取回说明。pi 的做法是条件拼接片段；本设计按"节在场性"做同样的事。

---

## 3. 命名分节结构：树的 system 由哪些节组成

### 3.1 节点回合的 system 节清单

| 节名 | 内容 | 在场规则 | 来源 |
|---|---|---|---|
| `preamble` | 节点使命（无标签的一段话） | 恒在 | 手写 prose |
| `process` | 步骤（两件事） | 恒在 | 手写 prose |
| `tools` | 一行一个工具片段 + "必须且只能调一个" | 恒在 | 代码生成（从工具清单） |
| `rules` | 操作纪律（推导）+ 协议规则（对应 gate.py） | 恒在 | 推导 + 手写 |
| `input` | user 消息格式说明（7 键 / 意图链 / 观测历史） | 恒在 | 手写 prose |
| `skills` | 已激活 skill 的清单（name + description） | 有激活块时 | 代码生成 |
| `<skill:gate>` | 你是门槛：不成立整个分支作废、兄弟不启动 | `node.gate` | 手写 prose |
| `<skill:compression>` | 工具结果可能被压、带取回标记、调 headroom_retrieve | `cfg.COMPRESS` 且叶子 | 手写 prose |

> 注：`skills` 元节和 `<skill:gate>` / `<skill:compression>` 是两层——元节是"已激活
> 清单"（对齐 pi 的 `<available_skills>` 结构），具体 skill 全文是独立命名节。两者都
> 按节点出生时静态属性定场。

### 3.2 每个节点类型的 system 组成（出生时定死，生命周期内不变）

| 节点类型 | 恒在节 | 条件节 |
|---|---|---|
| alloc | preamble / process / tools / rules / input | `<skill:gate>`（若 `node.gate`） |
| leaf | preamble / process / tools / rules / input | `<skill:gate>`（若 `node.gate`）+ `<skill:compression>`（若 `cfg.COMPRESS`） |
| intake | preamble / process / tools / rules / input | 无 |

### 3.3 节渲染规则

- 每节渲染成 `<节名>\n内容\n</节名>`；`preamble` 无标签、放在最前。
- 节名必须匹配 `[a-z][a-z0-9_-]*`（违反当场报错，§2 不掩盖）。
- 节在 system 里的**渲染顺序固定**（按 3.1 表自上而下），保证 KV 缓存按节命中稳定。

---

## 4. 内容来源与去重规则

1. **工具语义唯一来源 = schema，无例外**（`tool_specs.py` 的 pydantic description，
   provider 原样喂模型）。`tools` 节只生成"一行一个工具片段 + 何时用哪个"的
   **决策指导**，不重复工具描述。`bash`/`read`/`write` 是叶子的**直接工具**
   （`run_code` 是待删除的旧载体，不参与本设计）：三个工具各自注册、各自 schema
   description 承载签名 / 超时 / 语义，与其它工具完全同构。
2. **`rules` 节 = 操作纪律（从工具推导）+ 协议规则（手写）**：
   - 推导部分：有 `bash`/`read`/`write` → 文件与命令操作走它们（pi 的
     `buildRules` 同构）；有 `conclude` → "判定满足必须指得出证据"；有
     `create_children` → "除 notes 外必填、带父的可测物理量、最多一个门槛"……
     **工具清单变 → 纪律跟着变**。
   - 手写部分：协议级不变量（如"每次回复必须且只能调一个"、gate 语义），因
     `gate.py` 变。
   - 工具**内部行为**（bash 超时、read 的 offset/limit）归各工具 schema，
     rules 只放"何时用哪个"的决策纪律，不重复。
3. **skill 触发条件同源**：`node.gate`（Node 字段）和 `cfg.COMPRESS`（config）各只有一个定义。
4. **gate 双语义区分**：`alloc` 的"一次最多一个门槛"是分配节点检查子任务的协议规则，
   **常驻 alloc 的 `rules` 节**；`leaf.md` 的"你是门槛"才抽进 `<skill:gate>` 条件节。

---

## 5. 不变量（改代码前看）

1. **system = 命名分节 `Record<节名, 内容>`**，节名 = XML 标签名，节名通过正则校验。
2. **节组成 = f(节点出生时静态属性)**（kind / gate / cfg.COMPRESS），节点生命周期内
   不变 → system 字节稳定 → KV 缓存按前缀/按节命中。
3. **工具语义唯一来源 = schema，无例外**（`bash`/`read`/`write` 是叶子的直接工具，
   各住各的 schema description）。
4. **rules 的操作纪律部分从工具清单推导**，不手写死；协议规则因 `gate.py` 变。
5. **每节独立可测**：节在场性（哪节在/不在）+ 每节内容独立断言。
6. **双向核对**：文档点名的节 == 真渲染的节（`test_protocol.py` I 段，集合改成节名）。
7. **节渲染顺序固定**（3.3），触发同源（§4.3）。

---

## 6. 实现步骤（怎么实现）

> 每步做完跑 `uv run ruff check` + 全部 `tests/test_*.py`，绿了才进下一步。

### Step 0 · 现状基线（已完成，作为本设计的地基）

- `tree/prompts.py`：3 个 FastMCP prompt（`alloc`/`leaf`/`intake`）+ `render_turn`。
- 消费方：`turn.py ask()`、`intake.py` 走 `render_turn`。

### Step 1 · 把 `.md` 拆成"节"文件

`prompts/` 下按节分文件（`preamble.md` / `process.md` / `tools.md` / `rules.md` /
`input.md` / `skill_gate.md` / `skill_compression.md`），每节内容保持
现有 prose，去掉工具描述重复（W2）。`alloc`/`leaf`/`intake` 的差异通过"同一批节文件
+ 各节点类型的在场规则表"表达，不再一个节点一个大 .md。
`bash`/`read`/`write` **各自注册成直接工具**（`tree/runtime/turn.py` 或
`tree/protocol/tool_specs.py`），签名 / 超时 / 语义住各自的 schema description，
不从 `.md` 出；`run_code` 是待删除的旧载体，不为其保留任何设计空间。

### Step 2 · `tree/prompts.py` 变成"节组装器"

- 新增 `SECTIONS` 表（节名 → 加载/生成函数），对齐 pi 的 `buildSystemPromptSections`：

```python
def build_system_sections(which, node):
    """返回 Record<节名, 内容>（pi 的 SystemPromptSections）。"""
    s = {"preamble": _load("preamble"), "process": _load("process"), ...}
    s["tools"] = _tools_section(which)      # 从工具清单生成
    s["rules"] = _rules_section(which)      # 推导 + 协议规则
    if node.gate:
        s["skill:gate"] = _load("skill_gate")
    if which == "leaf" and cfg.COMPRESS:
        s["skill:compression"] = _load("skill_compression")
    return s

def render_system(sections):
    """Record<节名,内容> → system 文本：每节包 <节名> 标签，preamble 在最前无标签。"""
    ...
```

- `render_turn(name, node)` 返回的 wire 第一条 = `render_system(build_system_sections(...))`；
  FastMCP prompt 注册、参数校验、枚举全部保留（prompt 函数体 = 调这两个函数）。
- `tools` / `rules` 的推导部分用 `tree/protocol/tool_specs.py` 的工具清单作为单一事实。

### Step 3 · 工具语义去重（replace-evolution：删）

- `.md` 各节里不再出现工具描述措辞；schema 是唯一来源。
- `fields.py` 的 `render_wire` 里"手上的东西"短指向保留（提醒叶子能用的工具，
  完整签名在各工具的 schema description）。

### Step 4 · 测试更新（按节断言）

- `test_protocol.py` I 段：双向核对集合从"段落名"改成**节名集合**。
- K 段加节在场性断言：
  - gate=False 且 COMPRESS 关 → system 无 `<skill:gate>` / `<skill:compression>` 节；
  - gate=True → 有 `<skill:gate>` 节；COMPRESS 开 → 叶子有 `<skill:compression>` 节；
  - 同一节点两次组装字节一致；节名违反 `[a-z][a-z0-9_-]*` 当场报错。
- `test_compression.py`：system 断言改成"叶子 system 不含 bash/read/write 签名
  （它们住在各自工具的 schema description）、不含 `<skill:gate>` 节"。

### Step 5 · 验证与收尾

- 全量测试绿（7 个文件）+ `uv run ruff check` 全绿；
- 旧符号清零：grep 确认无整块散文残留、无工具描述双份；
- 同步 `docs/HANDOVER.md` §0。

---

## 7. 不做的事（YAGNI 边界）

- **user 消息 XML 定界**（`node.render()` 输出包 `<task>`）：本轮不做，system 侧先对齐。
- **模型按需读 skill 文件**（Claude Code 的"取 skill"工具）：树的触发条件是宿主已知
  的静态事实，宿主以节为单位注入 = 激活，模型不需要判断——引入取回工具是过度设计。
- **按节 diff / 增量重放**：pi 用它是为会话恢复时省 token；树的 system 在节点生命周期
  内不变，尚无动态节，diff 机制不引入（留接口：节结构天然支持，需要时再加）。
- **prompt 版本管理平台 / agent 框架**：无需求，不引入。
- **skills 再多切**：只有 `gate` / `compression` 两个真条件节，其余全部恒在。
