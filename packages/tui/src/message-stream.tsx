/** @jsxImportSource @opentui/react */
/**
 * 消息流：一行一条，直接铺开。
 *
 * **折行自己做**：引擎的换行只认带空格的西文（中日韩宽字符它不折，直接溢出行外），
 * 而"限制必须看得见"是硬要求 —— 所以这里按格宽把太长的行折成多行，一个字都不丢。
 * 折行的格数取屏幕宽度（这条流本来就是屏幕级的带子；接口里没有宽度字段）。
 *
 * 贴底与"往回看 N 行"都不用测量高度：视口是个裁剪盒子，靠对齐与一条相对位移就够
 * （`flex-end` 把内容压在底边、超出上边裁掉；`offset` 把内容整体往下挪几行）。
 * 这样新行进来时不用等排版也知道该停在哪儿 —— 也就没有"滚到上一帧的末尾"这种错。
 *
 * 变因：消息行的画法与滚动语义（贴底 / 回看）。
 */
import { stringWidth } from "bun";
import { useTerminalDimensions } from "@opentui/react";
import { tone } from "./tone.ts";
import type { ReactNode } from "react";

/** 一行消息：文本 + 一个**通用**的样式词。业务标签（user / model / …）不进这个包。 */
export type MessageLineStyle = "plain" | "dim" | "accent" | "danger";

export interface MessageLine {
  readonly text: string;
  readonly style?: MessageLineStyle;
}

export interface MessageStreamProps {
  readonly rows: readonly MessageLine[];
  /** 贴住底部：新行进来滚到最新（缺省 true）。`offset > 0` 时它无效。 */
  readonly follow?: boolean;
  /**
   * 从末尾往回数几个**显示行**（0 / 缺省 = 贴底看最新）；被折过的长行按它占的显示行数算。
   * 调用方用它做键盘滚动，不动就一直是 0。
   */
  readonly offset?: number;
}

function lineColor(style: MessageLineStyle | undefined): string | undefined {
  switch (style ?? "plain") {
    case "plain":
      return undefined;
    case "dim":
      return tone.dim;
    case "accent":
      return tone.accent;
    case "danger":
      return tone.danger;
  }
}

/**
 * 按格宽折行：放不下就接着下一行，**不丢字、不静默裁**（`budget <= 0` 时原样返回）。
 * 双宽字的第二格不许正好落在最后一格 —— 那种情况下引擎会把下一行画串（见 StatusBar 的说明）。
 */
function wrapCells(text: string, budget: number): string[] {
  if (budget <= 0) return [text];
  const out: string[] = [];
  let line = "";
  for (const ch of text) {
    const candidate = line + ch;
    const cells = stringWidth(candidate);
    if (cells > budget || (cells === budget && stringWidth(ch) > 1)) {
      out.push(line);
      line = ch;
      continue;
    }
    line = candidate;
  }
  out.push(line);
  return out;
}

export function MessageStream({ rows, follow = true, offset = 0 }: MessageStreamProps): ReactNode {
  const cols = useTerminalDimensions().width;
  const parked = offset > 0;
  const align = parked || follow ? "flex-end" : "flex-start";
  const display: MessageLine[] = [];
  for (const row of rows) {
    for (const text of wrapCells(row.text, cols)) display.push({ text, style: row.style });
  }
  return (
    <box flexGrow={1} flexDirection="column" overflow="hidden" justifyContent={align}>
      {/* position=relative + top：停住回看时，把内容整体往下挪 offset 行（不动布局，只挪画面）。 */}
      <box flexDirection="column" flexShrink={0} position="relative" top={parked ? offset : 0}>
        {display.map((row, index) => (
          <text key={index} fg={lineColor(row.style)} wrapMode="none">
            {row.text}
          </text>
        ))}
      </box>
    </box>
  );
}
