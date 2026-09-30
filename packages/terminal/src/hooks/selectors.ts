/**
 * 派生渲染数据：**唯一认识 tui 类型的一层** —— 把账、状态、事件算成组件要的 props。
 *
 * 这里只读不写、只拼结构不编语义：行从 `view.ts` 的纯函数来，这里只做
 * `Row → MessageLine` / `TreeRow → TreeStripItem` 的适配与窗口切片（样式词见 `style.ts`）。
 *
 * 参数从外面给（`selected` 与各区自己的视图位置都归各自的区持有），所以这一层只额外吃三片共享的：
 *   · `useStrip`  ← Session + Facts（作业表每变一次，`hands` 就变一次 —— 那也是这一片的重渲染信号）
 *   · `useStream` ← Session + Tail（账 + 正在吐的字）
 *   · `useLive`   ← Session + Tail + Facts + `job-output`
 *   · `useStatus` ← Session + Facts
 *
 * 变因：派生规则（哪些输入算成哪个区的 props）。
 */
import type { NodeId } from "@meristem/atree";
import type { Job } from "@meristem/roles";
import type { HandCardProps, MessageLine, TreeStripItem } from "@meristem/tui";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";
import { toLine } from "../style.ts";
import { STRIP_ROWS, foldThoughts, lineRows, placeholder, split, statusText, treeRows, treeWindow, unaccounted } from "../view.ts";
import { useJobOutput, useNow } from "./job-output.ts";

export interface StripData {
  readonly items: readonly TreeStripItem[];
  /** ↑/↓ 走的那份（与 `items` 出自同一次 `view.treeRows`，折叠语义一致）。 */
  readonly selectable: readonly NodeId[];
}

export function useStrip(selected: NodeId | null): StripData {
  const { store, tree } = useSession();
  const { errors } = useFacts();
  const rows = treeRows(store, selected, tree.jobs());
  const { window, selectable } = treeWindow(rows, STRIP_ROWS);
  const items = window.map((row) => {
    const failure = row.id === null ? undefined : errors.get(row.id);
    const mark = [row.mark, failure === undefined ? undefined : "✗ 接口失败"].filter((part) => part !== undefined).join(" ");
    return { id: row.id ?? "", text: row.text, selected: row.selected, mark: mark === "" ? undefined : mark };
  });
  return { items, selectable };
}

export interface StreamData {
  readonly rows: readonly MessageLine[];
  /** 贴着末尾（`scrollBack === 0`）。 */
  readonly follow: boolean;
  readonly offset: number;
}

export function useStream(node: NodeId | null, thoughtsOpen: boolean, scrollBack: number): StreamData {
  const { store } = useSession();
  const tail = useTail();
  const follow = scrollBack === 0;
  if (node === null) return { rows: [], follow, offset: scrollBack };
  // 账里的行（思考可按 ctrl+o 收起）＋ 正在吐的正文（思考单独在实时区画，不重复）
  const account = lineRows(store, node, []);
  const live = unaccounted(store, node, tail);
  const rows: readonly MessageLine[] = [
    ...(thoughtsOpen ? account : foldThoughts(account)).map(toLine),
    ...split(live?.text ?? "", "model").map(toLine),
  ];
  return { rows, follow, offset: scrollBack };
}

export interface LiveData {
  /** 这一轮正在吐的思考。 */
  readonly thoughts: readonly string[];
  /** 这条线上在跑的作业数（`tab` 在它们中间轮）。 */
  readonly jobCount: number;
  /** 选中的那一个（`esc` 取消它）；没有在跑的作业时 `null`。 */
  readonly current: Job | null;
  /** 那张卡片的 props；没有在跑的作业时 `null`。 */
  readonly card: Omit<HandCardProps, "state"> | null;
}

export function useLive(node: NodeId | null, jobCursor: number): LiveData {
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

export interface StatusData {
  readonly left: string;
  readonly right: string;
}

export function useStatus(node: NodeId | null, notice: string): StatusData {
  const { store, tree } = useSession();
  const { usages } = useFacts();
  const jobCount = node === null ? 0 : tree.jobs().filter((job) => job.space === node).length;
  return statusText(store, node, jobCount, node === null ? undefined : usages.get(node), notice);
}

export function usePlaceholder(node: NodeId | null): string {
  const { store } = useSession();
  return placeholder(node, store.root());
}
