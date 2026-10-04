/** @jsxImportSource @opentui/react */
/**
 * 视觉档 · 五区样张 —— **这一屏画成什么样**。
 *
 * 独立产物：不 import 原型那一份，原型也不认识它（两份文件之间没有代码关系）。
 * 原型是**设计对象**：去看它的帧与那份区清单，知道这一屏有哪些东西、各自什么状态、边界在哪，
 * 然后在这里从零写自己的一份 —— 分组、间距、强调怎么摆，由"好看"决定。
 *
 * 目标：**好看**（主次一眼读得出、密度有节奏、状态不靠颜色单独承载），且**在字符格的物理里**成立。
 *
 * 这一份的画法：**行与原型一一对应**（好对照），力气花在层次与颜色上；两处**提议**在下面标了 ——
 * 真组件自带的外观要改，提议落产品代码，不是在这里打补丁。
 *
 * 层次只用三档：基准（终端默认前景）/ 强调（accent、加粗）/ 次要（dim）；
 * 状态另算：在跑 running、失败 danger、选中底色 selection、状态条底色 status（都取自 `tone`）。
 */
import { TextAttributes } from "@opentui/core";
import { StatusBar, tone } from "../../src/index.ts";
import type { ReactNode } from "react";

const BOLD = TextAttributes.BOLD;

function TreeRow({ text, mark, selected = false }: { readonly text: string; readonly mark?: string; readonly selected?: boolean }): ReactNode {
  return (
    <box
      flexDirection="row"
      justifyContent="space-between"
      width="100%"
      backgroundColor={selected ? tone.selection : undefined}
      paddingRight={1}
    >
      <text>{text}</text>
      {mark === undefined ? null : <text fg={mark.startsWith("✗") ? tone.danger : tone.dim}>{mark}</text>}
    </box>
  );
}

function Row({ text, fg }: { readonly text: string; readonly fg?: string }): ReactNode {
  return <text fg={fg}>{text}</text>;
}

export default function FiveRegionsVisual(): ReactNode {
  return (
    <box flexDirection="column" width="100%" height="100%">
      {/* 1 树条带：选中 = 整行底色（真屏的机制）；在跑 = ▶ N；失败 = ✗ + danger（提议，见文件头） */}
      <box flexDirection="column" width="100%">
        <TreeRow text="重写树条带 · architect" />
        <TreeRow text="  分叉窗口 · coder" mark="▶ 1" selected />
        <TreeRow text="    窗口边界 · coder" />
        <TreeRow text="  ▸ 3 条线" />
        <TreeRow text="  整理 DESIGN · writer" mark="✗ 接口失败" />
        <TreeRow text="  作业卡片的边框 · designer" />
      </box>

      {/* 2 消息流：人说的话 accent；模型原话走 markdown（标题 accent 加粗、列表 dim）；
          思考与手的交代 dim（手那条"长得像人的话"也 dim —— 它不是人说的）；失败 danger + ✗ */}
      <box flexDirection="column" width="100%">
        <Row fg={tone.dim} text="先看窗口是不是纯函数：输入只有 rows 与 size，输出永远同一屏……" />
        <Row fg={tone.accent} text="## 折的是什么" />
        <Row text="展开的集合：选中路径 + 直接子节点 + 有活的线" />
        <Row fg={tone.dim} text="· 其余每个最大可折子树占一行" />
        <Row fg={tone.dim} text={'▸ bash {"command":"bun test --watch","timeout":300}'} />
        <Row fg={tone.dim} text="作业 #7f3a（bash）还在跑：已 3.4s，吐了 128 字" />
        <Row fg={tone.dim} text="作业 #7f3a（bash）：退出码 0 · 25 pass / 0 fail / 6 files" />
        <Row fg={tone.dim} text="接着看窗口这块要不要做成参数" />
      </box>

      {/* 3 实时区：正在吐的思考 dim、缩进 1；手卡片一个边框，名字 accent 加粗、参数 dim、
          时长 running、输出原文照铺（不裁剪不折叠，长的靠外面的滚动盒） */}
      <box flexDirection="column" width="100%" paddingX={1}>
        <text fg={tone.dim}>窗口在选中行周围取 size 行：越界就往回收，两端夹住……</text>
      </box>
      <box border borderStyle="single" borderColor={tone.border} flexDirection="column" paddingX={1}>
        <box flexDirection="row" gap={1}>
          <text fg={tone.accent} attributes={BOLD}>
            bash
          </text>
          <text fg={tone.dim}>{'{"command":"bun test --watch"}'}</text>
          <text fg={tone.running}>已跑 3.4s</text>
        </box>
        <text>25 pass</text>
        <text>0 fail</text>
        <text>Ran 25 tests across 6 files. [412.00ms]</text>
      </box>

      {/* 弹簧：把下面两行压到底 */}
      <box style={{ flexGrow: 1 }} />

      {/* 4 输入行：一屏唯一的文字入口；草稿还在（上一句写账失败，所以没清） */}
      <box width="100%">
        <text>把树条带也换成流式渲染</text>
      </box>

      {/* 5 状态条：永远一行、整屏最底。**借真组件**（`StatusBar`）—— 两端对齐 + 掐尾巴补 `…`
          是它的逻辑，手写一遍就会在放不下时把两端撞在一起；要改它的画法（底色 / 右端 dim / 掐哪头）
          就是改组件或 `tone`，落在产品代码里，不是在这里换一种写法 */}
      <StatusBar
        left="分叉窗口 · coder · …/runs/42 · 在跑 1"
        right="↑12.3k ↓4.1k（思考 2.0k / 缓存 8.0k）  enter 说话 · ctrl+b 分叉 · tab 作业 · esc 取消 · ctrl+c 退出"
      />
    </box>
  );
}
