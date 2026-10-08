/**
 * 端口：屏幕之外的一切从这里进来。
 *
 * **只有值，没有行为**：账（渲染树、画一条线是 atree 的面）、树（写账 + 事件）、角色清单
 * （分叉时给人挑）、数据根（造根时用）、一开始站在哪条线（`--at`）、退出回调（还原终端归 `mount`）。
 * 这一片**恒定** —— 装配完就不再变（所以值只算一次），它变了整棵树都该重渲染。
 *
 * 变因：装配输入（有几个端口、谁提供）。
 */
import { createContext, useContext, useMemo } from "react";
import type { ReactElement, ReactNode } from "react";
import type { NodeId } from "@meristem/atree";
import type { LineStore, Tree } from "@meristem/harness";
import type { Role } from "@meristem/roles";

export interface Session {
  readonly store: LineStore;
  readonly tree: Tree;
  readonly roles: readonly Role[];
  /** 数据根：**造根**时用（没有父可以继承目录）；之后每条线的目录缺省继承父。 */
  readonly workspace: string;
  /**
   * 人一开始站在哪条线上（`--at`）；**没给（`null`）就站在根**（树的入口）。
   * 空树（连根都还没有）时无处可站 —— 那时第一句话就是开树的那句（见 `screens/main.tsx`）。
   */
  readonly at: NodeId | null;
  /** 退出（还原终端由 `mount` 负责）：这里只喊一声。 */
  readonly onExit: () => void;
}

export interface SessionProps extends Session {
  readonly children: ReactNode;
}

const SessionContext = createContext<Session | null>(null);

export function SessionProvider({ children, store, tree, roles, workspace, at, onExit }: SessionProps): ReactElement {
  const value = useMemo<Session>(
    () => ({ store, tree, roles, workspace, at, onExit }),
    [store, tree, roles, workspace, at, onExit],
  );
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

/** 缺席就抛（不是返回默认值）：装配错要当场炸，不降级。 */
export function useSession(): Session {
  const session = useContext(SessionContext);
  if (session === null) throw new Error("useSession 必须在 SessionProvider 里面用");
  return session;
}
