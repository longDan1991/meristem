/**
 * 路由表：**哪一屏画什么**只有这一份（屏名就是这张表里的 `name`）。
 *
 * 和 web 路由一个形状：一个数组，一层布局（壳）包着若干屏。加一屏就是往 `children` 里 append 一项；
 * 屏名与参数形状都从这张表上长出来，所以 `open("…")` 写错名字、少给参数都过不了编译。
 * 命令表那边进屏靠 `screen.<屏名>`（命令模块从 id 的第二段读屏名），两边由装配层核对
 * （`main.ts`）—— 屏名改了就两处一起改。
 *
 * **八屏**（P0 §2.2）：主屏 + 挑角色 + 挑模型 + 键位表 + 选中复制 + 对话内搜索 + 变更日志与关于 +
 * 诊断日志。进屏只有三条路（修饰键 / 斜杠命令 / 从正文点进去开侧边），屏名与那些入口的对应关系
 * 写在命令表的 id 上。
 *
 * **默认那一屏是标了 `index: true` 的那一屏**（web 里 `"/"` 对应的页面）—— 打开就站在它上面，
 * `back()` 回到它。没有"主屏"这个特例：它就是表里的一项。
 *
 * **屏自带的行由屏自己画**：布局不留插槽（它只画壳那一行）—— 主屏自带状态行、事实行与输入行，
 * 别的屏什么都没有（P0 §3：跟着"我这条线"走的那几行只在要说话的屏上有意义）。
 *
 * 变因：有哪几屏、屏名、屏与布局怎么挂。
 */
import type { RouteObject } from "@meristem/tui";
import { Shell } from "./layout/shell.tsx";
import { AboutScreen } from "./screens/about.tsx";
import { CopyScreen } from "./screens/copy.tsx";
import { DiagnosticsScreen } from "./screens/diagnostics.tsx";
import { KeysScreen } from "./screens/keys.tsx";
import { MainScreen } from "./screens/main.tsx";
import { ModelScreen } from "./screens/model.tsx";
import { RoleScreen } from "./screens/role.tsx";
import { SearchScreen } from "./screens/search.tsx";

export const SCREENS = [
  {
    Component: Shell,
    children: [
      { name: "main", index: true, Component: MainScreen },
      { name: "role", Component: RoleScreen },
      { name: "model", Component: ModelScreen },
      { name: "keys", Component: KeysScreen },
      { name: "copy", Component: CopyScreen },
      { name: "search", Component: SearchScreen },
      { name: "about", Component: AboutScreen },
      { name: "diagnostics", Component: DiagnosticsScreen },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 复用一次类型：`useRouter<Screens>()` 与 `open` 的名字 / 参数都在这上面。 */
export type Screens = typeof SCREENS;

/** 表里**所有**屏的名字（布局摊平）——装配核对命令表指不指得到它们，用这个。 */
export function screenNames(routes: readonly RouteObject[] = SCREENS): readonly string[] {
  return routes.flatMap((route) => ("children" in route ? screenNames(route.children) : [route.name]));
}

/** 默认那一屏的名字（打开就站在它上面）：装配核对"哪几屏不需要进它的命令"用它。 */
export function indexScreen(routes: readonly RouteObject[] = SCREENS): string {
  for (const route of routes) {
    if ("children" in route) {
      const found = indexScreen(route.children);
      if (found !== "") return found;
      continue;
    }
    if (route.index === true) return route.name;
  }
  return "";
}
