/** @jsxImportSource @opentui/react */
/**
 * 一只手的卡片：名字 + 参数 + 输出 + 状态，外面一个边框盒子。
 *
 * 输出**原文照铺**（不裁剪、不折叠）：长输出靠外层滚动容纳，卡片自己不改内容。
 * 失败不单独分类（它是交代里的一段文本，DESIGN §9.3），所以卡片按状态画两态就够。
 *
 * 变因：手卡片的画法与状态词。
 */
import { TextAttributes } from "@opentui/core";
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

/**
 * 手卡片的**视觉态**：在跑 / 已结束。失败不在这里 —— 我们不分类失败（它是交代里的一段文本，
 * DESIGN §9.3），所以卡片按"已结束"画，字里看得出是怎么回事。
 */
export type HandState = "running" | "done";

export interface HandCardProps {
  readonly name: string;
  readonly args?: string;
  readonly output?: readonly string[];
  readonly state: HandState;
  readonly secs?: number;
}

function stateText(state: HandState, secs: number | undefined): string {
  const spent = secs === undefined ? "" : ` ${secs.toFixed(1)}s`;
  return state === "running" ? `已跑${spent}` : `已结束${spent}`;
}

export function HandCard({ name, args, output, state, secs }: HandCardProps): ReactNode {
  return (
    <box border borderStyle="single" borderColor={tone.border} flexDirection="column" paddingX={1}>
      <box flexDirection="row" gap={1}>
        <text fg={tone.accent} attributes={TextAttributes.BOLD}>
          {name}
        </text>
        {args === undefined || args === "" ? null : <text fg={tone.dim}>{args}</text>}
        <text fg={state === "running" ? tone.running : tone.dim}>{stateText(state, secs)}</text>
      </box>
      {(output ?? []).map((line, index) => (
        <text key={index}>{line}</text>
      ))}
    </box>
  );
}
