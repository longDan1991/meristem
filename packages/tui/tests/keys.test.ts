/**
 * 键的形状：opentui 的按键事件 → 全屏统一的那一种形状。
 *
 * 这条判据在"多个组件各挂各的键盘监听"之后变得要命：每个组件按这一种形状认自己的键，
 * 一颗键认错了名字（`return` 当成字、`space` 认不出、修饰键拼错），就有一处静默不响应。
 */
import { describe, expect, test } from "bun:test";
import { normalizeKey } from "../src/keys.ts";
import type { PressedKey } from "../src/keys.ts";

/** 一颗键：只给关心里那几个字段（其余按 opentui 的默认值）。 */
function key(name: string, rest: Partial<PressedKey> = {}): PressedKey {
  return { name, sequence: "", ctrl: false, meta: false, option: false, shift: false, ...rest };
}

describe("normalizeKey", () => {
  test("名字表里的键取表里的词", () => {
    expect(normalizeKey(key("return"))).toBe("enter");
    expect(normalizeKey(key("linefeed"))).toBe("enter");
    expect(normalizeKey(key("escape"))).toBe("escape");
    expect(normalizeKey(key("backspace"))).toBe("backspace");
    expect(normalizeKey(key("up"))).toBe("up");
    expect(normalizeKey(key("pagedown"))).toBe("pagedown");
  });

  test("打得出来的字原样（含中文与空格）", () => {
    expect(normalizeKey(key("a", { sequence: "a" }))).toBe("a");
    expect(normalizeKey(key("你", { sequence: "你" }))).toBe("你");
    expect(normalizeKey(key("space", { sequence: " " }))).toBe(" ");
  });

  test("修饰键拼成小写形状（meta / option 都算 alt）", () => {
    expect(normalizeKey(key("b", { ctrl: true, sequence: "\u0002" }))).toBe("ctrl+b");
    expect(normalizeKey(key("up", { option: true }))).toBe("alt+up");
    expect(normalizeKey(key("B", { ctrl: true, shift: true }))).toBe("ctrl+shift+b");
    expect(normalizeKey(key("space", { ctrl: true }))).toBe("ctrl+space");
  });

  test("控制字符不是字（终端给的原始序列挡在这里）", () => {
    expect(normalizeKey(key("", { sequence: "\u001b[1;5A" }))).toBeNull();
  });
});
