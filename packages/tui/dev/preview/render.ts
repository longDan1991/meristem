/**
 * 一棵 React 树 → **一帧**（渲染器自己算出来的格子）。
 *
 * 为什么走**真渲染器**、再拿一个终端模拟器读回来，而不用测试渲染器的 `captureCharFrame()`：
 * 后者在 100 列以上会把末行的文字丢掉（实测 100×40 的样张 10/10 丢，而真渲染器画的是对的）。
 * 设计要看的就是"真渲染器会画出什么"，拿一条测试路径的帧当依据，等于照着错的屏幕改设计。
 *
 * 为什么还要模拟器：真渲染器吐的是**增量差分**（光标定位 + 属性 + 字符），不是一张静态格子。
 * 把这段字节重放进一个终端模拟器（`@xterm/headless`，与浏览器里那面屏幕同源），才得到
 * "这一屏现在长什么样"。这是成熟轮子，不自己写（§5）—— 宽字符占几格、折行到哪、属性怎么叠，
 * 都由它兜住，而这些恰恰是设计要定死的东西。
 *
 * 变因：怎么把一棵树渲染成一帧（渲染器与模拟器的取用、等稳、收尾）。
 */
import { Writable } from "node:stream";
import type { IBufferCell, IBufferLine } from "@xterm/headless";
import { Terminal } from "@xterm/headless";
import { CliRenderEvents, createCliRenderer } from "@opentui/core";
import type { CliRenderer } from "@opentui/core";
import { createRoot, flushSync } from "@opentui/react";
import type { ReactNode } from "react";

export interface FrameSize {
  readonly cols: number;
  readonly rows: number;
}

/** 一格里能有的样子（SGR 的那几个开关）。这是**帧自己的词表**，与渲染引擎的属性位是两回事。 */
export const Attributes = {
  BOLD: 1,
  DIM: 2,
  ITALIC: 4,
  UNDERLINE: 8,
  BLINK: 16,
  INVERSE: 32,
  STRIKETHROUGH: 64,
} as const;

/** 一段同样式的字。`null` = 这一端用终端自己的默认色（不是"黑色"，两回事）。 */
export interface Span {
  readonly text: string;
  readonly fg: string | null;
  readonly bg: string | null;
  readonly attributes: number;
}

export interface Frame {
  readonly cols: number;
  readonly rows: number;
  readonly lines: readonly (readonly Span[])[];
}

/** 等稳的兜底上限：真渲染器一帧几十毫秒就画完，等不到就说明它没在画（下面会当场报错）。 */
const SETTLE_TIMEOUT_MS = 2000;

/** 连着这么多帧没有新字节，才算这一屏画完了。 */
const QUIET_FRAMES = 2;

/** 渲染器要往哪儿写：收进内存，攒成一段 ANSI 差分。 */
class MemorySink {
  readonly chunks: Buffer[] = [];

  get stream(): NodeJS.WriteStream {
    const sink = new Writable({
      write: (chunk: Buffer, _encoding, done) => {
        this.chunks.push(chunk);
        done();
      },
    });
    return sink as unknown as NodeJS.WriteStream;
  }

  get bytes(): number {
    return this.chunks.reduce((total, chunk) => total + chunk.length, 0);
  }

  /** 一次解码：按块解会把多字节字符切断。 */
  text(): string {
    return Buffer.concat(this.chunks).toString("utf8");
  }
}

function hex(color: number): string {
  return `#${color.toString(16).padStart(6, "0")}`;
}

/**
 * 一格的颜色。渲染引擎给的是真彩色（真渲染器写出来就是 `38;2;…`），所以这里只认
 * 真彩色与"默认"两种；冒出别的（调色板色）就当场炸 —— 悄悄当成默认色才是真的坏。
 */
function ink(cell: IBufferCell, which: "fg" | "bg"): string | null {
  const isDefault = which === "fg" ? cell.isFgDefault() : cell.isBgDefault();
  if (isDefault) return null;
  const isRgb = which === "fg" ? cell.isFgRGB() : cell.isBgRGB();
  if (!isRgb) throw new Error(`这一格用了${which} = ${which === "fg" ? cell.getFgColor() : cell.getBgColor()} 的调色板色，本工具只认真彩色；先把它换成 #rrggbb`);
  return hex(which === "fg" ? cell.getFgColor() : cell.getBgColor());
}

function attributesOf(cell: IBufferCell): number {
  let bits = 0;
  if (cell.isBold()) bits |= Attributes.BOLD;
  if (cell.isDim()) bits |= Attributes.DIM;
  if (cell.isItalic()) bits |= Attributes.ITALIC;
  if (cell.isUnderline()) bits |= Attributes.UNDERLINE;
  if (cell.isBlink()) bits |= Attributes.BLINK;
  if (cell.isInverse()) bits |= Attributes.INVERSE;
  if (cell.isStrikethrough()) bits |= Attributes.STRIKETHROUGH;
  return bits;
}

/** 一行 → 若干段：同样式的相邻格子并成一段（一段 = 一个 SGR 片段）。 */
function spansOf(line: IBufferLine, cols: number): readonly Span[] {
  const spans: Span[] = [];
  let open: { text: string; fg: string | null; bg: string | null; attributes: number } | null = null;
  for (let x = 0; x < cols; x += 1) {
    const cell = line.getCell(x);
    if (cell === undefined) break;
    // 宽字符的第二格没有自己的字：跳过它，文字已经在上一格里了。
    if (cell.getWidth() === 0) continue;
    const fg = ink(cell, "fg");
    const bg = ink(cell, "bg");
    const attributes = attributesOf(cell);
    const text = cell.getChars() === "" ? " " : cell.getChars();
    if (open !== null && open.fg === fg && open.bg === bg && open.attributes === attributes) {
      open.text += text;
    } else {
      open = { text, fg, bg, attributes };
      spans.push(open);
    }
  }
  return spans;
}

/** 等"连续若干帧没有新字节"：渲染器自己会推帧，推完就静了。 */
async function settle(renderer: CliRenderer, sink: MemorySink): Promise<void> {
  const quiet = Promise.withResolvers<void>();
  let last = -1;
  let streak = 0;
  const onFrame = (): void => {
    const now = sink.bytes;
    if (now > 0 && now === last) {
      streak += 1;
      if (streak >= QUIET_FRAMES) quiet.resolve();
      return;
    }
    streak = 0;
    last = now;
  };
  renderer.on(CliRenderEvents.FRAME, onFrame);
  const timer = setTimeout(quiet.resolve, SETTLE_TIMEOUT_MS);
  try {
    await quiet.promise;
  } finally {
    clearTimeout(timer);
    renderer.off(CliRenderEvents.FRAME, onFrame);
  }
}

/** 把一段 ANSI 差分重放进模拟器，再把这一屏读成格子。 */
async function readGrid(bytes: string, size: FrameSize): Promise<Frame> {
  // `buffer`（读这一屏的格子）在 5.5 里还挂在"提议中"的 API 后面，得显式打开。
  const terminal = new Terminal({ cols: size.cols, rows: size.rows, scrollback: 0, allowProposedApi: true });
  try {
    const replayed = Promise.withResolvers<void>();
    terminal.write(bytes, () => replayed.resolve());
    await replayed.promise;
    const screen = terminal.buffer.active;
    const lines: (readonly Span[])[] = [];
    for (let y = 0; y < size.rows; y += 1) {
      const line = screen.getLine(y);
      lines.push(line === undefined ? [] : spansOf(line, size.cols));
    }
    return { cols: size.cols, rows: size.rows, lines };
  } finally {
    terminal.dispose();
  }
}

/**
 * 画一帧：真渲染器画进内存 → 重放进模拟器 → 读成格子。
 *
 * **必须先 flushSync 再等稳**：没有帧循环推提交时，裸调用不会当场落地；而落地之后还要等它画完
 * —— 拿一张只画了一半的帧当设计依据，比画错还坏（所以宁可等，也不猜）。
 */
export async function renderFrame(node: ReactNode, size: FrameSize): Promise<Frame> {
  const sink = new MemorySink();
  const renderer = await createCliRenderer({
    stdout: sink.stream,
    width: size.cols,
    height: size.rows,
    screenMode: "main-screen",
    consoleMode: "disabled",
  });
  const root = createRoot(renderer);
  try {
    flushSync(() => {
      root.render(node);
    });
    await settle(renderer, sink);
    const bytes = sink.text();
    if (bytes === "") throw new Error("渲染器一个字节都没写出来：这一帧不成立");
    return await readGrid(bytes, size);
  } finally {
    root.unmount();
    renderer.destroy();
  }
}
