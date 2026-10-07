/** @jsxImportSource @opentui/react */
/**
 * 名单：一行 = 文本 + 右端记号 + 选中底色（内容由业务给，本包不认识血缘、命令或角色）。
 *
 * 四处都用它，所以它在这儿：内容区的树（档 ②/③）、敲 `/` 弹出的命令名单、挑角色/挑模型的名单、
 * 键位表（`/help`）—— 都是"一列行、一行选中、右端挂个记号"。
 *
 * **为什么不用 opentui 自带的 `<select>`**：它要**焦点**才吃 ↑↓/enter，而这一屏的焦点永远在输入行
 * （打字是唯一的文字入口，`docs/prototype/ours/P0/06-switching.md` 纪律②：面板不许吞普通打字）；
 * 而且那个焦点会被输入行抢回来（输入区盯着 `FOCUSED_RENDERABLE`）。所以这里只画，
 * 键归谁由命令表说（`command/`）。
 *
 * **没有缩进字段**：缩进已经在 `text` 里了，这里不按层级再补一次（血缘是业务的词）。
 * **没有滚动偏移**：铺几行由调用方决定（窗口是业务的），滚动归外面的滚动盒。
 *
 * 变因：这份名单的画法与选中表现。
 */
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

export interface RowListItem {
  /** 这一行的身份（React 的 key）：同一份名单里不许重复 —— 折起来的那些行也要各是各的。 */
  readonly key: string;
  readonly text: string;
  readonly selected: boolean;
  /** 状态标记（在动 / 出错 / 键位 / 当前那一个），由业务算好。 */
  readonly mark?: string;
  /** 次要的一行（比如选中那条就地展开的实况）：压一级明度，不抢主行的注意力。 */
  readonly muted?: boolean;
}

export interface RowListProps {
  readonly items: readonly RowListItem[];
}

export function RowList({ items }: RowListProps): ReactNode {
  return (
    <box flexDirection="column">
      {items.map((item) => (
        <box
          key={item.key}
          flexDirection="row"
          justifyContent="space-between"
          width="100%"
          backgroundColor={item.selected ? tone.selection : undefined}
          // 末尾留一列：右对齐的 mark 是中文时，双宽字会落在行的最后一格上（见 StatusBar 的说明）。
          paddingRight={1}
        >
          {/* 缩进已经在 text 里了，这里不按层级再补。 */}
          <text fg={item.muted === true ? tone.dim : undefined}>{item.text}</text>
          {item.mark === undefined ? null : <text fg={tone.dim}>{item.mark}</text>}
        </box>
      ))}
    </box>
  );
}
