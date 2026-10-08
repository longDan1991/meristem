/** @jsxImportSource @opentui/react */
/**
 * 挑角色：分叉（或说话）之前换一套注意力与手 —— **选中即回**（P0 故事 9）。
 *
 * 名单就是角色注册表给的那一份（`list()`：它自己的说明写着"给人挑的清单"），不筛不凑；
 * 当前穿的那一位右端标出来。走位键从命令表来（`list.*` 那三条，就挂在这一屏里），不在这里写键名。
 *
 * 变因：挑角色这一屏画什么、选中之后回哪儿。
 */
import { RowList, tone } from "@meristem/tui";
import type { ScreenViewProps } from "@meristem/tui";
import { useState } from "react";
import type { ReactNode } from "react";
import { KeyLine } from "../components/status.tsx";
import { useCommand } from "../hooks/commands.ts";
import { useSession } from "../providers/session.tsx";
import { NO_ROLE, useRoleChoice } from "../screens/main.tsx";

export function RoleScreen({ back }: ScreenViewProps<void>): ReactNode {
  const { roles } = useSession();
  const { role, pick } = useRoleChoice();
  const [at, setAt] = useState(() => {
    const current = roles.findIndex((item) => item.id === role);
    return current < 0 ? 0 : current;
  });

  // 走位（`list.*`）就近挂在这儿：这一屏在，走位就归它的名单。
  // 一个角色都没有时没有人接 —— 键行也就不写 `↑↓`，`enter` 也按不动（没什么可挑的）。
  useCommand(
    "list.*",
    (id) => {
      if (id === "list.enter") {
        const chosen = roles[at];
        if (chosen === undefined) return;
        pick(chosen.id);
        back();
        return;
      }
      const delta = id === "list.prev" ? -1 : 1;
      setAt((current) => (current + delta + roles.length) % roles.length);
    },
    roles.length > 0,
  );

  return (
    <box flexDirection="column" width="100%" height="100%">
      <box flexDirection="column" flexGrow={1} width="100%" style={{ paddingX: 1 }}>
        <text fg={tone.accent}>挑角色</text>
        <text fg={tone.dim}>选中即回：下一句话穿它（说话与分叉都算）</text>
        {roles.length === 0 ? (
          <text fg={tone.danger}>{NO_ROLE}</text>
        ) : (
          <RowList
            items={roles.map((item, index) => ({
              key: item.id,
              text: `${item.title} · ${item.id}`,
              selected: index === at,
              mark: item.id === role ? "当前" : undefined,
            }))}
          />
        )}
      </box>
      <KeyLine />
    </box>
  );
}
