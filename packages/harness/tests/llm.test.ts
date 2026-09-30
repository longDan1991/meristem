/**
 * 传输层：走 pi-ai 自带的**假 provider**（同一条路，只有网络是假的）——
 * 账 → provider 的形状、流 → 三件事（正文 / 思考 / 用量）、provider 的失败 → 抛出、引用解析。
 */
import {
  createModels,
  fauxAssistantMessage,
  fauxProvider,
  fauxText,
  fauxThinking,
  fauxToolCall,
} from "@earendil-works/pi-ai";
import { describe, expect, test } from "bun:test";
import type { LlmClient, TransportInput } from "../src/llm.ts";
import { createClient } from "../src/llm.ts";
import type { ToolSpec, Usage, WireMessage } from "../src/shape.ts";

const HANDS: readonly ToolSpec[] = [
  {
    name: "read",
    description: "读一个文件",
    schema: { type: "object", properties: { path: { type: "string" } } },
  },
];

const CREDENTIAL = { key: "k-1", from: "TEST_KEY" };

/** 一份走假 provider 的传输：目录显式传进去，其余与生产同一条路。 */
function rig(baseUrl?: string): { readonly client: LlmClient; readonly faux: ReturnType<typeof fauxProvider> } {
  const faux = fauxProvider({ models: [{ id: "faux-flash", reasoning: true }] });
  const models = createModels();
  models.setProvider(faux.provider);
  const input: TransportInput = {
    model: `${faux.provider.id}/faux-flash`,
    credential: CREDENTIAL,
    ...(baseUrl === undefined ? {} : { baseUrl }),
  };
  return { client: createClient(input, models), faux };
}

const user = (content: string): WireMessage => ({ id: "u1", role: "user", content });

describe("传输：账 → provider → 账", () => {
  test("一轮说下来的三件事各就各位；回复里没有 id", async () => {
    const { client, faux } = rig();
    faux.setResponses([
      fauxAssistantMessage(
        [fauxThinking("先看一眼"), fauxText("你好"), fauxToolCall("read", { path: "/tmp/a" })],
        { stopReason: "toolUse" },
      ),
    ]);

    const texts: string[] = [];
    const thoughts: string[] = [];
    const usages: Usage[] = [];
    const reply = await client.chat({ system: "你是干活的", messages: [user("在吗")] }, HANDS, {
      onText: (delta) => texts.push(delta),
      onReasoning: (delta) => thoughts.push(delta),
      onUsage: (usage) => usages.push(usage),
    });

    expect(texts.join("")).toBe("你好");
    expect(thoughts.join("")).toBe("先看一眼");
    expect(usages).toHaveLength(1);
    expect(usages[0]?.prompt).toBeGreaterThan(0);
    expect(usages[0]?.completion).toBeGreaterThan(0);
    expect(usages[0]?.total).toBeGreaterThan(0);

    expect(reply.role).toBe("assistant");
    expect(reply.content).toBe("你好");
    expect(reply.reasoning).toBe("先看一眼");
    expect(reply.toolCalls).toEqual([{ name: "read", arguments: { path: "/tmp/a" } }]);
    expect("id" in reply).toBe(false);
  });

  test("出网的那份：system 与手原样、记账字段一个都不发、起手回话按顺序配给调用", async () => {
    const { client, faux } = rig();
    let sent: unknown;
    faux.setResponses([
      (context) => {
        sent = context;
        return fauxAssistantMessage(fauxText("好"));
      },
    ]);

    const messages: WireMessage[] = [
      user("读一下 /a"),
      {
        id: "m2",
        role: "assistant",
        content: "看看",
        reasoning: "先想",
        toolCalls: [{ name: "read", arguments: { path: "/a" } }],
        by: "work",
      },
      { id: "m3", role: "tool", content: "起手：作业 #1（read）", by: "read" },
      { id: "m4", role: "user", content: "作业 #1（read）：读完了", by: "read" },
    ];
    await client.chat({ system: "你是干活的", messages }, HANDS, {});

    const wire = sent as { messages: Record<string, unknown>[] };
    expect(wire.messages.map((message) => message.role)).toEqual([
      "system",
      "user",
      "assistant",
      "toolResult",
      "user",
    ]);

    const [system, firstUser, assistant, result, settle] = wire.messages;
    expect(system?.content).toBe("你是干活的");
    expect(system?.toolsAdded).toEqual([
      { name: "read", description: "读一个文件", parameters: HANDS[0]?.schema },
    ]);
    expect(firstUser?.content).toBe("读一下 /a");

    const blocks = assistant?.content as {
      type: string;
      thinking?: string;
      text?: string;
      id?: string;
      name?: string;
      arguments?: unknown;
    }[];
    expect(blocks.map((block) => block.type)).toEqual(["thinking", "text", "toolCall"]);
    expect(blocks[0]?.thinking).toBe("先想");
    expect(blocks[1]?.text).toBe("看看");
    expect(blocks[2]?.name).toBe("read");
    expect(blocks[2]?.arguments).toEqual({ path: "/a" });
    expect(typeof blocks[2]?.id).toBe("string");
    expect(assistant?.stopReason).toBe("toolUse");

    // 起手那条回话认领的正是这个调用（按账上的顺序配）
    expect(result?.toolCallId).toBe(blocks[2]?.id);
    expect(result?.toolName).toBe("read");
    expect(result?.content).toEqual([{ type: "text", text: "起手：作业 #1（read）" }]);
    expect(result?.isError).toBe(false);

    // 结束那条在账里就是 user（它带着 `by`，但不发）
    expect(settle?.role).toBe("user");
    expect(settle?.content).toBe("作业 #1（read）：读完了");

    // 记账字段与我们的 id 一个字节都不出网
    for (const message of wire.messages) {
      expect("by" in message).toBe(false);
      expect("id" in message).toBe(false);
    }
    const sentText = JSON.stringify(wire);
    for (const id of ["u1", "m2", "m3", "m4"]) expect(sentText).not.toContain(id);
  });

  test("端点覆盖：挂在模型上发给 provider", async () => {
    const { client, faux } = rig("https://自建网关/v1");
    let seen: { baseUrl: string } | undefined;
    faux.setResponses([
      (_context, _options, _state, model) => {
        seen = model as { baseUrl: string };
        return fauxAssistantMessage(fauxText("好"));
      },
    ]);

    await client.chat({ system: "你是干活的", messages: [user("在吗")] }, [], {});
    expect(seen?.baseUrl).toBe("https://自建网关/v1");
  });

  test("provider 失败：带着模型与钥匙来源抛出来，钥匙的值一个字节都不出现", async () => {
    const { client, faux } = rig();
    expect(faux.getPendingResponseCount()).toBe(0); // 一条回复都不排队：假 provider 会回一条 error

    const caught = await client
      .chat({ system: "你是干活的", messages: [user("在吗")] }, HANDS, {})
      .catch((error: unknown) => error);

    expect(caught).toBeInstanceOf(Error);
    const message = (caught as Error).message;
    expect(message).toContain("模型接口失败（faux/faux-flash，钥匙来自 TEST_KEY）");
    expect(message).toContain("No more faux responses queued"); // provider 的原话留着
    expect(message).not.toContain("k-1");
  });
});

describe("引用解析：取不到就当场炸", () => {
  test("写成 provider/model；这家 provider / 这个模型没有，都抛出来", () => {
    expect(() => createClient({ model: "没有斜杠", credential: CREDENTIAL })).toThrow(/provider\/model/);
    expect(() => createClient({ model: "这家不存在/m", credential: CREDENTIAL })).toThrow(
      /没有这家 provider：这家不存在/,
    );
    expect(() => createClient({ model: "deepseek/没有这个模型", credential: CREDENTIAL })).toThrow(
      /deepseek 没有这个模型：没有这个模型/,
    );
  });

  test("内置目录里 deepseek/deepseek-flash 取得出来（配置里就写这个）", () => {
    expect(() => createClient({ model: "deepseek/deepseek-flash", credential: CREDENTIAL })).not.toThrow();
  });
});
