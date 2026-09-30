/**
 * 作业机制的边界：两个原语、三条结局、按空间筛、四只手的语义。
 *
 * 这一层不碰模型、不碰网络、不碰账 —— 所以这里全是确定性的断言。
 */
import { afterEach, describe, expect, test, vi } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Hand, HandContext } from "../src/role.ts";
import { background, settled } from "../src/jobs/base.ts";
import { channel } from "../src/jobs/channel.ts";
import { JOB_CANCEL, JOB_LIST, JOB_OUTPUT } from "../src/jobs/hands.ts";
import { all, find, register, running } from "../src/jobs/table.ts";
import { BASH } from "../src/tools/bash.ts";
import { READ } from "../src/tools/read.ts";
import { WRITE } from "../src/tools/write.ts";

const dirs: string[] = [];

/**
 * 等一个"生产者已经交出去、消费者还没取"的条件成立：**只让微任务转**，不等墙上时钟。
 * （底座的泵就是这么转的：push 解开一个已经挂着的 await，续体在下一个微任务里跑。）
 */
async function until(predicate: () => boolean, what: string): Promise<void> {
  for (let tick = 0; tick < 1000; tick += 1) {
    if (predicate()) return;
    await Promise.resolve();
  }
  throw new Error(`等了 1000 个微任务，条件还没成立：${what}`);
}

function workRoot(): string {
  const dir = mkdtempSync(join(tmpdir(), "meristem-jobs-"));
  dirs.push(dir);
  return dir;
}

function hold(space: string, timeout = 30, timeoutArg?: string) {
  const chunks = channel<string>();
  const { promise: done, resolve: land, reject: fail } = Promise.withResolvers<string>();
  let stops = 0;
  const job = background({
    space,
    name: "handmade",
    chunks: chunks.stream,
    done,
    stop: () => {
      stops += 1;
    },
    timeout,
    timeoutArg,
  });
  return { job, chunks, land, fail, stops: () => stops };
}

afterEach(() => {
  vi.useRealTimers();
  // 作业表是模块级的：测完把还在跑的收掉，免得漏到下一个用例（取消 = 摘除 + 交代）。
  for (const job of all()) job.cancel();
  for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe("settled：立刻结束的执行", () => {
  test("文本已经写好 → 返回时就是交代，也不进作业表", async () => {
    const job = settled({ space: "n1", name: "read" }, "文件内容");

    expect(job.report()).toBe("文件内容");
    expect(running("n1")).toEqual([]);
    await job.wait();
    expect(job.report()).toBe("文件内容");
  });

  test("执行失败 → 失败也是交代（换手的话说），不是异常", async () => {
    const job = settled({ space: "n1", name: "read" }, Promise.reject(new Error("ENOENT: 没有这个文件")));

    await job.wait();
    expect(job.report()).toContain("read 失败：ENOENT: 没有这个文件");
    expect(running("n1")).toEqual([]);
  });
});

describe("background：起之后才回来的执行", () => {
  test("起手时就在跑、就能被这条线看见；结束时摘掉、交代落地", async () => {
    const { job, chunks, land, stops } = hold("n1");

    expect(running("n1")).toEqual([job]);
    expect(job.report()).toContain(job.id);
    expect(job.report()).toContain("还在跑");

    chunks.push("hel");
    chunks.push("lo");
    await until(() => job.produced() === 5, "泵取走 hello");
    expect(job.output()).toBe("hello");
    expect(job.produced()).toBe(5);

    chunks.close();
    land("干完了");
    await job.wait();

    expect(job.report()).toBe("干完了");
    expect(running("n1")).toEqual([]);
    expect(stops()).toBe(0);
  });

  test("失败：交代说清是哪一手的失败", async () => {
    const { job, chunks, fail } = hold("n1");

    chunks.close();
    fail(new Error("连不上"));
    await job.wait();

    expect(job.report()).toContain(`作业 #${job.id}（handmade）失败：连不上`);
    expect(running("n1")).toEqual([]);
  });

  test("被别人取消：交代是「被人取消了」，stop 真的被调，重复取消无害", async () => {
    const { job, chunks, stops } = hold("n1");

    chunks.push("一堆输出");
    await until(() => job.produced() === 4, "泵取走取消前那点输出");
    job.cancel();
    job.cancel();
    await job.wait();

    expect(stops()).toBe(1);
    expect(job.report()).toContain("被人取消了");
    expect(job.report()).toContain("到此刻吐了 4 字");
    expect(job.report()).toContain("一堆输出");
    expect(running("n1")).toEqual([]);
  });

  test("超时：交代说得清「跑了多久、被杀、怎么跑更久」，到此刻的输出跟着留下", async () => {
    vi.useFakeTimers();
    const { job, chunks, stops } = hold("n1", 0.05, "timeout");

    chunks.push("跑了一半");
    await until(() => job.produced() === 4, "泵取走跑了一半");
    vi.advanceTimersByTime(50);
    await job.wait();

    expect(stops()).toBe(1);
    expect(job.report()).toContain("跑了 0.05 秒还没结束");
    expect(job.report()).toContain('把 timeout 写大些（0 = 不限）');
    expect(job.report()).toContain("跑了一半");
    expect(running("n1")).toEqual([]);
  });

  test("没有时间参数的手（MCP）：交代说的是兜底值，不含糊", async () => {
    vi.useFakeTimers();
    const chunks = channel<string>();
    const { promise: done } = Promise.withResolvers<string>();
    const job = background({
      space: "n1",
      name: "mcp__x",
      chunks: chunks.stream,
      done,
      stop: () => {},
      timeout: 0.05,
    });

    vi.advanceTimersByTime(50);
    await job.wait();
    expect(job.report()).toContain("这只手没有自己的时间参数，统一按 0.05 秒杀");
  });

  test("输出是原文：底座不裁剪、不折叠（压缩是发送边界的事）", async () => {
    const { job, chunks } = hold("n1");
    const whole = "头".repeat(3000) + "中".repeat(50_000) + "尾".repeat(3000);

    chunks.push(whole);
    chunks.close();
    await until(() => job.produced() === 56_000, "泵取走整块输出");

    expect(job.output()).toBe(whole);
    expect(job.output().length).toBe(56_000);
  });
});

describe("三只共享手按空间筛", () => {
  test("别人的作业不算这条线的：只有这条线自己起的在列", async () => {
    const here = workRoot();
    const hold1 = hold("n1");
    const hold2 = hold("n2");
    const ctx1: HandContext = { outputRoot: here, space: "n1" };

    const list = await JOB_LIST.run({}, ctx1);
    const text = list.report();
    expect(text).toContain(`#${hold1.job.id}`);
    expect(text).not.toContain(`#${hold2.job.id}`);

    const other = await JOB_LIST.run({}, { outputRoot: here, space: "n3" });
    expect(other.report()).toContain("没有还在跑的作业");
  });

  test("job_output 读到原样输出；不认识的 id 说得清它可能已经结束", async () => {
    const root = workRoot();
    const { job, chunks } = hold("n1");
    chunks.push("最新的几行");
    await until(() => job.produced() === 5, "泵取走输出");

    const seen = await JOB_OUTPUT.run({ id: job.id }, { outputRoot: root, space: "n1" });
    expect(seen.report()).toContain("最新的几行");
    expect(seen.report()).toContain("输出（原文，不是最终交代）");

    const missing = await JOB_OUTPUT.run({ id: "nope" }, { outputRoot: root, space: "n1" });
    expect(missing.report()).toContain("没有 #nope 这个还在跑的作业");
  });

  test("job_cancel 停得掉，而且自己也是一次立刻结束的执行", async () => {
    const root = workRoot();
    const { job, stops } = hold("n1");

    const cancelled = await JOB_CANCEL.run({ id: job.id }, { outputRoot: root, space: "n1" });
    expect(stops()).toBe(1);
    expect(cancelled.report()).toContain("已经让");
    expect(cancelled.report()).toContain("停下");
    expect(running("n1")).toEqual([]);

    const again = await JOB_CANCEL.run({ id: job.id }, { outputRoot: root, space: "n1" });
    expect(again.report()).toContain("没有 #" + job.id + " 这个还在跑的作业");
  });

  test("表按空间摘除：登记另一个空间的同名作业互不影响", () => {
    const a = hold("a");
    const b = hold("b");
    register(a.job);
    register(b.job);

    expect(find("a", a.job.id)).toBe(a.job);
    expect(find("a", b.job.id)).toBeNull();
    expect(find("b", b.job.id)).toBe(b.job);
    expect(running("a")).toEqual([a.job]);
  });
});

describe("read：按字节翻页", () => {
  const ctx = (root: string): HandContext => ({ outputRoot: root, space: "n1" });

  test("给出总长、本段范围与下一段 offset", async () => {
    const root = workRoot();
    writeFileSync(join(root, "big.txt"), "a".repeat(30_000));

    const first = await READ.run({ path: "big.txt", limit: 10 }, ctx(root));
    expect(first.report()).toContain("共 30000 字节；本段 0–10");
    expect(first.report()).toContain("还有 29990 字节；下一段：offset=10");

    const last = await READ.run({ path: "big.txt", offset: 29_990 }, ctx(root));
    expect(last.report()).toContain("本段 29990–30000");
    expect(last.report()).toContain("（到这里就完了）");
  });

  test("空文件、越界 offset、没这个文件、二进制都说清楚", async () => {
    const root = workRoot();
    writeFileSync(join(root, "empty.txt"), "");
    writeFileSync(join(root, "bin"), Buffer.from([0x61, 0x00, 0x62]));

    expect((await READ.run({ path: "empty.txt" }, ctx(root))).report()).toContain("（空文件）");
    writeFileSync(join(root, "tiny.txt"), "abc");
    expect((await READ.run({ path: "tiny.txt", offset: 5 }, ctx(root))).report()).toContain("越过结尾");
    expect((await READ.run({ path: "nope.txt" }, ctx(root))).report()).toContain("read 没能读");
    expect((await READ.run({ path: "bin" }, ctx(root))).report()).toContain("二进制文件：共 3 字节");
  });

  test("窗口切在多字节字符中间时不吐半个字", async () => {
    const root = workRoot();
    writeFileSync(join(root, "utf8.txt"), "aéb");

    const sliced = await READ.run({ path: "utf8.txt", limit: 2 }, ctx(root));
    expect(sliced.report()).toContain("本段 0–2");
    expect(sliced.report()).not.toContain("\uFFFD");
    expect(sliced.report()).toContain("下一段：offset=2");
  });
});

describe("write 与 bash：真落盘的那两只手", () => {
  const ctx = (root: string): HandContext => ({ outputRoot: root, space: "n1" });

  test("write 建目录、覆盖写、交代说清写了哪里", async () => {
    const root = workRoot();

    const job = await WRITE.run({ path: "deep/inside/a.txt", content: "你好" }, ctx(root));
    expect(job.report()).toContain("已写");
    expect(job.report()).toContain("2 字");
    expect(readFileSync(join(root, "deep/inside/a.txt"), "utf8")).toBe("你好");
    expect(running("n1")).toEqual([]);
  });

  test("bash 跑完一条命令：输出全量进交代，退出码也写出来", async () => {
    const root = workRoot();

    const ok = await BASH.run({ command: "echo hi; echo 警告 >&2" }, ctx(root));
    await ok.wait();
    expect(ok.report()).toContain("$ echo hi; echo 警告 >&2");
    expect(ok.report()).toContain("hi");
    expect(ok.report()).toContain("警告");
    expect(ok.report()).toContain("exit 0");
    expect(ok.report()).toContain(`cwd=${root}`);

    const bad = await BASH.run({ command: "exit 3" }, ctx(root));
    await bad.wait();
    expect(bad.report()).toContain("（没有输出）");
    expect(bad.report()).toContain("exit 3");
  });

  test("bash 的 cwd 相对这条线的输出根；不写 timeout 用缺省", async () => {
    const root = workRoot();
    const sub = join(root, "线一");
    mkdirSync(sub, { recursive: true });

    const job = await BASH.run({ command: "pwd", cwd: "线一" }, ctx(root));
    await job.wait();
    expect(job.report()).toContain("线一");
  });

  test("bash 的 timeout 写错：交代说明白怎么重来，不是异常", async () => {
    const root = workRoot();

    const job = await BASH.run({ command: "echo hi", timeout: -1 }, ctx(root));
    expect(job.report()).toContain("timeout 要是 ≥ 0 的秒数");
    expect(job.report()).toContain("0 = 不限");
  });

  test("bash 起不来（cwd 不存在）：交代说得清是在哪儿起的", async () => {
    const root = workRoot();

    const job = await BASH.run({ command: "echo hi", cwd: "没有这个目录" }, ctx(root));
    await job.wait();
    expect(job.report()).toContain("没能起这条命令");
    expect(job.report()).toContain(`cwd=${join(root, "没有这个目录")}`);
  });

  test("bash 被取消：无残留，交代是取消", async () => {
    const root = workRoot();

    const job = await BASH.run({ command: "sleep 30" }, ctx(root));
    expect(running("n1")).toEqual([job]);
    job.cancel();
    await job.wait();

    expect(job.report()).toContain("被人取消了");
    expect(running("n1")).toEqual([]);
    const leftover = Bun.spawnSync(["pgrep", "-fl", "sleep 30"]);
    expect(leftover.exitCode).not.toBe(0);
  });
});

/**
 * 手（`Hand`）都长一个样：这一份断言是给"以后新加的手"的最小契约。
 * 它不测具体语义（那些在上面），只测这个形状还在。
 */
test("内置的三只手都有名字 / 描述 / schema 与 snippet", () => {
  for (const hand of [BASH, READ, WRITE] as readonly Hand[]) {
    expect(hand.name.length).toBeGreaterThan(0);
    expect(hand.description.length).toBeGreaterThan(20);
    expect(hand.snippet?.length ?? 0).toBeGreaterThan(0);
    expect(hand.schema["type"]).toBe("object");
  }
});
