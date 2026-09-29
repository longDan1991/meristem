/**
 * 模型给的路径 → 真正去读写的路径：**绝对路径照用，相对路径落在这条线的输出根下**。
 *
 * 三只手（`read` / `write` / `bash` 的 `cwd`）共用这一份，不各写一遍。
 *
 * 变因：路径语义（相对谁）。
 */
import { isAbsolute, normalize } from "node:path";

export function resolvePath(outputRoot: string, path: string): string {
  return isAbsolute(path) ? normalize(path) : normalize(`${outputRoot}/${path}`);
}
