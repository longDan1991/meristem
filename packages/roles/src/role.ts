/**
 * 角色的两个面。
 *
 * 这个包只面对两方，**只导出这两方要用的东西**：
 *   · **LLM 面**：`Role`（system 字符串 + 能伸的手 + 执行）—— 喂给模型的和收回来的只有这些；
 *   · **人面**：`start` / `list` / `get` —— 人指一个目录、看清单、挑角色。
 * 装载、模板填空、技能扫描、MCP 连接、生命周期都在包内部，不导出：它们不是面，是实现。
 *
 * 作业（`Job`）不住这里：它是执行机制那一块，住 `jobs/`（DESIGN §9）。
 *
 * 变因：两个面的形状（对 LLM 承诺什么、对人承诺什么）。
 */
import type { Job } from "./jobs/job.ts";

export type RoleId = string;

/** LLM 面：一份角色对模型意味着什么。 */
export interface Role {
  readonly id: RoleId;

  /** 人面：给人看的那一行（挑角色时只看它）。 */
  readonly title: string;

  /**
   * 这条线的 system：角色那份 xml 填空后的字符串。
   *
   * 每次调用现算（运行时才发现的手 —— 比如 MCP 服务上的工具 —— 也在里面），
   * 所以同一个角色在两次调用之间可能不一样：改了手，system 就变（缓存随之失效），这是对的。
   */
  system(): string;

  /** 这次伸得出哪些手：内置手与 MCP 手在这里没有区别。 */
  hands(): readonly Hand[];

  /**
   * 按名字找一只手：找到给手，**找不到给一句话**。
   *
   * 模型点了没有的手是**正常的事**（它可以点错），所以这不是缺陷 —— 但那条 `tool_calls` 也得有条回音，
   * 不能装作没发生。**"没有这把"的话住这一层**：谁有哪些手、说这句话怎么说，都是能力的事；
   * harness 一个字的文本都不写（DESIGN §9.2）。
   */
  findHand(name: string): HandLookup;
}

/** 找手的结果：要么这只手，要么**回给模型的那一句话**（说清它手上有哪些）。 */
export type HandLookup =
  | { readonly kind: "hand"; readonly hand: Hand }
  | { readonly kind: "missing"; readonly answer: string };

/** 一只手：名字 + 一段描述 + schema + 一次执行（语义只有一份，没有第二处说明）。 */
export interface Hand {
  readonly name: string;
  /** 语义的唯一来源：provider 原样喂给模型（tools 数组里那一份）。 */
  readonly description: string;
  readonly schema: JsonSchema;
  /**
   * 一行短句（进 system 的 `tools` 节，给模型"我有哪些手"的索引；完整语义仍在 `description`）。
   * 没有它就不进 system（MCP 手就是这样：服务只给名字 / 描述 / schema）。
   */
  readonly snippet?: string;
  /** 这只手贡献的纪律条目（汇总进 system 的 `rules` 节，重复的会被去掉）。 */
  readonly guidelines?: readonly string[];
  /**
   * 跑一次：**把这次执行起起来，立刻返回 `Job`** —— 不许在这里 await 到结束（那等于把执行塞回
   * "一次调用一个结果"的同步世界，作业就没意义了）。
   *
   * 作业由**底座**登记进作业表（`jobs/base.ts`）：手不用自己往表里放东西。
   *
   * 时间纪律（DESIGN §9.9，三层逐层退）：
   *   · 能收时间参数的手**必须在 schema 里收**（模型自己写的命令，它比谁都清楚这条要多久；
   *     预期久的命令就该写更大的值，或 `0` = 明说无限期）；
   *   · 调用方不写时用哪个缺省值，**必须写在 `description` 里**（模型得知道自己跟什么规则打交道）；
   *   · 压根没有时间参数来源的手（MCP 服务给的 schema 我们改不了）由**底座兜底**，且要说出来。
   *   起执行时底座**要求给一个超时值** —— 让"忘了"这个状态不存在。
   *   超时的结局是一段交代（"跑了 120s 还没结束，把它杀了；要跑更久就写 timeout=…"），这条线继续。
   */
  run(args: unknown, ctx: HandContext): Promise<Job>;
}

/**
 * 运行时能提供、手能用到的两样东西（**只有事实，没有回调、没有表**）。
 *
 * 作业表不在这里：它是 Job 机制自己维护的**模块级内存结构**（`jobs/table.ts`），住那一块，
 * 手要按空间筛它就调那一块的查询函数 —— 上下文只负责告诉手"你在哪个空间里"。
 */
export interface HandContext {
  /** 这条线自己的输出根：相对路径的读写都落在这里。 */
  readonly outputRoot: string;

  /**
   * 这次执行所在的**空间**：由树在调用这只手的时候给（当前实现就是节点 id；
   * roles 只把它当键用，不解释它的含义）—— 底座把它写进 `Job.space`，
   * `job_list` 靠它筛出"这条线上起的作业"（从父线继承下来的那些消息里提到过的作业不属于它）。
   */
  readonly space: string;
}

/** provider 原样吃的 JSON Schema。 */
export type JsonSchema = Readonly<Record<string, unknown>>;
