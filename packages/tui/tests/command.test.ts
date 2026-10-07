/**
 * 命令总线（纯的那一半）的语义，四条：**后出现的先收**、**一层只跑一个**、**没人接就当没这回事**、
 * **`live` 与 `ask` 同一个判据**（所以"写出来的键"与"按得动的键"不可能对不上）。
 *
 * 这几条不是实现细节：P0 §1 决策 4 的判据就是"收掉**最后出现**的那一层"，而"只跑一个"是
 * `esc` 一次只收一层的全部依据。所以它们各错一次都得有人知道。
 */
import { describe, expect, test } from "bun:test";
import { createRegistry, matches } from "../src/command/registry.ts";

describe("matches", () => {
  test("精确的一条只匹配它自己", () => {
    expect(matches("view.tier", "view.tier")).toBe(true);
    expect(matches("view.tier", "view.side")).toBe(false);
    expect(matches("app.close", "app.closed")).toBe(false);
  });

  test("`前缀.*` 匹配整层，但不越界到名字相近的另一层", () => {
    expect(matches("screen.*", "screen.model")).toBe(true);
    expect(matches("screen.*", "screen.a.b")).toBe(true);
    expect(matches("screen.*", "screen")).toBe(false);
    expect(matches("screen.*", "screens.model")).toBe(false);
    expect(matches("list.*", "list.prev")).toBe(true);
    expect(matches("list.*", "view.tier")).toBe(false);
  });
});

describe("ask", () => {
  test("没人接：不跑任何东西，回 false", () => {
    const calls: string[] = [];
    const registry = createRegistry();
    expect(registry.ask("view.tier")).toBe(false);
    expect(calls).toEqual([]);
  });

  test("一层只跑一个：两个都接同一条时，后面的那个跑（后出现的先收）", () => {
    const calls: string[] = [];
    const registry = createRegistry();
    registry.subscribe("app.close", () => calls.push("先出现的"));
    registry.subscribe("app.close", () => calls.push("后出现的"));
    expect(registry.ask("app.close")).toBe(true);
    expect(calls).toEqual(["后出现的"]);
  });

  test("退订之后次序回到前一个（收掉一层就摘掉，靠的就是这个）", () => {
    const calls: string[] = [];
    const registry = createRegistry();
    registry.subscribe("app.close", () => calls.push("名单"));
    const off = registry.subscribe("app.close", () => calls.push("侧边"));
    registry.ask("app.close");
    off();
    registry.ask("app.close");
    expect(calls).toEqual(["侧边", "名单"]);
  });

  test("通配与具体混着挂：谁后挂谁先被问（同一层的两条命令互不干扰）", () => {
    const calls: string[] = [];
    const registry = createRegistry();
    registry.subscribe("list.*", (id) => calls.push(`名单：${id}`));
    registry.subscribe("list.prev", (id) => calls.push(`树：${id}`));
    registry.ask("list.prev");
    registry.ask("list.next");
    expect(calls).toEqual(["树：list.prev", "名单：list.next"]);
  });

  test("参数照传（分叉的两个口味靠它，不是靠两条 id）", () => {
    const seen: (string | undefined)[] = [];
    const registry = createRegistry();
    registry.subscribe("turn.fork", (_id, arg) => seen.push(arg));
    registry.ask("turn.fork", "summarize");
    registry.ask("turn.fork");
    expect(seen).toEqual(["summarize", undefined]);
  });
});

describe("live", () => {
  test("挂上来才算有接的人；摘掉就没有了", () => {
    const registry = createRegistry();
    expect(registry.live("app.close")).toBe(false);
    const off = registry.subscribe("app.close", () => {});
    expect(registry.live("app.close")).toBe(true);
    off();
    expect(registry.live("app.close")).toBe(false);
  });

  test("通配订阅算它覆盖的每一条", () => {
    const registry = createRegistry();
    registry.subscribe("screen.*", () => {});
    expect(registry.live("screen.model")).toBe(true);
    expect(registry.live("screen.role")).toBe(true);
    expect(registry.live("view.tier")).toBe(false);
  });
});
