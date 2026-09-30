/**
 * 树的边界：一轮对话、两条消息、唤醒、取消、重启留下的未完成区、总结分叉。
 *
 * 假传输（脚本化回复）+ 假手（立刻结束的 / 可控的长作业）—— 不碰网络，全在微任务里跑。
 */
import { afterEach, describe, expect, test } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load } from "@meristem/atree";
import type { NodeId } from "@meristem/atree";
import type { Hand, Job, Role, RoleId } from "@meristem/roles";
import { SUMMARY_FORK, background, settled } from "@meristem/roles";
import type { Event } from "../src/events.ts";
import type { LlmClient } from "../src/llm.ts";
import { start } from "../src/tree.ts";
import type { Tree } from "../src/tree.ts";
import { actionable } from "../src/plan.ts";
import type { LineStore } from "../src/props.ts";
import type { Wire, WireMessage } from "../src/shape.ts";

const dirs: string[] = [];

function tmp(): string {
  const dir = mkdtempSync(join(tmpdir(), "meristem-tree-"));
  dirs.push(dir);
  return dir;
}

afterEach(() => {
  for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

/** 只让微任务转地等一个条件（树的推进全是 promise，不需要墙上时钟）。 */
async function until(predicate: () => boolean, what: string): Promise<void> {
  for (let tick = 0; tick < 2000; tick += 1) {
    if (predicate()) return;
    await Promise.resolve();
  }
  throw new Error(`等了 2000 个微任务，条件还没成立：${what}`);
}

/** 让树空转几拍（微任务），用于断言"它**没有**做事"。 */
async function ticks(count = 50): Promise<void> {
  for (let tick = 0; tick < count; tick += 1) await Promise.resolve();
}

/** 脚本化传输：第 n 次调用返回第 n 条回复；把收到的 wire 全记下来供断言。 */
function scripted(replies: readonly WireMessage[]): LlmClient & { readonly wires: Wire[] } {
  const wires: Wire[] = [];
  let at = 0;
  return {
    wires,
    async chat(wire: Wire) {
      wires.push(wire);
      const reply = replies[at];
      at += 1;
      if (reply === undefined) throw new Error("脚本里没有更多回复了（这条线不该再说话）");
      return reply;
    },
  };
}

function reply(content: string, calls: readonly { name: string; args?: unknown }[] = []): WireMessage {
  return {
    id: "transport-tmp-id",
    role: "assistant",
    content,
    ...(calls.length === 0
      ? {}
      : { toolCalls: calls.map((call) => ({ name: call.name, arguments: call.args ?? {} })) }),
  };
}

function role(id: RoleId, hands: readonly Hand[]): Role {
  return {
    id,
    title: id,
    about: id,
    system: () => `你是 ${id}`,
    hands: () => hands,
    findHand(name) {
      const hand = hands.find((candidate) => candidate.name === name);
      if (hand !== undefined) return { kind: "hand", hand };
      const names = hands.map((candidate) => candidate.name).join(" / ");
      return { kind: "missing", answer: `没有叫 ${name} 的手（你有：${names || "一把都没有"}）` };
    },
  };
}

/** 立刻结束的手（`read` / `write` 那一类）。 */
function quickHand(name: string, text: string): Hand {
  return {
    name,
    description: `${name} 的说明`,
    schema: { type: "object", properties: {} },
    async run(_args: unknown, ctx) {
      return settled({ space: ctx.space, name }, text);
    },
  };
}

/** 可控的长作业：拿到手之后由测试决定什么时候结束。 */
function slowHand(name: string): {
  readonly hand: Hand;
  readonly running?: Job;
  release(text: string): void;
  readonly job: () => Job;
} {
  let land: ((text: string) => void) | null = null;
  let current: Job | null = null;
  const hand: Hand = {
    name,
    description: `${name} 的说明`,
    schema: { type: "object", properties: {} },
    async run(_args: unknown, ctx) {
      const { promise: done, resolve } = Promise.withResolvers<string>();
      land = resolve;
      const job = background({
        space: ctx.space,
        name,
        chunks: (async function* () {
          yield "开始吐字";
        })(),
        done,
        stop: () => {},
        timeout: 0,
      });
      current = job;
      return job;
    },
  };
  return {
    hand,
    release: (text: string) => land?.(text),
    job: () => {
      if (current === null) throw new Error("这一手还没被起过");
      return current;
    },
  };
}

interface Booted {
  readonly store: LineStore;
  readonly tree: Tree;
  readonly transport: LlmClient & { readonly wires: Wire[] };
  readonly events: Event[];
}

async function boot(replies: readonly WireMessage[], roles: readonly Role[]): Promise<Booted> {
  return bootWith(scripted(replies), roles);
}

async function bootWith(
  transport: LlmClient & { readonly wires: Wire[] },
  roles: readonly Role[],
): Promise<Booted> {
  const store: LineStore = await load(join(tmp(), "tree.jsonl"));
  const byId = new Map(roles.map((entry) => [entry.id, entry]));
  const tree = start({
    store,
    llm: transport,
    role: (id) => {
      const found = byId.get(id);
      if (found === undefined) throw new Error(`测试里没有这个角色：${id}`);
      return found;
    },
  });
  const events: Event[] = [];
  tree.subscribe((event) => events.push(event));
  return { store, tree, transport, events };
}

const contents = (store: LineStore, node: NodeId): readonly WireMessage[] => store.content(node);

describe("一轮对话", () => {
  test("人分叉说一句 → 模型回一句；账里两条，这条线回到等人", async () => {
    const { store, tree, transport } = await boot([reply("你好"), reply("在的")], [role("talk", [])]);
    tree.resume();

    const node = await tree.fork({ parent: null, role: "talk", inputText: "在吗", dir: tmp() });
    await until(() => contents(store, node).length === 2, "模型回了一句");

    expect(contents(store, node).map((message) => message.role)).toEqual(["user", "assistant"]);
    expect(contents(store, node)[1]?.content).toBe("你好");
    // 账里没有"状态"这个东西：在动还是在等人，读账 + 谁在跑就算得出来。
    expect("state" in (store.get(node)?.props ?? {})).toBe(false);
    expect(transport.wires[0]?.system).toBe("你是 talk");
    expect(transport.wires[0]?.messages.map((message) => message.content)).toEqual(["在吗"]);

    // 账里的 id 是**我们**定死的，不是传输层那个临时 id（§9.6）。
    expect(contents(store, node)[0]?.id).not.toBe("transport-tmp-id");

    await tree.say(node, "再问一句");
    await until(() => contents(store, node).length === 4, "第二次回答");
    expect(contents(store, node).map((message) => message.role)).toEqual([
      "user",
      "assistant",
      "user",
      "assistant",
    ]);
    expect(contents(store, node)[3]?.content).toBe("在的");

    tree.stop();
  });
});

describe("手：起手一条回话、结束一条消息", () => {
  test("立刻结束的手：只留一条回话（内容没变就不写第二次），模型接着往下说", async () => {
    const { store, tree } = await boot(
      [reply("", [{ name: "quick" }]), reply("看完了")],
      [role("work", [quickHand("quick", "结果在这里")])],
    );
    tree.resume();

    const node = await tree.fork({ parent: null, role: "work", inputText: "读一下", dir: tmp() });
    await until(() => contents(store, node).length === 4, "手跑完 + 模型接着说");

    const messages = contents(store, node);
    expect(messages.map((message) => message.role)).toEqual(["user", "assistant", "tool", "assistant"]);
    expect(messages[2]?.content).toBe("结果在这里");
    expect(messages[2]?.by).toBe("quick");
    expect(messages[3]?.content).toBe("看完了");

    tree.stop();
  });

  test("长作业：起手一条「还在跑」，结束时一条 user 消息（同一个作业 id），然后唤醒这条线", async () => {
    const slow = slowHand("long");
    const { store, tree, transport } = await boot(
      [reply("", [{ name: "long" }]), reply("收到")],
      [role("work", [slow.hand])],
    );
    tree.resume();

    const node = await tree.fork({ parent: null, role: "work", inputText: "跑一条长的", dir: tmp() });
    await until(() => contents(store, node).length === 3, "起手一条回话");

    const opened = contents(store, node);
    expect(opened[2]?.role).toBe("tool");
    expect(opened[2]?.content).toContain("还在跑");
    expect(tree.jobs()).toHaveLength(1);

    // 作业还没回来：这条线不该被推（传输只被叫过一次）。
    await ticks();
    expect(transport.wires).toHaveLength(1);

    slow.release("干完了，这是结果");
    await until(() => contents(store, node).length === 5, "结束一条消息 + 模型接着说");

    const settledMessages = contents(store, node);
    expect(settledMessages[3]?.role).toBe("user");
    expect(settledMessages[3]?.by).toBe("long");
    expect(settledMessages[3]?.content).toContain("干完了，这是结果");
    expect(settledMessages[3]?.content).toContain(slow.job().id);
    expect(settledMessages[4]?.content).toBe("收到");
    expect(tree.jobs()).toHaveLength(0);

    tree.stop();
  });

  test("人取消：交代是「被人取消了」，这条线照常继续", async () => {
    const slow = slowHand("long");
    const { store, tree } = await boot(
      [reply("", [{ name: "long" }]), reply("好")],
      [role("work", [slow.hand])],
    );
    tree.resume();

    const node = await tree.fork({ parent: null, role: "work", inputText: "跑", dir: tmp() });
    await until(() => tree.jobs().length === 1, "作业起了");
    tree.cancel(tree.jobs()[0]?.id ?? "");

    await until(() => contents(store, node).length === 5, "取消的交代进了账，模型接着说");
    expect(contents(store, node)[3]?.content).toContain("被人取消了");

    tree.stop();
  });

  test("模型点了一把没有的手：roles 给一句话回给它，这条线接着说（不是缺陷）", async () => {
    const { store, tree, transport } = await boot(
      [reply("", [{ name: "没这把" }]), reply("知道了")],
      [role("work", [])],
    );
    const node = await tree.fork({ parent: null, role: "work", inputText: "随便", dir: tmp() });
    await until(() => contents(store, node).length === 4, "回话 + 接着说");

    const messages = contents(store, node);
    expect(messages.map((message) => message.role)).toEqual(["user", "assistant", "tool", "assistant"]);
    expect(messages[2]?.content).toBe("没有叫 没这把 的手（你有：一把都没有）");
    expect(messages[2]?.by).toBeUndefined();
    expect(transport.wires).toHaveLength(2);

    tree.stop();
  });

  test("手自己起不来（run 抛出）：那是缺陷，把进程打穿（子进程里真跑一遍）", () => {
    const child = Bun.spawnSync([process.execPath, "run", join(import.meta.dir, "defect-child.ts"), tmp()]);

    expect(child.exitCode).toBe(7);
    expect(String(child.stdout)).toContain("账里的话：user,assistant");
    expect(String(child.stderr)).toContain("我起不来");
  });

  test("吐字期间人说的话：排在它后面（账上的顺序就是事情发生的顺序）", async () => {
    const { promise: pending, resolve: answer } = Promise.withResolvers<WireMessage>();
    let calls = 0;
    const wires: Wire[] = [];
    const transport: LlmClient & { readonly wires: Wire[] } = {
      wires,
      async chat(wire: Wire) {
        wires.push(wire);
        calls += 1;
        return calls === 1 ? pending : reply("在的");
      },
    };
    const { store, tree } = await bootWith(transport, [role("talk", [])]);
    const node = await tree.fork({ parent: null, role: "talk", inputText: "在吗", dir: tmp() });
    await until(() => transport.wires.length === 1, "这一轮已经发出去了");

    // 人说话：它**排在还没说完的那一轮后面**（不 await —— 这就是"投给这条线"）。
    const said = tree.say(node, "喂");
    await ticks();
    expect(contents(store, node).map((message) => message.role)).toEqual(["user"]);

    answer(reply("先说这一句"));
    await said;
    expect(contents(store, node).map((message) => message.content)).toEqual([
      "在吗",
      "先说这一句",
      "喂",
      "在的",
    ]);

    tree.stop();
  });

  test("没有谁等谁：A 的一轮还没回来，B 的话照样被接上", async () => {
    const { promise: pending, resolve: answer } = Promise.withResolvers<WireMessage>();
    let calls = 0;
    const wires: Wire[] = [];
    const transport: LlmClient & { readonly wires: Wire[] } = {
      wires,
      async chat(wire: Wire) {
        wires.push(wire);
        calls += 1;
        return calls === 1 ? pending : reply("B 的回答");
      },
    };
    const { store, tree } = await bootWith(transport, [role("talk", [])]);
    tree.resume();

    const slow = await tree.fork({ parent: null, role: "talk", inputText: "慢慢来", dir: tmp() });
    await until(() => wires.length === 1, "A 那一轮已经发出去了");

    const quick = await tree.fork({ parent: null, role: "talk", inputText: "快回我", dir: tmp() }).catch(() => null);
    // 造根只能有一个：第二条线从 A 分出来。
    const other = quick ?? (await tree.fork({ parent: slow, role: "talk", inputText: "快回我", dir: tmp() }));
    await until(() => contents(store, other).length === 2, "B 的话被接上了，尽管 A 还没回来");

    expect(contents(store, slow)).toHaveLength(1);
    answer(reply("A 的回答"));
    await until(() => contents(store, slow).length === 2, "A 的回答也到了");

    tree.stop();
  });
});

describe("模型接口失败：算人的", () => {
  test("账里一个字都不多、不自动重试；人重试之后这条线继续", async () => {
    let first = true;
    const wires: Wire[] = [];
    const transport: LlmClient & { readonly wires: Wire[] } = {
      wires,
      async chat(wire: Wire) {
        wires.push(wire);
        if (first) {
          first = false;
          throw new Error("502 网关抽风");
        }
        return reply("回来了");
      },
    };
    const { store, tree, events } = await bootWith(transport, [role("talk", [])]);
    tree.resume();

    const node = await tree.fork({ parent: null, role: "talk", inputText: "在吗", dir: tmp() });
    await until(() => events.some((event) => event.type === "transport_error"), "红字事件");

    expect(contents(store, node).map((message) => message.role)).toEqual(["user"]);
    expect(events.some((event) => event.type === "transport_error")).toBe(true);
    expect(wires).toHaveLength(1);

    tree.retry(node);
    await until(() => contents(store, node).length === 2, "重试之后有回话了");
    expect(contents(store, node)[1]?.content).toBe("回来了");

    tree.stop();
  });
});

describe("重启留下的未完成区", () => {
  test("伸出去了、没回话的手（重启后的未完成区）：这条线整条停住（人说话也不推进）", async () => {
    const { store, tree, transport } = await boot([reply("不该被叫到")], [role("talk", [])]);
    // 模拟"进程崩在起手与结束之间"：账里就是那个形状，然后**重启**（resume 就是那条路）。
    const node = store.create({
      parent: null,
      props: { name: "崩过的一条", role: "talk", outputRoot: tmp() },
    });
    store.append(node, [
      { id: "崩-1", role: "user", content: "在吗" },
      {
        id: "崩-2",
        role: "assistant",
        content: "我起了一手",
        toolCalls: [{ name: "bash", arguments: {} }],
      },
    ]);

    tree.resume();
    await ticks();
    expect(actionable(store, node, false)).toBe(false);
    expect(transport.wires).toHaveLength(0);

    // 人插话也不推进：账上不编那条回话（要接着干就分叉一条新线）。
    await tree.say(node, "怎么样了");
    await ticks();
    expect(transport.wires).toHaveLength(0);
    expect(contents(store, node).map((message) => message.role)).toEqual(["user", "assistant", "user"]);

    tree.stop();
  });
});

describe("总结分叉", () => {
  test("三步：造线 → 穿总结角色抽底（by=乙）→ 穿过人选的角色回应（by=丙）", async () => {
    const { store, tree, transport } = await boot(
      [reply("父线的第一句回答"), reply("父亲这一枝做过的事"), reply("按你说的办")],
      [role("talk", []), role("other", []), role(SUMMARY_FORK, [])],
    );
    tree.resume();

    const parent = await tree.fork({ parent: null, role: "talk", inputText: "先聊两句", dir: tmp() });
    await until(() => contents(store, parent).length === 2, "父线有一条回答");

    const child = await tree.fork({
      parent,
      role: "other",
      inputText: "换个方向接着干",
      mode: "summarize",
    });
    await until(() => contents(store, child).length === 3, "总结与回应都进了账");

    const messages = contents(store, child);
    expect(messages.map((message) => message.role)).toEqual(["user", "assistant", "assistant"]);
    expect(messages[1]?.by).toBe(SUMMARY_FORK);
    expect(messages[1]?.content).toBe("父亲这一枝做过的事");
    expect(messages[2]?.by).toBeUndefined();
    expect(messages[2]?.content).toBe("按你说的办");

    // 乙 那一轮看的是"父线看得见的历史 + 这条新消息"；丙 那一轮看的是新线自己看得见的。
    const summaryWire = transport.wires.at(-2);
    expect(summaryWire?.system).toContain(SUMMARY_FORK);
    expect(summaryWire?.messages.map((message) => message.role)).toEqual([
      "user",
      "assistant",
      "user",
    ]);
    const replyWire = transport.wires.at(-1);
    expect(replyWire?.system).toBe("你是 other");
    expect(replyWire?.messages.map((message) => message.role)).toEqual(["user", "assistant"]);

    // 新线自带边界：它自己看得见的就是它自己的三句，父线那两句不跟过来。
    expect(store.assemble(child)).toHaveLength(3);

    tree.stop();
  });
});

describe("收手", () => {
  test("收手：不再叫任何线，并把在跑的作业收掉", async () => {
    const slow = slowHand("long");
    const { store, tree } = await boot([reply("", [{ name: "long" }]), reply("不该被叫到")], [role("work", [slow.hand])]);
    const node = await tree.fork({ parent: null, role: "work", inputText: "跑", dir: tmp() });
    await until(() => tree.jobs().length === 1, "作业起了");

    tree.stop();
    expect(tree.jobs()).toHaveLength(0);
    await until(() => contents(store, node).some((message) => message.content.includes("被人取消了")), "取消的交代进账");
  });
});
