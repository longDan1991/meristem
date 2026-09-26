# 代码纪律（硬约束，优先于默认习惯）

这是本仓库写/改代码的**禁令清单**。它不是建议，是硬约束：**规则优先于你的默认写法，优先于"让报错消失"的冲动，优先于"先跑起来再说"。**

## 0. 执行协议（每次动手前后各过一遍）

1. **动手前后**：动手前读一遍本清单，明确这次改动可能触发哪几条；收尾前逐条对照自查。
2. **发现问题立即停**：一旦在做下面任何一条禁止的事，停下从根因修，不要"先这样、回头再说"。
3. **附带义务**：修改一个文件时，该文件里若已存在以下任何违规，**一并修正**，不要只动目标那一行。
4. **验收**：`uv run ruff check` 全绿才算改完（能机器判定的禁令见 §12）。

---

## 1. import 一律放模块顶层（禁绝延迟导入）

禁止任何非顶层 import：函数内 `import`、`try: import X`、条件 import。**没有例外。**

- ✗ `def f(): from a import b` / `try: import x except ImportError: ...`
- ✓ 顶层 `from a import b`

循环导入是**模块边界问题**，去修边界；不许用"函数内 import"绕过。**测试代码也不例外。**

## 2. 不许掩盖错误（报错必须暴露并修根因）

**报错消失 ≠ 错误消失。**禁止：

- 吞异常：`except: pass`、`except Exception: pass`、捕获后只 log 不 re-raise；
- 用返回 `None` / 默认值 / 假数据把失败糊过去，让错误数据继续流转；
- 用 `# noqa` / `# type: ignore` / `# pragma: no cover` 当创可贴压 lint 报错，而不是修代码；
- 改断言、加 skip、删用例让测试"假绿"。

根因修不了时，让错误**带着完整上下文在最早的点炸出来**（fail fast），不要降级兜底。

## 3. 不做过度设计

- 只有一个实现，就别造接口 / 基类 / 工厂 / 策略模式；
- 不为假想需求加参数 / 配置 / 开关（YAGNI：需求来了再加）；
- 不重新发明标准库 / 已有依赖已有的能力；
- 性能不算过度设计的挡箭牌——热路径的正确复杂度要求见 §11。

## 4. 不留代码残渣

- 删除未使用的 import / 变量 / 函数 / 参数；
- 不保留注释掉的旧代码块；
- 注释只解释 **why**，不解释 what；
- 不留 `print` / `TODO` / `FIXME` 调试残留。

## 5. 测试要真

- 不只测 happy path，必须覆盖错误路径与边界；
- 测试不依赖执行顺序 / 全局状态 / 具体文件路径；
- mock 只隔断外部副作用（网络、时钟、IO），不 mock 被测对象本身。

## 6. 正确性基础

- 不用可变默认参数（`def f(x=[])`）；
- 文件 / 连接用 context manager，不手动 open 不关；
- 副作用不藏在"读 / 查询"函数里；
- 不忽略返回值 / 错误码（如 `df.drop(...)` 没重新赋值、`list.sort()` 当 `sorted()` 用）；
- 不用 try/except 做控制流（`try: d[k] except KeyError` → `if k in d`）。

## 7. 禁止自行推导路径

**数据根 / 工作区根**的路径**只允许**来自项目已有的路径配置模块（各包的 `_paths.py` / `config.py` 里定义的 `DATA_ROOT`、`OUT_ROOT` 等常量），且在该模块里必须是**显式配置的绝对路径**（可留一个环境变量覆盖口）——路径是机器相关、部署相关的配置，探测会把"代码在哪"和"数据在哪"耦合起来，换机器 / 换部署位置时行为漂移。业务代码禁止：

- `Path(__file__).resolve().parent.parent / "data"` 之类的向上推算；
- `Path.cwd()` / `os.getcwd()` / 相对路径 / `~` 展开 / 向上探测；
- 把路径字符串直接写进业务函数。

**例外（仅此一类）**：**随代码发布、与代码同生共死的包内只读资产**（如 `strategy/registry` 自带的注册表目录）不算外部配置，允许用 `Path(__file__).resolve().parent` 定位并收敛成模块级唯一常量，业务代码仍从那里 import。

缺常量 → 先在 `_paths.py` 里按这个规矩加，再从业务代码 import。

## 8. 禁止循环查询数据库（禁绝 N+1）

数据库往返是网络副作用，**禁止在循环里逐条查**——能一次取完就一次取完。

- ✗ `for uid in uids: db.query(...)` / `for row in rows: session.get(...)`
- ✗ 循环里 `await` 单条查询、循环里调 ORM 关系懒加载
- ✓ `WHERE id IN (...)` 批量取，或在内存里用一次查询的结果 join / 建索引

大集合超出单次参数上限时，用流 / 游标（见 §10）。

## 9. 禁止使用锁（用队列和事件机制代替）

`Lock` / `RLock` / 信号量 / 条件变量 / 手动加解锁（`threading.Lock()` / `asyncio.Lock()` / `multiprocessing.Lock()` / `with lock:`），**一律禁止**——加锁是把"谁先谁后"交给运气，死锁和竞态都从这里长出来。也禁止自己写"状态 + 锁"保护的共享变量。

- ✓ 把共享可变状态改成**消息传递**：`queue.Queue` / `asyncio.Queue` / `Janus` 之类的队列，单一消费者串行化
- ✓ 等待某条件用 `threading.Event` / `asyncio.Event`（`Condition` 本质仍是锁，同样禁止）

判据：改动如果一个线程/协程只通过队列收发、不直接读写别人也在写的变量，就不需要锁。

## 10. 文件与数据库读写禁止分批（用流代替）

读写大文件 / 大结果集，**禁止"切成 N 份循环处理"**——每批都是一次新的打开 / 定位 / 往返，越分越慢，中途失败还会留下半成品。

- ✗ `for i in range(0, len(rows), 1000): write(rows[i:i+1000])` / 循环 `execute` 拼 INSERT
- ✗ 循环里 `read(chunk_size)` 手工拼接、逐段 `seek` 读写
- ✓ 文件：一次开的文件对象当**流**用——`shutil.copyfileobj` / `csv.reader` / `io` 管道 / 生成器逐行走到底
- ✓ 数据库：一次交互一条 SQL，用**游标 / server-side cursor** 流式取；写用 `executemany` 或单条大语句

没有流式接口（外部 API 硬性限制）是分批的唯一正当理由；这时用固定批大小一次算清、无中间状态，并注释写明 why。

## 11. 性能：热路径禁止重复计算与线性查找

性能是**设计输入，不是事后调优**：数据规模与调用次数动手前就要想清楚，算法 / 数据结构复杂度在写的时候就定死，"先跑通再说"、"数据量还小" 都不是理由。

判据两问：**这段在热路径上吗**（每条数据 / 每次请求都走）？**它的开销随数据量怎么涨**？答不出来就是设计没做完。

- ✗ 循环里做本该只做一次的事：`re.compile`、读同一份文件 / 配置、`json.loads` 同一份 payload、建同一个连接 → 提到循环外，或模块级固化；
- ✗ 用 list 线性扫描做成员判断 / 去重 / 配对：`if x in big_list`、`for a in A: for b in B` → 用 `set` / `dict` 建索引，把 O(n²) 降到 O(n)；
- ✗ 循环里字符串 / bytes `+=` 拼接 → `list.append` + `"".join`；
- ✗ pandas 逐行 `iterrows` / 无脑 `apply` → 向量化 / `groupby` / `merge`；
- ✗ 同一份数据重复解析 / 序列化 → 算一次，把结果往下传；
- ✗ `async` 里出现阻塞调用（`time.sleep`、同步 HTTP / DB、大段 CPU 计算）→ 用异步版本，或丢进线程池 / 进程池；
- ✗ 用全局 dict / list 当无界缓存 → 换有界缓存（`functools.lru_cache(maxsize=...)` 等）。

热点的认定以 profile（`timeit` / `cProfile`）为准；但不许拿 "还没测" 当借口保留一眼可见的 O(n²)、重复计算、阻塞事件循环。

## 12. 纪律由 lint 执行（不靠自觉）

`uv run ruff check` 是能机器判定的禁令的可执行版本，配置在根 `pyproject.toml [tool.ruff.lint]`：

| 规则 | 对应禁令 |
|---|---|
| `E402` / `PLC0415` | §1（模块级 / 函数内 import 不在顶部） |
| `BLE001` | §2（宽 `except` 吞异常） |
| `F401` / `F841` | §4（未使用的 import / 局部变量） |

**台账机制**：存量违规在行尾以 `# noqa: <规则>` 记账，汇总在 `docs/plan/AGENTS_DEBT_PLAN.md`；`noqa` 只压**已登记的旧账**，新代码再犯直接报错，新增 `noqa` 必须同步登记（否则就是 §2 禁止的"创可贴"）。

未纳入 lint、仍靠人判的：§3/§5/§6/§7/§8/§9/§10/§11/§13/§14，以及 §4 的 `print`（不启用 `T20`：CLI 输出与调试残留无法机器区分）。

## 13. 禁止重复造轮子（成熟能力必须用现成库）

一件**小而独立、边界清晰**的事，只要已经存在广泛使用、成熟稳定的第三方库（或标准库）在做，**禁止自己手写一份**。
判据：功能能用一个函数 / 一个文件装下、输入输出定义明确 → 八成有成熟库，先查再写。

## 14. commit 一律英文 + Conventional 前缀

提交信息是仓库历史里唯一写给**外部读者**的散文。**一律英文**（文档 / issue 可中文，提交不可）——中文提交把可读人群从全部读者缩到会说中文的那部分。**存量中文提交不追改**：改写历史会换掉全部 SHA，不值当；从下一个提交起执行即可。

形式：`<type>(<scope>): <subject>`

- `type` ∈ `feat` / `fix` / `docs` / `test` / `refactor` / `chore` / `build` / `ci` / `perf`；`scope` 可选，指模块（`prompts` / `protocol` / `loop` / `store` / `terminal` / `tools`）
- `subject`：祈使句现在时、全小写、≤ 72 字符、结尾不加句号
- `body`：写 **why**，不写 what（diff 自己会说）；与 `subject` 之间空一行
- 一个提交一件事；**重命名 / 移动 / 纯格式化**必须与逻辑改动分开提交，否则 review 时 diff 不可读
- 禁用 `wip` / `temp` / `update` / `fix bug` / 单字提交

```
feat(prompts): derive the rules section from the tool registry
fix(loop): keep the ledger append-only when a node is resumed
docs(terminal): pin the five-region layout as an invariant
```
