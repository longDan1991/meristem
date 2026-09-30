/**
 * 传输：给一条 wire + 这次伸得出的手，拿回一条回复（可能带手的调用）。
 *
 * 只吃 `@earendil-works/pi-ai` 的**传输面**（provider 适配 / 流式 / 它自带的瞬时重试 / usage /
 * 模型目录），而且引**子路径**（`/providers/all`），不引根入口 —— 面只露真的用得到的。
 * 它的 agent 层、会话、工具执行、TUI 都不引入：那套会话模型与本设计的树冲突。
 *
 * **两个 id 的分工**（DESIGN §9.6）：账里的参照物是**我们的**（`WireMessage.id`，写账时定死）；
 * provider 要的 `tool_calls[].id` / `tool_call_id` 是**临时物**，由这一层**出网时现造**
 * （同一段历史每次请求各造一套，互不认识也无所谓 —— 程序不靠它配对）。一句话：**临时 id 不进账，
 * 记账 id 不出网**。
 *
 * **配对不是程序的事**：作业 id 拼在消息内容里（起手一条、结束一条），模型自己认。
 * 这一层只按**账上的顺序**把起手那条回话配给对应的调用 —— 账保证"每条 `tool_calls` 后面就跟着
 * 它的回话"（`relay` 写账的顺序，DESIGN §9.5）。
 *
 * **回放历史**：provider 认的那份形状里，一条 assistant 必须带上 `api` / `provider` / `model` / `usage`
 * 这些字段，而账里只存"说过的话" —— 用量不进账（它只去 `Event.usage`），所以回放时给一份空用量；
 * 临时 id 现造；`id` / `by` 这类记账字段一个都不发。
 *
 * **思考的原文回得去，但签名回不去**：账里存的是思考**原文**（`WireMessage.reasoning`），
 * provider 认的回放签名不存 —— 于是 pi 只在有签名时才把原文发回去，没有签名的地方它按 compat
 * 补一个空字段（DeepSeek 这类"必须带 `reasoning_content`"的 provider 因此不会 400，但模型看不到
 * 上一轮的思考原文）。**要让原文带着回放，得把签名也记进账 —— 那是改设计，不是改这一层。**
 *
 * 自己的需要自己声明（不认任何配置对象）：**模型引用**、可选的**端点覆盖**、**钥匙**。
 * 引用在这里解析成"模型"这个事实（走 pi-ai 的模型目录：上下文多大、支不支持思考）；
 * 解析不出来当场炸（带上这家 provider 有哪些模型）。元数据先只服务传输（思考通道开不开、请求怎么发）；
 * 哪天调度要用（比如"这条线装不下了"），也是从这里把事实递出去，别处不许再解释一遍引用。
 *
 * **钥匙是装配层取的**（从哪个环境变量 / 文件来不归这里管），取完立刻交到这一个函数里。
 * 报错时只说 `credential.from`，**永不说 `key`** —— 401 要说得清是哪把钥匙被拒了。
 *
 * 变因：provider 与流式细节（换端点、换模型、换 SDK）。
 */
import type {
  Api,
  AssistantMessage,
  Context,
  JsonObject,
  Message,
  Model,
  Models,
  ThinkingContent,
  Tool,
  ToolCall as WireToolCall,
  TSchema,
  TextContent,
  Usage as WireUsage,
} from "@earendil-works/pi-ai";
import { builtinModels } from "@earendil-works/pi-ai/providers/all";
import type { Reply, ToolCall, ToolSpec, Usage, Wire, WireMessage } from "./shape.ts";

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
  /** 用哪个模型：`provider/model`（模式串，只在第一个 `/` 上断）。 */
  readonly model: string;
  /**
   * 真正发给端点的模型 id（可选）：目录里那份只负责"怎么发"（wire api 与元数据），
   * 换了名字的部署（自建网关 / 搬迁到别家）用它说出端点认的那串。不填就用目录里那份的 id。
   */
  readonly modelId?: string;
  /** 端点覆盖（可选）：走代理 / 自建网关才需要；不填就用该 provider 自带的端点。 */
  readonly baseUrl?: string;
  readonly credential: Credential;
}

export interface LlmClient {
  /**
   * 一次调用：这次伸得出的手（名字 / 描述 / schema）+ 一条 wire → 回复（正文 / 思考 / 手的调用）。
   *
   * 传进来的消息是我们内部的那份形状（账的形状），**由这一层挑键发出去** —— 各家认什么、
   * 不认什么（`reasoning` 要不要回传、`by` / `id` 这类记账字段一律不发、
   * provider 的临时 tool_call id 现造）是 provider 适配的事。
   */
  chat(wire: Wire, hands: readonly ToolSpec[], on: StreamHandlers): Promise<Reply>;
}

/**
 * 装配：引用 + 端点覆盖 + 钥匙 → 一次能发出去的传输面。
 *
 * `models` 缺省就是 pi-ai 的内置目录；显式传的那份是**测试留的口子**（假 provider 也走同一条路）。
 */
export function createClient(input: TransportInput, models: Models = builtinModels()): LlmClient {
  const model = resolve(models, input.model, input.baseUrl, input.modelId);
  return {
    async chat(wire, hands, on) {
      const context: Context = {
        systemPrompt: wire.system,
        messages: toMessages(wire.messages, model),
        tools: hands.map(toTool),
      };

      let reply: AssistantMessage | undefined;
      try {
        // 瞬时重试是 pi 的事（它的 SDK 层自带）；这一层不自己写重试循环，也不给模型设统一超时（§9.9）。
        for await (const event of models.stream(model, context, { apiKey: input.credential.key })) {
          switch (event.type) {
            case "text_delta":
              on.onText?.(event.delta);
              break;
            case "thinking_delta":
              on.onReasoning?.(event.delta);
              break;
            case "done":
              reply = event.message;
              break;
            case "error":
              // provider 的失败也是一条"回复"（形状上带 errorMessage）—— 在这里变成抛出，带着上下文炸出去。
              throw new Error(event.error.errorMessage ?? "provider 没给说法");
            default:
              break;
          }
        }
      } catch (error) {
        throw failed(error, model, input.credential.from);
      }

      if (reply === undefined) {
        throw new Error(
          `模型接口没给结局就把流收了（${model.provider}/${model.id}，钥匙来自 ${input.credential.from}）`,
        );
      }
      on.onUsage?.(toUsage(reply.usage));
      return fromAssistant(reply);
    },
  };
}

/** 引用 → 模型：解析不出来当场炸，并说清这家 provider 有哪些模型（不静默换一个）。 */
function resolve(
  models: Models,
  reference: string,
  baseUrl: string | undefined,
  sentId: string | undefined,
): Model<Api> {
  const cut = reference.indexOf("/");
  if (cut <= 0 || cut === reference.length - 1) {
    throw new Error(`模型引用要写成 provider/model（例如 deepseek/deepseek-flash），收到的是：${reference}`);
  }
  const provider = reference.slice(0, cut);
  const id = reference.slice(cut + 1);
  const model = models.getModel(provider, id);
  if (model === undefined) {
    const known = models.getModels(provider).map((one) => one.id);
    throw new Error(
      known.length === 0
        ? `模型目录里没有这家 provider：${provider}（引用是 ${reference}）`
        : `模型目录里 ${provider} 没有这个模型：${id}（它有：${known.join(" / ")}）`,
    );
  }
  // 端点覆盖与"发出去的 id"都是这一层的输入，而 pi 把它们挂在模型上 —— 复制一份，不动目录里那份。
  return {
    ...model,
    ...(baseUrl === undefined ? {} : { baseUrl }),
    ...(sentId === undefined ? {} : { id: sentId }),
  };
}

/** 账里的形状 → provider 的形状：**挑键**的地方（记账字段一个都不发，临时 id 现造）。 */
function toMessages(messages: readonly WireMessage[], model: Model<Api>): Message[] {
  const out: Message[] = [];
  // 时间戳只是 provider 的形状要求；账里的先后由写账顺序定，不由它定。
  const at = Date.now();
  // 上一条 assistant 发出的调用，与它按顺序等着认领的回话（游标，别在循环里切数组）。
  let waiting: readonly WireToolCall[] = [];
  let claimed = 0;
  // 这一次请求里第几个调用：临时 id 只要求在**这一次请求里**唯一 —— 我们的记账 id 一个字节都不出网。
  let minted = 0;

  for (const message of messages) {
    switch (message.role) {
      case "system":
        // 账里正常不该有 system（system 走 `wire.system`）；真出现了就按形状发出去，不吞掉。
        out.push({ role: "system", content: message.content, timestamp: at });
        break;

      case "user":
        out.push({ role: "user", content: message.content, timestamp: at });
        break;

      case "assistant": {
        const calls: WireToolCall[] = [];
        for (const call of message.toolCalls ?? []) {
          minted += 1;
          // 临时 id：provider 拿它在这一次请求里配对，出网即弃（下一次请求另造一套）—— 不进账，也不带账里的 id。
          calls.push({ type: "toolCall", id: `调用 ${minted}`, name: call.name, arguments: call.arguments as JsonObject });
        }
        const content: (TextContent | ThinkingContent | WireToolCall)[] = [];
        if (message.reasoning !== undefined) content.push({ type: "thinking", thinking: message.reasoning });
        if (message.content !== "") content.push({ type: "text", text: message.content });
        content.push(...calls);
        out.push({
          role: "assistant",
          content,
          api: model.api,
          provider: model.provider,
          model: model.id,
          // 账里不存用量（它只去 `Event.usage`）；回放不需要它，给空的那份。
          usage: EMPTY_USAGE,
          stopReason: calls.length === 0 ? "stop" : "toolUse",
          timestamp: at,
        });
        waiting = calls;
        claimed = 0;
        break;
      }

      case "tool": {
        const call = waiting[claimed];
        if (call === undefined) {
          throw new Error(
            `账里有一条没有对应调用的手回话（消息 id ${message.id}）：起手回话必须与 tool_calls 一一对应、同序`,
          );
        }
        claimed += 1;
        out.push({
          role: "toolResult",
          toolCallId: call.id,
          toolName: call.name,
          content: [{ type: "text", text: message.content }],
          // 账里没有错误位：失败也是一段交代（DESIGN §9）—— 与"这条回话是不是坏消息"无关。
          isError: false,
          timestamp: at,
        });
        break;
      }
    }
  }
  return out;
}

/** 一只手 → provider 认的工具：schema 是唯一语义来源，一个字段都不改。 */
function toTool(hand: ToolSpec): Tool {
  // 手给的 schema 就是 provider 原样吃的 JSON Schema；pi 的 `Tool` 收 TypeBox 的 `TSchema`
  // （同一份 JSON，只是标注更紧）—— 这是外部契约边界上唯一的标注。
  return { name: hand.name, description: hand.description, parameters: hand.schema as TSchema };
}

/** provider 的形状 → 账里的形状：**挑键**的地方（api / usage / 时间戳都不进账）。 */
function fromAssistant(message: AssistantMessage): Reply {
  const texts: string[] = [];
  const thoughts: string[] = [];
  const toolCalls: ToolCall[] = [];
  for (const block of message.content) {
    switch (block.type) {
      case "text":
        texts.push(block.text);
        break;
      case "thinking":
        thoughts.push(block.thinking);
        break;
      case "toolCall":
        toolCalls.push({ name: block.name, arguments: block.arguments });
        break;
    }
  }
  const reasoning = thoughts.join("");
  return {
    role: "assistant",
    content: texts.join(""),
    ...(reasoning === "" ? {} : { reasoning }),
    ...(toolCalls.length === 0 ? {} : { toolCalls }),
  };
}

/** provider 的用量 → 我们的用量（名字不同，去处在 `Event.usage`）。 */
function toUsage(usage: WireUsage): Usage {
  return {
    prompt: usage.input,
    completion: usage.output,
    reasoning: usage.reasoning ?? 0,
    cached: usage.cacheRead,
    total: usage.totalTokens,
  };
}

/** 传输失败：说清哪个模型、哪把钥匙（**只说来源，永远不说值**），并留下原始错误。 */
function failed(error: unknown, model: Model<Api>, from: string): Error {
  const detail = error instanceof Error ? error.message : String(error);
  return new Error(
    `模型接口失败（${model.provider}/${model.id}，钥匙来自 ${from}）：${detail}`,
    { cause: error },
  );
}

/** 回放历史用的空用量：账里不存用量，provider 回放时也不需要它。 */
const EMPTY_USAGE: WireUsage = {
  input: 0,
  output: 0,
  cacheRead: 0,
  cacheWrite: 0,
  totalTokens: 0,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
};
