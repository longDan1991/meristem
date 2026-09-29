/**
 * 一个 xml 就是一个角色：**人写的就是这个文件**，装载器把它变成 `Role`。
 *
 * 语法（人写的那一面，只有这几样）：
 *
 * ```xml
 * <role id="code" title="编程">
 *   <about>读 / 写 / 跑命令，把代码改到能跑</about>
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
 * 一个角色的 system 由装载器按固定顺序拼成（人不需要写占位符，也没有模板语法）：
 *
 *   preamble  = `<prompt>` 的原文（人写的）
 *   tools     = 一行一只：`- 名字: snippet`（只有自带 snippet 的手进得来；MCP 手不进）
 *   rules     = 各只手贡献的纪律条目（去重）
 *   skills    = 名字 / 描述 / 路径 + 一句"怎么读"（用 `read` 按路径读，技能没有专门的手）
 *
 * 约定：
 *   · `id` 必填且唯一（跟内置角色同名当场报错，不覆盖不并存）；`title` / `about` 给人看；
 *   · `<hands>` 点名的手必须是已知共享件，`<skills>` 点名的技能必须真存在
 *     （拼错当场报错，不静默少一把手 / 一个技能）；
 *   · 声明了技能就必须给 `read` 或 `bash`（不然模型知道有技能却读不到）→ 没给当场报错；
 *   · 作业的三只共享手（`job_list` / `job_output` / `job_cancel`）**不用点名**：装载器无条件并入
 *     —— 它们属于执行机制（所有角色都有），不是某块能力的开关；
 *   · `<prompt>` 里**不用解释“异步 / 后台 / 作业”这套机制**：模型侧看不见区别（一次执行而已）。
 *     要讲的纪律（“别拿 `job_output` 当轮询”）住在 schema 的 `description` 里，不在这里重复；
 *   · 手的语义**不在 `<prompt>` 里重复**：完整描述只有 schema 那一份；
 *   · `<mcp>` 只声明怎么连，**不负责下载 / 安装**（那是人的额外流程）；连不上 / 起不来 → 抛错，
 *     这个角色不成立。MCP 手只进 tools 数组，不进 system（服务没给 snippet）。
 *   · 角色目录与技能根由调用方传给 `start`（本包不解释部署配置），xml 里只写名字。
 *
 * 变因：这个格式（人怎么写角色）。
 */
import type { Role } from "./role.ts";

/** 解析一份 xml → 角色；语法 / 引用 / 占位符有问题当场报错，不产出半个角色。 */
export declare function parse(xml: string): Role;

/** 读一个 xml 文件 → 角色（随包发布的内置角色也走这条路）。 */
export declare function parseFile(path: string): Promise<Role>;
