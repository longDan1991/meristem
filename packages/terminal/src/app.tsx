/**
 * 一屏：把状态切片接起来、把路由装好。
 *
 * **这一层只做装配**（provider 顺序、路由表、默认那一屏），自己一个像素都不画；
 * "屏幕上有什么"在 `layout/`（壳）与 `screens/`（八屏各一个文件，各带它接的键与它自己的视图状态），
 * 页面里用的零件在 `components/`，与界面无关的功能性代码在 `lib/`。
 *
 * 状态切成四处（正文各自在各自文件里）：
 *   · **端口**（账 / 树 / 角色 / 数据根 / 一开始站哪 / 退出）—— `providers/session.tsx`：每个区都读，恒定；
 *   · **外面来的**（正在吐的字、作业事实 / 用量 / 接口失败）—— `providers/tail.tsx` /
 *     `providers/facts.tsx`：订阅攒出来的，被两三个区读，吐字再密也不惊动这一层；
 *   · **两个屏共用的一个值**（下一句话穿哪个角色）—— `RoleChoiceProvider`：挑角色那一屏要**写**它，
 *     主屏要读它，所以它得挂在路由**上面**（屏之间没有别的通道：`ScreenViewProps` 只有参数，
 *     而参数是导航数据，`back()` 也不带回头值）；
 *   · **主屏自己的**（站在哪条线、档与侧边、草稿的把手、上一动作的回执）—— 就是主屏那一屏的状态，
 *     所以它住在 `screens/main.tsx` 里，是那个组件的局部状态。
 *     **为什么不用挂在这上面**：屏不卸载了（`@meristem/tui` 的 `router.ts` 留着整个栈，
 *     被盖住的只是藏起来），所以进屏再回来它还是原来那个实例 —— P0 §6 的"原档、原侧边态"由
 *     路由本身给，不需要把状态提到屏外面。
 * 其余状态不住这一层：树滚到哪、名单里选到第几行都是各区自己的 —— 那些的写者与读者在同一处。
 *
 * **屏由路由装**：表在 `routes.ts` 进来一次（`RouterProvider` 自己把当前那一屏画出来），
 * 壳是那一层布局（`layout/shell.tsx`），默认那一屏是 `screens/main.tsx`。
 *
 * **命令是"谁执行谁就近挂上来"**（`CommandBusProvider`，排在所有业务 provider 外面）：表（一份 yaml）
 * 只写展示（名字 / 键 / 一句话 / 提示），执行写在各层自己的文件里（`hooks/commands.ts` 的
 * `useCommand`）—— 所以这一层里没有任何"id → 实现"的表，只有 provider 的顺序。
 * **按键也在那个 provider 里收口**（全界面唯一监听），所以别处拿不到按键：界面认领的键必然来自那张表。
 *
 * **写账只有一个口子**：`Tree`（用法在 `hooks/tree-actions.ts`）；别的地方不碰账。
 *
 * 变因：一屏怎么接（provider 顺序、路由表从哪来）。
 */
import { CommandBusProvider, RouterProvider } from "@meristem/tui";
import type { Commands } from "@meristem/tui";
import type { ReactNode } from "react";
import { FactsProvider } from "./providers/facts.tsx";
import type { Session } from "./providers/session.tsx";
import { SessionProvider } from "./providers/session.tsx";
import { TailProvider } from "./providers/tail.tsx";
import { SCREENS } from "./routes.ts";
import { RoleChoiceProvider } from "./screens/main.tsx";

export interface AppProps {
  readonly session: Session;
  /** 认得的命令（装配那里从 yaml 建一次，整棵树共用这一份）。 */
  readonly commands: Commands;
}

export function App({ session, commands }: AppProps): ReactNode {
  return (
    <SessionProvider {...session}>
      <TailProvider>
        <FactsProvider>
          {/* 命令总线排在最外面：谁要接命令都挂在这上面（每一块自己就近挂，见 `hooks/commands.ts`）。 */}
          <CommandBusProvider table={commands}>
            {/* 两个屏共用的那一个值：挑角色那一屏要写它，主屏要读它 —— 所以挂在路由上面。
                主屏自己不在这儿：它的状态是它那个组件的局部状态（屏不卸载，见文件头）。 */}
            <RoleChoiceProvider>
              <RouterProvider routes={SCREENS} />
            </RoleChoiceProvider>
          </CommandBusProvider>
        </FactsProvider>
      </TailProvider>
    </SessionProvider>
  );
}
