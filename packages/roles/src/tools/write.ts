/**
 * 手：`write` —— 写一个文件。
 *
 * 它是**作业**，属于"立刻结束"的那一种：用底座的 `settled(facts, 执行)` 包（DESIGN §9.3）。
 * 同步写完（内容本来就在手上）—— 它在 `run()` 返回时就已经结束，账里只占一条消息。
 *
 * 变因：这一只手的语义与实现。
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import type { Hand } from "../role.ts";
import { message, settled } from "../jobs/base.ts";
import { resolvePath } from "./paths.ts";

export interface WriteArgs {
  readonly path: string;
  readonly content: string;
}

export const WRITE: Hand = {
  name: "write",
  description:
    "写一个文件（父目录不存在就建）。路径相对的话落在你这棵树的输出根下（绝对路径照写）。\n" +
    "· content 是写进去的**全部**内容：整体覆盖，不是追加。",
  schema: {
    type: "object",
    properties: {
      path: { type: "string", description: "文件路径" },
      content: { type: "string", description: "写进去的全部内容（覆盖）" },
    },
    required: ["path", "content"],
    additionalProperties: false,
  },
  snippet: "写一个文件（覆盖）",
  async run(args: unknown, ctx) {
    const { path: given, content } = args as WriteArgs;
    const path = resolvePath(ctx.outputRoot, given);
    let text: string;
    try {
      mkdirSync(dirname(path), { recursive: true });
      writeFileSync(path, content, "utf8");
      text = `已写 ${path}（${content.length} 字）`;
    } catch (error) {
      text = `write 没能写 ${path}：${message(error)}`;
    }
    return settled({ space: ctx.space, name: "write" }, text);
  },
};
