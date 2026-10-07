/**
 * 命令总线（纯的那一半）：**谁在接、按什么次序问**。
 *
 * **两个职责，只有这两个**（这是这个模块存在的全部理由）：
 *   ① **别人问它**：一条命令（`view.tier`、`app.close`…）现在有没有人接、该找谁；
 *   ② **订阅**：谁想接就挂上来，不接了就摘掉。
 *   —— 名字、键、一句话、提示这些**展示**的东西不在这儿（那是命令表 `registry/commands.yaml` 的事）。
 *
 * **次序 = 出现的次序**：`subscribe` 追加在队尾，`ask` **从队尾往回**问第一个接的。
 * 谁挂上来，谁就是"刚刚出现的那个" —— 所以 `esc`（收掉眼前这一层）按下时收的正是最后出现的那一层。
 * 这条**不是**"注册顺序"的实现细节，它是这个机制的定义：P0 §1 决策 4 的判据就是"最后出现的那一层"。
 *
 * **一层只订一个**：同一条命令要是有两个接的人（比如"树"和"命令名单"都接 `list.*`），
 * 后挂上来的那个赢，前面那个**根本不会被问到** —— 所以不存在"两个都跑了"这种事。
 * 这也是它和广播的分界：广播是所有订阅者都跑（数据事件要那个），这里只跑一个。
 *
 * 变因：一条命令现在归谁接、按什么次序问。
 */

/** 接住之后干什么：拿到**具体 id**（通配订阅者要靠它分清是哪一条）与这个键带的参数。 */
export type Handling = (id: string, arg: string | undefined) => void;

/** 别处只用这两件：问一次、问"有接的人吗"。 */
export interface CommandBus {
  readonly ask: (id: string, arg?: string) => boolean;
  readonly live: (id: string) => boolean;
}

export interface Registry {
  /** 挂上来；返回摘掉它的函数。**位置 = 挂上来的时刻**（队尾）。 */
  subscribe(pattern: string, handling: Handling): () => void;
  /** 问一次：从队尾往回，第一个接的人执行并返回 `true`；没人接返回 `false`。 */
  ask(id: string, arg?: string): boolean;
  /** 这条命令这会儿有接的人吗（提示那一列要的是它，不是"现在按了会不会动"）。 */
  live(id: string): boolean;
}

/** 模式：精确的一条（`view.tier`），或整层（`screen.*`）。 */
export function matches(pattern: string, id: string): boolean {
  if (!pattern.endsWith(".*")) return pattern === id;
  const head = pattern.slice(0, -2);
  return id.startsWith(`${head}.`) && id.length > head.length + 1;
}

export function createRegistry(): Registry {
  const entries: { readonly pattern: string; readonly handling: Handling }[] = [];
  return {
    subscribe(pattern, handling) {
      const entry = { pattern, handling };
      entries.push(entry);
      return () => {
        const at = entries.indexOf(entry);
        if (at >= 0) entries.splice(at, 1);
      };
    },
    ask(id, arg) {
      // 队尾往回 = 最后出现的先问。"一层只订一个"就落在这个 `return` 上。
      for (let i = entries.length - 1; i >= 0; i -= 1) {
        const entry = entries[i];
        if (entry === undefined || !matches(entry.pattern, id)) continue;
        entry.handling(id, arg);
        return true;
      }
      return false;
    },
    live(id) {
      return entries.some((entry) => matches(entry.pattern, id));
    },
  };
}
