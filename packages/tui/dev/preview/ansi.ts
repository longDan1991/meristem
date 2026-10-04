/**
 * 一帧 → 两种投影：**带颜色的 ANSI**（真终端 / xterm.js 都能吃）与**纯文本**（wireframe）。
 *
 * 为什么要有 wireframe 这一档：原型那一步的判据是"结构对不对"，颜色在场人就会去评颜色，
 * 注意力当场跑偏。同一个查看器、同一帧，去掉颜色就是另一个问题。
 *
 * 颜色是**逐段**的（`fg` / `bg` / 属性位），不是逐行的：状态条的底色、选中行的反底、一个词加粗，
 * 都是格子级的事实，按行画就会丢。`null` 表示这一端用终端默认色 —— 也**不发**那一端的码，
 * 发了就把"终端自己的底色"这一层压掉了。
 *
 * 变因：一帧怎么变成一段可显示的字（颜色与属性的编码、wireframe 的取舍）。
 */
import { Attributes } from "./render.ts";
import type { Frame, Span } from "./render.ts";

/** 属性位 → ANSI SGR 码（一格里可能同时有几位）。 */
const SGR_BY_ATTRIBUTE: ReadonlyArray<readonly [bit: number, code: number]> = [
  [Attributes.BOLD, 1],
  [Attributes.DIM, 2],
  [Attributes.ITALIC, 3],
  [Attributes.UNDERLINE, 4],
  [Attributes.BLINK, 5],
  [Attributes.INVERSE, 7],
  [Attributes.STRIKETHROUGH, 9],
];

/** `#rrggbb` → `r;g;b`（ANSI 的真彩色是三段十进制，这一步只在这一处做）。 */
function sgrChannels(hex: string): string {
  return `${Number.parseInt(hex.slice(1, 3), 16)};${Number.parseInt(hex.slice(3, 5), 16)};${Number.parseInt(hex.slice(5, 7), 16)}`;
}

function sgrOf(span: Span): string {
  const codes = ["0"];
  if (span.fg !== null) codes.push(`38;2;${sgrChannels(span.fg)}`);
  if (span.bg !== null) codes.push(`48;2;${sgrChannels(span.bg)}`);
  for (const [bit, code] of SGR_BY_ATTRIBUTE) if ((span.attributes & bit) !== 0) codes.push(String(code));
  return `\u001b[${codes.join(";")}m`;
}

/**
 * 带颜色的整帧：行间用 `\r\n`（LF 只下移不回列，xterm 与真终端都按这个语义）。
 * **末尾不发换行**：帧就是 rows 行，多一个换行会把它推到下一行 —— 在只有 rows 行的屏幕上
 * 那一下就是滚动，第一行被挤出去（实测 xterm.js 里正是这么丢的）。
 */
export function toAnsi(frame: Frame): string {
  const lines = frame.lines.map((line) => line.map((span) => `${sgrOf(span)}${span.text}`).join("") + "\u001b[0m");
  return lines.join("\r\n");
}

/** 没有颜色的一帧：只有字与空格，行尾空格去掉（它不承载结构，只会在会话里变成噪音）。 */
export function toText(frame: Frame): string {
  return frame.lines.map((line) => line.map((span) => span.text).join("").replace(/\s+$/, "")).join("\n");
}
