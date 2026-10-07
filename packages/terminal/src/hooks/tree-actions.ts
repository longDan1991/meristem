/**
 * 写账：人的三个结构动作（**说话 / 分叉 / 收手**）与一个照看动作（**重试**）——
 * 全落在 `Tree` 上，这是界面唯一写账的口子。
 *
 * **只有"收手"（停整条线）**：人不能单独取消某一手（`esc` 只管视线层），所以这个面上没有"取消一个作业"。
 *
 * 参数**显式**：这里不读任何界面状态（站在哪条线、草稿里有什么都由调用方给），
 * 失败也**不吞**（原样抛给调用方，由它决定给不给回执）。
 *
 * 变因：账的写入口径（一次说话 / 一次分叉往账里写什么）。
 */
import { useMemo } from "react";
import type { NodeId } from "@meristem/atree";
import type { ForkInput } from "@meristem/harness";
import type { RoleId } from "@meristem/roles";
import { useSession } from "../providers/session.tsx";

export interface ForkParams {
  /** 父；`null` = **造根**（全局只发生一次，目录用 `dir`）。 */
  readonly parent: NodeId | null;
  /** 那句新话：决定新线从父线历史里抽哪一份底（`summarize` 时必须给）。 */
  readonly text: string;
  readonly role: RoleId;
  readonly mode: "inherit" | "summarize";
  /** 造根时的做事目录（有父就继承父的目录）。 */
  readonly dir: string;
}

export interface TreeActions {
  /** 说话：人的话就是账里的一条 user 消息，投给这条线。 */
  say(target: NodeId, text: string): Promise<void>;
  /** 分叉（含造根）：返回新线的 id。 */
  fork(params: ForkParams): Promise<NodeId>;
  /** 收手：不再叫任何线，在跑的作业都取消。 */
  stop(): void;
  /** 重试：把这条线放回推进（只用于"模型接口失败"）。 */
  retry(node: NodeId): void;
}

/** 只有一样依赖（`session.tree`），所以没有 provider，也不是共享状态。 */
export function useTreeActions(): TreeActions {
  const { tree } = useSession();
  return useMemo(
    () => ({
      say: (target: NodeId, text: string) => tree.say(target, text),
      fork: (params: ForkParams) =>
        tree.fork({
          parent: params.parent,
          role: params.role,
          inputText: params.text,
          mode: params.mode,
          ...(params.parent === null ? { dir: params.dir } : {}),
        } satisfies ForkInput),
      stop: () => tree.stop(),
      retry: (node: NodeId) => tree.retry(node),
    }),
    [tree],
  );
}
