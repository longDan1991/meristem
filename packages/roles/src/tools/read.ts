/**
 * 手：`read` —— 读一段文件（按字节翻页）。
 *
 * 它是**作业**，但属于"立刻结束"的那一种：用底座的 `settled(facts, 执行)` 包（DESIGN §9.3）。
 * 同步算完（窗口读，只读要的那一段）—— 这样它在 `run()` 返回时就已经结束，
 * 循环那条"起手一条回话、结束一条消息"只落在一条消息上（读文件不该在账里占两行）。
 *
 * 翻页参数在 schema 里；交代里要给出"下一段"的 offset（§5.6：截断 / 翻页必须说得出来）：
 * 单位是**字节**，读不动二进制（只告诉你是二进制、多大）。
 *
 * 变因：这一只手的语义与实现。
 */
import { closeSync, openSync, readSync, statSync } from "node:fs";
import type { Hand } from "../role.ts";
import { message, settled } from "../jobs/base.ts";
import { resolvePath } from "./paths.ts";

export interface ReadArgs {
  readonly path: string;
  /** 翻页：从第几个**字节**开始（交代里给出的"下一段"就是它）。 */
  readonly offset?: number;
  /** 最多读多少**字节**。 */
  readonly limit?: number;
}

const DEFAULT_LIMIT = 20_000;

export const READ: Hand = {
  name: "read",
  description:
    "读一个文件的一段。路径相对的话落在你这棵树的输出根下（绝对路径照读）。\n" +
    `· offset：从第几个**字节**开始，不写就是 0；limit：最多读多少**字节**，不写就是 ${DEFAULT_LIMIT}。\n` +
    "· 交代的第一行写着文件总字节数与本段范围；没读完的话最后一行写着下一段该给的 offset。\n" +
    "· 二进制文件不会被当文本读出来（只告诉你它是二进制、共多大）。",
  schema: {
    type: "object",
    properties: {
      path: { type: "string", description: "文件路径" },
      offset: { type: "integer", description: "从第几个字节开始（缺省 0）" },
      limit: { type: "integer", description: `最多读多少字节（缺省 ${DEFAULT_LIMIT}）` },
    },
    required: ["path"],
    additionalProperties: false,
  },
  snippet: "读一个文件的一段（按字节翻页）",
  guidelines: ["翻页要按交代里给的 offset 接着读：别把同一个文件从头读很多次。"],
  async run(args: unknown, ctx) {
    const { path: given, offset = 0, limit = DEFAULT_LIMIT } = args as ReadArgs;
    const path = resolvePath(ctx.outputRoot, given);
    let text: string;
    try {
      text = window(path, Math.max(0, offset), Math.max(0, limit));
    } catch (error) {
      text = `read 没能读 ${path}：${message(error)}`;
    }
    return settled({ space: ctx.space, name: "read" }, text);
  },
};

/** 读一段（同步、只读这一段，所以文件多大都不影响这次调用的开销）。 */
function window(path: string, offset: number, limit: number): string {
  const size = statSync(path).size;
  if (size === 0) return `${path}（空文件）`;
  if (offset >= size) {
    return `${path}（共 ${size} 字节；offset ${offset} 已经越过结尾，这里没有内容）`;
  }

  const length = Math.min(limit, size - offset);
  const buffer = Buffer.allocUnsafe(length);
  const fd = openSync(path, "r");
  let read = 0;
  try {
    read = readSync(fd, buffer, 0, length, offset);
  } finally {
    closeSync(fd);
  }

  const bytes = buffer.subarray(0, read);
  if (bytes.includes(0)) {
    return `${path}（二进制文件：共 ${size} 字节，没有按文本读）`;
  }

  // 窗口的两端可能切在多字节字符中间：切出来的半个字符不成字，去掉（换行 / 缺字由 offset 接着读）。
  const text = new TextDecoder("utf-8").decode(bytes).replace(/^\uFFFD/, "").replace(/\uFFFD$/, "");
  const end = offset + read;
  const rest = size - end;
  const more = rest > 0 ? `（还有 ${rest} 字节；下一段：offset=${end}）` : "（到这里就完了）";
  return `${path}（共 ${size} 字节；本段 ${offset}–${end}）\n${text}\n${more}`;
}
