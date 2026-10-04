/** @jsxImportSource @opentui/react */
/**
 * 输入行：人的话（打字归 opentui 的 `<input>`，回车才写账）。
 *
 * **单行编辑器不再自己写**：光标、宽字符、粘贴、撤销、左移右移、超出窗口时的水平滚动，
 * `<input>` 都有（`InputRenderable` 就是为这一件事的）。所以这一区自己只接**它还管不了的键**：
 * `ctrl+b` · `alt+b` 分叉、`ctrl+r` 换分叉用的角色 —— 提交的语境都在这一行。
 *
 * 这三个键都要**拿走**（`useKeys` 返回 `true`）：`ctrl+b` / `alt+b` 在输入框自带的键位里是
 * "光标左移 / 左移一个词"（opentui 的默认键位表），不拿走就会一次按键两件事都发生。
 *
 * **焦点一直在它身上**：打字是"焦点里的那个可编辑件"的事，而这一屏只有这一个文字入口 ——
 * 焦点被别的东西拿走（鼠标点一下别处就会）之后就再也打不进字，屏幕上看不出为什么。
 * 所以这里盯着"焦点换了谁"，一发现不在自己身上就抢回来。
 *
 * 写账失败时**草稿不清**：那句话还在输入框里，不用重打一遍（所以两个回调回的是"账写成了没有"）。
 *
 * 变因：这一区接哪些键（除编辑键之外的那些）、它的本地状态。
 */
import type { NodeId } from "@meristem/atree";
import { CliRenderEvents } from "@opentui/core";
import type { InputRenderable } from "@opentui/core";
import { useRenderer } from "@opentui/react";
import type { RoleId } from "@meristem/roles";
import { useKeys } from "@meristem/tui";
import { memo, useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { NO_CHOICE, useForkRole } from "../hooks/fork-role.ts";
import { useSession } from "../providers/session.tsx";

export interface InputRegionProps {
  /** 投给哪条线（`null` = 人还没进过任何一条线）。 */
  readonly target: NodeId | null;
  /** 说话；返回"账写成了没有"（成了才清输入框）。 */
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
}: InputRegionProps): ReactNode {
  const { store, roles } = useSession();
  const role = useForkRole(roles);
  const input = useRef<InputRenderable>(null);
  const renderer = useRenderer();

  // 焦点换了谁就把它抢回来（`focus()` 本来就幂等：已经在自己身上时什么都不做）。
  useEffect(() => {
    const again = (): void => input.current?.focus();
    renderer.on(CliRenderEvents.FOCUSED_RENDERABLE, again);
    return () => {
      renderer.off(CliRenderEvents.FOCUSED_RENDERABLE, again);
    };
  }, [renderer]);

  useKeys((key) => {
    switch (key) {
      case "ctrl+b":
        void branch("inherit");
        return true;
      case "alt+b":
        void branch("summarize");
        return true;
      case "ctrl+r": {
        const next = role.cycle();
        if (next !== null) onNotice(`分叉用的角色：${next.title}（${next.id}）`);
        return true;
      }
      default:
        return false;
    }
  });

  /** 说话：草稿就是输入框里那份（写账不成就留着，不用重打）。 */
  async function submit(): Promise<void> {
    const text = input.current?.value ?? "";
    if (text.trim() === "") return;
    const chosen = role.current;
    if (chosen === null) {
      onNotice(NO_CHOICE);
      return;
    }
    if (await onSend(target, text, chosen.id)) clear();
  }

  async function branch(mode: "inherit" | "summarize"): Promise<void> {
    const parent = target ?? store.root();
    if (parent === null) return;
    const chosen = role.current;
    if (chosen === null) {
      onNotice(NO_CHOICE);
      return;
    }
    const text = input.current?.value ?? "";
    if (mode === "summarize" && text.trim() === "") {
      onNotice("总结分叉要有那句新话：它决定新线从父线历史里抽哪一份底");
      return;
    }
    if (await onFork(parent, mode, text, chosen.id)) clear();
  }

  /** 清输入框：只在账写成了的时候。 */
  function clear(): void {
    if (input.current !== null) input.current.value = "";
  }

  return <input ref={input} focused width="100%" onSubmit={() => void submit()} />;
});
