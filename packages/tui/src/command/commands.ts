/**
 * 命令表：**一份 yaml 进来，界面认得的全部命令出去** —— 斜杠名字、别名、键、参数提示、
 * 键行写的几个字。它是命令模块的"展示那一半"（另一半是 `bus.tsx`：谁按了、归谁做）。
 *
 * **从路径建一份表**（不是一个写死路径的模块单例）：表是随应用发布的数据，路径由装载它的那一方给
 * （`packages/terminal` 给 `<包>/registry/commands.yaml`）—— 本包不认识任何应用把文件放哪。
 * 同一个进程只建一次：构造时读文件、校验、把查找用的索引一次建好。
 *
 * **作用面的词表也由调用方给**：`screen` / `turn` / `view` 这些是**应用自己的词**（它拿它们分组命令、
 * 决定谁接），本包不认识它们，只拿这张表把 id 的第一段卡住（写错一个作用面当场炸）。
 * 唯一在本包里有约定的是 `screen` —— **路由那一层**：`screen.<屏名>` 的第二段就是屏名，
 * 进屏那条订阅（`screen.*`）与 `byScreen` 都读它（路由也在本包，所以这条约定住在这儿）。
 *
 * **id 就是作用域路径**（点串起来：`screen.model` / `turn.fork` / `list.next`）：
 * 第一段是作用面，于是**作用面、进哪一屏**都从 id 读出来，表里不再声明一遍。表里只有展示的字段，
 * 没有"谁接 / 什么条件下接 / 做什么"—— 那是订阅方（`useCommand`）的事。
 *
 * **装载 fail-closed**（照 roles 的 xml 注册表）：读不成、不是对象、版本不对、字段拼错、id 形状不对、
 * 第一段不在词表里、名字或别名重复、同一个键挂在两条上、键写成裸字符（那是打字）—— 任一条当场抛，
 * 不静默跳过、不降级成半个表。
 *
 * 变因：从 yaml 读出来的那些命令长什么样、怎么查（以及装载时拒绝什么）。
 */
import { readFileSync } from "node:fs";
import { isKeySpec } from "./keys.ts";

/** id 的第一段：命令的**作用面**（应用自己的词，由调用方给词表）。 */
export type Layer = string;

/** 一个键挂在一条命令上；`arg` = 这个键调用它时带的固定参数（分叉的两个口味就靠它）。 */
export interface KeyBinding {
  readonly key: string;
  readonly arg?: string;
}

export interface Command {
  /** 作用域路径（`screen.model`）：斜杠名字与键都挂在它下面，订阅也按它找。 */
  readonly id: string;
  readonly layer: Layer;
  /** 进哪一屏（`screen.*` 的第二段）；不是进屏的命令就是 `null`。**从 id 读出来**，不是表里的字段。 */
  readonly screen: string | null;
  /** 斜杠名字；`null` = 只有键、没有斜杠名字（走位那种）。 */
  readonly name: string | null;
  readonly aliases: readonly string[];
  /** 匹配用的那些字（名字在最前，含别名）。**从 name 与 aliases 读出来**，不是表里的字段。 */
  readonly words: readonly string[];
  readonly desc: string;
  /** 键行右端写的那几个字（`null` = 不进键行）。只有"做事"的那几条写它。 */
  readonly hint: string | null;
  /** 给人看的参数提示（`[provider/model]`），不解析。 */
  readonly args: string | null;
  readonly keys: readonly KeyBinding[];
}

/** 按了某个键之后要找的那两件：哪条命令、连它这次的参数。 */
export interface KeyHit {
  readonly command: Command;
  readonly binding: KeyBinding;
}

/** 一条命令允许有的字段：多一个就是写错了（拼错字段不该静默变成"没有这个能力"）。 */
const FIELDS = ["id", "name", "aliases", "desc", "hint", "args", "keys"];

/** 一段名字的形状：小写字母开头，只含小写字母、数字、连字符。 */
const SEGMENT = /^[a-z][a-z0-9-]*$/;

/** 名字要这个形状；别名可以再松一点（`?` 是 `/?` 的别名），照样是一串不含空白的字。 */
const NAME_SHAPE = /^[a-z][a-z0-9-]*$/;
const ALIAS_SHAPE = /^[a-z0-9?.-]+$/;

function fail(where: string, why: string): never {
  throw new Error(`命令表 ${where}：${why}`);
}

function record(value: unknown, where: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) fail(where, "要是一个对象");
  return value as Record<string, unknown>;
}

function text(value: unknown, where: string, field: string): string {
  if (typeof value !== "string" || value.trim() === "") fail(where, `${field} 要是一句非空的话`);
  return value;
}

function optional(value: unknown, where: string, field: string): string | null {
  return value === undefined || value === null ? null : text(value, where, field);
}

function words(value: unknown, where: string, field: string): readonly string[] {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) fail(where, `${field} 要是一个数组`);
  return value.map((item) => text(item, where, field));
}

/** id 的作用面与屏名（就这两件从 id 读出来）；词表由调用方给。 */
function split(
  id: string,
  where: string,
  layers: readonly Layer[],
): { readonly layer: Layer; readonly screen: string | null } {
  const parts = id.split(".");
  const head = parts[0] ?? "";
  if (!layers.includes(head)) {
    fail(where, `id「${id}」的第一段要是作用面（${layers.join(" / ")}）`);
  }
  const rest = parts.slice(1);
  if (rest.length === 0 || rest.some((segment) => !SEGMENT.test(segment))) {
    fail(where, `id「${id}」要写成 作用面.名字（小写字母开头，只含小写字母数字连字符）`);
  }
  const layer = head;
  // `screen` 是本包（路由）那一层：它的第二段就是屏名，只有一段。
  if (layer === "screen" && rest.length !== 1) {
    fail(where, `id「${id}」是换屏：第二段就是屏名，只有一个（读到 ${rest.length} 段）`);
  }
  return { layer, screen: layer === "screen" ? (rest[0] ?? null) : null };
}

function one(value: unknown, where: string, layers: readonly Layer[]): Command {
  const entry = record(value, where);
  for (const key of Object.keys(entry)) {
    if (!FIELDS.includes(key)) fail(where, `不认识的字段「${key}」`);
  }

  const id = text(entry.id, where, "id");
  const { layer, screen } = split(id, where, layers);
  const desc = text(entry.desc, where, "desc");
  const name = optional(entry.name, where, "name");
  if (name !== null && !NAME_SHAPE.test(name)) {
    fail(where, `名字「${name}」要是小写字母开头、只含小写字母数字连字符`);
  }
  const aliases = words(entry.aliases, where, "aliases");
  for (const alias of aliases) {
    if (!ALIAS_SHAPE.test(alias)) fail(where, `别名「${alias}」的形状不对`);
  }

  if (entry.keys !== undefined && entry.keys !== null && !Array.isArray(entry.keys)) {
    fail(where, "keys 要是一个数组");
  }
  const raw: readonly unknown[] = Array.isArray(entry.keys) ? entry.keys : [];
  const keys = raw.map((item) => binding(item, where));

  return {
    id,
    layer,
    screen,
    name,
    aliases,
    words: name === null ? aliases : [name, ...aliases],
    desc,
    hint: optional(entry.hint, where, "hint"),
    args: optional(entry.args, where, "args"),
    keys,
  };
}

function binding(value: unknown, where: string): KeyBinding {
  if (typeof value === "string") {
    return { key: keyOf(value, where) };
  }
  const entry = record(value, `${where} 的 keys`);
  for (const key of Object.keys(entry)) {
    if (key !== "key" && key !== "arg") fail(where, `keys 里不认识的字段「${key}」`);
  }
  const arg = optional(entry.arg, where, "arg");
  const key = keyOf(text(entry.key, where, "key"), where);
  return arg === null ? { key } : { key, arg };
}

function keyOf(text: string, where: string): string {
  if (!isKeySpec(text)) fail(where, `键「${text}」不是界面能认领的写法（裸字符是打字，归输入件）`);
  return text;
}

/** 一份 yaml（已经是对象）：逐条校验，任何一条不对就抛。 */
function parse(doc: unknown, source: string, layers: readonly Layer[]): readonly Command[] {
  const top = record(doc, source);
  for (const key of Object.keys(top)) {
    if (key !== "version" && key !== "commands") fail(source, `不认识的字段「${key}」（只有 version 与 commands）`);
  }
  if (top.version !== 1) fail(source, `version 要是 1（读到 ${JSON.stringify(top.version)}）`);
  if (!Array.isArray(top.commands)) fail(source, "commands 要是一个数组");

  const commands = top.commands.map((item, index) => one(item, `${source} 第 ${index + 1} 条`, layers));
  unique(commands, source);
  return commands;
}

/** 同一份表里：id、斜杠名字与别名、键 —— 各自只许出现一次（一份语义只允许一份实现）。 */
function unique(commands: readonly Command[], source: string): void {
  const ids = new Set<string>();
  const names = new Set<string>();
  const keys = new Set<string>();
  for (const command of commands) {
    if (ids.has(command.id)) fail(source, `id「${command.id}」出现两次`);
    ids.add(command.id);
    for (const word of [command.name, ...command.aliases]) {
      if (word === null) continue;
      if (names.has(word)) fail(source, `名字或别名「${word}」出现两次（${command.id}）`);
      names.add(word);
    }
    for (const binding of command.keys) {
      if (keys.has(binding.key)) fail(source, `键「${binding.key}」挂在两条命令上（${command.id}）`);
      keys.add(binding.key);
    }
  }
}

/** 一份装好的命令表：构造时读文件校验，之后只读。 */
export class Commands {
  /** 表里的全部命令，顺序就是 yaml 里的顺序（提示那一列按它排）。 */
  readonly all: readonly Command[];
  private readonly ids: ReadonlyMap<string, Command>;
  private readonly hits: ReadonlyMap<string, KeyHit>;
  /** 有斜杠名字的那些（命令名单与键位表走它）。 */
  private readonly withName: readonly Command[];

  /** 从一个 yaml 路径建一份表（读不成 / 写错了当场抛）；`layers` = 这个应用自己的作用面词表。 */
  constructor(yamlPath: string, layers: readonly Layer[]) {
    let source: string;
    try {
      source = readFileSync(yamlPath, "utf8");
    } catch (error) {
      throw new Error(`命令表读不出来（${yamlPath}）：${error instanceof Error ? error.message : String(error)}`);
    }
    this.all = parse(Bun.YAML.parse(source), yamlPath, layers);

    const ids = new Map<string, Command>();
    const hits = new Map<string, KeyHit>();
    for (const command of this.all) {
      ids.set(command.id, command);
      for (const binding of command.keys) hits.set(binding.key, { command, binding });
    }
    this.ids = ids;
    this.hits = hits;
    this.withName = this.all.filter((command) => command.name !== null);
  }

  byId(id: string): Command | undefined {
    return this.ids.get(id);
  }

  /** 这个键归哪条命令（连带它带的参数）；没这条命令就是 `undefined`。 */
  byKey(key: string): KeyHit | undefined {
    return this.hits.get(key);
  }

  /** 进某一屏的那条命令（**路由那一层**：屏名就是 `screen.<屏名>` 的第二段）。 */
  byScreen(screen: string): Command | undefined {
    return this.ids.get(`screen.${screen}`);
  }

  /** 有斜杠名字的那些（顺序同 yaml）。 */
  named(): readonly Command[] {
    return this.withName;
  }

  /** 敲 `/` 之后那串字能匹配哪些命令（`draft` 含开头那个 `/`；只打一个 `/` 就是全部）。 */
  matches(draft: string): readonly Command[] {
    const query = draft.startsWith("/") ? draft.slice(1) : draft;
    if (query === "") return this.withName;
    const head = this.withName.filter((command) => command.words.some((word) => word.startsWith(query)));
    const rest = this.withName.filter(
      (command) => !head.includes(command) && command.words.some((word) => word.includes(query)),
    );
    return [...head, ...rest];
  }

  /** 指不到路由表里的那些屏名（空数组 = 都对得上）。 */
  missingScreens(names: readonly string[]): readonly string[] {
    const known = new Set(names);
    return this.all.flatMap((command) =>
      command.screen === null || known.has(command.screen) ? [] : [command.screen],
    );
  }
}
