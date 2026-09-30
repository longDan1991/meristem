/**
 * 语义标签 → 通用样式词：颜色映射**只住这一处**（tui 不认识业务标签）。
 *
 * 变因：颜色映射（哪个语义标签画成哪种样式）。
 */
import type { MessageLine, MessageLineStyle } from "@meristem/tui";
import type { Row, RowTag } from "./view.ts";

const STYLE: Record<RowTag, MessageLineStyle> = {
  title: "accent",
  dim: "dim",
  user: "accent",
  model: "plain",
  thought: "dim",
  hand: "dim",
  error: "danger",
};

/** 一个语义行 → 组件要的那一行（`Row` 不带颜色，只带标签）。 */
export function toLine(row: Row): MessageLine {
  return { text: row.text, style: STYLE[row.tag] };
}
