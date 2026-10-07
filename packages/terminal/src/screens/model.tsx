/** @jsxImportSource @opentui/react */
/**
 * 挑模型：这棵树的模型从哪来、换成哪个。
 *
 * **内容还没定**：换模型要一份模型目录（provider / 各家的 id / 上下文档），而仓里现在只有配置里那一个
 * 模型引用（`.env` 的 `MERISTEM_MODEL`）—— 名单从哪来、详情写什么，归它自己的细节那一格。
 *
 * 变因：挑模型这一屏画什么（等它的细节定了就是这个文件重写的内容）。
 */
import type { ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { Unspecified } from "../components/unspecified.tsx";

export function ModelScreen(_props: ScreenViewProps<void>): ReactNode {
  return <Unspecified screen="model" />;
}
