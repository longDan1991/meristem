/**
 * 组件：**只吃 props**。
 *
 * 这里没有任何 `import` 别的包 —— 传进来的是字符串数组与几个回调，所以别的 agent 项目
 * 也能直接用。差分渲染与键解码是它们共同的底座（屏幕只归这一个渲染器）。
 *
 * 布局策略**不在这里**：五区怎么排、哪些行该折，是业务那一层的事。
 *
 * 变因：组件自己的实现（怎么画、怎么键控、怎么差分）。
 */
import type { ReactElement, ReactNode } from "react";

/** 平铺的消息流（本包不做折叠判断：给什么画什么）。 */
export interface MessageStreamProps {
  readonly rows: readonly string[];
  /** 贴住底部（新行进来时滚到最新）。 */
  readonly follow?: boolean;
}

/** 思考行：一整段可收可展。 */
export interface ThoughtLineProps {
  readonly rows: readonly string[];
  readonly open?: boolean;
}

/**
 * 手卡片的**视觉态**：在跑 / 已结束。失败不在这里 —— 我们不分类失败（它是交代里的一段文本，
 * DESIGN §9.3），所以卡片按"已结束"画，字里看得出是怎么回事。
 */
export type HandState = "running" | "done";

/** 一只手的卡片：名字 + 参数 + 输出 + 状态。 */
export interface HandCardProps {
  readonly name: string;
  readonly args?: string;
  readonly output?: readonly string[];
  readonly state: HandState;
  readonly secs?: number;
}

export interface InputBoxProps {
  readonly value: string;
  readonly disabled?: boolean;
  readonly placeholder?: string;
}

/** 树条带：每条线一行（文本由业务给，本包不管血缘）。 */
export interface TreeStripItem {
  readonly id: string;
  readonly text: string;
  readonly selected: boolean;
  /** 状态标记（在动 / 等人 / 休息 / 出错），由业务算好。 */
  readonly mark?: string;
}

export interface TreeStripProps {
  readonly items: readonly TreeStripItem[];
  readonly offset?: number;
}

export interface StatusBarProps {
  readonly left?: string;
  readonly right?: string;
}

/** 一整屏的外壳：负责接管终端、差分重画、还原终端。 */
export interface FrameProps {
  readonly children: ReactNode;
  readonly onKey?: (key: string) => void;
}

export declare function MessageStream(props: MessageStreamProps): ReactElement;
export declare function ThoughtLine(props: ThoughtLineProps): ReactElement;
export declare function HandCard(props: HandCardProps): ReactElement;
export declare function InputBox(props: InputBoxProps): ReactElement;
export declare function TreeStrip(props: TreeStripProps): ReactElement;
export declare function StatusBar(props: StatusBarProps): ReactElement;
export declare function Frame(props: FrameProps): ReactElement;
