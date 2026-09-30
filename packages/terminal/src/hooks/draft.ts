/**
 * 草稿缓冲：文本与光标**一个状态**（只动本地，回车才写账）。
 *
 * **它不是 provider**：写它的是输入行的键，读它的也只有输入行 —— 状态、写者、读者都在那一处，
 * 所以它是个普通 hook，由 `components/input.tsx` 叫一次。
 *
 * 用 `useState` + 函数式更新承载那条约束：**同一拍里连来几个键，各自接在前一个的结果上**
 * （updater 读的是最新值，不是渲染闭包里的那份）——否则"跑个命令"只剩最后一个字，
 * 或者粘贴一整行再回车时那句话被静默吞掉。
 *
 * 变因：草稿的编辑语义（插入 / 删 / 移动光标）。
 */
import { useCallback, useMemo, useState } from "react";

export interface Draft {
  readonly text: string;
  readonly caret: number;
}

export interface DraftOps {
  /** 光标处插入一段字（可打印键）。 */
  insert(text: string): void;
  /** 删光标前（-1）/ 后（1）的一个字符；到边了就不动。 */
  erase(direction: -1 | 1): void;
  /** 光标移动：`home` / `end` 到头，`left` / `right` 走一格。 */
  moveCaret(key: "left" | "right" | "home" | "end"): void;
  /** 清空（写账成功后）。 */
  clear(): void;
}

export interface DraftStore extends Draft, DraftOps {}

/** 空缓冲区（一个常量，免得每次重置都造一个对象）。 */
const EMPTY: Draft = { text: "", caret: 0 };

export function useDraftBuffer(): DraftStore {
  const [buffer, setBuffer] = useState<Draft>(EMPTY);

  const insert = useCallback((text: string) => {
    setBuffer((current) => ({
      text: current.text.slice(0, current.caret) + text + current.text.slice(current.caret),
      caret: current.caret + text.length,
    }));
  }, []);

  const erase = useCallback((direction: -1 | 1) => {
    setBuffer((current) => {
      if (direction === -1) {
        if (current.caret === 0) return current;
        return {
          text: current.text.slice(0, current.caret - 1) + current.text.slice(current.caret),
          caret: current.caret - 1,
        };
      }
      if (current.caret >= current.text.length) return current;
      return {
        text: current.text.slice(0, current.caret) + current.text.slice(current.caret + 1),
        caret: current.caret,
      };
    });
  }, []);

  const moveCaret = useCallback((key: "left" | "right" | "home" | "end") => {
    setBuffer((current) => {
      const caret =
        key === "home"
          ? 0
          : key === "end"
            ? current.text.length
            : Math.min(Math.max(current.caret + (key === "left" ? -1 : 1), 0), current.text.length);
      return { text: current.text, caret };
    });
  }, []);

  const clear = useCallback(() => setBuffer(EMPTY), []);

  return useMemo(
    () => ({ text: buffer.text, caret: buffer.caret, insert, erase, moveCaret, clear }),
    [buffer, insert, erase, moveCaret, clear],
  );
}
