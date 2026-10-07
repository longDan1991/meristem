/**
 * 命令表（`command/commands.ts`）：**装载是 fail-closed 的** —— 读不成 / 版本不对 / 字段拼错 /
 * id 形状不对 / 名字与键重复 / 键写成裸字符，任一条都在**从路径建表**的时候当场抛，不静默降级。
 * 另外两条是这个模块的读法：作用面与屏名从 id 推出来、键能查到命令（连它带的参数）。
 *
 * 表是从**路径**建出来的（真实应用给的是自己的 `registry/commands.yaml`），所以这里把各种写错的样子
 * 写进临时 yaml 再建一次 —— 验的就是装载那条路，而不是某个内部函数。
 */
import { describe, expect, test } from "bun:test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Commands } from "../src/command/commands.ts";

const DIR = mkdtempSync(join(tmpdir(), "meristem-commands-"));
let serial = 0;

/** 这一份用例的作用面词表（应用自己的词，真实应用自己给一份）。 */
const LAYERS = ["screen", "app", "turn", "view", "list"];

/** 把一份表写成 yaml 落盘，再按路径建出来 —— 一份最小可用的表（够过校验），用来拼各种写错的版本。 */
function tableOf(...entries: readonly Record<string, unknown>[]): Commands {
  serial += 1;
  const path = join(DIR, `commands-${serial.toString()}.yaml`);
  const commands = entries.map((entry) => ({ id: "app.x", desc: "一件事", ...entry }));
  writeFileSync(path, Bun.YAML.stringify({ version: 1, commands }));
  return new Commands(path, LAYERS);
}

function one(entry: Record<string, unknown>): Commands {
  return tableOf(entry);
}

function throws(entry: Record<string, unknown>): string {
  try {
    one(entry);
  } catch (error) {
    return error instanceof Error ? error.message : String(error);
  }
  throw new Error("本该抛错，却没有");
}

describe("装一份表", () => {
  test("读不出来（路径不对）当场说清是哪个文件", () => {
    expect(() => new Commands(join(DIR, "没有这个文件.yaml"), LAYERS)).toThrow(/命令表读不出来/);
  });

  test("yaml 不是对象 / 版本不对 / commands 不是数组", () => {
    serial += 1;
    const path = join(DIR, `bad-${serial.toString()}.yaml`);
    writeFileSync(path, "- 一\n- 二\n");
    expect(() => new Commands(path, LAYERS)).toThrow(/要是一个对象/);

    const parsed = one({});
    expect(parsed.byId("app.x")?.desc).toBe("一件事");

    serial += 1;
    const wrong = join(DIR, `v2-${serial.toString()}.yaml`);
    writeFileSync(wrong, Bun.YAML.stringify({ version: 2, commands: [] }));
    expect(() => new Commands(wrong, LAYERS)).toThrow(/version 要是 1/);

    serial += 1;
    const notArray = join(DIR, `list-${serial.toString()}.yaml`);
    writeFileSync(notArray, Bun.YAML.stringify({ version: 1, commands: "不是数组" }));
    expect(() => new Commands(notArray, LAYERS)).toThrow(/commands 要是一个数组/);
  });

  test("缺省的字段读出来是 null / 空数组（不是 undefined 到处漏）", () => {
    const table = one({});
    const command = table.byId("app.x");
    expect(command?.name).toBeNull();
    expect(command?.hint).toBeNull();
    expect(command?.args).toBeNull();
    expect(command?.aliases).toEqual([]);
    expect(command?.words).toEqual([]);
    expect(command?.keys).toEqual([]);
  });
});

describe("id 读出来的那两件", () => {
  test("`screen` 与 `words` 都不是表里的字段", () => {
    const table = tableOf({ id: "screen.role", name: "role", aliases: ["r"] });
    const command = table.byId("screen.role");
    expect(command?.screen).toBe("role");
    expect(command?.words).toEqual(["role", "r"]);
    expect(command?.layer).toBe("screen");
    expect(one({ id: "app.quit" }).byId("app.quit")?.screen).toBeNull();
  });

  test("按 id / 按屏名找得到，找不到就是 undefined", () => {
    const table = tableOf({ id: "screen.model", name: "model" });
    expect(table.byScreen("model")?.id).toBe("screen.model");
    expect(table.byScreen("main")).toBeUndefined();
    expect(table.byId("screen.nope")).toBeUndefined();
  });
});

describe("按名字匹配（敲 / 之后那张名单）", () => {
  const table = tableOf({ id: "screen.keys", name: "help", aliases: ["?"] }, { id: "app.quit", name: "quit" });

  test("一个斜杠就是全部有名字的；前缀优先，其次是包含", () => {
    expect(table.matches("/")).toHaveLength(2);
    expect(table.matches("/he")[0]?.name).toBe("help");
    expect(table.matches("/?")[0]?.name).toBe("help");
    expect(table.matches("/ui")[0]?.name).toBe("quit");
    expect(table.matches("/zzz")).toEqual([]);
  });

  test("没有斜杠名字的那些不上名单", () => {
    const withWalk = tableOf({ id: "list.next", desc: "往下走一位" });
    expect(withWalk.named()).toEqual([]);
    expect(withWalk.matches("/")).toEqual([]);
  });
});

describe("写错了要当场炸", () => {
  test("id 的第一段必须是作用面", () => {
    expect(throws({ id: "do.magic" })).toMatch(/第一段要是作用面/);
    // 词表是调用方给的：不在表里的词当场报出来，连可选项一起说清
    expect(throws({ id: "do.magic" })).toContain("screen / app / turn / view / list");
  });

  test("id 要写成 作用面.名字", () => {
    expect(throws({ id: "screen" })).toMatch(/作用面\.名字/);
    expect(throws({ id: "screen.Model" })).toMatch(/作用面\.名字/);
    expect(throws({ id: "app." })).toMatch(/作用面\.名字/);
  });

  test("换屏的 id 只有两段（第二段就是屏名）", () => {
    expect(throws({ id: "screen.a.b" })).toMatch(/第二段就是屏名/);
  });

  test("id 重复", () => {
    expect(() => tableOf({ id: "app.a", desc: "一" }, { id: "app.a", desc: "二" })).toThrow(/出现两次/);
  });

  test("名字与别名重复", () => {
    expect(throws({ name: "help", aliases: ["help"] })).toMatch(/出现两次/);
  });

  test("同一个键挂两条命令", () => {
    const bad = () =>
      tableOf(
        { id: "app.a", desc: "一", keys: [{ key: "ctrl+x" }] },
        { id: "app.b", desc: "二", keys: [{ key: "ctrl+x" }] },
      );
    expect(bad).toThrow(/挂在两条命令上/);
  });

  test("裸字符不是界面能认领的键（那是打字）", () => {
    expect(throws({ keys: [{ key: "j" }] })).toMatch(/裸字符/);
    expect(() => one({ keys: [{ key: " " }] })).toThrow(); // 空白键先被"非空的话"挡下，同样当场炸
  });

  test("修饰键次序不对、名字不认识", () => {
    expect(throws({ keys: [{ key: "alt+ctrl+b" }] })).toMatch(/不是界面能认领的写法/);
    expect(throws({ keys: [{ key: "super+b" }] })).toMatch(/不是界面能认领的写法/);
    expect(throws({ keys: [{ key: "nope" }] })).toMatch(/不是界面能认领的写法/);
  });

  test("字段拼错也算写错（不静默变成没有这个能力）", () => {
    expect(throws({ key: "ctrl+x" })).toMatch(/不认识的字段/);
    expect(throws({ opens: "keys" })).toMatch(/不认识的字段/);
    expect(throws({ when: "list-open" })).toMatch(/不认识的字段/);
  });

  test("一条命令要有一句 desc", () => {
    expect(throws({ desc: "" })).toMatch(/desc 要是一句非空的话/);
  });
});
