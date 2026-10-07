/**
 * 屏幕外壳：**渲染器与终端的创建、还原只此一处**。
 *
 * 变因是"终端形态"：真终端有帧循环，React 自己把重画推上去；管道 / CI 里根本没有可重画的屏幕，
 * 只能降级成"每要一次就追加一帧文本"。两种形态之外的差别（画什么、怎么排）都在组件与业务里。
 *
 * 两个动作，**分开是有原因的**：
 *   · `render(node)` —— 把这一棵树画上去（装配时一次）；
 *   · `refresh()` —— 降级模式下"把当前状态再画一帧"（真终端下是空操作，帧循环自己画）。
 * 重画**不走**"再 render 同一棵树"：状态在 React 里，重 render 一棵多孩子的树会踩到渲染器
 * 卸载旧孩子的那条路（`remove expects a renderable child object`），而 flush 一下就够。
 *
 * 状态归 React，所以这个外壳自己不记除了"还原过没有 / 画过没有"之外的任何东西。
 */
import { createCliRenderer } from "@opentui/core";
import { createTestRenderer } from "@opentui/core/testing";
import { createRoot, flushSync } from "@opentui/react";
import type { Root } from "@opentui/react";
import type { ReactNode } from "react";

export interface Screen {
  /** 把这一棵树画上去（装配时调一次）。 */
  render(node: ReactNode): void;
  /** 降级模式下追加一帧当前状态；真终端下空操作（帧循环自己画）。 */
  refresh(): void;
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
    refresh() {
      // 真终端有帧循环：React 一提交，屏幕自己就更新了。
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
 * 这里**必须**用 `flushSync` 包住：没有渲染循环推提交，裸调用不会当场落地，flush 出来的
 * 会是还没画过的缓冲区。TTY 那条路相反 —— 那里帧是引擎自己推的。
 */
function pipedScreen(root: Root, flush: () => Promise<void>, capture: () => string, stop: () => void): Screen {
  let restored = false;
  let drawn = false;
  // 一帧 = 提交 + flush + 落盘，整段串起来：不然连着两次会一起提交，第一帧就丢了。
  let queue: Promise<void> = Promise.resolve();

  const draw = async (): Promise<void> => {
    await flush();
    // 帧之间空一行：capture 出来的字符串自己带结尾换行，先去掉再补一次，免得空成两行。
    const frame = capture().replace(/\n+$/, "");
    process.stdout.write(drawn ? `\n${frame}\n` : `${frame}\n`);
    drawn = true;
  };

  return {
    render(node) {
      queue = queue.then(async () => {
        flushSync(() => {
          root.render(node);
        });
        await draw();
      });
    },
    refresh() {
      queue = queue.then(async () => {
        // 空回调也没有关系：它把已经排上的更新催成一次提交。
        flushSync(() => {});
        await draw();
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
  // 两条路给同一个契约：`ctrl+c` **归界面自己**（命令表里有这条），引擎不许抢先退出 ——
  // 真终端那条本来就关着，管道 / 测试这条也得关（不然一按 `ctrl+c` 屏幕就没了，界面再也没机会收尾）。
  if (process.stdout.isTTY === true) {
    const renderer = await createCliRenderer({ exitOnCtrlC: false });
    return ttyScreen(
      createRoot(renderer),
      () => renderer.destroy(),
    );
  }
  const test = await createTestRenderer({ width: PIPED_WIDTH, height: PIPED_HEIGHT, exitOnCtrlC: false });
  return pipedScreen(
    createRoot(test.renderer),
    () => test.flush(),
    () => test.captureCharFrame(),
    () => test.renderer.destroy(),
  );
}
