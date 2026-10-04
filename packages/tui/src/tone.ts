/**
 * 一处配色。
 *
 * 谁画的都得取这里的颜色 —— 这一份是唯一的事实：散回各处就会出现"这个 dim 比那个 dim 亮一点"，
 * 也就是闪。所以它是对外的（业务那一层画的那些行也从这里取），不是包内的私事。
 *
 * 变因：视觉体系本身的调整（加一个颜色、换个底色）。
 */
export const tone = {
  dim: "#6b7280",
  accent: "#4ea1ff",
  danger: "#e5484d",
  border: "#3f4653",
  selection: "#2f4a70",
  running: "#e0a458",
  status: "#20262f",
} as const;
