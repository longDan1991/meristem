/**
 * `@meristem/tui` 的对外面：**只吃 props 的通用件** + **命令模块** + **屏幕** + **路由** + **一处配色**。
 *
 * 这个包不认识任何 agent 数据结构、不认识角色、不认识账 —— 它连 `@meristem/atree` 都不依赖。
 * 留在这一面的东西有两条硬判据：
 *
 *   · **换一个应用也照样用**（泛化的名单 / 状态条 / 命令模块 / 渲染器生命周期 / 配色）——
 *     一沾业务词（手 / 思考 / 线）就住 terminal，那是那一屏的画法；
 *   · **opentui 没有这件东西**。它有的就不许再写一份：单行编辑器用它的 `<input>`（光标 / 粘贴 /
 *     宽字符都是现成的）、滚动用它会滚的 `<scrollbox>`、折行用 `wrapMode="char"`、布局用它自己的
 *     flex。所以这里既没有输入框，也没有"一行行铺文本"的那种组件 —— 铺文本就是它的 `<text>`。
 *     留下的每一件都带着**引擎没有的那条规矩**（状态条：放不下时掐哪头、补 `…`；名单：
 *     一行 = 文本 + 右端记号 + 选中底色、只铺几行；命令模块：一份 yaml 当表、**一层只跑一个**、
 *     从队尾往回问 —— 引擎给的 `useKeyboard` 是所有订阅者都跑，没有"有人接了就别往下传"这件事，
 *     也没有"这个键是谁的"）。名单**不用 opentui 的 `<select>`**：那个要焦点才吃 ↑↓/enter，
 *     而终端界面的焦点永远在输入行，键归命令表。
 *
 * 只吃 props、不量屏幕：组件按容器给的宽度画，**折行与滚动都归 opentui**，这样放进任何容器都对。
 * 唯一还在问终端尺寸的是状态条 —— 它要整行两端对齐，而"放不下时补 `…`"必须先知道宽度
 * （引擎自带的裁切是无声的）。
 *
 * 边界：**布局策略不在这里**（几区怎么排、子树怎么折是业务）。**键也只有一条路**：按键由命令模块
 * 统一收口（`CommandBusProvider`），谁做什么由订阅声明 —— 这一面给的是**原语**（`useBus`），
 * "什么时候挂、什么时候摘"那一步合成在应用那一层（`useCommand`：它还要问"这一屏在被盖住吗"）。
 * 这一面不出去任何 "自己监听按键" 的东西，所以界面认领的键必然来自那张表。
 *
 * opentui 的类型与其组件**不从这一面出去**：这里的名字都是本包自己的词，这样换渲染层
 * 也只需改这一个包。
 */

export { Commands } from "./command/commands.ts";
export { CommandBusProvider, useBus, useCommands } from "./command/bus.tsx";
export { RouterProvider, ScreenOutlet, onActivated, onDeactivated, useRouter } from "./router/router.ts";
export { tone } from "./tone.ts";
export { RowList } from "./row-list.tsx";
export { StatusBar } from "./status-bar.tsx";
export { openScreen } from "./screen.ts";

export type { Command, KeyBinding, KeyHit, Layer } from "./command/commands.ts";
export type { Bus } from "./command/bus.tsx";
export type { CommandBus } from "./command/registry.ts";
export type { Handling, Registry } from "./command/registry.ts";
export type { Router, RouterProviderProps } from "./router/router.ts";
export type {
  AnyScreen,
  LayoutRoute,
  Names,
  ParamsOf,
  RouteObject,
  ScreenRef,
  ScreenRoute,
  ScreenViewProps,
  ScreensOf,
} from "./router/route.ts";
export type { RowListItem, RowListProps } from "./row-list.tsx";
export type { StatusBarProps } from "./status-bar.tsx";
export type { Screen } from "./screen.ts";
