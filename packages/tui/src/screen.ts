/**
 * 屏幕外壳：**渲染器与终端的创建、还原只此一处**。
 *
 * 变因是"终端形态"：真终端要接管屏幕并差分重画，管道 / CI 里根本没有可重画的屏幕，
 * 只能降级成"每次调用追加一帧文本"。两种形态之外的差别（画什么、怎么排）都在组件与业务里。
 *
 * 状态归 React（`render` 可以反复调用、只做 diff），所以这个外壳自己不记除了"还原过没有"
 * 之外的任何东西 —— 那一个布尔值是为了幂等，不是因为屏幕有状态。
 */
import { createCliRenderer } from "@opentui/core";
import { createTestRenderer } from "@opentui/core/testing";
import { createRoot, flushSync } from "@opentui/react";
import type { Root } from "@opentui/react";
import type { ReactNode } from "react";

export interface Screen {
  /** 画这一屏。TTY 下 React 状态自己驱动后续重画；非真终端下每次调用追加一帧文本。 */
  render(node: ReactNode): void;
  /** 还原终端（幂等）。 */
  restore(): Promise<void>;
}

/** 非真终端（管道 / CI）的尺寸取定值：没有真屏幕可问，帧的输出要可复现。 */
const PIPED_WIDTH = 100;
const PIPED_HEIGHT = 40;

function ttyScreen(root: Root, stop: () => void): Screen {
  let restored = false;
  return {
    render(node) {
      root.render(node);
    },
    async restore() {
      // 幂等：收手动作只能来一次，重复调用是别人的自由。
      if (restored) return;
      restored = true;
      root.unmount();
      stop();
    },
  };
}

/**
 * 降级模式：每帧 flush 出来追加到 stdout（帧之间空一行）。屏幕没有"重画"这回事，
 * 所以这里看见的就是"屏幕内容"本身，一帧不多一帧不少。
 *
 * 这里**必须**用 `flushSync` 包住 render：没有渲染循环推帧，裸调用不会当场提交，
 * 于是 flush 出来的会是还没画过的缓冲区。TTY 那条路相反 —— 那里帧是引擎自己推的。
 */
function pipedScreen(root: Root, flush: () => Promise<void>, capture: () => string, stop: () => void): Screen {
  // 无头渲染器没有帧循环来推提交：`flushSync` 让这一棵树当场落地，不然 flush 出来的是还没画过的缓冲区。
  let restored = false;
  let drawn = false;
  // 一帧 = 渲染 + flush + 落盘，整段串起来：不然连着两次 render 会一起提交，第一帧就丢了。
  let queue: Promise<void> = Promise.resolve();
  return {
    render(node) {
      queue = queue.then(async () => {
        flushSync(() => {
          root.render(node);
        });
        await flush();
        // 帧之间空一行：capture 出来的字符串自己带结尾换行，先去掉再补一次，免得空成两行。
        const frame = capture().replace(/\n+$/, "");
        process.stdout.write(drawn ? `\n${frame}\n` : `${frame}\n`);
        drawn = true;
      });
    },
    async restore() {
      if (restored) return;
      restored = true;
      await queue;
      root.unmount();
      stop();
    },
  };
}

export async function openScreen(): Promise<Screen> {
  if (process.stdout.isTTY === true) {
    const renderer = await createCliRenderer({ exitOnCtrlC: false });
    return ttyScreen(
      createRoot(renderer),
      () => renderer.destroy(),
    );
  }
  const test = await createTestRenderer({ width: PIPED_WIDTH, height: PIPED_HEIGHT });
  return pipedScreen(
    createRoot(test.renderer),
    () => test.flush(),
    () => test.captureCharFrame(),
    () => test.renderer.destroy(),
  );
}
