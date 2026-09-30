/**
 * 部署配置：**装配层的事** —— 入口解释环境，然后把值分给各包。
 *
 * 为什么住在这里、不住在某个包里：包只声明自己需要的值（树的账给 atree、角色目录与技能根给 roles、
 * 模型引用 / 端点 / 钥匙给传输）。**"配置是什么、从哪加载"是应用的问题**：换个加载来源
 * （`.env` / 文件 / 命令行 / 测试传参）只动这一处，包一行不改。包自己读环境变量 = 第二份定义。
 *
 * 从哪儿读：`process.env`；`.env` 由运行时在**起进程的目录**里自动加载（Bun 只认当前目录，不往上找）。
 * 这里**没有一行"找配置文件"的代码** —— 配置在哪儿是部署的事，代码不替它挑路径（同 AGENTS §7）。
 * 所以从仓库根起（`bun start`）就读得到根上的 `.env`；别处起就自己把变量放进环境。
 * 键名与格式写在仓库根的 `.env.example` 里（那是给人看的唯一一份说明）。
 *
 * 缺必填项当场炸（带着缺哪个键的名字 + 该往哪儿放）—— 不兜底、不静默换假模型。
 *
 * **密钥只在 `loadCredential` 一处读**：取出来的值立刻交给传输层 —— 不进 `Config`、不进别的对象、
 * 不打印值，报错只说它从哪个变量来。
 *
 * 变因：部署（换机器、换端点、换数据根、换模型）。
 */
import { isAbsolute, join } from "node:path";
import type { Credential } from "@meristem/harness";

export interface Config {
  /** 数据根（绝对路径）：agent 的做事目录，这棵树自己的东西（账）也落在这里。 */
  readonly workspace: string;
  /**
   * 这棵树的账（绝对路径）：**全局一棵树、一个用户一份账** —— 不靠推算、不去目录里挑。
   * 缺省 `<workspace>/.tree/ledger.jsonl`（从数据根推出来，不是从代码位置推）。
   */
  readonly tree: string;
  /** 额外角色目录（可选）：一个 xml 一个角色。没给 = 只有随包发布的内置角色（`summary-fork`）。 */
  readonly roleDir?: string;
  /** 技能根（可选，`:` 分隔）：`SKILL.md` 非递归扫描，同名 first-wins。没给 = 没有技能根。 */
  readonly skillDirs: readonly string[];
  /** 用哪个模型（给传输）：`provider/model`（模式串）。换模型只改这一处。 */
  readonly model: string;
  /** 发给端点的模型 id（可选）：目录里那份只管怎么发，换了名字的端点用它说出端点认的那串。 */
  readonly modelId?: string;
  /** 端点覆盖（给传输，可选）：走代理 / 自建网关才需要；不填用该 provider 自带的端点。 */
  readonly baseUrl?: string;
}

/** 读配置；缺必填项抛错（带着缺哪个键的名字）。 */
export function loadConfig(env: Record<string, string | undefined> = process.env): Config {
  const workspace = absolutePath(env, "MERISTEM_WORKSPACE");
  const rawTree = env.MERISTEM_TRACE;
  const rawRoles = env.MERISTEM_ROLES;
  const rawBase = env.MERISTEM_BASE_URL;
  const rawModelId = env.MERISTEM_MODEL_ID;
  return {
    workspace,
    tree:
      rawTree === undefined || rawTree === ""
        ? join(workspace, ".tree", "ledger.jsonl")
        : absolutePath(env, "MERISTEM_TRACE"),
    ...(rawRoles === undefined || rawRoles === "" ? {} : { roleDir: absolutePath(env, "MERISTEM_ROLES") }),
    skillDirs: skillDirs(env.MERISTEM_SKILLS),
    model: required(env, "MERISTEM_MODEL"),
    ...(rawModelId === undefined || rawModelId === "" ? {} : { modelId: rawModelId }),
    ...(rawBase === undefined || rawBase === "" ? {} : { baseUrl: rawBase }),
  };
}

/**
 * 取钥匙；没设 / 空串抛错（带着变量名）。
 *
 * 取完立刻传给 `createClient`：不进 `Config`、不进别的对象、不打印 —— 要打印只说 `from`。
 */
export function loadCredential(env: Record<string, string | undefined> = process.env): Credential {
  const key = env.MERISTEM_API_KEY;
  if (key === undefined || key === "") throw new Error(missing("MERISTEM_API_KEY"));
  return { key, from: "MERISTEM_API_KEY" };
}

/**
 * 必填项：缺失 / 空串当场抛，**错误里写出变量名 + 该往哪儿放** —— 部署出问题时，这两样就是最快的定位。
 * 不兜底、不换默认值（默认值会把"没配上"变成一次静默跑歪的部署）。
 */
function required(env: Record<string, string | undefined>, name: string): string {
  const value = env[name];
  if (value === undefined || value === "") throw new Error(missing(name));
  return value;
}

/** 路径项：**必须是绝对路径**。路径是部署配置，不许推算 —— 相对路径的含义挂在"进程从哪儿起的"上，
 * 换个目录启动就悄悄指向另一棵树 / 另一个工作区，而人以为自己看的是同一份账。 */
function absolutePath(env: Record<string, string | undefined>, name: string): string {
  const value = required(env, name);
  if (!isAbsolute(value)) {
    throw new Error(`${name} 必须是绝对路径，给的是 ${value}（相对路径随进程的当前目录漂，不许推算）`);
  }
  return value;
}

/** 技能根：可选，`:` 分隔；每一项也都是路径（同样要绝对）。没给 = 没有技能根。 */
function skillDirs(raw: string | undefined): readonly string[] {
  if (raw === undefined || raw === "") return [];
  return raw.split(":").map((dir) => {
    if (!isAbsolute(dir)) {
      throw new Error(`MERISTEM_SKILLS 里的路径必须是绝对路径，给的是 ${dir}（相对路径不许推算）`);
    }
    return dir;
  });
}

/** 缺配置时说什么：变量名 + 该往哪儿放（`.env` 只从起进程的目录读，这是个容易踩的坑）。 */
function missing(name: string): string {
  return (
    `缺少环境变量 ${name}：从仓库根起（bun start）读的是根上的 .env —— ` +
    `.env 只从起进程的目录加载，别的目录起就要先把变量放进环境（键名见 .env.example）`
  );
}
