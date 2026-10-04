/** @jsxImportSource @opentui/react */
/**
 * 一屏：把状态切片接起来、把五个区摆好。
 *
 * **这一层只做装配**（provider 顺序、五区顺序、把 props 递下去），自己一个像素都不画；
 * "屏幕上有什么"在 `components/`（一区一个文件，各带它接的键与它自己的视图状态）。
 *
 * 状态切成三处（各自的正文在各自文件里）：
 *   · **端口**（账 / 树 / 角色 / 数据根 / 退出）—— `providers/session.tsx`：每个区都读，恒定；
 *   · **外面来的**（正在吐的字、作业事实 / 用量 / 接口失败）—— `providers/tail.tsx` /
 *     `providers/facts.tsx`：订阅攒出来的，被两三个区读，吐字再密也不惊动这一层；
 *   · **这一屏的共享状态与编排**（我站在哪条线、上一动作的回执）—— `hooks/screen.ts`：
 *     写它的是人在这屏上的动作，读者是多个区，所以由这一层持有、按区以 props 下发。
 * 其余状态不住这一层：思考展不展（消息流）、在第几张卡片（实时区）都是各区自己的
 * —— 那些的写者与读者在同一处。
 *
 * **五个区装在一个滚动盒里**（opentui 的 `<scrollbox>`）：一屏就是"一页"，比屏幕长了就滚动，
 * 而且**贴着底**（`stickyScroll` + `stickyStart: "bottom"`）—— 新行进来时人看的是最新那段，
 * 不用等排版、也没有"滚到上一帧的末尾"这种错。滚动位置归它，所以各个区里不再有"滚到哪"这个状态。
 * 页是底对齐的（`contentOptions.justifyContent`）：内容不满一屏时也贴着底下那几行（输入行永远在同一处）。
 * **右侧那条滚动条关掉**（`verticalScrollbarOptions`）：它默认占一列宽，而这一屏的宽度要全给正文；
 * `visible: false` 会让它整体退出排版，那一列还回来。
 *
 * **键位分区**：没有集中键位表，谁在意谁接（`useKeys`）。这一层只接整屏的这几条
 * （`ctrl+c` 退出、`ctrl+x` 收手、翻页与一行一行走），五个区各接自己那几条（见 `components/`）。
 *
 * **写账只有一个口子**：`Tree`（用法在 `hooks/tree-actions.ts`）；别的地方不碰账。
 *
 * 一屏只有一个根（滚动盒）：渲染器要求根下只有一个孩子（见 `@meristem/tui` 的说明），它不接键。
 *
 * 变因：一屏怎么接（provider 顺序、五区顺序、谁拿哪些 props）。
 */

import type { NodeId } from "@meristem/atree";
import { useKeys } from "@meristem/tui";
import type { ReactNode } from "react";
import { InputRegion } from "./components/input.tsx";
import { LiveRegion } from "./components/realtime.tsx";
import { StatusRegion } from "./components/status.tsx";
import { StreamRegion } from "./components/stream.tsx";
import { TreeStripRegion } from "./components/tree-strip.tsx";
import { useScreen } from "./hooks/screen.ts";
import { FactsProvider } from "./providers/facts.tsx";
import type { Session } from "./providers/session.tsx";
import { SessionProvider, useSession } from "./providers/session.tsx";
import { TailProvider } from "./providers/tail.tsx";

export interface AppProps {
  readonly session: Session;
  /** 人一开始站在哪条线上（`--at`）；`null` = 没指定 → 站在根（空树则先无处可站，见 `useScreen`）。 */
  readonly at: NodeId | null;
}

export function App({ session, at }: AppProps): ReactNode {
  return (
    <SessionProvider {...session}>
      <TailProvider>
        <FactsProvider>
          <Console at={at} />
        </FactsProvider>
      </TailProvider>
    </SessionProvider>
  );
}

/** 画一屏的那一层：在 provider 里面（要读事件那两片），并持有这一屏的店主（`useScreen`）。 */
function Console({ at }: { readonly at: NodeId | null }): ReactNode {
  const { onExit } = useSession();
  const screen = useScreen(at);

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
      <box style={{flexGrow: 1}}>
        <TreeStripRegion selected={screen.selected} onSelect={screen.select} onRetry={screen.retry} />
        <StreamRegion node={screen.selected} />
        <LiveRegion node={screen.selected} onCancel={screen.cancel} />
      </box>
      <box>
        <InputRegion target={screen.selected} onSend={screen.send} onFork={screen.fork} onNotice={screen.notify} />
        <StatusRegion node={screen.selected} notice={screen.notice} />
      </box>
    </scrollbox>
  );
}
