/**
 * 这一屏的共享状态，与"人的动作落到状态和账上"的编排 —— 屏幕的**店主**。
 *
 * **为什么是个 provider**：屏住在路由表里（`screens/table.ts`），离装配很远，拿到店主的路只有
 * context；仓库里"被多处读的共享状态"就是 provider（端口 / 事件两片都是这个形状），所以它不再是一个
 * 只给 `app.tsx` 调的 hook。装配层只负责把 `--at` 这一件外面来的东西递进来。
 *
 * 共享状态只有两样（都被多个区读，所以由这一层持有、按区以 props 下发）：
 *   · **我站在哪条线**（`selected`）—— 树条带 / 消息流 / 实时区 / 状态条都读；
 *   · **上一动作的回执**（`notice`）—— 状态条读。
 *
 * 其余状态不住这里：各区自己的视图状态（思考展不展、滚到哪、在第几张卡片、草稿、分叉角色）
 * 由区自己持有 —— 那些的写者与读者都在同一处；吐字与作业事实来自事件，住 `providers/tail.tsx` /
 * `providers/facts.tsx`。
 *
 * 编排 = 把人的动作接到上面的状态与写账上（`hooks/tree-actions.ts`）：说话 / 分叉成功后把选中
 * 落到新线上，失败把那句话写进回执 —— 动作本身不吞错，这一层负责把它变成**给人看的一件事**。
 *
 * 变因：这一屏的共享状态与动作编排。
 */
import { createContext, useCallback, useContext, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import type { NodeId } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import { useFacts } from "./facts.tsx";
import { useSession } from "./session.tsx";
import { NO_CHOICE, pickers } from "../hooks/fork-role.ts";
import { useTreeActions } from "../hooks/tree-actions.ts";

export interface Screen {
  readonly selected: NodeId | null;
  readonly notice: string;
  /** 切节点：↑↓、说话、分叉都走它（区自己只报"下一个是谁"），顺带清掉上一句回执。 */
  select(node: NodeId | null): void;
  /** 写一句回执。 */
  notify(text: string): void;
  /**
   * 说话：投给 `target`；`target === null` 时，这一句就是开树的那句。
   * 成功后选中落在写入的那条线上；失败写进回执并回 `false`（调用方据此决定要不要清草稿）。
   */
  send(target: NodeId | null, text: string, role: RoleId): Promise<boolean>;
  /** 分叉：从 `parent` 分出新的一条，成功选中它并回 `true`；失败写进回执并回 `false`。 */
  fork(parent: NodeId, mode: "inherit" | "summarize", text: string, role: RoleId): Promise<boolean>;
  /** 收手（`ctrl+x`）：不再叫任何线，在跑的作业都取消。 */
  stop(): void;
  /** 重试选中的线（`ctrl+t`，只对"模型接口失败"有效）。 */
  retry(): void;
  /** 取消一个在跑的作业（实时区那张选中的卡片）。 */
  cancel(job: string, name: string): void;
}

export interface ScreenProps {
  /**
   * 人一开始站在哪条线上（`--at`）；**没给（`null`）就站在根**（树的入口）。
   * 空树（连根都还没有）时无处可站，`selected` 才是 `null` —— 那时第一句话就是开树的那句。
   */
  readonly at: NodeId | null;
  readonly children: ReactNode;
}

const ScreenContext = createContext<Screen | null>(null);

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function ScreenProvider({ at, children }: ScreenProps): ReactElement {
  const { store, roles, workspace } = useSession();
  const actions = useTreeActions();
  const { errors, clearError } = useFacts();
  const [selected, setSelected] = useState<NodeId | null>(() => at ?? store.root());
  // 一个可挑的角色都没有时，一进来就把话说清楚：不然按了回车像是界面卡住了
  const [notice, setNotice] = useState(() => (pickers(roles).length === 0 ? NO_CHOICE : ""));

  const select = useCallback((node: NodeId | null) => {
    setSelected(node);
    setNotice("");
  }, []);

  const notify = useCallback((text: string) => setNotice(text), []);

  const send = useCallback(
    async (target: NodeId | null, text: string, role: RoleId): Promise<boolean> => {
      if (text.trim() === "") return false;
      try {
        const node = target ?? store.root();
        if (node === null) {
          // target 为 null：这一句就是开树的那句（造根 = 一次没有父的分叉，目录用数据根）
          const born = await actions.fork({ parent: null, mode: "inherit", role, text, dir: workspace });
          setSelected(born);
        } else {
          // 再开口 = 这条线不算"接口失败过的"了（harness 那边也一样）
          clearError(node);
          await actions.say(node, text);
          setSelected(node);
        }
        setNotice("");
        return true;
      } catch (error) {
        setNotice(messageOf(error));
        return false;
      }
    },
    [actions, clearError, store, workspace],
  );

  const fork = useCallback(
    async (parent: NodeId, mode: "inherit" | "summarize", text: string, role: RoleId): Promise<boolean> => {
      try {
        const born = await actions.fork({ parent, mode, role, text, dir: workspace });
        setSelected(born);
        setNotice("");
        return true;
      } catch (error) {
        setNotice(messageOf(error));
        return false;
      }
    },
    [actions, workspace],
  );

  const stop = useCallback(() => {
    actions.stop();
    setNotice("已收手：不再叫任何线，在跑的作业都取消了");
  }, [actions]);

  const retry = useCallback(() => {
    if (selected === null || !errors.has(selected)) {
      setNotice("这条线没有接口失败要重试");
      return;
    }
    setNotice("已把这条线放回推进");
    clearError(selected);
    actions.retry(selected);
  }, [actions, clearError, errors, selected]);

  const cancel = useCallback(
    (job: string, name: string) => {
      actions.cancel(job);
      setNotice(`已让「${name}」停下（作业 #${job}）`);
    },
    [actions],
  );

  return (
    <ScreenContext.Provider value={{ selected, notice, select, notify, send, fork, stop, retry, cancel }}>
      {children}
    </ScreenContext.Provider>
  );
}

/** 缺席就抛（不是返回默认值）：装配错要当场炸，不降级。 */
export function useScreen(): Screen {
  const screen = useContext(ScreenContext);
  if (screen === null) throw new Error("useScreen 必须在 ScreenProvider 里面用");
  return screen;
}
