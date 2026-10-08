/** @jsxImportSource @opentui/react */
/**
 * 命令总线：**把按键重映射成"某件事发生了"**，并把它交给接这件事的那个组件。
 * 整个模块就是这一件事，所以它有三半，都在这一个目录里：
 *
 *   · `commands.ts` —— **表**：一份 yaml 进来，认得的命令（名字 / 键 / 一句话 / 提示）出去；
 *   · `keys.ts` —— **词表**：opentui 的按键事件归一化成一种写法（`ctrl+b` / `enter` / `打字`）；
 *   · 这个文件 —— **收口**：唯一的按键监听（按键 → 查表 → 问谁接）与订阅（谁接就挂上来）。
 *
 * **键盘只在这一处收**：别处再也拿不到按键（`useKeys` 那种旁路没有了）—— 所以"界面认领的键"必然
 * 来自那张表，写进表里的键也必然会有人按到。**认领的键吃掉**（`preventDefault`）：opentui 的派发是
 * 全局监听先过、焦点里那个可编辑件后过，看到 `defaultPrevented` 就不动手 —— 不然 `ctrl+b` 会既要
 * 拿去分叉、又被输入框当成"光标左移"。没认领的键（表里没有，或没人接）原样落到焦点件上，所以打字、
 * 退格、左右移动仍然是它的。
 *
 * **一条命令只跑一个**：`ask` 从队尾往回问第一个接的人（`registry.ts`）—— 谁后挂上来谁先被问。
 * 于是"同一件事有两份实现"在结构上不可能，而 `esc` 收的正是最后出现的那一层。
 *
 * **"接命令"这件事不在这里**：这一面只给原语（`useBus`：`subscribe` / `changed` / `ask` / `live`），
 * 把"什么时候挂、什么时候摘"留给接的人。那件事要问两样东西：**我这一层在不在**（应用自己的条件）
 * 与**我这一屏是不是被盖住了**（路由的激活，见 `router.ts` 的 `onActivated`）—— 两样都只有调用点
 * 知道，所以合成那一下写在**应用**那一边（`hooks/commands.ts` 的 `useCommand`）。于是命令模块
 * 不认识路由模块，路由模块也不认识命令模块。
 *
 * **次序 = 出现的次序**：订阅挂上来就排在队尾，`ask` 从队尾往回问第一个接的人 —— 所以"这一层刚
 * 出现"与"它排在最后"是同一件事（P0 §1 决策 4）。摘掉一层再挂回来，它自然又回到队尾。
 *
 * **`live(id)` 与 `ask` 共用同一个判据**：谁挂着谁就有接的人 —— 所以"键行写着的键"与
 * "按下去真的会不会动"不可能对不上。
 *
 * 变因：按键怎么收口、一套订阅原语长什么样。
 */
import { useKeyboard } from "@opentui/react";
import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Commands } from "./commands.ts";
import { normalizeKey } from "./keys.ts";
import { createRegistry } from "./registry.ts";
import type { CommandBus, Handling } from "./registry.ts";

export type { CommandBus } from "./registry.ts";

export interface CommandBusProps {
  /** 认得的命令（从 yaml 建的一份表）—— 装配那里建一次，整棵树共用这一份。 */
  readonly table: Commands;
  readonly children: ReactNode;
}

/** 总线本体：问一条命令、看它有没有人接、挂上去、以及订阅增减之后喊那一声。 */
export interface Bus extends CommandBus {
  /** 挂一条订阅；返回摘掉它的函数。**位置 = 挂上来的时刻**（队尾，所以后出现的先被问）。 */
  readonly subscribe: (pattern: string, handling: Handling) => () => void;
  /** 订阅增减之后喊一声：读 `live()` 的那些人（键行）要重画。 */
  readonly changed: () => void;
}

interface Internals {
  readonly table: Commands;
  readonly bus: Bus;
}

const BusContext = createContext<Internals | null>(null);

export function CommandBusProvider({ table, children }: CommandBusProps): ReactNode {
  const registry = useMemo(() => createRegistry(), []);
  // 订阅增减很稀有（一次按键改变"哪一层在"），所以这里用一版计数器让读 `live()` 的人重画就够了。
  const [version, setVersion] = useState(0);
  const internals = useMemo<Internals>(
    () => ({
      table,
      bus: {
        ask: (id, arg) => registry.ask(id, arg),
        live: (id) => registry.live(id),
        subscribe: (pattern, handling) => registry.subscribe(pattern, handling),
        changed: () => setVersion((current) => current + 1),
      },
    }),
    [registry, table],
  );
  // 上下文的值每次都换一个（`version` 一变就换）：读 `live()` 的那些人（键行）才会重画。
  // **但 `bus` 本身保持同一个身份**：订阅那一层把 `bus` 写进依赖（`hooks/commands.ts`），
  // 每次重画换一个身份就会变成"挂上 → changed → 重画 → 身份变了 → 摘掉再挂"的自激。
  // 要重画的是这个上下文值，不是 bus 的身份。
  const value = useMemo<Internals>(() => ({ ...internals }), [internals, version]);

  // 界面唯一的按键监听：按键 → 归一化 → 查表 → 问谁接。接住了就吃掉这个键。
  useKeyboard((event) => {
    const key = normalizeKey(event);
    if (key === null) return;
    const hit = table.byKey(key);
    if (hit === undefined) return;
    if (registry.ask(hit.command.id, hit.binding.arg)) event.preventDefault();
  });

  return <BusContext.Provider value={value}>{children}</BusContext.Provider>;
}

function useInternals(where: string): Internals {
  const internals = useContext(BusContext);
  if (internals === null) throw new Error(`${where} 必须在 CommandBusProvider 里面用`);
  return internals;
}

/**
 * 总线本体：**只有"接命令"的那个口（和应用里的 `useCommand`、示例）才用它**。
 *
 * "什么时候挂、什么时候摘"由接的人自己决定 —— 应用里那件事写在一处
 * （`packages/terminal/src/hooks/commands.ts`），它还要问路由"这一屏是不是被盖住了"。
 */
export function useBus(): Bus {
  return useInternals("useBus").bus;
}

/** 认得的那些命令（命令名单、键位表、键行的提示都要读它）。 */
export function useCommands(): Commands {
  return useInternals("useCommands").table;
}
