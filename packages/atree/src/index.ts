/**
 * `@meristem/atree` 的对外面：**一棵通用的树**。
 *
 * 这个包回答的是"任何树都有的那件事"：节点（父、属性、边界、出生顺序）、每个节点自己的内容、
 * 一条 append-only 的账、以及**沿枝拼接内容**这份机制。参考 DOM：
 * `Node<P>` ≈ element（`props` ≈ attributes），`Store.assemble()` ≈ `textContent`，
 * `boundary` ≈ shadow root。
 *
 * 对外只有三件事：`load(path)`（有树折出来，没有就是空的内存树）、`Store` 上的两类操作
 * （查写节点 / 查写内容）、`close()` 收手。它不管"有哪些树"—— 全局只有一棵树，多用户的清单
 * 是将来一层的事（DESIGN §7）。
 * 落盘格式、缓冲、重放、账文件长什么样，全是内部机制 —— 不上面。
 *
 * 它不认识名字 / 角色 / 目录 / 状态 / 消息长什么样 —— `props` 与内容都是上层给的类型，
 * 一个字段都不解释。
 *
 * **账长什么样**（写在 `store/record.ts`，这里只用它的结论）：一行一条 JSON 的追加文件 ——
 * 出生一笔（节点：父 / props / 边界 / 出生时刻）+ 内容若干笔（一笔 = 接在这个长度之后的新内容）
 * + 属性若干笔（props 补丁）。树不是另一份数据结构，**树就是这份账折出来的样子**。
 *
 * 主坐标轴：**数据结构与存取机制**。
 */

export type { Node, NodeId } from "./shape/node.ts";

export type { Store, TreeInput } from "./store/store.ts";
export { load } from "./store/store.ts";
