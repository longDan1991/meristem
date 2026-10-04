/**
 * 键的注册与归一化：**tui 只统一键的形状，键是什么意思全归调用方**。
 *
 * 每个关心按键的组件自己调一次 `useKeys` —— opentui 的 `useKeyboard` 是"每次调用挂一个监听"，
 * 多个组件各挂各的、都会收到每一次按键，所以"这个键归哪个组件"由组件自己声明（谁在意谁接），
 * 这里只保证大家看到的是同一种形状：`ctrl+b` / `alt+up` / `up` / 打得出来的字。
 *
 * **接了的键要"拿走"**：返回 `true` = 这个键我处理了，于是 `preventDefault()`。opentui 的派发顺序是
 * 全局监听（就是这里）先过、焦点里的那个可编辑件（`<input>` / `<textarea>`）后过，看到
 * `defaultPrevented` 就不动手 —— 不然同一次 `ctrl+b` 会既被我们拿去分叉、又被输入框当成"光标左移"。
 * 没处理的键（返回 `false` / 什么都不返回）原样落到焦点件上，所以打字、删除、左右移动仍然是它的。
 *
 * 传进来的函数**永远是最新的那个**（opentui 内部用 `useEffectEvent` 转接，只挂一次监听），
 * 所以调用方不必操心"订阅要不要重挂"。
 *
 * 变因：键的归一化规则（哪些 opentui 事件算哪个键）与"谁拿走这个键"的约定。
 */
import type { KeyEvent } from "@opentui/core";
import { useKeyboard } from "@opentui/react";

/** 处理一个归一化后的键；返回 `true` 表示这个键归调用方，不再往下递给焦点里的可编辑件。 */
export type KeyHandler = (key: string) => boolean | void;

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

export function useKeys(handler: KeyHandler): void {
  useKeyboard((event) => {
    const key = normalizeKey(event);
    if (key === null) return;
    if (handler(key) === true) event.preventDefault();
  });
}
