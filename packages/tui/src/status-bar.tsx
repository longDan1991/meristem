/** @jsxImportSource @opentui/react */
/**
 * 状态条：整行一条，**永远只占一行、两端不重叠**。
 *
 * 要对齐就得知道格数，格数用 `stringWidth` 数 —— 中文是双宽，拿字符串长度凑会歪。
 * 宽度取屏幕宽度：这个条本来就是屏幕级的带子（接口里没有宽度字段，量容器又会引入状态与重画）。
 * 放不下时掐哪头是定死的：左串开头是"这条线叫什么"、右串开头是用量，都是更该留住的一头，
 * 所以两头都掐尾巴并补 `…`（限制必须看得见）；左串挤到没地方就整段不画。
 *
 * 变因：状态条的画法与"放不下时留哪一头"。
 */
import { stringWidth } from "bun";
import { useTerminalDimensions } from "@opentui/react";
import { clipTail } from "./text.ts";
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface StatusBarProps {
  readonly left?: string;
  readonly right?: string;
}

export function StatusBar({ left, right }: StatusBarProps): ReactNode {
  // 末尾留一列：双宽字的第二格落在最后一格时，引擎会把这一行画成两行宽（实测：20 格的行画成
  // 40 格），后面的行跟着串位。右对齐的中文正好会压在那儿，所以宁可少用一列。
  const cols = Math.max(0, useTerminalDimensions().width - 1);
  const rightText = clipTail(right ?? "", cols);
  // 两头之间至少空一列。
  const leftText = clipTail(left ?? "", cols - stringWidth(rightText) - 1);
  const pad = " ".repeat(Math.max(0, cols - stringWidth(leftText) - stringWidth(rightText)));
  return (
    <box width="100%" height={1} flexDirection="row" overflow="hidden" backgroundColor={tone.status}>
      <text wrapMode="none">
        {leftText}
        <span fg={tone.dim}>{pad + rightText}</span>
      </text>
    </box>
  );
}
