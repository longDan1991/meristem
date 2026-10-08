/** @jsxImportSource @opentui/react */
/**
 * 命令模块的**用例**：一份能跑的样例，回答"表从哪来、谁监听键盘、订阅怎么写、次序怎么定"。
 * 好看那一档不在这里（那是 `dev/visual/` 的事），要验的是**接法**。
 *
 * 五处要点：
 *   ① 表从一个**路径**建出来（`new Commands(路径, 作用面词表)`）：同一个进程建一次，整棵树共用这一份。
 *      作用面（id 的第一段）是**应用自己的词** —— 这一份用例用的是 `app` / `demo`，模块只负责卡住它。
 *   ② **没有任何组件碰按键**：`CommandBusProvider` 是唯一监听的地方（按键 → 查表 → 问谁接）。
 *      没被认领的键（`j` / 退格 / 中文）原样落到焦点里的输入件上 —— 这里没有输入件，所以什么也不发生。
 *   ③ **谁作用谁订阅，而合成那一下写在调用点**：这一面只给原语（`useBus`），`useLayer`（本文件里
 *      那十几行）把"什么时候挂、什么时候摘"补上。`active` 就是"这一层在不在"：只在它为真时挂着，
 *      **翻转时才重挂** —— 所以挂上来的时刻就是那层出现的时刻，次序由此恒等于出现的次序。
 *      （真应用里那一层写在 `packages/terminal/src/hooks/commands.ts`：它还要问路由"这一屏被盖住了吗"。）
 *   ④ **一条命令只跑一个，从队尾往回问**：这里的 `esc` 有三层——内层、外层、壳上那条"退屏"
 *      （最后一条要真压了一屏才有）。**后出现的那层排在队尾**，所以先按 `alt+o` 再按 `alt+i`
 *      时，`esc` 收的是内层；反过来按，收的就是外层。
 *   ⑤ 通配（`demo.*`）让**一条**订阅接住整层，处理器拿到的是**具体的 id**；
 *      "这会儿能按什么"是问 `live(id)` 问出来的 —— 与"按下去会不会动"同一个判据，所以不可能对不上。
 *
 * 跑起来看：`bun run packages/tui/dev/preview/frame.ts packages/tui/src/command/example/two-layers.tsx --wireframe`
 */
import { join } from "node:path";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { CommandBusProvider, Commands, tone, useBus, useCommands } from "../../index.ts";
import type { CommandBus, Handling } from "../../index.ts";

/** ① 表从路径建：整棵树共用这一份（真实应用建在装配那一层）。作用面词表也是这一份用例自己的。 */
const TABLE = new Commands(join(import.meta.dir, "commands.yaml"), ["app", "demo"]);

/**
 * ③ **接一条命令**：这一面（`bus.tsx`）只给原语，所以"什么时候挂、什么时候摘"写在这儿。
 *
 * 真应用里这一下合成在**应用**那一层（`packages/terminal/src/hooks/commands.ts` 的 `useCommand`），
 * 因为它还要问路由"这一屏被盖住了吗"（`onActivated`）—— 那时屏不卸载，光看挂载/卸载不够。
 * 这一份用例只有一层浮层、不涉及路由，所以按 `active` 挂就够了。
 */
function useLayer(pattern: string, handling: Handling, active = true): void {
  const bus = useBus();
  const latest = useRef(handling);
  latest.current = handling;
  useEffect(() => {
    if (!active) return;
    const off = bus.subscribe(pattern, (id, arg) => latest.current(id, arg));
    bus.changed();
    return () => {
      off();
      bus.changed();
    };
  }, [bus, pattern, active]);
}

/** 一层：它在，就接住 `esc`（`onClose` 是"收掉我"）。 */
function Layer({ what, onClose }: { readonly what: string; readonly onClose: () => void }): ReactNode {
  useLayer("app.close", () => onClose());
  return <text fg={tone.running}>{`▌ ${what}：这一层在 —— 现在 esc 收我`}</text>;
}

/** 外面那一层 + 一个通配订阅（`demo.*`）：两条键都归它，它按**具体的 id** 分辨是谁。 */
function Panel(): ReactNode {
  const [outer, setOuter] = useState(false);
  const [inner, setInner] = useState(false);
  const [notice, setNotice] = useState("");
  const bus = useBus();
  const table = useCommands();

  // ⑤ 一条订阅接住整层；处理器拿得到具体的 id。
  useLayer("demo.*", (id) => {
    setNotice(`有人接了 ✓ ${id}`);
    if (id === "demo.outer") setOuter(true);
    if (id === "demo.inner") setInner(true);
  });
  useLayer("app.quit", () => setNotice("退出：真应用在这里收终端"));

  return (
    <box flexDirection="column" width="100%" paddingX={1}>
      <text fg={tone.accent}>命令模块 · 用例</text>
      <text>{`外层：${outer ? "在" : "不在"} · 内层：${inner ? "在" : "不在"} · 回执：${notice}`}</text>
      {outer ? <Layer what="外层" onClose={() => setOuter(false)} /> : null}
      {inner ? <Layer what="内层" onClose={() => setInner(false)} /> : null}
      <text fg={tone.dim}>alt+o 开外层 · alt+i 开内层 · esc 收一层 · ctrl+c 退出</text>
      <text fg={tone.dim}>{`这会儿能按：${hintsOf(table, bus)}`}</text>
    </box>
  );
}

/** ⑤ "这会儿能按什么"：有 `hint` 又**有人接**的才写 —— 与"按了会不会动"同一个判据。 */
function hintsOf(table: Commands, bus: CommandBus): string {
  const live = table.all.filter((command) => command.hint !== null && bus.live(command.id));
  if (live.length === 0) return "（没有）";
  return live.map((command) => `${command.keys[0]?.key ?? ""} ${command.hint ?? ""}`).join(" · ");
}

/** 装配：表在这里进来一次，provider 自己监听键盘（这一份用例整棵树就是这个元素）。 */
export default (
  <CommandBusProvider table={TABLE}>
    <Panel />
  </CommandBusProvider>
);
