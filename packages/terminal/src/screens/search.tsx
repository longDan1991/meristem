/** @jsxImportSource @opentui/react */
/**
 * 在这一条线里找一句话（P0 故事 15）。
 *
 * **内容还没定**：搜什么（我说的话 / 它说的话 / 手的交代）、命中怎么列、选中之后跳到哪一处 ——
 * P0 §9 第 6 条把这几条留给人拍。所以这一屏先只有位置与进出。
 *
 * 变因：搜索这一屏画什么（等它的细节定了就是这个文件重写的内容）。
 */
import type { ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { Unspecified } from "../components/unspecified.tsx";

export function SearchScreen(_props: ScreenViewProps<void>): ReactNode {
  return <Unspecified screen="search" />;
}
