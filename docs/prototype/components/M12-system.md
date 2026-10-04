# 组件 · M12 系统与视觉（系统与视觉层面的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 17 条 · jcode 36 条

## 两家在这一刻的对照（事实）

- omp 17 条 / jcode 36 条；omp 以视觉原语（DynamicBorder/OverlayPanel/PanelRows/form-theme/shimmer/动画）+ HubFrame + 设置项；jcode 以复制/选择/滚动/点击交互（copy badge/选区/滚轮/拖动）+ 系统消息块 + 入场动画为主

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | EditorTopGap | band 形态且上行状态行本帧有内容 | 不占行（塌缩）；否则 1 空行（注：布局占位（塌缩/空行），非用户内容） | —（仅占位 0/1 行） | packages/tui/src/prompt/editor-top-gap.ts:31 |
| omp | 魔法关键字 shimmer | 草稿含注册关键字且位于 prose（非代码/URL）中 | 关键字按时间相位做彩色渐变（注：打字时的彩色渐变动画） | 关键字移除即停 | packages/tui/src/prompt/magic-keywords.ts:110 |
| omp | setTitle | 扩展调用 | 设置终端窗口/标签标题（OSC 0）（注：设置终端窗口/标签标题（OSC 0）） | 下次 setTitle 覆盖 | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:136 / tui/src/terminal.ts:2545 |
| omp | display-preferences | 从不直接上屏 | 全局显示开关（hideToolActivity/readToolResultPreview/showImages/cacheMissMarker/showTokenUsage/showTurnTime）（注：从不直接上屏，全局显示开关常量） | n/a | packages/tui/src/chat/display-preferences.ts:12 |
| omp | OverlayPanel | 内联 overlay（selector/ask/settings/plugin 等） | 圆角框：带标题顶边+│内容│行+底边；PanelDivider=「├─┤」（注：通用 overlay 面板原语（select/ask/settings/plugin 用）） | overlay 关闭；宽<4 截断 | packages/tui/src/chrome/overlay-box.ts:218 |
| omp | PanelRows / topBorder / divider / row / splitRow 等 | 由 overlay 屏组装时（从不单独出现） | 纯字符串行原语：顶/底边框、分隔线、│行│、双栏布局（注：纯字符串行原语） | n/a | packages/tui/src/chrome/overlay-box.ts:22 |
| omp | DynamicBorder | bash/eval 框、转录浏览器上下边框 | 一行 boxRound 横线（按视宽重复）（注：bash/eval 框/浏览器边框行） | 单行；native 描述为空 | packages/tui/src/chrome/dynamic-border.ts:14 |
| omp | selector-helpers | 使全文/选择器屏（历史搜索、tree 等） | 共享滚动列表+滚动条(muted 轨/accent 滑块)、居中窗口、tab 切换、整屏补齐（注：历史搜索/tree 等选择器屏的共享滚动 helper） | n/a | packages/tui/src/chrome/selector-helpers.ts:17 |
| omp | visual-truncate | 从不直接上屏 | 按视觉行从尾部截断文本，返回 visualLines+skippedCount（注：从不直接上屏，视觉截断工具） | n/a | packages/tui/src/chrome/visual-truncate.ts:43 |
| omp | shared.ts (sanitizeStatusText / getTabBarTheme) | overlay 状态文本与标签页渲染时 | 单行化状态文本；标签栏配色（active/inactive/muted/hover）（注：从不直接上屏，状态文本/标签配色） | n/a | packages/tui/src/chrome/shared.ts:9 |
| omp | form-theme | overlay 表单字段 | 配色函数：label 粗体 accent / desc muted / error / hint dim（注：从不直接上屏，表单配色） | n/a | packages/tui/src/chrome/form-theme.ts:5 |
| omp | index.ts | 从不直接上屏 | chrome 桶式 re-export（注：从不直接上屏，桶式 re-export） | n/a | packages/tui/src/chrome/index.ts:1 |
| omp | local-date | 从不直接上屏 | YYYY-MM-DD 与「日期 时:分 ±HH:MM」格式化函数（注：从不直接上屏，日期格式化） | n/a | packages/tui/src/chrome/local-date.ts:2 |
| omp | keybinding-hints | 从不直接上屏 | 生成「dim 键 + muted 描述」提示串（editorKey/interruptKey/appKeyHint 等）（注：从不直接上屏，键提示串生成） | n/a | packages/tui/src/chrome/keybinding-hints.ts:18 |
| omp | HubFrame | 出现在 agents-hub 与 model-hub 内（全屏 split 框架） | 标题边框 + sidebar/body split + divider + footer(chip 条) + bottom；提供 sidebar 滚动、chip 命中范围、宽度测量（注：agents-hub/model-hub 共用的 split 框架原语） | 随宿主面板关闭 | packages/tui/src/overlays/hub-frame.ts:118-203 |
| omp | describeHubFrame/describeHubSidebar/describeHubChips（原生） | 宿主原生渲染时 | overlayCard(标题)+row(sidebar/body)+rule+footer；sidebar 为 list(item 带 icon/annotation)，footer 为 tabs（注：原生渲染 helper） | 随宿主 | packages/tui/src/overlays/hub-frame.ts:60-136 |
| omp | Fireworks 面板 | 自动触发，每个交互会话至多一个 modal | 终端顶部 33% 高的粒子 canvas(星星+多组烟花+横幅，34 帧循环，85ms/帧)；原生为顶部玻璃 sheet：✦✧ 彩字 + shimmer 标题 + 副标题 + Close（注：自动触发的烟花庆祝动画） | Esc 或 Close 关闭 | packages/tui/src/overlays/codex-reset-fireworks.ts:18-19,91-99,279-400 |
| jcode | 复制选区状态 | copy_selection_status 有值 | `{pane} selection · {chars}[·{lines}] · Enter/Y copy · Esc exit` | 退出复制模式 | crates/jcode-tui/src/tui/ui_input.rs:1662-1690 |
| jcode | learn hint（学键提示） | learn_hint 被设置后 8s 内 | 紫色粗体提示文本 | 8s 后消失 | crates/jcode-tui/src/tui/ui_input.rs:1757-1766; app/tui_state.rs:993-1002 |
| jcode | hotkey feedback | 按下罕见/未绑定组合后 5s 内 | 青色 (102,204,221) 文本 | 5s 后消失 | crates/jcode-tui/src/tui/ui_input.rs:1768-1776; app/tui_state.rs:1005-1014 |
| jcode | Updates 框（未读 changelog） | 存在未读条目（~/.jcode/last_seen_changelog；首启取最新 5 条）且顶栏留白够 | 圆角“Updates”框：逐行“• 主题” | 正文≤8 行；溢出“…N more · /changelog to see all”；宽≤20 或高<3 不画 | crates/jcode-tui/src/tui/ui_header.rs:961 |
| jcode | copy badge（行内复制提示） | 可复制内容行（错误/工具失败/代码块等）逐行附着；按修饰键时高亮 | 行尾 dim “ [Alt] [⇧] [A]”（标签可配）；按下时高亮，复制后“✓ Copied!” | 预留宽度挤占该行内容并截断（末尾省略号）；行不够宽则换行或截断 | crates/jcode-tui/src/tui/ui.rs:162/196；宽度计算 crates/jcode-tui/src/tui/ui_viewport.rs:222 |
| jcode | Copy/selection mode 状态行 | 按 Alt+Y 进入；拖选时 | 状态行“{Chat\|Side pane\|Input} selection · N chars[· M lines] · Enter/Y copy · Esc exit”；无选区“{pane} selection · drag to copy”；拖动中“… · dragging… · Enter/Y copy · Esc exit” | Esc 退出；复制后退出；Enter/Y 复制选中 | crates/jcode-tui/src/tui/ui_input.rs:1665（状态源 crates/jcode-tui/src/tui/app/tui_state.rs:2005；进出 crates/jcode-tui/src/tui/app/copy_selection.rs:8） |
| jcode | Copy/selection 高亮 | 存在选区（Chat / SidePane / Input 各自） | 选中的聊天行/侧栏行/输入行按选区列范围高亮（反白） | Esc 或复制后清除；覆盖层复制快照仅 Chat 选区生效 | crates/jcode-tui/src/tui/ui_overlays.rs:105；crates/jcode-tui/src/tui/ui_viewport.rs:923；crates/jcode-tui/src/tui/ui_pinned_selection.rs:10；crates/jcode-tui/src/tui/ui_input.rs:2595 |
| jcode | Copy/selection 拖拽滚动（边缘自动滚） | 选区拖到视口上下边缘 | 无额外图形；内容持续滚动以扩展选区 | 松手或离开边缘 | crates/jcode-tui/src/tui/app.rs:1212（copy_selection_edge_autoscroll） |
| jcode | system（系统消息块） | 系统/状态文本写入正文 | 有 markdown 标记走 markdown（保留硬换行），否则纯文本保留缩进；统一 system 色 | 长行按宽换行（不截断） | crates/jcode-tui/src/tui/ui_messages.rs:539 |
| jcode | 单行 system notice | Launch hotkeys / Update diverged / 🧊 冷缓存 三类 | 压成一行、省略号截断；kitty 下替换宽度不稳的 ⚡⏳⏰ 字形 | 超出即省略号截断 | crates/jcode-tui/src/tui/ui_messages.rs:50 |
| jcode | meta 行 | role=meta（仅显示元信息） | 原文纯文本一行（进 raw_plain_lines） | 按宽处理 | crates/jcode-tui/src/tui/ui_prepare.rs:1501 |
| jcode | spacer 空行块 | Ctrl+L 终端式清屏后 | content 指定行数的空白行（注：doubt: Ctrl+L 清屏产物） | 无 | crates/jcode-tui/src/tui/ui_prepare.rs:1608 |
| jcode | 自绘滚动条（display.native_scrollbars） | 开启且内容溢出（total_lines > visible_height） | 右缘 1 列 track；thumb `╷`顶 `│`体 `╵`底，仅 1 格时 `•`；聚焦亮/未聚焦暗 | 不溢出即不画任何列 | crates/jcode-tui/src/tui/ui.rs:3652 |
| jcode | 滚动计数 `↑N` | 自绘滚动条关闭且 scroll>0 | 正文右上角 dim 的向上已滚行数 | 打开自绘滚动条即隐藏 | crates/jcode-tui/src/tui/ui_viewport.rs:1212 |
| jcode | 滚动计数 `↓N` | 自绘滚动条关闭、暂停跟随且未到底 | 正文右下角 queued 色的剩余行数 | 同上；到底即消失 | crates/jcode-tui/src/tui/ui_viewport.rs:1316 |
| jcode | handterm 宿主原生滚动条 | 宿主提供 HANDTERM_NATIVE_SCROLL_SOCKET（外部终端） | 宿主自绘的 scrollbar；App 经 socket 上报 chat/side 面板 x/y/宽高/位置/内容长 | 无 socket 则完全不起作用 | crates/jcode-tui/src/tui/app/handterm_native_scroll.rs:1 |
| jcode | prompt 入场动画 | display.prompt_entry_animation=true 且用户 prompt 行刚滚入视口 | 该行背景色脉冲 + 文字 shimmer 横向扫过 | PROMPT_ENTRY_ANIMATION_MS 到期后淡回常态 | crates/jcode-tui/src/tui/ui.rs:765 |
| jcode | 滚轮动量/平滑滚动 | 鼠标滚轮/触控板滚动正文或右栏 | 队列最多 30 行，前几帧多行/帧、随后减速到 1 行/帧 | 到达底部立即清队列（不积累 phantom 滚动） | crates/jcode-tui/src/tui/app/navigation.rs:814 |
| jcode | copy badge `[Alt] [s]` | 渲染时有可见复制目标（最多 12 个，键 s d f g w e r t x c v b） | 行尾 `[⌥] [X]` 徽标 + 复制成功/失败反馈 | 目标滚出可见区即消失 | crates/jcode-tui/src/tui/ui_viewport.rs:598 |
| jcode | 左键点 composer | Down 落在输入框 | 光标移到该字符位；随后可拖选输入文本 | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1555 |
| jcode | 左键拖选（正文/侧栏/覆盖层） | Down + Drag + Up（同格 jitter 不算拖） | 选区高亮；释放复制到剪贴板并保持高亮 | 下一次点击清除高亮 | crates/jcode-tui/src/tui/app/copy_selection.rs:519 |
| jcode | 拖到窗格边界自动滚动 | 拖拽停在可见区顶/底边行 | 浏览器式单行/帧连续滚动，扩展选区 | 离开边界或释放即停（无动量滑行） | crates/jcode-tui/src/tui/app/copy_selection.rs:467 |
| jcode | 点击 swarm `▸ expand`/`▾ collapse` | Up 落在通知卡首行行尾徽标 | 该卡 tldr ↔ 全正文切换 | 无 tldr 的卡无此响应 | crates/jcode-tui/src/tui/app/navigation.rs:218 |
| jcode | 点击内联图片/标签 | Up 落在图片占位区或 label 行 | Fit→Large→Full 循环（跳过与上一级相同的几何） | 点图片旁边空白不响应 | crates/jcode-tui/src/tui/app/navigation.rs:179 |
| jcode | 点击编辑 expand badge | Up 落在 `expand` 徽标 | diff 切到 FullInline 全展开 + 徽标脉冲 1.1s | 已在 FullInline 时不行为（仅脉冲） | crates/jcode-tui/src/tui/app/navigation.rs:1707 |
| jcode | 点击 copy badge | Up 落在 `[Alt] [x]` | 复制该块 + 状态行 `Copied ...`，失败则 `Failed to copy ...` | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1723 |
| jcode | 点击链接 | Up 落在 URL | 打开系统浏览器 | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1747 |
| jcode | 点击置顶 todo `… +N more` | Down 落在 band 的更多行 | band 展开显示全部 todo 行 | 无（保持展开） | crates/jcode-tui/src/tui/app/navigation.rs:1542 |
| jcode | 滚轮悬停 diagram 面板 | 指针在 diagram pane 内 | pan（上下/左右）；Ctrl+滚 = zoom ±10% | 到 pan 边界不再回落到正文滚动 | crates/jcode-tui/src/tui/app/navigation.rs:1655 |
| jcode | 滚轮悬停 diff/侧栏 | 指针在 diff pane 且 pane 可见 | 滚动右栏；侧栏可见时 Ctrl+滚改图片 zoom 并立即重绘 | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1671 |
| jcode | 拖动 diagram 边框 | Down 在边框行/列，再 Drag | 实时改 pane 比例（side 按列、bottom 按行） | Up 结束拖拽 | crates/jcode-tui/src/tui/app/navigation.rs:1585 |
| jcode | 点击图/正文切换焦点 | Down 落在 diagram/正文/diff | diagram 边框与标题高亮切换；点正文把 diff 焦点关掉 | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1523 |
| jcode | 滚轮在会话选择器 | 指针在预览区 | 共享动量平滑滚动预览；指针在列表则步进选中项 | 到底清动量队列 | crates/jcode-tui/src/tui/app/navigation.rs:1458 |
| jcode | 滚轮在帮助/更新日志/模型状态覆盖层 | 对应覆盖层打开且滚轮 | 该覆盖层滚动；非滚动事件交给拖选复制 | 无 | crates/jcode-tui/src/tui/app/navigation.rs:1394 |
| jcode | 点击面板图片打开预览 | Up 落在已注册的面板图片区 | 全屏图片预览打开（并清 mermaid 图状态） | 任意左键 Up 关闭预览 | crates/jcode-tui/src/tui/app/navigation.rs:1690 |
| jcode | 滚轮滚正文（兜底） | 以上分支都未命中 | 正文进入动量滚动；向上滚即暂停跟随底部 | 滚到底恢复跟随 | crates/jcode-tui/src/tui/app/navigation.rs:1751 |
| jcode | Copy/selection mode 状态行 | 按 Alt+Y 进入；拖选时 | 状态行“{Chat｜Side pane｜Input} selection · N chars[· M lines] · Enter/Y copy · Esc exit”；无选区“{pane} selection · drag to copy”；拖动中“… · dragging… · Enter/Y copy · Esc exit” | Esc 退出；复制后退出；Enter/Y 复制选中 | crates/jcode-tui/src/tui/ui_input.rs:1665（状态源 crates/jcode-tui/src/tui/app/tui_state.rs:2005；进出 crates/jcode-tui/src/tui/app/copy_selection.rs:8） |
