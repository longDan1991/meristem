/** @jsxImportSource @opentui/react */
/**
 * 变更日志与关于：这一版改了什么、我装的是哪一版（P0 故事 18）。
 *
 * **内容还没定**：版本号从哪来（`package.json`）、变更日志从哪读（仓里现在没有 CHANGELOG 文件）、
 * 一屏怎么排 —— 都归它自己的细节那一格。所以这一屏先只有位置与进出。
 *
 * 变因：变更日志与关于这一屏画什么（等它的细节定了就是这个文件重写的内容）。
 */
import type { ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { Unspecified } from "../components/unspecified.tsx";

export function AboutScreen(_props: ScreenViewProps<void>): ReactNode {
  return <Unspecified screen="about" />;
}
