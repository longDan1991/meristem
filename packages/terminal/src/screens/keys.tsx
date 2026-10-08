/** @jsxImportSource @opentui/react */
/**
 * 键位表（`/help`）：**这一屏的数据就是命令表** —— 不另写一份键位清单（那就是同一件事的第二个出口）。
 *
 * 分三组，按命令 id 的作用面分：**进一屏**（`screen.*`）· **就地做事**（`app.*` / `turn.*` / `view.*`）·
 * **走位**（`list.*`：只在某一份名单挂着时才有去处）。一条一行，右端是它的键。
 *
 * 左端写"短的一句"（命令表里的 `hint`，没有就用 `desc`）—— 键位表要的是**一眼扫过**，
 * 不是把每条的一句话都读一遍（那是 `/` 名单的事）。编辑器自己的键不在这张表里：那些归 opentui 的
 * 输入件，界面既不认领也改不了；底下明说一句，免得人以为漏了。
 *
 * 变因：键位表这一屏怎么分组（数据是那一份命令表）。
 */
import { RowList, tone, useCommands } from "@meristem/tui";
import type { Command, Layer, ScreenViewProps } from "@meristem/tui";
import type { ReactNode } from "react";
import { KeyLine } from "../components/status.tsx";

const GROUPS: readonly { readonly title: string; readonly layers: readonly Layer[] }[] = [
  { title: "进一屏", layers: ["screen"] },
  { title: "就地做事", layers: ["app", "turn", "view"] },
  { title: "走位（树 / 名单里）", layers: ["list"] },
];

export function KeysScreen(_props: ScreenViewProps<void>): ReactNode {
  const table = useCommands();
  return (
    <box flexDirection="column" width="100%" height="100%">
      <box flexDirection="column" flexGrow={1} width="100%" style={{ paddingX: 1 }}>
        <scrollbox flexGrow={1} verticalScrollbarOptions={{ visible: false }}>
          {GROUPS.map((group) => (
            <box key={group.title} flexDirection="column" width="100%">
              <text fg={tone.accent}>{group.title}</text>
              <RowList
                items={table.all
                  .filter((command) => group.layers.includes(command.layer))
                  .map((command) => ({
                    key: command.id,
                    text: `${namesOf(command)}${command.hint ?? command.desc}`,
                    selected: false,
                    mark: command.keys.map((binding) => binding.key).join(" / ") || undefined,
                  }))}
              />
            </box>
          ))}
          <text fg={tone.dim}>
            编辑器自己的键（打字 / 退格 / 左右 / 行首行尾 / 粘贴）归输入件，不在上面这张表里
          </text>
        </scrollbox>
      </box>
      <KeyLine />
    </box>
  );
}

/** 左端前半段：有斜杠名字就写它（连着别名），没有就什么也不写（走位那几条只有"做什么"）。 */
function namesOf(command: Command): string {
  return command.words.length === 0 ? "" : `${command.words.map((word) => `/${word}`).join(" · ")}  `;
}
