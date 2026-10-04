/**
 * 状态条：选中线的事实 + 用量 + 这会儿能用的键。
 *
 * **不接键**：它只把"现在能用哪些键"写出来（那份字归这里）。
 *
 * 变因：这一区画什么（两行文案）、它要的 props 从哪来。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, Usage } from "@meristem/harness";
import { StatusBar } from "@meristem/tui";
import { memo } from "react";
import type { ReactElement } from "react";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";

/** 状态条两行文案。 */
export function statusText(
  store: LineStore,
  node: NodeId | null,
  jobCount: number,
  usage: Usage | undefined,
  notice: string,
): { readonly left: string; readonly right: string } {
  if (node === null) {
    return { left: notice, right: "enter 说话 · ctrl+c 退出" };
  }
  const facts = store.get(node)?.props;
  const left = [
    facts === undefined ? node : `${facts.name} · ${facts.role} · ${shortPath(facts.outputRoot)}`,
    jobCount > 0 ? `在跑 ${jobCount}` : undefined,
    notice === "" ? undefined : notice,
  ]
    .filter((part) => part !== undefined)
    .join(" · ");
  const keys = ["enter 说话", "ctrl+b 分叉", "tab 作业", jobCount > 0 ? "esc 取消" : undefined, "ctrl+c 退出"].filter(
    (part) => part !== undefined,
  );
  return { left, right: [usageLine(usage), keys.join(" · ")].filter((part) => part !== undefined).join("  ") };
}

/** 一行里放不下整条路径：留住最后一段，省略**看得见**（状态条是给人扫一眼的，不是账）。 */
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

/** 这一片要的 props：两行文案。 */
interface StatusData {
  readonly left: string;
  readonly right: string;
}

/** 读账 + 作业事实 + 用量，算成状态条的两行文案。 */
function useStatus(node: NodeId | null, notice: string): StatusData {
  const { store, tree } = useSession();
  const { usages } = useFacts();
  const jobCount = node === null ? 0 : tree.jobs().filter((job) => job.space === node).length;
  return statusText(store, node, jobCount, node === null ? undefined : usages.get(node), notice);
}

export interface StatusRegionProps {
  readonly node: NodeId | null;
  readonly notice: string;
}

export const StatusRegion = memo(function StatusRegion({ node, notice }: StatusRegionProps): ReactElement {
  const { left, right } = useStatus(node, notice);
  return <StatusBar left={left} right={right} />;
});
