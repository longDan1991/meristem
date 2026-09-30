/**
 * 键的形状：**归一化后哪些算"打进去一个字"**。
 *
 * 这条判据在"多个组件各挂各的键盘监听"之后变得要命：输入行对每个"字"都插一下，
 * 要是 `up` / `tab` / `enter` 也算字，按一下箭头就会往草稿里塞一个 `up`。
 */
import { describe, expect, test } from "bun:test";
import { isPrintable } from "../src/keys.ts";

describe("isPrintable", () => {
  test("打得出来的字（含中文、空格、整段粘贴）算字", () => {
    for (const key of ["a", "你", " ", "。", "粘贴一整行"]) expect(isPrintable(key)).toBe(true);
  });

  test("名字表里的键不算字 —— 哪怕它们没有修饰键", () => {
    for (const key of ["up", "down", "left", "right", "home", "end", "enter", "backspace", "delete", "escape", "tab", "pageup", "pagedown"]) {
      expect(isPrintable(key)).toBe(false);
    }
  });

  test("带修饰键的不算字", () => {
    for (const key of ["ctrl+b", "alt+b", "ctrl+o", "shift+tab", "alt+up"]) expect(isPrintable(key)).toBe(false);
  });

  test("空键不算字", () => {
    expect(isPrintable("")).toBe(false);
  });
});
