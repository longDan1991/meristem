/** @jsxImportSource @opentui/react */
/**
 * 壳（布局）：**一行都不画** —— 它只剩两件事：给屏留一格（`ScreenOutlet`），接全界面共用的那几条命令。
 *
 * **为什么壳不再画东西**：一行写什么，只看它跟着谁走（P0 §3）。跟着**那条线**走的（状态行 / 输入行 /
 * 事实行）只有主屏有；跟着**眼前这一层**走的键行每一屏都不一样 —— 所以四行都归各屏自己画，
 * 壳上没有一行是"哪一屏都长一样"的。屏自己那一格拿满整屏。
 *
 * **壳接的那三条**：`screen.*`（进屏，进哪一屏由 id 的第二段说）、`app.quit`（喊退出）、
 * `app.close` 里"退掉压着的屏"那一层 —— 它只在真有屏压着时才有主（P0 §1 决策 4 的一层）。
 * 按键本身不在这儿翻：**全界面唯一的按键监听在命令模块里**（`CommandBusProvider`），
 * 这里只声明"这几条归壳接"。**一条命令只跑一个**（从队尾往回问）—— 所以这一层不筛、不排序。
 *
 * 变因：壳接哪几条命令、以及（将来若出现"哪一屏都长一样"的东西时）壳上多哪一块。
 */
import { ScreenOutlet, useRouter } from "@meristem/tui";
import type { Names } from "@meristem/tui";
import type { ReactNode } from "react";
import { useCommand } from "../hooks/commands.ts";
import { useSession } from "../providers/session.tsx";
import type { Screens } from "../routes.ts";

type ScreenName = Names<Screens>;

/** 命令 id 的第二段（`screen.model` → `model`）：进哪一屏由它说。 */
function openedBy(id: string): ScreenName {
  return id.slice(id.indexOf(".") + 1) as ScreenName;
}

export function Shell(): ReactNode {
  const router = useRouter<Screens>();
  const { onExit } = useSession();

  useCommand("screen.*", (id) => router.open(openedBy(id)));
  useCommand("app.quit", () => onExit());
  useCommand("app.close", () => router.back(), router.depth > 1);

  // 屏在这一格画它自己（含它自带的那几行）—— 壳不替任何一屏摆东西。
  return <ScreenOutlet />;
}
