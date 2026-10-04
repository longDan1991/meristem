/**
 * 实时区：这一轮正在吐的**思考**（`ThoughtLine`）＋ 选中的那张**手卡片**（`HandCard`，
 * 输出自己遍历 `Job.stream()`，原文不裁剪）。
 *
 * 卡片游标归它自己：`tab` 在"这条线上在跑的作业"里轮、`esc` 取消选中的那张 —— 它知道
 * 选中的是哪一张，所以只把作业报出去（`onCancel`）。
 *
 * 换了一条线就把游标归零（同消息流的滚动位置，渲染期直接改状态）。
 *
 * 变因：这一区画什么、它要的 props 从哪来、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import type { Job } from "@meristem/roles";
import { useKeys } from "@meristem/tui";
import { memo, useState } from "react";
import type { ReactElement } from "react";
import { useJobOutput, useNow } from "../hooks/job-output.ts";
import { unaccounted } from "../lib/inflight.ts";
import { split } from "../lib/rows.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";
import { HandCard } from "./hand-card.tsx";
import type { HandCardProps } from "./hand-card.tsx";
import { ThoughtLine } from "./thought-line.tsx";

/** 这一片要的 props：正在吐的思考、在跑的作业清单与选中的那一张。 */
interface LiveData {
  /** 这一轮正在吐的思考。 */
  readonly thoughts: readonly string[];
  /** 这条线上在跑的作业数（`tab` 在它们中间轮）。 */
  readonly jobCount: number;
  /** 选中的那一个（`esc` 取消它）；没有在跑的作业时 `null`。 */
  readonly current: Job | null;
  /** 那张卡片的 props；没有在跑的作业时 `null`。 */
  readonly card: Omit<HandCardProps, "state"> | null;
}

/** 读账 + 正在吐的字 + 作业事实，算成这一片要的思考与卡片。 */
function useLive(node: NodeId | null, jobCursor: number): LiveData {
  const { store, tree } = useSession();
  const { hands } = useFacts();
  const tail = useTail();
  const jobs = node === null ? [] : tree.jobs().filter((job) => job.space === node);
  const current = jobs[Math.min(jobCursor, jobs.length - 1)] ?? null;
  const output = useJobOutput(current);
  const now = useNow(current !== null);
  const live = node === null ? null : unaccounted(store, node, tail);
  const card =
    current === null
      ? null
      : {
          name: current.name,
          args: hands.get(current.id)?.args,
          output,
          secs: (now - current.at) / 1000,
        };
  return { thoughts: split(live?.thought ?? "", "thought").map((row) => row.text), jobCount: jobs.length, current, card };
}

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
      if (jobCount === 0) return false;
      setJobCursor((cursor) => (cursor + 1) % jobCount);
      return true;
    }
    if (key === "escape") {
      if (current === null) return false;
      onCancel(current.id, current.name);
      return true;
    }
    return false;
  });

  return (
    <>
      {thoughts.length > 0 ? <ThoughtLine rows={thoughts} open /> : null}
      {card === null ? null : <HandCard {...card} state="running" />}
    </>
  );
});
