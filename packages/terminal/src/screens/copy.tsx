/** @jsxImportSource @opentui/react */
/**
 * 选中 / 复制：把某几块（人的话 / 它的话 / 一手 / 一整条线）单独拿出来（P0 故事 14）。
 *
 * **内容还没定**：选块怎么选（一整屏还是一层浮层 —— P0 §9 第 5 条把这条留给人拍）、复制走哪儿
 * （剪贴板还是 OSC52）、复制完怎么退，都归它自己的细节那一格。
 *
 * 变因：选中 / 复制这一屏画什么（等它的细节定了就是这个文件重写的内容）。
 */
import type { ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { Unspecified } from "../components/unspecified.tsx";

export function CopyScreen(_props: ScreenViewProps<void>): ReactNode {
  return <Unspecified screen="copy" />;
}
