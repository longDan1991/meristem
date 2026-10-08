/**
 * 键行的键提示：**有接的人才写**（问总线），且最多占给定格数（放不下掐尾巴补 `…`）。
 *
 * 表用的是**随代码发布的那一份**（提示那一条依赖表里的 `hint` 字段，所以拿真表验才有意义）；
 * 总线是一份**假的**（只回 `live`）：提示只依赖"谁挂上来了"，不依赖谁去做。
 */
import { describe, expect, test } from "bun:test";
import { Commands } from "@meristem/tui";
import type { CommandBus } from "@meristem/tui";
import { keyHints } from "../src/lib/hints.ts";
import { COMMANDS_PATH, LAYERS } from "../src/registry.ts";

/** 随代码发布的那一份表（提示里的字面量都从它来）。 */
const TABLE = new Commands(COMMANDS_PATH, LAYERS);

function busOf(...live: readonly string[]): CommandBus {
  const set = new Set(live);
  return { ask: () => false, live: (id) => set.has(id) };
}

/** 宽预算：看得见全部提示（120 格画布上，留够左端之后右端大约有这么多）。 */
const ROOM = 200;

describe("keyHints", () => {
  test("一条都没人接：什么都不写", () => {
    expect(keyHints(TABLE, busOf(), ROOM)).toBe("");
  });

  test("只写有接的人的那些，且换屏的七条不在里面（它们走 `/` 名单）", () => {
    const hints = keyHints(TABLE, busOf("turn.fork", "turn.stop", "app.close", "app.quit", "view.tier"), ROOM);
    expect(hints).toContain("ctrl+b 分叉");
    expect(hints).toContain("ctrl+x 收手");
    expect(hints).toContain("alt+l 换档");
    expect(hints).not.toContain("alt+m");
    expect(hints).not.toContain("/");
  });

  test("档与侧边只在主屏上写：主屏不在（没人接 `view.*`）就不写它们，壳上的那几条照写", () => {
    const elsewhere = keyHints(TABLE, busOf("turn.stop", "app.close", "app.quit"), ROOM);
    expect(elsewhere).not.toContain("alt+l");
    expect(elsewhere).not.toContain("alt+k");
    expect(elsewhere).toContain("ctrl+x 收手");
    expect(elsewhere).toContain("escape 收掉这一层");
  });

  test("`esc` 只在真有可收的层时才写（没人接 `app.close` 就不写）", () => {
    expect(keyHints(TABLE, busOf("turn.stop"), ROOM)).not.toContain("escape");
    expect(keyHints(TABLE, busOf("turn.stop", "app.close"), ROOM)).toContain("escape 收掉这一层");
  });

  test("顺序就是命令表里的顺序（分叉 → 收手 → 换档，表里怎么写就怎么排）", () => {
    const hints = keyHints(TABLE, busOf("turn.fork", "turn.stop", "view.tier"), ROOM);
    expect(hints.indexOf("ctrl+b 分叉")).toBeLessThan(hints.indexOf("ctrl+x 收手"));
    expect(hints.indexOf("ctrl+x 收手")).toBeLessThan(hints.indexOf("alt+l 换档"));
  });

  test("放不下就掐掉并说出来；一条都放不下也说一声", () => {
    const roomy = keyHints(TABLE, busOf("turn.fork", "turn.stop", "view.tier"), ROOM);
    const tight = keyHints(TABLE, busOf("turn.fork", "turn.stop", "view.tier"), 20);
    expect(tight.length).toBeLessThan(roomy.length);
    expect(tight.endsWith("…")).toBe(true);
    expect(tight).toContain("ctrl+b 分叉");
    expect(keyHints(TABLE, busOf("turn.fork"), 4)).toBe("…");
  });
});
