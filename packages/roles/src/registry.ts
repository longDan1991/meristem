/**
 * 人面：指一个目录、看清单、挑角色。
 *
 * 一个 xml 就是一个角色 —— `start` 收到的是角色目录与技能根（都来自装配层，
 * 本包不解释部署配置）。包内自带的内置角色也是 xml，同一条装载路径；
 * **同名当场报错**（一份语义只允许一份实现）。
 *
 * `start` 也负责把角色自己管起来的东西接上（比如 MCP 服务）：任何一台连不上 / 起不来
 * 当场抛错 —— 那个角色就不成立（不静默跳过一台，也不产出半个清单）。
 * 装载是**整个换掉**：`start` 就是这一次的那一份（同一个进程只在开树时叫一次）。
 *
 * `SUMMARY_FORK` 的 id 与它的 xml 都住这里：id 只有这一份定义（不许在别处写字符串），
 * 角色本体是随代码发布的 xml（`registry/`，见 AGENTS §7 那条"包内只读资产"的例外）。
 *
 * 数据就在这个包里（一份列表），不请别人代存。
 *
 * 变因：角色的来源与查找（注册表机制）。
 */
import { readdirSync } from "node:fs";
import { join } from "node:path";
import type { Role, RoleId } from "./role.ts";
import { discovered } from "./skills/index.ts";
import { ALL as BUILTIN_HANDS } from "./tools/index.ts";
import { parseFile } from "./xml.ts";

/** 随代码发布的角色目录（与代码同生共死，不是部署配置）。 */
const BUILTIN_DIR = join(import.meta.dir, "..", "registry");

/**
 * 包内自带的**总结分叉**角色（分叉时先抽一份底的那位，乙）。harness 用它把"总结分叉"接上。
 * 它的职责与两条硬纪律写在 `registry/summary-fork.xml` 里（提示词就在那儿，不在代码里）。
 */
export const SUMMARY_FORK: RoleId = "summary-fork";

const roles = new Map<RoleId, Role>();

/**
 * 装载角色（含包内内置角色）：`dir` = 角色目录，`skillDirs` = 技能根。
 * 语法 / 引用（手名、技能名）/ 冲突 / 连接有问题当场抛错。
 *
 * **作业的三只共享手由这里无条件并入**（`JOB_LIST` / `JOB_OUTPUT` / `JOB_CANCEL`，见 `jobs/hands.ts`）：
 * 它们属于执行机制，不是某块能力的开关 —— 所以不需要在 xml 里点名，也不许被关掉
 * （模型看不见作业，就不知道一手跑没跑完、也没法看进度，作业就成了隐形的东西）。
 */
export async function start(dir: string, skillDirs: readonly string[]): Promise<void> {
  const available = { hands: BUILTIN_HANDS, skills: discovered(skillDirs) };
  const drafts = await Promise.all(
    [...xmlFiles(dir), ...xmlFiles(BUILTIN_DIR)].map((path) => parseFile(path, available)),
  );

  // MCP 还没接上（没有时间参数那些手的兜底值也还没定，DESIGN §7）：声明了服务的角色**不成立**，
  // 不静默少一把手 —— 角色得知道自己的手少了，而不是以为自己在用一把没有的手。
  const declared = drafts.filter((draft) => draft.mcp.length > 0);
  if (declared.length > 0) {
    throw new Error(
      `角色 ${declared.map((draft) => draft.id).join("、")} 声明了 <mcp>，但 MCP 还没接上` +
        `（兜底超时还没定，DESIGN §7）：先把 <mcp> 去掉，或等这一层接上`,
    );
  }

  const loaded = new Map<RoleId, Role>();
  for (const draft of drafts) {
    if (loaded.has(draft.id)) {
      throw new Error(`角色 id 重了：${draft.id}（一份语义只允许一份实现）`);
    }
    loaded.set(draft.id, draft.role());
  }

  roles.clear();
  for (const [id, role] of loaded) roles.set(id, role);
}

/** 按 id 取；没有这个角色 → 抛错（拼错不该静默降级成"没有能力"）。 */
export function get(id: RoleId): Role {
  const role = roles.get(id);
  if (role === undefined) {
    const known = [...roles.keys()].join(" / ") || "一个都没有";
    throw new Error(`没有这个角色：${id}（装载到的：${known}）`);
  }
  return role;
}

/** 全部角色：给人挑的清单（分叉时用），按 id 排序 —— 清单的顺序不该随文件系统抖。 */
export function list(): readonly Role[] {
  return [...roles.values()].sort((left, right) => (left.id < right.id ? -1 : 1));
}

/** 角色目录里的 xml（不递归）—— 排序只为"装载与报错的顺序"稳定。 */
function xmlFiles(dir: string): readonly string[] {
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".xml"))
    .map((entry) => join(dir, entry.name))
    .sort();
}
