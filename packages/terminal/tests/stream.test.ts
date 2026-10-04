/**
 * 收起思考（`ctrl+o`）：一串思考压成一行说明，开头 / 末尾 / 没有思考三种都收得住。
 *
 * 只调纯函数（吃数组吐数组），不渲染。
 */
import { describe, expect, test } from "bun:test";
import { foldThoughts } from "../src/components/stream.tsx";
import type { Row } from "../src/lib/rows.ts";

const row = (text: string, tag: Row["tag"]): Row => ({ text, tag, kind: "line" });

describe("foldThoughts", () => {
  test("一串思考压成一行说明，其余原样按序", () => {
    const folded = foldThoughts([row("人说的", "user"), row("想 1", "thought"), row("想 2", "thought"), row("模型说的", "model")]);
    expect(folded.map((one) => one.text)).toEqual(["人说的", "▸ 思考 2 行（ctrl+o 展开）", "模型说的"]);
    expect(folded[1]?.tag).toBe("dim");
  });

  test("开头与末尾的两串都收得住", () => {
    const folded = foldThoughts([row("想 1", "thought"), row("正文", "model"), row("想 2", "thought")]);
    expect(folded.map((one) => one.text)).toEqual(["▸ 思考 1 行（ctrl+o 展开）", "正文", "▸ 思考 1 行（ctrl+o 展开）"]);
  });

  test("没有思考时不加任何说明行", () => {
    const rows = [row("人说的", "user"), row("模型说的", "model")];
    expect(foldThoughts(rows)).toEqual(rows);
  });
});
