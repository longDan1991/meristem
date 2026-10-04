/**
 * 行的词表：语义标签（`RowTag`）、一行的形状（`RowKind`）、一行（`Row`）、折叠记号（`FOLD`）、
 * 一段字怎么变成一行 / 一整段（`split` / `asBlock`）。
 *
 * 消息流与实时区按同一份词画行（一个标签一种颜色），树条带折起来的子树与消息流里一手的过程的
 * 头行共用同一个折叠记号。词表只有一份，改这里一起动。
 *
 * 变因：一行的语义（有哪些标签、什么形状、折叠记号怎么写、一段字怎么变成行）。
 */

/** 行的语义标签：只说"这是什么行"，颜色由 style 定。 */
export type RowTag = "title" | "dim" | "user" | "model" | "thought" | "hand" | "error";

/**
 * 一行的形状（决定**谁画**）：
 *   · `line` —— 一行文字，按显示格折行就完了；
 *   · `markdown` —— 一整段模型原话，**不许拆行**：标题 / 列表 / 代码围栏要连成一段才认得出来，
 *     整段交给 opentui 的 markdown 渲染件。
 */
export type RowKind = "line" | "markdown";

export interface Row {
  readonly text: string;
  readonly tag: RowTag;
  readonly kind: RowKind;
  /** 这一段还在吐（markdown 的半截文档要按"还没写完"解析）。只有 `markdown` 用得上。 */
  readonly live?: boolean;
}

/** 折叠记号：折起来的子树、一手的过程的头行、收起的思考都用它。 */
export const FOLD = "▸ ";

/** 一段字按行拆成若干个**文字行**（空串不铺）。 */
export function split(text: string, tag: RowTag): readonly Row[] {
  return text === "" ? [] : text.split("\n").map((line) => ({ text: line, tag, kind: "line" }));
}

/** 一段字当成**一整段** markdown（空串不铺）：模型的原话。 */
export function asBlock(text: string, live: boolean): readonly Row[] {
  return text === "" ? [] : [{ text, tag: "model", kind: "markdown", live }];
}
