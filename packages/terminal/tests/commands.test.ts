/**
 * **随代码发布的那一份表**（`registry/commands.yaml`）：它装得上、八屏都进得去、键都对得上 ——
 * 装载校验那部分在命令模块自己的用例里（`packages/tui/tests/commands.test.ts`），
 * 这一份只管**这一份文件的内容**是不是我们要的。
 */
import { describe, expect, test } from "bun:test";
import { Commands } from "@meristem/tui";
import { COMMANDS_PATH, LAYERS } from "../src/registry.ts";

const TABLE = new Commands(COMMANDS_PATH, LAYERS);

describe("这一份表", () => {
  test("换屏的那些：id 的第二段就是屏名，八屏里七个要「进」（默认那一屏不用）", () => {
    const screens = TABLE.all.flatMap((command) => (command.screen === null ? [] : [command.screen]));
    expect(screens).toEqual(["role", "model", "keys", "copy", "search", "about", "diagnostics"]);
    expect(TABLE.byScreen("main")).toBeUndefined();
    expect(TABLE.byScreen("model")?.id).toBe("screen.model");
  });

  test("五个作用面都在用，每条命令都有 id、作用面与一句 desc", () => {
    const layers = new Set(TABLE.all.map((command) => command.layer));
    expect([...layers].sort()).toEqual(["app", "list", "screen", "turn", "view"]);
    expect(TABLE.all.every((command) => command.id !== "" && command.desc !== "")).toBe(true);
  });

  test("名字与别名都不重复", () => {
    const words = TABLE.all.flatMap((command) => command.words);
    expect(new Set(words).size).toBe(words.length);
  });

  test("按定下来的键找得到命令（连它带的参数）", () => {
    expect(TABLE.byKey("alt+m")?.command.id).toBe("screen.model");
    expect(TABLE.byKey("ctrl+r")?.command.id).toBe("screen.search");
    expect(TABLE.byKey("alt+a")?.command.id).toBe("screen.role");
    expect(TABLE.byKey("alt+t")?.command.id).toBe("view.tier");
    expect(TABLE.byKey("alt+s")?.command.id).toBe("view.side");
    expect(TABLE.byKey("alt+p")?.command.id).toBe("view.side-page");
    expect(TABLE.byKey("alt+r")?.command.id).toBe("turn.retry");
    expect(TABLE.byKey("up")?.command.id).toBe("list.prev");
    expect(TABLE.byKey("ctrl+b")?.binding.arg).toBe("inherit");
    expect(TABLE.byKey("alt+b")?.binding.arg).toBe("summarize");
    expect(TABLE.byKey("nope")).toBeUndefined();
  });

  test("敲 / 之后：一个斜杠是全部名单，打了字按名字与别名过滤，前缀优先", () => {
    expect(TABLE.matches("/")).toHaveLength(TABLE.named().length);
    expect(TABLE.matches("/he")[0]?.name).toBe("help");
    expect(TABLE.matches("/?")[0]?.name).toBe("help");
    expect(TABLE.matches("/ver")[0]?.name).toBe("changelog");
    expect(TABLE.matches("/zzz")).toEqual([]);
  });

  test("`esc` 只管视线层：取消某一手已经不在这张表里了", () => {
    const closing = TABLE.all.filter((command) => command.id === "app.close");
    expect(closing).toHaveLength(1);
    expect(TABLE.byId("turn.cancel")).toBeUndefined();
  });
});

describe("装配核对：屏名指得到吗", () => {
  test("对得上就是空数组", () => {
    expect(TABLE.missingScreens(["role", "model", "keys", "copy", "search", "about", "diagnostics"])).toEqual([]);
  });

  test("指不到的名字会被报出来", () => {
    expect(TABLE.missingScreens(["role"])).toContain("model");
  });
});
