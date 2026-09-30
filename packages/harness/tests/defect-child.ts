/**
 * 缺陷场景的子进程（给 `tree.test.ts` 用）：一只手的 `run` 抛出（起不来）。
 *
 * 这里证明两件事：账里**没有**替它编出来的回话；缺陷**不被吞** —— 它带着真实的栈打在进程上。
 * 单独一个子进程是因为"把进程打穿"这件事在测试进程里没法验证（会把整个测试跑一起带走）。
 *
 * 用法：`bun run defect-child.ts <工作目录>`；退出码 7 = 缺陷如期到达进程边界。
 */
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load } from "@meristem/atree";
import type { Hand, Role } from "@meristem/roles";
import type { LlmClient } from "../src/llm.ts";
import type { Reply } from "../src/shape.ts";
import type { LineProps } from "../src/props.ts";
import type { WireMessage } from "../src/shape.ts";
import { start } from "../src/tree.ts";

const store = await load<LineProps, WireMessage>(
  join(mkdtempSync(join(tmpdir(), "meristem-defect-")), "tree.jsonl"),
);
const broken: Hand = {
  name: "broken",
  description: "起不来的那一只",
  schema: { type: "object", properties: {} },
  async run() {
    throw new Error("我起不来");
  },
};
const work: Role = {
  id: "work",
  title: "干活",
  about: "干活",
  system: () => "你是干活的",
  hands: () => [broken],
  findHand: (name) => (name === broken.name
    ? { kind: "hand", hand: broken }
    : { kind: "missing", answer: `没有叫 ${name} 的手` }),
};
const transport: LlmClient = {
  async chat(): Promise<Reply> {
    return { role: "assistant", content: "", toolCalls: [{ name: "broken", arguments: {} }] };
  },
};
const tree = start({ store, llm: transport, role: () => work });
const node = await tree.fork({ parent: null, role: "work", inputText: "随便", dir: process.argv[2] ?? "." });

process.on("uncaughtException", (error) => {
  console.log(`账里的话：${store.content(node).map((message) => message.role).join(",")}`);
  console.error(`缺陷：${error.message}`);
  process.exit(7);
});

tree.resume();
await Bun.sleep(200); // 缺陷该在这之前把进程打穿（真打穿了就到不了这里）
console.log("没崩 —— 缺陷被吞了");
process.exit(0);
