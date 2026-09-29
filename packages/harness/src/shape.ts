/**
 * 一条线里流动的东西：**消息与 wire 的形状 —— harness 的词汇**。
 *
 * atree 只知道"内容是某个不透明的类型 `M`"，所以这些类型住这里：
 * 这里是"一次调用发出去什么、收回来什么"的形状（换 provider、加消息种类的变因都在这一个文件里）。
 *
 * **配对不是程序的事**（DESIGN §9.6）：程序不记"哪条回话配哪次调用"。
 * 作业 id 会**拼在消息内容里**（起手一条、结束一条），模型靠那个 id 自己把前后对上。
 * provider 那套临时 id（`tool_calls[].id` / `tool_call_id`）由传输层**出网时现造**、
 * 回来时折回我们的形状 —— **临时 id 不进账，记账 id 不出网**。
 *
 * 变因：消息形状与 schema 类型（换 provider、加消息种类）。
 */

/** 平铺对话里的角色。 */
export type ChatRole = "system" | "user" | "assistant" | "tool";

/** provider 原样吃的 JSON Schema。 */
export type JsonSchema = Readonly<Record<string, unknown>>;

/** 一次调用：写了哪只手、参数是什么。**它不带 id** —— 谁是谁靠内容里的作业 id 认。 */
export interface ToolCall {
  readonly name: string;
  readonly arguments: unknown;
}

export interface WireMessage {
  /**
   * 这条消息的**稳定 id**（我们给的，写账时定死、随消息进账）。
   *
   * 它的用处是把"账里的引用"钉住：人指得出"就是这一条"，追溯与复现都吃得准
   * （DESIGN §5.2：引用是引用，不是复述）。它**不是** provider 的 id，也不发给 provider。
   */
  readonly id: string;
  readonly role: ChatRole;
  readonly content: string;
  /** assistant 的思考原文（`reasoning_content`）：随消息进历史。 */
  readonly reasoning?: string;
  readonly toolCalls?: readonly ToolCall[];
  /**
   * 这条回复**是在哪个角色下产生的**（缺省 = 节点的角色）。
   *
   * 一条线通常只有一个角色，所以它通常为空。唯一的例外是**总结分叉**：新线开局先穿总结角色
   * 说一条（`by` = 总结角色），再换成人选的角色。记下来才分得清"哪句话是谁的角色说的" ——
   * 不记，追溯时只能按节点角色猜，而猜就是漂移（DESIGN §5.1 / §5.2）。
   *
   * **记账字段，不发给 provider**。作业的结果消息用它标"是哪只手回来的"。
   */
  readonly by?: string;
}

/** 一次调用发出去的东西：一段 system + 平铺对话。 */
export interface Wire {
  readonly system: string;
  readonly messages: readonly WireMessage[];
}

/** 一次调用的用量。 */
export interface Usage {
  readonly prompt: number;
  readonly completion: number;
  readonly reasoning: number;
  readonly cached: number;
  readonly total: number;
}
