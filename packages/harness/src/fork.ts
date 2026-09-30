/**
 * 出生语义：人的一次分叉 → 新的一条线（**造根也只是"没有父"的那一种，全局一棵树里只发生一次**）。
 *
 * **人只给三样**：从哪条线分（`parent`）、要哪个角色、说一句什么。
 * 名字由代码取那句的前几个字；上下文从哪来由 `mode` 定；目录缺省与父相同。
 *
 * "新会话"不是这个包的词：全局一棵树，**一次以根为父的分叉就是一条新会话** ——
 * 那是界面上的一个动作（`parent = store.root()`），harness 不为它多造概念。
 *
 * 出生时定死的事实：**属性**（名字 / 角色 / 做事目录）、**父**、
 * **是不是一段内容的边界**（总结分叉开的线自带底 → `boundary = true`）。
 * 定死之后只读 —— 父的名字与角色不会再变，所以意图链不会变旧。
 *
 * **内部规则**：对外只有 `Tree.fork`（人点的那一下）；`born` 不上面 ——
 * 界面不该自己造节点再塞进账里。它只算"这个节点该长什么样"，**记进账的是 Store**（账的唯一写者）。
 *
 * 变因：出生语义（给新线哪些事实、名字与目录怎么起、两种模式各做什么）。
 */
import type { Node, NodeId, TreeInput } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import type { LineProps } from "./props.ts";

/** 分叉的输入：只有人能给的几样，别的一律程序自己算。 */
export interface ForkInput {
  /** 父；`null` = **造根**（全局一棵树只有第一次是这样，第二个根当场报错；这时 `dir` 必给 —— 没有父可以继承）。 */
  readonly parent: NodeId | null;
  /** 新线用哪个角色（人选的，丙）。 */
  readonly role: RoleId;
  /**
   * 人这句话：**既是这次分叉的输入，也是新线对话的第一条 user 消息** ——
   * 分叉一步做完，不用先开一条空线再往里打字。
   */
  readonly inputText: string;
  /**
   * 出生方式（缺省 `inherit`）：
   *   · `inherit`   —— 新线看得见的 msgs = 自己的 + 父的 + … 一直拼到该停的地方；
   *   · `summarize` —— **总结分叉**（三步，中间换两次"穿谁的系统提示词"）：
   *       1. 造新线（`boundary = true`，从此自带底）+ 把人的那句话写进新线的对话；
   *       2. **穿总结角色**（`roles.SUMMARY_FORK`，乙）跑一轮：它**只做一件事** —— 从父线看得见
   *          的历史里抽出与那条新消息相关的**全部**信息，输出成一份自足的底。它**不回应用户**
   *          （不打招呼、不问问题、不给方案）：回应用户是新角色的事，重复一次就有两个回答者，
   *          账上分不清谁答的。这一条回复记 `by = 乙`（见 `WireMessage.by`）。
   *       3. **换成人选的角色**（丙），由丙 回应用户那句话。
   *
   *   因为第 2 步的产物是对"历史"的陈述、第 3 步的产物才是"对用户说的话"，所以这条线的账读起来
   *   是清楚的：谁的总结、谁的回答，各归各位。
   */
  readonly mode?: "inherit" | "summarize";
  /** 做事的目录：缺省与父节点同目录（开新树时没有父，必须给）。 */
  readonly dir?: string;
}

/** 算出"这个节点该长什么样"（交给 `Store.create` 记进账）。 */
export function born(input: ForkInput, parent: Node<LineProps> | null): TreeInput<LineProps> {
  const outputRoot = input.dir ?? parent?.props.outputRoot;
  if (outputRoot === undefined) throw new Error("造根必须给目录（没有父可以继承）");

  return {
    parent: input.parent,
    boundary: input.mode === "summarize",
    props: {
      name: nameOf(input.inputText),
      role: input.role,
      outputRoot,
    },
  };
}

/** 名字：人那句话的第一个非空行，太长就掐断（人的话就是名字的来源，不许模型生成摘要冒充它）。 */
function nameOf(text: string): string {
  const line = text
    .split("\n")
    .map((part) => part.replace(/\s+/g, " ").trim())
    .find((part) => part !== "");
  if (line === undefined) return "（没有说一句话）";
  return line.length <= 24 ? line : `${line.slice(0, 24)}…`;
}
