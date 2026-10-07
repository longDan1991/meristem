/**
 * 键的归一化（命令模块里"纯的那半"）：opentui 的按键事件 → 全屏统一的那一种形状，
 * 外加"这份写法能不能当界面认领的键"（命令表装载时用它把关）。
 *
 * 这条判据要命的地方：**表里写的键必须写得成运行时会出现的形状** —— 一颗键认错了名字
 * （`return` 当成字、`space` 认不出、修饰键拼错），结果就是那一条命令永远不响，而屏幕上看不出为什么。
 */
import { describe, expect, test } from "bun:test";
import { isKeySpec, normalizeKey } from "../src/command/keys.ts";
import type { PressedKey } from "../src/command/keys.ts";

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

/**
 * 命令表装载时用的那条：这份写法能不能当**界面认领的键**。
 * 判据与 `normalizeKey` 的产出对齐 —— 表里写不出运行时会出现的形状，就是一颗永远不响的键；
 * 而裸字符必须是"打字"，不能被界面认领（`P0/02-screens.md` §2.1）。
 */
describe("isKeySpec", () => {
  test("特殊键与带修饰键的组合都算", () => {
    for (const text of ["up", "down", "enter", "escape", "tab", "pageup", "ctrl+b", "alt+m", "ctrl+o", "alt+r", "ctrl+shift+b", "ctrl+space"]) {
      expect(isKeySpec(text)).toBe(true);
    }
  });

  test("裸字符不算（那是打字）", () => {
    for (const text of ["j", "a", "1", "你", " "]) {
      expect(isKeySpec(text)).toBe(false);
    }
  });

  test("拼错的写法不算：不认识的键名、不认识的修饰键、乱的次序、重复的修饰键", () => {
    for (const text of ["nope", "super+b", "alt+ctrl+b", "ctrl+ctrl+b", "meta+b", "+b", "ctrl+"]) {
      expect(isKeySpec(text)).toBe(false);
    }
  });
});
