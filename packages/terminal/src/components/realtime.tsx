/** @jsxImportSource @opentui/react */
/**
 * 实时区：这一轮正在吐的**思考**（`ThoughtLine`）＋**在跑的每一手各一张卡片**（`HandCard`，
 * 输出自己遍历 `Job.stream()`，原文不裁剪）。
 *
 * **这一片不接键**：卡片游标那个概念没有了（`tab` 换卡片是旧实现的残留，命令表里没有这条命令）。
 * 在跑的每一手都画出来 —— 有 N 手就是 N 张卡片，"手上还有几件活"从卡片的数量上一眼看得出，
 * 不用再记一个游标。取消归 `esc`（命令表里的 `app.close` → 收掉眼前这一层，落到最底层时取消
 * 选中的那条线上在跑的那一手），所以这里也不再管 `esc`。
 *
 * 卡片长在**内容区末尾**（对话的下方）：它还没进账，是"正在发生"的那一段（P0 故事 3）。
 *
 * 变因：这一区画什么（思考与在跑的卡片）。
 */
import type { NodeId } from "@meristem/atree";
import type { Job } from "@meristem/roles";
import { memo } from "react";
import type { ReactNode } from "react";
import { useJobOutput, useNow } from "../hooks/job-output.ts";
import { unaccounted } from "../lib/inflight.ts";
import { split } from "../lib/rows.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";
import { HandCard } from "./hand-card.tsx";
import { ThoughtLine } from "./thought-line.tsx";

export interface LiveRegionProps {
  readonly node: NodeId | null;
}

export const LiveRegion = memo(function LiveRegion({ node }: LiveRegionProps): ReactNode {
  const { store, tree } = useSession();
  const tail = useTail();
  if (node === null) return null;
  const live = unaccounted(store, node, tail);
  const thoughts = split(live?.thought ?? "", "thought").map((row) => row.text);
  const jobs = tree.jobs().filter((job) => job.space === node);
  return (
    <>
      {thoughts.length > 0 ? <ThoughtLine rows={thoughts} open /> : null}
      {jobs.map((job) => (
        <RunningCard key={job.id} job={job} />
      ))}
    </>
  );
});

/** 一张在跑的卡片：它吐出来的原文，一直长（不裁剪、不折叠）。 */
function RunningCard({ job }: { readonly job: Job }): ReactNode {
  const { hands } = useFacts();
  const output = useJobOutput(job);
  const now = useNow(true);
  return (
    <HandCard
      name={job.name}
      args={hands.get(job.id)?.args}
      output={output}
      secs={(now - job.at) / 1000}
      state="running"
    />
  );
}
