# humanoid 交接文档

写于 2026-09-17。交接对象：接着做这个项目的人（或下一个会话的我）。

**这份只讲进度与交接**：怎么跑、东西在哪、做到哪一步、还剩什么、踩过哪些坑。
**设计上的本质与不变量在 `docs/PROMPTS.md`**（原 `docs/DESIGN.md` 已删，内容并入其中）—— 这里不重复它们。

> ⚠️ **本文档写于 2026-09-17，正文按当时 `tree/` 布局写的；2026-09-22 起代码已重构。**
> 现在的结构是 `core/`（protocol + runtime + prompts）+ `tools/`（工具）+ `terminal/`（终端）。
> `turn.py` / `hands.py` / `scheduler.py` / `reconcile.py` / `intake.py` / `tool_specs.py` /
> `tree/` 这些名字**都不存在了**：入口（intake）就是会话树的根节点（不是独立循环），
> 工具实现住 `tools/defs.py`（schema 与实现一体），控制流只剩 `core/runtime/loop.py` 一个。
> 下面 §0–§8 的叙述按当时布局写，模块名一律以 §2.1 的**当前代码地图**为准；
> 各包 docstring 与 `docs/PROMPTS.md` 是当前真相。

> **2026-09 删除：keywords 检索层整体移除。** 老树索引（先例）、能力库/盒子
> （现成做法、`search_tools`、出生即注入）全部删掉，`keywords` 字段不再存在；
> 分配节点 / 叶子节点的分工保留（`alloc.md` / `leaf.md` 还在，内容已去掉
> 检索相关段落）。对应模块 `tree/memory/`、`tree/runtime/box.py` 与测试
> `test_caps.py` / `test_index.py` / `test_box.py` 已删除；`session_label`
> （现 `Store.label`）/ `iter_trace_lines`（现 `Store.iter_lines`）迁到
> `tree/runtime/store.py` —— 整个会话存储现在是一个 `Store` 对象（见 §2.1）。

> **后续：`docs/PROMPTS.md` 已实现（系统提示词 = 命名分节结构，pi 范式）。**
> 三套整块散文（`alloc.md` / `leaf.md` / `intake.md`）连同所有 .md 提示词文件全部删掉，
> 节内容**直接写在代码里**（`tree/prompts/` 包：`prose.py` 散文节 / `skills.py` 条件节 /
> `tools.py` + `rules.py` 从 `tool_specs.NODE_TOOLS` 推导，每节一个函数，`lines` + append +
> join，对齐 pi 的 `system-prompt.ts`）。
> **system 不走 @mcp.prompt**：`tree/prompts/__init__.py` 的 `render_turn` 直接返回
> `[system, 基础 user]` 分开两条；**class Node 不碰字符串**，消息拼接全部在
> `tree/prompts/messages.py`（header / lineage / base_user / child_result）。
> **每个节点（分配节点和叶子一样）都是完整 Loop**：统一维护平铺对话
> （基础 user 字节稳定 + 累积的 assistant/tool/user），分配节点的每次分配（create_children
> 的 tool 回话）和下层结论（调度器注入）都在对话里，不再单发 render 整个历史。
> 叶子从 `run_code`（一段代码）改成**直接工具**（`bash` / `read` / `write` / `conclude`），
> 工具语义唯一来源 = schema description；`tree/runtime/sandbox.py`、
> `effects.snapshot_workspace/classify_paths`、`config.SNIPPET_DIR` 随之删除。
> 工具清单的单一事实是 `tool_specs.NODE_TOOLS`。

> **2026-09 存储重构：检查点 = `{node, msgs}`，编排字段全部删除。** Node 删掉
> `attempts` / `observations` / `status` —— 历史只活在一处（每个节点的平铺对话 msgs），
> 状态检查点 = `{"node": node_to_dict(node), "msgs": [...]}`（2026-09-22 起对话**增量落盘**：
> 每节点第一笔全量、之后只带自上次检查点以来新增的消息，`session.load` 按序拼回全量），
> 没有 ready / finished / waiting /
> rest / gate_id 等编排字段。编排由 `tree/runtime/reconcile.py`（actionable 谓词 + settle 结算，
> **调度与恢复共用一份**）从节点事实和对话推导：恢复时用同一个 settle 补投递
> （崩溃窗口：孩子出了结论、没结算进父节点）。`artifacts` / `art_effects` / `contracts`
> 契约机制整体删除（effects / gate / tool_specs / rules 同步清理）。`deferred`（门槛的
> 暂缓规格）是节点上唯一计划性质的数据；gate 靠子节点上的 `gate=True` 找，不存 gate_id。
> intake 仍是独立循环（不是根节点），会话 = 多棵树 + chat_* 对话 —— intake 并入根节点是下一步。

---

## 0. 现在到哪一步了

**跑得动、省得下、下次能捡回来，而且开工前会先把预期谈清楚。**

铁证（同一个量化任务，加索引前 vs 后）：

| | 加索引前（`runs/night_quant`） | 加索引后 |
|---|---|---|
| 时长 | 11.5 小时 | **4.3 分钟**（最近一次 4.0 分钟） |
| 节点 | 2443 | **2**（最近一次 **1**） |
| tokens | 3570 万 | **3 万** |
| 结论 | 没有结论（被 kill） | **阻塞 + 原因**，且**明确引用先例** |

最后那次根节点的结论原文：

> 要达成"账户权益在2026-12-31收盘≥本金×2"必须依赖真实A股账户与未来行情：
> 开户/入金需人到场，不在工具能力内；**先例2已实测账户接口缺本金与币种字段**，
> 无法建立权益基线；2026-12-31尚未到来，时间流逝不可由工具触发。
> 模拟账户或历史回测不能作为该验收标准的证据，故任务阻塞。

**会话可续跑**（最近加的）：`trace.jsonl` 升级成统一会话记录（节点生命周期 +
`state` 检查点 + `chat_*` 对话混排，append-only）。入口默认就是 intake；
`python3 main.py -r` 列表选一个老会话加载成当前会话 —— 对话接着谈、
没跑完的树接着跑（中断时在飞的那一步作废，节点带完整历史重新问模型）。
`--intake` / `--mock` / MockLLM / 直跑模式已删（入口是唯一顶层，且要真模型）。
**老数据只留档案、不留兼容**：空 trace / 无 state 检查点的废会话和顶层老 trace 已删除，
`migrate_sessions.py` 随之删除 —— 运行时只认一种格式，没有任何兼容层；
工作区里还有 29 场「入口并入根之前」的过渡格式会话，当**只读档案**留着
（`load` 能读回任务树接着跑，但没有入口对话）。

测试：**8 个测试文件、200+ 断言，全离线，不调模型**（见 §6）。

---

## 1. 怎么跑

```bash
cd /Users/wxlong/MYCode/humanoid

# 真跑（路径全部来自 .env，入口默认就是 intake；CLI 只剩 -r 一个参数）
# 任务、验收标准、并发……全在终端里谈定 —— 入口问你要什么、怎么算验收
python3 main.py

# 接着上次的会话：列表选一个加载成当前会话，对话接着谈、没跑完的树接着跑
# （选了之后马上重建整棵 Node 树，对话接着谈）
python3 main.py -r

# 跑完当场就把整棵树打出来。想事后从 trace 重建 —— 现在没有这个脚本了（见 §5①）

# 测试
for t in protocol tools intake compression resume cli tty; do python3 tests/test_$t.py; done
```

**`.env` 是唯一的事实来源**（`tree/config.py` 读它）：

```bash
export TREE_BASE_URL='...'                     # 模型
export TREE_API_KEY='...'
export TREE_MODEL='deepseek-v4-flash'
export TREE_WORKSPACE='/Users/wxlong/output/humanoid'   # ← 工作区
export TREE_WORKERS='6'                                # 同时在飞的模型调用数（并发开关，默认 6）
```

三条路径的关系：**跑出来的东西一律落在工作区**。工作区既是 agent 的 cwd
（上次写的代码和数据还在），也是历史 trace 的堆放地。项目目录里只有代码和提示词。

- 不设 `--trace` 时，自动写 `<工作区>/runs/<月日-时分秒>-<任务哈希>/trace.jsonl`
- **工作目录只有 `TREE_WORKSPACE` 一个来源**。没有 `-w`、没有默认值、没有先例可改。
  先例只提供"那里有过什么"（而且只在它等于当前 cwd 时才叫"工作目录"），
  不提供"你该在哪干活"。

---

## 2. 东西都在哪

### 2.1 代码地图

| 文件 | 干什么 |
|---|---|
| `main.py` | **程序入口 + 初始化**：`init()` 检查 API key、确保工作区存在并 chdir 进去，然后 `sys.exit(cli.main())`。唯一初始化点 |
| `cli.py` | **命令行**：`parse_args`（只剩 `-r`）→ `asyncio.run` 派发到 `terminal.chat.run_session` |
| `core/__init__.py` | 包初始化：`import litellm` 前钉死本地模型成本表（`LITELLM_LOCAL_MODEL_COST_MAP`），离线可跑 |
| `core/config.py` | `.env` + 路径规则。**唯一能定义路径的地方**（AGENTS §7）：`WORKSPACE` / `COMPRESS` / `WORKERS` |
| `core/llm.py` | LLM（OpenAI 兼容；`acompletion` 真异步流式 + 思考；`Message` = 文本 + 工具调用 + `usage`）；`ChatPool` = `llm.chat` 的并发上限（消息传递、无锁） |
| `core/events.py` | 事件出口 `EventSink`：同步 fan-out（`subscribe` / `emit`）。机制半边，不认事件词汇 |
| `core/compression.py` | 叶子工具输出的线上压缩（headroom）：发送边界路由压缩 + `headroom_retrieve` 取回 |
| `core/effects.py` | effects 抽取（bash/write 同一套壳；只进 trace 事件，不落节点状态） |
| `core/protocol/fields.py` | **协议层**：`Node` 形式字段（无 attempts/observations/status —— 历史在对话里）+ `node_to_dict` / `node_from_dict` / `task_root` / `is_task_root` + `EXTERNAL_CLASSES` / `VERDICTS` |
| `core/protocol/gate.py` | **协议层**：闸门（必填项 / 锚点 / 证据降级 / 根校验；证据从对话推导观测轮数与子任务名） |
| `core/runtime/plan.py` | 纯规则：`which_of`（节点类型 → 提示词/工具类型）/ `actionable`（该不该调 LLM：没出结论 + 最后一条不是 assistant）/ `make_child` |
| `core/runtime/dialogue.py` | 一个节点的平铺对话账本（assistant / tool / user / feedback 写方法）+ `pair` 线上配对规范化（补占位 tool 回话，不改账本） |
| `core/runtime/store.py` | **一场会话的存储 —— 一个 `Store` 对象**：树 + 记录落盘（内存缓冲 + `pydash.throttle` 节流懒写）；接口 `Store.roots()` / `Store.load(session)` / `Store.new(root, seed)` / `put` / `append_*` / `set_verdict`；检查点 = Node 全字段 + 对话增量。`Store.iter_lines` 读记录 |
| `core/runtime/loop.py` | **唯一的控制流**：扫活跃节点 → 调 LLM / 异步跑工具 → 折回；事件只发 `loop_start` / `loop_end` / `message_update`（带 scope）。`run(store, llm, ...)` 是入口 |
| `core/prompts/` | **命名分节（内容直接写在代码里，没有 .md）**：`prose.py` 散文节（preamble / process / input，每节一个函数）、`skills.py` 两个条件节（gate / compression）、`tools.py` + `rules.py` 从 `NODE_TOOLS` 推导、`messages.py` 节点消息拼接（header / lineage / base_user / child_result / result_marks）、`feedback.py` 模型会读到的反馈文本。`__init__.py` 是节组装器（`build_system_sections` + `render_system` + `render_turn`） |
| `tools/specs.py` | **工具清单单一事实**：`mcp` 实例 + `NODE_TOOLS`（alloc / leaf / intake 各自的工具名）+ `ChildSpec`（形式字段形状）+ `allowed_names` / `openai_tools`（转 litellm 要的 OpenAI 格式） |
| `tools/defs.py` | 工具实现：`@mcp.tool` 函数（`create_children` / `conclude` / `submit_root` / `bash` / `read` / `write`，schema 与实现一体）+ `run_tool` 驱动（ContextVar 注入 `(loop, nid)`） |
| `terminal/chat.py` | **终端会话 + 装配层**：`run_session` 拿参数 → 运行现场（一份存储 `env["store"]`）→ 打横幅，`-r` 时 `Store.load(id)` 读回整棵树；`converse` 是终端话轮（ask / say / 事件路由 / rich Live 树视图） |
| `terminal/view.py` | 树的视图：`render_tree`（每节点一行，运行中 ·、出结论 ✓/✗；compact 实时视图带吐字尾巴） |
| `terminal/picker.py` | `-r` 的会话选择器（prompt_toolkit 自绘列表） |
| `docs/PROMPTS.md` | **设计文档：本质与不变量**（改代码前先看） |
| `docs/HANDOVER.md` | 本文档：怎么跑、资产在哪、剩余工作 |

**并发模型**：整个运行时是 asyncio —— 一场会话只有一个 `Loop`（`core/runtime/loop.py`）：
每轮把活跃节点并发发 LLM（`ChatPool` 限同时在飞的 `llm.chat` 数，最贵的资源），
工具调用也并发发（`tools/defs.run_tool` 在 asyncio task 里跑，ContextVar 注入现场；
bash 走 `asyncio` 子进程），都不占线程。无锁：树的变更一律走 `Store` 的写入方法，
由单线程事件循环串行化（AGENTS §9）。落盘是内存缓冲 + `pydash.throttle` 节流懒写
（成熟库，不自写节流），读记录前 / 进程退出时统一 flush。

### 2.2 真实数据资产（在工作区里）

```
/Users/wxlong/output/humanoid/
├── runs/…                     ← 29 场档案会话（入口并入根之前的数据，只读；`load` 能读回任务树续跑，无对话）
│   ├── night_quant/           ← 最值钱的那棵树：11.5 小时 / 2443 节点 / 35.7M tokens
│   └── verify{2,3,4}/ mock*/ 0918-*/ 0919-*/ realwrite*/ sum/ twofiles/ mkfile/
├── caps.jsonl                 ← 旧能力库（已删检索层，文件留着不动）
└── output/ / data/ / strategies/ / backtest_engine.py / run_backtest.py
                               ← 更早（还没有工作区概念时）跑出来的散件
```

**别删 `runs/night_quant/trace.jsonl`** —— 它是历史会话资产（旧能力库就是从它挖的）。

---

## 3. 已实现的功能点（不再留详细历史）

**全部已实现**，实现见 §2.1 代码地图，设计与不变量见 `docs/PROMPTS.md`，
行为由 §6 测试守住：通道=工具调用、入口同构、终端会话、bash 超时、
7 键同构、意图链、阻塞枝、无长度检查等。详细历史记录已清理 ——
需要细节看代码与测试，不在此留档。

---

## 4. 明确不做的（别再讨论）

- **negative caps / deadend 层** —— 已随检索层整体删除（删它的理由仍有效，
  但落点 `TreeIndex` / `caps.py` 已不存在）。
- **引导 LLM（常驻的第二个 agent）** —— 入口是唯一的顶层循环，它不是
  第二个 agent：手在树上（`run`），它自己只会谈和交形式。

---

## 5. 还没做的（按优先级，落点都写清楚了）

### ① 控制面（人的接口）—— 设计已定，代码一行没有

要做的是：**人直接指着某一层说话**，
五个动作全部翻译成既有形式字段，全部带 `来源: 人工`：

| 人的动作 | 落到哪 |
|---|---|
| 跟某层对话 | 追加一条带来源标记的外部观测 |
| 禁用某分支（模板理由 / 自写理由） | 等价于"门槛不成立"（分支作废、兄弟不启动） |
| 在某层加一个分支 | 走 `children`，过**同一套校验**（人不是后门） |
| "你这样分还不如那样分" | 写一条外部观测进该层对话：`人工否决｜理由`，作废该层子分支重分配 |
| 暂停某分支 | 记 `人工暂停｜理由`（合法，但必须带理由） |

- **落点**：`terminal/control.py`，**不是** `tree/`。控制面换的是"介质与话轮"
  （人怎么插话、怎么看见树），不是树的规矩 —— 它的变因和 `terminal/chat.py`
  完全相同，所以共享同一个包，不另开模块。装配那天在 `main.py` 加子命令即可。
  动作不要直接改内存里的 `Node` —— 写 trace 事件，再由调度器在下一个决策点读进去。
- **不要做"有树在跑就拒绝"这类锁**：正在跑的叶子看不见字段变更，
  正确做法是走**对话（外部观测消息）**通道 —— 人的话变成一条外部观测，下一个决策点就可见。
- **不要先做 LLM 视图**：先做一个筛选（阻塞 > 被拒 > 门槛不过 > 其余折叠），
  人会自然告诉你他想看什么。节点寻址用路径或名字前缀。
- **顺手要补的**：从 trace 重建整棵树的视图（原来在 `report.py` 里，
  已随根目录清理删掉）—— 控制面要用它。
- **测试**：`tests/test_control.py`，五类动作各一条断言，
  尤其"人工加分支要过和模型同一套校验"。

### ② 分配节点的无进展检测

叶子有了（`turn.py` 里的 `bump`）。分配节点"**重复同一套拆法**"还没人抓：
`balk` 只抓"同一份**被拒**的理由"，而一套被接受、但毫无进展的重复拆法它抓不到。

- **落点**：`turn.py` `step` 的子任务分支，对整组 `children` 算一个指纹，走同一个 `bump`。
- **先做粗的**：完全相同的 `name` 集合才算重复。想去抓"换了措辞的同一套拆法"，
  就得引入词法相似度 —— 那是新的噪音源，不急。
- 注意：停下时必须把原因写清楚（和叶子的无进展停下同一个纪律）。

### ③ `prompt/次 恒定` 的长跑验证（欠着的）

- 平铺 agent 的 prompt 是**线性涨**的（实测 2529 → 169760 tokens）。
  树形按设计应该恒定，但**没有长样本证明**。
- **怎么测**：真跑一个 30 分钟以上的任务，从 trace 的 `alloc_in` / `leaf_in`
  payload 里量每次 prompt 的长度，看它随深度/节点数怎么变。
- ⚠️ **唯一可能让它涨的地方**：若将来重新引入按命中注入需重测
  （2026-09 检索层已删，当前没有按命中增长的东西）。

### ④ 入口在真模型上跑一次

- `python3 main.py`（终端里说出任务；CLI 只剩 `-r`）
- 看三件事：会不会真的问用户（而不是自己编一个目标）；
  谈出来的 `accept` 有没有可测物理量；它会不会自己提一条标准（而不是问用户要）；
  看着做不成的事，它会不会老老实实谈成一件可验收的事。

### ⑤ 小项

- 无进展检测的阈值 3 / 5 是**拍的**，没有依据
- `EXTERNAL_CLASSES` 是硬编码的四类（在 `tree/protocol/fields.py`）；
  按设计它只应作"提议"，由人确认
- headroom 压缩的 token 阈值（`min_tokens_to_compress`）和无进展阈值一样是拍的

---

## 6. 测试（全离线）

| 文件 | 断言 | 管什么 |
|---|---|---|
| `tests/test_protocol.py` | 60 | 拆/不拆、门槛、证据降级（含**引自更早一轮的子节点不算编造**）、必填项与 `conc_range` 形状被拒、**`kind` 写错不兜底**、长字段原样通过、无进展停下、分配节点没有 execute、**收到的行首 == 要写的 7 个键**、**文档点名的节 == 真渲染的节（节名集合双向核对）**、**意图链两种节点都有**、**命名分节：节在场性（gate/COMPRESS 条件节）/ 字节稳定 / 节名校验**、**提示词注册成 FastMCP prompt：可枚举 / 缺必填被校验挡住 / wire=[system,user]** |
| `tests/test_tools.py` | 20 | 截断/限制必须可见：read 报区间+可翻页、bash 输出不截断、bash 超时可见/可调/连子进程一起杀 |
| `tests/test_intake.py` | 24 | 入口：话原样送到用户面前（多行也不压）、**只认 `root`：别的 JSON／纯聊天都当话**、形式不合规当场打回并说清原因（含 **`kind` 写错/没写**）、**没有回合数限制**、**合规的根被拿去跑、结论回填**、闸门逐条说不、**吐字只吐话不吐形式** |
| `tests/test_cli.py` | 12 | `main.py` 的参数契约：入口默认就是 intake、要真模型（没 API key 当场报错，不许拿假模型聊）、`-r` 没有老会话当场说清；**守门**：硬编码的默认任务/标准不许回到源码里、`--intake`/`--mock` 老路已删 |
| `tests/test_tty.py` | 53 | 终端会话：问→答→**根被跑掉**、问题只显示一遍、**模型的话一小口一小口吐出来（吐完才轮到读）、形式不吐、思考画成灰的（真终端才上色）**、**裸 `--intake` 先收开场白**、**读驱的是真 `prompt_toolkit` 会话（管道喂进去）**：回车发送（CR / LF 都算）/ 上箭头翻历史 / Alt-Enter 换行 / 括号粘贴多行当一条 / Ctrl-D 收手、旁白到位、**任务树实时画出来（非终端逐帧追加、真终端 rich Live 原地重画）**、**节点级吐字画进树的节点下（思考/说，真终端）**、**跑任务时输入不冻结：敲的字进 Live 帧、跑完按顺序交出去**、**每节点一行铺开：整棵树所有节点正在吐的字都看得见**；**边界守门**：terminal 不碰树的决策层、tree 不 import terminal、main.py 不再自己读输入、terminal 不再自己写 `input()` |
| `tests/test_compression.py` | 19 | 平铺对话（分配节点和叶子同构）：asst/tool 配对、压缩只发生在发送边界（存储原文、线上压短、user 一字未动）、LOG 折叠嵌取回标记且按 hash 可逆、`TREE_COMPRESS=0` 保险阀、压不动的大输出完整到达 |
| `tests/test_resume.py` | 44 | 会话续跑：从 {node, msgs} 检查点重建、崩溃窗口补投递、门槛续跑/作废、in_flight 树接着跑、结论回填、共享谓词重排队列 |
| `tests/test_llm.py` | 12 | `llm._stream` 流式解析：文本/思考/工具参数两段碎片拼回完整 Message、usage 随 Message 走、坏参数 JSON 当场炸、自定义型 tool-call 跳过、多个工具按 index 排序 |

```bash
for t in protocol tools intake compression resume cli tty llm; do python3 tests/test_$t.py; done
```

**待补**：控制面落地后，人的五类动作各要一条断言（见 §5①）。

---

## 7. 踩过的坑（别重犯）

1. **静默截断（本项目最大的一次教训）**
   模型不会自己注意到信息不全，它会**反复重读**。实测：一个叶子把同一个文件读了 25 次，
   因为提示词里每条观测只给它看前 200 字，**而且没告诉它那是截断**。
   它不是傻，是被剥夺了信息。
   → 规矩：**截断要么可见（写明"还有 N 字/还有 M 条"+怎么取回），要么就别截。**
   全仓 `[:N]` 现在只剩三类：可见截断（当面说清还有多少）、哈希摘要、uuid 前缀 ——
   后两类不藏信息（见第 17 条）。

2. **静默切片要盘干净。** `str(obs)[:400]` 会让"只在 400 字之后不一样"的两次观测
   看起来一样，真的进展被当成原地打转。哈希摘要、uuid 前缀不藏信息，可以留。

3. **"取回的路"必须真的通。** `read` 返回里写了"`read(offset=2000)` 取下一段"，
   但 `offset` 从来没传下去 —— 模型照做了也拿不到下一段，只能反复重读。
   当时靠白名单透传来修（`path/content/cmd/timeout/offset/limit`）；
   现在工具按名字接到宿主（`hands.run` + 工具 schema），
   少一个参数就是子进程里当场一个 `TypeError` —— 这一类漏传在结构上不可能再发生。

4. **任何"退回去重来"的路径都必须计数，否则就是死循环。** 实测撞了两次：
   看不懂的输出（同一回合不停）、总缺 `accept` 的子任务（一直分配 → 一直被拒）。
   这两种情况都**没有动作**，所以"重复动作"那个信号永远不触发。
   现在收口在两处（`step` / `balk`），各只有一条出路。
   同类坑：**工具报错曾经是提前 `return`**，于是同一个报错无限重试 ——
   现在工具报错也当成一条普通观测继续走到底。

5. **`edit` 和 `bash` 放同一个调用块会竞态** —— 测试跑在修改之前，出过两次假失败。

6. **`__pycache__` 陈旧字节码** 会 `ImportError`。改动后先 `rm -rf tree/__pycache__`。

7. **测试跑真 `bash` 会污染项目目录** —— 测试必须 `os.chdir` 到临时目录
   （`proof.txt` 就是这么跑到项目根目录的，已修）。

8. **trace 是历史数据，格式必须向前兼容** —— `mine_trace` 认两种
   （`concluded`/`done`、`action`/`leaf_tool`），索引也必须认老格式（中英文键都认），
   否则那棵树就是死数据。

9. **`effects_of` 必须在动作之前跑**，写完之后跑会把 `create` 永远记成 `modify`。

10. **`write` 的契约字段不能直接喂给工具函数**（会 TypeError）。

11. **检索的脏分要无条件重置**（`n.score = best`），否则跨查询残留。

12. **单个数字 token 会命中一切**（"净值为1"、"1.0"…）→ 数字至少两位才算 token。

13. **中文虚词 bigram 会让任何两句话都对上**（"名称**到的**映射表"）→ 要有虚字过滤。

14. **把一次失败当永久否证。** "阻塞的是死路"这句话本身就是坑 ——
    阻塞只说明"当时的条件不成立"。纠正它需要的是把 `证据` / `外部需求` /
    "卡在哪条命令"带进渲染，再加上改掉那半句提示词。

15. **拿"像"当决策依据。** 像不像只是召回。决策依据永远是"证据还指不指得动"：
    像但证据过期 → 重做；不像但那件产物还在 → 照样能用。

16. **把负知识另存一份。** 全语料里结论级阻塞 0 条 —— 就算建了库，初期也是空的；
    而一旦它有了剪枝权，错误就再也不会被推翻（不调用 → 无 counter-evidence → 永不退休）。

17. **别用"复活"这个词。** 树没有挂起状态；"接着跑"实际只能是"新建一个节点，
    把老节点的对话/历史搬过来当起点"。老树能复用的是**证据**，不是进度。

18. **提示词和代码检查是一对，改一边就要看另一边。** 提示词在 `tree/prompts/`（节内容
    直接写在代码里，改提示词要碰 `prose.py` / `rules.py`），硬性要求在 `tree/protocol/gate.py`
    （必填项 / 锚点 / 门槛 / 证据降级）和 `tree/protocol/fields.py`
    （`EXTERNAL_CLASSES`）。`tree/prompts/__init__.py` 的文件头列了对照表。

19. **文档要分离。** 设计文档（`docs/PROMPTS.md`）只写设计与不变量（不讲进度），
    `docs/HANDOVER.md`（本文）只写进度与交接（不讲设计）。混在一起两边都读不下去。

20. **先例的"工作目录"是个陷阱（实测，一次真实跑）。** 渲染里写
    `工作目录: <老树目录>`，模型会把它抄进子任务的详情当"当前工作目录"，
    于是 `hello.py` 被写进了一棵早就不该再写的老树里，而进程 cwd 其实在别处 ——
    "产出只落工作区"这条不变量当场破了。
    → 规矩：**先例的目录只有在等于当前 cwd 时才叫"工作目录"**；
    否则只能说"先例的数据在那边（只读）"。工作目录只有 `TREE_WORKSPACE`
    一个来源（`main.py` 里没有任何别的入口），提示词里不需要让模型选。

21. **证据复核不能只看最后一轮。** 老的 `_evidence_ok` 只取最后一轮分配尝试的
    `results`，而最后一轮常常是**被拒的一次分配**（那条尝试里根本没有结果），
    于是上面一轮真跑过的子任务名被判成"编出来的"，一次本该满足的结论被降级成未满足。
    → 现在证据从整份对话推导（下层结论消息全量累积在对话里），天然覆盖所有轮次，
    这类窗口在结构上不存在了。

22. **同一个问题在终端上显示两遍。** `intake` 原来把"问什么 / 建议什么"同时交给
    `on_say`（旁白）和 `ask`（问用户），于是终端里出现"问：X / 我建议：Y / X /
    （我的建议：Y）/ › "。加一句注释提醒"这两条别重复显示"是守不住的 ——
    这是边界错位（两条通道传了同一份东西），不是记性问题。
    正确动作是移边界：**问题与建议只走 `ask`，旁白（打回理由、重复计数）只走 `on_say`**。

23. **终端交互不能塞进 `main.py` 或 `tree/`。** 一个是装配层（参数/`.env`/cwd），
    一个是树的规矩 —— 它们的变因都不是"人怎么在 tty 上说话"。
    塞进去的后果：改一句提示语要动 `main.py`，`tree/` 里多出一堆 `input()/print()`
    （`tree/runtime/intake.py` 因此变得只能跑在真终端上，测试不了）。
    → 落点 `terminal/`，变因清单见 `terminal/__init__.py`；
    依赖方向单向（`main.py` → `terminal` → `tree.intake`），由 `tests/test_tty.py` G 段守门。

24. **别把"实现省事"包装成纪律。** 终端输入曾经有一条"硬纪律"：**回车只换行、
    空行才发送**。当时记下的理由是中文输入法里回车用来确认候选词 —— 但这条规矩
    的真实代价全落在用户身上：**敲完的行改不了、没有历史、粘贴多行会被当成好几句**。
    它看着像纪律，其实是为了省掉"自己写多行输入"这件事。
    → 现在读直接交给 `prompt_toolkit`（`PromptSession`）：回车发送，方向键 / 历史 /
    括号粘贴都是现成的，"分几行写"交给 Alt-Enter 这个独立按键；只绑 Alt-Enter、
    **不绑 `c-j`**（拿 `c-j` 顶换行会在某些路径下把回车也吃成换行：实测
    `prompt_async` 一去不回，buffer 里多出一个 `\n`）；
    `input()` 那套 isatty 补换行、空行收尾、`at_start` 收行的代码一并删掉。
    教训：**凡是把成本转嫁给用户的"规矩"，先问一句"这是不是为了我实现省事"**；
    成熟库已经解决的事，自己写一遍只会更差（AGENTS §13）。

25. **默认值就是伪造用户的话。** `-c` 原来默认为"期末账户权益 >= 本金 x 2"，
    出口和任务默认值不是一对时，就可能把一条用户从没提过的验收标准当成
    "用户给的验收标准"送进入口。实测：一句"帮我自动做视频赚钱"被谈成了
    "历史回测还是模拟盘/实盘？初始资金 100 万..." —— 入口没错，它只是在
    圆一个假事实，而且**看起来很像真的**（这类污染最难发现）。
    → 规矩：**命令行没有默认任务、没有默认验收标准**；想要的默认值就显式
    写出来，不想写就让入口去问用户。种子只写用户真说过的：没给的就是没给。
    同类：提示词里的举例也是这种污染（`keywords` 举 `["akshare","回测","2026-12-31"]`
    会把所有任务往量化上带），举例要让形状清楚、不携带领域。

---

## 8. 一句话交接

**能跑、能省、能被下次捡回来；开工前会先把预期谈清楚。**
入口把用户的一句话谈成一个能验收的根任务；"死路"不建库 ——
阻塞结论本来就在树上，而且会把"卡在哪条命令"一起带回来。工作目录不用再手给了。

接着做的人：**先做 §5①（控制面），再做 §5②，然后 §5③ 那个长跑验证。**
