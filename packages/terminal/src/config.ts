/**
 * 部署配置：**装配层的事** —— 入口解释环境，然后把值分给各包。
 *
 * 为什么住在这里、不住在某个包里：包只声明自己需要的值（树的账文件给 atree、角色目录与技能根给 roles、
 * 模型引用 / 端点覆盖 / 钥匙给传输）。**"配置是什么、从哪加载"是应用的问题**：换个加载来源
 * （`.env` / 文件 / 命令行 / 测试传参）只动这一处，包一行不改。包自己读环境变量 = 第二份定义。
 *
 * 缺必填项当场炸（带着缺哪个键的名字）—— 不兜底、不静默换假模型。
 *
 * **密钥只在 `loadCredential` 一处取**：这里只写**变量名**（配置可以进版本控制，密钥不行），
 * 取出来的值立刻交给传输层 —— 不进别的对象、不打印值，报错只说来源。
 *
 * 变因：部署（换机器、换端点、换数据根、换模型）。
 */
import type { Credential } from "@meristem/harness";

export interface Config {
  /** 数据根（绝对路径）：在根上开线时，它的做事目录缺省就是这里（之后的线缺省继承父）。 */
  readonly workspace: string;
  /** 这棵树（绝对路径）：**全局一棵树、一个用户一份账**，显式配置 —— 不靠推算、不去目录里挑。 */
  readonly tree: string;
  /** 角色目录（给 roles）：一个 xml 一个角色。 */
  readonly roleDir: string;
  /** 技能根（给 roles）：`SKILL.md` 非递归扫描，同名 first-wins。 */
  readonly skillDirs: readonly string[];
  /** 用哪个模型（给传输）：`provider/model`（模式串）。换模型只改这一处。 */
  readonly model: string;
  /** 端点覆盖（给传输，可选）：走代理 / 自建网关才需要；不填用该 provider 自带的端点。 */
  readonly baseUrl?: string;
  /** 钥匙从哪个环境变量取：**只写名字**。 */
  readonly apiKeyEnv: string;
}

/** 读配置；缺必填项抛错（带着缺哪个键的名字）。 */
export declare function loadConfig(env?: Record<string, string | undefined>): Config;

/**
 * 取钥匙；没设 / 空串抛错（带着变量名）。
 *
 * 取完立刻传给 `createClient`：不塞进 `Config`、不塞进别的对象、不打印 —— 要打印只说 `from`。
 */
export declare function loadCredential(
  cfg: Config,
  env?: Record<string, string | undefined>,
): Credential;
