/**
 * 路由表：**哪一屏画什么**只有这一份（屏名就是这张表里的 `name`）。
 *
 * 和 web 路由一个形状：一个数组，一层布局（壳）包着若干屏。加一屏就是往 `children` 里 append 一项；
 * 屏名与参数形状都从这张表上长出来，所以 `open("…")` 写错名字、少给参数都过不了编译。
 *
 * **默认那一屏是标了 `index: true` 的那一屏**（web 里 `"/"` 对应的页面）—— 打开就站在它上面，
 * `back()` 回到它。没有"主屏"这个特例：它就是表里的一项。
 *
 * 变因：有哪几屏、屏名、屏与布局怎么挂。
 */
import type { RouteObject } from "@meristem/tui";
import { MainScreen } from "./main.tsx";
import { Shell } from "./shell.tsx";

export const SCREENS = [
  {
    Component: Shell,
    children: [{ name: "main", index: true, Component: MainScreen }],
  },
] as const satisfies readonly RouteObject[];

/** 复用一次类型：`useRouter<Screens>()` 与 `open` 的名字 / 参数都在这上面。 */
export type Screens = typeof SCREENS;
