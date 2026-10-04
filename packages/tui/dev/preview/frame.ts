#!/usr/bin/env bun
/**
 * 把一份 mock 渲成一帧，吐给外面 —— 这是"看设计"的**唯一出口**（预览服务也调它）。
 *
 * 为什么 mock 必须走动态 import（静态 import 做不到）：设计是热改的，"这一份是哪一个文件"
 * 只能是运行时给的事实（命令行参数），编译期没有这个路径。为什么吐三种形态：真终端吃 ANSI（默认）、
 * 写进会话吃纯文本（`--wireframe`）、预览服务吃文件里的 JSON（`--out <path>`）—— 三种都是同一帧的投影，不各画一份。
 *
 * 用法：bun run packages/tui/dev/preview/frame.ts <mock.tsx> [--cols 100] [--rows 40] [--wireframe] [--out <path>]
 */
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { createElement } from "react";
import type { ComponentType, ReactNode } from "react";
import { toAnsi, toText } from "./ansi.ts";
import { renderFrame } from "./render.ts";
import type { FrameSize } from "./render.ts";

/**
 * mock 的约定：`default` 导出要么是节点，要么是组件（函数）。组件必须**挂成元素**再渲染 ——
 * 直接调用函数等于在 React 之外跑，里面的 hook 会当场炸（"Invalid hook call"）。
 */
function screenOf(mod: { default?: unknown }): ReactNode {
  const screen: unknown = mod.default;
  if (typeof screen === "function") return createElement(screen as ComponentType);
  return screen as ReactNode;
}

function sizeOf(cols: string, rows: string): FrameSize {
  const width = Number(cols);
  const height = Number(rows);
  if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    console.error(`--cols / --rows 要是正整数，收到 cols=${cols} rows=${rows}`);
    process.exit(2);
  }
  return { cols: width, rows: height };
}

function usage(): never {
  console.error(
    "用法：bun run packages/tui/dev/preview/frame.ts <mock.tsx> [--cols 100] [--rows 40] [--wireframe] [--out <path>]",
  );
  process.exit(2);
}

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    cols: { type: "string", default: "100" },
    rows: { type: "string", default: "40" },
    wireframe: { type: "boolean", default: false },
    out: { type: "string" },
  },
  allowPositionals: true,
});

const mock = positionals[0] ?? usage();
const mod = (await import(pathToFileURL(mock).href)) as { default?: unknown };
const frame = await renderFrame(screenOf(mod), sizeOf(values.cols, values.rows));
const payload = JSON.stringify({ cols: frame.cols, rows: frame.rows, ansi: toAnsi(frame), text: toText(frame) });

if (values.out !== undefined) {
  // 帧走文件回传：调用方（预览服务）要的是数据，而 mock 里的调试打印会走 stdout —— 两者不挤同一条管道。
  await Bun.write(values.out, payload);
} else if (values.wireframe) {
  process.stdout.write(`${toText(frame)}\n`);
} else {
  process.stdout.write(toAnsi(frame));
}
