/** @jsxImportSource @opentui/react */
/**
 * 一整屏的外壳：占满终端，并把**键的形状**归一化后交给调用方。
 *
 * 键位语义（哪个键是什么意思、要不要拦）全归调用方 —— 这里只做形状上的统一，
 * 所以不拦键、不做 `preventDefault` 之外的分支。
 *
 * 变因：键的归一化规则与外壳本身（终端尺寸怎么用）。
 */
import { useKeyboard, useTerminalDimensions } from "@opentui/react";
import type { KeyEvent } from "@opentui/core";
import type { ReactNode } from "react";

export interface FrameProps {
  readonly children: ReactNode;
  readonly onKey?: (key: string) => void;
}

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

/**
 * 归一化后的键：可打印字符原样（`"a"` / `"你"` / `" "`），特殊键取名字表里的词，
 * 带修饰键就是 `ctrl+b` / `alt+b` / `shift+tab` 这种小写形状。认不出来的键往上递没有意义（返回 null）。
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

export function Frame({ children, onKey }: FrameProps): ReactNode {
  const { width, height } = useTerminalDimensions();
  useKeyboard((event) => {
    if (onKey === undefined) return;
    const key = normalizeKey(event);
    if (key !== null) onKey(key);
  });
  return (
    <box width={width} height={height} flexDirection="column">
      {children}
    </box>
  );
}
