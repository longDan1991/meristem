/** @jsxImportSource @opentui/react */
/**
 * 思考行：一整段可收可展。
 *
 * 它住 terminal 而不是 tui：**"思考"这个词本身**（连"它该不该收"）都是这一屏的语义，
 * 通用件里没有这个概念。
 *
 * 收起时只报行数（"思考（N 行）"）—— 本组件不判断这段思考该不该收，那是调用方的开关。
 *
 * 变因：思考行的画法。
 */
import { tone } from "@meristem/tui";
import type { ReactNode } from "react";

export interface ThoughtLineProps {
  readonly rows: readonly string[];
  readonly open?: boolean;
}

export function ThoughtLine({ rows, open = false }: ThoughtLineProps): ReactNode {
  if (!open) {
    return <text fg={tone.dim} style={{paddingX:1}}>{`思考（${rows.length} 行）`}</text>;
  }
  return (
    <box flexDirection="column" style={{paddingX:1}}>
      {rows.map((row, index) => (
        <text key={index} fg={tone.dim} wrapMode="char">
          {row}
        </text>
      ))}
    </box>
  );
}
