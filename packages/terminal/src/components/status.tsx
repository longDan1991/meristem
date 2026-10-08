/** @jsxImportSource @opentui/react */
/**
 * 主屏自带的三条字行：**状态行** · **事实行** · **键行**（整屏最底）。
 *
 * 切法只有一条：这一行写的东西**跟着谁走** —— 三条都只在"哪一屏"这件事上分家：状态行与事实行跟着
 * **我站着的那条线**，键行跟着**眼前这一层**。三条都由那一屏自己画（P0 §3）；零件不自己去取状态，
 * 要什么由主屏以 props 递下来（状态行与事实行吃 `LineProps`，键行只要命令表与总线）。
 *
 * 三条行都是终端的**一条行**：宽度不够时由 `StatusBar` 掐尾巴补 `…`（不许换行、不许两端撞上）。
 *
 * 变因：三条行各写什么（字段与文案）、各自从哪取事实。
 */
import { stringWidth } from "bun";
import type { NodeId } from "@meristem/atree";
import type { Usage } from "@meristem/harness";
import type { Job } from "@meristem/roles";
import { StatusBar, useBus, useCommands } from "@meristem/tui";
import { useTerminalDimensions } from "@opentui/react";
import { memo } from "react";
import type { ReactNode } from "react";
import { useNow } from "../hooks/job-output.ts";
import { keyHints } from "../lib/hints.ts";
import { unaccounted } from "../lib/inflight.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";

/** 状态行与事实行要的东西：我站着的那条线 + 上一动作的回执（都由主屏递下来）。 */
export interface LineProps {
  readonly selected: NodeId | null;
  readonly notice: string;
}

/** 状态行：手上在跑的那一手 / 正在吐字 / 树在休息，外加**上一动作的回执**。 */
export const StatusLine = memo(function StatusLine({ selected, notice }: LineProps): ReactNode {
  const { store, tree } = useSession();
  const tail = useTail();
  const jobs = selected === null ? [] : tree.jobs().filter((job) => job.space === selected);
  const now = useNow(jobs.length > 0);
  const live = selected === null ? null : unaccounted(store, selected, tail);
  // 还没有线（P0 故事 1 的第一次打开）→ 这一行整条不出现：那会儿没有"正在发生的事"可说。
  if (selected === null) return null;
  const left = [activityOf(jobs, live !== null, now), notice === "" ? undefined : notice]
    .filter((part) => part !== undefined)
    .join(" · ");
  return <StatusBar left={left} right={jobs.length > 1 ? `在跑 ${jobs.length}` : undefined} />;
});

function activityOf(jobs: readonly Job[], streaming: boolean, now: number): string {
  const running = jobs[0];
  if (running === undefined) return streaming ? "正在吐字" : "树在休息";
  const rest = jobs.length > 1 ? `（还有 ${jobs.length - 1} 个）` : "";
  return `作业 #${running.id} ${running.name} 已跑 ${((now - running.at) / 1000).toFixed(1)}s${rest}`;
}

/** 事实行：名字 · 角色 · 目录 ｜ 用掉多少 —— **四样都跟着我站着的那条线走**。 */
export const FactLine = memo(function FactLine({ selected, notice }: LineProps): ReactNode {
  const { store } = useSession();
  const { usages } = useFacts();
  const cols = useTerminalDimensions().width;
  // 还没有线、也没有回执要说 → 这一行不出现（第一次打开就是留白 + 输入行 + 键行，P0 故事 1）。
  if (selected === null && notice === "") return null;
  if (selected === null) {
    return <StatusBar left={notice} right={undefined} />;
  }
  const line = store.get(selected)?.props;
  const left = line === undefined ? selected : `${line.name} · ${line.role} · ${shortPath(line.outputRoot)}`;
  return <StatusBar left={left} right={fits(left, usageLine(usages.get(selected)), cols)} />;
});

/** 键行：**这会儿能按什么**（P0 §7 规则 7 的唯一出口）—— 跟着眼前这一层走，所以每一屏自带一条。 */
export const KeyLine = memo(function KeyLine(): ReactNode {
  const bus = useBus();
  const table = useCommands();
  const cols = useTerminalDimensions().width;
  return <StatusBar left="" right={keyHints(table, bus, Math.max(0, cols - 1))} />;
});

/** 事实行左端"我在哪条线"至少留这么多格（右端的用量不许把它挤没）。 */
const MIN_LEFT = 24;

/** 事实行右端：用量放不下就**整个撤掉** —— 左端那个名字比用量重要。 */
function fits(left: string, right: string | undefined, cols: number): string | undefined {
  if (right === undefined) return undefined;
  const usable = Math.max(0, cols - 1);
  const reserved = Math.min(stringWidth(left), MIN_LEFT) + 1;
  return stringWidth(right) + 2 <= usable - reserved ? right : undefined;
}

/** 一行里放不下整条路径：留住最后一段，省略**看得见**（这一行是给人扫一眼的，不是账）。 */
function shortPath(path: string): string {
  const parts = path.split("/").filter((part) => part !== "");
  const tail = parts.at(-1) ?? path;
  return path.length <= 24 || parts.length <= 1 ? path : `…/${tail}`;
}

function usageLine(usage: Usage | undefined): string | undefined {
  if (usage === undefined) return undefined;
  return `↑${tokens(usage.prompt)} ↓${tokens(usage.completion)}（思考 ${tokens(usage.reasoning)} / 缓存 ${tokens(usage.cached)}）`;
}

function tokens(count: number): string {
  return count < 1000 ? String(count) : `${(count / 1000).toFixed(1)}k`;
}
