/**
 * 装载层的边界：xml 怎么写、system 怎么拼、点名错了怎么办、内置角色在不在。
 *
 * 全部落在临时目录上（不碰仓库、不依赖执行顺序），走的是对外面（`start` / `list` / `get`）
 * 与装进 `xml.ts` 的 `parse`。
 */
import { afterEach, describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { SUMMARY_FORK, get, list, start } from "../src/registry.ts";
import { parse, type Available } from "../src/xml.ts";
import { ALL as BUILTIN_HANDS } from "../src/tools/index.ts";
import { discovered } from "../src/skills/index.ts";

const dirs: string[] = [];

function tmp(prefix: string): string {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  dirs.push(dir);
  return dir;
}

/** 一个临时角色目录（文件 → xml）。 */
function roleDir(files: Record<string, string>): string {
  const dir = tmp("meristem-roles-");
  for (const [name, xml] of Object.entries(files)) writeFileSync(join(dir, name), xml);
  return dir;
}

/** 一个临时技能根（相对路径 → 文件内容）。 */
function skillRoot(files: Record<string, string>): string {
  const root = tmp("meristem-skills-");
  for (const [rel, body] of Object.entries(files)) {
    const path = join(root, rel);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, body);
  }
  return root;
}

const available = (skills: readonly { name: string; description: string; location: string }[] = []): Available => ({
  hands: BUILTIN_HANDS,
  skills,
});

afterEach(() => {
  for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe("一份 xml → 一个角色", () => {
  test("system 的顺序是：人写的原文 → tools → rules → skills（空节不出现）", () => {
    const draft = parse(
      `<role id="code" title="编程">
         <about>读 / 写 / 跑命令</about>
         <prompt>你是好人。</prompt>
         <hands>read bash</hands>
       </role>`,
      available(),
      "code.xml",
    );
    const system = draft.role().system();

    expect(system.startsWith("你是好人。")).toBe(true);
    expect(system).toContain("<tools>");
    expect(system.indexOf("- read:")).toBeGreaterThan(-1);
    expect(system.indexOf("- read:")).toBeLessThan(system.indexOf("- bash:"));
    expect(system).toContain("<rules>");
    expect(system).not.toContain("<skills>");
  });

  test("无条件的作业共享手：手清单 = 点名的 + 三只作业手（xml 里不用点名）", () => {
    const draft = parse(`<role id="code" title="编程"><about>干什么</about><hands>read</hands></role>`, available(), "x");

    expect(draft.role().hands().map((hand) => hand.name)).toEqual([
      "read",
      "job_list",
      "job_output",
      "job_cancel",
    ]);
  });

  test("rules 去重：同一句纪律只出现一次", () => {
    // job_list 与 job_output 贡献同一句"等待是自动的…"，两者都在手清单里 → 只该留一条。
    const draft = parse(`<role id="code" title="编程"><about>干什么</about></role>`, available(), "x");
    const occurrences = draft.role().system().split("等待是自动的").length - 1;

    expect(occurrences).toBe(1);
  });

  test("没写 <prompt> 也合法（纯对话线）：system 里只剩机器那几节", () => {
    const draft = parse(`<role id="talk" title="闲聊"><about>只说话</about></role>`, available(), "x");
    const system = draft.role().system();

    expect(system.startsWith("<tools>")).toBe(true);
  });

  test("技能清单：名字 / 描述 / SKILL.md 的绝对路径", () => {
    const root = skillRoot({
      "agent-reach/SKILL.md": "---\nname: agent-reach\ndescription: 联网检索\n---\n\n正文\n",
    });
    const skills = discovered([root]);
    const draft = parse(
      `<role id="research" title="调研"><about>上网查</about><prompt>你是调研员</prompt><hands>read</hands><skills>agent-reach</skills></role>`,
      available(skills),
      "research.xml",
    );

    const system = draft.role().system();
    expect(system).toContain("<skills>");
    expect(system).toContain("agent-reach: 联网检索");
    expect(system).toContain(join(root, "agent-reach", "SKILL.md"));
    expect(draft.role().hands().some((hand) => hand.name === "read")).toBe(true);
  });
});

describe("拼错就当场报错，不产出半个角色", () => {
  const bad = (xml: string): (() => unknown) => () => parse(xml, available(), "x.xml");

  test("不认识的手 / 技能", () => {
    expect(bad(`<role id="a" title="t"><about>b</about><hands>bsah</hands></role>`)).toThrow(
      "没有叫 bsah 的手",
    );
    expect(bad(`<role id="a" title="t"><about>b</about><hands>read</hands><skills>没这个技能</skills></role>`)).toThrow(
      "没有叫 没这个技能 的技能",
    );
  });

  test("作业共享手不用点名（点名反而报错）", () => {
    expect(bad(`<role id="a" title="t"><about>b</about><hands>job_list</hands></role>`)).toThrow(
      "不用点名",
    );
  });

  test("声明了技能却没给 read / bash：模型知道有技能也读不到", () => {
    const root = skillRoot({ "s/SKILL.md": "---\nname: s\n---\n" });
    expect(() =>
      parse(
        `<role id="a" title="t"><about>b</about><hands>write</hands><skills>s</skills></role>`,
        available(discovered([root])),
        "x.xml",
      ),
    ).toThrow("read");
  });

  test("语法 / 结构问题都带上是哪个文件", () => {
    expect(bad(`<role id="a" title="t"><about>b</about>`)).toThrow("x.xml");
    expect(bad(`<notrole></notrole>`)).toThrow("根标签");
    expect(bad(`<role title="t"><about>b</about></role>`)).toThrow("少了 id");
    expect(bad(`<role id="a" title="t"><about>b</about><hand>read</hand></role>`)).toThrow("不认识的标签");
  });

  test("技能本身缺 front matter 时用目录名（描述留空也不骗人）", () => {
    const root = skillRoot({ "光秃秃/SKILL.md": "正文没有 front matter\n" });

    expect(discovered([root])).toEqual([
      { name: "光秃秃", description: "", location: join(root, "光秃秃", "SKILL.md") },
    ]);
  });

  test("同名技能 first-wins：先给的那个根赢", () => {
    const first = skillRoot({ "a/SKILL.md": "---\nname: same\ndescription: 先来的\n---\n" });
    const second = skillRoot({ "b/SKILL.md": "---\nname: same\ndescription: 后来的\n---\n" });

    expect(discovered([first, second])).toHaveLength(1);
    expect(discovered([first, second])[0]?.description).toBe("先来的");
  });
});

describe("注册表：装载、查、清单", () => {
  test("装载人与内置两类角色；清单按 id 排序；内置的总结分叉在", async () => {
    const dir = roleDir({
      "b.xml": `<role id="bbb" title="乙"><about>乙</about></role>`,
      "a.xml": `<role id="aaa" title="甲"><about>甲</about></role>`,
    });
    await start(dir, []);

    expect(list().map((role) => role.id)).toEqual(["aaa", "bbb", SUMMARY_FORK]);
    expect(get("aaa").title).toBe("甲");
  });

  test("内置的总结分叉带着它的两条硬纪律（提示词住在 xml 里）", () => {
    const system = get(SUMMARY_FORK).system();

    expect(system).toContain("只总结，不回应用户");
    expect(system).toContain("自足");
  });

  test("id 重了（两份实现）当场报错", async () => {
    const dir = roleDir({
      "a.xml": `<role id="same" title="甲"><about>甲</about></role>`,
      "b.xml": `<role id="same" title="乙"><about>乙</about></role>`,
    });

    await expect(start(dir, [])).rejects.toThrow("角色 id 重了：same");
  });

  test("声明了 <mcp> 的角色现在不成立（说清是 MCP 还没接上）", async () => {
    const dir = roleDir({
      "a.xml": `<role id="git" title="git"><about>用 git</about><mcp command="uvx mcp-server-git"/></role>`,
    });

    await expect(start(dir, [])).rejects.toThrow("MCP 还没接上");
  });

  test("按名字找手：找得到给手，找不到给一句话（那句话就是回给模型的东西）", async () => {
    const dir = roleDir({
      "a.xml": `<role id="work" title="干活"><about>干活</about><hands>read</hands></role>`,
    });
    await start(dir, []);
    const work = get("work");

    const found = work.findHand("read");
    expect(found.kind).toBe("hand");
    if (found.kind === "hand") expect(found.hand.name).toBe("read");

    const missing = work.findHand("bsah");
    expect(missing.kind).toBe("missing");
    if (missing.kind === "missing") {
      expect(missing.answer).toContain("没有叫 bsah 的手");
      expect(missing.answer).toContain("read");
    }
  });

  test("没有这个角色 / 技能根不存在：当场抛错，不静默降级", async () => {
    const dir = roleDir({ "a.xml": `<role id="aaa" title="甲"><about>甲</about></role>` });
    await start(dir, []);

    expect(() => get("nope")).toThrow("没有这个角色：nope");
    await expect(start(dir, [join(dir, "没有这个技能根")])).rejects.toThrow();
  });
});
