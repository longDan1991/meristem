/**
 * 键的归一化与合法性：**这一份只统一键的形状，键是什么意思全归命令表**。
 *
 * opentui 给的每一次按键（`KeyEvent`）在这里变成一种唯一写法：`ctrl+b` / `alt+up` / `up` /
 * 打得出来的字。这张形状表是命令表（`commands.ts`）与总线（`bus.tsx`）共用的词表 ——
 * 表里写的键必须写得成运行时会出现的形状，否则那颗键永远不响，所以装载时用 `isKeySpec` 当场校验。
 *
 * **监听不在这儿**：谁按键、按了算哪条命令、有没有人接，都在 `bus.tsx` 的 provider 里收口
 * （整个界面只有那一处监听）—— 这样"界面认领的键"必然来自命令表，没有旁路。
 *
 * 变因：键的归一化规则（哪些 opentui 事件算哪个键）与"什么样的写法算界面认领的键"。
 */
import type { KeyEvent } from "@opentui/core";

/** opentui 的键名 → 归一化后的名字。没在这张表里的就是可打印字符（含中文 / 标点）。 */
const KEY_NAMES: Readonly<Record<string, string>> = {
  return: "enter",
  linefeed: "enter",
  backspace: "backspace",
  delete: "delete",
  escape: "escape",
  tab: "tab",
  up: "up",
  down: "down",
  left: "left",
  right: "right",
  home: "home",
  end: "end",
  pageup: "pageup",
  pagedown: "pagedown",
  space: " ",
};

/** 控制字符不是"人打的字"：终端给的原始序列（ESC 开头）靠它挡掉。 */
const CONTROL = /[\p{Cc}\p{Cs}]/u;

/** 归一化只看这几个字段（opentui 的 `KeyEvent` 满足它；这样这条规矩也能单独测）。 */
export type PressedKey = Pick<KeyEvent, "name" | "ctrl" | "meta" | "option" | "shift" | "sequence">;

/**
 * 归一化后的键：可打印字符原样（`"a"` / `"你"` / `" "`），特殊键取名字表里的词，
 * 带修饰键就是 `ctrl+b` / `alt+up` 这种小写形状。认不出来的键往上递没有意义（返回 null）。
 */
export function normalizeKey(event: PressedKey): string | null {
  const named = KEY_NAMES[event.name];
  const printable = event.sequence.length > 0 && !CONTROL.test(event.sequence) ? event.sequence : null;
  const base = named ?? printable ?? (event.name.length === 1 && !CONTROL.test(event.name) ? event.name : null);
  if (base === null) return null;
  const mods: string[] = [];
  if (event.ctrl) mods.push("ctrl");
  if (event.meta || event.option) mods.push("alt");
  if (event.shift) mods.push("shift");
  if (mods.length === 0) return base;
  const key = base === " " ? "space" : base.length === 1 ? base.toLowerCase() : base;
  return [...mods, key].join("+");
}

/** 修饰键的次序：`normalizeKey` 只产出这一种排法（`ctrl` → `alt` → `shift`）。 */
const MODIFIERS = ["ctrl", "alt", "shift"] as const;

/** 特殊键的那些名字（`normalizeKey` 认得的那张表的值；裸空格不算 —— 那是打字）。 */
const NAMED = new Set<string>(Object.values(KEY_NAMES).filter((name) => name !== " "));

/**
 * 这份写法能不能当**界面认领的键**：特殊键（`up` / `enter` / `escape`…，可带修饰键）或
 * 一个带修饰键的字符（`ctrl+b`）。**裸字符不是** —— 那是打字，归输入件（P0 §2.1：裸字符不是入口）。
 * 命令表装载时用它校验，写错一个键当场炸。
 */
export function isKeySpec(text: string): boolean {
  const parts = text.split("+");
  const base = parts.pop() ?? "";
  if (base === "") return false;
  // 修饰键各一次、次序与 `normalizeKey` 拼的一致（ctrl → alt → shift）。
  let last = -1;
  for (const mod of parts) {
    const at = (MODIFIERS as readonly string[]).indexOf(mod);
    if (at <= last) return false;
    last = at;
  }
  if (parts.length === 0) return NAMED.has(base);
  return NAMED.has(base) || base === "space" || (base.length === 1 && /[a-z0-9]/.test(base));
}
