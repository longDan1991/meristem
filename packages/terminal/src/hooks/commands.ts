/**
 * 接一条命令：**把"什么时候挂、什么时候摘"补齐**（`@meristem/tui` 那一面只给原语）。
 *
 * 两样东西决定这一下挂不挂：
 *   · **这一层在不在眼前**（`active`，调用点自己的条件）—— 比如"草稿以 `/` 开头"、"档不是 ①"；
 *   · **这一屏在不在眼前**（路由的 `onActivated`）—— 屏不卸载了，被盖住的那一屏还在树上，
 *     所以"挂载"不再等于"出现"（见 `@meristem/tui` 的 `router.ts`）。
 *
 * 两样都只有调用点知道，所以合成写在**应用这一层**：命令模块因此不认识路由模块，路由模块也不认识
 * 命令模块，两边各自只认识自己那半。**次序 = 出现的次序**那条照旧成立：挂上来排在队尾，被盖住
 * 时摘掉、回来时重挂 —— 队尾因此总是"刚出现的这一层"（P0 §1 决策 4 的 `esc`）。
 *
 * 变因：一套订阅原语怎么变成"接一条命令"。
 */
import { onActivated, useBus } from "@meristem/tui";
import type { Handling } from "@meristem/tui";
import { useRef } from "react";

export function useCommand(pattern: string, handling: Handling, active = true): void {
  const { subscribe, changed } = useBus();
  const latest = useRef(handling);
  latest.current = handling;
  onActivated(() => {
    if (!active) return;
    const off = subscribe(pattern, (id, arg) => latest.current(id, arg));
    changed();
    return () => {
      off();
      changed();
    };
  }, [subscribe, changed, pattern, active]);
}
