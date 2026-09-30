/** @jsxImportSource @opentui/react */
/**
 * 思考行：一整段可收可展。
 *
 * 收起时只报行数（"思考（N 行）"）—— 本包不判断这段思考该不该收，那是调用方的开关。
 *
 * 变因：思考行的画法。
 */
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface ThoughtLineProps {
  readonly rows: readonly string[];
  readonly open?: boolean;
}

export function ThoughtLine({ rows, open = false }: ThoughtLineProps): ReactNode {
  if (!open) {
    return <text fg={tone.dim}>{`思考（${rows.length} 行）`}</text>;
  }
  return (
    <box flexDirection="column">
      {rows.map((row, index) => (
        <text key={index} fg={tone.dim}>
          {row}
        </text>
      ))}
    </box>
  );
}
