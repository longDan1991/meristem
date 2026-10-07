/**
 * 表 → 查表用的一层索引：名字 → 那一屏（连同包着它的那些布局，外 → 内），以及默认那一屏是谁。
 * 一次装配算一次，运行时就查它。
 *
 * 三条 fail-closed（照 `@meristem/harness` 装载角色那条规矩：错了当场炸，不降级）：
 *   · 屏名重复；
 *   · 默认那一屏（`index: true`）不是正好一个；
 *   · 表里出现了 `byName` 之外的名字（只可能发生在拿两张表的 ref 混用的时候，见 `router.ts`）。
 *
 * 变因：名字的查找、布局链、默认那一屏。
 */
import type { AnyScreen, LayoutRoute, RouteObject } from "./route.ts";

/** 一屏在表里的位置：它自己 + 包着它的那些布局（外 → 内）。 */
export interface Match {
  readonly route: AnyScreen;
  readonly chain: readonly LayoutRoute[];
}

export interface RouteIndex {
  readonly byName: Record<string, Match>;
  /** 默认那一屏的名字（`index: true` 那一屏）。 */
  readonly index: string;
}

export function indexRoutes(routes: readonly RouteObject[]): RouteIndex {
  // 先摊平（布局里的 children 也走一遍），摊平时记住链 —— 之后查表就只是一次取值。
  const flat: Match[] = [];
  const walk = (entries: readonly RouteObject[], chain: readonly LayoutRoute[]): void => {
    for (const entry of entries) {
      if ("children" in entry) walk(entry.children, [...chain, entry]);
      else flat.push({ route: entry, chain });
    }
  };
  walk(routes, []);

  const byName: Record<string, Match> = {};
  let index: string | null = null;
  for (const found of flat) {
    const name = found.route.name;
    if (Object.hasOwn(byName, name)) throw new Error(`屏名重复：${name} 出现了两次`);
    byName[name] = found;
    if (found.route.index === true) {
      if (index !== null) throw new Error(`默认那一屏（index: true）只能有一个：${index} 与 ${name} 都写了`);
      index = name;
    }
  }
  if (index === null) throw new Error('表里没有默认那一屏：给某一屏写上 index: true（就是 web 里的 "/"）');

  return { byName, index };
}
