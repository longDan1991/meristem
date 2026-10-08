/** @jsxImportSource @opentui/react */
/**
 * 路由：**站在哪一屏怎么变**（默认那一屏在栈底、`open` 压栈、`replace` 不压栈、`back` 弹栈），
 * 以及**表怎么摊平**（布局里的屏也算数、哪些表要当场炸）。
 *
 * 走位写在屏自己的 `onActivated` 里：**它每次露头走一步**（一次里连做几步会被 React 合批，
 * 中间那几屏根本不渲染，脚印就少了几笔），`walkOnce` 保证同一步只走一次 —— 否则回到默认那一屏时
 * 它又开一次屏，成了环。屏不卸载（被盖住的只是藏起来），所以"露头"不等于"挂载"：拿挂载当这一步的
 * 时机，被盖住的那几屏会在每次重渲染时又记一笔脚印。判断看的是**脚印**（一串屏名 + 参数），它比读帧里的像素可靠：非 TTY 的
 * 渲染器在**挂载后**更新时画的帧会缺行（见 `dev/preview/render.ts` 那条路径）。布局 + `ScreenOutlet`
 * 的渲染路径另有一条**静态**帧测试（那种情况读帧是准的）。
 */
import { beforeEach, describe, expect, test } from "bun:test";
import { onActivated, RouterProvider, ScreenOutlet, useRouter } from "../src/router/router.ts";
import type { LayoutRoute, RouteObject, ScreenRoute, ScreenViewProps } from "../src/router/route.ts";
import type { ReactNode } from "react";
import { renderFrame } from "../dev/preview/render.ts";
import type { Frame } from "../dev/preview/render.ts";
import { indexRoutes } from "../src/router/table.ts";

/** 帧里那几行字（样式不管，只看写了什么）。 */
function textOf(frame: Frame): string {
  return frame.lines.map((line) => line.map((span) => span.text).join("")).join("\n");
}

/** 脚印：每次"站在哪一屏"变了记一笔。 */
const TRAIL: string[] = [];

function note(entry: string): void {
  if (TRAIL[TRAIL.length - 1] !== entry) TRAIL.push(entry);
}

/** 走位里的每一步只走一次（不然就是环）。 */
const WALKED = new Set<string>();

function walkOnce(step: string): boolean {
  if (WALKED.has(step)) return false;
  WALKED.add(step);
  return true;
}

/** 壳：布局。`ScreenOutlet` 就是给屏留位的地方。 */
function Shell(): ReactNode {
  return (
    <box flexDirection="column" width="100%">
      <text>壳</text>
      <ScreenOutlet />
    </box>
  );
}

/** 进屏：默认那一屏挂上来就开 pick（带着参数）。 */
const OPEN_ONLY = [
  {
    Component: Shell,
    children: [
      {
        name: "main",
        index: true,
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof OPEN_ONLY>();
          onActivated(() => {
            note("main");
            if (walkOnce("open:main")) router.open("pick", { items: ["一", "二"] });
          }, []);
          return <text>主屏</text>;
        },
      },
      {
        name: "pick",
        Component: ({ params }: ScreenViewProps<{ readonly items: readonly string[] }>): ReactNode => {
          onActivated(() => {
            note(`pick:${params.items.join(",")}`);
          }, []);
          return <text>挑</text>;
        },
      },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 出屏：pick 挂上来就 back。 */
const OPEN_BACK = [
  {
    Component: Shell,
    children: [
      {
        name: "main",
        index: true,
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof OPEN_BACK>();
          onActivated(() => {
            note("main");
            if (walkOnce("back:main")) router.open("pick");
          }, []);
          return <text>主屏</text>;
        },
      },
      {
        name: "pick",
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof OPEN_BACK>();
          onActivated(() => {
            note("pick");
            if (walkOnce("back:pick")) router.back();
          }, []);
          return <text>挑</text>;
        },
      },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 在默认那一屏上 back：什么都不做（不弹穿栈底）。 */
const BACK_AT_BOTTOM = [
  {
    Component: Shell,
    children: [
      {
        name: "main",
        index: true,
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof BACK_AT_BOTTOM>();
          onActivated(() => {
            note("main");
            if (walkOnce("bottom:main")) router.back();
          }, []);
          return <text>主屏</text>;
        },
      },
      {
        name: "pick",
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          onActivated(() => {
            note("pick");
          }, []);
          return <text>挑</text>;
        },
      },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 压了栈的话最后落点会是 pick，所以这条脚印能分出来 `replace` 到底压没压。 */
const REPLACE_THEN_BACK = [
  {
    Component: Shell,
    children: [
      {
        name: "main",
        index: true,
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof REPLACE_THEN_BACK>();
          onActivated(() => {
            note("main");
            if (walkOnce("replace:main")) router.open("pick");
          }, []);
          return <text>主屏</text>;
        },
      },
      {
        name: "pick",
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof REPLACE_THEN_BACK>();
          onActivated(() => {
            note("pick");
            if (walkOnce("replace:pick")) router.replace("about");
          }, []);
          return <text>挑</text>;
        },
      },
      {
        name: "about",
        Component: (_props: ScreenViewProps<void>): ReactNode => {
          const router = useRouter<typeof REPLACE_THEN_BACK>();
          onActivated(() => {
            note("about");
            if (walkOnce("replace:about")) router.back();
          }, []);
          return <text>关于</text>;
        },
      },
    ],
  },
] as const satisfies readonly RouteObject[];

/** 静态：默认那一屏挂上来不动（读帧准的就是这种）。 */
const STATIC = [
  {
    Component: Shell,
    children: [
      { name: "main", index: true, Component: (_props: ScreenViewProps<void>): ReactNode => <text>主屏</text> },
    ],
  },
] as const satisfies readonly RouteObject[];

const SIZE = { cols: 40, rows: 6 };

beforeEach(() => {
  TRAIL.length = 0;
});

describe("站在哪一屏", () => {
  test("open：进那一屏，参数原样到（默认那一屏在栈底）", async () => {
    await renderFrame(<RouterProvider routes={OPEN_ONLY} />, SIZE);
    expect(TRAIL).toEqual(["main", "pick:一,二"]);
  });

  test("back：回默认那一屏", async () => {
    await renderFrame(<RouterProvider routes={OPEN_BACK} />, SIZE);
    expect(TRAIL).toEqual(["main", "pick", "main"]);
  });

  test("back：在默认那一屏上什么都不做（不弹穿栈底）", async () => {
    await renderFrame(<RouterProvider routes={BACK_AT_BOTTOM} />, SIZE);
    expect(TRAIL).toEqual(["main"]);
  });

  test("replace：换掉当前那一屏，不压栈（back 落回默认那一屏，不是被换掉的那一屏）", async () => {
    await renderFrame(<RouterProvider routes={REPLACE_THEN_BACK} />, SIZE);
    expect(TRAIL).toEqual(["main", "pick", "about", "main"]);
  });

  test("布局 + ScreenOutlet：壳与默认那一屏都画出来（静态，读帧是准的）", async () => {
    const text = textOf(await renderFrame(<RouterProvider routes={STATIC} />, SIZE));
    expect(text).toContain("壳");
    expect(text).toContain("主屏");
  });

  test("provider 外面用：当场炸（错误画进帧里，不静默降级）", async () => {
    function Bare(): ReactNode {
      useRouter();
      return <text>不该画出来</text>;
    }
    const text = textOf(await renderFrame(<Bare />, { cols: 70, rows: 4 }));
    expect(text).toContain("useRouter 必须在 RouterProvider 里面用");
  });
});

// ── 表本身：摊平与 fail-closed ────────────────────────────────────
const route = (name: string, index?: true): ScreenRoute<void> => ({
  name,
  ...(index === undefined ? {} : { index }),
  Component: () => null,
});
const layoutOf = (children: readonly RouteObject[]): LayoutRoute => ({ Component: () => null, children });

describe("indexRoutes", () => {
  test("布局里的屏也查得到，链是外→内", () => {
    const index = indexRoutes([layoutOf([layoutOf([route("main", true), route("pick")]), route("help")])]);
    expect(Object.keys(index.byName).sort()).toEqual(["help", "main", "pick"]);
    expect(index.byName["main"]?.route.name).toBe("main");
    expect(index.byName["pick"]?.chain).toHaveLength(2);
    expect(index.byName["help"]?.chain).toHaveLength(1);
    expect(index.index).toBe("main");
  });

  test("屏名重复：炸", () => {
    expect(() => indexRoutes([layoutOf([route("main", true), route("main")])])).toThrow("屏名重复");
  });

  test("默认那一屏不是正好一个：炸", () => {
    expect(() => indexRoutes([layoutOf([route("main", true), route("pick", true)])])).toThrow("只能有一个");
    expect(() => indexRoutes([layoutOf([route("main"), route("pick")])])).toThrow("没有默认那一屏");
  });
});
