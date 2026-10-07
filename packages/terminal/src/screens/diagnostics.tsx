/** @jsxImportSource @opentui/react */
/**
 * 诊断 / 日志：出问题了，看现场（请求原文 / 日志 / 终端能力），只读（P0 故事 17）。
 *
 * **内容还没定**：现场有哪些项、从哪取（诊断那一份数据面归 S11 那条线，在 P2）、要不要能翻页 ——
 * 都归它自己的细节那一格。所以这一屏先只有位置与进出。
 *
 * 变因：诊断这一屏画什么（等它的细节定了就是这个文件重写的内容）。
 */
import type { ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { Unspecified } from "../components/unspecified.tsx";

export function DiagnosticsScreen(_props: ScreenViewProps<void>): ReactNode {
  return <Unspecified screen="diagnostics" />;
}
