/**
 * 树的形状（**通用的树**，参考 DOM）。
 *
 * 这个包不认识"名字""角色""目录""状态""消息"这些词：它只认结构 ——
 *   · 一个节点有父（`parent`）和自己的属性（`props`，**完全不透明**，上层定义）；
 *   · 节点可以是一段内容的边界（`boundary`，DOM 里最近的东西是 shadow root）；
 *   · 节点有序（账的顺序就是出生顺序），内容往后追加。
 *
 * DOM 的对应物：`Node<P>` ≈ element（`props` ≈ attributes、`parent` ≈ parentNode，
 * 子节点用 `Store.children()` 查），`Store.assemble()` ≈ `textContent`（拼这一枝的内容）。
 *
 * 变因：结构本身的字段（加一笔通用事实）。这是全仓库最稳定的一层。
 */

export type NodeId = string;

export interface Node<P> {
  readonly id: NodeId;
  /** 父；`null` = 根（一棵树只有一个根）。 */
  readonly parent: NodeId | null;
  /** 上层自己定义的结构（名字、角色、做事目录、状态……）：对本包**完全不透明**。 */
  readonly props: P;
  /**
   * 这一枝自成一段：拼接内容（`Store.assemble`）到它为止，不再往上接。
   *
   * 为什么它是结构而不是 `props`：拼接要用它，而 `props` 对本包不透明。
   */
  readonly boundary: boolean;
  /** 出生时刻。 */
  readonly at: number;
}
