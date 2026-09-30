/**
 * 视图：**纯函数** —— 只读账 → 行。不认识账怎么写、不认识事件、不认识 tui。
 *
 * 展示的变因住这一层：树怎么折、选中谁、一行里放什么字。
 * 颜色 / 布局 / 键位归 `app.tsx`（那头才认识外壳）。
 *
 * 变因：展示（出哪些行、每行标什么）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore } from "@meristem/harness";
import type { Job } from "@meristem/roles";

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
