/** @jsxImportSource @opentui/react */
/**
 * 主屏：默认那一屏（表里标了 `index: true` 的那一屏）—— **一条对话 + 一块结构 + 一块侧边**。
 *
 * **两块可变的东西都长在它里面**（P0 §2.2：主屏的细节就是"**它里面的**内容区（三档）+ 侧边（三态）"）：
 *   · **内容区**只有一个轴 —— 你看见多少结构（P0 §4）。同一个键循环三档：
 *     ① 这段对话（默认，我这条线的事 + 最底下一行「谁在动」）· ② 盯住一条（对话被挤短，底部向上长出
 *     一段树与其实况）· ③ 整棵树（整块内容区换成树）；
 *   · **侧边**（P0 §5）在内容区右边，三态：收起 0 列 / 分成两栏（右边一列）/ 占满全屏（内容区让位）。
 * 所以**这一屏占的宽度也要自己分**：先切出侧边那一列，剩下的给内容区（全屏时反过来）。
 *
 * **档 ② 那段树**的预算 = 内容区 ÷ 3（夹 3..16 行 —— P0 §4 的代价一节写明），所以这里算得出来：
 * 整屏高减去壳那两行、再减去**这一屏自带的输入行**（含它上面那层命令名单），就是内容区。
 *
 * **这一屏自带的那几条命令就近挂在这儿**（命令表里 `view.*`，以及 `esc` 的两层：
 * 侧边占满 / 档不是 ①）。后出现的先收（P0 §1 决策 4）：每一条的 `active` 就是"这一层在不在"，
 * 所以挂上来的那一刻就是那层出现的时刻 —— `esc` 的次序由此自动成立，这里不写次序。
 * 走位（`list.*`）归眼前那份名单（`tree-view.tsx` 与各名单屏）；壳上的那几条归壳（`layout/shell.tsx`）。
 *
 * 变因：主屏有哪几档、每档里摆哪几块、档 ② 从对话那里借多少、侧边吃多少列。
 */
import { useCommand } from "@meristem/tui";
import type { ScreenViewProps } from "@meristem/tui";
import { useTerminalDimensions } from "@opentui/react";
import { useMemo } from "react";
import type { ReactNode } from "react";
import { LiveRegion } from "../components/realtime.tsx";
import { SidePanel } from "../components/side.tsx";
import { StreamRegion } from "../components/stream.tsx";
import { TreeView } from "../components/tree-view.tsx";
import { WhoRunning } from "../components/who-running.tsx";
import { SHELL_ROWS } from "../layout/shell.tsx";
import { SIDE_PAGES } from "../lib/side.ts";
import { useScreen } from "../providers/screen.tsx";

/** 档 ② 那段树最多占内容区的几分之一（P0 §4：≤ 内容高/3，夹 3..16 行）。 */
const BUDGET_SHARE = 3;
const BUDGET_MIN = 3;
const BUDGET_MAX = 16;

/** 分栏时右侧那一列多宽（P0 §9 第 3 条把宽度档位留作开口：先给一档）。 */
const SPLIT_MIN = 28;
const SPLIT_SHARE = 3;

/** 档 ② 的树段行数预算。 */
export function tierBudget(rows: number): number {
  return Math.min(Math.max(Math.floor(rows / BUDGET_SHARE), BUDGET_MIN), BUDGET_MAX);
}

export function MainScreen(_props: ScreenViewProps<void>): ReactNode {
  const screen = useScreen();
  const { tier, selected, side, page } = screen;
  const { width: cols, height } = useTerminalDimensions();
  const rows = Math.max(1, height - SHELL_ROWS - screen.composerRows);

  // 这一屏自带的那几条（`view.*`）。`view.side-page` 只在侧边开着时有主：没开就没有页可换。
  useCommand("view.tier", () => screen.cycleTier());
  useCommand("view.side", () => screen.cycleSide());
  useCommand("view.side-page", () => screen.cyclePage(SIDE_PAGES.length), side !== "hidden");
  // `esc` 在这一屏有两层可收：侧边占满 → 分成两栏；档不是 ① → 收回一档。
  // `active` 就是"这一层在不在" —— 挂上来的时刻 = 这层出现的时刻，所以后出现的先收。
  useCommand("app.close", () => screen.unwindSide(), side === "full");
  useCommand("app.close", () => screen.unwindTier(), tier !== 1);

  // 对话那一块：账 + 正在吐的字 + 在跑的卡片；它自己滚动、贴着底（新行进来时看的是最新那段）。
  const talk = useMemo(
    () => (
      <scrollbox
        flexGrow={1}
        stickyScroll
        stickyStart="bottom"
        contentOptions={{ justifyContent: "flex-end" }}
        verticalScrollbarOptions={{ visible: false }}
      >
        <StreamRegion node={selected} />
        <LiveRegion node={selected} />
      </scrollbox>
    ),
    [selected],
  );

  const split = Math.max(SPLIT_MIN, Math.floor(cols / SPLIT_SHARE));
  // 内容区的宽度**只在"收起 ↔ 分栏"之间变，绝不变成 0**：来回压成 0 会把里面那份贴底滚动盒量坏
  // （回到分栏时它自己撑满、把树顶出视野）。占满全屏那一态是**不显示**它（`visible`），不是卸载 ——
  // 卸载还会让区里的订阅跟着摘挂一遍，次序跟着乱动。
  const contentWidth = side === "hidden" ? "100%" : cols - split;
  return (
    <box flexDirection="row" width="100%" height="100%">
      <box flexDirection="column" width={contentWidth} visible={side !== "full"}>
        {tier === 3 ? null : talk}
        {tier === 1 ? <WhoRunning /> : null}
        {tier === 2 ? <TreeView size={tierBudget(rows)} detail /> : null}
        {tier === 3 ? <TreeView size={rows} detail={false} /> : null}
      </box>
      {side === "hidden" ? null : (
        // 侧边**浮在上面**：这样无论内容区多宽，它都拿得住自己那一份（分栏时右边一列、占满时整屏），
        // 不用跟内容区抢 flex 空间。
        <box
          position="absolute"
          top={0}
          left={side === "full" ? 0 : cols - split}
          width={side === "full" ? "100%" : split}
        >
          <SidePanel page={page} />
        </box>
      )}
    </box>
  );
}
