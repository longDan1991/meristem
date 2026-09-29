/**
 * `@meristem/harness` 的对外面：**一棵树的推进器**。
 *
 * 交互面只有两样：**操作**（`Loop`：run / say / fork / stop / jobs / cancel / retry）与
 * **事件**（`Loop.subscribe`）。读账是 atree 的面（界面直接读 `Store`，那是个通用树：
 * 节点 + 内容 + 拼接）；工具、技能、提示词分节、MCP 是 roles 的面 —— harness 这些词一个都不认识。
 *
 * **消息与属性的词汇住在这里**：atree 只认"不透明的 props / 不透明的内容数组"，
 * 所以「一条线有哪些人看得见的事实」（`LineProps`：名字 / 角色 / 做事目录 / 状态）与
 * 「一次调用流动什么」（`WireMessage` / `Wire` / `Usage`）都是这个包的定义。
 * **没有配对规则**：起手一条回话、结束一条消息，作业 id 拼在内容里，配对由模型自己认（§9.6）。
 *
 * **作业的形状（`Job`）住 roles**，不住这里 —— 依赖方向是 harness → roles（DESIGN §8）。
 * harness 只是它的消费者：起手、settle 时把交代写回账、把"在跑什么"（`Loop.jobs()`）告诉界面。
 * 文本一个字都不从这里出去（`Job.report()` 是唯一出口，DESIGN §9）。
 *
 * 装配面只有一样：`createClient`（`llm` 是注入的端口，谁注入谁就得能造真的那个）。
 *
 * **没有 `Config`、没有 `loadConfig`、没有一个自己的旋钮。** 包不定义"配置"、也不读 `.env`
 * —— 那两件事都是装配层的（谁让这段代码跑起来，谁解释环境）。harness 只声明自己需要的**端口**，
 * 值一概不收。包自己读环境变量 = 第二份配置定义，换个加载来源（文件 / 传参 / 测试）就得再改一遍包。
 *
 * 主坐标轴：**回合怎么推进**（唤醒时机、上下文组装、错误处置、出生与调度规则）。
 */

export type { NodeState, LineProps, LineStore } from "./props.ts";
export type { ChatRole, JsonSchema, ToolCall, Usage, Wire, WireMessage } from "./shape.ts";

export type { Event } from "./events.ts";

export type { Credential, LlmClient, StreamHandlers, TransportInput } from "./llm.ts";
export { createClient } from "./llm.ts";

export type { ForkInput } from "./fork.ts";

export type { Loop, StartInput } from "./loop.ts";
export { start } from "./loop.ts";
