/**
 * 屏与键**真的按一遍**：真渲染器 + 真按键 + 真帧。
 *
 * 为什么要有这一条（而不是只测纯函数）：命令的**执行**是各层自己就近挂上来的（`useCommand`），
 * 装载期看不到全貌 —— "这条命令有没有人接"只有按下去才知道。这条测试就是那个兜底：
 * 每个键按下去要**真的有动静**（帧变了），而且 `esc` 的次序要正好是**后出现的先收**
 * （P0 §1 决策 4：收掉最后出现的那一层）。
 *
 * 模型永不真的调用（假 `chat` 一叫就抛），所以这一屏只走界面那几条路。
 */
import { act, createElement } from "react";
import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { load } from "@meristem/atree";
import type { NodeId } from "@meristem/atree";
import { start as startTree } from "@meristem/harness";
import type { LineProps, LineStore, LlmClient, WireMessage } from "@meristem/harness";
import { get, list, start as startRoles } from "@meristem/roles";
import { Commands } from "@meristem/tui";
import type { TestRendererSetup } from "@opentui/core/testing";
import { testRender } from "@opentui/react/test-utils";
import { App } from "../src/app.tsx";
import { COMMANDS_PATH, LAYERS } from "../src/registry.ts";

const DIR = `/tmp/meristem-screens-${process.pid.toString()}`;
/** 认得的命令：随代码发布的那一份表（装配层在真应用里也是这样建的）。 */
const COMMANDS = new Commands(COMMANDS_PATH, LAYERS);

let store: LineStore;
let setup: TestRendererSetup;
let dir: string;
/** 退出那一声被喊了几次（`app.quit` 就是喊它）。 */
let exits: number;

beforeEach(async () => {
  // 每个用例一条新账：`create` 是写账的，且同一份账只允许一个写者（文件级测试同进程串着跑）。
  dir = `${DIR}-${crypto.randomUUID()}`;
  exits = 0;
  store = await load<LineProps, WireMessage>(`${dir}/ledger.jsonl`);
  await startRoles(undefined, []);
  const llm = {
    chat: (): never => {
      throw new Error("这几条路不该真的叫模型");
    },
  } as unknown as LlmClient;
  const tree = startTree({ store, llm, role: get });
  // 两条线：档 ② 要"我以外的线"才存在（只有一条线时 ①③ 直接来回）。
  store.create({ parent: null, props: { name: "我", role: "bare", outputRoot: dir } });
  const root = store.root() as NodeId;
  store.create({ parent: root, props: { name: "整理 DESIGN", role: "bare", outputRoot: dir } });
  setup = await testRender(
    createElement(App, {
      session: { store, tree, roles: list(), workspace: dir, onExit: () => (exits += 1) },
      at: null,
      commands: COMMANDS,
    }),
    // `ctrl+c` 归界面自己（命令表里那条 `app.quit`），所以引擎不许抢先退出 —— 不然一按屏幕就没了。
    { width: 100, height: 24, exitOnCtrlC: false },
  );
  await settle();
});

afterEach(async () => {
  setup.renderer.destroy();
  await store.close();
});

/**
 * React 的提交 → 总线的版本 → 各区的 effect → 渲染器一轮 —— 这条链有好几步，
 * 所以等到"渲染器没有排队的活了"再读帧（不然读到的是上一帧，断言会假红）。
 */
async function settle(): Promise<void> {
  for (let round = 0; round < 6; round += 1) {
    await new Promise((resolve) => setTimeout(resolve, 10));
    await setup.renderOnce();
  }
}

async function press(key: string, modifiers?: Record<string, boolean>): Promise<void> {
  await act(async () => {
    setup.mockInput.pressKey(key as never, modifiers as never);
  });
  await settle();
}

async function escape(): Promise<void> {
  await act(async () => {
    setup.mockInput.pressEscape();
  });
  await settle();
}

async function type(text: string): Promise<void> {
  await act(async () => {
    await setup.mockInput.typeText(text);
  });
  await settle();
}

async function enter(): Promise<void> {
  await act(async () => {
    setup.mockInput.pressEnter();
  });
  await settle();
}

function frame(): string {
  return setup.captureCharFrame();
}

/** 档 ②/③ 的树行（名字 · 角色）。 */
const TREE = "整理 DESIGN · bare";
/** 侧边那一栏的页名。 */
const SIDE = "材料";

describe("打开", () => {
  test("壳那两行在，内容区是这段对话（档 ①）", () => {
    expect(frame()).toContain("树在休息");
    expect(frame()).toContain("我 · bare");
    expect(frame()).not.toContain(TREE);
  });
});

describe("档与侧边（都长在主屏里）", () => {
  test("alt+t 循环三档：①→②→③→①", async () => {
    await press("t", { meta: true }); // ② 树的一小段
    expect(frame()).toContain(TREE);
    await press("t", { meta: true }); // ③ 整棵树
    expect(frame()).toContain(TREE);
    await press("t", { meta: true }); // ① 回到这段对话
    expect(frame()).not.toContain(TREE);
  });

  test("alt+s 循环三态；alt+p 换页（页留在那儿，切态不动它）", async () => {
    await press("s", { meta: true });
    expect(frame()).toContain(SIDE);
    await press("p", { meta: true });
    expect(frame()).toContain("图与 PDF");
    await press("s", { meta: true }); // 占满全屏
    expect(frame()).toContain("图与 PDF"); // 态换了，页没变
    await press("s", { meta: true }); // 收起
    expect(frame()).not.toContain(SIDE);
  });

  test("换档不动壳：状态行与底下那行还在原位", async () => {
    await press("t", { meta: true });
    expect(frame()).toContain("树在休息");
    expect(frame()).toContain("我 · bare");
  });
});

describe("esc：收掉最后出现的那一层（P0 §1 决策 4）", () => {
  test("先换档、后开侧边 → esc 先收侧边，档还在", async () => {
    await press("t", { meta: true }); // 档 ②（先出现）
    await press("s", { meta: true }); // 分成两栏
    await press("s", { meta: true }); // 占满全屏（后出现）
    await escape(); // 收"占满全屏"这一层
    expect(frame()).toContain(SIDE);
    expect(frame()).toContain(TREE); // 档还开着
    await escape(); // 分栏不是一层（P0 §1：esc 收的是"占满全屏"），所以这一下轮到档
    expect(frame()).not.toContain(TREE);
    expect(frame()).toContain(SIDE); // 侧边还是分栏那一态
  });

  test("先开侧边、后换档 → esc 先收档", async () => {
    await press("s", { meta: true }); // 分成两栏（先出现）
    await press("s", { meta: true }); // 占满全屏
    await press("t", { meta: true }); // 档 ②（后出现）
    await escape(); // 收档
    expect(frame()).not.toContain(TREE);
    expect(frame()).toContain(SIDE); // 侧边那一层还在
    await escape(); // 现在才轮到侧边
    expect(frame()).not.toContain("占满");
  });

  test("没有可收的层时 esc 什么都不动（不许误触别的东西）", async () => {
    await escape();
    expect(frame()).toContain("树在休息");
    expect(frame()).not.toContain(TREE);
  });
});

describe("输入行与命令名单", () => {
  test("敲 / 弹名单、边打边过滤", async () => {
    await type("/he");
    expect(frame()).toContain("/help");
    expect(frame()).not.toContain("/copy");
  });

  test("名单里回车执行那条命令（/help → 键位表）", async () => {
    await type("/he");
    await enter();
    expect(frame()).toContain("进一屏"); // 键位表第一组
    expect(frame()).toContain("/role");
  });

  test("esc 先收名单：档照旧留着（名单是后出现的那一层）", async () => {
    await press("t", { meta: true });
    await type("/");
    expect(frame()).toContain("/help");
    await escape();
    expect(frame()).not.toContain("/help"); // 名单收了
    expect(frame()).toContain(TREE); // 档还在
  });

  test("名单开着时 ↑↓ 归名单，不归树（一层只跑一个）", async () => {
    await press("t", { meta: true }); // 树在，走位本来是它的
    await type("/");
    await act(async () => {
      setup.mockInput.pressArrow("down");
    });
    await settle();
    // 帧里同时有名单与树，只断言"没崩且名单还在"（选中行的变化由名单自己那一份管）。
    expect(frame()).toContain("/help");
  });
});

describe("进屏与回屏（修饰键这条路）", () => {
  test("ctrl+c 真的接到人（退出那一声喊了）", async () => {
    await press("c", { ctrl: true });
    expect(exits).toBe(1);
  });

  test("alt+m 进挑模型，esc 回到主屏", async () => {
    await press("m", { meta: true });
    expect(frame()).toContain("挑模型");
    await escape();
    expect(frame()).toContain("树在休息");
  });

  test("alt+a 进挑角色（真名单）", async () => {
    await press("a", { meta: true });
    expect(frame()).toContain("挑角色");
  });

  test("屏压着时 esc 的次序：先退屏，别动主屏的档", async () => {
    await press("t", { meta: true }); // 档 ②
    await press("m", { meta: true }); // 压一屏（后出现，但它不是主屏里的层）
    expect(frame()).toContain("挑模型");
    await escape();
    expect(frame()).toContain("树在休息");
    expect(frame()).toContain(TREE); // 主屏的档没被动（退屏那一层收掉了就停）
  });
});
