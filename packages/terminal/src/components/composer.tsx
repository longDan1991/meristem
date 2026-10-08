/** @jsxImportSource @opentui/react */
/**
 * 输入行：人的话（打字归 opentui 的 `<input>`，回车才走账），以及**命令名单**那一层浮层。
 *
 * **这是主屏自带的一块**（只有要说话的那一屏需要它；别的屏不画输入行 —— 它们能按什么由自己那条键行写着）。
 * 位置由主屏自己给，要的东西也由主屏递下来（P0 §3：跟着"我这条线"走的那几行都归主屏）。
 *
 * 它自己只管四件：
 *   ① **焦点一直在它身上** —— 打字是"焦点里的那个可编辑件"的事，而这一屏只有这一个文字入口；
 *      焦点被别的东西拿走（鼠标点一下别处就会）之后就再也打不进字，屏幕上看不出为什么。
 *      **只在"这一屏在眼前"时握着**（`onActivated`）：被盖住的那一屏连隐藏着的输入件都该放手。
 *   ② **敲 `/` 弹名单**（P0 §2.1 的第二条进屏之路）：输入行上方列出匹配的命令、边打边过滤，
 *      回车执行；**以 `/` 开头的那一行不发模型**。名单不是一屏（P0 §2.3），它是这一行的一层浮层。
 *   ③ **把草稿挂给主屏**（`registerDraft`）：那一句话在输入件手里（它是可编辑件），说话 / 分叉要读它、
 *      写进账之后要清它。**挂一个可变的把手，不走 React 状态** —— 打字是热路径，每敲一个字惊动整棵树不值当。
 *   ④ **回车那一下归它**：名单里选中了哪条就执行哪条（问总线），没敲 `/` 就是一句话（交给主屏）。
 *
 * **这一层自带的命令就近挂在这儿**：名单开着时 `↑↓`/回车归名单（订阅 `list.*`，**挂上来的时刻就是
 * 这层浮层出现的时刻** —— 所以它压过树那一份，P0 §1 决策 4）、`esc` 先收掉名单（订阅 `app.close`）。
 * 壳上的那几条归壳；档与侧边归主屏；走位归眼前那份名单 —— 这里不再有"哪个键归谁"的判断。
 *
 * 变因：输入行的编辑器接法、命令名单浮层的画法与它自己那几条命令。
 */
import type { NodeId } from "@meristem/atree";
import { RowList, tone } from "@meristem/tui";
import { onActivated, onDeactivated, useBus, useCommands } from "@meristem/tui";
import type { Command } from "@meristem/tui";
import { CliRenderEvents, InputRenderableEvents } from "@opentui/core";
import type { InputRenderable } from "@opentui/core";
import { useRenderer } from "@opentui/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useCommand } from "../hooks/commands.ts";
import { FOLD } from "../lib/rows.ts";
import type { DraftHandle } from "../screens/main.tsx";

/** 名单最多铺几行（其余折成一行「还有 N 条」—— 说不出来的限制才是惩罚）。 */
export const PALETTE_ROWS = 8;

/** 输入行要的东西：我站着的那条线（占位文案）＋ 主屏的动作（说话 / 回执 / 草稿把手 / 行数）。 */
export interface ComposerProps {
  readonly selected: NodeId | null;
  readonly say: (text: string) => Promise<boolean>;
  readonly notify: (text: string) => void;
  readonly registerDraft: (handle: DraftHandle | null) => void;
  /** 报"这一块占几行"（含名单铺出来的那些行）：主屏据它算内容区的高度。 */
  readonly setRows: (rows: number) => void;
}

export function Composer({ selected, say, notify, registerDraft, setRows }: ComposerProps): ReactNode {
  const bus = useBus();
  const table = useCommands();
  const renderer = useRenderer();
  const input = useRef<InputRenderable>(null);
  // 草稿的镜像：名单要按它过滤、按它开关。**不往回写** —— 输入件才是草稿的 owner。
  const [draft, setDraft] = useState("");
  const [at, setAt] = useState(0);

  const clear = useCallback(() => {
    if (input.current !== null) input.current.value = "";
    setDraft("");
    setAt(0);
  }, []);

  // 挂给主屏的把手：说话 / 分叉读 `text`，写进账之后调 `clear`。
  const handle = useMemo<DraftHandle>(() => ({ text: "", clear }), [clear]);
  useEffect(() => {
    registerDraft(handle);
    return () => registerDraft(null);
  }, [handle, registerDraft]);

  // 焦点换了谁就把它抢回来（`focus()` 本来就幂等：已经在自己身上时什么都不做）。
  // **只在"这一屏在眼前"时握着**：被盖住的那一屏不该再吃按键。
  onActivated(() => {
    const again = (): void => input.current?.focus();
    renderer.on(CliRenderEvents.FOCUSED_RENDERABLE, again);
    again();
    return () => renderer.off(CliRenderEvents.FOCUSED_RENDERABLE, again);
  }, [input, renderer]);

  // 被盖住时**把焦点交出去**：不然打字会静静进到那只看不见的输入框里（藏着的盒子把焦点件 blur 掉
  // 这一步引擎不做 —— 它只在自己的 `visible` 翻转时 blur；我藏的是外面那个盒子）。
  // 卸载不算"被盖住"（这一屏没了），所以这一下写成 `onDeactivated`，不在 `onActivated` 的收尾里。
  onDeactivated(() => input.current?.blur(), [input]);

  // 草稿的镜像：插入 / 删除 / 被程序清掉都会发这个事件。顺带把名单的选择归零。
  useEffect(() => {
    const renderable = input.current;
    if (renderable === null) return;
    const mirror = (value: string): void => {
      handle.text = value;
      setDraft(value);
      setAt(0);
    };
    renderable.on(InputRenderableEvents.INPUT, mirror);
    mirror(renderable.value);
    return () => {
      renderable.off(InputRenderableEvents.INPUT, mirror);
    };
  }, [handle, input]);

  const open = draft.startsWith("/");
  const found = open ? table.matches(draft) : [];
  const choice = found[Math.min(at, Math.max(found.length - 1, 0))] ?? null;

  // 名单开着 = 这一层浮层在：`list.*` 归它（走位与回车都就地解决），`esc` 也先收它。
  // 挂上来的时刻就是它出现的时刻 → 总线从队尾往回问，它自然压过树那份。
  useCommand(
    "list.*",
    (id) => {
      if (id === "list.enter") {
        if (choice === null) return;
        const chosen = choice.id;
        clear();
        bus.ask(chosen);
        return;
      }
      if (found.length === 0) return;
      const delta = id === "list.prev" ? -1 : 1;
      setAt((current) => (current + delta + found.length) % found.length);
    },
    open,
  );
  useCommand("app.close", () => clear(), open);

  // 这一块占几行（输入 1 行 + 名单铺出来的那些行）：内容区是"整屏减这一屏自带的那几行再减这一块"。
  const paletteRows = !open
    ? 0
    : found.length === 0
      ? 1
      : Math.min(found.length, PALETTE_ROWS) + (found.length > PALETTE_ROWS ? 1 : 0);
  useEffect(() => {
    setRows(1 + paletteRows);
  }, [paletteRows, setRows]);

  /** 回车那一下：名单里选中了哪条就执行哪条；`/` 开头但没这条就说一声；其余是一句话。 */
  const submit = useCallback((): void => {
    if (choice !== null) {
      const chosen = choice.id;
      clear();
      bus.ask(chosen);
      return;
    }
    const text = input.current?.value ?? "";
    if (text.startsWith("/")) {
      notify(`没有这条命令：${text}`);
      clear();
      return;
    }
    if (text.trim() === "") return;
    // 说话写成之后主屏自己清草稿（它拿着那把把手）。
    void say(text);
  }, [bus, choice, clear, notify, say]);

  return (
    <box flexDirection="column" width="100%">
      {open ? <Palette draft={draft} found={found} at={at} /> : null}
      <input
        ref={input}
        focused
        width="100%"
        // 空树上第一句话就是开树的那句（P0 故事 1）：别的档位上这句话没有意义，所以是空的。
        placeholder={selected === null ? "这句话就是开树的那句" : ""}
        onSubmit={submit}
      />
    </box>
  );
}

/** 命令名单：一行一条命令（名字 + 别名 + 一句话），右端挂它的键。 */
function Palette({
  draft,
  found,
  at,
}: {
  readonly draft: string;
  readonly found: readonly Command[];
  readonly at: number;
}): ReactNode {
  const shown = found.slice(0, PALETTE_ROWS);
  const rest = found.length - shown.length;
  return (
    <box flexDirection="column" width="100%">
      <RowList
        items={shown.map((command, index) => ({
          key: command.id,
          text: `/${command.name ?? ""}${aliasesOf(command)}  ${command.desc}`,
          selected: index === at,
          mark: command.keys.map((binding) => binding.key).join(" ") || undefined,
        }))}
      />
      {found.length === 0 ? <text fg={tone.danger}>{`没有这条命令：${draft}`}</text> : null}
      {rest > 0 ? <text fg={tone.dim}>{`${FOLD}还有 ${rest} 条`}</text> : null}
    </box>
  );
}

function aliasesOf(command: Command): string {
  return command.aliases.length === 0 ? "" : ` (${command.aliases.map((alias) => `/${alias}`).join(" ")})`;
}
