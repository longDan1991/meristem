/**
 * 状态条：选中线的事实 + 用量 + 这会儿能用的键。
 *
 * **不接键**：它只把"现在能用哪些键"写出来（那份字归 `view.ts`）。
 *
 * 变因：这一区画什么。
 */
import type { NodeId } from "@meristem/atree";
import { StatusBar } from "@meristem/tui";
import { memo } from "react";
import type { ReactElement } from "react";
import { useStatus } from "../hooks/selectors.ts";

export interface StatusRegionProps {
  readonly node: NodeId | null;
  readonly notice: string;
}

export const StatusRegion = memo(function StatusRegion({ node, notice }: StatusRegionProps): ReactElement {
  const { left, right } = useStatus(node, notice);
  return <StatusBar left={left} right={right} />;
});
