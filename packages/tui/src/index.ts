/**
 * `@meristem/tui` 的对外面：**只吃 props 的组件** + **屏幕**。
 *
 * 这个包不认识任何 agent 数据结构、不认识角色、不认识账 —— 它连 `@meristem/atree` 都不依赖。
 * 里面是 AI agent 这类界面反复要用的那几件东西，配上差分渲染与键解码；屏幕（谁创建渲染器、
 * 谁还原终端）也只此一处，别的地方不许再摸终端。
 *
 * 边界：**布局策略不在这里**（几区怎么排、子树怎么折是业务，住 terminal）；
 * 组件只负责"给我这些行 / 这个状态，我怎么画得稳、不闪"。
 * opentui 的类型与其组件**不从这一面出去**：这里的名字都是本包自己的词，这样换渲染层
 * 也只需改这一个包。
 */

export { Frame } from "./frame.tsx";
export { MessageStream } from "./message-stream.tsx";
export { ThoughtLine } from "./thought-line.tsx";
export { HandCard } from "./hand-card.tsx";
export { InputBox } from "./input-box.tsx";
export { TreeStrip } from "./tree-strip.tsx";
export { StatusBar } from "./status-bar.tsx";
export { openScreen } from "./screen.ts";

export type { FrameProps } from "./frame.tsx";
export type { MessageLine, MessageLineStyle, MessageStreamProps } from "./message-stream.tsx";
export type { ThoughtLineProps } from "./thought-line.tsx";
export type { HandCardProps, HandState } from "./hand-card.tsx";
export type { InputBoxProps } from "./input-box.tsx";
export type { TreeStripItem, TreeStripProps } from "./tree-strip.tsx";
export type { StatusBarProps } from "./status-bar.tsx";
export type { Screen } from "./screen.ts";
