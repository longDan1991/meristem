/**
 * 实时区：这一轮正在吐的**思考**（`ThoughtLine`）＋ 选中的那张**手卡片**（`HandCard`，
 * 输出自己遍历 `Job.stream()`，原文不裁剪）。
 *
 * 卡片游标归它自己：`tab` 在"这条线上在跑的作业"里轮、`esc` 取消选中的那张 —— 它知道
 * 选中的是哪一张，所以只把作业报出去（`onCancel`）。
 *
 * 换了一条线就把游标归零（同消息流的滚动位置，渲染期直接改状态）。
 *
 * 变因：这一区画什么、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import { HandCard, ThoughtLine, useKeys } from "@meristem/tui";
import { memo, useState } from "react";
import type { ReactElement } from "react";
import { useLive } from "../hooks/selectors.ts";

export interface LiveRegionProps {
  readonly node: NodeId | null;
  /** `esc`：取消这张卡片代表的作业。 */
  readonly onCancel: (job: string, name: string) => void;
}

export const LiveRegion = memo(function LiveRegion({ node, onCancel }: LiveRegionProps): ReactElement {
  const [jobCursor, setJobCursor] = useState(0);
  const [viewed, setViewed] = useState(node);
  if (viewed !== node) {
    setViewed(node);
    setJobCursor(0);
  }

  const { thoughts, jobCount, current, card } = useLive(node, jobCursor);

  useKeys((key) => {
    if (key === "tab") {
      if (jobCount > 0) setJobCursor((cursor) => (cursor + 1) % jobCount);
      return;
    }
    if (key === "escape" && current !== null) onCancel(current.id, current.name);
  });

  return (
    <>
      {thoughts.length > 0 ? <ThoughtLine rows={thoughts} open /> : null}
      {card === null ? null : <HandCard {...card} state="running" />}
    </>
  );
});
