/**
 * 终端生命周期：接管终端、订阅事件、把人的输入送回账里；返回时终端已还原。
 *
 * 这是**唯一摸终端**的地方（不写裸 ANSI，也不开第二个渲染器抢同一块屏）。真终端下 React 自己
 * 推帧；管道 / CI 里没有帧循环，就退化成"每有事发生就再画一帧"（React 按类型 diff，状态不丢）。
 *
 * 这里只负责"屏的生死"：退出由人的 `ctrl+c` 喊一声（`onExit` 就是那一声），收手（取消在跑的作业）
 * 归装配层在 `finally` 里做。
 *
 * 变因：终端生命周期（接管 / 还原 / 降级）。
 */
import { openScreen } from "@meristem/tui";
import type { Commands } from "@meristem/tui";
import type { ReactElement } from "react";
import { App } from "./app.tsx";
import type { Session } from "./providers/session.tsx";

export interface MountProps {
  /** 装配置一次算出来的那些端口：不含 `onExit` —— 退出这一声由这里接（谁创建屏幕谁管还原）。 */
  readonly session: Omit<Session, "onExit">;
  /** 认得的命令（装配那里从 yaml 建一次）。 */
  readonly commands: Commands;
}

export async function mount(props: MountProps): Promise<void> {
  const screen = await openScreen();
  const exit = Promise.withResolvers<void>();
  const element: ReactElement = (
    <App session={{ ...props.session, onExit: () => exit.resolve() }} commands={props.commands} />
  );
  try {
    screen.render(element);
    if (!process.stdout.isTTY) {
      // 降级：没有帧循环，所以每有事发生就催一帧（React 自己带状态，这里只催它提交）
      const unsubscribe = props.session.tree.subscribe(() => screen.refresh());
      try {
        await exit.promise;
      } finally {
        unsubscribe();
      }
      return;
    }
    await exit.promise;
  } finally {
    await screen.restore();
  }
}
