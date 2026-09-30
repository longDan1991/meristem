/**
 * 传输：给一条 wire，拿回一条回复（可能带手的调用）。
 *
 * 只吃 `@oh-my-pi/pi-ai` 的**传输面**（provider 适配 / 流式 / 重试 / usage）。
 * 它的 agent 层（`pi-agent-core` / `pi-coding-agent`）与 `pi-tui` 都不引入：
 * 那套会话模型与本设计的树冲突，而 `pi-tui` 把整条 agent 栈写进了自己的 dependencies。
 *
 * **两个 id 的分工**（DESIGN §9.6）：账里的参照物是**我们的**（`WireMessage.id`，写账时定死）；
 * provider 要的 `tool_calls[].id` / `tool_call_id` 是**临时物**，由这一层**出网时现造**（同一段历史
 * 每次请求各造一套，互不认识也无所谓 —— 程序不靠它配对）。一句话：**临时 id 不进账，记账 id 不出网**。
 *
 * **配对不是程序的事**：作业 id 拼在消息内容里（起手一条、结束一条），模型自己认。
 * 所以这一层不需要"把回话配到调用上"的逻辑 —— 每条 `tool_calls` 都已经有一条回话在它后面。
 *
 * 自己的需要自己声明（不认任何配置对象）：**模型引用**、可选的**端点覆盖**、**钥匙**。
 * 引用在这里解析成"模型"这个事实（走 pi-ai 的模型目录：元数据有上下文多大、支不支持思考、
 * 支不支持工具调用）；解析不出来 / 这家 provider 伸不了工具，当场炸。
 * 元数据先只服务传输（思考通道开不开、请求怎么发）；哪天调度要用（比如"这条线装不下了"），
 * 也是从这里把事实递出去，别处不许再解释一遍引用。
 *
 * **钥匙是装配层取的**（从哪个环境变量 / 文件来不归这里管），取完立刻交到这一个函数里。
 * 报错时只说 `credential.from`，**永不说 `key`** —— 401 要说得清是哪把钥匙被拒了。
 *
 * 变因：provider 与流式细节（换端点、换模型、换 SDK）。
 */
import type { JsonSchema, Usage, Wire, WireMessage } from "./shape.ts";

export interface StreamHandlers {
  /** 正文增量（终端画在这个节点那一行上）。 */
  onText?(delta: string): void;
  /** 思考增量。 */
  onReasoning?(delta: string): void;
  /**
   * 这次调用的用量（流末尾报一次，provider 给多少就是多少）。
   * 它只有一个去处：`Event.usage`（给人看 / 记账用），**不进 msgs** —— 账里放的是说过的话。
   */
  onUsage?(usage: Usage): void;
}

/** 一把钥匙 + 它的来源：来源是给人看的那一面，值不给任何人看。 */
export interface Credential {
  readonly key: string;
  /** 从哪来的（环境变量名 / 文件路径）：只出现在报错与日志里。 */
  readonly from: string;
}

export interface TransportInput {
  /** 用哪个模型：`provider/model`（模式串）。 */
  readonly model: string;
  /** 端点覆盖（可选）：走代理 / 自建网关才需要；不填就用该 provider 自带的端点。 */
  readonly baseUrl?: string;
  readonly credential: Credential;
}

export interface LlmClient {
  /**
   * 一次调用：这次伸得出的手（只要 schema）+ 一条 wire → 回复（正文 / 思考 / 手的调用）。
   *
   * 传进来的消息是我们内部的那份形状（账的形状），**由这一层挑键发出去** —— 各家认什么、
   * 不认什么（`reasoning` 要不要回传、`by` / `id` 这类记账字段一律不发、
   * provider 的临时 tool_call id 现造）是 provider 适配的事。
   */
  chat(wire: Wire, schemas: readonly JsonSchema[], on: StreamHandlers): Promise<WireMessage>;
}

/** 装配：引用 + 端点覆盖 + 钥匙 → 一次能发出去的传输面。 */
export declare function createClient(input: TransportInput): LlmClient;
