/**
 * 一处配色。
 *
 * 组件只吃 props（业务标签不进这个包），所以"什么样式词画成什么颜色"的决定权只能落在包内 ——
 * 这一份是唯一的事实：散回各组件就会出现"这个 dim 比那个 dim 亮一点"，也就是闪。
 *
 * 变因：视觉体系本身的调整（加一个通用样式词、换个底色）。
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
