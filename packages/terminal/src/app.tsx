/**
 * 应用：订阅事件 + 用 tui 的组件装出一屏 + 收人的动作。
 *
 * 人的动作只有三个**写账**的：**说话**（选中哪条线就投给哪条线）、**分叉**（从选中的线分出新的一条，
 * 分叉时挑角色）、**收手**；外加一个**本地**动作：**切节点**（改"我站在哪"，只影响选中与渲染，
 * 不写账）。三者全落在 `Tree` 上，别处不另开写账的口子。不做"给模型看的输入"：人的话就是账里的
 * 一条 user 消息。
 *
 * **照看两件事**（都是"面向人"的动作，DESIGN §9.2）：
 *   · **取消一个作业**：作用在"选中线上那张**选中的手卡片**"上（在线上的作业里选，缺省选最近一个在跑的）；
 *   · **重试**：只在界面上有红字（模型接口失败）时有效 —— `Tree.retry(node)` 把那条线放回推进。
 * 两个都只转发，不在界面里编语义：作业的文本一律来自 `Job.report()` / `Job.output()`
 * （事件只带结构：作业 id、名字、参数、秒数）。
 *
 * **全局一棵树**（DESIGN §7）：树一直在这儿，所以没有"新会话 / 接着哪个会话"这回事 ——
 * **新会话 = 以根为父的一次分叉**（界面上一个动作）；造根 = 一次"没有父的分叉"，全局只发生一次。
 * 从哪儿接着看 = 切节点（`--at` 是它的启动形式）。
 *
 * 读账直接读 `Store`（渲染树、画一条线）—— 名字 / 角色 / 做事目录都在节点的 `props` 里
 * （那是 harness 定的形状），一条线自己的对话在它的内容里。事件从 `Tree.subscribe` 来，
 * 它只是"去看账 / 去看作业"的提示；作业吐出来的东西界面自己遍历 `Job.stream()`
 * （`message` / `hand_start` / `hand_end` / `usage` / `transport_error`），**真相是账与作业本身**。
 *
 * **一屏五区**：
 *   1. **树条带** —— 每条线一行（人写的名字 + 角色 + 在跑的记号），`↑` / `↓` 切节点；
 *   2. **消息流** —— 选中那条线的账（人 / 模型 / 思考 / 手的过程）＋ 末尾接"正在吐、还没进账"的字；
 *   3. **实时区** —— 这一轮正在吐的**思考**（`ThoughtLine`）＋ 选中的那张**手卡片**（`HandCard`，
 *      输出自己遍历 `Job.stream()`，原文不裁剪）；
 *   4. **状态条** —— 选中线的事实 + 用量 + 这会儿能用的键；
 *   5. **输入行** —— 人的话（只动本地缓冲区，回车才写账）。
 *
 * **颜色与键位住这一层**：`view.ts` 只给语义标签（`RowTag`），这里把它映射成 tui 的通用样式词；
 * 键位也一样 —— tui 只把按键归一化成字符串，键位语义全在这一处（`onKey`）。
 *
 * 屏归这一个应用所有：不写裸 ANSI，也不开第二个渲染器抢同一块屏。
 *
 * 变因：交互与布局（几区怎么排、键位、选中语义、把事件映射成组件 props）。
 */
import type { NodeId } from "@meristem/atree";
import type { LineStore, Tree, Usage } from "@meristem/harness";
import type { Job, Role, RoleId } from "@meristem/roles";
import { SUMMARY_FORK } from "@meristem/roles";
import {
  Frame,
  HandCard,
  InputBox,
  MessageStream,
  StatusBar,
  ThoughtLine,
  TreeStrip,
  openScreen,
  type MessageLine,
  type MessageLineStyle,
  type TreeStripItem,
} from "@meristem/tui";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactElement } from "react";
import type { Row, RowTag, TreeRow } from "./view.ts";
import { lineRows, treeRows } from "./view.ts";

export interface UiProps {
  readonly store: LineStore;
  readonly tree: Tree;
  /** 分叉时让人挑的角色清单（数据来源只有 roles 一处）。 */
  readonly roles: readonly Role[];
  /** 数据根：**造根**时用（没有父可以继承目录）；之后每条线的目录缺省继承父。 */
  readonly workspace: string;
  /** 人一开始站在哪条线上（`--at`）；`null` = 还没进过任何一条线。 */
  readonly at: NodeId | null;
  /** 退出（收手、还原终端由 `mount` 负责）：这里只喊一声。 */
  readonly onExit: () => void;
}

/**
 * 输入缓冲区：文本与光标**一个状态**。
 *
 * 草稿是**同步状态**（`useRef` + 重画）而不是渲染闭包里的值：
 *   · 同一拍里连来几个键，各自接在前一个的结果上（读闭包会让"跑个命令"只剩最后一个字）；
 *   · **动作读到的就是此刻的草稿** —— 打字快 / 粘贴一整行再回车时，闭包里的那份还是空的，
 *     于是回车把这句话静默吞掉（人以为卡住了）。
 */
interface Draft {
  readonly text: string;
  readonly caret: number;
}

/** 一个作业的界面事实：事件只带结构（名字 / 参数 / id），一个字的内容都不带。 */
interface HandFact {
  readonly name: string;
  readonly args: string;
}

/**
 * 正在吐、还没进账的字（一条线一份）。
 *
 * `base` = 这份字开始攒的时候账有多长：账一长出来（assistant 那条进账了），这份字就作废 ——
 * 从这里画过的东西又从账里画一遍就是两份，而"哪一份才是事实"没有答案。
 */
interface Tail {
  readonly node: NodeId;
  readonly base: number;
  readonly text: string;
  readonly thought: string;
}

/** 语义标签 → 通用样式词：颜色映射只住这一处（tui 不认识业务标签）。 */
const STYLE: Record<RowTag, MessageLineStyle> = {
  title: "accent",
  dim: "dim",
  user: "accent",
  model: "plain",
  thought: "dim",
  hand: "dim",
  error: "danger",
};

/** 树条带最多铺几行（选中行永远在窗口里，其余靠折叠与滚动）。 */
const STRIP_ROWS = 8;
/** 空缓冲区（一个常量，免得每次重置都造一个对象）。 */
const EMPTY_DRAFT: Draft = { text: "", caret: 0 };

/** 一次滚多少行。 */
const SCROLL_STEP = 10;
/** 作业输出可能吐得很密：重画合成到 50ms 一帧，不然一行一个 setState 会把屏幕淹掉。 */
const OUTPUT_FRAME_MS = 50;

/** 一整屏：树条带 + 选中那条线的消息流 + 实时输出 + 状态条 + 输入行。 */
export function App(props: UiProps): ReactElement {
  const { store, tree, roles, workspace } = props;

  const [selected, setSelected] = useState<NodeId | null>(props.at);
  const draft = useRef<Draft>(EMPTY_DRAFT);
  const [tail, setTail] = useState<Tail | null>(null);
  const [facts, setFacts] = useState<ReadonlyMap<string, HandFact>>(new Map());
  const [errors, setErrors] = useState<ReadonlyMap<NodeId, string>>(new Map());
  const [usages, setUsages] = useState<ReadonlyMap<NodeId, Usage>>(new Map());
  // 分叉用它开启：机制角色（总结分叉的乙）不是给人挑的能力，跳过它
  const [forkRole, setForkRole] = useState<RoleId>(() => pickers(roles)[0]?.id ?? "");
  const [jobCursor, setJobCursor] = useState(0);
  const [thoughtsOpen, setThoughtsOpen] = useState(false);
  const [scrollBack, setScrollBack] = useState(0);
  // 一个可挑的角色都没有时，一进来就把话说清楚：不然按了回车像是界面卡住了
  const [notice, setNotice] = useState(() => (pickers(roles).length === 0 ? NO_CHOICE : ""));
  const [, redraw] = useState(0);

  // 事件只带结构：记下结构事实，然后重画一帧（账与作业自己去读）
  useEffect(() => {
    return tree.subscribe((event) => {
      switch (event.type) {
        case "message":
          setTail((current) => {
            const grew = current === null || current.node !== event.node || current.base !== store.content(event.node).length;
            const base = grew ? store.content(event.node).length : current.base;
            const text = grew ? "" : current.text;
            const thought = grew ? "" : current.thought;
            return event.channel === "text"
              ? { node: event.node, base, text: text + event.delta, thought }
              : { node: event.node, base, text, thought: thought + event.delta };
          });
          break;
        case "hand_start":
          setFacts((current) => new Map(current).set(event.job, { name: event.name, args: jsonOf(event.args) }));
          setTail((current) => (current?.node === event.node ? null : current));
          break;
        case "hand_end":
          setFacts((current) =>
            new Map(current).set(event.job, { name: event.name, args: current.get(event.job)?.args ?? "" }),
          );
          break;
        case "usage":
          setUsages((current) => new Map(current).set(event.node, event.usage));
          break;
        case "transport_error":
          setErrors((current) => new Map(current).set(event.node, event.error.message));
          break;
      }
      redraw((tick) => tick + 1);
    });
  }, [store, tree]);

  const jobs = tree.jobs();
  const node = selected !== null && store.get(selected) !== null ? selected : null;
  const lineJobs = node === null ? [] : jobs.filter((job) => job.space === node);
  const current = lineJobs[Math.min(jobCursor, lineJobs.length - 1)] ?? null;

  const output = useJobOutput(current);
  const now = useNow(lineJobs.length > 0);

  // 消息流：账里的行（思考可按 ctrl+o 收起）＋ 正在吐的正文（思考单独在实时区画，不重复）
  const accountRows = node === null ? [] : lineRows(store, node, []);
  const live = node === null ? null : unaccounted(store, node, tail);
  const streamRows: readonly MessageLine[] = [
    ...(thoughtsOpen ? accountRows : foldedThoughts(accountRows)).map(toMessageLine),
    ...split(live?.text ?? "", "model").map(toMessageLine),
  ];

  const strip = buildStrip(treeRows(store, node, jobs), errors);
  const status = buildStatus(store, node, lineJobs, usages, current !== null, notice);
  const thinking = split(live?.thought ?? "", "thought");

  const handler = useRef<(key: string) => void>(() => {});
  handler.current = (key: string): void => {
    if (key === "ctrl+c") {
      props.onExit();
      return;
    }
    if (key === "enter") {
      guard(send());
      return;
    }
    if (key === "ctrl+b") {
      guard(fork("inherit"));
      return;
    }
    if (key === "alt+b") {
      guard(fork("summarize"));
      return;
    }
    if (key === "ctrl+x") {
      tree.stop();
      setNotice("已收手：不再叫任何线，在跑的作业都取消了");
      return;
    }
    if (key === "ctrl+t") {
      guard(retry());
      return;
    }
    if (key === "ctrl+o") {
      setThoughtsOpen((open) => !open);
      return;
    }
    if (key === "ctrl+r") {
      cycleRole();
      return;
    }
    if (key === "escape") {
      cancelJob();
      return;
    }
    if (key === "tab") {
      setJobCursor((cursor) => (lineJobs.length === 0 ? 0 : (cursor + 1) % lineJobs.length));
      return;
    }
    if (key === "up" || key === "down") {
      moveSelection(key === "up" ? -1 : 1);
      return;
    }
    if (key === "alt+up" || key === "pageup") {
      setScrollBack((back) => back + (key === "pageup" ? SCROLL_STEP : 1));
      return;
    }
    if (key === "alt+down" || key === "pagedown") {
      setScrollBack((back) => Math.max(0, back - (key === "pagedown" ? SCROLL_STEP : 1)));
      return;
    }
    if (key === "left" || key === "right" || key === "home" || key === "end") {
      moveCaret(key);
      return;
    }
    if (key === "backspace" || key === "delete") {
      edit(key === "backspace" ? -1 : 1);
      return;
    }
    if (isPrintable(key)) insert(key);
  };

  /** 一次按键的处理身份固定（Frame 那边不必为每个渲染重新订阅键盘）。 */
  const onKey = useCallback((key: string) => handler.current(key), []);

  return (
    <Frame onKey={onKey}>
      <TreeStrip items={strip.items} />
      <MessageStream rows={streamRows} follow={scrollBack === 0} offset={scrollBack} />
      {thinking.length > 0 ? <ThoughtLine rows={thinking.map((row) => row.text)} open /> : null}
      {current === null ? null : (
        <HandCard
          name={current.name}
          args={facts.get(current.id)?.args}
          output={output}
          state="running"
          secs={(now - current.at) / 1000}
        />
      )}
      <StatusBar left={status.left} right={status.right} />
      <InputBox value={draft.current.text} caret={draft.current.caret} placeholder={placeholder(node, store.root())} />
    </Frame>
  );

  // ---- 动作：写账的只有三样，其余是本地动作 ----

  async function send(): Promise<void> {
    const text = draft.current.text;
    if (text.trim() === "") return;
    if (forkRole === "") {
      setNotice(NO_CHOICE);
      return;
    }
    setNotice("");
    const target = node ?? store.root();
    if (target === null) {
      // 还没有根：这一句就是开树的那句（造根 = 一次没有父的分叉，目录用数据根）
      const born = await tree.fork({ parent: null, role: forkRole, inputText: text, dir: workspace });
      // 送进去了才清草稿：动作失败时人那句话还在，不用重打一遍
      clearDraft();
      setSelected(born);
      return;
    }
    // 再开口 = 这条线不算"接口失败过的"了（harness 那边也一样）
    setErrors((current) => without(current, target));
    await tree.say(target, text);
    clearDraft();
    setSelected(target);
  }

  async function fork(mode: "inherit" | "summarize"): Promise<void> {
    const parent = node ?? store.root();
    if (parent === null) {
      setNotice("还没有根：先说一句什么");
      return;
    }
    if (forkRole === "") {
      setNotice(NO_CHOICE);
      return;
    }
    const text = draft.current.text;
    setNotice("");
    if (mode === "summarize" && text.trim() === "") {
      setNotice("总结分叉要有那句新话：它决定新线从父线历史里抽哪一份底");
      return;
    }
    const born = await tree.fork({ parent, role: forkRole, inputText: text, mode });
    clearDraft();
    setSelected(born);
  }

  async function retry(): Promise<void> {
    if (node === null || !errors.has(node)) {
      setNotice("这条线没有接口失败要重试");
      return;
    }
    setNotice("已把这条线放回推进");
    setErrors((current) => without(current, node));
    tree.retry(node);
  }

  function cancelJob(): void {
    if (current === null) {
      setNotice("这条线上没有在跑的作业");
      return;
    }
    tree.cancel(current.id);
    setNotice(`已让「${current.name}」停下（作业 #${current.id}）`);
  }

  function moveSelection(delta: number): void {
    const ids = strip.selectable;
    if (ids.length === 0) return;
    const at = node === null ? -1 : ids.indexOf(node);
    const next = at < 0 ? (delta > 0 ? 0 : ids.length - 1) : Math.min(Math.max(at + delta, 0), ids.length - 1);
    setNotice("");
    setSelected(ids[next] ?? null);
    setJobCursor(0);
    setScrollBack(0);
  }

  function cycleRole(): void {
    const choosable = pickers(roles);
    if (choosable.length === 0) return;
    const at = choosable.findIndex((role) => role.id === forkRole);
    const next = choosable[(at + 1) % choosable.length];
    if (next === undefined) return;
    setForkRole(next.id);
    setNotice(`分叉用的角色：${next.title}（${next.id}）`);
  }

  function insert(text: string): void {
    const buffer = draft.current;
    draft.current = {
      text: buffer.text.slice(0, buffer.caret) + text + buffer.text.slice(buffer.caret),
      caret: buffer.caret + text.length,
    };
    redraw((tick) => tick + 1);
  }

  /** 删光标前（-1）或光标后（1）的一个字符；到边了就不动。 */
  function edit(direction: -1 | 1): void {
    const buffer = draft.current;
    if (direction === -1) {
      if (buffer.caret === 0) return;
      draft.current = {
        text: buffer.text.slice(0, buffer.caret - 1) + buffer.text.slice(buffer.caret),
        caret: buffer.caret - 1,
      };
    } else {
      if (buffer.caret >= buffer.text.length) return;
      draft.current = {
        text: buffer.text.slice(0, buffer.caret) + buffer.text.slice(buffer.caret + 1),
        caret: buffer.caret,
      };
    }
    redraw((tick) => tick + 1);
  }

  function moveCaret(key: string): void {
    const buffer = draft.current;
    const caret =
      key === "home"
        ? 0
        : key === "end"
          ? buffer.text.length
          : Math.min(Math.max(buffer.caret + (key === "left" ? -1 : 1), 0), buffer.text.length);
    draft.current = { text: buffer.text, caret };
    redraw((tick) => tick + 1);
  }

  function clearDraft(): void {
    draft.current = EMPTY_DRAFT;
    setScrollBack(0);
    redraw((tick) => tick + 1);
  }

  /** 动作失败是**给人看的一件事**（界面上那行提示）：账没变、作业没变，人自己决定下一步。 */
  function guard(action: Promise<void>): void {
    void action.catch((error: unknown) => {
      setNotice(error instanceof Error ? error.message : String(error));
    });
  }
}

/** 接管终端、订阅事件、把人的输入送回账里；返回时终端已还原。非真终端时逐帧追加（降级）。 */
export async function mount(props: Omit<UiProps, "onExit">): Promise<void> {
  const screen = await openScreen();
  const exit = Promise.withResolvers<void>();
  const element = <App {...props} onExit={() => exit.resolve()} />;
  try {
    screen.render(element);
    if (!process.stdout.isTTY) {
      // 降级：没有差分重画，所以每有事发生就再追加一帧（React 按类型 diff，状态不丢）
      const unsubscribe = props.tree.subscribe(() => screen.render(element));
      try {
        await exit.promise;
      } finally {
        unsubscribe();
      }
      return;
    }
    await exit.promise;
  } finally {
    await screen.restore();
  }
}

// ---- 渲染用的小函数：都在这里，方便一眼看出"界面只拼结构，不拼语义" ----

/** 把账里的行按 `ctrl+o` 收/展：收起来的一串思考压成一行说明（**看得见的限制**，不是静默丢字）。 */
function foldedThoughts(rows: readonly Row[]): readonly Row[] {
  const folded: Row[] = [];
  let run = 0;
  for (const row of rows) {
    if (row.tag === "thought") {
      run += 1;
      continue;
    }
    if (run > 0) folded.push({ text: `▸ 思考 ${run} 行（ctrl+o 展开）`, tag: "dim" });
    run = 0;
    folded.push(row);
  }
  if (run > 0) folded.push({ text: `▸ 思考 ${run} 行（ctrl+o 展开）`, tag: "dim" });
  return folded;
}

function toMessageLine(row: Row): MessageLine {
  return { text: row.text, style: STYLE[row.tag] };
}

/** 正在吐的字里账里还没有的那部分（assistant 那条一进账，它整段就都在账里了）。 */
function unaccounted(store: LineStore, node: NodeId, tail: Tail | null): Tail | null {
  if (tail === null || tail.node !== node) return null;
  const last = store.content(node).at(-1);
  if (last === undefined || last.role !== "assistant") return tail;
  return {
    node,
    base: tail.base,
    text: last.content.endsWith(tail.text) ? "" : tail.text,
    thought: (last.reasoning ?? "").endsWith(tail.thought) ? "" : tail.thought,
  };
}

function split(text: string, tag: RowTag): readonly Row[] {
  return text === "" ? [] : text.split("\n").map((line) => ({ text: line, tag }));
}

function buildStrip(rows: readonly TreeRow[], errors: ReadonlyMap<NodeId, string>): {
  readonly items: readonly TreeStripItem[];
  readonly selectable: readonly NodeId[];
} {
  // 只画选中行所在的那个窗口：树一大，条带会吃掉整屏（可选的那份是**全部**行，↑/↓ 走全树）。
  const at = rows.findIndex((row) => row.selected);
  const start = windowOffset(at, rows.length);
  const items = rows.slice(start, start + STRIP_ROWS).map((row) => {
    const failure = row.id === null ? undefined : errors.get(row.id);
    const mark = [row.mark, failure === undefined ? undefined : "✗ 接口失败"].filter((part) => part !== undefined).join(" ");
    return { id: row.id ?? "", text: row.text, selected: row.selected, mark: mark === "" ? undefined : mark };
  });
  return { items, selectable: rows.flatMap((row) => (row.id === null ? [] : [row.id])) };
}

/** 让选中的那一行落在窗口里（树条带只铺 `STRIP_ROWS` 行）。 */
function windowOffset(at: number, total: number): number {
  if (total <= STRIP_ROWS || at < 0) return 0;
  const half = Math.floor(STRIP_ROWS / 2);
  return Math.min(Math.max(at - half, 0), total - STRIP_ROWS);
}

function buildStatus(
  store: LineStore,
  node: NodeId | null,
  lineJobs: readonly Job[],
  usages: ReadonlyMap<NodeId, Usage>,
  hasJob: boolean,
  notice: string,
): { readonly left: string; readonly right: string } {
  if (node === null) {
    // 没有根时**更**要说清楚：人正要打第一句话，这时按回车没反应最像"界面卡住了"。
    return {
      left: notice === "" ? "还没有根 —— 说一句什么，就以它开第一条线" : notice,
      right: "enter 说话 · ctrl+c 退出",
    };
  }
  const facts = store.get(node)?.props;
  const left = [
    facts === undefined ? node : `${facts.name} · ${facts.role} · ${shortPath(facts.outputRoot)}`,
    lineJobs.length > 0 ? `在跑 ${lineJobs.length}` : undefined,
    notice === "" ? undefined : notice,
  ]
    .filter((part) => part !== undefined)
    .join(" · ");
  const keys = ["enter 说话", "ctrl+b 分叉", "tab 作业", hasJob ? "esc 取消" : undefined, "ctrl+c 退出"].filter(
    (part) => part !== undefined,
  );
  return { left, right: [usageLine(usages.get(node)), keys.join(" · ")].filter((part) => part !== undefined).join("  ") };
}

/** 一行里放不下整条路径：留住最后一段，省略**看得见**（状态条是给人扫一眼的，不是账）。 */
function shortPath(path: string): string {
  const parts = path.split("/").filter((part) => part !== "");
  const tail = parts.at(-1) ?? path;
  return path.length <= 24 || parts.length <= 1 ? path : `…/${tail}`;
}

function usageLine(usage: Usage | undefined): string | undefined {
  if (usage === undefined) return undefined;
  return `↑${tokens(usage.prompt)} ↓${tokens(usage.completion)}（思考 ${tokens(usage.reasoning)} / 缓存 ${tokens(usage.cached)}）`;
}

function tokens(count: number): string {
  return count < 1000 ? String(count) : `${(count / 1000).toFixed(1)}k`;
}

function placeholder(node: NodeId | null, root: NodeId | null): string {
  if (node === null) return "说一句什么（没有根就以这一句开第一条线）";
  if (root === null) return "说一句什么";
  return "跟这条线说一句（回车进账）";
}

/** 一个可挑的角色都没有时说什么：角色是部署的事（一个 xml 一个角色），代码不替它编一个。 */
const NO_CHOICE =
  "没有可选的角色：一个人选的角色就是一个 xml，放进 MERISTEM_ROLES 指的目录" +
  "（内置的 summary-fork 是分叉时程序穿的机制角色，不给人挑）";

/** 人挑得到的角色：机制角色（总结分叉）不在里面 —— 它是分叉时程序穿的那一位，不是一块能力。 */
function pickers(roles: readonly Role[]): readonly Role[] {
  return roles.filter((role) => role.id !== SUMMARY_FORK);
}

function jsonOf(value: unknown): string {
  return JSON.stringify(value) ?? String(value);
}

/** 归一化后的键里，哪些算"打进去一个字"（其余是命令，见 `onKey`）。 */
function isPrintable(key: string): boolean {
  return key.length > 0 && !key.includes("+");
}

function without<K, V>(map: ReadonlyMap<K, V>, key: K): ReadonlyMap<K, V> {
  const next = new Map(map);
  next.delete(key);
  return next;
}

/**
 * 跟着一个作业的输出走（**原文，不裁剪**）：先给已有的、再给新来的，作业一结束就收。
 *
 * 累积在 ref 里、重画按 `OUTPUT_FRAME_MS` 合成 —— 每来一块就 setState 会把屏幕淹掉，
 * 而拼整段取长度是 O(输出) 的（要长度就问 `Job.produced()`）。
 */
function useJobOutput(job: Job | null): readonly string[] {
  const lines = useRef<string[]>([]);
  const partial = useRef("");
  const pending = useRef(false);
  const [, bump] = useState(0);

  useEffect(() => {
    lines.current = [];
    partial.current = "";
    pending.current = false;
    if (job === null) return;
    let live = true;
    const frame = setInterval(() => {
      if (!pending.current) return;
      pending.current = false;
      bump((tick) => tick + 1);
    }, OUTPUT_FRAME_MS);
    void (async () => {
      for await (const chunk of job.stream()) {
        if (!live) return;
        const parts = (partial.current + chunk).split("\n");
        partial.current = parts.pop() ?? "";
        lines.current.push(...parts);
        pending.current = true;
      }
      pending.current = true;
    })();
    return () => {
      live = false;
      clearInterval(frame);
    };
  }, [job]);

  return partial.current === "" ? lines.current : [...lines.current, partial.current];
}

/** "已跑多久"要走字：有作业在跑时每秒重画一次，没有就不转（界面自己的一秒，与树无关）。 */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return now;
}
