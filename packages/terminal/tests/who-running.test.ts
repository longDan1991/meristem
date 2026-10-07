/**
 * 「谁在动」那一条选谁、按什么顺序：一行一条线（还在动 / 出错的），**没有活就没有这一条**。
 *
 * 两件事各错一次都会骗人：把安静的线也算进来（整条永远在），或者顺序不跟树一致（同一份事实
 * 每次画成不同的屏）。作业只用到 `space` 一个字段，所以这里喂普通对象就够。
 */
import { describe, expect, test } from "bun:test";
import { load } from "@meristem/atree";
import type { LineProps, LineStore, WireMessage } from "@meristem/harness";
import type { NodeId } from "@meristem/atree";
import { actives } from "../src/components/who-running.tsx";

async function tree(): Promise<LineStore> {
  // 每个用例一个新目录：`create` 是写账的，同一个目录第二次跑就已经有根了。
  const dir = `/tmp/meristem-who-${process.pid.toString()}-${crypto.randomUUID()}`;
  const store = await load<LineProps, WireMessage>(`${dir}/ledger.jsonl`);
  const root = store.create({ parent: null, props: { name: "我", role: "bare", outputRoot: "/tmp" } });
  store.create({ parent: root, props: { name: "整理 DESIGN", role: "bare", outputRoot: "/tmp" } });
  return store;
}

function ids(store: LineStore): readonly NodeId[] {
  return store.nodes();
}

describe("actives", () => {
  test("没有活也没有错：一条都不列（整条不出现）", async () => {
    const store = await tree();
    expect(actives(store, [], new Map())).toEqual([]);
  });

  test("在跑的线与出错的线各占一行，顺序跟树一致、安静的线不进来", async () => {
    const store = await tree();
    const [root, child] = ids(store);
    if (root === undefined || child === undefined) throw new Error("树没建起来");
    const lines = actives(store, [{ space: child }, { space: child }, { space: root }], new Map([[child, "接口挂了"]]));
    expect(lines.map((line) => line.id)).toEqual([root, child]);
    expect(lines.map((line) => line.jobs)).toEqual([1, 2]);
    expect(lines.map((line) => line.failed)).toEqual([false, true]);
    expect(lines.map((line) => line.name)).toEqual(["我", "整理 DESIGN"]);
  });
});
