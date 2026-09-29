/**
 * 一条记录 → 一行 / 一行 → 记录。**内部**（上层走 `load`）。
 *
 * 形状的正文（三种记录长什么样、为什么内容不挂在节点上）在本文件顶部；
 * 这里只管两件机械的事：编码，以及**折叠**（逐行读回来，把属性折成当前值、把内容按顺序接上）。
 *
 * 折叠是**对账**而不是"尽量读懂"：对不上（节点生两次、两个根、内容接不上、坏行）当场炸，
 * 带着行号与那行原文的片段 —— 账是唯一的事实来源，读歪了比读不出来更糟。
 *
 * 变因：记录格式（多一种事实、改一种 payload）。
 */
import type { Node, NodeId } from "../shape/node.ts";

/** 内容的一笔增量：`base` = 上次写入时的长度（对账用），`added` = 新接上的内容。 */
export interface ContentDelta<M> {
  readonly base: number;
  readonly added: readonly M[];
}

export type LedgerRecord<P, M> =
  | { readonly t: number; readonly node: NodeId; readonly kind: "node"; readonly payload: Node<P> }
  | { readonly t: number; readonly node: NodeId; readonly kind: "content"; readonly payload: ContentDelta<M> }
  | { readonly t: number; readonly node: NodeId; readonly kind: "props"; readonly payload: Partial<P> };

/** 重放出来的东西：节点表（属性已折叠）+ 每个节点自己的内容。 */
export interface Replayed<P, M> {
  readonly nodes: ReadonlyMap<NodeId, Node<P>>;
  /** 内容的数组是**活的**（可变）：折出来之后由 `store` 一个人持有并就地往后长。 */
  readonly content: ReadonlyMap<NodeId, M[]>;
}

/** 一条记录 → 一行（不含换行）。 */
export function encode<P, M>(record: LedgerRecord<P, M>): string {
  return JSON.stringify(record);
}

/** 逐行重放。崩溃留下的**最后**半行由读的一方（`jsonl`）丢掉，这里只处理完整的行。 */
export async function replay<P, M>(lines: AsyncIterable<string>): Promise<Replayed<P, M>> {
  const nodes = new Map<NodeId, Node<P>>();
  // 就地追加（不是每笔复制一遍整段内容）：一句话一个节点也能有上千条，O(n²) 在这里是实打实的。
  const content = new Map<NodeId, M[]>();
  let root: NodeId | null = null;
  let at = 0;

  for await (const line of lines) {
    at += 1;
    const record = parse<P, M>(line, at);

    if (record.kind === "node") {
      const node = record.payload;
      if (nodes.has(record.node)) throw bad(at, line, `节点出生了两次：${record.node}`);
      if (node.id !== record.node) throw bad(at, line, `记录的节点与本行说的不是同一个：${record.node} / ${node.id}`);
      if (node.parent === null) {
        if (root !== null) throw bad(at, line, `账里有第二个根：${root} 与 ${record.node}`);
        root = record.node;
      } else if (!nodes.has(node.parent)) {
        throw bad(at, line, `父还没出生：${node.parent}`);
      }
      nodes.set(node.id, node);
      continue;
    }

    const node = nodes.get(record.node);
    if (node === undefined) throw bad(at, line, `这个节点还没出生：${record.node}`);

    if (record.kind === "content") {
      let current = content.get(record.node);
      if (current === undefined) {
        current = [];
        content.set(record.node, current);
      }
      if (record.payload.base !== current.length) {
        throw bad(
          at,
          line,
          `内容接不上：说接在第 ${record.payload.base} 条之后，实际有 ${current.length} 条`,
        );
      }
      current.push(...record.payload.added);
      continue;
    }

    nodes.set(record.node, { ...node, props: { ...node.props, ...record.payload } });
  }

  return { nodes, content };
}

function parse<P, M>(line: string, at: number): LedgerRecord<P, M> {
  if (line === "") throw bad(at, line, "空行");

  let value: unknown;
  try {
    value = JSON.parse(line);
  } catch (cause) {
    throw new Error(`账第 ${at} 行不是 JSON：${snippet(line)}`, { cause });
  }

  const record = value as Partial<LedgerRecord<P, M>>;
  if (typeof record !== "object" || record === null) throw bad(at, line, "不是一个对象");
  if (typeof record.t !== "number" || typeof record.node !== "string") {
    throw bad(at, line, "缺 t / node");
  }

  switch (record.kind) {
    case "node": {
      const node = record.payload as Node<P> | undefined;
      if (
        node === undefined ||
        typeof node.id !== "string" ||
        (node.parent !== null && typeof node.parent !== "string") ||
        typeof node.boundary !== "boolean" ||
        typeof node.at !== "number"
      ) {
        throw bad(at, line, "节点那一笔缺字段");
      }
      return record as LedgerRecord<P, M>;
    }
    case "content": {
      const delta = record.payload as ContentDelta<M> | undefined;
      if (delta === undefined || typeof delta.base !== "number" || !Array.isArray(delta.added)) {
        throw bad(at, line, "内容那一笔缺字段");
      }
      return record as LedgerRecord<P, M>;
    }
    case "props": {
      const patch = record.payload;
      if (typeof patch !== "object" || patch === null) throw bad(at, line, "属性那一笔不是一个对象");
      return record as LedgerRecord<P, M>;
    }
    default:
      throw bad(at, line, `认不出的种类：${String((record as { kind?: unknown }).kind)}`);
  }
}

function bad(at: number, line: string, why: string): Error {
  return new Error(`账第 ${at} 行读不动（${why}）：${snippet(line)}`);
}

function snippet(line: string): string {
  return line.length > 120 ? `${line.slice(0, 120)}…` : line;
}
