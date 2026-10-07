/**
 * 侧边能放哪些页：**只列有数据来源的那五页**（P0 §5 的页面种类表）。
 *
 * 待办 / 目标与计划 / 名册那三页**不在这里**：它们没有对应物（P0 §9 第 1 条把"要不要连对象一起抄进来"
 * 留给人拍）—— 位置留着不等于先画一个空壳。
 *
 * 为什么在 `lib`：这是**这一屏共享的词表**，两个地方读它 —— 侧边那一栏照着画、换页那条命令照着绕圈
 * （主屏自己换页）。页数写在两个地方会出现"转到第 6 页但只有 5 页"。
 *
 * 变因：侧边有哪些页、每页是什么。
 */
export interface SidePage {
  readonly id: string;
  readonly title: string;
  /** 这一页是什么、数据从哪来（P0 §5 的表）。 */
  readonly note: string;
}

/** 有数据来源的那五页，顺序就是轮换顺序。 */
export const SIDE_PAGES: readonly SidePage[] = [
  { id: "material", title: "材料", note: "模型提到的文件全文 / 我自己放进去的材料" },
  { id: "image", title: "图与 PDF", note: "模型给的图、我摊开看的 PDF" },
  { id: "diff", title: "改动", note: "它动过的文件，一行行加 / 减" },
  { id: "recap", title: "回望", note: "我不在场时发生了什么（从账里取）" },
  { id: "hand", title: "这一手的原文", note: "当前这一手：手名与状态、吐出来的原文、吃进去什么" },
];
