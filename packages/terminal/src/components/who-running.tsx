/** @jsxImportSource @opentui/react */
/**
 * 「谁在动」：一行一条线 —— 还在动的 / 出错的那几条（P0 §3：最多 3 行 + 1 行「还有 N 条」，
 * **没有活就整条不出现**）。
 *
 * **只画在档 ①**：档 ② 那个位置让给树的一小段、档 ③ 也不画 —— 同一件事不在两处说
 * （档 ② 的树行右端本来就带 `▶N` / `✗`，段首还有计数）。所以这一片由档 ① 挂，不是壳的一部分。
 *
 * 记号与树里一致：`▶N` = 这条线上在跑几个作业，`✗` = 模型接口失败（那就是它的形状，不是颜色）。
 *
 * 变因：这一条画什么（哪几条算"在动"、最多几行）与它从哪取事实。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore } from "@meristem/harness";
import { RowList, tone } from "@meristem/tui";
import { memo } from "react";
import type { ReactNode } from "react";
import { FOLD } from "../lib/rows.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";

/** 最多铺几行（其余折成一行「还有 N 条」—— P0 §3）。 */
export const WHO_ROWS = 3;

interface Active {
  readonly id: NodeId;
  readonly name: string;
  readonly role: string;
  readonly jobs: number;
  readonly failed: boolean;
}

/** 在动 / 出错的线，顺序跟树一致（账的顺序 = 出生顺序）—— 同一份事实每次都画成同一屏。 */
export function actives(
  store: LineStore,
  jobs: readonly { readonly space: NodeId }[],
  errors: ReadonlyMap<NodeId, string>,
): readonly Active[] {
  const busy = new Map<NodeId, number>();
  for (const job of jobs) busy.set(job.space, (busy.get(job.space) ?? 0) + 1);
  return store.nodes().flatMap((id) => {
    const count = busy.get(id) ?? 0;
    const failed = errors.has(id);
    if (count === 0 && !failed) return [];
    const node = store.get(id);
    if (node === null) return [];
    return [{ id, name: node.props.name, role: node.props.role, jobs: count, failed }];
  });
}

export interface WhoRunningProps {
  /** 我站着的那条线（那一行带 `▌`）。 */
  readonly selected: NodeId | null;
}

export const WhoRunning = memo(function WhoRunning({ selected }: WhoRunningProps): ReactNode {
  const { store, tree } = useSession();
  const { errors } = useFacts();

  const lines = actives(store, tree.jobs(), errors);
  if (lines.length === 0) return null;

  const shown = lines.slice(0, WHO_ROWS);
  const rest = lines.length - shown.length;
  return (
    <box flexDirection="column" width="100%">
      <RowList
        items={shown.map((line) => ({
          key: line.id,
          // `▌` 钉住"我站着的这条线"；其余行首留出同样一格，名字才对得齐。
          text: `${line.id === selected ? "▌" : " "}${line.name} · ${line.role}`,
          selected: false,
          mark: [line.failed ? "✗ 出错" : undefined, line.jobs > 0 ? `▶${line.jobs}` : undefined]
            .filter((part) => part !== undefined)
            .join(" "),
        }))}
      />
      {rest > 0 ? <text fg={tone.dim}>{`${FOLD}还有 ${rest} 条`}</text> : null}
    </box>
  );
});
