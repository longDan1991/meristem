/** @jsxImportSource @opentui/react */
/**
 * 路由的**用例**：一份能跑的样例，回答"表长什么样、表在哪进来、屏怎么接参数、进 / 出从哪发生"。
 * 好看那一档不在这里（那是 `dev/visual/five-regions.tsx` 的事），屏也是假的 —— 这里要验的是**接法**。
 *
 * 五处要点：
 *   ① 表是一个数组，`as const satisfies readonly RouteObject[]` 钉住它；`open` 的名字与参数形状都从它
 *      长出来，所以写错名字、少给参数、参数形状不对，都在编译期被挡住（不用另写一份类型表）。
 *   ② **没有"主屏"这回事**：默认那一屏只是标了 `index: true` 的那一屏（web 里 `"/"` 对应的页面），
 *      `back()` 回到它 —— 所以 `current` 永远有值，不是 `null`。
 *   ③ 表**只在装配那里**进来一次（`RouterProvider`，它不吃 children）；其余组件一个都不拿表，
 *      谁要用都是一句 `useRouter()`。
 *   ④ 壳（不随屏变的那部分）是一层**布局**：没有名字，`ScreenOutlet()` 是给屏留位的地方（web 的 `<Outlet/>`）。
 *   ⑤ 屏只吃两个 props（`params` + `back`），不认识路由 —— 于是它也能单独被预览工具渲染。
 *
 * 跑起来看：`bun run packages/tui/dev/preview/frame.ts packages/tui/src/router/example/two-screens.tsx --wireframe`
 */
import { useState } from "react";
import type { ReactNode } from "react";
import { RouterProvider, ScreenOutlet, tone, useKeys, useRouter } from "../../index.ts";
import type { RouteObject, ScreenViewProps } from "../../index.ts";

/** 默认那一屏：`index: true` 那一屏，进来就站在它上面。 */
function Main(_props: ScreenViewProps<void>): ReactNode {
  return (
    <box flexDirection="column" paddingX={1}>
      <text fg={tone.accent}>主屏</text>
      <text fg={tone.dim}>它不是什么特例：表里标了 index 的那一屏就是默认，和 web 的 "/" 一样。</text>
    </box>
  );
}

/** 关于：无参屏。`esc` 或 `enter` 都是"回来"，什么都不改。 */
function About({ back }: ScreenViewProps<void>): ReactNode {
  useKeys((key) => {
    if (key !== "escape" && key !== "enter") return false;
    back();
    return true;
  });
  return (
    <box flexDirection="column" paddingX={1}>
      <text fg={tone.accent}>关于</text>
      <text fg={tone.dim}>一屏画在布局留的那块地方：壳不动，回来时原档、原侧边态。</text>
    </box>
  );
}

/** 挑一挑：有参屏。参数由 `open` 给，屏不自己去取数据。 */
function Pick({ params, back }: ScreenViewProps<{ readonly items: readonly string[] }>): ReactNode {
  const [at, setAt] = useState(0);
  const count = params.items.length;

  useKeys((key) => {
    const move = (step: number): void => setAt((now) => (count === 0 ? 0 : (now + step + count) % count));
    switch (key) {
      case "up":
        move(-1);
        return true;
      case "down":
        move(1);
        return true;
      case "enter":
      case "escape":
        back();
        return true;
      default:
        return false;
    }
  });

  return (
    <box flexDirection="column" paddingX={1}>
      <text fg={tone.accent}>挑一挑（{count} 条，过来时带给我的）</text>
      {params.items.map((item, index) => (
        <box key={item} width="100%" backgroundColor={index === at ? tone.selection : undefined}>
          <text>{item}</text>
        </box>
      ))}
    </box>
  );
}

/** 壳：不随屏变的那部分（web 里的根布局）。`ScreenOutlet()` 就是给屏留位的地方。 */
function Shell(): ReactNode {
  const router = useRouter<Screens>();

  // 进屏的那两个键归壳；`esc` 归屏自己 —— 一个键在同一处只有一个含义（`07-rules.md` §2）
  useKeys((key) => {
    switch (key) {
      case "ctrl+a":
        router.open("about");
        return true;
      case "ctrl+p":
        router.open("pick", { items: ["一", "二", "三"] });
        return true;
      case "ctrl+n":
        router.replace("pick", { items: ["甲", "乙"] }); // 换掉当前那一层，不压栈
        return true;
      default:
        return false;
    }
  });

  return (
    <box flexDirection="column" width="100%" height="100%">
      <ScreenOutlet />
      <box style={{ flexGrow: 1 }} />
      {/* 底下那行：这会儿能用的键（`07-rules.md` §7：能用的键只说这一处） */}
      <text fg={tone.dim}>
        {router.current.name === "main" ? "ctrl+a 关于 · ctrl+p 挑一挑" : "ctrl+n 换一屏 · esc 回来"}
      </text>
    </box>
  );
}

/** 表：一层布局（壳）包着三屏；默认那一屏标 `index`。加一屏就是往 children 里 append 一项。 */
const SCREENS = [
  {
    Component: Shell,
    children: [
      { name: "main", index: true, Component: Main },
      { name: "about", Component: About },
      { name: "pick", Component: Pick },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 复用一次类型：`open` 的名字与参数形状都在这上面。 */
type Screens = typeof SCREENS;

/** 装配：表在这里进来一次，路由自己把当前那一屏画出来（这一份用例整棵树就是这个元素）。 */
export default <RouterProvider routes={SCREENS} />;
