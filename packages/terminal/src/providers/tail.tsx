/**
 * 正在吐、还没进账的字（一条线一份）—— 事件里**最热**的一片，单独一个 context。
 *
 * 只有 `message` 事件动它（正文与思考两条通道分开）；`hand_start` 把它清掉（起手了，
 * 这条线在吐的字要么马上进账、要么到此为止）。单独切开是为了让"吐一个字"只重渲染
 * 消息流与实时区，不连带树条带 / 状态条 / 输入行。
 *
 * `base` = 这份字开始攒的时候账有多长：账一长出来（assistant 那条进账了），这份字就作废 ——
 * 从这里画过的东西又从账里画一遍就是两份，而"哪一份才是事实"没有答案。
 *
 * 与 `facts.tsx` 各订阅一份事件（同一个 sink 支持多订阅者）：两片关心的类型不同、节奏也不同，
 * 分开订阅比把两片状态塞进一个组件省事。
 *
 * 变因：harness 的吐字事件（两条通道、作废规则）。
 */
import { createContext, useContext, useEffect, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import type { NodeId } from "@meristem/atree";
import { useSession } from "./session.tsx";

export interface Tail {
  readonly node: NodeId;
  readonly base: number;
  readonly text: string;
  readonly thought: string;
}

export interface TailProps {
  readonly children: ReactNode;
}

const TailContext = createContext<Tail | null>(null);

export function TailProvider({ children }: TailProps): ReactElement {
  const { store, tree } = useSession();
  const [tail, setTail] = useState<Tail | null>(null);

  useEffect(
    () =>
      tree.subscribe((event) => {
        if (event.type === "hand_start") {
          setTail((current) => (current !== null && current.node === event.node ? null : current));
          return;
        }
        if (event.type !== "message") return;
        setTail((current) => {
          const account = store.content(event.node).length;
          const grew = current === null || current.node !== event.node || current.base !== account;
          const base = grew ? account : current.base;
          const text = grew ? "" : current.text;
          const thought = grew ? "" : current.thought;
          return event.channel === "text"
            ? { node: event.node, base, text: text + event.delta, thought }
            : { node: event.node, base, text, thought: thought + event.delta };
        });
      }),
    [store, tree],
  );

  return <TailContext.Provider value={tail}>{children}</TailContext.Provider>;
}

export function useTail(): Tail | null {
  return useContext(TailContext);
}
