/**
 * 消息流：选中那条线的账（人 / 模型 / 思考 / 手的过程）＋ 末尾"正在吐、还没进账"的字。
 *
 * **看的位置归它自己**：`ctrl+o` 展开 / 收起账里的思考，`alt+↑↓` 走一行、`pageup` / `pagedown`
 * 走一屏往回看。写者（这几个键）与读者（这一片）都在这里，所以是两个普通 `useState`。
 *
 * 换了一条线就把滚动位置归零（渲染期直接改状态，免得先按旧位置画一帧再跳回来）。
 *
 * 变因：这一区画什么、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import { MessageStream, useKeys } from "@meristem/tui";
import { memo, useState } from "react";
import type { ReactElement } from "react";
import { useStream } from "../hooks/selectors.ts";

export interface StreamRegionProps {
  readonly node: NodeId | null;
}

/** 一屏滚多少行（`pageup` / `pagedown`）。 */
const SCROLL_STEP = 10;

export const StreamRegion = memo(function StreamRegion({ node }: StreamRegionProps): ReactElement {
  const [thoughtsOpen, setThoughtsOpen] = useState(false);
  const [scrollBack, setScrollBack] = useState(0);
  const [viewed, setViewed] = useState(node);
  if (viewed !== node) {
    setViewed(node);
    setScrollBack(0);
  }

  const { rows, follow, offset } = useStream(node, thoughtsOpen, scrollBack);

  useKeys((key) => {
    if (key === "ctrl+o") {
      setThoughtsOpen((open) => !open);
      return;
    }
    if (key === "alt+up" || key === "pageup") {
      setScrollBack((back) => back + (key === "pageup" ? SCROLL_STEP : 1));
      return;
    }
    if (key === "alt+down" || key === "pagedown") {
      setScrollBack((back) => Math.max(0, back - (key === "pagedown" ? SCROLL_STEP : 1)));
    }
  });

  return <MessageStream rows={rows} follow={follow} offset={offset} />;
});
