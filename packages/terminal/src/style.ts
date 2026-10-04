/**
 * 画一行要的两样东西：**语义标签 → 颜色**，以及**模型那段 markdown 的语法配色** ——
 * 都在这一处（tui 不认识业务标签，也不认识 markdown）。
 *
 * 模型的原话不在这里画：它整段交给 opentui 的 markdown 渲染件（`<markdown>`），
 * 这里只给它一份配色（标题 / 强调 / 行内代码 / 引用 / 列表 / 链接各是什么颜色）。
 * 配色跟 `tone` 是同一份事实：散开就会出现"这个强调比那个强调亮一点"。
 *
 * 变因：颜色映射（哪个语义标签、哪个 markdown 记号画成什么颜色）。
 */
import { SyntaxStyle } from "@opentui/core";
import { tone } from "@meristem/tui";
import type { RowTag } from "./lib/rows.ts";

/** 一个语义行画成什么颜色（`undefined` = 终端的默认前景色）。 */
export const colorByTag: Readonly<Record<RowTag, string | undefined>> = {
  title: tone.accent,
  dim: tone.dim,
  user: tone.accent,
  model: undefined,
  thought: tone.dim,
  hand: tone.dim,
  error: tone.danger,
};

/**
 * 模型那段 markdown 的语法配色。没列出来的记号（含代码围栏里的 token）走 `default` ——
 * 就是"不给覆盖"（正文用基准前景色），不去猜没配过的语言。
 *
 * 名字按 markdown 渲染件查表的方式给：它先按整段名字（`markup.link.label`）查，查不到就退到
 * 第一个点之前（`markup.link`），再查不到就是 `default`。
 */
export const syntaxStyle = SyntaxStyle.fromStyles({
  default: {},
  "markup.heading": { fg: tone.accent, bold: true },
  "markup.strong": { bold: true },
  "markup.italic": { italic: true },
  "markup.strikethrough": { dim: true },
  "markup.raw": { fg: tone.accent },
  "markup.quote": { fg: tone.dim },
  "markup.list": { fg: tone.dim },
  "markup.link": { fg: tone.accent },
  "markup.link.url": { fg: tone.dim },
});
