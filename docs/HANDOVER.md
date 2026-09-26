# meristem 交接文档

写于 2026-09-17，持续更新。交接对象：接着做这个项目的人（或下一个会话的我）。

**这份只讲进度与交接**：怎么跑、东西在哪、做到哪一步、还剩什么、踩过哪些坑。
**设计上的本质与不变量在 `docs/PROMPTS.md`**（原 `docs/DESIGN.md` 已删，内容并入其中）—— 这里不重复它们。

> **代码地图以 §2.1 为准**：`core/`（protocol + runtime + prompts）+ `tools/`（工具）+ `terminal/`（终端）。
> `tree/` / `turn.py` / `hands.py` / `scheduler.py` / `reconcile.py` / `intake.py` /
> `tool_specs.py` / `mine_trace.py` 这些名字都不存在了，正文里若还出现就是历史叙述。
> 已被删掉的旧机制：keywords 检索层（先例 / 能力库 / 出生即注入）、节点上的编排字段
> （`attempts` / `observations` / `status`）、契约机制（`artifacts` / `contracts` / `effects`）。

> **2026-09-24 清理：一份语义只留一处实现。** 这轮把"同一件事有两份说法"收干净了：
> - **工具作用域用 fastmcp 自己的可见性功能**：工具在声明处带 `scope:<层>` 标签
>   （`@mcp.tool(tags={scope_tag(LEAF)})`），清单由库算出来（把定义表挂成只读视图 +
>   `enable(tags=…, only=True)` + `list_tools()`，`tools/specs.py`），`scope_names` 是唯一出口 ——
>   提示词 tools 节、发送边界的校验、发给 provider 的 `tools=` 全从它派生。
>   `NODE_TOOLS` / `ACTION_TOOLS` / 自写的 `@scoped` 投影都已删。
> - **词表与措辞各一份**：可测物理量（`ANCHOR_RE` + `ANCHOR_HINT`）、7 个形式字段
>   （`FORM_FIELDS`）、外部需求 / 判定 / 动作工具的提示文本 —— 住 `core/protocol/fields.py`
>   与 `core/protocol/feedback.py`；协议层不再 import 工具层（动作集由调用方传）。
> - **修掉的行为洞**：根节点给 gate 现在被 `validate_root` 当场拒（根没有兄弟）；
>   会话摘要取**最新**谈成的任务（原来取第一个）；`iter_lines` 改成先解析再按 kind 过滤
>   （原来拿原始行做子串匹配，跟 json 分隔符写法隐式耦合）。
> - **trace 不再重复记** `alloc_in` / `*_out`（那是检查点 msgs 里已有的同一批消息）；
>   量"prompt 随深度涨不涨"看 `usage` 记录的 `prompt`。
> - **死重**：`store.state` 直接存 `Dialogue`、去死参数 / 死初始化 / 死变量、
>   `chat.py` 与 `view.py` 的重复分支合一、`deliver` 挪回 `core/llm.py`、删掉只有测试用的
>   `Store.label`（摘要测试改走 `Store.roots`）。
> - **文档**：`docs/PROMPTS.md` 的节名 / 并行调用 / 实现落点对齐代码，并由 `test_protocol`
>   真读它核对；§7 里讲已删子系统的条目清掉。

---

## 0. 现在到哪一步了

**跑得动、省得下、下次能捡回来，而且开工前会先把预期谈清楚。终端是能看的一条应用（五区一屏）。**

**2026-09-26 统一 Textual 组件：rich / prompt_toolkit 删净**（设计同步到 `docs/TERMINAL.md`）：
上一轮虽然把屏交给了 Textual，行 / 框 / 列表仍在"自己画"或借 rich —— 日志区是 `RichLog`
吃 rich renderable、工具输出是 rich `Panel`、树条带自己拼带样式的 `Text`、`-r` 的选择器是
prompt_toolkit 自绘。这一轮把它们全换成组件，并把 rich / prompt_toolkit 从依赖表与代码里删净：

- **组件化**：日志区 = `VerticalScroll` + 一条消息一个组件（`Markdown` / `Static`，工具输出
  `Collapsible`）；树条带 = `OptionList`（高亮 / 滚动 / 滚轮都是它的）；`-r` 选择器 =
  `OptionList`；状态条 = `Static`。样式一律走 CSS 类（`view.ROW_CSS`），不手写 rich。
- **开场白进应用**：新会话"要做什么"由应用自己收（第一条回车就是种子；`store=None` 进场）
  —— 不再"进应用前先跑一个 prompt_toolkit 提示框"，也就少了一个渲染器与第二套输入。
- **非真终端按行读**：管道 / 重定向那条路不进应用（那里没有屏可占），输入按行读 `stdin`，
  EOF / Ctrl-C 当收手。
- **删净**：`rich` / `prompt-toolkit` 不在 `pyproject.toml`，源码里也没有它们的 import
  （`test_tty` F 段守着）；textual 自己依赖 rich 是它的内务，与本项目的依赖无关。
- 顺带：`view.py` 的返回值从 rich renderable 变成组件（`render_tail` 一段一个 `Static`）；
  `_SessionApp` 的 store 参数可为 `None`。

**2026-09-26 换 Textual：整块屏交给应用**（设计在 `docs/TERMINAL.md`）：
前一轮是"正常缓冲日志 + 底部 prompt_toolkit 提示区 + 切节点 `\x1b[2J` 清屏重印"，它栽在
**两个渲染器抢同一块屏**上（坑①），于是这一轮把整块屏交给 Textual：

- **屏归应用**：Textual 进备用屏，五区一屏 —— 日志区（`RichLog`，应用内滚动）+ 实时尾巴
  + 树条带 + 状态条 + 输入行（`TextArea`）。切频道重绘 = `RichLog.clear()` 再写回去：
  **不写裸 ANSI**、不猜"我上帧画了几行"，差分重绘与擦除是 Textual 渲染器的事。
- **提交才落地**：日志区只画选中节点**已提交**的消息（`store.dialogue`）；还没进 store 的
  那一小段活在**尾巴区**。落地时机 = `tool_start` / 入口提问（`ask`）/ `loop_end` —— 都是
  "消息已经进了 store"的那几个点；切回来看是同一份内容（重画读 store）。
- **一个频道一个流**：↑↓ 切选中节点，日志区清掉重画它；别的节点的事件不写进来（免得串台），
  树条带（`·` 标记）与状态条（`n 运行中`）看得见它在跑，切过去连它的实时尾巴一起看。
- **代价说清楚**：终端 scrollback 不再承载会话历史（退出应用后终端恢复原样），历史在日志区
  里滚（滚轮 / PgUp / PgDn 归 Textual，鼠标被应用接管；复制靠 Textual 自己的选择）。
- 顺带补上 `loop.py` 的 `tool_start.arguments`：文档 §4 早就写着"工具行带参数"，代码没发，
  终端画出来一直是 `工具: 名()`。
- 测试：`test_tty` 全段改到**无头驱动 + Pilot**（A/B/D/E/H/J/K/L/Q），新增
  `test_terminal_pty`（真 pty：备用屏 / 鼠标接管 / 真方向键切频道 / 打字回车 / Ctrl-C 收手）。
- **踩过的坑**（都留了测试）：① **屏只能有一个 owner** —— rich 手写 `\x1b[2J` 与
  prompt_toolkit 渲染器互相不知道对方画了什么；而且 `\x1b[2J` 擦掉的是"当前屏"而不是推进
  scrollback，屏上还没滚出去的对话（含用户刚敲的）直接没了，重印的快照又堆进 scrollback；
  ② multiline 输入的回车默认是插换行不是提交（要显式绑 Enter=提交、Alt-Enter=换行，
  prompt_toolkit 与 TextArea 都一样）；③ prompt_toolkit 全局 `AppSession` 缓存第一个
  `create_output()`（当时只对开场白/非真终端那条路有意义；后来 prompt_toolkit 删净，
  这两条路都不再走它 —— 见上面"统一 Textual 组件"那条）；
  ④ 合成键一整段写（`hello\r` 一次写）会和 Textual 的键分发抢跑，提交到半截字 ——
  真键盘一个键一次读不会遇到，`test_terminal_pty` 照真键盘分开写；⑤ 焦点是挂载后
  下一个消息泵才生效的，早于它敲进去的键会丢（真用户敲不了那么快，测试等 `PTY_READY` 标记）。

铁证（同一个量化任务，加索引前 vs 后）：

| | 加索引前（`runs/night_quant`） | 加索引后 |
|---|---|---|
| 时长 | 11.5 小时 | **4.3 分钟**（最近一次 4.0 分钟） |
| 节点 | 2443 | **2**（最近一次 **1**） |
| tokens | 3570 万 | **3 万** |
| 结论 | 没有结论（被 kill） | **阻塞 + 原因**，且说清卡在哪一条 |

最后那次根节点的结论原文：

> 要达成"账户权益在2026-12-31收盘≥本金×2"必须依赖真实A股账户与未来行情：
> 开户/入金需人到场，不在工具能力内；**先例2已实测账户接口缺本金与币种字段**，
> 无法建立权益基线；2026-12-31尚未到来，时间流逝不可由工具触发。
> 模拟账户或历史回测不能作为该验收标准的证据，故任务阻塞。

**会话可续跑**：`trace.jsonl` 是一份统一会话记录（节点生命周期事件 +
`state` 检查点 + `tool` / `usage` 等运行事件混排，append-only）。入口默认就是 intake；
`python3 cli.py -r` 列表选一个老会话加载成当前会话 —— 对话接着谈、
没跑完的树接着跑（中断时在飞的那一步作废，节点带完整历史重新问模型）。
`--intake` / `--mock` / MockLLM / 直跑模式已删（入口是唯一顶层，且要真模型）。
**老数据只留档案、不留兼容**：空 trace / 无 state 检查点的废会话和顶层老 trace 已删除，
`migrate_sessions.py` 随之删除 —— 运行时只认一种格式，没有任何兼容层；
工作区里还有 29 场「入口并入根之前」的过渡格式会话，当**只读档案**留着
（`load` 能读回任务树接着跑，但没有入口对话）。

测试：**8 个测试文件、317 条断言，全离线，不调模型**（见 §6）。

---

## 1. 怎么跑

```bash
cd /Users/wxlong/MYCode/meristem

# 真跑（路径全部来自 .env，入口默认就是 intake；CLI 只剩 -r 一个参数）
# 任务、验收标准、并发……全在终端里谈定 —— 入口问你要什么、怎么算验收
python3 cli.py

# 接着上次的会话：列表选一个加载成当前会话，对话接着谈、没跑完的树接着跑
# （选了之后马上重建整棵 Node 树，对话接着谈）
python3 cli.py -r

# 跑完当场就把整棵树打出来。想事后从 trace 重建 —— 现在没有这个脚本了（见 §5①）

# 测试
for t in protocol tools intake resume cli tty; do python3 tests/test_$t.py; done
```

### 1.5 通用 skill 机制（2026-09-25）

对齐 oh-my-pi 的 skills 范式：`SKILLS_DIRS` 下 `*/SKILL.md` 非递归扫描（同名 first-wins），
`<skills>` prompt 节只放 name + description 检索面（一行一个），正文模型按需经
`read_skill` 工具读 `skill://<名字>/<路径>`（先 `_manifest` 看清单，再读 SKILL.md / 子文件）。
机制对具体 skill 一无所知——加 skill 就是在任意 SKILLS_DIRS 根下放一个目录，零代码。

**agent-reach 只是当前注册的一个 skill**（16 平台联网路由；MIT）：
它的目录落在默认扫描根 `~/.agents/skills` 下（`agent-reach skill --install` 的标准落点），
路由表 / 失败重试链住它的 SKILL.md + references/，随它的版本换代自动生效（重扫即新）。

**一次性安装（换机器重做）：**

```bash
# 1. agent-reach CLI 本体（uv 工具链；pipx 同模型，但本机没装 pipx、装它要动 brew）
uv tool install https://github.com/Panniantong/agent-reach/archive/main.zip

# 2. 它的 SKILL 落标准位置（通用扫描根 ~/.agents/skills 下的一个 skill）
agent-reach skill --install

# 3. 只读体检 → 看哪些渠道通
agent-reach install --env=auto

# 4. 系统级依赖 + 可选渠道（需要用户点名 + 授权；channels: twitter,xiaohongshu,reddit,
#    facebook,instagram,bilibili,linkedin,boss,xiaoyuzhou,xueqiu,all）
agent-reach install --env=auto --system --channels=<点名>
```

**配置**：扫描根 = `core/config.py` 的 `SKILLS_DIRS`（逗号分隔，默认 `~/.agents/skills`，
env `SKILLS_DIRS` 覆盖，§7 路径纪律）。新增 skill 目录到任意根即可。

**踩过的坑**：
- 上游 CLI 必须进**启动 cli.py 的进程 PATH**（bash 工具继承它的环境）：`uv tool install`
  装的 agent-reach 在 `~/.local/bin`，但 yt-dlp 等装在它的 venv 里不在 PATH ——
  所以 `agent-reach install --system` 那一步要用系统级安装（或手动补 PATH）。
- 转录 / 下载类命令超 bash 默认 120s：显式 `timeout`；Whisper 转录用 `agent-reach transcribe`。
- agent-reach 的 SKILL 明文要求中间产物放 `/tmp`，别在工作区留文件（与"write 是产出"
  不冲突：调研观测走 /tmp，最终报告才写工作区）。

**`.env` 是唯一的事实来源**（`core/config.py` 读它）：

```bash
export TREE_BASE_URL='...'                     # 模型
export TREE_API_KEY='...'
export TREE_MODEL='deepseek-v4-flash'
export TREE_WORKSPACE='/Users/wxlong/output/humanoid'   # ← 工作区
export TREE_WORKERS='6'                                # 同时在飞的模型调用数（并发开关，默认 6）
```

三条路径的关系：**跑出来的东西一律落在工作区**。工作区既是 agent 的 cwd
（上次写的代码和数据还在），也是历史 trace 的堆放地。项目目录里只有代码和提示词。

- 记录路径自动生成：`<工作区>/runs/<月日-时分秒>-<随机>/trace.jsonl`（没有 `--trace` 参数）
- **工作目录只有 `TREE_WORKSPACE` 一个来源**。没有 `-w`、没有默认值。

---

## 2. 东西都在哪

### 2.1 代码地图

| 文件 | 干什么 |
|---|---|
| `cli.py` | **命令行入口（唯一可执行入口）**：`parse_args`（只剩 `-r`）→ `main.init()` → `main.main(args)`；除 `main` 外不 import 任何项目模块 |
| `main.py` | **初始化 + 入口函数**：`init()` 检查 API key、确保工作区存在并 chdir 进去；`main(args)` 把参数派发给 `terminal.chat.run_session`。唯一初始化点 |
| `core/__init__.py` | 包初始化：`import litellm` 前钉死本地模型成本表（`LITELLM_LOCAL_MODEL_COST_MAP`），离线可跑 |
| `core/config.py` | `.env` + 路径规则。**唯一能定义路径的地方**（AGENTS §7）：`WORKSPACE` / `WORKERS` |
| `core/llm.py` | LLM（OpenAI 兼容；`acompletion` 真异步流式 + 思考；`Message` = 文本 + 思考（`reasoning`，留底进历史）+ 工具调用 + `usage`）；`ChatPool` = `llm.chat` 的并发上限（消息传递、无锁） |
| `core/events.py` | 事件出口 `EventSink`：同步 fan-out（`subscribe` / `emit`）。机制半边，不认事件词汇 |
| `core/protocol/fields.py` | **协议层**：`Node` 形式字段（无 attempts/observations/status —— 历史在对话里）+ `node_to_dict` / `node_from_dict` / `task_root` / `is_task_root` + 词表（`VERDICTS` / `EXTERNAL_CLASSES` / `FORM_FIELDS` / `ANCHOR_RE` + `ANCHOR_HINT`） |
| `core/protocol/gate.py` | **协议层**：闸门（必填项 / 锚点 / 证据降级 / 根校验；证据从对话推导观测轮数与子任务名） |
| `core/runtime/plan.py` | 纯规则：`which_of`（节点类型 → 提示词/工具类型）/ `actionable`（该不该调 LLM：没出结论 + 最后一条不是 assistant）/ `make_child` |
| `core/runtime/dialogue.py` | 一个节点的平铺对话账本（assistant / tool / user / feedback 写方法，assistant 带 `reasoning`）+ `pair` 线上配对规范化（补占位 tool 回话，不改账本） |
| `core/runtime/store.py` | **一场会话的存储 —— 一个 `Store` 对象**：树 + 记录落盘（内存缓冲 + `pydash.throttle` 节流懒写）；接口 `Store.roots()` / `Store.load(session)` / `Store.new(root, seed)` / `put` / `append_*` / `set_verdict`；检查点 = Node 全字段 + 对话增量。`Store.iter_lines` 读记录 |
| `core/runtime/loop.py` | **唯一的控制流**：扫活跃节点 → 调 LLM / 异步跑工具 → 折回；事件只发 `loop_start` / `loop_end` / `message_update` / `tool_start` / `tool_end` / `usage`（都带 scope）。`run(store, llm, ...)` 是入口 |
| `core/prompts/` | **命名分节（内容直接写在代码里，没有 .md）**：`prose.py` 散文节（preamble / process / input，每节一个函数）、`skills.py` 条件节（gate）、`tools.py` + `rules.py` 从 `tools.scope_names` 派生、`messages.py` 节点消息拼接（header / lineage / base_user / child_result / result_marks）、`feedback.py` 模型会读到的反馈文本与词表提示。`__init__.py` 是节组装器（`build_system_sections` + `render_system` + `render_turn`） |
| `tools/specs.py` | **工具注册表 + schema 适配**：`mcp` 实例（工具的 tags 声明作用域）+ `load` / `scope_names` / `action_names`（作用域视图，走 fastmcp 的可见性过滤：挂只读视图 + `enable(only=True)` + `list_tools`，供提示词与校验用）+ `ChildSpec`（形式字段形状）+ `openai_tools`（转 litellm 要的 OpenAI 格式） |
| `tools/defs.py` | 工具实现（bash 之外）：`@mcp.tool` 函数（`create_children` / `conclude` / `submit_root` / `read` / `write`，作用域 = tags，schema 与实现一体）+ `run_tool` 驱动（ContextVar 注入 `(loop, nid)`）+ 结算（`_push_results` / `_resolve_gate`）。`from tools import bash` 即把 bash 工具注册进 mcp |
| `tools/bash.py` | **bash 工具独立成文件**：schema 与给模型的描述照抄 oh-my-pi 的 BashTool（`command` / `timeout` / `cwd`，`timeout=0` 禁用 deadline，`cwd` 代替 `cd`）；执行走 llmbash 进程内 shell（不压缩输出）—— 持久 shell 池按 cwd 复用 + 并发重叠降级 one-shot 真并行 + 坏会话弃用重建 |
| `tools/skills.py` | **通用 skill 加载**：import 时扫描 `cfg.SKILLS_DIRS` 下 `*/SKILL.md` 挂成 fastmcp `SkillsDirectoryProvider` + `read_skill` 工具（leaf 动作，读 `skill://<名字>/...` 资源）+ `discovered()`（name+description 清单，喂 `<skills>` 节）—— 对齐 oh-my-pi，机制对具体 skill 一无所知 |
| `tools/context.py` | 工具共享现场：`(loop, nid)` ContextVar 注入（`get_binding` / `_current`）+ `_action_result` 记 tool 观测进 trace |
| `terminal/chat.py` | **终端会话 + 装配层**：`run_session` 拿参数 → `-r` 时 `Store.roots()` 列出老会话、选中后 `Store.load(picked)` 读回整棵树，攒横幅（工作目录 / 并发 / 限制 / 已加载的会话）；`converse` 是终端话轮，按 stdout 是不是真终端分流。真终端 = `_SessionApp`（**Textual**，布局见 `docs/TERMINAL.md`）：五区一屏 —— 日志区（`VerticalScroll`，一条消息一个组件：`Markdown` / `Static` / 工具 `Collapsible`）+ 实时尾巴（没进 store 的那一小段，一段一个 `Static`）+ 树条带（`OptionList`）+ 状态条（`Static`）+ 输入行（`TextArea`）；↑↓ 切频道 = 清日志区重挂（widget 操作，不写裸 ANSI）；Enter 提交 / Alt-Enter 换行 / Ctrl-P·Ctrl-N 翻历史 / Ctrl-T 收展树 / Ctrl-F 折叠 / Ctrl-Q / Ctrl-C 收手（不看输入行里有什么；Ctrl-D 不占，归输入行删字符）/ 状态条常显收手键；事件路由（loop_start / loop_end / message_update / tool_* / usage）+ 一条输入队列（谈与跑共用）。`store=None` = 还没谈定：应用先进场收种子；非真终端降级为逐帧打印 + 按行读 stdin |
| `terminal/view.py` | 树的视图（**只产 Textual 组件**，样式在 `ROW_CSS`）：`render_folded`（地图：跑完的子树折一行带统计、活跃路径展开，返回 `[(node_id, 行)]`）+ `render_stream`（选中节点**已提交**的消息流：assistant = `Markdown`、工具输出 = `Collapsible` 框、判定绿/红）+ `render_tail`（**还没提交**的实时尾巴：思考灰斜体 / 说话纯文本） |
| `terminal/picker.py` | `-r` 的会话选择器（Textual `OptionList`：↑↓ 挪高亮、回车选中即加载） |
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
行为由 §6 测试守住：通道=工具调用、入口同构、终端会话、bash 超时（引擎 = llmbash，
输出不压缩、逐字到达）、7 键同构、意图链、阻塞枝、无长度检查等。详细历史记录已清理 ——
需要细节看代码与测试，不在此留档。

**2026-09 bash 引擎换 llmbash**（`tools/bash.py`）：命令跑在 llmbash 进程内 shell 上
（常见命令不 fork/exec）。会话管理照 oh-my-pi 的 `bash-executor`：持久 shell 按 key
（工作区）复用 —— export / 函数跨调用保留，每次 `run` 显式传 `cwd=工作区根` 保住
「相对路径一律相对工作区根」的约定；**同一时间一个 key 只跑一条，并发重叠的 bash 调用
降级为一次性 one-shot shell，真并行不排队**；坏会话（run 抛错）弃用重建。超时走 CancelToken，
`timed_out=True` 返回而非异常，进程树连同后台 job 一起杀，
**`timeout=0` = 不限时**（对齐 oh-my-pi 的"0 禁用 deadline"）。依赖 PyPI 上的
`llmbash>=0.1.0`（分发名 `llmbash`，import 仍是 `llm_sh`）——曾用 `[tool.uv].find-links`
指向 `llm-sh/target/wheels` 装本地 wheel，2026-09 发布后已删。

**2026-09-24 压缩整体去掉**：wire 级压缩（`compress_messages` / `headroom_retrieve` 取回工具 /
`skill_compression` 节 / `cfg.COMPRESS`）全删，llmbash 的 `minimize` 关闭 —— read / bash / write
的输出一字不动，不再有任何压缩与取回；`headroom-ai` 依赖一并移除（锁文件同步）。完整实现
在 git 历史里，要恢复压缩从那里捡。

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

- **落点**：`terminal/control.py`，**不是** `core/`。控制面换的是"介质与话轮"
  （人怎么插话、怎么看见树），不是树的规矩 —— 它的变因和 `terminal/chat.py`
  完全相同，所以共享同一个包，不另开模块。装配那天在 `cli.py` 加子命令即可。
  动作不要直接改内存里的 `Node` —— 写 trace 事件，再由调度器在下一个决策点读进去。
- **"指着某一层说话"的选点已经在了**：树条带（焦点常在输入行，↑↓ 选节点，
  选中即切流、也决定输入打给谁）就是控制面的瞄准具 —— 五个动作都挂在"当前选中节点"上，
  输入行打给选中的节点（入口根 = 对话，其它节点 = 外部观测）。
- **不要做"有树在跑就拒绝"这类锁**：正在跑的叶子看不见字段变更，
  正确做法是走**对话（外部观测消息）**通道 —— 人的话变成一条外部观测，下一个决策点就可见。
- **不要先做 LLM 视图**：先做一个筛选（阻塞 > 被拒 > 门槛不过 > 其余折叠），
  人会自然告诉你他想看什么。节点寻址用路径或名字前缀。
- **顺手要补的**：从 trace 重建整棵树的视图（原来在 `report.py` 里，
  已随根目录清理删掉）—— 控制面要用它。
- **测试**：`tests/test_control.py`，五类动作各一条断言，
  尤其"人工加分支要过和模型同一套校验"。

### ② 无进展检测（叶子和分配节点都没有）

现在没有任何计数器：历史只活在对话里，`actionable` 只看"最后一条是不是 assistant"。
所以"**重复同一件事**"没人抓 —— 分配节点尤其明显：一套被接受、但毫无进展的拆法
会一直被重复拆下去（叶子反复重读同一个文件同理）。

- **落点**：叶子的动作在 `tools/context._action_result`（它已经在记 tool 观测）；
  分配节点的拆法在 `tools/defs.py` 的 `create_children`（它已经写 `allocated` 记录）。
  两处对"这一轮的动作集合"算一个指纹，重复就写清原因回对话（或直接回绝这一次）。
- **先做粗的**：完全相同的 `name` 集合 / 完全相同的命令才算重复。想去抓"换了措辞的
  同一套拆法"，就得引入词法相似度 —— 那是新的噪音源，不急。
- 注意：停下时必须把原因写清楚（和「阻塞」同一条纪律）。
- 实测过的两种形态：看不懂的输出会让同一回合不停重试；总缺 `accept` 的子任务会被一直
  分配又被一直拒 —— 这两种都**没有"动作"**，所以只抓"重复动作"是不够的，
  要抓的是"这一轮的动作集合与上一轮相同"。

### ③ `prompt/次 恒定` 的长跑验证（欠着的）

- 平铺 agent 的 prompt 是**线性涨**的（实测 2529 → 169760 tokens）。
  树形按设计应该恒定，但**没有长样本证明**。
- **怎么测**：真跑一个 30 分钟以上的任务，从 trace 的 `usage` 记录里读每次调用的
  `prompt` —— 那就是这一次的 prompt 长度（不用去翻消息拼回全量），看它随深度 / 节点数怎么变。
- ⚠️ **唯一可能让它涨的地方**：若将来重新引入按命中注入需重测
  （检索层已删，当前没有按命中增长的东西）。

### ④ 入口在真模型上跑一次

- `python3 cli.py`（终端里说出任务；CLI 只剩 `-r`）
- 看三件事：会不会真的问用户（而不是自己编一个目标）；
  谈出来的 `accept` 有没有可测物理量；它会不会自己提一条标准（而不是问用户要）；
  看着做不成的事，它会不会老老实实谈成一件可验收的事。

### ⑤ 小项

- `EXTERNAL_CLASSES` 是硬编码的四类（在 `core/protocol/fields.py`）；
  按设计它只应作"提议"，由人确认 —— 人确认这条路还没实现（控制面，见 §5①），
  当前按词表过滤后即算事实。
- 将来做 §5② 无进展检测时，阈值也必然是拍的 —— 要给依据（实测数据），别再拍一个数。

---

## 6. 测试（全离线）

| 文件 | 断言 | 管什么 |
|---|---|---|
| `tests/test_protocol.py` | 63 | 拆/不拆、门槛、证据降级（含**引自更早一轮的子节点不算编造**）、必填项与 `conc_range` 形状被拒、**`kind` 写错不兜底**、长字段原样通过、分配节点没有 execute、**收到的行首 == 协议的形式字段（`FORM_FIELDS`）== 工具 schema 的键**、**设计文档点名的节 == 真渲染的节（测试真读 `docs/PROMPTS.md`）**、**意图链两种节点都有**、**节在场性 / 字节稳定 / 节名校验**、**wire=[system]**、**工具作用域：声明只在 tags 一处 / 清单 == 库的可见性过滤结果 / 指导齐全 / 动作工具集** |
| `tests/test_tools.py` | 30 | 截断/限制必须可见：read 报区间+可翻页、bash 输出不截断、bash 超时可见/可调/连子进程一起杀、**bash 输出不压缩逐字到达 + rm 真删文件**、**timeout=0 不限时**、**并发 bash 降级 one-shot 真并行** |
| `tests/test_intake.py` | 25 | 入口：话原样送到用户面前（多行也不压）、**只认 `root`：别的 JSON／纯聊天都当话**、形式不合规当场打回并说清原因（含 **`kind` 写错/没写**、**给根标 gate**）、**没有回合数限制**、**合规的根被拿去跑、结论回填**、闸门逐条说不、**吐字只吐话不吐形式** |
| `tests/test_cli.py` | 15 | `cli.py` 的参数契约：入口默认就是 intake、要真模型（没 API key 当场报错，不许拿假模型聊）、`-r` 没有老会话当场说清；**守门**：硬编码的默认任务/标准不许回到源码里、`--intake`/`--mock` 老路已删 |
| `tests/test_tty.py` | 124 | 终端会话（**无头驱动 + Pilot 驱真应用**）：问→答→**根被跑掉**、问题只显示一遍、**模型的话一小口一小口上屏（屏上有半截话时整段还没到）、形式只走工具那一行**、**思考流式进尾巴区、落地成灰斜体历史行、样式真上了屏**、**长尾巴滚到最新那几行（不卡在头 8 行）**、**新会话"要做什么"在应用里收（第一条回车就是种子，收下才起树）**、**非真终端按行读 stdin（空行也是一条、EOF / Ctrl-C 收手）**、旁白到位、**↑↓ 切频道：日志区清成选中节点的对话（选中底色落在选中那一行）**、**折叠渲染：跑完的子树折一行带统计、活跃路径展开、选中路径强制展开、显式展开压过自动折叠**、**流渲染：加粗 user 行 / `Markdown` 组件 / 工具行 / 工具输出 `Collapsible` 框 / 判定行；尾巴是另一块（render_tail：思考灰斜体、说话纯文本）**、**Markdown 真被解析（`**` 没原样上屏）**、**跑任务时输入不冻结：敲的行排队、按顺序以「你:」交出去**、**并行：三个孩子同时挂在树上（· 不折叠）**、**事件词汇：tool_start（带参数）/tool_end（耗时）/usage（字段/先后序）**、**Q 段：喂真键位与事件——Ctrl-T 收/展、Ctrl-F 只折已出结论的节点、Ctrl-P·Ctrl-N 翻历史（光标落末尾）、回车提交（空行不入队）、Alt-Enter 换行（输入行长高）、尾巴落地（tool_start 把思考+说话写进日志区）、别的频道的事件与尾巴都不串台、loop_end 重画判定（✗→✓）、**Ctrl-Q / Ctrl-C 有字也收手 / Ctrl-D 不再收手（退给输入行删字符）/ 状态条常显收手键****、**run 炸了带着原异常退场（app.error，不吞）**、**converse 按 stdout 分流**、**非真终端逐帧打印折叠树**、**S 段：`-r` 的会话选择器（列表在 / ↑↓ 挪高亮 / 回车挑中那一行 / Ctrl-C 取消）**；**边界守门**：terminal 不碰树的决策层、**视图层只产 Textual 组件**、**rich / prompt_toolkit 在依赖表与源码里都没有**、**不再手写裸 ANSI 清屏 / 不再 patch_stdout**、core 不 import terminal、main.py 不再自己读输入、terminal 不再自己写 `input()` |
| `tests/test_terminal_pty.py` | 15 | 真终端介质（**真 pty + 真驱动**）：进备用屏 / 退出时离开备用屏、接管鼠标（滚轮归日志区）、第一帧画完（种子/话/思考/树条带/状态条/输入行都在）、**真方向键切频道（↓ 换成子节点对话、↑ 切回）**、输入行拿住焦点（`PTY_READY` 标记）、**敲字回车提交后进日志区**、Ctrl-C 干净收手（退出码 0）。慢（≈10s）且要 pty，所以只放无头驱动看不到的那一层 |
| `tests/test_resume.py` | 32 | 会话续跑：从 {node, msgs} 检查点重建、崩溃窗口补投递、门槛续跑/作废、in_flight 树接着跑、结论回填、末行截断容错、增量检查点拼回全量、**会话摘要认最新谈成的任务**、**记录读路径认解析后的 kind（嵌入同形键的非 state 记录不算、紧凑分隔符的 state 照样认）**、**同一秒里连开两场会话不撞进同一条记录** |
| `tests/test_llm.py` | 13 | `llm._stream` 流式解析：文本/思考/工具参数两段碎片拼回完整 Message、usage 随 Message 走、坏参数 JSON 当场炸、自定义型 tool-call 跳过、多个工具按 index 排序 |

```bash
for t in protocol tools intake resume cli tty terminal_pty llm; do python3 tests/test_$t.py; done
```

**待补**：控制面落地后，人的五类动作各要一条断言（见 §5①）。

---

## 7. 踩过的坑（别重犯）

1. **静默截断（本项目最大的一次教训）**
   模型不会自己注意到信息不全，它会**反复重读**。实测：一个叶子把同一个文件读了 25 次，
   因为提示词里每条观测只给它看前 200 字，**而且没告诉它那是截断**。
   它不是傻，是被剥夺了信息。
   → 规矩：**截断要么可见（写明"还有 N 字/还有 M 条"+怎么取回），要么就别截。**
   全仓切片现在只剩两类：可见截断（`read` 报区间 + 翻页提示）、标识符前缀
   （`uuid[:8]` / `hex[:6]`）—— 后者不藏信息。

2. **"取回的路"必须真的通。** `read` 返回里写了"`read(offset=2000)` 取下一段"，
   而 `offset` 参数必须真的能传下去（现在 offset / limit 就是工具参数，写进 schema）。
   凡是观测里承诺了"怎么拿回完整的东西"，那条路就得是通的 —— 否则模型只能反复重读。

3. **写文件和跑命令放同一个调用块会竞态** —— 测试跑在写入之前，出过两次假失败。

4. **`__pycache__` 陈旧字节码** 会 `ImportError`。改动后清一遍：
   `find . -name __pycache__ -prune -exec rm -rf {} +`（别只清某个包）。

5. **测试跑真 `bash` 会污染项目目录** —— 测试必须 `os.chdir` 到临时目录
   （`proof.txt` 就是这么跑到项目根目录的，已修）。

6. **trace 只有一种格式解释。** 旧档案的节点上带着已删的编排字段
   （`attempts` / `observations` / `status` / `keywords`…），`node_from_dict` 不采信、
   直接丢 —— 这是**唯一**的容忍；除此之外坏数据（没有 state 检查点、根不唯一、
   中间坏行）一律当场炸，不做半成品树。

7. **单个数字会命中一切**（"净值为1"、"1.0"…）→ 锚点里的数字至少两位
   （`core/protocol/fields.ANCHOR_RE`）。

8. **把一次失败当永久否证。** "阻塞的是死路"这句话本身就是坑 ——
   阻塞只说明"当时的条件不成立"。纠正它需要的是把 `证据` / `外部需求` /
   "卡在哪条命令"带进渲染（rules 节的阻塞段就是这么写的）。

9. **别用"复活"这个词。** 树没有挂起状态；"接着跑"实际只能是"新建一个节点，
   把老节点的对话/历史搬过来当起点"。老树能复用的是**证据**，不是进度。

10. **提示词和代码检查是一对，改一边就要看另一边。** 提示词在 `core/prompts/`
    （节内容直接写在代码里，改提示词要碰 `prose.py` / `rules.py` / `feedback.py`），
    硬性要求在 `core/protocol/gate.py`（必填项 / 锚点继承 / 门槛 / 证据降级 / 根校验）
    与 `core/protocol/fields.py`（词表、`ANCHOR_RE` / `ANCHOR_HINT`、`FORM_FIELDS`）。
    `gate.py` 文件头列了对照关系。

11. **文档要分离。** 设计文档（`docs/PROMPTS.md`）只写设计与不变量（不讲进度），
    `docs/HANDOVER.md`（本文）只写进度与交接（不讲设计）。混在一起两边都读不下去。
    设计文档里出现的节名由 `tests/test_protocol.py` 真读它核对 —— 文档漂了测试会红。

12. **工作目录不许多来源（实测，一次真实跑）。** 渲染里写过
    `工作目录: <某个老树目录>`，模型会把它抄进子任务的详情当"当前工作目录"，
    于是 `hello.py` 被写进了一棵早就该只读的树里，而进程 cwd 其实在别处 ——
    "产出只落工作区"这条不变量当场破了。
    → 规矩：**工作目录只有 `TREE_WORKSPACE` 一个来源**（`main.py` 的 `init` 是唯一初始化点），
    提示词里不让模型选目录；记录下来的老会话只提供"那里有过什么"（只读）。

13. **证据复核不能只看最后一轮。** 老的 `_evidence_ok` 只取最后一轮分配尝试的
    `results`，而最后一轮常常是**被拒的一次分配**（那条尝试里根本没有结果），
    于是上面一轮真跑过的子任务名被判成"编出来的"，一次本该满足的结论被降级成未满足。
    → 现在证据从整份对话推导（`result_marks` 扫全量下层结论消息），天然覆盖所有轮次。

14. **同一份东西别走两条通道。** `intake` 原来把"问什么 / 建议什么"同时交给
    `on_say`（旁白）和 `ask`（问用户），终端里就出现"问：X / 我建议：Y / X /（我的建议：Y）/ › "。
    加注释提醒"这两条别重复显示"是守不住的 —— 这是边界错位，不是记性问题。
    正确动作是移边界：**问题与建议只走 `ask`，旁白（打回理由、接到任务）只走 `on_say`**。

15. **终端交互不能塞进入口（`cli.py` / `main.py`）或核心层。** 一个是参数 / `.env` / cwd 的装配，
    一个是树的规矩 —— 它们的变因都不是"人怎么在 tty 上说话"。
    塞进去的后果：改一句提示语要动入口文件，核心层里多出一堆 `input()/print()`
    （老 `intake.py` 因此变得只能跑在真终端上，测试不了）。
    → 落点 `terminal/`，变因清单见 `terminal/__init__.py`；
    依赖方向单向（`cli.py` → `main.py` → `terminal` → `core`），由 `tests/test_tty.py` F 段守门。

16. **别把"实现省事"包装成纪律。** 终端输入曾经有一条"硬纪律"：**回车只换行、
    空行才发送**。当时记下的理由是中文输入法里回车用来确认候选词 —— 但这条规矩
    的真实代价全落在用户身上：**敲完的行改不了、没有历史、粘贴多行会被当成好几句**。
    它看着像纪律，其实是为了省掉"自己写多行输入"这件事。
    → 现在读交给成熟部件：交互会话里是 Textual 的 `TextArea`（回车提交、Alt-Enter 换行、
    历史 Ctrl-P/Ctrl-N、多行粘贴都是部件能力），开场白（新会话"要做什么"）也在同一块屏的
    同一条输入行上收；非真终端（管道 / 重定向）没有屏可占，就按行读 `stdin` ——
    一个介质一套输入，不再有第二个渲染器 / 第二套键位。同一课：回车 / 换行的绑定要显式写对 ——
    多行输入部件的回车默认是插换行，**提交键要自己绑**（拿 `c-j` 顶换行会把回车也吃成换行）；
    `input()` 那套 isatty 补换行、空行收尾、`at_start` 收行的代码一并删掉。
    教训：**凡是把成本转嫁给用户的"规矩"，先问一句"这是不是为了我实现省事"**；
    成熟库已经解决的事，自己写一遍只会更差（AGENTS §13）。

17. **默认值就是伪造用户的话。** `-c` 原来默认为"期末账户权益 >= 本金 x 2"，
    出口和任务默认值不是一对时，就可能把一条用户从没提过的验收标准当成
    "用户给的验收标准"送进入口。实测：一句"帮我自动做视频赚钱"被谈成了
    "历史回测还是模拟盘/实盘？初始资金 100 万..." —— 入口没错，它只是在
    圆一个假事实，而且**看起来很像真的**（这类污染最难发现）。
    → 规矩：**命令行没有默认任务、没有默认验收标准**；想要的默认值就显式
    写出来，不想写就让入口去问用户。种子只写用户真说过的：没给的就是没给。
    同类：提示词里的举例也是这种污染（举例要只给形状、不携带领域）。

18. **空回车/纯空白不算回答。** 入口提问后用户直接回车（或敲了一串空格），
    `ask` 返回 `""` 被原样 `append_user` 进对话 —— `actionable` 只看"最后一条
    不是 assistant"，空 user 消息照样触发再一轮 LLM。模型面对一条空 user 轮
    只能写元叙述：实测屏幕变成
    `…我就去跑调研。› The user hasn't responded yet. Wait, looking at the conversation…`
    （`› ` 是终端提示符不是模型吐的；空回车后提示符留在原地，新一轮吐字紧跟其后，
    看着就像"loop 自己不停说"）。而且每次空回车 = 一次带全历史的 LLM 调用，
    连续空回车能把它变成空转。
    → 修在 `_ask` 边界（运行时语义）：空/纯空白**不入账、不惊动模型**，循环等
    同一句；终端 `ask` 再补一句"回车发的是空行——Ctrl-D 结束，或重新输入"。
    判据：**用户没说 = 对话没推进**，这不是提示词能兜住的，是对话语义。

---

## 8. 一句话交接

**能跑、能省、能被下次捡回来；开工前会先把预期谈清楚。**
入口把用户的一句话谈成一个能验收的根任务；"死路"不建库 ——
阻塞结论本来就在树上，而且会把"卡在哪条命令"一起带回来。工作目录不用再手给了。

接着做的人：**先做 §5①（控制面），再做 §5②，然后 §5③ 那个长跑验证。**
