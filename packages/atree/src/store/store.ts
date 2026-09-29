/**
 * Store：一棵树 = **查写节点** + **查写内容**。就这两类事情，没有第三类。
 *
 * 这个包不认识名字 / 角色 / 目录 / 状态 / 消息长什么样 —— 它只知道"节点挂着 `props`（不透明），
 * 节点有序，每个节点有一份自己的内容数组（也是不透明的 `M`）"。
 *
 * **开与收**：给个路径就完了（`load`）—— 有账就折出来，没有就是一棵**空的内存树**；
 * 第一次真写入才落盘建文件。收手时 `close()` 把缓冲落盘。
 * 中间没有任何旋钮，也没有观察口：**时机是上层造成的，唤醒归上层自己管**（它本来就知道
 * 自己什么时候写了什么），这个包只管数据。
 *
 * **拼接内容（`assemble`）住在这一层**：上层要"这条线这一枝完整的上下文"时，不用自己走树 ——
 * 往上走、碰上 `boundary` 停下、按顺序接上各代内容，这份机制属于树。
 * 至于"什么内容""为什么这里要停"，是上层自己给它的事实。
 *
 * 内存里的索引（节点表、子节点表、内容表）与账是同一份事实的两种形态：账是只追加的正文，
 * 索引是折出来的当前值。**写的时候两份一起推进**（先记账、再改内存：记账炸了就没人以为写成功了）。
 *
 * 读与写在同一面（DOM 也是这样：同一个 document 既查又写）；只读的一面由调用方按类型收窄。
 *
 * 变因：账的内存机制（索引、增量、恢复组装、拼接）。
 */
import { randomUUID } from "node:crypto";
import type { Node, NodeId } from "../shape/node.ts";
import { openFile, type LedgerFile } from "./jsonl.ts";
import { replay, type Replayed } from "./record.ts";

/** 造一个节点要的东西：挂在哪、属性是什么、是不是一段内容的边界。 */
export interface TreeInput<P> {
  /** 父；`null` = 造根（一棵树只允许一个根）。 */
  readonly parent: NodeId | null;
  readonly props: P;
  /** 这一枝自成一段：拼接内容时到它为止。 */
  readonly boundary?: boolean;
}

export interface Store<P, M> {
  /* ---- 节点 ---- */

  /** 根；还没造出根时是 `null`（空树是合法状态：这棵树还没开出来）。 */
  root(): NodeId | null;
  get(id: NodeId): Node<P> | null;
  /** 子节点（出生顺序）。 */
  children(id: NodeId): readonly NodeId[];
  /** 造一个节点：父为 `null` 就是造根（第二个根当场报错）。 */
  create(input: TreeInput<P>): NodeId;
  /** 改属性（DOM 的 setAttribute）：账里记一笔补丁，读出来是折叠后的当前值。 */
  patch(id: NodeId, props: Partial<P>): void;

  /* ---- 内容（消息）---- */

  /**
   * 这个节点自己的内容；祖先的内容要用 `assemble` 才有。
   *
   * 给的是**活引用**（只追加的数组，内容只会往后长）：别把它当快照存着，要快照自己复制一份。
   * 这样每笔追加都是摊还 O(1) —— 一条线的对话可以很长，逐笔复制整段是 O(n²)。
   */
  content(id: NodeId): readonly M[];
  /** 追加内容：顺序就是账的顺序。 */
  append(id: NodeId, added: readonly M[]): void;
  /** **拼接**：这条线这一枝的完整内容 —— 从自己往上接，碰上边界（含它）停下。 */
  assemble(id: NodeId): readonly M[];

  /* ---- 生命周期 ---- */

  /** 收手：缓冲落盘并放手（进程退出前叫一次）。 */
  close(): Promise<void>;
}

/**
 * 打开一棵树：路径指向的那份账 —— 有就折出来（节点、内容，属性折成当前值），
 * 没有 / 还是空的就返回一棵空的内存树（连文件都不建，等第一次真写入）。
 *
 * **为什么没有"这底下有哪些树"的接口**：这个包只管一棵树。多用户（一人一棵树）会需要一份清单，
 * 但那是将来一层的事，现在不做 —— 现在**全局只有一棵树**，路径由配置显式给出（DESIGN §7）。
 */
export async function load<P, M>(path: string): Promise<Store<P, M>> {
  const file = openFile<P, M>(path);
  return openStore(file, await replay<P, M>(file.read()));
}

function openStore<P, M>(file: LedgerFile<P, M>, replayed: Replayed<P, M>): Store<P, M> {
  const nodes = new Map<NodeId, Node<P>>(replayed.nodes);
  const content = new Map<NodeId, M[]>(replayed.content);
  const kids = new Map<NodeId | null, NodeId[]>();
  for (const node of nodes.values()) childList(kids, node.parent).push(node.id);

  function nodeOf(id: NodeId): Node<P> {
    const node = nodes.get(id);
    if (node === undefined) throw new Error(`没有这个节点：${id}`);
    return node;
  }

  /** 这个节点自己的内容数组（**活的**：存在就返回它，不存在就放一个空的进去）。 */
  function own(id: NodeId): M[] {
    nodeOf(id);
    const list = content.get(id);
    if (list !== undefined) return list;
    const fresh: M[] = [];
    content.set(id, fresh);
    return fresh;
  }

  return {
    root() {
      return childList(kids, null)[0] ?? null;
    },

    get(id) {
      return nodes.get(id) ?? null;
    },

    children(id) {
      nodeOf(id);
      return childList(kids, id);
    },

    create(input) {
      if (input.parent === null) {
        const existing = childList(kids, null)[0];
        if (existing !== undefined) throw new Error(`已经有一个根了：${existing}`);
      } else {
        nodeOf(input.parent);
      }
      const at = Date.now();
      const node: Node<P> = {
        id: randomUUID(),
        parent: input.parent,
        props: input.props,
        boundary: input.boundary ?? false,
        at,
      };
      file.append({ t: at, node: node.id, kind: "node", payload: node });
      nodes.set(node.id, node);
      childList(kids, node.parent).push(node.id);
      return node.id;
    },

    patch(id, props) {
      const node = nodeOf(id);
      if (Object.keys(props).length === 0) return;
      const at = Date.now();
      file.append({ t: at, node: id, kind: "props", payload: props });
      nodes.set(id, { ...node, props: { ...node.props, ...props } });
    },

    content(id) {
      return own(id);
    },

    append(id, added) {
      if (added.length === 0) return;
      const current = own(id);
      file.append({ t: Date.now(), node: id, kind: "content", payload: { base: current.length, added } });
      // 就地长（`content(id)` 给的是这个活的数组）：见接口上那句"别当快照存着"。
      current.push(...added);
    },

    assemble(id) {
      const chain: NodeId[] = [];
      for (let cur: NodeId | null = id; cur !== null; ) {
        const node = nodeOf(cur);
        chain.push(node.id);
        if (node.boundary) break;
        cur = node.parent;
      }
      const out: M[] = [];
      for (let i = chain.length - 1; i >= 0; i -= 1) {
        const step = chain[i];
        if (step === undefined) continue;
        for (const message of content.get(step) ?? []) out.push(message);
      }
      return out;
    },

    close() {
      return file.close();
    },
  };
}

function childList(kids: Map<NodeId | null, NodeId[]>, parent: NodeId | null): NodeId[] {
  const list = kids.get(parent);
  if (list !== undefined) return list;
  const fresh: NodeId[] = [];
  kids.set(parent, fresh);
  return fresh;
}
