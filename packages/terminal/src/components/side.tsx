/** @jsxImportSource @opentui/react */
/**
 * 侧边：主屏右侧那一列（三态由**主屏**定：收起 0 列 / 分成两栏 / 占满全屏），里面按**页**轮换。
 *
 * **它属于主屏**（P0 §2.2：主屏的细节就是"它里面的内容区 + 侧边"）：摆它、切态、切页都是那一屏自己的事
 * （`screens/main.tsx`），别的屏没有这一列。
 *
 * **页表在 `lib/side.ts`**（只列有数据来源的那五页）：画它的是这一栏，换页那条命令由主屏按它绕圈
 * —— 页数只写一处，不然会出现"转到第 6 页但只有 5 页"。
 *
 * **每页的内部还没定**（那是 `P0/08-handoff.md` 说的"下一份接着定"里的事）：所以这里只写
 * "这一页是什么、数据从哪来"，不编内容。这一栏现在的作用是**把位置与轮换立起来**：
 * 正文让位多少、壳动不动、一个键怎么在三态与五页之间走 —— 这些是骨架，页里的东西是下一份。
 * **怎么切态切页不在这儿写**：那是命令表的事，键行与本页的键提示已经在说（同一件事不说两遍）。
 *
 * 变因：侧边这一栏怎么画（有哪些页在 `lib/side.ts`）。
 */
import { tone } from "@meristem/tui";
import type { ReactNode } from "react";
import { SIDE_PAGES } from "../lib/side.ts";

export interface SidePanelProps {
  /** 第几页（0 起）。 */
  readonly page: number;
}

export function SidePanel({ page }: SidePanelProps): ReactNode {
  const at = page % SIDE_PAGES.length;
  const current = SIDE_PAGES[at];
  if (current === undefined) return null;
  return (
    <box
      flexDirection="column"
      width="100%"
      height="100%"
      border
      borderStyle="single"
      borderColor={tone.border}
      paddingX={1}
    >
      <box flexDirection="row" justifyContent="space-between" width="100%">
        <text fg={tone.accent}>{current.title}</text>
        <text fg={tone.dim}>{`${at + 1}/${SIDE_PAGES.length}`}</text>
      </box>
      <text fg={tone.dim}>{current.note}</text>
      <text fg={tone.dim}>这一页的内部还没定（下一份接着定）</text>
    </box>
  );
}
