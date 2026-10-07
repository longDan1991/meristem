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
 * **`active` = 我这儿这会儿有没有这一层**：订阅只在 `active` 为真时挂着（翻转时才挂 / 摘），
 * 所以**挂上来的时刻就是那层出现的时刻** —— 次序由此自动等于"出现的次序"（P0 §1 决策 4）。
 * 别处一般不写 `active`（它作用的东西一直在）；"有没有可做的事"由处理器自己说清
 * （比如分叉在草稿为空时写一句"要有那句新话"，而不是让键静默失效）。
 *
 * **`live(id)` 与 `ask` 共用同一个判据**：谁挂上来谁就有接的人 —— 所以"底下那行写着的键"与
 * "按下去真的会不会动"不可能对不上。
 *
 * 变因：按键怎么收口、订阅怎么跟组件生命周期绑在一起。
 */
import { useKeyboard } from "@opentui/react";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
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

interface Internals {
  readonly table: Commands;
  readonly bus: CommandBus;
  readonly subscribe: (pattern: string, handling: Handling) => () => void;
  /** 订阅增减之后喊一声：读 `live()` 的那些人（底下那行）要重画。 */
  readonly changed: () => void;
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
      },
      subscribe: (pattern, handling) => registry.subscribe(pattern, handling),
      changed: () => setVersion((current) => current + 1),
    }),
    [registry, table],
  );
  // 上下文的值每次都换一个（`version` 一变就换）：底下那行这类只读 `live()` 的消费者才会重画。
  const value = useMemo<Internals>(() => ({ ...internals, bus: { ...internals.bus } }), [internals, version]);

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
 * 我接这几条（模式可以是一条，也可以是整层 `screen.*`）。
 *
 * `handling` 每次渲染都是新的闭包（它读最新的状态），但**订阅不重挂** —— 挂在一只只读盒子里，
 * 次序只在 `active` 真的翻转时才变。这就是"次序 = 出现的次序"能成立的原因。
 */
export function useCommand(pattern: string, handling: Handling, active = true): void {
  const { subscribe, changed } = useInternals("useCommand");
  const latest = useRef(handling);
  latest.current = handling;
  useEffect(() => {
    if (!active) return;
    const off = subscribe(pattern, (id, arg) => latest.current(id, arg));
    changed();
    return () => {
      off();
      changed();
    };
  }, [subscribe, changed, pattern, active]);
}

/** 问一次（按一个键的那一刻用）／问"有接的人吗"（底下那行用）。 */
export function useCommandBus(): CommandBus {
  return useInternals("useCommandBus").bus;
}

/** 认得的那些命令（命令名单、键位表、底下那行的提示都要读它）。 */
export function useCommands(): Commands {
  return useInternals("useCommands").table;
}
