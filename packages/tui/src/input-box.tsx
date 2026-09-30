/** @jsxImportSource @opentui/react */
/**
 * 输入行：**只显示不接收输入**（输入缓冲区归调用方，编辑键也归调用方）。
 *
 * 一行高、不换行。光标画在 `caret` 那个字符**前面**；值为空时也画（后面跟着 placeholder），
 * 让人看得出"这里能打字"。
 *
 * **看不见也要说得出来**：一行放不下整段话时水平窗口跟着光标走，被截掉的那一侧画 `‹` / `›`
 * —— 光标跑出视野、或者右边还有字却一点提示都没有，都是"说不出来的限制"。
 * 格数按 `text.ts` 那份规矩数（中文双宽），切窗口也按格切：宽字符不许只露一半。
 *
 * 变因：输入行的画法与光标的表现。
 */
import { useTerminalDimensions } from "@opentui/react";
import { cellsOf, clipTail, glyphs, textOf } from "./text.ts";
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface InputBoxProps {
  readonly value: string;
  /** 光标位置（UTF-16 下标，0..value.length；缺省 = 末尾）。光标画在那个字符**前面**。 */
  readonly caret?: number;
  /**
   * 从哪个**显示格**开始画（0 = 最左）。缺省 = 自己保证光标可见（窗口跟着光标走）；
   * 给了就照给的位置画（光标可能因此不在视野里 —— 那是调用方明确要的）。
   */
  readonly offset?: number;
  readonly disabled?: boolean;
  readonly placeholder?: string;
}

/** 光标块。 */
const CARET = "▌";
/** 左边 / 右边还有字时的记号（各占一格）。 */
const MORE_LEFT = "‹";
const MORE_RIGHT = "›";

export function InputBox({ value, caret, offset, disabled = false, placeholder }: InputBoxProps): ReactNode {
  // 末尾留一列：双宽字的第二格落在最后一格时引擎会把这一行画成两行宽（同状态条那条口径）
  const cols = Math.max(1, useTerminalDimensions().width - 1);
  const at = Math.min(Math.max(caret ?? value.length, 0), value.length);
  const cursorColor = disabled ? tone.dim : tone.accent;
  const cursor = <span fg={cursorColor}>{CARET}</span>;

  if (value === "") {
    // 提示语也是"看得见"的一部分：太长就掐到一行以内（记号补 `…`），不许溢出行外把版面推花。
    return (
      <box width="100%" height={1} flexDirection="row" overflow="hidden">
        <text fg={tone.dim} wrapMode="none">
          {clipTail(placeholder ?? "", Math.max(0, cols - 1))}
          {cursor}
        </text>
      </box>
    );
  }

  const all = glyphs(value);
  const caretCell = cellsOf(all.filter((glyph) => glyph.at < at));
  // 窗口起点（格）：缺省把光标留在窗口里（右边留一格给它自己），给了 offset 就听调用方的
  const start = offset === undefined ? Math.max(0, caretCell - (cols - 2)) : Math.max(0, offset);
  const head = start > 0;
  const budget = cols - (head ? 1 : 0);

  // 从左往右吃字符：完全在起点左边的跳过，宽字符要么整格进来要么不进
  let used = 0;
  let from = all.length;
  let to = all.length;
  let cell = 0;
  for (const [index, glyph] of all.entries()) {
    const glyphStart = cell;
    cell += glyph.wide;
    if (glyphStart + glyph.wide <= start || glyphStart < start) continue;
    if (used + glyph.wide > budget) break;
    if (from === all.length) from = index;
    to = index + 1;
    used += glyph.wide;
  }
  let shown = all.slice(from, to);
  // 右边还有字就给它腾一格（从右端往回吐，宽字符整格吐）
  let tail = from + shown.length < all.length;
  while (tail && used + 1 > budget && shown.length > 0) {
    const dropped = shown[shown.length - 1];
    if (dropped === undefined) break;
    shown = shown.slice(0, -1);
    used -= dropped.wide;
  }
  tail = from + shown.length < all.length;

  // 光标落在窗口里哪一段：`at` 之前的字在它左边
  const split = shown.findIndex((glyph) => glyph.at >= at);
  const before = split < 0 ? shown : shown.slice(0, split);
  const after = split < 0 ? [] : shown.slice(split);
  const lastGlyph = shown.at(-1);
  const inside =
    shown.length > 0 && at >= (shown[0]?.at ?? -1) && at <= (lastGlyph === undefined ? -1 : lastGlyph.at + lastGlyph.ch.length);

  return (
    // 一行高、不换行：宽字符窗口最多画到最后一格，多出来的那一格让盒子裁掉，绝不让它折行。
    <box width="100%" height={1} flexDirection="row" overflow="hidden">
      <text fg={disabled ? tone.dim : undefined} wrapMode="none">
        {head ? MORE_LEFT : ""}
        {textOf(before)}
        {inside ? cursor : null}
        {textOf(after)}
        {tail ? MORE_RIGHT : ""}
      </text>
    </box>
  );
}
