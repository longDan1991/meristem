/**
 * 一屏：把状态切片接起来、把路由装好。
 *
 * **这一层只做装配**（provider 顺序、路由表、默认那一屏），自己一个像素都不画；
 * "屏幕上有什么"在 `screens/`（壳与各屏一个文件，各带它接的键与它自己的视图状态）。
 *
 * 状态切成三处（各自的正文在各自文件里），三处都是 provider：
 *   · **端口**（账 / 树 / 角色 / 数据根 / 退出）—— `providers/session.tsx`：每个区都读，恒定；
 *   · **外面来的**（正在吐的字、作业事实 / 用量 / 接口失败）—— `providers/tail.tsx` /
 *     `providers/facts.tsx`：订阅攒出来的，被两三个区读，吐字再密也不惊动这一层；
 *   · **这一屏的共享状态与编排**（我站在哪条线、上一动作的回执）—— `providers/screen.tsx`：
 *     写它的是人在这屏上的动作，读者是多个区，所以由它持有、按区以 props 下发。
 * 其余状态不住这一层：思考展不展（消息流）、在第几张卡片（实时区）都是各区自己的
 * —— 那些的写者与读者在同一处。
 *
 * **屏由路由装**：表在 `screens/table.ts` 进来一次（`RouterProvider` 自己把当前那一屏画出来），
 * 壳是那一层布局（`screens/shell.tsx`），默认那一屏是 `screens/main.tsx`。所以 provider 顺序里
 * 路由在最里面 —— 屏要读上面那三片状态。
 *
 * **写账只有一个口子**：`Tree`（用法在 `hooks/tree-actions.ts`）；别的地方不碰账。
 *
 * 变因：一屏怎么接（provider 顺序、路由表从哪来）。
 */

import type { NodeId } from "@meristem/atree";
import { RouterProvider } from "@meristem/tui";
import type { ReactNode } from "react";
import { FactsProvider } from "./providers/facts.tsx";
import { ScreenProvider } from "./providers/screen.tsx";
import type { Session } from "./providers/session.tsx";
import { SessionProvider } from "./providers/session.tsx";
import { TailProvider } from "./providers/tail.tsx";
import { SCREENS } from "./screens/table.ts";

export interface AppProps {
  readonly session: Session;
  /** 人一开始站在哪条线上（`--at`）；`null` = 没指定 → 站在根（空树则先无处可站，见 `screen.tsx`）。 */
  readonly at: NodeId | null;
}

export function App({ session, at }: AppProps): ReactNode {
  return (
    <SessionProvider {...session}>
      <TailProvider>
        <FactsProvider>
          <ScreenProvider at={at}>
            <RouterProvider routes={SCREENS} />
          </ScreenProvider>
        </FactsProvider>
      </TailProvider>
    </SessionProvider>
  );
}
