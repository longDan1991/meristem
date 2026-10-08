/**
 * 键行右端的"这会儿能按什么"（P0 §7 规则 7：能用的键只有这一个出口）。
 *
 * **它是问出来的，不是列出来的**：表（一份 yaml 建的 `Commands`）里有 `hint` 的命令里，挑
 * **有接的人**的那些（问总线）。而"有接的人"正是"按下去真的会动"的同一个判据 —— 所以这里写不出
 * 一个按了没反应的键（档与侧边只在主屏上写、`esc` 只在真有可收的层时写、走位只在眼前真有名单时写）。
 *
 * 换屏的那七条不写在这儿（走 `/` 名单 —— 那里有全名与一句话），否则会把左端的"我在哪条线"挤没。
 *
 * **最多占给定的格数**（`budget` 由调用方按"左端要留多少"算出来）：左端被挤没了比少写两个键更坏。
 * 放不下的部分掐掉并补 `…`；一条都放不下也说一声"还有"，不是空白。
 *
 * 变因：那一行右端的键提示怎么算。
 */
import { stringWidth } from "bun";
import type { CommandBus, Commands } from "@meristem/tui";

export function keyHints(table: Commands, bus: CommandBus, budget: number): string {
  const all = table.all
    .filter((command) => command.hint !== null && command.keys.length > 0 && bus.live(command.id))
    .map((command) => `${command.keys[0]?.key ?? ""} ${command.hint ?? ""}`);
  const shown: string[] = [];
  for (const hint of all) {
    if (stringWidth([...shown, hint].join(" · ")) > budget) break;
    shown.push(hint);
  }
  if (shown.length === 0) return all.length === 0 ? "" : "…";
  return shown.length === all.length ? shown.join(" · ") : `${shown.join(" · ")} · …`;
}
