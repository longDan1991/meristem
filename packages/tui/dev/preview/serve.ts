#!/usr/bin/env bun
/**
 * 设计预览服务：把一帧放在浏览器里看 —— **xterm.js 当那面屏幕**。
 *
 * 为什么是 xterm.js 而不是自己画格子：宽字符、折行、SGR 属性、光标、主题都是它的活，而它正是
 * 这一行里成熟的那件东西（§5：不重复造轮子）。自己画格子会在"一个汉字占几格"上立刻说谎。
 *
 * 为什么帧由**子进程**算：mock 是热改的，同进程 import 会吃到模块缓存 —— 屏幕上停着上一版、
 * 又看不出哪里不对。子进程每次从零开始，顺带把 mock 里的炸隔在服务之外（服务只管显示）。
 *
 * 为什么改文件就自己刷新：设计是"改一下、看一眼"的循环，人只该做前面那半。
 *
 * 用法：bun run packages/tui/dev/preview/serve.ts <mock.tsx> [--cols 100] [--rows 40] [--port 4173]
 */
import { watch } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

interface Frame {
  readonly cols: number;
  readonly rows: number;
  readonly ansi: string;
  readonly text: string;
}

/** 屏幕上的东西：一帧 + 这一帧有没有问题（有错时保住上一帧，把错挂在旁边，不假装画好了）。 */
interface Shown {
  readonly frame: Frame;
  readonly failure: string | null;
}

function usage(): never {
  console.error("用法：bun run packages/tui/dev/preview/serve.ts <mock.tsx> [--cols 100] [--rows 40] [--port 4173]");
  process.exit(2);
}

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    cols: { type: "string" },
    rows: { type: "string" },
    port: { type: "string", default: "4173" },
  },
  allowPositionals: true,
});

const mock = positionals[0] ?? usage();

const HERE = import.meta.dir;
const FRAME_CLI = path.join(HERE, "frame.ts");
const PAYLOAD = path.join(tmpdir(), `meristem-design-preview-${process.pid}.json`);
const XTERM = path.dirname(fileURLToPath(import.meta.resolve("@xterm/xterm/package.json")));

/** 帧走**文件**回传：mock 里一句 `console.log` 就会把 stdout 上的 JSON 冲烂，而调试打印是人会干的事。 */
async function renderMock(): Promise<{ ok: true; frame: Frame } | { ok: false; failure: string }> {
  const args = [process.execPath, FRAME_CLI, mock, "--out", PAYLOAD];
  if (values.cols !== undefined) args.push("--cols", values.cols);
  if (values.rows !== undefined) args.push("--rows", values.rows);
  const proc = Bun.spawn(args, { stdout: "inherit", stderr: "pipe" });
  const failure = await new Response(proc.stderr).text();
  const code = await proc.exited;
  if (code !== 0) return { ok: false, failure: failure.trim() === "" ? `渲染失败（退出码 ${code}）` : failure.trim() };
  return { ok: true, frame: JSON.parse(await Bun.file(PAYLOAD).text()) as Frame };
}

let shown: Shown;
const listeners = new Set<ReadableStreamDefaultController<string>>();

const first = await renderMock();
if (!first.ok) {
  console.error(first.failure);
  process.exit(1);
}
shown = { frame: first.frame, failure: null };

async function refresh(): Promise<void> {
  const next = await renderMock();
  if (!next.ok) {
    console.error(next.failure.split("\n")[0]);
    if (shown.failure === null) {
      shown = { frame: shown.frame, failure: next.failure };
      notify();
    }
    return;
  }
  shown = { frame: next.frame, failure: null };
  console.log(`已更新 ${next.frame.cols}×${next.frame.rows}`);
  notify();
}

function notify(): void {
  for (const listener of listeners) listener.enqueue("data: update\n\n");
}

// 防抖：编辑器写一个文件是好几次系统调用，每一次都重渲纯属浪费（渲染是子进程，不便宜）。
let pending: Timer | undefined;
const base = path.basename(mock);
watch(path.dirname(path.resolve(mock)), (_event, filename) => {
  if (filename !== null && filename !== base) return;
  clearTimeout(pending);
  pending = setTimeout(() => {
    pending = undefined;
    void refresh();
  }, 80);
});

Bun.serve({
  hostname: "127.0.0.1",
  port: Number(values.port),
  fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/") return new Response(Bun.file(path.join(HERE, "index.html")));
    if (url.pathname === "/frame") return Response.json(shown, { headers: { "cache-control": "no-store" } });
    if (url.pathname === "/vendor/xterm.js") return new Response(Bun.file(path.join(XTERM, "lib/xterm.js")));
    if (url.pathname === "/vendor/xterm.css") return new Response(Bun.file(path.join(XTERM, "css/xterm.css")));
    if (url.pathname === "/events") {
      let held: ReadableStreamDefaultController<string> | null = null;
      const stream = new ReadableStream<string>({
        start(controller) {
          held = controller;
          listeners.add(controller);
          // 断线重连的间隔：服务活着，浏览器自己会接回来。
          controller.enqueue("retry: 500\n\n");
        },
        cancel() {
          if (held !== null) listeners.delete(held);
        },
      });
      return new Response(stream, { headers: { "content-type": "text/event-stream", "cache-control": "no-store" } });
    }
    return new Response("not found", { status: 404 });
  },
});

console.log(`预览：http://127.0.0.1:${values.port}/   （改 ${mock} 即刷新）`);
