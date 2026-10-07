/**
 * 一屏：把状态切片接起来、把路由装好。
 *
 * **这一层只做装配**（provider 顺序、路由表、默认那一屏），自己一个像素都不画；
 * "屏幕上有什么"在 `layout/`（壳）与 `screens/`（八屏各一个文件，各带它接的键与它自己的视图状态），
 * 页面里用的零件在 `components/`，与界面无关的功能性代码在 `lib/`。
 *
 * 状态切成三处（各自的正文在各自文件里），三处都是 provider：
 *   · **端口**（账 / 树 / 角色 / 数据根 / 退出）—— `providers/session.tsx`：每个区都读，恒定；
 *   · **外面来的**（正在吐的字、作业事实 / 用量 / 接口失败）—— `providers/tail.tsx` /
 *     `providers/facts.tsx`：订阅攒出来的，被两三个区读，吐字再密也不惊动这一层；
 *   · **这一屏的共享状态与编排**（我站在哪条线、档与侧边、草稿的把手、上一动作的回执）——
 *     `providers/screen.tsx`：写它的是人在这屏上的动作，读者是多个区。
 * 其余状态不住这一层：树滚到哪、名单里选到第几行都是各区自己的 —— 那些的写者与读者在同一处。
 *
 * **屏由路由装**：表在 `routes.ts` 进来一次（`RouterProvider` 自己把当前那一屏画出来），
 * 壳是那一层布局（`layout/shell.tsx`），默认那一屏是 `screens/main.tsx`。
 *
 * **命令是"谁执行谁就近挂上来"**（`CommandBusProvider`，排在店主外面）：表（一份 yaml）只写展示
 * （名字 / 键 / 一句话 / 提示），执行写在各层自己的文件里（`useCommand`）—— 所以这一层里没有
 * 任何"id → 实现"的表，只有 provider 的顺序。**按键也在那个 provider 里收口**（全界面唯一监听），
 * 所以别处拿不到按键：界面认领的键必然来自那张表。
 *
 * **写账只有一个口子**：`Tree`（用法在 `hooks/tree-actions.ts`）；别的地方不碰账。
 *
 * 变因：一屏怎么接（provider 顺序、路由表从哪来）。
 */
import type { NodeId } from "@meristem/atree";
import { CommandBusProvider, RouterProvider } from "@meristem/tui";
import type { Commands } from "@meristem/tui";
import type { ReactNode } from "react";
import { FactsProvider } from "./providers/facts.tsx";
import { ScreenProvider } from "./providers/screen.tsx";
import type { Session } from "./providers/session.tsx";
import { SessionProvider } from "./providers/session.tsx";
import { TailProvider } from "./providers/tail.tsx";
import { SCREENS } from "./routes.ts";

export interface AppProps {
  readonly session: Session;
  /** 人一开始站在哪条线上（`--at`）；`null` = 没指定 → 站在根（空树则先无处可站，见 `providers/screen.tsx`）。 */
  readonly at: NodeId | null;
  /** 认得的命令（装配那里从 yaml 建一次，整棵树共用这一份）。 */
  readonly commands: Commands;
}

export function App({ session, at, commands }: AppProps): ReactNode {
  return (
    <SessionProvider {...session}>
      <TailProvider>
        <FactsProvider>
          {/* 命令总线排在店主外面：店主（这一条线自己的命令）与每一屏、每一块都要挂上来。 */}
          <CommandBusProvider table={commands}>
            <ScreenProvider at={at}>
              <RouterProvider routes={SCREENS} />
            </ScreenProvider>
          </CommandBusProvider>
        </FactsProvider>
      </TailProvider>
    </SessionProvider>
  );
}
