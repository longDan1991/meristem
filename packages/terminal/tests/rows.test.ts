/**
 * 拆行（`split`）：空串不铺行、其余按行拆开、每行带同一个标签。
 *
 * 只调纯函数（吃字吐数组），不渲染。
 */
import { describe, expect, test } from "bun:test";
import { split } from "../src/lib/rows.ts";

describe("split", () => {
  test("空串不铺行", () => {
    expect(split("", "model")).toEqual([]);
  });

  test("按行拆开、每行带同一个标签", () => {
    expect(split("一\n二", "thought")).toEqual([
      { text: "一", tag: "thought", kind: "line" },
      { text: "二", tag: "thought", kind: "line" },
    ]);
  });
});
