/** @jsxImportSource @opentui/react */
/**
 * 主屏：默认那一屏（表里标了 `index: true` 的那一屏）—— **一条线 + 一块结构 + 一块侧边 + 它自带的四行**，
 * 外加这条线自己的**状态与动作**。
 *
 * **这一屏的状态就住在这个文件里**（`MainScreen` 的局部状态）：我站在哪条线、树上选中哪条、档、侧边、
 * 第几页、卡片展不展、输入件占几行、上一动作的回执 —— 加这一屏自己的那几条键与动作。
 * 它们和"这一屏画什么"共享同一个变因：加一档结构、换一种说法，状态、动作、它接的键、它画的行都要一起动
 * （模块边界按共同变因划，不按"名词"划）。所以这一处同时是这一屏的状态、读它的口、与它本身。
 *
 * **为什么不用为了"进屏回来"把状态提到上面**：屏不卸载了 —— 路由留着整个栈，被盖住的只是藏起来
 * （`@meristem/tui` 的 `router.ts`），所以进挑角色再回来，这一屏还是原来那个实例，P0 §6 的
 * "回来时是**原档、原侧边态**"由路由本身给。**提上去的只有一件**：`role`（下一句话穿谁）——
 * 挑角色那一屏要**写**它，而屏之间只有参数这条路（参数是导航数据，`back()` 也不带回头值），
 * 所以它挂在路由上面，见下面的 `RoleChoiceProvider`。
 *
 * **零件吃 props**：对话、树、那三行、输入行都是"这一屏里的零件"，要什么由这一屏递下去。
 *
 * 这一屏自己的状态：
 *   · **我站在哪条线**（`selected`）与**树上选中的那条**（`cursor`）—— 前者对话 / 状态行 / 事实行 /
 *     谁在动 都读；后者只树读。两者分开：P0 §6 —— ↑↓ 只移选中、不切过去；
 *   · **内容区在第几档 / 侧边在第几态第几页 / 卡片展不展** —— 写它们的是这一屏自己那几条键（`view.*`）；
 *   · **上一动作的回执**（`notice`）—— 状态行与事实行读；
 *   · **草稿**（把手）—— 那句话在**输入件**手里（它是可编辑件），这里只挂一个引用：
 *     说话 / 分叉要读它、写进账之后要清它。**不走 React 状态** —— 每敲一个字都惊动整棵树不值当。
 *
 * **这一条线自己的命令挂在这儿**（命令表里 `turn.*` 与 `view.*`）：账的动作本来就是这个对象的方法，
 * 所以"谁接、什么条件下接"跟着它们写在一起（`useCommand`）—— 别处不再有一张"id → 实现"的表。
 * 这几条**只在这一屏在眼前时接**（`useCommand` 里那一半由路由的 `onActivated` 给）：被盖住时按不到
 * —— `ctrl+x` 那种"任何档都该按得动"说的是**任何档**，不是"任何屏"（P0 §1 故事 20）。
 * 全局的那两条（进屏 / 退出）归壳（`layout/shell.tsx`）。
 *
 * 变因：主屏有哪几档、每档里摆哪几块、自带哪几行、档 ② 从对话那里借多少、侧边吃多少列，
 * 以及这条线的状态与动作。
 */
import type { NodeId } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import type { ScreenViewProps } from "@meristem/tui";
import { useTerminalDimensions } from "@opentui/react";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Composer } from "../components/composer.tsx";
import { LiveRegion } from "../components/realtime.tsx";
import { SidePanel } from "../components/side.tsx";
import { FactLine, KeyLine, StatusLine } from "../components/status.tsx";
import { StreamRegion } from "../components/stream.tsx";
import { TreeView } from "../components/tree-view.tsx";
import { WhoRunning } from "../components/who-running.tsx";
import { useCommand } from "../hooks/commands.ts";
import { useTreeActions } from "../hooks/tree-actions.ts";
import { SIDE_PAGES } from "../lib/side.ts";
import { nextPage, nextSide, nextTier, unwindSide, unwindTier } from "../lib/view.ts";
import type { Side, Tier } from "../lib/view.ts";
import { useFacts } from "../providers/facts.tsx";
import { useSession } from "../providers/session.tsx";

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

/** **两个屏共用的那一个值**：下一句话穿哪个角色（挑角色那一屏写它，说话与分叉读它）。 */
export interface RoleChoice {
  readonly role: RoleId | null;
  /** 挑了一位：下一句话就穿它（说话与分叉都算）。 */
  pick(role: RoleId): void;
}

const RoleChoiceContext = createContext<RoleChoice | null>(null);

/**
 * 它为什么挂在路由**上面**（`app.tsx`）：写它的是挑角色那一屏，读它的是主屏 —— 两个屏之间只有
 * 参数这条路，而参数是导航数据（`back()` 也不带回头值），所以这一个值得由上面发。
 * 别的主屏状态不在这儿：那些只被这一屏自己读（见文件头）。
 */
export function RoleChoiceProvider({ children }: { readonly children: ReactNode }): ReactNode {
  const { roles } = useSession();
  const [role, setRole] = useState<RoleId | null>(() => roles[0]?.id ?? null);
  const pick = useCallback((chosen: RoleId) => setRole(chosen), []);
  const value = useMemo<RoleChoice>(() => ({ role, pick }), [role, pick]);
  return <RoleChoiceContext.Provider value={value}>{children}</RoleChoiceContext.Provider>;
}

/** 缺席就抛（不是返回默认值）：装配错要当场炸，不降级。 */
export function useRoleChoice(): RoleChoice {
  const choice = useContext(RoleChoiceContext);
  if (choice === null) throw new Error("useRoleChoice 必须在 RoleChoiceProvider 里面用");
  return choice;
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** 这一屏自带、行数固定的那几行：状态行 + 事实行 + 键行。输入行不在里面 —— 它会随名单长高，自己报数。 */
const OWN_ROWS = 3;

/** 档 ② 那段树最多占内容区的几分之一（P0 §4：≤ 内容高/3，夹 3..16 行）。 */
const BUDGET_SHARE = 3;
const BUDGET_MIN = 3;
const BUDGET_MAX = 16;

/** 分栏时右侧那一列多宽（P0 §9 第 3 条把宽度档位留作开口：先给一档）。 */
const SPLIT_MIN = 28;
const SPLIT_SHARE = 3;

/** 档 ② 的树段行数预算。 */
export function tierBudget(rows: number): number {
  return Math.min(Math.max(Math.floor(rows / BUDGET_SHARE), BUDGET_MIN), BUDGET_MAX);
}

export function MainScreen(_props: ScreenViewProps<void>): ReactNode {
  const { store, roles, workspace, at } = useSession();
  const { role } = useRoleChoice();
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
  // 一个角色都没有时，一进来就把话说清楚：不然按了回车像是界面卡住了
  const [notice, setNotice] = useState(() => (roles.length === 0 ? NO_ROLE : ""));

  const draftHandle = useRef<DraftHandle | null>(null);
  const registerDraft = useCallback((handle: DraftHandle | null) => {
    draftHandle.current = handle;
  }, []);
  const clearDraft = useCallback(() => draftHandle.current?.clear(), []);

  // 换了角色，上一动作的回执不再算数（挑角色那一屏改写 `role`，这一行字读的是"上一动作"）。
  const worn = useRef(role);
  useEffect(() => {
    if (worn.current === role) return;
    worn.current = role;
    setNotice("");
  }, [role]);

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
  // 没有"接口失败"要重试时这条命令没有接的人 —— 所以 `alt+r` 按不动，键行也不写它。
  useCommand("turn.retry", () => retry(), selected !== null && errors.has(selected));

  // 这一屏自带的那几条（`view.*`）。`view.side-page` 只在侧边开着时有主：没开就没有页可换。
  useCommand("view.tier", () => cycleTier());
  useCommand("view.side", () => cycleSide());
  useCommand("view.side-page", () => cyclePage(SIDE_PAGES.length), side !== "hidden");
  // `esc` 在这一屏有两层可收：侧边占满 → 分成两栏；档不是 ① → 收回一档。
  // `active` 就是"这一层在不在" —— 挂上来的时刻 = 这层出现的时刻，所以后出现的先收。
  useCommand("app.close", () => unwindSideHere(), side === "full");
  useCommand("app.close", () => unwindTierHere(), tier !== 1);

  const { width: cols, height } = useTerminalDimensions();
  const rows = Math.max(1, height - OWN_ROWS - composerRows);

  // 对话那一块：账 + 正在吐的字 + 在跑的卡片；它自己滚动、贴着底（新行进来时看的是最新那段）。
  const talk = useMemo(
    () => (
      <scrollbox
        flexGrow={1}
        stickyScroll
        stickyStart="bottom"
        contentOptions={{ justifyContent: "flex-end" }}
        verticalScrollbarOptions={{ visible: false }}
      >
        <StreamRegion node={selected} thoughts={thoughts} toggleThoughts={toggleThoughts} />
        <LiveRegion node={selected} />
      </scrollbox>
    ),
    [selected, thoughts, toggleThoughts],
  );

  const split = Math.max(SPLIT_MIN, Math.floor(cols / SPLIT_SHARE));
  // 内容区的宽度**只在"收起 ↔ 分栏"之间变，绝不变成 0**：来回压成 0 会把里面那份贴底滚动盒量坏
  // （回到分栏时它自己撑满、把树顶出视野）。占满全屏那一态是**不显示**它（`visible`），不是卸载 ——
  // 卸载还会让区里的订阅跟着摘挂一遍，次序跟着乱动。
  const contentWidth = side === "hidden" ? "100%" : cols - split;
  return (
    <box flexDirection="column" width="100%" height="100%">
      {/* 内容区 + 侧边：宽度在这一格里分。 */}
      <box flexDirection="row" flexGrow={1} width="100%">
        <box flexDirection="column" width={contentWidth} visible={side !== "full"}>
          {tier === 3 ? null : talk}
          {tier === 1 ? <WhoRunning selected={selected} /> : null}
          {tier === 2 ? (
            <TreeView
              size={tierBudget(rows)}
              detail
              cursor={cursor}
              moveCursor={moveCursor}
              enterLine={enterLine}
            />
          ) : null}
          {tier === 3 ? (
            <TreeView size={rows} detail={false} cursor={cursor} moveCursor={moveCursor} enterLine={enterLine} />
          ) : null}
        </box>
        {side === "hidden" ? null : (
          // 侧边**浮在上面**：这样无论内容区多宽，它都拿得住自己那一份（分栏时右边一列、占满时整屏），
          // 不用跟内容区抢 flex 空间。
          <box
            position="absolute"
            top={0}
            left={side === "full" ? 0 : cols - split}
            width={side === "full" ? "100%" : split}
          >
            <SidePanel page={page} />
          </box>
        )}
      </box>
      {/* 这一屏自带的四行：状态行 → 输入行（含它上面那层名单）→ 事实行 → 键行（P0 §3 的 ③④⑤⑥）。 */}
      <StatusLine selected={selected} notice={notice} />
      <Composer
        selected={selected}
        say={say}
        notify={notify}
        registerDraft={registerDraft}
        setRows={setComposerRows}
      />
      <FactLine selected={selected} notice={notice} />
      <KeyLine />
    </box>
  );
}
