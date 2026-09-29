/**
 * `@meristem/tui` 的对外面：**只吃 props 的组件**。
 *
 * 这个包不认识任何 agent 数据结构、不认识角色、不认识账 —— 它连 `@meristem/atree` 都不依赖。
 * 里面是 AI agent 这类界面反复要用的那几件东西，配上差分渲染与键解码。
 *
 * 边界：**布局策略不在这里**（几区怎么排、子树怎么折是业务，住 terminal）；
 * 组件只负责"给我这些行 / 这个状态，我怎么画得稳、不闪"。
 */

export {
  Frame,
  HandCard,
  InputBox,
  MessageStream,
  StatusBar,
  ThoughtLine,
  TreeStrip,
} from "./components.tsx";

export type {
  FrameProps,
  HandCardProps,
  HandState,
  InputBoxProps,
  MessageStreamProps,
  StatusBarProps,
  ThoughtLineProps,
  TreeStripProps,
  TreeStripItem,
} from "./components.tsx";
