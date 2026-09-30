/**
 * 跟着一个作业的输出走（**原文，不裁剪**）：先给已有的，再给新来的，作业一结束就收。
 *
 * 累积在 ref 里、重画按 `OUTPUT_FRAME_MS` 合成 —— 每来一块就 setState 会把屏幕淹掉，
 * 而拼整段取长度是 O(输出) 的（要长度就问 `Job.produced()`）。
 *
 * `useNow` 是"已跑多久"要走字的钟：有作业在跑时每秒重画一次，没有就不转（界面自己的一秒，与树无关）。
 *
 * 变因：`Job.stream()` 的消费方式与重画节奏。
 */
import { useEffect, useRef, useState } from "react";
import type { Job } from "@meristem/roles";

/** 作业输出可能吐得很密：重画合成到 50ms 一帧，不然一行一个 setState 会把屏幕淹掉。 */
const OUTPUT_FRAME_MS = 50;

export function useJobOutput(job: Job | null): readonly string[] {
  const lines = useRef<string[]>([]);
  const partial = useRef("");
  const pending = useRef(false);
  const [, bump] = useState(0);

  useEffect(() => {
    lines.current = [];
    partial.current = "";
    pending.current = false;
    if (job === null) return;
    let live = true;
    const frame = setInterval(() => {
      if (!pending.current) return;
      pending.current = false;
      bump((tick) => tick + 1);
    }, OUTPUT_FRAME_MS);
    void (async () => {
      for await (const chunk of job.stream()) {
        if (!live) return;
        const parts = (partial.current + chunk).split("\n");
        partial.current = parts.pop() ?? "";
        lines.current.push(...parts);
        pending.current = true;
      }
      pending.current = true;
    })();
    return () => {
      live = false;
      clearInterval(frame);
    };
  }, [job]);

  return partial.current === "" ? lines.current : [...lines.current, partial.current];
}

/** "已跑多久"要走字：有作业在跑时每秒重画一次，没有就不转。 */
export function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return now;
}
