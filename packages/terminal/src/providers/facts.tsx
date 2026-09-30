/**
 * 事件里除吐字之外的事实：手的过程（作业）、用量、模型接口失败。
 *
 * 事件只带**结构**（作业 id、名字、参数、秒数），一个字的内容都不带 —— 界面要看字，
 * 交代问 `Job.report()`、吐出来的自己遍历 `Job.stream()`（见 `hooks/job-output.ts`）。
 * 这三样都在"一手起 / 一手结束 / 一轮结束 / 一次失败"时动，节奏比吐字慢得多，所以与
 * `tail.tsx` 分开：它一变，树条带 / 状态条 / 实时区重渲染，消息流不重渲染。
 *
 * `hands` 的 map 身份就是"在跑的作业表变了"的信号：`useStrip` / `useLive` 在渲染里读
 * `tree.jobs()`，靠这一片的重渲染把它们带到屏幕上。
 *
 * 变因：harness 的作业 / 用量 / 失败事件。
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import type { NodeId } from "@meristem/atree";
import type { Usage } from "@meristem/harness";
import { useSession } from "./session.tsx";

/** 一个作业的界面事实。 */
export interface HandFact {
  readonly name: string;
  readonly args: string;
}

export interface Facts {
  /** 作业 id → 界面事实。 */
  readonly hands: ReadonlyMap<string, HandFact>;
  readonly usages: ReadonlyMap<NodeId, Usage>;
  /** 模型接口失败的红字（不是任何一手的事，进不了账）。 */
  readonly errors: ReadonlyMap<NodeId, string>;
}

export interface FactsOps {
  /** 这条线不再算"接口失败过"（再开口 / 重试成功后调用）。 */
  clearError(node: NodeId): void;
}

export interface FactsStore extends Facts, FactsOps {}

export interface FactsProps {
  readonly children: ReactNode;
}

const FactsContext = createContext<FactsStore | null>(null);

function jsonOf(value: unknown): string {
  return JSON.stringify(value) ?? String(value);
}

function without<K, V>(map: ReadonlyMap<K, V>, key: K): ReadonlyMap<K, V> {
  const next = new Map(map);
  next.delete(key);
  return next;
}

export function FactsProvider({ children }: FactsProps): ReactElement {
  const { tree } = useSession();
  const [hands, setHands] = useState<ReadonlyMap<string, HandFact>>(() => new Map());
  const [usages, setUsages] = useState<ReadonlyMap<NodeId, Usage>>(() => new Map());
  const [errors, setErrors] = useState<ReadonlyMap<NodeId, string>>(() => new Map());

  useEffect(
    () =>
      tree.subscribe((event) => {
        switch (event.type) {
          case "hand_start":
            setHands((current) => new Map(current).set(event.job, { name: event.name, args: jsonOf(event.args) }));
            return;
          case "hand_end":
            setHands((current) =>
              new Map(current).set(event.job, { name: event.name, args: current.get(event.job)?.args ?? "" }),
            );
            return;
          case "usage":
            setUsages((current) => new Map(current).set(event.node, event.usage));
            return;
          case "transport_error":
            setErrors((current) => new Map(current).set(event.node, event.error.message));
            return;
          case "message":
            return;
        }
      }),
    [tree],
  );

  const clearError = useCallback((node: NodeId) => setErrors((current) => without(current, node)), []);
  const value = useMemo<FactsStore>(() => ({ hands, usages, errors, clearError }), [hands, usages, errors, clearError]);

  return <FactsContext.Provider value={value}>{children}</FactsContext.Provider>;
}

export function useFacts(): FactsStore {
  const facts = useContext(FactsContext);
  if (facts === null) throw new Error("useFacts 必须在 FactsProvider 里面用");
  return facts;
}
