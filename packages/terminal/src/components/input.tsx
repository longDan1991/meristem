/**
 * 输入行：人的话（打字只动本地缓冲区，回车才写账）。
 *
 * **键都归它自己**：可打印字符 / `backspace` / `delete` / `←→` / `home` / `end` 编辑草稿；
 * `enter` 说话、`ctrl+b` · `alt+b` 分叉、`ctrl+r` 换分叉用的角色 —— 提交的语境都在这一行。
 * 草稿（`hooks/draft.ts`）与分叉角色（`hooks/fork-role.ts`）也都是它自己的状态。
 *
 * 写账失败时**草稿不清**：人那句话还在，不用重打一遍（所以两个回调回的是"账写成了没有"）。
 *
 * 变因：这一区画什么、它接哪些键、它的本地状态。
 */
import type { NodeId } from "@meristem/atree";
import type { RoleId } from "@meristem/roles";
import { InputBox, isPrintable, useKeys } from "@meristem/tui";
import { memo } from "react";
import type { ReactElement } from "react";
import { useDraftBuffer } from "../hooks/draft.ts";
import { NO_CHOICE, useForkRole } from "../hooks/fork-role.ts";
import { usePlaceholder } from "../hooks/selectors.ts";
import { useSession } from "../providers/session.tsx";

export interface InputRegionProps {
  /** 投给哪条线（`null` = 人还没进过任何一条线）。 */
  readonly target: NodeId | null;
  /** 说话；返回"账写成了没有"（成了才清草稿）。 */
  readonly onSend: (target: NodeId | null, text: string, role: RoleId) => Promise<boolean>;
  /** 分叉；返回"账写成了没有"。 */
  readonly onFork: (
    parent: NodeId,
    mode: "inherit" | "summarize",
    text: string,
    role: RoleId,
  ) => Promise<boolean>;
  /** 一句回执（比如"总结分叉要有那句新话"）。 */
  readonly onNotice: (text: string) => void;
}

export const InputRegion = memo(function InputRegion({
  target,
  onSend,
  onFork,
  onNotice,
}: InputRegionProps): ReactElement {
  const { store, roles } = useSession();
  const draft = useDraftBuffer();
  const role = useForkRole(roles);
  const hint = usePlaceholder(target);

  useKeys((key) => {
    if (isPrintable(key)) {
      draft.insert(key);
      return;
    }
    switch (key) {
      case "backspace":
        draft.erase(-1);
        return;
      case "delete":
        draft.erase(1);
        return;
      case "left":
      case "right":
      case "home":
      case "end":
        draft.moveCaret(key);
        return;
      case "enter":
        void submit();
        return;
      case "ctrl+b":
        void branch("inherit");
        return;
      case "alt+b":
        void branch("summarize");
        return;
      case "ctrl+r": {
        const next = role.cycle();
        if (next !== null) onNotice(`分叉用的角色：${next.title}（${next.id}）`);
        return;
      }
      default:
        return;
    }
  });

  async function submit(): Promise<void> {
    const text = draft.text;
    if (text.trim() === "") return;
    const chosen = role.current;
    if (chosen === null) {
      onNotice(NO_CHOICE);
      return;
    }
    if (await onSend(target, text, chosen.id)) draft.clear();
  }

  async function branch(mode: "inherit" | "summarize"): Promise<void> {
    const parent = target ?? store.root();
    if (parent === null) {
      onNotice("还没有根：先说一句什么");
      return;
    }
    const chosen = role.current;
    if (chosen === null) {
      onNotice(NO_CHOICE);
      return;
    }
    const text = draft.text;
    if (mode === "summarize" && text.trim() === "") {
      onNotice("总结分叉要有那句新话：它决定新线从父线历史里抽哪一份底");
      return;
    }
    if (await onFork(parent, mode, text, chosen.id)) draft.clear();
  }

  return <InputBox value={draft.text} caret={draft.caret} placeholder={hint} />;
});
