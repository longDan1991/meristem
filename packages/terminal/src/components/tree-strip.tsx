/**
 * 树条带：每条线一行（人写的名字 + 角色 + 在跑的记号 + 接口失败），`↑` / `↓` 切节点、`ctrl+t` 重试。
 *
 * 它是**列表控件**，所以箭头键归它自己：可选清单在它手里（`useStrip`），"下一个是谁"它自己算，
 * 只把结果报给店主（`onSelect`）。`ctrl+t`（重试选中的线）也归它 —— 那条线的接口失败正是画在
 * 这一片上的红字。
 *
 * 变因：这一区画什么、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import { TreeStrip, useKeys } from "@meristem/tui";
import { memo } from "react";
import type { ReactElement } from "react";
import { useStrip } from "../hooks/selectors.ts";

export interface TreeStripRegionProps {
  readonly selected: NodeId | null;
  readonly onSelect: (node: NodeId | null) => void;
  /** `ctrl+t`：把选中的线放回推进（只对"模型接口失败"有效）。 */
  readonly onRetry: () => void;
}

export const TreeStripRegion = memo(function TreeStripRegion({
  selected,
  onSelect,
  onRetry,
}: TreeStripRegionProps): ReactElement {
  const { items, selectable } = useStrip(selected);

  useKeys((key) => {
    if (key === "up" || key === "down") {
      if (selectable.length === 0) return;
      const delta = key === "up" ? -1 : 1;
      const at = selected === null ? -1 : selectable.indexOf(selected);
      const next =
        at < 0 ? (delta > 0 ? 0 : selectable.length - 1) : Math.min(Math.max(at + delta, 0), selectable.length - 1);
      onSelect(selectable[next] ?? null);
      return;
    }
    if (key === "ctrl+t") onRetry();
  });

  return <TreeStrip items={items} />;
});
