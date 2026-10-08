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
 * **屏不卸载，只有"是不是在最上面"在变**（照 React Navigation 与 Vue 的 `<KeepAlive>`）：栈里每一项
 * 都留在树上，被盖住的那几项 `visible` 为假（布局引擎的 `display:none`：不参与布局、不画、
 * 顺带把里面的焦点也放掉）。所以**进屏再回来，那一屏原来什么样还是什么样** ——
 * `docs/prototype/ours/P0/06-switching.md` 最后一行"回来时是原档、原侧边态"靠的就是这个，
 * 而不是靠把状态提到屏外面。**弹栈才算销毁**（`back` / `replace` 换掉的那一项真的卸载）：
 * 于是缓存的身份就是**栈项自己**，不需要 `include` / `exclude` / `max`（那是 Vue 那种"连弹掉
 * 也留着"的缓存才要的东西）。
 *
 * 代价是"挂载"不再等于"出现在眼前"：被盖住的那一屏，它的 effect 还活着。所以这一层另给两个
 * 钩子 —— `onActivated` / `onDeactivated`（Vue 的 `onActivated` / `onDeactivated`，
 * React Navigation 的 `useFocusEffect`）—— 把"进入 / 离开"从"挂载 / 卸载"里拆出来。
 * **订阅（命令、作业流、焦点）跟着"在不在眼前"走，不跟着"在不在树上"走。**
 *
 * 变因：当前那一屏（栈）、布局链怎么套、以及"屏幕生死"的另一半（谁在眼前）。
 */
import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { Names, ParamsOf, RouteObject, ScreenRef, ScreenViewProps } from "./route.ts";
import { indexRoutes } from "./table.ts";
import type { RouteIndex } from "./table.ts";

export interface Router<R extends readonly RouteObject[]> {
  /** 当前那一屏：默认那一屏在栈底，所以永远有（不是 `null`）。 */
  readonly current: ScreenRef<R>;
  /** 现在压着几层屏（`1` = 就在默认那一屏上）。谁要问"还回得上去吗"（`esc` 收掉眼前这一层）看它。 */
  readonly depth: number;
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

/** 栈里的一项 = 站着的那一屏 + 它自己的号（号只当 React 兄弟之间的 `key`：栈项自己就是身份）。 */
interface Entry<R extends readonly RouteObject[]> {
  readonly id: number;
  readonly ref: ScreenRef<R>;
}

export function RouterProvider<R extends readonly RouteObject[]>(props: RouterProviderProps<R>): ReactNode {
  const index = useMemo(() => indexRoutes(props.routes), [props.routes]);
  // 默认那一屏的 ref：名字是运行时查出来的（`index: true` 那一屏），表保证了它与"不吃参数"配对。
  const initial = useMemo(() => ({ name: index.index, params: undefined }) as ScreenRef<R>, [index]);
  const [stack, setStack] = useState<readonly Entry<R>[]>(() => [{ id: 0, ref: initial }]);
  const sequence = useRef(1);

  /** 新栈项：号只增不减 —— 谁进栈谁拿一个新号，弹掉那一项连它的号一起没了。 */
  const mint = useCallback(<N extends Names<R>>(name: N, params: ParamsOf<R, N>): Entry<R> => {
    const id = sequence.current;
    sequence.current += 1;
    return { id, ref: refOf<R, N>(name, params) };
  }, []);

  const back = useCallback(() => setStack((now) => (now.length > 1 ? now.slice(0, -1) : now)), []);

  const open = useCallback(
    <N extends Names<R>>(name: N, ...args: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]): void => {
      // `[]` 在类型上没有第 0 项，所以取这一下；签名已经保证有参屏一定有值。
      const params = args[0] as ParamsOf<R, N>;
      setStack((now) => [...now, mint(name, params)]);
    },
    [mint],
  );

  const replace = useCallback(
    <N extends Names<R>>(name: N, ...args: [ParamsOf<R, N>] extends [void] ? [] : [params: ParamsOf<R, N>]): void => {
      const params = args[0] as ParamsOf<R, N>;
      setStack((now) => [...now.slice(0, -1), mint(name, params)]);
    },
    [mint],
  );

  const current = stack[stack.length - 1] ?? { id: 0, ref: initial };
  const depth = stack.length;
  const node = useMemo(() => renderStack(index, stack, back), [index, stack, back]);
  const router = useMemo<Router<R>>(
    () => ({ current: current.ref, depth, open, replace, back }),
    [current, depth, open, replace, back],
  );

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

/**
 * 这一层**在不在眼前**：栈里最上面那一项为真，被它盖住的那些为假。不在任何屏里的（壳、屏之上的
 * provider）也是真 —— "被盖住"只可能是"屏被屏盖住"。
 *
 * 它只在这一个文件里流转：`onActivated` / `onDeactivated` 是它唯一的出口，所以"谁被盖住了"这件事
 * 不外泄（命令模块不认识路由，路由也不认识命令模块）。
 */
const ActivationContext = createContext(true);

/**
 * 这一层露头时跑（挂载时也跑一次）；**返回的那个函数在"被盖住"和卸载时跑**。
 *
 * 就是 React Navigation 的 `useFocusEffect` / Vue 的 `onActivated`：一次订阅的寿命正好是
 * "函数体一进一出"，所以被盖住的那一屏不再接键、不再跟在跑的作业 —— 回到眼前时自己再挂上。
 * `deps` 与 `useEffect` 同义（不给 = 每次渲染都重来）。
 */
export function onActivated(effect: () => void | (() => void), deps?: readonly unknown[]): void {
  const activated = useContext(ActivationContext);
  useEffect(() => {
    if (!activated) return;
    return effect();
  }, deps === undefined ? undefined : [...deps, activated]);
}

/**
 * 只有收尾、没有配对启动的那件事（**被盖住时**跑，`deps` 同 `useEffect`）。
 *
 * 卸载**不算**被盖住（那是"这一屏没了"）—— 那种收尾写在 `onActivated` 的返回函数里，
 * 所以两件事各自只有一个去处。
 */
export function onDeactivated(effect: () => void, deps?: readonly unknown[]): void {
  const activated = useContext(ActivationContext);
  useEffect(() => {
    if (activated) return;
    effect();
  }, deps === undefined ? undefined : [...deps, activated]);
}

/** 名字与参数 → "当前这一屏"。写在返回位置：只有返回位置能确认"这个名字配这个参数"（对象字面量当实参不行）。 */
function refOf<R extends readonly RouteObject[], N extends Names<R>>(name: N, params: ParamsOf<R, N>): ScreenRef<R> {
  return { name, params };
}

/**
 * 把栈画出来：**每一项自己一条布局链**（布局只是那一项的壳），只有最上面那一项在眼前，
 * 被它盖住的那些留着但 `visible` 为假 —— 连同它们的壳一起藏，所以活着的壳永远只有一份。
 *
 * **顺序 = 栈的顺序**（栈底在前）：同一次提交里新挂上来的那一项排在后面，它的 effect 也最后跑 ——
 * "挂上来的时刻就是它出现的时刻"这条在最上面那一项上照旧成立。
 */
function renderStack<R extends readonly RouteObject[]>(
  index: RouteIndex,
  stack: readonly Entry<R>[],
  back: () => void,
): ReactNode {
  const top = stack.length - 1;
  return stack.map((entry, position) =>
    createElement(
      "box",
      { key: entry.id, width: "100%", height: "100%", visible: position === top },
      createElement(ActivationContext.Provider, { value: position === top }, renderEntry(index, entry.ref, back)),
    ),
  );
}

/**
 * 把一屏画出来：布局链从外往内套，屏画在最里面那个 `ScreenOutlet()` 上。
 * 名字这里按 `string` 查 —— 表已经在装配时查好了默认屏，运行时只可能拿到表里的名字（混用两张表的 ref 会当场炸）。
 */
function renderEntry<R extends readonly RouteObject[]>(
  index: RouteIndex,
  ref: ScreenRef<R>,
  back: () => void,
): ReactNode {
  const match = index.byName[ref.name];
  if (match === undefined) throw new Error(`表里没有这一屏：${ref.name}`);
  // 一处 `as`：参数形状只有 `open` 那一刻是精确的，运行时拿到的是"存在类型"。
  const Component = match.route.Component as (props: ScreenViewProps<unknown>) => ReactNode;
  return match.chain.reduceRight<ReactNode>(
    (inner, layout) => createElement(OutletContext.Provider, { value: inner }, createElement(layout.Component)),
    createElement(Component, { params: ref.params, back }),
  );
}
