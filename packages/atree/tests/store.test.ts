/**
 * atree 的真测试：**记录就是事实**这条不变量，逐条兑现。
 *
 * 全部落在临时目录上（不碰仓库、不依赖执行顺序），用的是这个包的对外面（`load`）；
 * 需要"读歪的账"时直接手写 JSON 行 —— 那正是要防的输入。
 */
import { afterEach, beforeEach, expect, test } from "bun:test";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load } from "../src/index.ts";

interface Props {
  readonly name: string;
}

let dir: string;

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "atree-"));
});

afterEach(() => {
  rmSync(dir, { recursive: true, force: true });
});

function nodeLine(t: number, id: string, parent: string | null = null, boundary = false): string {
  return JSON.stringify({
    t,
    node: id,
    kind: "node",
    payload: { id, parent, props: { name: id }, boundary, at: t },
  });
}

function contentLine(t: number, id: string, base: number, added: readonly string[]): string {
  return JSON.stringify({ t, node: id, kind: "content", payload: { base, added } });
}

test("写进去的东西,读回来一模一样", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  expect(store.root()).toBeNull();

  const root = store.create({ parent: null, props: { name: "我" } });
  const kid = store.create({ parent: root, props: { name: "读文档" } });
  store.append(root, ["第一条", "第二条"]);
  store.append(kid, ["子的一条"]);
  store.patch(kid, { name: "读文档 v2" });
  await store.close();

  const back = await load<Props, string>(path);
  expect(back.root()).toBe(root);
  expect(back.get(root)?.props.name).toBe("我");
  expect(back.get(kid)?.props.name).toBe("读文档 v2");
  expect(back.children(root)).toEqual([kid]);
  expect(back.content(root)).toEqual(["第一条", "第二条"]);
  expect(back.content(kid)).toEqual(["子的一条"]);
  expect(back.assemble(kid)).toEqual(["第一条", "第二条", "子的一条"]);
  await back.close();
});

test("空树不落盘:没有内容就不建文件", async () => {
  const path = join(dir, "深层", "tree.jsonl");
  const store = await load<Props, string>(path);
  expect(store.root()).toBeNull();
  await store.close();
  expect(existsSync(path)).toBe(false);

  const again = await load<Props, string>(path);
  again.create({ parent: null, props: { name: "我" } });
  await again.close();
  expect(existsSync(path)).toBe(true);
});

test("最后一笔没写完的那半行丢掉,前面的照收", async () => {
  const path = join(dir, "tree.jsonl");
  writeFileSync(
    path,
    [
      nodeLine(1, "r"),
      contentLine(2, "r", 0, ["说过的话"]),
      '{"t":3,"node":"r","kind":"content","payload":{"base":1,"adde',
    ].join("\n"), // 崩在最后一笔上：文件就这么断在半行，没有换行收尾
  );

  const store = await load<Props, string>(path);
  expect(store.content("r")).toEqual(["说过的话"]);
  await store.close();
});

test("中间读不动的行当场炸", async () => {
  const path = join(dir, "tree.jsonl");
  writeFileSync(path, [nodeLine(1, "r"), "这不是 JSON", contentLine(3, "r", 0, ["x"])].join("\n") + "\n");
  await expect(load(path)).rejects.toThrow(/第 2 行/);
});

test("内容接不上当场炸", async () => {
  const path = join(dir, "tree.jsonl");
  writeFileSync(path, [nodeLine(1, "r"), contentLine(2, "r", 1, ["x"])].join("\n") + "\n");
  await expect(load(path)).rejects.toThrow(/接不上/);
});

test("父还没出生 / 第二个根当场炸", async () => {
  const orphan = join(dir, "orphan.jsonl");
  writeFileSync(orphan, nodeLine(1, "k", "没有这个父") + "\n");
  await expect(load(orphan)).rejects.toThrow(/父还没出生/);

  const twoRoots = join(dir, "two.jsonl");
  writeFileSync(twoRoots, [nodeLine(1, "a", null), nodeLine(2, "b", null)].join("\n") + "\n");
  await expect(load(twoRoots)).rejects.toThrow(/第二个根/);
});

test("拼接碰上边界就停,而且边界随账一起活下来", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  const root = store.create({ parent: null, props: { name: "根" } });
  const mid = store.create({ parent: root, props: { name: "自带底的一条" }, boundary: true });
  const leaf = store.create({ parent: mid, props: { name: "再往下" } });
  store.append(root, ["根说过"]);
  store.append(mid, ["底"]);
  store.append(leaf, ["往下说的"]);
  expect(store.assemble(leaf)).toEqual(["底", "往下说的"]);
  expect(store.assemble(mid)).toEqual(["底"]);
  expect(store.assemble(root)).toEqual(["根说过"]);
  await store.close();

  const back = await load<Props, string>(path);
  expect(back.get(mid)?.boundary).toBe(true);
  expect(back.assemble(leaf)).toEqual(["底", "往下说的"]);
  await back.close();
});

test("空追加与空补丁不往账里写", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  const root = store.create({ parent: null, props: { name: "我" } });
  store.append(root, []);
  store.patch(root, {});
  await store.close();

  const lines = readFileSync(path, "utf8").trim().split("\n");
  expect(lines).toHaveLength(1);
});

test("攒够一批就落盘,不必等 close", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  const root = store.create({ parent: null, props: { name: "我" } });
  store.append(root, ["x".repeat(70 * 1024)]);

  const lines = readFileSync(path, "utf8").trim().split("\n");
  expect(lines).toHaveLength(2);
  expect(JSON.parse(lines[1] ?? "{}").payload.added[0]).toHaveLength(70 * 1024);
  await store.close();
});

test("子节点顺序就是出生顺序,读回来也是", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  const root = store.create({ parent: null, props: { name: "我" } });
  const kids = [
    store.create({ parent: root, props: { name: "一" } }),
    store.create({ parent: root, props: { name: "二" } }),
    store.create({ parent: root, props: { name: "三" } }),
  ];
  await store.close();

  const back = await load<Props, string>(path);
  expect(back.children(root)).toEqual(kids);
  await back.close();
});

test("拿不存在的节点做事当场报错,get 是唯一宽容的入口", async () => {
  const store = await load<Props, string>(join(dir, "tree.jsonl"));
  expect(store.get("没有这个节点")).toBeNull();
  expect(() => store.children("没有这个节点")).toThrow(/没有这个节点/);
  expect(() => store.content("没有这个节点")).toThrow(/没有这个节点/);
  expect(() => store.append("没有这个节点", ["x"])).toThrow(/没有这个节点/);
  expect(() => store.patch("没有这个节点", { name: "x" })).toThrow(/没有这个节点/);
  expect(() => store.assemble("没有这个节点")).toThrow(/没有这个节点/);
  expect(() => store.create({ parent: "没有这个节点", props: { name: "x" } })).toThrow(/没有这个节点/);
  await store.close();
});

test("第二个根当场报错", async () => {
  const store = await load<Props, string>(join(dir, "tree.jsonl"));
  store.create({ parent: null, props: { name: "我" } });
  expect(() => store.create({ parent: null, props: { name: "又一个我" } })).toThrow(/已经有一个根/);
  await store.close();
});

test("同一份账只能有一个写者", async () => {
  const path = join(dir, "tree.jsonl");
  const store = await load<Props, string>(path);
  await expect(load(path)).rejects.toThrow(/一个写者/);
  await store.close();
  const again = await load<Props, string>(path);
  await again.close();
});
