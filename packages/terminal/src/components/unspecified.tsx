/** @jsxImportSource @opentui/react */
/**
 * 「内部还没定」的那几屏的**同一份**身子：名字与一句话（从命令表里取，不抄第二遍）+ 怎么进 / 怎么出
 * + 一句明说"里面还没定"。
 *
 * 为什么要有这么一块：八屏的骨架先立起来（进得去、出得来、壳不动），但只有两屏的内容已经定得下来
 * （键位表读的就是命令表；挑角色读角色注册表）—— 其余五屏**要等它们各自的细节**（`P0/02-screens.md`
 * 的"细节在哪"一列写着待写）。所以那五屏画的是"位置在这儿、里面还没定"，**不是**编一份像样的假内容：
 * 假装有了，下一份文档就会照着假的长。
 *
 * 变因：屏幕骨架那几句话（怎么进 / 怎么出 / 里面还没定）。
 */
import { tone, useCommands } from "@meristem/tui";
import type { ReactNode } from "react";
import { KeyLine } from "./status.tsx";

export interface UnspecifiedProps {
  /** 屏名：与路由表、命令表 `screen.*` 的第二段是同一个词。 */
  readonly screen: string;
}

export function Unspecified({ screen }: UnspecifiedProps): ReactNode {
  const command = useCommands().byScreen(screen);
  // 装配时核过"每一屏都有进它的命令"（`main.ts`），所以这里没有就是装配错了：当场炸，不画一个空屏。
  if (command === undefined) throw new Error(`命令表里没有 screen.${screen}（每一屏都得有一条进它的命令）`);
  const names = command.words.map((word) => `/${word}`).join(" ");
  const keys = command.keys.map((binding) => binding.key).join(" / ");
  return (
    <box flexDirection="column" width="100%" height="100%">
      <box flexDirection="column" flexGrow={1} width="100%" style={{ paddingX: 1 }}>
        <text fg={tone.accent}>{command.desc}</text>
        <text fg={tone.dim}>{`怎么进：${keys === "" ? names : `${names}（${keys}）`}`}</text>
        <text fg={tone.dim}>这一屏的内部还没定（P0 §2.2 的「细节在哪」写着待写）—— 定了再往里填</text>
        <text fg={tone.dim}>esc 回来：回来时是原档、原侧边态</text>
      </box>
      <KeyLine />
    </box>
  );
}
