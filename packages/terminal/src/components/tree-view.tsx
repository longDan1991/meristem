/** @jsxImportSource @opentui/react */
/**
 * 树：内容区档 ②（一小段 + 选中那行的实况）与档 ③（整块）画的是同一份东西，只有两处不同 ——
 * **窗口多大**与**选中下面要不要就地展开实况**。所以一个组件、两个开关，不写两份画法。
 *
 * **选中画在树上**（`▸` 是选中行的底色）：P0 §4 规则 3 —— 选中不许画在当场看不见的东西上；
 * 窗口跟着选中滚（规则 4），所以选中的那条永远在视野里。`↑↓` 只移选中、**不切过去**
 * （切过去是 `enter`：换掉我站着的线并回档 ①，P0 §6）。
 *
 * **整块是一个名单**：树行与"选中那行的实况"同一份名单里的行（实况那几行 `muted`、不可选中）——
 * 实况就长在选中行下面（accordion，不是另开一块），而布局上只有一列行，不叠盒子。
 * 这一块占**恰好 `size` 行**（档 ② 的预算 / 档 ③ 的整块高）：高度是显式给的，不靠内容撑。
 *
 * **键从命令表来**：这一片认领的是表里 `list.*` 那几条（键写在 `registry/commands.yaml`），
 * 不在这里再写一遍键名 —— 键位表屏与键行读的是同一份；**挂上来与否就是"这份名单在不在"**。
 *
 * 变因：树的窗口与实况这两处画法（折树与窗口预算是 `lib/tree.ts` 的纯计算）。
 */
import type { NodeId } from "@meristem/atree";
import { RowList } from "@meristem/tui";
import type { RowListItem } from "@meristem/tui";
import { memo } from "react";
import type { ReactNode } from "react";
import { useCommand } from "../hooks/commands.ts";
import { useNow } from "../hooks/job-output.ts";
import { unaccounted } from "../lib/inflight.ts";
import { treeRows, treeWindow } from "../lib/tree.ts";
import type { TreeRow } from "../lib/tree.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";

/** 实况那块铺几行（名字·角色 / 手上的活 / 正在吐的那一句）。 */
export const DETAIL_ROWS = 3;

/** 实况的缩进：比树行的缩进再深两级（它属于上面那一行的展开，不是又一条线）。 */
const DETAIL_INDENT = "    ";

export interface TreeViewProps {
  /** 这一段一共几行（档 ② 的预算 / 档 ③ 的整块高）。实况占的那几行从这里扣。 */
  readonly size: number;
  /** 选中那行下面就地展开它的实况（档 ②）。 */
  readonly detail: boolean;
  /** 树上选中的那条、换它那一下、以及"切到这条线"（走位与切换归主屏那一份状态）。 */
  readonly cursor: NodeId | null;
  readonly moveCursor: (node: NodeId | null) => void;
  readonly enterLine: (node: NodeId) => void;
}

/** 一行树（带折起来的那种不可选中的行）。 */
function itemsOf(rows: readonly TreeRow[], errors: ReadonlyMap<NodeId, string>): readonly RowListItem[] {
  return rows.map((row) => {
    const failure = row.id === null ? undefined : errors.get(row.id);
    const mark = [row.mark, failure === undefined ? undefined : "✗ 接口错误"]
      .filter((part) => part !== undefined)
      .join(" ");
    return { key: row.key, text: row.text, selected: row.selected, mark: mark === "" ? undefined : mark };
  });
}

export const TreeView = memo(function TreeView({
  size,
  detail,
  cursor,
  moveCursor,
  enterLine,
}: TreeViewProps): ReactNode {
  const { store, tree } = useSession();
  const { errors } = useFacts();

  const rows = treeRows(store, cursor, tree.jobs());
  const windowSize = Math.max(1, detail ? size - DETAIL_ROWS : size);
  const { window, selectable } = treeWindow(rows, windowSize);
  const facts = useDetail(detail ? cursor : null);

  // 走位（`list.*`）就近挂在这儿：这一片在，走位就归它（挂上来的时刻 = 树出现的时刻 ——
  // 命令名单浮层若也开着，它挂得更晚，于是 `↑↓` 归名单，P0 §1 决策 4）。
  useCommand("list.*", (id) => {
    if (selectable.length === 0) return;
    const at = cursor === null ? -1 : selectable.indexOf(cursor);
    if (id === "list.enter") {
      const chosen = selectable[at < 0 ? 0 : at];
      if (chosen !== undefined) enterLine(chosen);
      return;
    }
    const delta = id === "list.prev" ? -1 : 1;
    const next =
      at < 0 ? (delta > 0 ? 0 : selectable.length - 1) : Math.min(Math.max(at + delta, 0), selectable.length - 1);
    moveCursor(selectable[next] ?? null);
  });

  // 实况就插在选中那行下面（accordion：不是另开一块，也没有第二个盒子）。
  const at = window.findIndex((row) => row.selected);
  const above = at < 0 ? window : window.slice(0, at + 1);
  const below = at < 0 ? [] : window.slice(at + 1);
  const items: readonly RowListItem[] = [
    ...itemsOf(above, errors),
    ...(at >= 0 ? facts.map((line, index) => ({
      key: `detail:${index.toString()}`,
      text: `${DETAIL_INDENT}${line}`,
      selected: false,
      muted: true,
    })) : []),
    ...itemsOf(below, errors),
  ];

  return (
    // 高度是**预算**（档 ② 从对话那里借来的那几行 / 档 ③ 的整块），不许被压：对话那块 `flexGrow`
    // 会来抢地方，这一块必须 `flexShrink: 0` 才拿得住（不然切来切去之后它会被挤成 0 行，屏上什么都没有）。
    <box flexDirection="column" width="100%" height={size} style={{ flexShrink: 0 }}>
      <RowList items={items} />
    </box>
  );
});

/**
 * 选中那条线的实况，三行文字：名字·角色 / 手上的活 / 正在吐的那一句（P0 §4 档 ②）。
 * 取数据（不是画）：它要挂在选中那行下面，所以是行数据，不是一块界面。
 */
function useDetail(node: NodeId | null): readonly string[] {
  const { store, tree } = useSession();
  const tail = useTail();
  const jobs = node === null ? [] : tree.jobs().filter((job) => job.space === node);
  const now = useNow(jobs.length > 0);
  if (node === null) return [];
  const facts = store.get(node)?.props;
  const live = unaccounted(store, node, tail);
  const hands =
    jobs.length === 0
      ? "手上的活：没有"
      : `手上的活：${jobs.map((job) => `${job.name} ${((now - job.at) / 1000).toFixed(1)}s`).join(" · ")}`;
  // 正在吐的取第一行就够：完整原文在侧边的"这一手的原文"那一页。
  const first = (live === null ? "" : live.thought === "" ? live.text : live.thought).split("\n")[0] ?? "";
  return [
    facts === undefined ? node : `${facts.name} · ${facts.role}`,
    hands,
    first === "" ? "正在吐：还没有" : `正在吐：${first}`,
  ];
}
