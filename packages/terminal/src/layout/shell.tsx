/** @jsxImportSource @opentui/react */
/**
 * 壳（布局）：**不随屏变的那一部分 —— 只有两行字**。
 *
 * P0 §3 钉的形状：**状态行**（眼前正在发生的事）与**底下那行**（我在哪、烧了多少、能按什么）——
 * 任何档、任何屏都在原位、一格不动。它们上面那一整格是**屏自己画的**（web 的 `<Outlet/>`）：
 * 内容区、以及长在内容区右边的**侧边**，都在主屏自己那儿（P0 §2.2：主屏的细节就是"**它里面的**
 * 内容区（三档）+ 侧边（三态）"）—— 别的屏没有侧边，也就不该由壳替它们摆一个。
 *
 * **输入行也不在壳里**：只有要说话的那一屏需要它（`ScreenRoute.Composer`，现在只有主屏写了它），
 * 壳只给它位置（状态行与底下那行之间）。
 *
 * **壳只做一件事：画那两行**（外加接自己那几条命令）。
 *
 *   ① **画**：状态行与底下那行 —— 上面那一整格是屏自己画的。
 *   ② **接自己的**：`screen.*`（进屏，问路由）、`app.quit`、`app.close` 里"退掉压着的屏"那一层。
 *      按键本身不在这儿翻：**全界面唯一的按键监听在命令模块里**（`CommandBusProvider`），
 *      这里只声明"这几条归壳接"。**一条命令只跑一个**（从队尾往回问，P0 §1 决策 4：
 *      `esc` 收掉**最后出现**的那一层）—— 所以这一层不筛、不排序。
 *
 * 变因：壳有哪两行、它们各占哪一块。
 */
import { ScreenOutlet, useCommand, useRouter } from "@meristem/tui";
import type { Names } from "@meristem/tui";
import { createElement } from "react";
import type { ReactNode } from "react";
import { BottomLine, StatusLine } from "../components/status.tsx";
import { useScreen } from "../providers/screen.tsx";
import type { Screens } from "../routes.ts";

/** 壳里那两行字占几行（状态行 + 底下那行）。内容区拿剩下的；输入行是屏自带的，不算在里面。 */
export const SHELL_ROWS = 2;

type ScreenName = Names<Screens>;

/** 命令 id 的第二段（`screen.model` → `model`）：进哪一屏由它说。 */
function openedBy(id: string): ScreenName {
  return id.slice(id.indexOf(".") + 1) as ScreenName;
}

export function Shell(): ReactNode {
  const router = useRouter<Screens>();
  const screen = useScreen();

  // 壳接的那三条：进屏（整个 `screen` 层，进哪一屏由 id 的第二段说）、退出、
  // 以及"退掉压着的屏"这一层 —— 它只在真有屏压着时才有主（P0 §1 决策 4 的一层）。
  useCommand("screen.*", (id) => router.open(openedBy(id)));
  useCommand("app.quit", () => screen.quit());
  useCommand("app.close", () => router.back(), router.depth > 1);

  const Composer = router.Composer;
  return (
    <box flexDirection="column" width="100%" height="100%">
      {/* 屏在这一格里画它自己：内容区、侧边、名单 —— 壳不替任何一屏摆它里面的东西。 */}
      <box flexDirection="column" style={{ flexGrow: 1 }}>
        <ScreenOutlet />
      </box>
      <StatusLine />
      {/* 屏自带的那一块：只有写了 Composer 的屏才有（现在只有主屏 —— 要说话的那一屏）。 */}
      {Composer === undefined ? null : createElement(Composer)}
      <BottomLine />
    </box>
  );
}
