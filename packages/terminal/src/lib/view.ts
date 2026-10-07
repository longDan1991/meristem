/**
 * 看的东西那两个开关的词表与它们的迁移：**内容区的档**（P0 §4）与**侧边的态**（P0 §5）。
 *
 * 为什么在 `lib`：读它们的有三处（店主 `providers/screen.tsx`、主屏的档位切换、侧边与底下那行），
 * 而"下一个是哪一档"是**纯函数**，不该住在任何一个界面里 —— 住在这儿，两旁都拿它算，也只有一份。
 *
 * **档 ② 会被跳过**：树上只有我这一条线时没有"另一条"可盯（P0 §4 规则 1），所以 ①↔③ 直接来回。
 * 这个条件（`others`）由调用方给：只有它知道树上有没有别的线。
 *
 * 变因：档有哪几档、侧边有哪几态、循环与收掉一层怎么走。
 */

/** 内容区的档：① 这段对话 · ② 盯住一条（树的一小段） · ③ 整棵树。 */
export type Tier = 1 | 2 | 3;

/** 侧边：收起（0 列）· 分成两栏（右边一列）· 占满全屏（正文让位）。 */
export type Side = "hidden" | "split" | "full";

/**
 * 内容区换一档（一个键循环三档）。`others` = 树上除了我站着的那条还有别的线
 * —— 没有就跳过档 ②（那时它没有内容可放）。
 */
export function nextTier(current: Tier, others: boolean): Tier {
  if (current === 1) return others ? 2 : 3;
  if (current === 2) return 3;
  return 1;
}

/** `esc` 收掉档这一层：③→②→①；树上只有我这一条线时直接回 ①（档 ② 不存在）。 */
export function unwindTier(current: Tier, others: boolean): Tier {
  return current === 3 && others ? 2 : 1;
}

/** 侧边换一态：收起 → 分成两栏 → 占满全屏 → 收起。 */
export function nextSide(current: Side): Side {
  if (current === "hidden") return "split";
  return current === "split" ? "full" : "hidden";
}

/** `esc` 在侧边占满全屏时收回分成两栏（分栏是并排，不是"眼前这一层"，不收）。 */
export function unwindSide(current: Side): Side {
  return current === "full" ? "split" : current;
}

/** 侧边换一页：绕圈（页数由画侧边的那一处给，页表在 `lib/side.ts`）。 */
export function nextPage(current: number, pages: number): number {
  return pages <= 0 ? 0 : (current + 1) % pages;
}
