/**
 * 树条带窗口的边界：树不长时整棵在窗口里、树长时只铺 STRIP_ROWS 行、选中行永远落得住、
 * 可选中清单含全部有 id 的行而**不含**被折起来的行。
 *
 * 只调纯函数（吃数组吐数组），不渲染。
 */
import { describe, expect, test } from "bun:test";
import { STRIP_ROWS, treeWindow } from "../src/components/tree-strip.tsx";
import type { TreeRow } from "../src/components/tree-strip.tsx";

function strip(n: number, selectedAt: number): readonly TreeRow[] {
  return Array.from({ length: n }, (_, i) => ({
    key: i === 2 ? `fold:${i}` : `n${i}`,
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
