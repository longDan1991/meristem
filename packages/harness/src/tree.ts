/**
 * 一棵树的推进器：**harness 对外只有两样 —— 操作与事件。**
 *
 * 界面能做的动作全在 `Tree` 的方法上，能看见的东西全在 `subscribe` 那一栏；没有第三样。
 * 读账（渲染树、画一条线）是 atree 的面，界面直接读 `Store`，不从这里过。
 *
 * **harness 不要任何配置值，只要端口**（账、角色表、传输）。它不定义"配置"、不读 `.env`、
 * 也没有自己的旋钮：没有并发上限（分叉是人做的，同时在飞的东西本来就不多，该动的线全部一起推），
 * 没有轮次 / 深度 / 节点 / token / 时间上限（DESIGN §5.5）。数据根 / 角色目录 / 模型引用 / 钥匙
 * 分别是 atree、roles、传输的事，由装配层读一次配置后分头交过去。
 *
 * **生命周期**（这套定义的正文）：
 *   开    —— 装配层把树接上（空树则连根都还没有）；**造根 = 一次没有父的分叉**（全局一棵树，只发生一次）
 *   恢复  —— 读账即恢复：谁欠一句话是算得出来的（`plan.actionable`）
 *   推进  —— 组装这条线看得见的 msgs（`Store.assemble`）→ 让模型说话 →
 *            把它伸出的手交给角色起作业 → **起手一条回话、结束一条消息**（见下）→ 唤醒
 *   等人  —— 没有人的操作、也没有在跑的作业：**等待，不是返回**（人不在场是常态，DESIGN §5.7）
 *   出生  —— 人分叉，开一条新线（两种模式见 `ForkInput`）
 *   收手  —— 人的动作，`stop`（顺带取消所有在跑的作业）
 *
 * 人的动作只有三个：**说话 / 分叉 / 收手**（结构动作只有人有，模型只能提议 —— DESIGN §5.3
 * 这条靠接口写死：模型那侧只有手，拿不到 `Tree`）；另外两个是照看性的：**取消一个作业**、
 * **重试一次模型接口失败**。
 *
 * 操作从队列进来、事件往订阅者出去（消息传递，不共享可变状态、不加锁）：
 * 界面在自己的事件处理里调 `say` / `fork` 时，`run()` 可能正跑着，所以**所有写账只由一个消费者串行落盘**。
 * **唤醒归循环自己**：时机都是它造成的（人的操作、作业结束），不需要去"观察"账 —— 树包只管数据。
 *
 * **作业在循环里的位置**（DESIGN §9.2 的"面向循环"）：
 *
 *   1. 起手：把 `args`、`ctx`（`{ outputRoot, space = 这个节点 }`）交给 `hand.run`，拿回一个 `Job`
 *      （作业表由底座登记，循环不写那张表）。
 *   2. **起手一条回话**：立刻往账里写一条 `role: "tool"` 的回话，内容 = `job.report()`
 *      （还在跑 → "作业 #abc 已起…"；已经结束 → 结果）—— 每个 `tool_calls` 因此条条有回话，
 *      provider 那边天然合法，**程序不需要任何配对结构**。
 *   3. **结束一条消息**：若它还在跑，就等它（`job.wait()`，**循环从不 poll**）—— settle 时再往账里写
 *      一条 `role: "user"` 的消息（内容 = `report()`，同一个作业 id 在里面），发状态事件、**唤醒这条线**；
 *      **内容没变就不写第二次**（立刻结束的手只留起手那一条）。
 *   4. 调度时跳过"还有作业在跑"的线（`plan.actionable(..., true)`；表就是 `roles` 那张，按空间筛）。
 *   5. 人取消 → 转发 `job.cancel()`；`stop`（收手）→ 取消所有在跑的作业。
 *   6. 模型接口失败 → 跳过这条线 + `Event.transport_error`（不入账、不自动重试，§9.8）。
 *
 *   绝不做的：判断这一手会长不长（§9.3）；生成任何文本（消息内容一律来自 `job.report()`）；
 *   设统一超时（超时在每只手的底座里，§9.9）；轮询；重试；因为作业多就限并发；
 *   **替模型编交代** —— 它点了没有的手、或者手自己起不来，那是缺陷，当场炸（见 `advance` 里的 `guard`）。
 *
 * **各条线互不等待**：一轮起起来就往下走（同一轮只起一次用 `busy` 挡），谁先回来谁先被推 ——
 * 一条慢线不该堵住别的线。
 *
 * 它不认识工具 / 技能 / 提示词分节 / MCP —— 那些词全在角色端口后面。
 *
 * 变因：控制流的推进方式（唤醒、上下文组装、错误处置、出生与调度规则）。
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

/** 一棵正在推进的树：操作 + 事件。两个方向都收在这里，别处不另开口子。 */
export interface Tree {
  /** 推进到收手为止：树休息不是出口。 */
  run(): Promise<void>;

  /** 说话：人的话就是账里的一条 user 消息，投给某一条线。落盘后返回。 */
  say(node: NodeId, text: string): Promise<void>;

  /**
   * 分叉：开一条新线，返回新线的 id（界面据此选中它）。**造根就是 `parent: null` 的那一种**。
   *
   * `mode = "summarize"` 时这个动作里连着做完三件事（造线 → 穿总结角色抽底 → 穿人选角色回应），
   * 详细次序见 `ForkInput`。
   */
  fork(input: ForkInput): Promise<NodeId>;

  /** 收手：循环停手，**并取消所有在跑的作业**（不留可见残留；取消的交代仍是事实，照样进账）。 */
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

export function start(input: StartInput): Tree {
  const sink: EventSink = createSink();
  /** 模型接口失败过的线：**只在内存里**（§9.8 说账里一个字都不多），人重试时清掉。 */
  const failed = new Set<NodeId>();
  /** 正在推的线：同一轮不许被推两次（`fork` 里那几轮也占着这一格）。 */
  const busy = new Set<NodeId>();
  /** 缺陷（模型点了没有的手 / 手自己起不来）：记下来，由 `run` 当场炸出去 —— 不在这儿吞。 */
  let defect: unknown = null;
  const seen = new Map<NodeId, NodeState>();
  let stopping = false;
  let woken = false;
  let wakeup: (() => void) | null = null;

  /**
   * 唤醒：把挂着的那个等待解开；**没人挂的时候把标记留下** ——
   * 人操作可能正好发生在循环入睡之前，丢了这一下这条线就再也没人叫了。
   */
  function wake(): void {
    woken = true;
    const resolve = wakeup;
    wakeup = null;
    resolve?.();
  }

  /** 等人：挂起来，直到有人动（人的操作 / 作业结束 / 收手）；已经有人动过就不睡。 */
  async function idle(): Promise<void> {
    if (woken) return;
    const { promise, resolve } = Promise.withResolvers<void>();
    wakeup = resolve;
    await promise;
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

  /** 哪些空间里还有作业在跑（一次问到位，循环不逐条查）。 */
  function runningSpaces(): ReadonlySet<string> {
    return new Set(allJobs().map((job) => job.space));
  }

  /**
   * 让一条线说一轮（它是一整轮：一次调用 + 把它伸出的手起起来）。
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

    // 还在跑就等它（不是轮询）；结束时那条消息进账、这条线被唤醒。
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
      wake();
    });
  }

  /**
   * 把一轮包起来：出了缺陷就记下来（`run` 会把它炸出去），完事唤醒 ——
   * 一轮结束是"可能有别的线该动了"的时机，所以唤醒归它自己（不靠谁在外面等）。
   */
  function guard(work: Promise<void>): Promise<void> {
    return work
      .catch((error: unknown) => {
        defect ??= error;
      })
      .finally(() => wake());
  }

  /**
   * 把该动的线都**起起来**（起完就返回，**不等它们**）：一条线慢不该堵住别的线。
   * 返回"这一轮起了几轮"。
   */
  function advance(): boolean {
    const running = runningSpaces();
    let started = false;

    for (const id of input.store.nodes()) {
      if (failed.has(id) || busy.has(id)) continue;
      if (!actionable(input.store, id, running.has(id))) continue;
      busy.add(id);
      started = true;
      void guard(
        speak(id, input.role(node(id).props.role), input.store.assemble(id)).finally(() => busy.delete(id)),
      );
    }

    return started;
  }

  /** 状态只**发事件**、不进账：它是推出来的（读账 + 谁在跑），落一份进账只会漂（`props.ts`）。 */
  function emitStates(): void {
    const running = runningSpaces();
    for (const id of input.store.nodes()) {
      const state = stateOf(input.store, id, running.has(id));
      if (seen.get(id) === state) continue;
      seen.set(id, state);
      sink.emit({ type: "state", node: id, state });
    }
  }

  async function run(): Promise<void> {
    while (!stopping) {
      if (defect !== null) throw defect;
      woken = false;
      const started = advance();
      emitStates();
      // 起了新活就马上再看一眼（收尾 / 接手）；否则没别的事就睡到有人动为止。
      if (!started && !woken) await idle();
    }
  }

  return {
    run,

    async say(id: NodeId, text: string): Promise<void> {
      append(id, [{ role: "user", content: text }]);
      failed.delete(id);
      wake();
    },

    async fork(choice: ForkInput): Promise<NodeId> {
      const parent = choice.parent === null ? null : node(choice.parent);
      const created = input.store.create(born(choice, parent));
      append(created, [{ role: "user", content: choice.inputText }]);
      busy.add(created);

      try {
        if (choice.mode === "summarize") {
          // 乙：只抽底、不回应用户 —— 它看的是**父线看得见的历史 + 这条新消息**
          // （新线自带边界，往后自己看不到父线，所以这一轮要把两边都摆出来）。
          const history = parent === null ? [] : input.store.assemble(parent.id);
          await guard(
            speak(
              created,
              input.role(SUMMARY_FORK),
              [...history, ...input.store.content(created)],
              SUMMARY_FORK,
            ),
          );
          // 丙：回应用户那句话（常规一轮：组装这条线看得见的 msgs）。
          if (defect === null) {
            await guard(speak(created, input.role(choice.role), input.store.assemble(created)));
          }
        }
      } finally {
        busy.delete(created);
        emitStates();
        wake();
      }

      return created;
    },

    stop(): void {
      stopping = true;
      for (const job of allJobs()) job.cancel();
      wake();
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
      wake();
    },

    subscribe: (consumer) => sink.subscribe(consumer),
  };
}
