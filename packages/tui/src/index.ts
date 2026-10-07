/**
 * `@meristem/tui` 的对外面：**只吃 props 的通用件** + **键的注册** + **屏幕** + **路由** + **一处配色**。
 *
 * 这个包不认识任何 agent 数据结构、不认识角色、不认识账 —— 它连 `@meristem/atree` 都不依赖。
 * 留在这一面的东西有两条硬判据：
 *
 *   · **换一个应用也照样用**（泛化的条带 / 状态条 / 键的形状 / 渲染器生命周期 / 配色）——
 *     一沾业务词（手 / 思考 / 线）就住 terminal，那是那一屏的画法；
 *   · **opentui 没有这件东西**。它有的就不许再写一份：单行编辑器用它的 `<input>`（光标 / 粘贴 /
 *     宽字符都是现成的）、滚动用它会滚的 `<scrollbox>`、折行用 `wrapMode="char"`、布局用它自己的
 *     flex。所以这里既没有输入框，也没有"一行行铺文本"的那种组件 —— 铺文本就是它的 `<text>`。
 *     留下的每一件都带着**引擎没有的那条规矩**（状态条：放不下时掐哪头、补 `…`；条带：
 *     一行 = 文本 + 右端记号 + 选中底色、只铺几行）。
 *
 * 只吃 props、不量屏幕：组件按容器给的宽度画，**折行与滚动都归 opentui**，这样放进任何容器都对。
 * 唯一还在问终端尺寸的是状态条 —— 它要整行两端对齐，而"放不下时补 `…`"必须先知道宽度
 * （引擎自带的裁切是无声的）。
 *
 * 边界：**布局策略不在这里**（几区怎么排、子树怎么折是业务，住 terminal）。**键也一样**：
 * 哪些键归谁由调用方声明（各组件自己 `useKeys`，处理了要返回 `true` —— 见 `keys.ts`），
 * 这里只把 opentui 的按键事件归一化成字符串。
 *
 * opentui 的类型与其组件**不从这一面出去**：这里的名字都是本包自己的词，这样换渲染层
 * 也只需改这一个包。
 */

export { useKeys } from "./keys.ts";
export { RouterProvider, ScreenOutlet, useRouter } from "./router/router.ts";
export { tone } from "./tone.ts";
export { TreeStrip } from "./tree-strip.tsx";
export { StatusBar } from "./status-bar.tsx";
export { openScreen } from "./screen.ts";

export type { KeyHandler } from "./keys.ts";
export type { Router, RouterProviderProps } from "./router/router.ts";
export type { AnyScreen, LayoutRoute, RouteObject, ScreenRef, ScreenRoute, ScreenViewProps } from "./router/route.ts";
export type { TreeStripItem, TreeStripProps } from "./tree-strip.tsx";
export type { StatusBarProps } from "./status-bar.tsx";
export type { Screen } from "./screen.ts";
