/**
 * `skills`：`SKILL.md` 目录形式的静态内容包（名字 + 一句描述 + 一个路径）。
 *
 * **技能不需要专门的手**：它就在磁盘上，`read` 就能读。所以清单进 system（名字 / 描述 /
 * 路径 —— 不然模型不知道自己有这些技能），正文由模型自己按路径去读（读了才付上下文成本）。
 * 角色在 xml 里点名要哪些；没点名的技能不进清单。
 *
 * 扫描规则：每个技能根下的**直接子目录**里要有 `SKILL.md`（不递归）；名字与描述取文件开头
 * front matter（`---` 之间那几行 `name:` / `description:`）—— 没写名字就用目录名、没写描述就是空。
 * **同名 first-wins**（先给的根先赢，后面的同名不覆盖）。
 *
 * 变因：技能这一能力的语义（扫描规则、清单形状）。
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

export interface SkillInfo {
  readonly name: string;
  readonly description: string;
  /** 绝对路径（`SKILL.md`）：清单里给出来，模型靠它去 read。 */
  readonly location: string;
}

/** 扫描技能根：每个子目录下的 SKILL.md（非递归），同名 first-wins。根不存在直接抛错（配置问题当场说）。 */
export function discovered(dirs: readonly string[]): readonly SkillInfo[] {
  const found = new Map<string, SkillInfo>();
  for (const root of dirs) {
    for (const entry of readdirSync(root, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const location = join(root, entry.name, "SKILL.md");
      if (!existsSync(location)) continue;
      const head = frontMatter(readFileSync(location, "utf8"));
      const name = head.get("name") ?? entry.name;
      if (found.has(name)) continue;
      found.set(name, { name, description: head.get("description") ?? "", location });
    }
  }
  return [...found.values()];
}

/** system 里 `skills` 那一节的**内容**（标签由 `xml.ts` 统一加）。没有技能就返回空串。 */
export function block(skills: readonly SkillInfo[]): string {
  if (skills.length === 0) return "";
  const lines = skills.map((skill) =>
    skill.description === ""
      ? `- ${skill.name} —— ${skill.location}`
      : `- ${skill.name}: ${skill.description} —— ${skill.location}`,
  );
  return `正文按路径用 read 读（不在这里：读了才付上下文的钱）。\n${lines.join("\n")}`;
}

/** front matter：文件开头 `---` 与下一个 `---` 之间的 `键: 值` 行（只有这两个键有语义，别的忽略）。 */
function frontMatter(text: string): Map<string, string> {
  const fields = new Map<string, string>();
  const lines = text.split("\n");
  if (lines[0]?.trim() !== "---") return fields;
  for (const line of lines.slice(1)) {
    if (line.trim() === "---") break;
    const at = line.indexOf(":");
    if (at <= 0) continue;
    fields.set(line.slice(0, at).trim(), line.slice(at + 1).trim());
  }
  return fields;
}
