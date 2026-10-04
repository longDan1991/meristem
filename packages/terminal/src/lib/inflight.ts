/**
 * 正在吐、还没进账的那部分（`Tail` 里账已经收下的那截要减掉）—— 消息流画正文、实时区画思考，
 * 两边都按同一条规则判断哪些字还归自己画。
 *
 * 变因：账的末尾与正在吐的字怎么对上（哪些算"还没进账"）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore } from "@meristem/harness";
import type { Tail } from "../providers/tail.tsx";

/** 正在吐的字里账里还没有的那部分（assistant 那条一进账，它整段就都在账里了）。 */
export function unaccounted(store: LineStore, node: NodeId, tail: Tail | null): Tail | null {
  if (tail === null || tail.node !== node) return null;
  const last = store.content(node).at(-1);
  if (last === undefined || last.role !== "assistant") return tail;
  return {
    node,
    base: tail.base,
    text: last.content.endsWith(tail.text) ? "" : tail.text,
    thought: (last.reasoning ?? "").endsWith(tail.thought) ? "" : tail.thought,
  };
}
