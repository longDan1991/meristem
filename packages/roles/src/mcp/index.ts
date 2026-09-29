/**
 * `mcp`：MCP 对接 —— 远端或本地的工具源，变成手之后与内置手没有区别。
 *
 * 声明只有"怎么连"这一件事：
 *   · `url`     —— 远端服务，一个地址；
 *   · `command` —— 本地服务，一行命令行（程序 + 参数）。
 * **下载 / 安装不在这里做**：那是人的额外流程（装好了再写进来）。起不来就抛错，
 * 那个角色不成立 —— 角色得知道自己的手少了，而不是以为自己在用一把没有的手。
 * 服务名与工具名由那台服务自己给，我们不自造名字。
 *
 * **作业**：一次调用就是一次执行，用底座的 `background(...)` 包（远端可能很久才回）。
 *
 * **时间**：服务给的 schema 里通常没有时间参数（我们改不了它）→ 由底座的 `timeout` 给一个**兜底值**，
 * 而且这件事要**说出来**（那只手的 `description` 里写明"它没有自己的超时，统一按 N 杀"）——
 * 说不出来的限制才是惩罚（DESIGN §9.9）；兜底值定多少见 DESIGN §7（还没定）。
 *
 * 变因：MCP 协议与传输（新传输、握手、能力发现）。
 */
import type { Hand } from "../role.ts";

export type McpServerDecl =
  | { readonly kind: "url"; readonly url: string }
  | { readonly kind: "command"; readonly command: string };

/** 连上并发现工具；返回的手挂在角色上。任何一台连不上 / 起不来 → 抛错。 */
export declare function mcpHands(decls: readonly McpServerDecl[]): Promise<readonly Hand[]>;
