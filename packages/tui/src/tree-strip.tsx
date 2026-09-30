/** @jsxImportSource @opentui/react */
/**
 * 树条带：每条线一行（文本由业务给，本包不管血缘）。
 *
 * **没有缩进字段**：缩进已经在 `text` 里了，这里不按层级再补一次（血缘是业务的词）。
 * `offset` 是滚动偏移 —— 从第几条开始画。
 *
 * 变因：树条带的画法与选中表现。
 */
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface TreeStripItem {
  readonly id: string;
  readonly text: string;
  readonly selected: boolean;
  /** 状态标记（在动 / 等人 / 休息 / 出错），由业务算好。 */
  readonly mark?: string;
}

export interface TreeStripProps {
  readonly items: readonly TreeStripItem[];
  readonly offset?: number;
}

export function TreeStrip({ items, offset = 0 }: TreeStripProps): ReactNode {
  return (
    <box flexDirection="column">
      {items.slice(offset).map((item) => (
        <box
          key={item.id}
          flexDirection="row"
          justifyContent="space-between"
          width="100%"
          backgroundColor={item.selected ? tone.selection : undefined}
          // 末尾留一列：右对齐的 mark 是中文时，双宽字会落在行的最后一格上（见 StatusBar 的说明）。
          paddingRight={1}
        >
          {/* 缩进已经在 text 里了，这里不按层级再补。 */}
          <text>{item.text}</text>
          {item.mark === undefined ? null : <text fg={tone.dim}>{item.mark}</text>}
        </box>
      ))}
    </box>
  );
}
