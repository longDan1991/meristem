/**
 * 这一屏的共享状态，与"人的动作落到状态和账上"的编排 —— 屏幕的**店主**。
 *
 * **为什么是个 provider**：屏住在路由表里（`routes.ts`），离装配很远，拿到店主的路只有 context；
 * 仓库里"被多处读的共享状态"就是 provider（端口 / 事件两片都是这个形状）。装配层只负责把 `--at`
 * 这一件外面来的东西递进来。
 *
 * 共享状态（都被多个区读、或被**别处的键**写，所以由这一层持有、按区以 props 下发）：
 *   · **我站在哪条线**（`selected`）与**树上选中的那条**（`cursor`）—— 前者树 / 消息流 / 状态行 /
 *     底下那行 / 谁在动 都读；后者只树读。两者分开：P0 §6 —— ↑↓ 只移选中、不切过去；
 *   · **内容区在第几档 / 侧边在第几态第几页 / 卡片展不展** —— 写它们的是壳上的键（命令表里
 *     `view.*`），读它们的是内容区、侧边、底下那行；循环与"收掉一层"的走法是纯函数（`lib/view.ts`）；
 *   · **上一动作的回执**（`notice`）—— 状态行读；
 *   · **下一句话穿哪个角色**（`role`）—— 写它的挑角色那一屏，读它的是说话与分叉；
 *   · **草稿**（`draft` / `registerDraft`）—— 那一句话在**输入件**手里（它是可编辑件），这里只挂一个
 *     把手：说话 / 分叉要读它、写进账之后要清它。**不走 React 状态** —— 每敲一个字都惊动整棵树
 *     不值当（打字是热路径）。
 *
 * **这一条线自己的命令挂在这儿**（命令表里 `turn.*`）：账的动作本来就是这个对象的方法，所以
 * "谁接、什么条件下接"跟着它们写在一起（`useCommand`）—— 枢纽那一层不再有一张"id → 实现"的表。
 *
 * 变因：这一屏的共享状态与动作编排。
 */
import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import type { NodeId } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import { useCommand } from "@meristem/tui";
import { nextPage, nextSide, nextTier, unwindSide, unwindTier } from "../lib/view.ts";
import type { Side, Tier } from "../lib/view.ts";
import { useFacts } from "./facts.tsx";
import { useSession } from "./session.tsx";
import { useTreeActions } from "../hooks/tree-actions.ts";

/** 一个角色都没有时说什么（角色是部署的事：一个 xml 就是一个角色）。 */
export const NO_ROLE = "没有角色可用：角色的来源是 MERISTEM_ROLES 指的目录（那里一个 xml 就是一个角色）";

/**
 * 输入行挂上来的把手。**为什么是可变对象**：草稿在输入件手里，逐字更新它不能让整棵树重画
 * （打字是热路径），所以这里只留一个"当前那句话 + 清掉它"的引用。
 */
export interface DraftHandle {
  /** 现在草稿里是什么（说话 / 分叉读它）。 */
  text: string;
  clear(): void;
}

export interface Screen {
  readonly selected: NodeId | null;
  readonly cursor: NodeId | null;
  readonly notice: string;
  readonly tier: Tier;
  readonly side: Side;
  readonly page: number;
  readonly role: RoleId | null;
  readonly thoughts: boolean;
  /**
   * 屏自带的那一块占几行（现在只有主屏的输入行会报它）：内容区 = 整屏 − 壳 − 它。
   * 谁要按行算内容区（主屏算树的预算）就读它，不自己猜。
   */
  readonly composerRows: number;
  draft(): string;
  clearDraft(): void;
  /** 输入行报"我的把手在这儿"（卸下时报 `null`）。 */
  registerDraft(handle: DraftHandle | null): void;
  /** 屏自带的那一块报"我占几行"（卸下时报 0）。 */
  setComposerRows(rows: number): void;
  moveCursor(node: NodeId | null): void;
  enterLine(node: NodeId): void;
  notify(text: string): void;
  cycleTier(): void;
  unwindTier(): void;
  cycleSide(): void;
  unwindSide(): void;
  cyclePage(pages: number): void;
  toggleThoughts(): void;
  pickRole(role: RoleId): void;
  say(text: string): Promise<boolean>;
  fork(mode: "inherit" | "summarize", text: string): Promise<boolean>;
  stop(): void;
  retry(): void;
  quit(): void;
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
  const { store, roles, workspace, onExit } = useSession();
  const actions = useTreeActions();
  const { errors, clearError } = useFacts();
  const [selected, setSelected] = useState<NodeId | null>(() => at ?? store.root());
  // 树上选中的那条：进档 ②/③ 时默认盯住我站着的这条（P0 §6 第一行），所以初值跟 `selected` 一致。
  const [cursor, setCursor] = useState<NodeId | null>(() => at ?? store.root());
  const [tier, setTier] = useState<Tier>(1);
  const [side, setSide] = useState<Side>("hidden");
  const [page, setPage] = useState(0);
  const [thoughts, setThoughts] = useState(false);
  const [composerRows, setComposerRows] = useState(0);
  const [role, setRole] = useState<RoleId | null>(() => roles[0]?.id ?? null);
  // 一个角色都没有时，一进来就把话说清楚：不然按了回车像是界面卡住了
  const [notice, setNotice] = useState(() => (roles.length === 0 ? NO_ROLE : ""));

  const draftHandle = useRef<DraftHandle | null>(null);
  const registerDraft = useCallback((handle: DraftHandle | null) => {
    draftHandle.current = handle;
  }, []);
  const clearDraft = useCallback(() => draftHandle.current?.clear(), []);

  /** 站在哪条线跟着动时，树上的选中也跟过去（"我以外的线"只有自己按 ↑↓ 才会被选中）。 */
  const stand = useCallback((node: NodeId | null) => {
    setSelected(node);
    setCursor(node);
    setNotice("");
  }, []);

  const moveCursor = useCallback((node: NodeId | null) => {
    setCursor(node);
    setNotice("");
  }, []);

  const enterLine = useCallback(
    (node: NodeId) => {
      stand(node);
      setTier(1);
    },
    [stand],
  );

  const notify = useCallback((text: string) => setNotice(text), []);

  /** 树上除了我站着的这条还有没有别的线：没有就跳过档 ②（它那时没有内容可放）。 */
  const others = useCallback(() => selected !== null && store.nodes().some((id) => id !== selected), [selected, store]);

  const cycleTier = useCallback(() => setTier((current) => nextTier(current, others())), [others]);
  const unwindTierHere = useCallback(() => setTier((current) => unwindTier(current, others())), [others]);
  const cycleSide = useCallback(() => setSide((current) => nextSide(current)), []);
  const unwindSideHere = useCallback(() => setSide((current) => unwindSide(current)), []);
  const cyclePage = useCallback((pages: number) => setPage((current) => nextPage(current, pages)), []);
  const toggleThoughts = useCallback(() => setThoughts((open) => !open), []);

  const pickRole = useCallback((chosen: RoleId) => {
    setRole(chosen);
    setNotice("");
  }, []);

  const say = useCallback(
    async (text: string): Promise<boolean> => {
      if (text.trim() === "") return false;
      if (role === null) {
        setNotice(NO_ROLE);
        return false;
      }
      try {
        const node = selected ?? store.root();
        if (node === null) {
          // 还没有根：这一句就是开树的那句（造根 = 一次没有父的分叉，目录用数据根）
          const born = await actions.fork({ parent: null, mode: "inherit", role, text, dir: workspace });
          stand(born);
        } else {
          // 再开口 = 这条线不算"接口失败过的"了（harness 那边也一样）
          clearError(node);
          await actions.say(node, text);
          stand(node);
        }
        clearDraft();
        return true;
      } catch (error) {
        setNotice(messageOf(error));
        return false;
      }
    },
    [actions, clearDraft, clearError, role, selected, stand, store, workspace],
  );

  const fork = useCallback(
    async (mode: "inherit" | "summarize", text: string): Promise<boolean> => {
      if (role === null) {
        setNotice(NO_ROLE);
        return false;
      }
      const parent = selected ?? store.root();
      if (parent === null) {
        setNotice("还没有这条线：先说出第一句话，才有可分叉的地方");
        return false;
      }
      try {
        const born = await actions.fork({ parent, mode, role, text, dir: workspace });
        stand(born);
        setTier(1);
        clearDraft();
        return true;
      } catch (error) {
        setNotice(messageOf(error));
        return false;
      }
    },
    [actions, clearDraft, role, selected, stand, store, workspace],
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
    clearError(selected);
    actions.retry(selected);
    setNotice("已把这条线放回推进");
  }, [actions, clearError, errors, selected]);

  const quit = useCallback(() => onExit(), [onExit]);

  const draft = useCallback(() => draftHandle.current?.text ?? "", []);

  // 这一条线自己的那几条命令（命令表里 `turn.*`）—— **执行就近挂在这儿**：账的动作就是这个对象的方法，
  // 所以谁接、按什么条件接，跟那些方法写在一起。
  useCommand("turn.fork", (_id, arg) => {
    const text = draft();
    if (text.trim() === "") {
      notify("分叉要有那句话：它决定新线从父线历史里抽哪一份底");
      return;
    }
    void fork(arg === "summarize" ? "summarize" : "inherit", text);
  });
  useCommand("turn.stop", () => stop());
  // 没有"接口失败"要重试时这条命令没有接的人 —— 所以 `alt+r` 按不动，底下那行也不写它。
  useCommand("turn.retry", () => retry(), selected !== null && errors.has(selected));

  const value = useMemo<Screen>(
    () => ({
      selected,
      cursor,
      notice,
      tier,
      side,
      page,
      role,
      thoughts,
      composerRows,
      draft,
      clearDraft,
      registerDraft,
      setComposerRows,
      moveCursor,
      enterLine,
      notify,
      cycleTier,
      unwindTier: unwindTierHere,
      cycleSide,
      unwindSide: unwindSideHere,
      cyclePage,
      toggleThoughts,
      pickRole,
      say,
      fork,
      stop,
      retry,
      quit,
    }),
    [
      selected,
      cursor,
      notice,
      tier,
      side,
      page,
      role,
      thoughts,
      composerRows,
      draft,
      clearDraft,
      registerDraft,
      setComposerRows,
      moveCursor,
      enterLine,
      notify,
      cycleTier,
      unwindTierHere,
      cycleSide,
      unwindSideHere,
      cyclePage,
      toggleThoughts,
      pickRole,
      say,
      fork,
      stop,
      retry,
      quit,
    ],
  );

  return <ScreenContext.Provider value={value}>{children}</ScreenContext.Provider>;
}

/** 缺席就抛（不是返回默认值）：装配错要当场炸，不降级。 */
export function useScreen(): Screen {
  const screen = useContext(ScreenContext);
  if (screen === null) throw new Error("useScreen 必须在 ScreenProvider 里面用");
  return screen;
}
