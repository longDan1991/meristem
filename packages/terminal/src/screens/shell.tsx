/** @jsxImportSource @opentui/react */
/**
 * 壳：**不随屏变的那一部分**（路由里的那一层布局）+ 整屏那几条键。
 *
 * 一屏只有一个根（滚动盒）：渲染器要求根下只有一个孩子（见 `@meristem/tui` 的说明），它不接键。
 * **五个区装在一个滚动盒里**：一屏就是"一页"，比屏幕长了就滚动，而且**贴着底**（`stickyScroll` +
 * `stickyStart: "bottom"`）—— 新行进来时人看的是最新那段，不用等排版、也没有"滚到上一帧的末尾"这种错。
 * 滚动位置归它，所以各个区里不再有"滚到哪"这个状态。页是底对齐的（`contentOptions.justifyContent`）：
 * 内容不满一屏时也贴着底下那几行（输入行永远在同一处）。**右侧那条滚动条关掉**
 * （`verticalScrollbarOptions`）：它默认占一列宽，而这一屏的宽度要全给正文；`visible: false` 会让它
 * 整体退出排版，那一列还回来。
 *
 * **壳在屏外面**：`ScreenOutlet()` 是给屏留位的地方（web 的 `<Outlet/>`）；换屏时壳与底下那两行不动，
 * 只是那块地方换了内容。
 *
 * **键位分区**：没有集中键位表，谁在意谁接（`useKeys`）。壳只接整屏的这几条（`ctrl+c` 退出、
 * `ctrl+x` 收手）；`esc` / `↑↓` 那些归屏自己（`screens/main.tsx` 与各区）。
 *
 * 变因：壳里有什么（滚动盒的行为、输入行与状态条的位置、整屏那几条键）。
 */
import { useKeys, ScreenOutlet } from "@meristem/tui";
import type { ReactNode } from "react";
import { InputRegion } from "../components/input.tsx";
import { StatusRegion } from "../components/status.tsx";
import { useSession } from "../providers/session.tsx";
import { useScreen } from "../providers/screen.tsx";

export function Shell(): ReactNode {
  const { onExit } = useSession();
  const screen = useScreen();

  useKeys((key) => {
    switch (key) {
      case "ctrl+c":
        onExit();
        return true;
      case "ctrl+x":
        screen.stop();
        return true;
      default:
        return false;
    }
  });

  return (
    <scrollbox
      width="100%"
      height="100%"
      stickyScroll
      stickyStart="bottom"
      contentOptions={{ justifyContent: "flex-end" }}
      verticalScrollbarOptions={{ visible: false }}
    >
      <ScreenOutlet />
      <box>
        <InputRegion target={screen.selected} onSend={screen.send} onFork={screen.fork} onNotice={screen.notify} />
        <StatusRegion node={screen.selected} notice={screen.notice} />
      </box>
    </scrollbox>
  );
}
