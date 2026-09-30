/**
 * 按**格**处理文本：两件共用的小事 —— 拆成字（每个字占几格）与"掐到预算以内"。
 *
 * 为什么单独一处：中文是双宽，按 `length` 数会歪；而"一个字要么整格留下、要么整格不要"
 * 这条规矩必须**只有一份**（状态条与输入行都按它切窗口，各写一份迟早会一份切半个宽字符）。
 *
 * 变因：格宽这条规矩本身（怎么数、切在哪）。
 */
import { stringWidth } from "bun";

/** 一个字符 + 它在原串里的下标 + 它占几格（`for…of` 按码点走，代理对不会被切成半个）。 */
export interface Glyph {
  readonly ch: string;
  readonly at: number;
  readonly wide: number;
}

/** 拆成字（`at` 是 UTF-16 下标，调用方拿它对比光标位置）。 */
export function glyphs(text: string): readonly Glyph[] {
  const out: Glyph[] = [];
  let at = 0;
  for (const ch of text) {
    out.push({ ch, at, wide: stringWidth(ch) });
    at += ch.length;
  }
  return out;
}

/** 这些字一共占几格。 */
export function cellsOf(list: readonly Glyph[]): number {
  return list.reduce((sum, glyph) => sum + glyph.wide, 0);
}

/** 连同字符一起拼回来（`textOf(glyphs(x)) === x`）。 */
export function textOf(list: readonly Glyph[]): string {
  return list.map((glyph) => glyph.ch).join("");
}

/** 掐尾巴：放不下就裁到 `budget` 格以内并补省略号（`budget <= 0` = 整段不画）。 */
export function clipTail(text: string, budget: number): string {
  if (budget <= 0) return "";
  if (stringWidth(text) <= budget) return text;
  const room = budget - 1;
  let cut = "";
  for (const ch of text) {
    if (stringWidth(cut + ch) > room) break;
    cut += ch;
  }
  return `${cut}…`;
}
