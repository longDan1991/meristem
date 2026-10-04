/** @jsxImportSource @opentui/react */
/**
 * 消息流：选中那条线的账（人 / 模型 / 思考 / 手的过程）＋ 末尾"正在吐、还没进账"的字。
 *
 * **看的位置不在这一片**：滚动归首页那个滚动盒（`app.tsx`），这里只画"选中这条线上的行"。
 * 这一片自己只接一条键：`ctrl+o` 展开 / 收起账里的思考（展不展是这一片的视图状态）。
 *
 * **模型的原话整段交给 markdown 渲染件**（`<markdown>`）：标题 / 列表 / 代码围栏这些结构是
 * 一整段才认得出来的，所以它不按行拆；其余的行（人的话 / 手的交代 / 思考 / 接口失败）都是一行文字。
 *
 * **这一区的展示规则归这里**：账怎么平铺成行（`lineRows`）、思考怎么收起（`foldThoughts`）——
 * 纯函数，只服务这一片。
 *
 * 变因：这一区画什么（哪些行、思考折不折、模型那段怎么画）、它要的 props 从哪来、它接哪些键。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore } from "@meristem/harness";
import { useKeys } from "@meristem/tui";
import { memo, useState } from "react";
import type { ReactNode } from "react";
import { unaccounted } from "../lib/inflight.ts";
import { asBlock, FOLD, split } from "../lib/rows.ts";
import type { Row } from "../lib/rows.ts";
import { useSession } from "../providers/session.tsx";
import { useTail } from "../providers/tail.tsx";
import { colorByTag, syntaxStyle } from "../style.ts";

/**
 * 选中那条线的正文：它自己的平铺对话（人 / 模型 / 思考 / 手的过程）+ `tail`（正在吐、还没进账的字，
 * 原样接在末尾，标什么都不改）。
 *
 * **只认结构与顺序，不解析一个字**：作业 id 拼在消息文本里，那是给模型配对用的（DESIGN §9.6），
 * 界面要认的是形状 —— "`tool_calls` 后面紧跟着回话"。所以一条 `assistant` 的每个调用各铺一行头
 * （头行属于那条消息，跟着它的正文按账的顺序排），回话再按调用的顺序**位置**配对：只吃紧挨着的那条
 * `role: "tool"`，以及紧随其后 `by === 调用名` 的那条 `role: "user"`。
 * `tool_calls` 后面**不是**回话的（进程崩在中间留下的未完成区）只铺头行，后面的消息各按各的普通规则铺
 * （它们是独立的事实，不能被硬拉进上一条手的过程里）。
 *
 * 在跑的作业（卡片：名字 / 参数 / 已跑多久 / 现在吐了什么）**不在这里** —— 它还没进账，
 * 那是实时区拿 `Job.output()` / `Job.stream()` 画的（DESIGN §9.2 的"面向人"）。
 */
export function lineRows(store: LineStore, node: NodeId, tail: readonly Row[]): readonly Row[] {
  const rows: Row[] = [];
  const messages = store.content(node);
  let index = 0;
  while (index < messages.length) {
    const message = messages[index];
    if (message === undefined) break;

    if (message.role === "assistant") {
      // 思考按行铺；模型的原话**整段**走 markdown（不拆行：标题 / 列表 / 代码围栏要连成一段才认得出来）
      rows.push(...split(message.reasoning ?? "", "thought"));
      rows.push(...asBlock(message.content, false));
      const calls = message.toolCalls ?? [];
      // 头行来自这条 assistant 消息（它在回话之前），所以按账的顺序把这一组头先铺完；
      // 回话再按调用的顺序位置配对 —— 严格紧挨着，中间隔了什么就说明这一手没有回话。
      for (const call of calls) rows.push(...split(FOLD + call.name + " " + JSON.stringify(call.arguments), "hand"));

      let cursor = index + 1;
      for (const call of calls) {
        const reply = messages[cursor];
        if (reply?.role !== "tool") break;
        rows.push(...split(reply.content, "hand"));
        cursor += 1;
        const ending = messages[cursor];
        if (ending?.role === "user" && ending.by === call.name) {
          rows.push(...split(ending.content, "hand"));
          cursor += 1;
        }
      }
      index = cursor;
      continue;
    }

    // 没有前导 tool_calls 的 tool 消息是孤儿回话：它是账里的一段事实，但不是"某只手的过程"。
    // `by` 是"从手回来的"的结构标记（`user` 那条交代就靠它认），所以带 `by` 的 user 消息标 hand：
    // 它长得像人的话，但它不是人说的。
    if (message.role === "user") {
      rows.push(...split(message.content, message.by === undefined ? "user" : "hand"));
    } else {
      rows.push(...split(message.content, "dim"));
    }
    index += 1;
  }

  return [...rows, ...tail];
}

/** `ctrl+o` 收起时，把一串思考压成一行说明（**看得见的限制**，不是静默丢字）。 */
export function foldThoughts(rows: readonly Row[]): readonly Row[] {
  const folded: Row[] = [];
  let run = 0;
  const flush = (): void => {
    if (run > 0) folded.push({ text: `${FOLD}思考 ${run} 行（ctrl+o 展开）`, tag: "dim", kind: "line" });
    run = 0;
  };
  for (const row of rows) {
    if (row.tag === "thought") {
      run += 1;
      continue;
    }
    flush();
    folded.push(row);
  }
  flush();
  return folded;
}

/** 这一片要的 props：账里的行（思考可按 ctrl+o 收起）＋ 正在吐的正文。 */
interface StreamData {
  readonly rows: readonly Row[];
}

/** 读账 + 正在吐的字，算成这一片的行（思考单独在实时区画，不重复）。 */
function useStream(node: NodeId | null, thoughtsOpen: boolean): StreamData {
  const { store } = useSession();
  const tail = useTail();
  if (node === null) return { rows: [] };
  const account = lineRows(store, node, []);
  const live = unaccounted(store, node, tail);
  // 末尾那段（正在吐、还没进账）也走 markdown：它是同一条消息的前半截，`live` 让解析器按"还没写完"解析
  const rows: readonly Row[] = [
    ...(thoughtsOpen ? account : foldThoughts(account)),
    ...asBlock(live?.text ?? "", true),
  ];
  return { rows };
}

export interface StreamRegionProps {
  readonly node: NodeId | null;
}

export const StreamRegion = memo(function StreamRegion({ node }: StreamRegionProps): ReactNode {
  const [thoughtsOpen, setThoughtsOpen] = useState(false);
  const { rows } = useStream(node, thoughtsOpen);

  useKeys((key) => {
    if (key === "ctrl+o") {
      setThoughtsOpen((open) => !open);
      return true;
    }
    return false;
  });

  // 普通行一行一条（折行归引擎的 `wrapMode="char"`，不切半个宽字）；
  // 模型的原话整段交给 markdown 渲染件。滚动归外面的滚动盒。
  return (
    <box flexDirection="column" style={{paddingX:1}}>
      {rows.map((row, index) =>
        row.kind === "markdown" ? (
          <markdown key={index} content={row.text} syntaxStyle={syntaxStyle} streaming={row.live === true} />
        ) : (
          <text key={index} fg={colorByTag[row.tag]} wrapMode="char">
            {row.text}
          </text>
        ),
      )}
    </box>
  );
});
