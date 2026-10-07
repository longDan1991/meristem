/** @jsxImportSource @opentui/react */
/**
 * 壳上的两条字行：**状态行**（输入行上方）与**底下那行**（整屏最底）。
 *
 * **状态行 = 眼前这一件正在发生的事**（照 jcode 的"活动行"、omp 的"工作行"）：手上在跑的那一手
 * （作业 id、手名、已跑多久）／正在吐字／树在休息，外加**上一动作的回执**（它也得看得见 —— 底下那行
 * 的左端是"我在哪条线"，再挂一句话就会把名字挤掉）。它不属于任何一档、任何一屏 —— 壳不动。
 *
 * **底下那行 = 事实**：左端"我在哪条线、穿哪个角色、在哪做事"（名字只在两处出现：这里与树行上），
 * 右端"用了多少、这会儿能按什么"。**能用的键只有这一个出口**（P0 §7 规则 7），而那份键是从命令表 +
 * 总线**问出来**的（有接的人才写）——不是这里再手写一张。
 *
 * 两条行都是终端的**一条行**：宽度不够时由 `StatusBar` 掐尾巴补 `…`（不许换行、不许两端撞上）。
 *
 * 变因：两条行各写什么（字段与文案），以及从哪取事实。
 */
import { stringWidth } from "bun";
import type { Usage } from "@meristem/harness";
import type { Job } from "@meristem/roles";
import { StatusBar, useCommandBus, useCommands } from "@meristem/tui";
import type { CommandBus, Commands } from "@meristem/tui";
import { useTerminalDimensions } from "@opentui/react";
import { memo } from "react";
import type { ReactNode } from "react";
import { useNow } from "../hooks/job-output.ts";
import { keyHints } from "../lib/hints.ts";
import { unaccounted } from "../lib/inflight.ts";
import { useFacts } from "../providers/facts.tsx";
import { useScreen } from "../providers/screen.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";

/** 状态行：手上在跑的那一手 / 正在吐字 / 树在休息，外加**上一动作的回执**。 */
export const StatusLine = memo(function StatusLine(): ReactNode {
  const { store, tree } = useSession();
  const screen = useScreen();
  const tail = useTail();
  const { selected, notice } = screen;
  const jobs = selected === null ? [] : tree.jobs().filter((job) => job.space === selected);
  const now = useNow(jobs.length > 0);
  const live = selected === null ? null : unaccounted(store, selected, tail);
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

/** 底下那行：名字 · 角色 · 目录 ｜ 用量 + 能用的键。 */
export const BottomLine = memo(function BottomLine(): ReactNode {
  const { store } = useSession();
  const { usages } = useFacts();
  const screen = useScreen();
  const bus = useCommandBus();
  const table = useCommands();
  const cols = useTerminalDimensions().width;
  const { selected, notice } = screen;
  if (selected === null) {
    return <StatusBar left={notice} right={rightOf(table, notice, cols, undefined, bus)} />;
  }
  const line = store.get(selected)?.props;
  const left = line === undefined ? selected : `${line.name} · ${line.role} · ${shortPath(line.outputRoot)}`;
  return <StatusBar left={left} right={rightOf(table, left, cols, usageLine(usages.get(selected)), bus)} />;
});

/** 左端"我在哪条线"至少留这么多格（右端的用量与键提示不许把它挤没）。 */
const MIN_LEFT = 24;

/** 右端那串：用量 + 键提示，且**先给左端留够格数**。 */
function rightOf(
  table: Commands,
  left: string,
  cols: number,
  usage: string | undefined,
  bus: CommandBus,
): string {
  const usable = Math.max(0, cols - 1);
  const reserved = Math.min(stringWidth(left), MIN_LEFT) + 1;
  const used = usage === undefined ? 0 : stringWidth(usage) + 2;
  const hints = keyHints(table, bus, Math.max(0, usable - reserved - used));
  return [usage, hints].filter((part) => part !== undefined && part !== "").join("  ");
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
