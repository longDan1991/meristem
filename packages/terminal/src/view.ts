/**
 * 视图：**纯函数** —— 只读账 → 行。不认识账怎么写、不认识事件、不认识 tui。
 *
 * 展示的变因住这一层：树怎么折、选中谁、一行里放什么字。
 * 颜色归 `style.ts`、键位归各区自己（`components/`）、布局与接线归 `app.tsx`（那几处才认识外壳）。
 *
 * 变因：展示（出哪些行、每行标什么）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, Usage } from "@meristem/harness";
import type { Job } from "@meristem/roles";
import type { Tail } from "./providers/tail.tsx";

/** 行的语义标签：只说"这是什么行"，颜色由 app 定。 */
export type RowTag = "title" | "dim" | "user" | "model" | "thought" | "hand" | "error";

export interface Row {
  readonly text: string;
  readonly tag: RowTag;
}

/** 树条带的一行。`id === null` 表示这一行是被折起来的子树（不可选中）。 */
export interface TreeRow {
  readonly id: NodeId | null;
  readonly text: string;
  readonly depth: number;
  readonly selected: boolean;
  readonly mark?: string;
}

/** 一层的缩进与两种记号（展示的字面量只在这里定一份）。 */
const INDENT = "  ";
const FOLD = "▸ ";
const MARK = "▶ ";

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
 * `selected === null`（还没进过任何一条线）就是那一屏"只有根 + 有活的线"。没有节点 → 空数组。
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
      id,
      text: INDENT.repeat(depth) + node.props.name + " · " + node.props.role,
      depth,
      selected: id === selected,
    };
    rows.push(count === 0 ? base : { ...base, mark: MARK + count });
    for (const kid of store.children(id)) {
      if (visible.has(kid)) walk(kid, depth + 1);
      else {
        const text = INDENT.repeat(depth + 1) + FOLD + (size.get(kid) ?? 1) + " 条线";
        rows.push({ id: null, text, depth: depth + 1, selected: false });
      }
    }
  };
  walk(root, 0);
  return rows;
}

/**
 * 选中那条线的正文：它自己的平铺对话（人 / 模型 / 思考 / 手的过程）+ `tail`（正在吐、还没进账的字，
 * 原样接在末尾，标什么都不改）。
 *
 * **只认结构与顺序，不解析一个字**：作业 id 拼在消息文本里，那是给模型配对用的（DESIGN §9.6），
 * 界面要认的是形状 —— "`tool_calls` 后面紧跟着回话"。所以一条 `assistant` 的每个调用各铺一行头
 * （头行属于那条消息，跟着它的正文按账的顺序排），回话再按调用的顺序**位置**配对：只吃紧挨着的那条
 * `role: "tool"`，以及紧随其后 `by === 调用名` 的那条 `role: "user"`。
 * `tool_calls` 后面**不是**回话的（进程崩在中间留下的未完成区）只铺头行，后面的消息各按各的普通规则铺
 * （它们是独立的事实，不能被硬拉进上一条手的过程里）。
 *
 * 在跑的作业（卡片：名字 / 参数 / 已跑多久 / 现在吐了什么）**不在这里** —— 它还没进账，
 * 那是 `app.tsx` 拿 `Job.output()` / `Job.stream()` 画的（DESIGN §9.2 的"面向人"）。
 */
export function lineRows(store: LineStore, node: NodeId, tail: readonly Row[]): readonly Row[] {
  const rows: Row[] = [];
  /** 空串不铺（没有字的消息就是没有行）；其余按行拆开，一行一个 Row。 */
  const push = (content: string, tag: RowTag): void => {
    if (content === "") return;
    for (const line of content.split("\n")) rows.push({ text: line, tag });
  };

  const messages = store.content(node);
  let index = 0;
  while (index < messages.length) {
    const message = messages[index];
    if (message === undefined) break;

    if (message.role === "assistant") {
      push(message.reasoning ?? "", "thought");
      push(message.content, "model");
      const calls = message.toolCalls ?? [];
      // 头行来自这条 assistant 消息（它在回话之前），所以按账的顺序把这一组头先铺完；
      // 回话再按调用的顺序位置配对 —— 严格紧挨着，中间隔了什么就说明这一手没有回话。
      for (const call of calls) push(FOLD + call.name + " " + JSON.stringify(call.arguments), "hand");

      let cursor = index + 1;
      for (const call of calls) {
        const reply = messages[cursor];
        if (reply?.role !== "tool") break;
        push(reply.content, "hand");
        cursor += 1;
        const ending = messages[cursor];
        if (ending?.role === "user" && ending.by === call.name) {
          push(ending.content, "hand");
          cursor += 1;
        }
      }
      index = cursor;
      continue;
    }

    // 没有前导 tool_calls 的 tool 消息是孤儿回话：它是账里的一段事实，但不是"某只手的过程"。
    // `by` 是"从手回来的"的结构标记（`user` 那条交代就靠它认），所以带 `by` 的 user 消息标 hand：
    // 它长得像人的话，但它不是人说的。
    if (message.role === "user") push(message.content, message.by === undefined ? "user" : "hand");
    else push(message.content, "dim");
    index += 1;
  }

  return [...rows, ...tail];
}

// ---- 派生成"给人看的行 / 文案"：账 + 吐字 + 在跑什么，纯函数，不认识 tui / React ----

/** 树条带最多铺几行（选中行永远在窗口里，其余靠折叠与滚动）。 */
export const STRIP_ROWS = 8;

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

/** `ctrl+o` 收起时，把一串思考压成一行说明（**看得见的限制**，不是静默丢字）。 */
export function foldThoughts(rows: readonly Row[]): readonly Row[] {
  const folded: Row[] = [];
  let run = 0;
  const flush = (): void => {
    if (run > 0) folded.push({ text: `▸ 思考 ${run} 行（ctrl+o 展开）`, tag: "dim" });
    run = 0;
  };
  for (const row of rows) {
    if (row.tag === "thought") {
      run += 1;
      continue;
    }
    flush();
    folded.push(row);
  }
  flush();
  return folded;
}

/** 正在吐的字里账里还没有的那部分（assistant 那条一进账，它整段就都在账里了）。 */
export function unaccounted(store: LineStore, node: NodeId, tail: Tail | null): Tail | null {
  if (tail === null || tail.node !== node) return null;
  const last = store.content(node).at(-1);
  if (last === undefined || last.role !== "assistant") return tail;
  return {
    node,
    base: tail.base,
    text: last.content.endsWith(tail.text) ? "" : tail.text,
    thought: (last.reasoning ?? "").endsWith(tail.thought) ? "" : tail.thought,
  };
}

/** 一段字按行拆成带标签的 Row（空串不铺）。 */
export function split(text: string, tag: RowTag): readonly Row[] {
  return text === "" ? [] : text.split("\n").map((line) => ({ text: line, tag }));
}

/**
 * 状态条两行文案。没有根时**更**要说清楚：人正要打第一句话，这时按回车没反应最像"界面卡住了"。
 */
export function statusText(
  store: LineStore,
  node: NodeId | null,
  jobCount: number,
  usage: Usage | undefined,
  notice: string,
): { readonly left: string; readonly right: string } {
  if (node === null) {
    return {
      left: notice === "" ? "还没有根 —— 说一句什么，就以它开第一条线" : notice,
      right: "enter 说话 · ctrl+c 退出",
    };
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

/** 输入行的 placeholder。 */
export function placeholder(node: NodeId | null, root: NodeId | null): string {
  if (node === null) return "说一句什么（没有根就以这一句开第一条线）";
  if (root === null) return "说一句什么";
  return "跟这条线说一句（回车进账）";
}

