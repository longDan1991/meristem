/**
 * 一个 xml 就是一个角色：**人写的就是这个文件**，装载器把它变成 `Role`。
 *
 * 语法（人写的那一面，只有这几样）：
 *
 * ```xml
 * <role id="code" title="编程">
 *   <prompt>                <!-- 系统提示词的正文，纯文本，程序不改一个字 -->
 *     你是……                 <!-- 手是什么、什么时候用哪把，直接写在这里 -->
 *   </prompt>
 *   <hands>bash read write</hands>   <!-- 要哪几把内置手（机器声明） -->
 *   <skills>agent-reach</skills>     <!-- 要哪些技能（机器声明） -->
 *   <mcp url="https://mcp.example.com/v1"/>                      <!-- 远端：一个地址 -->
 *   <mcp command="uvx mcp-server-git --repository /tmp/repo"/>   <!-- 本地：一行命令行 -->
 * </role>
 * ```
 *
 * 一个角色的 system 由装载器按固定顺序拼成（人不需要写占位符，也没有模板语法），
 * 每一节是一对同名标签包住的几行；空节整个不出现：
 *
 *   preamble  = `<prompt>` 的原文（人写的，原样放最前面，不包标签）
 *   tools     = 一行一只：`- 名字: snippet`（只有自带 snippet 的手进得来；MCP 手不进）
 *   rules     = 各只手贡献的纪律条目（去重，先后按手的顺序）
 *   skills    = 名字 / 描述 / 路径 + 一句"怎么读"（用 `read` 按路径读，技能没有专门的手）
 *
 * 约定：
 *   · `id` / `title` 必填（`title` 是**给人看的那一行**：挑角色时只看它）；
 *   · `id` 必填且唯一（跟内置角色同名当场报错，不覆盖不并存）；
 *   · `<hands>` 点名的手必须是已知内置手，`<skills>` 点名的技能必须真存在
 *     （拼错当场报错，不静默少一把手 / 一个技能）；
 *   · 声明了技能就必须给 `read` 或 `bash`（不然模型知道有技能却读不到）→ 没给当场报错；
 *   · 作业的三只共享手（`job_list` / `job_output` / `job_cancel`）**不用点名**：**点了手的角色**
 *     都无条件并入 —— 它们属于执行机制，不是某块能力的开关；点名它们反而当场报错。
 *     一只手都不点的角色（全关）连它们也不给：没有手可伸，也就没有作业可看；
 *   · `<prompt>` 可以整个不写（那就是"纯对话线"，零提示词也合法）；
 *   · `<prompt>` 里**不用解释“异步 / 后台 / 作业”这套机制**：模型侧看不见区别（一次执行而已）。
 *     要讲的纪律（“别拿 `job_output` 当轮询”）住在 schema 的 `description` 里，不在这里重复；
 *   · 手的语义**不在 `<prompt>` 里重复**：完整描述只有 schema 那一份；
 *   · `<mcp>` 只声明怎么连，**不负责下载 / 安装**（那是人的额外流程）。
 *   · 角色目录与技能根由调用方传给 `start`（本包不解释部署配置），xml 里只写名字。
 *   · 不认识的标签 / 属性一律报错（拼错不当成"没写"）。
 *
 * 解析出来的是 `Draft`（还没连 MCP 的手）：MCP 手要连上服务才知道有哪些，那一步在 `registry.ts`
 * 里做（`Draft.role(extra)` 把它们补上）。system 与 MCP 无关 —— 服务只给名字 / 描述 / schema，
 * 没有 snippet，所以进不了 tools 节。
 *
 * 变因：这个格式（人怎么写角色）。
 */
import { readFile } from "node:fs/promises";
import { XMLParser, XMLValidator } from "fast-xml-parser";
import type { Hand, Role, RoleId } from "./role.ts";
import { JOB_HANDS } from "./jobs/hands.ts";
import type { McpServerDecl } from "./mcp/index.ts";
import { block as skillsSection, type SkillInfo } from "./skills/index.ts";

/** 装载时手上有哪些东西可以点名（都来自装载器，xml 自己不找）。 */
export interface Available {
  readonly hands: readonly Hand[];
  readonly skills: readonly SkillInfo[];
}

/** 解出来、但还没连 MCP 的角色。 */
export interface Draft {
  readonly id: RoleId;
  readonly title: string;
  /** xml 里声明的服务（`start` 据此连；连不上那个角色就不成立）。 */
  readonly mcp: readonly McpServerDecl[];
  /** 补上 MCP 手之后的最终角色（system 不受影响：MCP 手没有 snippet）。 */
  role(extra?: readonly Hand[]): Role;
}

/**
 * 解析一份 xml → `Draft`；语法 / 引用 / 未知标签有问题当场报错，不产出半个角色。
 * `source` 只用于报错（文件路径或"xml"）。
 */
export function parse(xml: string, available: Available, source: string): Draft {
  const problem = XMLValidator.validate(xml);
  if (problem !== true) {
    throw new Error(`${source}: xml 读不动 —— ${problem.err.msg}（第 ${problem.err.line} 行）`);
  }

  const doc: unknown = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: "@_",
    trimValues: false,
    parseTagValue: false,
    parseAttributeValue: false,
    isArray: (name) => name === "mcp",
  }).parse(xml);

  const root = own(doc, "role", source);
  dropBlankText(root, source, "role");
  known(root, ["@_id", "@_title", "prompt", "hands", "skills", "mcp"], source, "role");

  const id = required(root, "@_id", source).trim();
  if (id === "" || /\s/.test(id)) throw new Error(`${source}: id 必填，而且不能带空格`);
  const title = required(root, "@_title", source).trim();

  const hands = resolveHands(root["hands"], available.hands, source);
  const skills = resolveSkills(root["skills"], available, source);
  const mcp = resolveMcp(root["mcp"], source);

  // 声明了技能就必须给得到手的读法：不然模型知道自己有技能，却没有任何手能去读它。
  if (skills.length > 0 && !hands.some((hand) => hand.name === "read" || hand.name === "bash")) {
    throw new Error(`${source}: 声明了技能却没给 read 或 bash（模型知道有技能也读不到）`);
  }

  const preamble = typeof root["prompt"] === "string" ? root["prompt"].trim() : "";

  return built(id, title, mcp, preamble, hands, skills);
}

/** 读一个 xml 文件 → `Draft`（随包发布的内置角色也走这条路）。 */
export async function parseFile(path: string, available: Available): Promise<Draft> {
  return parse(await readFile(path, "utf8"), available, path);
}

/**
 * 什么都不带的角色（提示词 / 手 / 技能 / 服务全空）—— **内置的基础角色**走这条路
 * （`registry.ts` 的 `Builtin.Bare`：它在代码里建，没有 xml）。跟 xml 出来的角色同一条造法。
 */
export function empty(id: RoleId, title: string): Draft {
  return built(id, title, [], "", [], []);
}

/** 一个角色的所有组成部分 → `Draft`（`parse` 与 `empty` 共用，只有这一处把它们拼起来）。 */
function built(
  id: RoleId,
  title: string,
  mcp: readonly McpServerDecl[],
  preamble: string,
  hands: readonly Hand[],
  skills: readonly SkillInfo[],
): Draft {
  return {
    id,
    title,
    mcp,
    role(extra = []) {
      // 一只手都没有的角色（点名的与 MCP 的都算）连作业那三只也不带：没有手可伸，作业无从谈起。
      const all = hands.length + extra.length === 0 ? [] : [...hands, ...JOB_HANDS, ...extra];
      return {
        id,
        title,
        system: () => compose(preamble, all, skills),
        hands: () => all,
        findHand(name) {
          const hand = all.find((candidate) => candidate.name === name);
          if (hand !== undefined) return { kind: "hand", hand };
          if (all.length === 0) {
            return {
              kind: "missing",
              answer: `这条线上你一只手动不了（没有手可伸），${name} 调不了，也没有别的手可换。`,
            };
          }
          const names = all.map((candidate) => candidate.name).join(" / ");
          return {
            kind: "missing",
            answer:
              `这条线上没有叫 ${name} 的手。你手上的手是：${names}（见 system 的 tools 一节）` +
              " —— 用里面有的名字重来。",
          };
        },
      };
    },
  };
}

/** system 的拼法（顺序即契约，DESIGN §8）：人写的原文 → tools → rules → skills。 */
function compose(preamble: string, hands: readonly Hand[], skills: readonly SkillInfo[]): string {
  const tools = hands
    .filter((hand) => hand.snippet !== undefined)
    .map((hand) => `- ${hand.name}: ${hand.snippet}`)
    .join("\n");

  const seen = new Set<string>();
  const rules: string[] = [];
  for (const hand of hands) {
    for (const rule of hand.guidelines ?? []) {
      if (seen.has(rule)) continue;
      seen.add(rule);
      rules.push(`- ${rule}`);
    }
  }

  return [
    preamble,
    section("tools", tools),
    section("rules", rules.join("\n")),
    section("skills", skillsSection(skills)),
  ]
    .filter((part) => part !== "")
    .join("\n\n");
}

function section(name: string, content: string): string {
  return content === "" ? "" : `<${name}>\n${content}\n</${name}>`;
}

/**
 * 点名的手 → 手对象，按写的顺序（重复写只算一次）。作业那三只**不在这里**：它们由 `built`
 * 按"这个角色有没有手"并进来（点了手的角色都自动带上，见 DESIGN §9.2）。
 */
function resolveHands(given: unknown, catalog: readonly Hand[], source: string): readonly Hand[] {
  if (given === undefined) return [];
  const names = words(given, "hands", source);
  const job = new Set(JOB_HANDS.map((hand) => hand.name));
  const chosen: Hand[] = [];
  for (const name of names) {
    if (job.has(name)) {
      throw new Error(`${source}: <hands> 不用点名 ${name} —— 点了手的角色都自动带上作业那三只共享手`);
    }
    const hand = catalog.find((candidate) => candidate.name === name);
    if (hand === undefined) {
      const known = catalog.map((candidate) => candidate.name).join(" / ");
      throw new Error(`${source}: 没有叫 ${name} 的手（内置手：${known}）`);
    }
    if (!chosen.includes(hand)) chosen.push(hand);
  }
  return chosen;
}

/** 点名的技能 → 技能信息，按写的顺序；声明了技能就必须给得到手的读法。 */
function resolveSkills(
  given: unknown,
  available: Available,
  source: string,
): readonly SkillInfo[] {
  if (given === undefined) return [];
  const names = words(given, "skills", source);
  const chosen: SkillInfo[] = [];
  for (const name of names) {
    const skill = available.skills.find((candidate) => candidate.name === name);
    if (skill === undefined) {
      const known = available.skills.map((candidate) => candidate.name).join(" / ") || "（一个都没有）";
      throw new Error(`${source}: 没有叫 ${name} 的技能（技能根里找到的：${known}）`);
    }
    if (!chosen.includes(skill)) chosen.push(skill);
  }
  return chosen;
}

function resolveMcp(given: unknown, source: string): readonly McpServerDecl[] {
  if (given === undefined) return [];
  if (!Array.isArray(given)) throw new Error(`${source}: <mcp> 解析不出来`);
  return given.map((entry: unknown) => {
    const node = record(entry, source, "mcp");
    known(node, ["@_url", "@_command"], source, "mcp");
    const url = node["@_url"];
    const command = node["@_command"];
    if (typeof url === "string" && command === undefined) return { kind: "url", url };
    if (typeof command === "string" && url === undefined) return { kind: "command", command };
    throw new Error(`${source}: <mcp> 要写 url="…" 或 command="…"（两样都写 / 都不写都不行）`);
  });
}

/** 一段文本 → 空白分出来的词（`<hands>bash read write</hands>`）。 */
function words(given: unknown, tag: string, source: string): readonly string[] {
  if (typeof given !== "string") throw new Error(`${source}: <${tag}> 里只能写名字`);
  return given.split(/\s+/).filter((word) => word !== "");
}

function own(node: unknown, tag: string, source: string): Record<string, unknown> {
  const doc = record(node, source, "文档");
  const names = Object.keys(doc);
  if (names.length !== 1 || names[0] !== tag) {
    throw new Error(`${source}: 根标签要正好是一个 <${tag}>（读到：${names.join(", ") || "空"}）`);
  }
  return record(doc[tag], source, tag);
}

/**
 * 子元素之间的换行与缩进是**排版**，不是内容：纯空白的 `#text` 直接丢掉。
 * 标签外真写了文字才算错（那是写错了地方，不该静默当没看见）。
 */
function dropBlankText(node: Record<string, unknown>, source: string, tag: string): void {
  const text = node["#text"];
  if (text === undefined) return;
  if (typeof text === "string" && text.trim() === "") {
    delete node["#text"];
    return;
  }
  throw new Error(`${source}: <${tag}> 里标签外不能有文字`);
}

function record(node: unknown, source: string, tag: string): Record<string, unknown> {
  if (typeof node !== "object" || node === null || Array.isArray(node)) {
    throw new Error(`${source}: <${tag}> 的形状不对`);
  }
  return node as Record<string, unknown>;
}

function known(node: Record<string, unknown>, allowed: readonly string[], source: string, tag: string): void {
  const unknown = Object.keys(node).filter((key) => !allowed.includes(key));
  if (unknown.length > 0) {
    throw new Error(`${source}: <${tag}> 里不认识的标签 / 属性：${unknown.join(", ")}`);
  }
}

function required(node: Record<string, unknown>, key: string, source: string): string {
  const value = node[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${source}: 少了 ${key.startsWith("@_") ? key.slice(2) : key}`);
  }
  return value;
}
