/**
 * 一棵正在跑的树：**harness 对外只有两样 —— 操作与事件。**
 *
 * 界面能做的动作全在 `Tree` 的方法上，能看见的东西全在 `subscribe` 那一栏；没有第三样。
 * 读账（渲染树、画一条线）是 atree 的面，界面直接读 `Store`，不从这里过。
 *
 * **这里没有常驻循环。** 推进的时机全是**具体事件**，每一个都知道自己在叫哪条线：
 *
 *   · 人说话 / 人重试 / 人分叉 —— 直接叫那条线；
 *   · 作业结束 —— 叫它所属的那条线；
 *   · 开树（`resume`）—— 走一遍账，把该说话的那几条各自叫一次。
 *
 * 所以不存在"扫一遍整棵树看看谁该动"，也不存在"等所有线都跑完"：**没有人动，就是休息**，
 * 不需要一台机器在那儿转着看。
 *
 * **同一个节点同时只发一次**：每条线在内存里有一格运行态（`speaking` = 模型还没说完，
 * `again` = 说话的功夫里又有人动过）。卡住的**只有同一个节点的并发**，不是全局：别的线照常说话；
 * 同一条线正在吐字时，人再说话会被**当场拒掉**（界面据此告诉他"这条线正在吐字"）——
 * 把人的话塞进一条正在生成的回复中间，账上就成了"回答落在提问前面"。
 *
 * 这一格**只在内存里**（进程一没就没了），而"该不该说话"永远从账上重新算（`plan.actionable`）——
 * 所以重启之后照样接着走：`resume()` 走一遍就恢复了。谁在跑（作业）另有唯一一份（roles 的作业表）。
 *
 * **生命周期**（这套定义的正文）：
 *   开    —— 装配层把树接上（空树则连根都还没有）；**造根 = 一次没有父的分叉**（全局一棵树，只发生一次）
 *   恢复  —— 读账即恢复：`resume()` 把该说话的线各叫一次（谁欠一句话是算得出来的）
 *   推进  —— 组装这条线看得见的 msgs（`Store.assemble`）→ 让模型说话 →
 *            把它伸出的手交给角色起作业 → **起手一条回话、结束一条消息**（见下）→ 这条线这一段结束
 *   等人  —— 没有触发点就什么都不做（人不在场是常态，DESIGN §5.7）
 *   出生  —— 人分叉，开一条新线（两种模式见 `ForkInput`）
 *   收手  —— 人的动作，`stop`（顺带取消所有在跑的作业）
 *
 * 人的动作只有三个：**说话 / 分叉 / 收手**（结构动作只有人有，模型只能提议 —— DESIGN §5.3
 * 这条靠接口写死：模型那侧只有手，拿不到 `Tree`）；另外两个是照看性的：**取消一个作业**、
 * **重试一次模型接口失败**。
 *
 * 事件往订阅者出去；账的写入（`Store.append`）是同步的，而一条线只在"没在吐字"时才被叫，
 * 所以同一个节点不会有两轮同时在往账里塞消息（不加锁，也不需要）。
 *
 * **作业在树里的位置**（DESIGN §9.2 的"树自己做的"）：
 *
 *   1. 起手：把 `args`、`ctx`（`{ outputRoot, space = 这个节点 }`）交给 `hand.run`，拿回一个 `Job`
 *      （作业表由底座登记，树不写那张表）。
 *   2. **起手一条回话**：立刻往账里写一条 `role: "tool"` 的回话，内容 = `job.report()`
 *      （还在跑 → "作业 #abc 已起…"；已经结束 → 结果）—— 每个 `tool_calls` 因此条条有回话，
 *      provider 那边天然合法，**程序不需要任何配对结构**。
 *   3. **结束一条消息**：若它还在跑，就等它（`job.wait()`，**从不 poll**）—— settle 时再往账里写
 *      一条 `role: "user"` 的消息（内容 = `report()`，同一个作业 id 在里面）、发状态事件、
 *      **叫这条线一声**；**内容没变就不写第二次**（立刻结束的手只留起手那一条）。
 *   4. 叫一条线之前先看两件事实：这条线上还有没有作业在跑、账末是不是"伸出去没回话的手"
 *      （`plan.actionable`；表就是 roles 那张，按空间筛）。
 *   5. 人取消 → 转发 `job.cancel()`；`stop`（收手）→ 取消所有在跑的作业。
 *   6. 模型接口失败 → 这条线记在内存里不再动 + `Event.transport_error`（不入账、不自动重试，§9.8）。
 *
 *   绝不做的：判断这一手会长不长（§9.3）；生成任何文本（消息内容一律来自 `job.report()`）；
 *   设统一超时（超时在每只手的底座里，§9.9）；轮询；重试；因为作业多就限并发；
 *   **替模型编交代** —— 它点了没有的手、或者手自己起不来，那是缺陷，当场把进程打穿（见 `crash`）。
 *
 * 它不认识工具 / 技能 / 提示词分节 / MCP —— 那些词全在角色端口后面。
 *
 * 变因：控制流的推进方式（触发点、上下文组装、错误处置、出生与调度规则）。
 */
import { randomUUID } from "node:crypto";
import type { Node, NodeId } from "@meristem/atree";
import type { Job, Role, RoleId } from "@meristem/roles";
import { SUMMARY_FORK, all as allJobs } from "@meristem/roles";
import { createSink } from "./events.ts";
import type { Event, EventSink } from "./events.ts";
import type { ForkInput } from "./fork.ts";
import { born } from "./fork.ts";
import type { LlmClient } from "./llm.ts";
import { actionable, stateOf } from "./plan.ts";
import type { LineProps, LineStore, NodeState } from "./props.ts";
import type { ToolCall, WireMessage } from "./shape.ts";

/** 装配输入：**只有端口**，没有值。 */
export interface StartInput {
  readonly store: LineStore;
  readonly llm: LlmClient;
  /** 取角色：harness 眼里的能力入口只有这一个（角色由人选，不由模型挑）。 */
  readonly role: (id: RoleId) => Role;
}

/** 一棵正在跑的树：操作 + 事件。两个方向都收在这里，别处不另开口子。 */
export interface Tree {
  /**
   * 开树 / 恢复：按账走一遍，把**该说话的那几条线各叫一次**（重启之后也靠它接着走）。
   * 它不等谁说完 —— 叫完就返回，接下来由各个触发点接手。
   */
  resume(): void;

  /**
   * 说话：人的话就是账里的一条 user 消息，投给某一条线。落盘后返回。
   *
   * **这条线正在吐字时当场拒掉**（模型还没说完）：现在插话会让它的回答落在你的问题前面。
   * 界面据此告诉人"这条线正在吐字"。
   */
  say(node: NodeId, text: string): Promise<void>;

  /**
   * 分叉：开一条新线，返回新线的 id（界面据此选中它）。**造根就是 `parent: null` 的那一种**。
   *
   * `mode = "summarize"` 时这个动作里连着做完三件事（造线 → 穿总结角色抽底 → 穿人选角色回应），
   * 详细次序见 `ForkInput`。
   */
  fork(input: ForkInput): Promise<NodeId>;

  /** 收手：不再叫任何线，**并取消所有在跑的作业**（取消的交代仍是事实，照样进账）。 */
  stop(): void;

  /** 在跑的作业（**数据**，不是回调）：界面据此画树条带上的记号与手卡片。 */
  jobs(): readonly Job[];

  /** 人取消某个作业（界面上那张卡片）：转发给 `job.cancel()`，结局是一条交代。 */
  cancel(job: string): void;

  /**
   * 人重试：**只用于"模型接口失败"**（§9.8）—— 把这条线重新放回推进。
   * 它不修任何别的东西（作业有自己的超时与取消，别处不需要重试）。
   */
  retry(node: NodeId): void;

  /** 事件：看得见的那一面；返回退订。分发顺序 = 注册顺序。 */
  subscribe(consumer: (event: Event) => void): () => void;
}

/** 还没写进账的一条消息（`id` 是写账那一刻才定死的，见 DESIGN §9.6）。 */
type Fresh = Omit<WireMessage, "id">;

/** 一条线的运行态：**只在内存里**，进程一没就没了（"该不该说话"永远从账上重算）。 */
interface Live {
  /** 模型还没说完（这一格卡住的就是它：同一处不许再发一次）。 */
  speaking: boolean;
  /** 正在说话的功夫里又有人动过：说完再看一眼。 */
  again: boolean;
}

export function start(input: StartInput): Tree {
  const sink: EventSink = createSink();
  /** 模型接口失败过的线：**只在内存里**（§9.8 说账里一个字都不多），人重试 / 再开口时清掉。 */
  const failed = new Set<NodeId>();
  const live = new Map<NodeId, Live>();
  const seen = new Map<NodeId, NodeState>();
  let stopped = false;

  function liveOf(id: NodeId): Live {
    let state = live.get(id);
    if (state === undefined) {
      state = { speaking: false, again: false };
      live.set(id, state);
    }
    return state;
  }

  function node(id: NodeId): Node<LineProps> {
    const found = input.store.get(id);
    if (found === null) throw new Error(`账里没有这个节点：${id}`);
    return found;
  }

  /** 写账：`id` 由**我们**定死（传输层给的临时 id 不进账）。 */
  function append(id: NodeId, messages: readonly Fresh[]): void {
    input.store.append(
      id,
      messages.map((message) => ({ ...message, id: randomUUID() })),
    );
  }

  /** 这条线上还有没有作业在跑（就一次筛选，树不另存一份）。 */
  function hasJob(id: NodeId): boolean {
    return allJobs().some((job) => job.space === id);
  }

  /**
   * 缺陷（模型点了没有的手 / 手自己起不来 / 传输面用错）：**不回话、不兜底、不咽下去** ——
   * 把它扔回进程（定时器里抛 = 未捕获异常），让程序带着真实的栈倒下去。
   */
  function crash(error: unknown): void {
    setTimeout(() => {
      throw error;
    }, 0);
  }

  /** 把一段活儿包起来：缺陷走 `crash`，别的都不在这儿处理。 */
  function guard(work: Promise<void>): void {
    void work.catch(crash);
  }

  /** 状态只**发事件**、不进账：它是推出来的（读账 + 谁在跑），落一份进账只会漂（`props.ts`）。 */
  function emitState(id: NodeId): void {
    const state = stateOf(input.store, id, hasJob(id));
    if (seen.get(id) === state) return;
    seen.set(id, state);
    sink.emit({ type: "state", node: id, state });
  }

  /**
   * 让一条线说一轮（一次调用 + 把它伸出的手起起来）。
   * `messages` 显式传进来，是因为总结分叉那一轮看的**不是**新线自己看得见的东西（见 `fork`）。
   */
  async function speak(id: NodeId, role: Role, messages: readonly WireMessage[], by?: string): Promise<void> {
    let reply: WireMessage;
    try {
      reply = await input.llm.chat(
        { system: role.system(), messages },
        role.hands().map((hand) => hand.schema),
        {
          onText: (delta) => sink.emit({ type: "message", node: id, channel: "text", delta }),
          onReasoning: (delta) => sink.emit({ type: "message", node: id, channel: "thought", delta }),
          onUsage: (usage) => sink.emit({ type: "usage", node: id, usage }),
        },
      );
    } catch (error) {
      // 模型接口失败：账里一个字都不多 —— 这条线停在这儿，红字与重试归人（§9.8）。
      failed.add(id);
      sink.emit({
        type: "transport_error",
        node: id,
        error: error instanceof Error ? error : new Error(String(error)),
      });
      return;
    }

    append(id, [by === undefined ? reply : { ...reply, by }]);
    // 手按它在 `tool_calls` 里的顺序起（账的顺序 = 它写的顺序）；`run` 只负责"起起来"。
    for (const call of reply.toolCalls ?? []) await startHand(id, role, call);
  }

  /** 把一次调用变成一次执行：起手一条回话，结束一条消息（§9.5）。 */
  async function startHand(id: NodeId, role: Role, call: ToolCall): Promise<void> {
    const hand = role.hands().find((candidate) => candidate.name === call.name);
    if (hand === undefined) {
      // 模型只该点给它的手（schema 就在 wire 里）：点了没有的 = 传下去的手与它看到的不一致 ——
      // 那是缺陷，当场炸。**不替它编一条交代**：harness 一个字的文本都不写（§9.2）。
      throw new Error(
        `模型点了没有的手：${call.name}（这条线的角色是 ${role.id}，它的手只有：${role
          .hands()
          .map((candidate) => candidate.name)
          .join(" / ")}）`,
      );
    }

    // 手自己起不来（`run` 抛出）也是缺陷：交代是手写的东西，不由这里编（见底座的两个原语）。
    const job: Job = await hand.run(call.arguments, {
      outputRoot: node(id).props.outputRoot,
      space: id,
    });

    const started = job.report();
    append(id, [{ role: "tool", by: hand.name, content: started }]);
    sink.emit({ type: "hand_start", node: id, name: hand.name, args: call.arguments, job: job.id });

    // 还在跑就等它（不是轮询）；结束时那条消息进账、这条线被叫一声。
    void job.wait().then(() => {
      sink.emit({
        type: "hand_end",
        node: id,
        name: hand.name,
        job: job.id,
        secs: (Date.now() - job.at) / 1000,
      });
      const settled = job.report();
      if (settled !== started) append(id, [{ role: "user", by: hand.name, content: settled }]);
      advance(id);
    });
  }

  /**
   * 叫一条线说话 —— **同一个节点同时只发一次**：正在吐字就记一笔"等它说完再看"。
   *
   * 这就是全部的调度：没有队列、没有循环、没有全局扫描；该不该说话永远从账上重新算
   * （`plan.actionable`：账末该它说 + 这条线上没有还在跑的作业 + 不是"伸出去没回话"的未完成区）。
   */
  function advance(id: NodeId): void {
    if (stopped) return;
    emitState(id);

    const state = liveOf(id);
    if (state.speaking) {
      state.again = true;
      return;
    }
    if (!actionable(input.store, id, hasJob(id))) return;

    state.speaking = true;
    guard(
      speak(id, input.role(node(id).props.role), input.store.assemble(id)).finally(() => {
        state.speaking = false;
        emitState(id);
        if (state.again) {
          state.again = false;
          advance(id);
        }
      }),
    );
  }

  return {
    resume(): void {
      for (const id of input.store.nodes()) advance(id);
    },

    async say(id: NodeId, text: string): Promise<void> {
      node(id);
      if (liveOf(id).speaking) {
        throw new Error(
          "这条线正在吐字（模型还没说完）：等它说完再说 —— 现在插话会让它的回答落在你的问题前面",
        );
      }
      append(id, [{ role: "user", content: text }]);
      // 人又开口了，这条线就再试一次（§9.8 的重试是人的事）。
      failed.delete(id);
      advance(id);
    },

    async fork(choice: ForkInput): Promise<NodeId> {
      const parent = choice.parent === null ? null : node(choice.parent);
      const created = input.store.create(born(choice, parent));
      append(created, [{ role: "user", content: choice.inputText }]);
      emitState(created);

      if (choice.mode !== "summarize") {
        advance(created);
        return created;
      }

      // 总结分叉：这个动作里连着两轮（乙抽底 → 丙回应），中间不许别人插进来 —— 先占了那一格。
      const state = liveOf(created);
      state.speaking = true;
      try {
        // 乙：只抽底、不回应用户 —— 它看的是**父线看得见的历史 + 这条新消息**
        // （新线自带边界，往后自己看不到父线，所以这一轮要把两边都摆出来）。
        const history = parent === null ? [] : input.store.assemble(parent.id);
        await speak(
          created,
          input.role(SUMMARY_FORK),
          [...history, ...input.store.content(created)],
          SUMMARY_FORK,
        );
        // 丙：回应用户那句话（常规一轮：组装这条线看得见的 msgs）。
        await speak(created, input.role(choice.role), input.store.assemble(created));
      } catch (error) {
        crash(error);
      } finally {
        state.speaking = false;
        emitState(created);
      }

      return created;
    },

    stop(): void {
      stopped = true;
      for (const job of allJobs()) job.cancel();
    },

    jobs(): readonly Job[] {
      return allJobs();
    },

    cancel(job: string): void {
      const found = allJobs().find((candidate) => candidate.id === job);
      if (found === undefined) return;
      found.cancel();
    },

    retry(id: NodeId): void {
      failed.delete(id);
      advance(id);
    },

    subscribe: (consumer) => sink.subscribe(consumer),
  };
}
