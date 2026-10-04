# 组件 · M5 它伸手（它调用工具时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 41 条 · jcode 16 条

## 两家在这一刻的对照（事实）

- omp 41 条 / jcode 16 条；omp 按输出行数分级（≥3 全量/2 折叠/1 活动行/0 隐藏），按类型渲染 bash/diff/read/todo/wait/task/工具卡；jcode 用 `tool:` 名 + 工具结果行 + 内联 diff（Inline/FullInline/Off）+ 可选 expand

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | ≥3 行 → 全量工具渲染 | 分配 ≥3 行（或无挤压） | 跑该工具的完整 renderer：框/头行/body/section/footer | 挤压到 <3 行且内容超配时才降级 | packages/tui/src/chat/tool-execution.ts:1258 |
| omp | 2 行 → 语义折叠卡 | 分配=2 且 trimBlankEdges 后超 2 行 | 第 1 行 '╭─ <粗体 label> · <muted detail> <dim 秒s>'，第 2 行 '╰' | 再挤压降 1 行；detail 用 truncateToWidth(width-4) 截断 | packages/tui/src/chat/tool-execution.ts:1276 |
| omp | 1 行 → 活动行 + 脉冲 | 分配=1 且内容超 1 行 | <spinner 帧 或 '•'> + ' <粗体 label> · <detail> <秒s>'；未跑完用共享时钟脉冲 | 分配=0 → 整块隐藏 | packages/tui/src/chat/tool-execution.ts:1289 |
| omp | 0 行 → 隐藏（不取消执行） | 分配=0，或被 hideToolActivity / wait 良性跳过 | render 返回 []，占 0 行；执行与 finalize 不受影响 | 不显示，直到重新拿到行预算 | packages/tui/src/chat/tool-execution.ts:1254 |
| omp | 活动摘要（label/detail/elapsed 从哪来） | 折叠/活动行需要一行文字时 | 优先 renderer.activitySummary；否则取 args 的 command/path/input 首行；再否则 '<label> · running' | 无 detail 的自定义摘要且未在跑 → 只留 label；在跑 → 补 'running' | packages/tui/src/chat/tool-execution.ts:1302 |
| omp | 原生 TSP tool 帧（describe） | 支持 tool 节点的终端 | node('tool')：title/target/badges/status/exit/note + collapsed + preview 行数 | 折叠由终端执行；预览上限 DEFAULT_TERMINAL_PREVIEW_LINES=10 | packages/tui/src/chat/tool-execution.ts:987 |
| omp | 工具卡状态底色 | 按 partial/isError 切换 | pending → toolPendingBg；错误 → toolErrorBg；完成 → toolSuccessBg（虚线框） | 良性跳过(steering 打断)走中性 pending 底，不涂红 | packages/tui/src/chat/tool-execution.ts:1418 |
| omp | 工具卡行数分配来源（viewport allocator） | active 块数 > 可用行数时 | 每块先 1 行，余额优先给普通文本块、再给 tool-activity 卡（各按从新到旧） | 余额用尽即停在 1 行；仍超则走 emergency 一行摘要 'N more transcript blocks active' | packages/tui/src/chrome/transcript-container.ts:514 |
| omp | bash/eval 执行框（buildExecutionFrame） | 用户 ! / $ 命令或 bash 工具运行中 | 上边框 + '$ <cmd>' 粗体头 + 输出 + Loader 'Running… (esc to cancel)' + 下边框 | 命令结束换状态尾注；输出折叠到 20 行 | packages/tui/src/chat/execution-shared.ts:51 |
| omp | 执行输出 · 折叠 20 行（tail） | 输出行数 > PREVIEW_LINES=20 且未展开 | 只显示尾部 20 行（edge=tail，先按终端宽度换行再裁），sixel 整段保留 | 尾注 '… N more lines (ctrl+o to expand)'；展开显示全量 | packages/tui/src/chat/execution-shared.ts:25 |
| omp | 流式输出缓存上限（100 行） | 命令输出高速涌入 | 显示缓存只留最后 PREVIEW_LINES*5=100 行；chunk 按 50ms 节流合批 | 更早的行丢出显示缓存（完整输出走 artifact/最终 setComplete） | packages/tui/src/chat/bash-execution.ts:36 |
| omp | 单行 4000 列截断 | 任一行可见宽度 > MAX_DISPLAY_LINE_CHARS=4000 | 截到 4000 列 + '… [N visible columns omitted]' | 被省略的列永不显示（artifact 里有） | packages/tui/src/chat/execution-shared.ts:28 |
| omp | 执行后尾注（exit/cancel/truncation） | 命令结束且有话要说 | '… N more lines (ctrl+o to expand)' / '(cancelled)' / '(exit <code>)' / 截断与 artifact 失败文案，各占一行 | 无内容时整个 footer 不渲染 | packages/tui/src/chat/execution-shared.ts:80 |
| omp | 截断通知文案（formatTruncationMetaNotice） | 工具输出被 head/tail/middle 截断 | 'Showing lines a-b of N'、'(10KB limit)'、'. Use :N to continue'、'Read artifact://… for full output' | 无截断元数据则不出现 | packages/tui/src/tools/output-meta.ts:210 |
| omp | 通用输出面板截断（formatOutputPaneLines） | code cell / 工具卡 / live 面板超行 | head 边：'… N more lines ⟨ctrl+o⟩'；tail 边：'… (N earlier lines, showing M of T)' | 展开显示全量；limit=0 时一行不留 | packages/tui/src/render/output-pane.ts:65 |
| omp | diff 渲染（edit / apply_patch） | edit/apply_patch 有 diff 内容 | 红 -行/绿 +行/灰 context，行号 gutter 至少 3 位，单行替换做词级反白 | 超行数按 hunk 截断并加 '… (N more hunks, M more lines) ctrl+o' | packages/tui/src/chrome/diff.ts:170 |
| omp | edit 折叠 diff 窗口 | edit 卡折叠且 diff 超行 | renderDiffSection + sliceCollapsedDiffRows 只画窗口内完整行 | 尾部 '… (N more hunks, M more lines) ⟨ctrl+o⟩' | packages/tui/src/tools/edit.ts:1050 |
| omp | Read 卡（file/image/url） | read 工具调用/结果 | 头 'Read <path>:行范围'，code cell 折叠只显示前 3 行 (OUTPUT_COLLAPSED) | 尾部 '… N more lines ⟨ctrl+o⟩'；展开 10 行 (OUTPUT_EXPANDED) | packages/tui/src/tools/read.ts:431 |
| omp | Read 分组卡（read-tool-group） | 一轮里连续读多个文件 | 每文件一行摘要 + 每文件前 3 行预览（TRIMMED_BODY_PREVIEW 折叠不裁） | 每文件尾部 '… N more lines ⟨ctrl+o⟩' | packages/tui/src/chat/read-tool-group.ts:139 |
| omp | 图片渲染（终端协议） | 结果带 image 块且终端支持（Kitty/Sixel/iTerm） | 内联图形（Kitty 非 PNG 先转 PNG）；native 走 blob 节点 | 不支持的终端退化为文本占位；已退休 history 也用文本回退 | packages/tui/src/chat/tool-execution.ts:649 |
| omp | 工具错误卡（isError） | 结果 isError=true | 红色边框 + 错误图标头行 + error 色正文（如 read 的 'Read <path>' 错误帧）（注：工具结果 isError 时的红色错误卡） | 常驻，可展开 | packages/tui/src/tools/read.ts:498 |
| omp | 默认工具卡（无 renderer） | 工具不在注册表且无自定义 renderCall/renderResult | formatDefaultToolExecution：工具名 + 输入/输出摘要，背景染色块 | 有 renderer 时改走对应卡；挤压时按行数预算折叠 | packages/tui/src/tools/default-renderer.ts:156 |
| omp | think 工具（内联草稿） | think 工具调用参数流式 | inline：italic thinkingText 的 Markdown 正文，无结果块 | 结果不渲染（renderResult 返回 undefined） | packages/tui/src/tools/think.ts:21 |
| omp | Todo 卡 | todo 工具返回 | 头 'Todo' + '<closed>/<total>'，body 为 checklist 全量 phases | 'No todos' 单行；错误走红卡；每相全完成则该相折叠 | packages/tui/src/tools/todo.ts:505 |
| omp | Wait 卡（后台作业/peer 消息） | wait 返回作业快照或 IRC 消息 | 头行 + 每个 job 一行（状态图标/标签/耗时/%），IRC 消息卡带正文 | 'No jobs to process' 空态；正文折叠 3 行 | packages/tui/src/tools/wait.ts:722 |
| omp | Task / subagent 卡 | task 工具派发子代理 | 每个 agent 一行：id/role 徽标/任务摘要/状态/耗时；结果卡折叠，汇总 '1 succeeded · 1 failed · 12s' | 折叠 '… N more agents ⟨ctrl+o⟩'；失败/中止转 error 色 | packages/tui/src/tools/task.ts:2090 |
| omp | grep/glob/find/web_search 结果卡 | 搜索工具返回 | 头行 + 命中行列表 + '… N more matches/lines' | 非展开只显示前若干行 + ctrl+o 提示 | packages/tui/src/tools/grep.ts:248 |
| omp | Write 卡（流式 body） | write 工具参数流式/结果返回 | 头行 + 文件正文预览，折叠时前若干行 | 尾行 '… N more lines ⟨ctrl+o⟩' | packages/tui/src/tools/write.ts:520 |
| omp | ToolActivityContainer（工具活动显隐代理） | 包住 tool activity 类块 | 可见时透传子渲染；不可见时 render 返回 [] | 隐藏只切一个 prop，子块仍挂载 | packages/tui/src/chrome/tool-activity.ts:12 |
| omp | buildIrcMessageCard | irc:incoming/autoreply/relay/workpool 消息 | IRC 卡（tools/wait 实现）：kind/from/to/body/时间（注：tools/wait 的 IRC 消息卡（agent 间消息）） | 由该卡自身 expand 控制 | packages/tui/src/chat/transcript-render-helpers.ts:118 |
| omp | ToolExecutionComponent | 任意工具调用（pending/running/done/error/cancelled） | 卡/`tool` 框 role `omp.tool.<name>`：head 动词+目标、status、elapsed；body=renderer 输出；late diagnostics chip | 无 body 不折叠；hideToolActivity 隐藏；视口挤出→1-2 行紧凑卡 | packages/tui/src/chat/tool-execution.ts:295 |
| omp | ReadToolGroupComponent | 连续 read 调用（单个或成组） | 「Read <path>:sel」或「Read (N)」+每文件 1 行(glyph/路径/range/冲突 chip 22px)；预览为编号 code | 折叠预览到 COLLAPSED_PREVIEW_LINES+「… N more lines」 | packages/tui/src/chat/read-tool-group.ts:346 |
| omp | BashExecutionComponent | 用户 `!` 命令执行 | 框「$ <command>」（`!!` dim）+输出尾窗 20 行+loader；native tool 卡带 you/not sent 徽标 | 折叠 20 行+「… N more lines (ctrl+o)」；运行中不 finalize | packages/tui/src/chat/bash-execution.ts:55 |
| omp | EvalExecutionComponent | 用户 `$` Python/JS 执行 | 框「>>> <高亮代码>」+输出尾窗 20 行+loader | 折叠 20 行+「… N more lines」；运行中不 finalize | packages/tui/src/chat/eval-execution.ts:31 |
| omp | image-loading | 从不直接上屏 | 图片解码校验/PNG 转换/大小上限 20MiB 逻辑（注：从不直接上屏，图片解码校验逻辑） | n/a | packages/tui/src/chat/image-loading.ts:4 |
| omp | execution-shared | 从不直接上屏（bash/eval 卡构建期调用） | 执行框 scaffold、状态页脚、native card/tool 描述（ansi 输出 20 行预览）（注：从不直接上屏，执行框 scaffold 共享） | n/a | packages/tui/src/chat/execution-shared.ts:143 |
| omp | ToolActivityContainer | 包裹工具活动块时 | 无自身内容；hideToolActivity 时整块隐藏 | 隐藏时 render 返回 [] | packages/tui/src/chrome/tool-activity.ts:12 |
| omp | diff.ts (renderDiff / nativeDiff) | 工具卡内的 diff 正文 | 每行前缀+行号+内容；删红增绿、单行替换词级反色、缩进/空白可视化 | 由工具卡折叠控制；>999 行行号宽度恒定 | packages/tui/src/chrome/diff.ts:172 |
| omp | Console 面板（ANSI） | 交互式 bash 工具（PTY）运行时 | 圆角框：头 `icon Console <cmd> [state]`、PTY 视口（≤终端行 80%-4）、脚 `escape force-kill · input forwarded to PTY`（注：交互式 bash 工具的 PTY 面板） | 会话结束脚变 `session finished` | packages/tui/src/tools/bash-interactive.ts:319 |
| omp | Console sheet（Tern） | Tern 渲染 | full sheet `Console`：命令 + 状态徽标、ansi PTY 屏、Force kill 按钮（注：交互式 bash 工具的 sheet） | 同上 | packages/tui/src/tools/bash-interactive.ts:276 |
| omp | state 徽标 | 始终 | `[running]` / `[timed out]` / `[killed]` / `[exit 0]` / `[exit N]` / `[exited]`，按语调着色（注：Console 状态徽标） | 状态推进即变 | packages/tui/src/tools/bash-interactive.ts:276 |
| jcode | swarm transcript 卡（spawn 回调下） | transcript 里的 swarm spawn 工具调用 | 每 member 一行稳定摘要：图标+状态字形+label+ · Working/Completed · 模型 · Provider route（不含动态 age/tail/todo）（注：doubt: spawn 工具卡；亦涉 M11 名册） | 宽度紧时从右往左丢 metadata 直到放不下 label | crates/jcode-tui/src/tui/info_widget_swarm_gallery.rs:111, crates/jcode-tui-render/src/swarm_gallery.rs:312 |
| jcode | `tool:` 工具名行 | 该条 assistant 带 tool_calls | 一行 `  tool: a · b · c`；单个时标签为 `tool:` | 放不下先丢尾部工具名，改显 `· +N more` | crates/jcode-tui/src/tui/ui_messages.rs:317 |
| jcode | 工具结果行（主行） | 每条 role=tool 结果（含 batch / 失败） | `  ✓\|✗\|⚠ <tool名> · <intent> · <dim 摘要> · <tokens>`，⚠=部分成功，✗=失败 | 先保 token 后缀；中段摘要按剩余宽截断；intent 占位优先 | crates/jcode-tui/src/tui/ui_messages.rs:4106 |
| jcode | 编辑统计 `(+N -M)` | edit 类工具（write/edit/multiedit/patch/apply_patch/replace）且有行变更 | 行尾绿 `+N` 红 `-M` | 无变更时不渲染 | crates/jcode-tui/src/tui/ui_messages.rs:4143 |
| jcode | dimmed 技术细节 | display.tool_call_details=true（默认 false） | intent 之后再接 ` · <command/path/args>`（dim） | 关：只显示 intent；无 intent 时总回退技术摘要；错误摘要永远显示 | crates/jcode-tui/src/tui/ui_messages.rs:4100 |
| jcode | bash 命令详情行 | bash 行无 intent 且首行未含 `$` | 第二行 `    <command>`（dim，带 budget 截断） | 超宽截断；有 intent 时永不落到第二行 | crates/jcode-tui/src/tui/ui_messages.rs:4233 |
| jcode | bash 输出尾行（show_bash_output） | display.show_bash_output=true 且输出非 'Command completed successfully (no output)' | 末 3 行非空输出，`      ` 缩进 dim | 只保留最后 3 行 | crates/jcode-tui/src/tui/ui_messages.rs:4261 |
| jcode | agentgrep 全文（show_agentgrep_output） | 工具名 agentgrep 且 display.show_agentgrep_output=true | `    │ ` 边框缩进的搜索结果正文 | 硬上限 400 行（MAX_BODY_LINES） | crates/jcode-tui/src/tui/ui_messages.rs:487 |
| jcode | batch 子调用行 | tool_name=batch 且有 tool_calls 数组 | 每子调用一行 `✓/✗ <sub tool> · …`（含子结果摘要），内嵌 todo/draft/discovery 卡右缩进 | 按行宽截断；子结果按 index 匹配 | crates/jcode-tui/src/tui/ui_messages.rs:4290 |
| jcode | gmail draft 卡 | tool=gmail 且 action=draft | 卡片（Draft ID 等，非错误才画） | 无 Draft ID 时不渲染 | crates/jcode-tui/src/tui/ui_messages.rs:3394 |
| jcode | discovery / integration_tools 卡 | 工具为 integration_tools 的搜索结果 | 条目卡：名称+简介，选择态附 URL/setup（注：doubt: 工具结果卡；亦涉 S10） | 详情 ≤2 行、setup ≤3 行 | crates/jcode-tui/src/tui/ui_messages.rs:3619 |
| jcode | 内联 diff（Inline 模式） | diff_mode=Inline 且 edit 工具、行变更可解析 | `┌─ diff · path`，每行 `│ +/−/上下文`（语法高亮按 diff 色 tint），换文件插 `├─ diff · path`，尾 `└─` | >12 行进头6+尾6 折叠，中插 `│ ... N more changes ...`；行宽不足右侧 `…`；尾变 `└─ (+A -D total)` | crates/jcode-tui/src/tui/ui_messages.rs:4300 |
| jcode | 内联 diff（FullInline 模式） | diff_mode=FullInline | 同 Inline，但不折叠、行内不截断 | 无折叠无截断（只受终端高度） | crates/jcode-tui/src/tui/ui_messages.rs:4323 |
| jcode | Off 模式 | diff_mode=Off | 正文完全不画 diff（只留编辑统计 `(+N -M)`） | 无 | crates/jcode-config-types/src/lib.rs:66 |
| jcode | 工具行 token 徽标 | 每条工具结果都有 | ` · 1.2k` 近似 token；色随 Normal/Warning/Danger 变 | 始终保留（靠右侧截断） | crates/jcode-tui/src/tui/ui_messages.rs:4455 |
| jcode | expand badge `[Alt] [⇧] [E] expand` | 编辑 diff 可展开（>12 行或行超宽） | 行尾徽标；展开后变 `✓ Expanded`（注：doubt: diff 展开徽标） | diff 未被截断则不渲染徽标 | crates/jcode-tui/src/tui/ui_viewport.rs:57 |
| jcode | 工具结果行（主行） | 每条 role=tool 结果（含 batch / 失败） | `  ✓｜✗｜⚠ <tool名> · <intent> · <dim 摘要> · <tokens>`，⚠=部分成功，✗=失败 | 先保 token 后缀；中段摘要按剩余宽截断；intent 占位优先 | crates/jcode-tui/src/tui/ui_messages.rs:4106 |
