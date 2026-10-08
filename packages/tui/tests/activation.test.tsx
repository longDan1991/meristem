/** @jsxImportSource @opentui/react */
/**
 * 路由的另一半：**屏不卸载，只有"在不在眼前"在变**。
 *
 * 四条要钉住（它们就是这次加缓存的全部理由与全部代价）：
 *   ① 被盖住的那一屏**实例还在**（回来时是原来那个，状态没丢）；
 *   ② 被盖住的那一屏**不再接键**（`onActivated` 的收尾把订阅摘了 —— 不摘的话 `esc` 会先撞上它）；
 *   ③ `onActivated` / `onDeactivated` 各自什么时候跑（"卸载"不算"被盖住"）；
 *   ④ 弹栈才算销毁（`replace` 换掉的那一项、`back` 弹掉的那一项真的卸载）。
 *
 * 按键 → 查表 → 问谁接这条路走真渲染器与真按键（与 `screens.test.tsx` 同一个理由：装载期看不到
 * "谁接了这条命令"的全貌）。表用命令模块自带的那一份用例表（`app.*` / `demo.*`）。
 */
import { join } from "node:path";
import { expect, test } from "bun:test";
import { act, useState } from "react";
import type { ReactNode } from "react";
import type { TestRendererSetup } from "@opentui/core/testing";
import { testRender } from "@opentui/react/test-utils";
import { CommandBusProvider, useBus } from "../src/command/bus.tsx";
import { Commands } from "../src/command/commands.ts";
import { onActivated, onDeactivated, RouterProvider, ScreenOutlet, useRouter } from "../src/router/router.ts";
import type { RouteObject, ScreenViewProps } from "../src/router/route.ts";

const TABLE = new Commands(join(import.meta.dir, "../src/command/example/commands.yaml"), ["app", "demo"]);

/** 脚印：谁露头 / 谁退到后面 / 谁真的卸载了。 */
const LOG: string[] = [];
/** 实例化的次数：屏不卸载，所以它只该涨一次。 */
const MOUNTS = { main: 0, other: 0 };

/**
 * 接一条命令（原语那一层）：应用里的 `useCommand` 就是在这个形状上加"这一层在不在"。
 * `bus` 写进依赖是安全的 —— 它的身份跨重画不变（见 `command/bus.tsx`）。
 */
function useRaw(pattern: string, handling: (id: string) => void): void {
  const bus = useBus();
  onActivated(() => {
    const off = bus.subscribe(pattern, (id) => handling(id));
    bus.changed();
    return () => {
      off();
      bus.changed();
    };
  }, [bus, pattern]);
}

function Main(_props: ScreenViewProps<void>): ReactNode {
  const router = useRouter<typeof ROUTES>();
  const [count, setCount] = useState(() => {
    MOUNTS.main += 1;
    return 0;
  });
  onActivated(() => {
    LOG.push("main:on");
    return () => LOG.push("main:off");
  }, []);
  onDeactivated(() => LOG.push("main:idle"), []);
  useRaw("demo.outer", () => router.open("other"));
  useRaw("demo.inner", () => router.replace("other"));
  useRaw("app.close", () => {
    LOG.push("main:bump");
    setCount((current) => current + 1);
  });
  return <text>{`count=${String(count)}`}</text>;
}

function Other(_props: ScreenViewProps<void>): ReactNode {
  const router = useRouter<typeof ROUTES>();
  useState(() => {
    MOUNTS.other += 1;
    return 0;
  });
  onActivated(() => {
    LOG.push("other:on");
    return () => LOG.push("other:off");
  }, []);
  onDeactivated(() => LOG.push("other:idle"), []);
  useRaw("app.close", () => router.back());
  return <text>另一屏</text>;
}

/** 壳：只给屏留一格（与真应用那一层同一个形状）。 */
function Shell(): ReactNode {
  return <ScreenOutlet />;
}

const ROUTES = [
  {
    Component: Shell,
    children: [
      { name: "main", index: true, Component: Main },
      { name: "other", Component: Other },
    ],
  },
] as const satisfies readonly RouteObject[];

async function settle(setup: TestRendererSetup): Promise<void> {
  for (let round = 0; round < 6; round += 1) {
    await Bun.sleep(10);
    await setup.renderOnce();
  }
}

async function press(setup: TestRendererSetup, key: string, modifiers?: Record<string, boolean>): Promise<void> {
  await act(async () => {
    setup.mockInput.pressKey(key as never, modifiers as never);
  });
  await settle(setup);
}

async function escape(setup: TestRendererSetup): Promise<void> {
  await act(async () => {
    setup.mockInput.pressEscape();
  });
  await settle(setup);
}

async function start(): Promise<TestRendererSetup> {
  LOG.length = 0;
  MOUNTS.main = 0;
  MOUNTS.other = 0;
  const setup = await testRender(
    <CommandBusProvider table={TABLE}>
      <RouterProvider routes={ROUTES} />
    </CommandBusProvider>,
    { width: 40, height: 8, exitOnCtrlC: false },
  );
  await settle(setup);
  return setup;
}

test("被盖住的屏：实例留着、键不再接；露头时重新接上", async () => {
  const setup = await start();
  expect(LOG).toEqual(["main:on"]);
  expect(setup.captureCharFrame()).toContain("count=0");

  // `esc` 这一下归主屏（它是眼前那一层里唯一接 `app.close` 的）。
  await escape(setup);
  expect(LOG).toEqual(["main:on", "main:bump"]);
  expect(setup.captureCharFrame()).toContain("count=1");

  // 压一屏：主屏退到后面（收尾跑一遍，`onDeactivated` 也跑），新的一屏露头。实例没换。
  await press(setup, "o", { meta: true });
  expect(LOG).toEqual(["main:on", "main:bump", "main:off", "main:idle", "other:on"]);
  expect(MOUNTS.main).toBe(1);
  expect(setup.captureCharFrame()).toContain("另一屏");
  expect(setup.captureCharFrame()).not.toContain("count="); // 藏起来 = 不画

  // 被盖住的主屏不再接它的命令：这一条键没人接，什么都不会发生。
  await press(setup, "i", { meta: true });
  expect(LOG).toEqual(["main:on", "main:bump", "main:off", "main:idle", "other:on"]);

  // 弹回去：弹掉的那一屏真的卸载（它露着头，所以只有 `onActivated` 的收尾，没有 `onDeactivated`），
  // 主屏又露头 —— 还是原来那个实例，`count` 还在。
  await escape(setup);
  expect(LOG).toEqual(["main:on", "main:bump", "main:off", "main:idle", "other:on", "other:off", "main:on"]);
  expect(MOUNTS.main).toBe(1);
  expect(setup.captureCharFrame()).toContain("count=1");

  await act(async () => {
    setup.renderer.destroy();
  });
});

test("replace：被换掉的那一项真的卸载（只有弹栈与替换才算销毁）", async () => {
  const setup = await start();
  await press(setup, "i", { meta: true }); // 主屏自己接的：`demo.inner` → replace("other")
  expect(LOG).toEqual(["main:on", "main:off", "other:on"]); // 主屏卸载（露着头地卸载，所以没有 `main:idle`）
  expect(MOUNTS.other).toBe(1);
  expect(setup.captureCharFrame()).toContain("另一屏");
  await act(async () => {
    setup.renderer.destroy();
  });
});
