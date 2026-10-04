/**
 * 树条带：每条线一行（人写的名字 + 角色 + 在跑的记号 + 接口失败），`↑` / `↓` 切节点、`ctrl+t` 重试。
 *
 * 它是**列表控件**，所以箭头键归它自己：可选清单在它手里（`useStrip`），"下一个是谁"它自己算，
 * 只把结果报给店主（`onSelect`）。`ctrl+t`（重试选中的线）也归它 —— 那条线的接口失败正是画在
 * 这一片上的红字。
 *
 * **这一区的展示规则也归这里**：树怎么折（`treeRows`）、窗口怎么切（`treeWindow`）—— 纯函数，
 * 只服务这一片。
 *
 * 变因：这一区画什么（折树规则、窗口）、它要的 props 从哪来、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore } from "@meristem/harness";
import type { Job } from "@meristem/roles";
import { TreeStrip, useKeys } from "@meristem/tui";
import type { TreeStripItem } from "@meristem/tui";
import { memo } from "react";
import type { ReactElement } from "react";
import { FOLD } from "../lib/rows.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";

/** 一层的缩进与两种记号（展示的字面量只在这里定一份）。 */
const INDENT = "  ";
const MARK = "▶ ";

/**
 * 树条带的一行。`id === null` 表示这一行是被折起来的子树（不可选中）。
 *
 * `key` 与 `id` 分开：折起来的那些行没有节点（`id === null`），但**每一行都得有自己的身份**
 * （React 按它认"还是这一行"）—— 一屏里可能有好几行折起来的子树，共用空 key 会串。
 */
export interface TreeRow {
  readonly key: string;
  readonly id: NodeId | null;
  readonly text: string;
  readonly depth: number;
  readonly selected: boolean;
  readonly mark?: string;
}

/**
 * 树条带最多铺几行（选中行永远在窗口里，其余靠折叠与滚动）。
 *
 * **为什么不挂一个 `<scrollbox>` 让它滚**：条带是个**固定高度的窗口**（8 行），"选中那一行在窗口里"
 * 是个纯计算（下面那个 `treeWindow`），什么时候都对、也不依赖排版跑完 —— 而滚动盒把这一行带进视野
 * `scrollChildIntoView()` 得等排版算完才有坐标（挂载那一次调用正好在排版之前，会静默不动）。
 * 8 行的固定窗口用不着滚动盒那一套（滚轮、滚动条、跟随），所以这里自己切窗口。
 * **一页里真正会滚的是外面那个盒**（`app.tsx`）。
 */
export const STRIP_ROWS = 8;

/**
 * 树条带：每条线一行 —— **人写的名字 + 角色**（都在节点的 `props` 里），缩进自己拼进 `text`。
 *
 * 返回 id 而不是纯行，是因为**这是张地图不是一段文字**：界面靠 `id === null` 认出"这一行是被折起来的
 * 子树"（不可选中、不可当选中线），靠 `selected` 认出人现在站在哪。
 *
 * 折的规矩（确定性的：同一份账 + 同一个选中，永远是同一屏）：
 *   · **看得见** = 选中路径（根 → 选中的线，含它自己）+ 选中线的直接子节点 +
 *     **有在跑作业的线与其所有祖先** —— "哪里有活"不许被折掉，那是这张图唯一的机械事实（DESIGN §9.2 的"看"）；
 *   · 其余每个**最大可折子树**在它父节点的位置上占一行 `▸ N 条线`（N 含子树根），`id = null`、不可选中；
 *   · `mark` = 这条线上的在跑作业数（`Job.space` 就是节点 id），没有作业就不设这个字段。
 *
 * `selected === null` 只会出现在空树（连根都还没有）：没有节点 → 空数组。
 */
export function treeRows(
  store: LineStore,
  selected: NodeId | null,
  jobs: readonly Job[],
): readonly TreeRow[] {
  const root = store.root();
  if (root === null) return [];

  // 有在跑作业的空间（就是节点）：Job.space 由树在调用那只手的时候给。
  const busy = new Set<NodeId>();
  for (const job of jobs) busy.add(job.space);

  const visible = new Set<NodeId>([root]);
  // 选中路径：往上走到根为止（走到不存在的节点就停 —— 账里没有的东西不该被当成路径）。
  for (let cursor = selected; cursor !== null; cursor = store.get(cursor)?.parent ?? null) {
    visible.add(cursor);
  }
  // 选中线的直接子节点：分叉的入口得看得见。
  if (selected !== null) for (const kid of store.children(selected)) visible.add(kid);
  // 有活的线连同它的祖先链：折一行会把它整枝藏掉，所以整枝都得撑开。
  for (const space of busy) {
    for (let cursor: NodeId | null = space; cursor !== null; cursor = store.get(cursor)?.parent ?? null) {
      visible.add(cursor);
    }
  }

  // 折起来那行的节点数：一趟逆序累加就够（账的顺序父在子前，所以反着走时子已经算完）——
  // 不让每一帧渲染退化成 O(n²)。
  const size = new Map<NodeId, number>();
  const order = store.nodes();
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const id = order[index];
    if (id === undefined) continue;
    let total = 1;
    for (const kid of store.children(id)) total += size.get(kid) ?? 0;
    size.set(id, total);
  }

  const rows: TreeRow[] = [];
  const walk = (id: NodeId, depth: number): void => {
    const node = store.get(id);
    if (node === null) return;
    const count = busy.has(id) ? jobs.filter((job) => job.space === id).length : 0;
    const base = {
      key: id,
      id,
      text: INDENT.repeat(depth) + node.props.name + " · " + node.props.role,
      depth,
      selected: id === selected,
    };
    rows.push(count === 0 ? base : { ...base, mark: MARK + count });
    for (const kid of store.children(id)) {
      if (visible.has(kid)) walk(kid, depth + 1);
      else {
        // 折起来这行的身份 = "谁的哪一枝"（父 + 子树根）：同一屏里几行折叠各是各的
        const text = INDENT.repeat(depth + 1) + FOLD + (size.get(kid) ?? 1) + " 条线";
        rows.push({ key: `fold:${id}:${kid}`, id: null, text, depth: depth + 1, selected: false });
      }
    }
  };
  walk(root, 0);
  return rows;
}

/** 树条带窗口：只铺 `size` 行、让选中行落在窗口里；`selectable` 是**全部**可选中行（↑/↓ 走它）。 */
export function treeWindow(
  rows: readonly TreeRow[],
  size: number,
): { readonly window: readonly TreeRow[]; readonly selectable: readonly NodeId[] } {
  const at = rows.findIndex((row) => row.selected);
  const start = windowOffset(at, rows.length, size);
  return {
    window: rows.slice(start, start + size),
    selectable: rows.flatMap((row) => (row.id === null ? [] : [row.id])),
  };
}

/** 让选中的那一行落在窗口里（树条带只铺 `size` 行）。 */
function windowOffset(at: number, total: number, size: number): number {
  if (total <= size || at < 0) return 0;
  const half = Math.floor(size / 2);
  return Math.min(Math.max(at - half, 0), total - size);
}

/** 这一片要的 props：窗口里的行（含接口失败的红字）与 ↑/↓ 走的可选清单。 */
interface StripData {
  readonly items: readonly TreeStripItem[];
  /** ↑/↓ 走的那份（与 `items` 出自同一次 `treeRows`，折叠语义一致）。 */
  readonly selectable: readonly NodeId[];
}

/** 读账 + 作业事实，算成这一片要的行；作业表每变一次（`errors` / `tree.jobs()`）就重算一遍。 */
function useStrip(selected: NodeId | null): StripData {
  const { store, tree } = useSession();
  const { errors } = useFacts();
  const rows = treeRows(store, selected, tree.jobs());
  const { window, selectable } = treeWindow(rows, STRIP_ROWS);
  const items = window.map((row) => {
    const failure = row.id === null ? undefined : errors.get(row.id);
    const mark = [row.mark, failure === undefined ? undefined : "✗ 接口失败"].filter((part) => part !== undefined).join(" ");
    return { key: row.key, text: row.text, selected: row.selected, mark: mark === "" ? undefined : mark };
  });
  return { items, selectable };
}

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
      if (selectable.length === 0) return false;
      const delta = key === "up" ? -1 : 1;
      const at = selected === null ? -1 : selectable.indexOf(selected);
      const next =
        at < 0 ? (delta > 0 ? 0 : selectable.length - 1) : Math.min(Math.max(at + delta, 0), selectable.length - 1);
      onSelect(selectable[next] ?? null);
      return true;
    }
    if (key === "ctrl+t") {
      onRetry();
      return true;
    }
    return false;
  });

  return <TreeStrip items={items} />;
});
