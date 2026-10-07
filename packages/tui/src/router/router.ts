/**
 * 路由：**现在站在哪一屏**，以及进 / 出那两下。
 *
 * 表在**装配**那里进来一次（`RouterProvider` 的 props），provider **自己把当前那一屏画出来** ——
 * 它不吃 children（web 的 `<RouterProvider router={router}/>` 也是这样）。包着这一屏的那些**布局**先画，
 * 布局里用 `ScreenOutlet()` 给屏留位（web 的 `<Outlet/>`）。
 *
 * 借 web 路由的就这几件：**一张表**（数组）、**名字当判别式**、**`index` 那一屏当默认**（就是 `"/"`）、
 * **进屏压栈 / `replace` 换掉当前这一屏 / `back()` 弹栈**、**参数原样透传**，参数形状从表上长出来。
 * 故意不借的：path / loader / 守卫 / 链接 —— 终端的屏是并列的（`docs/prototype/ours/P0/02-screens.md`），
 * 数据各自从自己的门来。
 *
 * 变因：当前那一屏（栈）、布局链怎么套、以及"表进来一次"的装配。
 */
import { createContext, createElement, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Names, ParamsOf, RouteObject, ScreenRef, ScreenViewProps } from "./route.ts";
import { indexRoutes } from "./table.ts";
import type { RouteIndex } from "./table.ts";

export interface Router<R extends readonly RouteObject[]> {
  /** 当前那一屏：默认那一屏在栈底，所以永远有（不是 `null`）。 */
  readonly current: ScreenRef<R>;
  /** 进屏。无参屏一个参数都不要，有参屏必填；名字不在表里过不了编译。 */
  open<N extends Names<R>>(
    name: N,
    ...params: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]
  ): void;
  /** 换掉当前那一屏（不压栈）：位置不动，只是站着的那一层换了另一屏；默认那一屏也能被换掉。 */
  replace<N extends Names<R>>(
    name: N,
    ...params: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]
  ): void;
  /** 回上一层；已经在默认那一屏时什么都不做。 */
  back(): void;
}

export interface RouterProviderProps<R extends readonly RouteObject[]> {
  /** 表：`as const satisfies readonly RouteObject[]` 写成的常量数组。 */
  readonly routes: R;
}

export function RouterProvider<R extends readonly RouteObject[]>(props: RouterProviderProps<R>): ReactNode {
  const index = useMemo(() => indexRoutes(props.routes), [props.routes]);
  // 默认那一屏的 ref：名字是运行时查出来的（`index: true` 那一屏），表保证了它与"不吃参数"配对。
  const initial = useMemo(() => ({ name: index.index, params: undefined }) as ScreenRef<R>, [index]);
  const [stack, setStack] = useState<readonly ScreenRef<R>[]>(() => [initial]);

  const back = useCallback(() => setStack((now) => (now.length > 1 ? now.slice(0, -1) : now)), []);

  const open = useCallback(
    <N extends Names<R>>(name: N, ...args: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]): void => {
      // `[]` 在类型上没有第 0 项，所以取这一下；签名已经保证有参屏一定有值。
      const params = args[0] as ParamsOf<R, N>;
      setStack((now) => [...now, refOf<R, N>(name, params)]);
    },
    [],
  );

  const replace = useCallback(
    <N extends Names<R>>(name: N, ...args: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]): void => {
      const params = args[0] as ParamsOf<R, N>;
      setStack((now) => [...now.slice(0, -1), refOf<R, N>(name, params)]);
    },
    [],
  );

  const current = stack[stack.length - 1] ?? initial;
  const node = useMemo(() => renderScreen(index, current, back), [index, current, back]);
  const router = useMemo<Router<R>>(() => ({ current, open, replace, back }), [current, open, replace, back]);

  return createElement(RouterContext.Provider, { value: router }, node);
}

/** 布局里给屏留位的地方：把当前那一屏画在这儿（web 的 `<Outlet/>`）。 */
export function ScreenOutlet(): ReactNode {
  return useContext(OutletContext);
}

/**
 * 取这一棵树的路由。**不带表** —— 表在装配那里。
 *
 * 类型参数就是这个用途：context 是模块级的，装进去的 `R` 编译器看不见，所以在**调用点**声明一次
 * （`useRouter<typeof SCREENS>()`，或先写一个 `type Screens = typeof SCREENS` 复用）。
 * 前提是取自同一个 `RouterProvider`：一棵树里只有一份表。
 */
export function useRouter<R extends readonly RouteObject[] = RouteObject[]>(): Router<R> {
  const router = useContext(RouterContext);
  if (router === null) throw new Error("useRouter 必须在 RouterProvider 里面用");
  return router as Router<R>;
}

/** 模块级 context：`R` 只有装配那一刻知道（见 `useRouter`）。 */
const RouterContext = createContext<unknown>(null);

/** 布局这一层"往里画什么"。每一层布局各拿一份，所以不用知道自己在第几层。 */
const OutletContext = createContext<ReactNode>(null);

/** 名字与参数 → "当前这一屏"。写在返回位置：只有返回位置能确认"这个名字配这个参数"（对象字面量当实参不行）。 */
function refOf<R extends readonly RouteObject[], N extends Names<R>>(name: N, params: ParamsOf<R, N>): ScreenRef<R> {
  return { name, params };
}

/**
 * 把当前那一屏画出来：布局链从外往内套，屏画在最里面那个 `ScreenOutlet()` 上。
 * 名字这里按 `string` 查 —— 表已经在装配时查好了默认屏，运行时只可能拿到表里的名字（混用两张表的 ref 会当场炸）。
 */
function renderScreen(
  index: RouteIndex,
  current: { readonly name: string; readonly params: unknown },
  back: () => void,
): ReactNode {
  const match = index.byName[current.name];
  if (match === undefined) throw new Error(`表里没有这一屏：${current.name}`);
  // 一处 `as`：参数形状只有 `open` 那一刻是精确的，运行时拿到的是"存在类型"。
  const Component = match.route.Component as (props: ScreenViewProps<unknown>) => ReactNode;
  return match.chain.reduceRight<ReactNode>(
    (inner, layout) => createElement(OutletContext.Provider, { value: inner }, createElement(layout.Component)),
    createElement(Component, { params: current.params, back }),
  );
}
