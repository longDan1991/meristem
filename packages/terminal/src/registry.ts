/**
 * 本应用的**命令面**：随代码发布的那张表在哪、它的 id 允许用哪几个作用面。
 *
 * 为什么单独一份：命令模块（`@meristem/tui` 的 `command/`）不认识 `screen` / `turn` / `view` 这些词 ——
 * 它们是**这一屏自己的词**（拿它们分组命令、决定谁接）。所以词表与文件位置由应用声明，装配时交给它
 * 卡住 id 的第一段（写错一个作用面、或表找不到，都在装载时当场炸）。
 *
 * 分组怎么显示（哪一组叫什么、哪几层的命令排在一起）是画法，住 `screens/keys.tsx` —— 不在这一份里。
 *
 * 变因：这一张表的文件位置与作用面词表（改词表就是改这一份）。
 */
import { join } from "node:path";
import type { Layer } from "@meristem/tui";

/** 表在哪：与代码同生共死（不是部署配置），所以按模块目录定位（照 roles 的 `registry/`）。 */
export const COMMANDS_PATH = join(import.meta.dir, "..", "registry", "commands.yaml");

/**
 * 作用面（id 的第一段）：
 *   · `screen` —— 换屏（路由那一层；第二段就是屏名）；
 *   · `app` —— 整个应用（收掉一层 / 退出）；
 *   · `turn` —— 我站着的这条线（说话 / 分叉 / 收手 / 重试）；
 *   · `view` —— 看的东西（档 / 侧边 / 折叠）；
 *   · `list` —— 眼前那份名单（走位）。
 */
export const LAYERS: readonly Layer[] = ["screen", "app", "turn", "view", "list"];
