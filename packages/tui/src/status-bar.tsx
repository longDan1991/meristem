/** @jsxImportSource @opentui/react */
/**
 * 状态条：整行一条，**永远只占一行、两端不重叠**。
 *
 * 两端靠引擎摆（`flexDirection="row"` + `justifyContent="space-between"`），不再自己补空格。
 * 但**放不下时掐哪头仍然要自己算**：这条本来就是屏幕级的带子（整行两端对齐、右端贴着屏幕右边），
 * 而"我看得出来这句话被掐了"靠的是 `…` —— 引擎自带的裁切是无声的，所以宽度得先知道（问终端尺寸）。
 *
 * 掐的是尾巴并补 `…`：左串开头是"这条线叫什么"、右串开头是用量，都是更该留住的一头；
 * 左串挤到没地方就整段不画。中文是双宽，格数用 `stringWidth` 数 —— 拿字符串长度凑会歪。
 *
 * 变因：状态条的画法与"放不下时留哪一头"。
 */
import { stringWidth } from "bun";
import { useTerminalDimensions } from "@opentui/react";
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface StatusBarProps {
  readonly left?: string;
  readonly right?: string;
}

/** 掐尾巴：放不下就裁到 `budget` 格以内并补省略号（`budget <= 0` = 整段不画）。 */
function clipTail(text: string, budget: number): string {
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

export function StatusBar({ left, right }: StatusBarProps): ReactNode {
  // 末尾留一列：双宽字的第二格落在最后一格时，引擎会把这一行画成两行宽（实测：20 格的行画成
  // 40 格），后面的行跟着串位。右对齐的中文正好会压在那儿，所以宁可少用一列。
  const cols = Math.max(0, useTerminalDimensions().width - 1);
  const rightText = clipTail(right ?? "", cols);
  // 两头之间至少空一列。
  const leftText = clipTail(left ?? "", cols - stringWidth(rightText) - 1);
  return (
    <box
      width="100%"
      height={1}
      flexDirection="row"
      justifyContent="space-between"
      overflow="hidden"
      backgroundColor={tone.status}
    >
      <text wrapMode="none">{leftText}</text>
      <text wrapMode="none" fg={tone.dim}>
        {rightText}
      </text>
    </box>
  );
}
