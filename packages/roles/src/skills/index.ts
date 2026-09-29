/**
 * `skills`：`SKILL.md` 目录形式的静态内容包（名字 + 一句描述 + 一个路径）。
 *
 * **技能不需要专门的手**：它就在磁盘上，`read` 就能读。所以清单进 system（名字 / 描述 /
 * 路径 —— 不然模型不知道自己有这些技能），正文由模型自己按路径去读（读了才付上下文成本）。
 * 角色在 xml 里点名要哪些；没点名的技能不进清单。
 *
 * 变因：技能这一能力的语义（扫描规则、清单形状）。
 */

export interface SkillInfo {
  readonly name: string;
  readonly description: string;
  /** 绝对路径（`SKILL.md` 或技能目录）：清单里给出来，模型靠它去 read。 */
  readonly location: string;
}

/** 扫描技能根：每个子目录下的 SKILL.md（非递归），同名 first-wins。 */
export declare function discovered(dirs: readonly string[]): readonly SkillInfo[];

/** system 里那一节的文本：名字 + 描述 + 路径，外加一句"怎么读"。没有技能时返回空串。 */
export declare function block(skills: readonly SkillInfo[]): string;
