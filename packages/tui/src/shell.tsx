/** @jsxImportSource @opentui/react */
/**
 * 一整屏的容器：铺满终端、竖排。
 *
 * 它**不接键**（键由各组件自己 `useKeys`）。存在的唯一理由是渲染器要求**根下只有一个孩子**：
 * 根下摆多个孩子时，重渲染 / 卸载会踩到渲染器"清容器"那条路（`remove expects a renderable child object`，
 * 实测：一个盒子包住同样的内容就正常），所以几个区先收进这一个盒子。
 *
 * 变因：终端尺寸怎么用（一整屏怎么占）。
 */
import { useTerminalDimensions } from "@opentui/react";
import type { ReactNode } from "react";

export interface ShellProps {
  readonly children: ReactNode;
}

export function Shell({ children }: ShellProps): ReactNode {
  const { width, height } = useTerminalDimensions();
  return (
    <box width={width} height={height} flexDirection="column">
      {children}
    </box>
  );
}
