/**
 * 三只作业共享手：`job_list` / `job_output` / `job_cancel`。
 *
 * **所有角色都有**（装载器无条件并入，xml 里不必点名）：它们属于执行机制，
 * 不是某块能力的开关 —— 模型看不见作业，就不知道一手跑没跑完、也没法看进度或停掉它。
 * 它们**本身也是作业**（立刻结束的那种）：不为作业另立一套协议，结果照常进账。
 *
 * 它们拿作业只有一条路：`HandContext.space` + 作业表（`table.ts`）。
 * **按空间筛**：只有**这条线上起的**作业在列 —— 从父线继承下来的消息里提到过的那些作业
 * 不属于它（那是别人空间里的东西，早就结束了）。
 *
 * 变因：模型侧那三只手的语义（怎么看、怎么停）。
 */
import type { Hand } from "../role.ts";
import { progress, settled } from "./base.ts";
import { find, running } from "./table.ts";

/** 看进度这条纪律三只手共用一句话：等待是循环的事，轮询不是模型的事。 */
const WAITING_IS_THE_LOOP_S_JOB =
  "等待是循环的事：该等就把这一轮说完 —— 作业一结束循环会叫醒你，别拿 job_output 当轮询手段。";

/** 这条线上现在有哪些作业在跑：按 `space` 筛作业表，说出 id / 名字 / 已跑多久 / 吐了多少。 */
export const JOB_LIST: Hand = {
  name: "job_list",
  description:
    "这条线上现在有哪些作业还在跑。只列**这条线自己起的**作业，每条给出 id、名字、已跑多久、吐了多少字。",
  schema: { type: "object", properties: {}, additionalProperties: false },
  snippet: "看这条线上还有哪些作业在跑",
  guidelines: [WAITING_IS_THE_LOOP_S_JOB],
  async run(_args: unknown, ctx) {
    const jobs = running(ctx.space);
    const text =
      jobs.length === 0
        ? "这条线上现在没有还在跑的作业。"
        : `这条线上有 ${jobs.length} 个作业还在跑：\n${jobs
            .map((job) => `· #${job.id}（${job.name}）：${progress(job)}`)
            .join("\n")}`;
    return settled({ space: ctx.space, name: "job_list" }, text);
  },
};

/** 看某个作业现在吐了什么。**尾巴 ≠ 最终交代**（后者在作业结束时进账）—— description 里要写死。 */
export const JOB_OUTPUT: Hand = {
  name: "job_output",
  description:
    "看某个还在跑的作业现在吐了什么。这是**有界窗口（头 + 尾）**，中间的原文在这里看不到，" +
    "**它不是最终交代** —— 最终交代会在作业结束时自动进账，不要靠它来交付或收尾。",
  schema: {
    type: "object",
    properties: { id: { type: "string", description: "作业 id（消息里那个 # 后面的东西）" } },
    required: ["id"],
    additionalProperties: false,
  },
  snippet: "看一个还在跑的作业现在吐了什么（尾巴，有界）",
  guidelines: [WAITING_IS_THE_LOOP_S_JOB],
  async run(args: unknown, ctx) {
    const { id } = args as { id: string };
    const job = find(ctx.space, id);
    const text =
      job === null
        ? `这条线上没有 #${id} 这个还在跑的作业（它可能已经结束了 —— 结束的交代就在对话里）。`
        : `#${id}（${job.name}）：${progress(job)}\n--- 尾巴（有界窗口，不是最终交代）---\n${job.output() || "（还没有输出）"}`;
    return settled({ space: ctx.space, name: "job_output" }, text);
  },
};

/** 不想让它跑了：结局是一条交代（"被人取消了"）。 */
export const JOB_CANCEL: Hand = {
  name: "job_cancel",
  description:
    "让某个还在跑的作业停下（它等的东西多半不会来了 —— 等输入、挂住的远端调用）。" +
    "结局仍然是一条交代（“被人取消了”），马上会进账，不是特殊的失败状态。",
  schema: {
    type: "object",
    properties: { id: { type: "string", description: "作业 id（消息里那个 # 后面的东西）" } },
    required: ["id"],
    additionalProperties: false,
  },
  snippet: "让一个还在跑的作业停下",
  async run(args: unknown, ctx) {
    const { id } = args as { id: string };
    const job = find(ctx.space, id);
    if (job === null) {
      return settled(
        { space: ctx.space, name: "job_cancel" },
        `这条线上没有 #${id} 这个还在跑的作业（它可能已经结束了 —— 结束的交代就在对话里）。`,
      );
    }
    job.cancel();
    return settled(
      { space: ctx.space, name: "job_cancel" },
      `已经让 #${id}（${job.name}）停下；它的交代马上进账。`,
    );
  },
};

/**
 * 三只作业共享手 —— **所有角色都有**（装载器无条件并入）。
 *
 * 它们的 `description` 要写明两件事（schema 是唯一语义来源，不在提示词里重复）：
 *   1. **看尾巴 ≠ 拿到最终交代**：最终交代会在作业结束时进账，别把 `job_output` 当交付；
 *   2. **别拿 `job_output` 当轮询手段**：要等就说完这一轮 —— 等待是循环的事，作业结束会叫醒这条线。
 */
export const JOB_HANDS: readonly Hand[] = [JOB_LIST, JOB_OUTPUT, JOB_CANCEL];
