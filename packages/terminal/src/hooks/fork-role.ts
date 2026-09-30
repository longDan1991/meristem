/**
 * 分叉时穿哪块能力：在人挑得到的角色里轮（`ctrl+r`）。
 *
 * **输入行自己的状态**：写它的是输入行的键（`ctrl+r`），读它的也是输入行（说话 / 分叉要把它交给
 * 写账那一层）—— 没有跨区规则，也不被别的区读，所以既不是 provider、也不归根。
 *
 * 机制角色（`SUMMARY_FORK`）不在可挑之列：它是分叉时程序穿的那一位，不是一块能力。
 *
 * 变因：分叉穿哪块能力（挑哪些角色、怎么轮）。
 */
import { useCallback, useMemo, useState } from "react";
import type { Role } from "@meristem/roles";
import { SUMMARY_FORK } from "@meristem/roles";

/** 一个人可选的角色都没有时说什么（角色是部署的事，代码不替它编一个）。 */
export const NO_CHOICE =
  "没有可选的角色：一个人选的角色就是一个 xml，放进 MERISTEM_ROLES 指的目录" +
  "（内置的 summary-fork 是分叉时程序穿的机制角色，不给人挑）";

export interface ForkRole {
  /** 当前这一位；一个可挑的角色都没有时是 `null`（这时按回车要说话，得先说清为什么不行）。 */
  readonly current: Role | null;
  /** 轮下一位，并把它给回来（好让调用方说一句"现在是哪一位"）；没有可挑的角色时 `null`。 */
  cycle(): Role | null;
}

/** 人挑得到的角色：机制角色（总结分叉的乙）不在里面 —— 它不是一块能力。 */
export function pickers(roles: readonly Role[]): readonly Role[] {
  return roles.filter((role) => role.id !== SUMMARY_FORK);
}

export function useForkRole(roles: readonly Role[]): ForkRole {
  const choosable = useMemo(() => pickers(roles), [roles]);
  const [at, setAt] = useState(0);

  const cycle = useCallback((): Role | null => {
    if (choosable.length === 0) return null;
    const next = choosable[(at + 1) % choosable.length] ?? null;
    setAt((current) => (current + 1) % choosable.length);
    return next;
  }, [at, choosable]);

  const current = choosable.length === 0 ? null : (choosable[at % choosable.length] ?? null);
  return { current, cycle };
}
