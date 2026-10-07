/**
 * 一屏、一层布局，以及"从表里长出来的类型"。
 *
 * 表和 web 路由一个形状：**一个数组**，里面是路由对象。一屏有**名字**（导航按名字进），可以被一层
 * **布局**包着；布局没有名字 —— 它不是一次导航，只画"不随屏变的那部分"（壳），里面用
 * `ScreenOutlet()` 给屏留位（web 的 `<Outlet/>`）。
 *
 * **没有"主屏"这回事**：默认那一屏就是标了 `index: true` 的那一屏（web 里就是 `"/"` 对应的页面）。
 * 进来时站在它上面，`back()` 回到它，所以 `current` 永远不是 `null`。
 *
 * 参数形状不用另写一份类型表：名字与参数类型都从这张数组上长出来（`Names` / `ParamsOf`）。
 *
 * 变因：一屏怎么写、一层布局怎么写、一张表能推出哪些类型。
 */
import type { ReactNode } from "react";

/** 一屏拿到的两个 props：它要的参数 + 回上一层那一下。 */
export interface ScreenViewProps<P> {
  readonly params: P;
  /** 回上一层；已经在最底下那一屏时什么都不做。 */
  readonly back: () => void;
}

/** 一屏：有名字，`open` 按名字进。 */
export interface ScreenRoute<P = void> {
  readonly name: string;
  /** 默认那一屏（web 的 `"/"`）：一条表里正好一个，且它不吃参数。 */
  readonly index?: true;
  /**
   * 一个**组件**，不是"返回元素的函数"：屏里要用 hook（键、局部状态），所以必须由 React
   * 挂成自己的元素（`createElement`），直接调用函数等于在 React 之外跑。
   *
   * **每一屏都要把参数类型写出来**：不吃参数就写 `ScreenViewProps<void>`。不写（连 props 都没有）
   * 的话 `open` 会以为它要一个 `unknown` 参数 —— 因为"没有参数"这件事在类型上读不出来。
   */
  readonly Component: (props: ScreenViewProps<P>) => ReactNode;
  /**
   * 这一屏**自带的一小块**：布局替它摆位置，摆哪儿由布局定。**不吃 props** —— 它要什么自己从
   * 状态里取（`useScreen` / 命令表），布局只负责位置。
   *
   * 为什么有这么个东西：**不是每一屏都需要同一些零件**。比如输入行只有"说话"的那一屏需要，
   * 其余屏（键位表、挑角色…）在那儿放的是它自己的键；所以它是屏自带的，不是壳的固定件。
   */
  readonly Composer?: () => ReactNode;
}

/** 一层布局：没有名字，只画壳；`children` 是画在它里面的路由对象。 */
export interface LayoutRoute {
  readonly Component: () => ReactNode;
  readonly children: readonly RouteObject[];
}

/** 数组元素的共同上界：各屏参数形状不同，所以是 `never` —— 它给 `satisfies` 用，不给屏用。 */
export type AnyScreen = ScreenRoute<never>;

/** 表里的一项能是什么：一屏，或一层布局。 */
export type RouteObject = AnyScreen | LayoutRoute;

/** 表里**所有**的屏：把布局里的 `children` 摊平（名字与参数形状都从这儿长出来）。 */
export type ScreensOf<R extends readonly RouteObject[]> = R[number] extends infer E
  ? E extends LayoutRoute
    ? ScreensOf<E["children"]>
    : E extends AnyScreen
      ? E
      : never
  : never;

/** 表里所有屏的名字。 */
export type Names<R extends readonly RouteObject[]> = ScreensOf<R>["name"];

/** 某个名字那一屏的参数形状。 */
export type ParamsOf<R extends readonly RouteObject[], N extends Names<R>> = ScreensOf<R> extends infer S
  ? S extends { readonly name: N; readonly Component: (props: ScreenViewProps<infer P>) => ReactNode }
    ? P
    : never
  : never;

/** 当前那一屏；判别联合：`name` 一收窄，`params` 跟着窄。 */
export type ScreenRef<R extends readonly RouteObject[]> = {
  [N in Names<R>]: { readonly name: N; readonly params: ParamsOf<R, N> };
}[Names<R>];
