/**
 * 键的注册与归一化：**tui 只统一键的形状，键是什么意思全归调用方**。
 *
 * 每个关心按键的组件自己调一次 `useKeys` —— opentui 的 `useKeyboard` 是"每次调用挂一个监听"，
 * 多个组件各挂各的、都会收到每一次按键，所以"这个键归哪个组件"由组件自己声明（谁在意谁接），
 * 这里只保证大家看到的是同一种形状：`ctrl+b` / `alt+up` / `up` / 打得出来的字。
 *
 * 传进来的函数**永远是最新的那个**（opentui 内部用 `useEffectEvent` 转接，只挂一次监听），
 * 所以调用方不必操心"订阅要不要重挂"。
 *
 * 变因：键的归一化规则（哪些 opentui 事件算哪个键）。
 */
import type { KeyEvent } from "@opentui/core";
import { useKeyboard } from "@opentui/react";

export type KeyHandler = (key: string) => void;

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

/**
 * 命令键：这些名字不是"人打的字"。
 * 空格不在里面 —— 它既是名字表里的词，也真的是一个字。
 */
const COMMANDS: ReadonlySet<string> = new Set([
  "enter",
  "backspace",
  "delete",
  "escape",
  "tab",
  "up",
  "down",
  "left",
  "right",
  "home",
  "end",
  "pageup",
  "pagedown",
]);

/** 控制字符不是"人打的字"：终端给的原始序列（ESC 开头）靠它挡掉。 */
const CONTROL = /[\p{Cc}\p{Cs}]/u;

/**
 * 归一化后的键：可打印字符原样（`"a"` / `"你"` / `" "`），特殊键取名字表里的词，
 * 带修饰键就是 `ctrl+b` / `alt+up` 这种小写形状。认不出来的键往上递没有意义（返回 null）。
 */
function normalizeKey(event: KeyEvent): string | null {
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

export function useKeys(handler: KeyHandler): void {
  useKeyboard((event) => {
    const key = normalizeKey(event);
    if (key !== null) handler(key);
  });
}

export function isPrintable(key: string): boolean {
  return key.length > 0 && !key.includes("+") && !COMMANDS.has(key);
}
