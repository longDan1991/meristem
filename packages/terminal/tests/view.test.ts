/**
 * 界面派生（纯函数）的边界：窗口要留住选中行、折叠要数得清、拆行不吞空串。
 *
 * 不碰 React、不碰 tui、不碰账 —— 全部吃数组吐数组，所以不需要屏幕也不需要文件。
 */
import { describe, expect, test } from "bun:test";
import { STRIP_ROWS, foldThoughts, split, treeWindow } from "../src/view.ts";
import type { Row, TreeRow } from "../src/view.ts";

function strip(n: number, selectedAt: number): readonly TreeRow[] {
  return Array.from({ length: n }, (_, i) => ({
    id: i === 2 ? null : `n${i}`, // 第 2 行是一条被折起来的子树（不可选中）
    text: `行 ${i}`,
    depth: 0,
    selected: i === selectedAt,
  }));
}

describe("treeWindow", () => {
  test("树不长时整棵都在窗口里", () => {
    const { window } = treeWindow(strip(3, 0), STRIP_ROWS);
    expect(window).toHaveLength(3);
  });

  test("树比窗口长时只铺 STRIP_ROWS 行", () => {
    const { window } = treeWindow(strip(40, 20), STRIP_ROWS);
    expect(window).toHaveLength(STRIP_ROWS);
  });

  test("选中行永远在窗口里（靠上、靠下、居中三种）", () => {
    const rows = strip(40, 0);
    for (const at of [0, 1, 20, 38, 39]) {
      const { window } = treeWindow(rows.map((row, i) => ({ ...row, selected: i === at })), STRIP_ROWS);
      expect(window.some((row) => row.selected)).toBe(true);
    }
  });

  test("可选中清单含全部有 id 的行，不含被折起来的行", () => {
    const { selectable } = treeWindow(strip(5, 0), STRIP_ROWS);
    expect(selectable).toEqual(["n0", "n1", "n3", "n4"]);
  });
});

describe("foldThoughts", () => {
  const row = (text: string, tag: Row["tag"]): Row => ({ text, tag });

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

describe("split", () => {
  test("空串不铺行", () => {
    expect(split("", "model")).toEqual([]);
  });

  test("按行拆开、每行带同一个标签", () => {
    expect(split("一\n二", "thought")).toEqual([
      { text: "一", tag: "thought" },
      { text: "二", tag: "thought" },
    ]);
  });
});
