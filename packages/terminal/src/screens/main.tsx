/** @jsxImportSource @opentui/react */
/**
 * 主屏：**默认那一屏**（表里标了 `index: true` 的那一屏，就是 web 里 `"/"` 对应的页面）。
 *
 * 它没有特别之处 —— 打开就在这里、`esc` 到不了更上面，都是"它在栈底"这一件事的结果，
 * 不是这一屏自己的性质。里面是内容区的三个区（档与侧边见 `docs/prototype/ours/P0/04-tiers.md`、
 * `05-side.md`，还没实现）。
 *
 * 变因：默认那一屏里放哪几个区、按什么顺序。
 */
import type { ReactNode } from "react";
import type { ScreenViewProps } from "@meristem/tui";
import { LiveRegion } from "../components/realtime.tsx";
import { StreamRegion } from "../components/stream.tsx";
import { TreeStripRegion } from "../components/tree-strip.tsx";
import { useScreen } from "../providers/screen.tsx";

export function MainScreen(_props: ScreenViewProps<void>): ReactNode {
  const screen = useScreen();

  return (
    <box style={{flexGrow: 1}}>
      <TreeStripRegion selected={screen.selected} onSelect={screen.select} onRetry={screen.retry} />
      <StreamRegion node={screen.selected} />
      <LiveRegion node={screen.selected} onCancel={screen.cancel} />
    </box>
  );
}
