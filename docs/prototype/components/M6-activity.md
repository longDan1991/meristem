# 组件 · M6 它在动（它在跑动作时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 19 条 · jcode 18 条

## 两家在这一刻的对照（事实）

- omp 19 条 / jcode 18 条；omp 以工作 loader/HUD（判分、下载、/omfg、/cleanse、live visualizer 频谱）为主；jcode 以状态行字面进度（构建/限流/connecting/thinking/streaming+running tool/batch/压缩/语音）为主

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | working row（Loader WorkingRowSpec） | 回合进行中 | starburst spinner（retry 时改倒计时 ring）+ 闪烁 intent + '·' + 计时 + 撑开的空隙 + tok/s + Stop(esc) 控件 | 压缩时 Stop 前加不定进度条；turn 结束整行消失 | packages/tui/src/components/loader.ts:58 |
| omp | progressHudContainer · 判分批次行 | 并发 judge batch 运行中/刚结束 | 右对齐 '<dim intent> ━━━─── <done/total> · $cost · N failed'，18 列进度条（注：judge 批次进度+成本+失败数） | 窄屏先丢 label 再丢 bar；结束保留 JUDGMENT_BATCH_PROGRESS_RETAIN_MS 后删行 | packages/coding-agent/src/modes/progress-hud.ts:75 |
| omp | progressHudContainer · 自动下载行 | 自动下载/安装模型或二进制 | 右对齐 byte 进度条 + 'a / b'；无大小则当前步骤；完成 'ready'，失败 'failed: 原因'（注：自动下载/安装进度条） | 150ms 内完成不出现；done 留 1.5s，failed 留 10s 后消失 | packages/coding-agent/src/modes/progress-hud.ts:162 |
| omp | statusContainer | 有临时活/维护任务时（工作 loader、压缩、重试、交接、worktree、选择器摘要） | StatusHudContainer：spinner+文案、右侧 tok/s trailer、停止控件；空时显示 idle tok/s 行（注：工作 loader HUD 容器（spinner+tok/s）） | agent_end/disposeChildren 即清空 | packages/coding-agent/src/modes/interactive-mode.ts:720,1805,1821 |
| omp | omfgContainer | /omfg 投诉生成 TTSR 规则运行中 | OmfgPanelComponent（生成中→规则面板）（注：/omfg 规则生成面板容器） | 结束/关闭即 clear | packages/coding-agent/src/modes/controllers/omfg-controller.ts:87,301 |
| omp | cleanseContainer | /cleanse 诊断运行中 | CleansePanelComponent（诊断进度/结果面板）（注：/cleanse 诊断面板容器） | 结束/中断即 clear | packages/coding-agent/src/modes/controllers/cleanse-command-controller.ts:82,147 |
| omp | progressHudContainer（新发现） | judge 批次或自动下载进行中 | JudgmentBatchProgressHud + DownloadActivityHud，工作行正上方 | 任务结束即移行 | packages/coding-agent/src/modes/interactive-mode.ts:1817-1820 / modes/progress-hud.ts:75,162 |
| omp | 工作行 / idle 行（StatusHudContainer 内容） | 跑回合显示工作 loader；空转且测到 tok/s 显示 idle 行 | label+elapsed(计时)+tok/s trailer+停止控件；idle 只右对齐 tok/s（注：工作 loader + 空闲 tok/s 行） | agent_end 清空；无 tok/s 则 idle 不画 | packages/coding-agent/src/modes/interactive-mode.ts:1321,736 |
| omp | createLiveBoard | 独立 CLI 命令（bench/cleanse/if-bench） | 约 12.5fps 原位重绘的多行板；log 行在其上方滚出（注：bench/cleanse/if-bench 的实时重绘板） | close() 清板；非 TTY 完全不渲染、log 退化为普通写 | packages/tui/src/chrome/live-board.ts:38 |
| omp | /omfg 面板 | /omfg <complaint> | 面板标题「/omfg <complaint>」；正文=状态行 + 生成的 TTSR 规则预览(流式) + footer 提示（注：/omfg 规则生成面板（进行中）） | 状态收尾(saved/rejected/aborted/error)后面板留驻直到用户关；Esc/取消 | packages/tui/src/overlays/omfg-panel.ts:13-60 |
| omp | 阶段状态行 | generating/validating/confirming/saving/saved/rejected/aborted/error | 头部 spinner(在飞状态) + 状态文案「Generating TTSR rule…」「Saved <path>」等（注：生成/校验等阶段状态） | 状态切换即刷新 | packages/tui/src/overlays/omfg-panel.ts:14-40,73-110 |
| omp | /cleanse 面板 | /cleanse [request] [--all] | 面板标题「/cleanse <request>」；正文=phase/checker/agent 进度 + 日志区(≤14 行，最新在下)；footer 显示 outcome 色（注：TUI 内 /cleanse 内联面板（诊断进行中）；疑点：诊断亦近 M9） | 完成后面板留驻直到用户关；日志只保 14 行(丢最旧) | packages/tui/src/overlays/cleanse-panel.ts:23-24,47-66,101-130 |
| omp | 带边框 loader | hook 操作进行中 | 上下边框 + CancellableLoader 动画行 + 「esc cancel」提示 | 操作完成/取消后移除 | packages/tui/src/overlays/bordered-loader.ts:9-30 |
| omp | LiveVisualizer 面板 | 实时语音通话中（替换编辑器槽位） | 固定 3 行面板：频谱/状态、mic 电平、转写行，外包圆角框与页脚（注：实时语音通话面板（替换编辑器槽位）；疑点：语音通话无更贴切分类） | 通话结束还原编辑器 | packages/tui/src/apps/live-visualizer.ts:62 |
| omp | phase 状态 | 通话各阶段 | `○ connecting` / `● listening` / `○ working`(spinner) / `» speaking` / `× muted` / `! error`（注：通话各阶段状态） | 阶段切换即变 | packages/tui/src/apps/live-visualizer.ts:167 |
| omp | mic 电平 | 始终 | `mic` + meter bar（无 meter 能力则 progress），level 按 1/20 步进（注：mic 电平表） | muted 时归零 | packages/tui/src/apps/live-visualizer.ts:167 |
| omp | 频谱动画 | 非 muted | 2 行方块频谱（█▇▆▅▄▃▂▁），能量 sqrt 衰减驱动（注：2 行方块频谱动画） | muted 不画（energy=0） | packages/tui/src/apps/live-visualizer.ts:289 |
| omp | 转写行 | 用户语音转写流入 | 单行 accent 文本，过宽时左侧 `…` 截断保留尾部（注：语音转写流入行） | clearTranscript 或通话结束 | packages/tui/src/apps/live-visualizer.ts:256 |
| omp | 通话按钮 / 页脚 | 始终 | `space Mute\|Unmute` + `escape End call`；ANSI 页脚 `icon phase · space mute · escape end`（注：通话操作按钮/页脚） | 放不下只留 `icon phase`，再不行空标签 | packages/tui/src/apps/live-visualizer.ts:262 |
| omp | 通话按钮 / 页脚 | 始终 | `space Mute｜Unmute` + `escape End call`；ANSI 页脚 `icon phase · space mute · escape end`（注：通话操作按钮/页脚） | 放不下只留 `icon phase`，再不行空标签 | packages/tui/src/apps/live-visualizer.ts:262 |
| jcode | 构建进度 (build progress) | read_build_progress() 有值（最高优先） | spinner(12.5fps) + ` {text}` 黄 | 构建读完即消失 | crates/jcode-tui/src/tui/ui_input.rs:796-807 |
| jcode | 限流 Rate limited | rate_limit_remaining() 有值 | spinner(4fps) + `Rate limited. Auto-retry in {h\|m\|s}...`(+queued) | 倒计时结束/重试发出 | crates/jcode-tui/src/tui/ui_input.rs:808-833 |
| jcode | sending… | ProcessingStatus::Sending | spinner + ` sending… {elapsed}` dim(+queued) | 进入 Connecting/Thinking | crates/jcode-tui/src/tui/ui_input.rs:841-853 |
| jcode | connecting 族（refreshing auth/connecting/sending context/waiting for response/retrying N/M） | ProcessingStatus::Connecting(phase) | spinner + `{phase}… {elapsed}{transport}` | 阶段切换 | crates/jcode-tui/src/tui/ui_input.rs:621-630,854-886 |
| jcode | connecting 变黄阈值 | Retrying 恒黄；Auth/Connecting/SendingRequest 本阶段 >10s 变黄 | rgb(255,193,7)，其余 dim | 阶段重置换色 | crates/jcode-tui/src/tui/ui_input.rs:864-881 |
| jcode | thinking… | ProcessingStatus::Thinking | spinner + ` thinking… {elapsed}{transport}` dim(+queued) | 开始流式/工具 | crates/jcode-tui/src/tui/ui_input.rs:887-897 |
| jcode | streaming + tps | ProcessingStatus::Streaming | `{time}·{tps:.1} tps·↑in ↓out{transport}` | 转 Thinking/工具/turn 结束 | crates/jcode-tui/src/tui/ui_input.rs:898-935 |
| jcode | streaming 静默/停滞标记 | >2s 无 token→`(no tokens Ns)`；>10s→`(stalled Ns)` | 前缀插在耗时前；消息结束后不再显示 | 有新 token 即消失 | crates/jcode-tui/src/tui/ui_input.rs:714-727 |
| jcode | running tool | ProcessingStatus::RunningTool(name) | spinner+` running {name}`+` · {detail}`粗体+transport+elapsed | 工具结束 | crates/jcode-tui/src/tui/ui_input.rs:951-1078,1080-1102 |
| jcode | running tool 尾部 · alt+B bg | 每次 running tool 都追加 | ` · {alt_chord("B")} bg`（Alt+B / ⌥+B） | 工具结束 | crates/jcode-tui/src/tui/ui_input.rs:1048-1051 |
| jcode | batch 进度 | RunningTool("batch") | ` · {done}/{total} done` + ` · last done: X` 或 ` · running: #1 name +N` | batch 结束（完成后隐藏 last done） | crates/jcode-tui/src/tui/ui_input.rs:729-772,975-982 |
| jcode | subagent 状态括注 | subagent_status() 有值 | ` ({status})` dim | 子代理结束 | crates/jcode-tui/src/tui/ui_input.rs:1004-1009 |
| jcode | `+N queued` 后缀 | pending_count>0，拼接在各处理分支尾 | ` · +N queued`，queued_color（注：doubt: 活动行处理中后缀；亦含 M3 排队语义） | 队列清空 | crates/jcode-tui/src/tui/ui_input.rs:790-795,1105-1111 |
| jcode | 语音：录音中 | voice phase=Recording | `● m:ss ▁▃▅… {live≤56字\|listening…} · {key} send · Esc cancel` 红粗（注：doubt: 录音计时；亦涉 M2 输入） | 停止/取消/转写 | crates/jcode-tui/src/tui/app/voice_input.rs:275-300,346-355 |
| jcode | 语音：转写中 | voice phase=Transcribing | `◌ Transcribing…{live} · Esc discard` 蓝粗 | 出结果/丢弃 | crates/jcode-tui/src/tui/app/voice_input.rs:302-312 |
| jcode | 压缩进度通知 | 本地未在远端且 jcode 压缩进行中 | 压缩进度条文本（status_notice 同一格）（注：doubt: 压缩进度；亦涉 M10 压缩） | 压缩结束 | crates/jcode-tui/src/tui/app/tui_state.rs:976-984; conversation_state.rs:49-70 |
| jcode | Remote·顶栏启动阶段标签 | 远端引导中（spawning/connecting/loading session/reload/reconnect） | 顶栏 model 行位置显示“starting server… / connecting to server… / loading session… / waiting for reload… / reconnecting (N)…”并在 >1s 后附秒数（注：doubt: 远端启动 connecting 阶段） | 收到 history/模型 catalog 即清空；<1s 不显示秒 | crates/jcode-tui/src/tui/app.rs:463；读取 crates/jcode-tui/src/tui/app/tui_state.rs:149 |
| jcode | 🐝 Swarm await 行 | scope=swarm_await（等待子 agent 结束） | 单行 `🐝 ✓ 3/3` 或 `2/3 finished`（从成员状态行数出）（注：doubt: 等待子 agent 中） | 压成一行 | crates/jcode-tui/src/tui/ui_messages.rs:3103 |
| jcode | 限流 Rate limited | rate_limit_remaining() 有值 | spinner(4fps) + `Rate limited. Auto-retry in {h｜m｜s}...`(+queued) | 倒计时结束/重试发出 | crates/jcode-tui/src/tui/ui_input.rs:808-833 |
| jcode | 语音：录音中 | voice phase=Recording | `● m:ss ▁▃▅… {live≤56字｜listening…} · {key} send · Esc cancel` 红粗（注：doubt: 录音计时；亦涉 M2 输入） | 停止/取消/转写 | crates/jcode-tui/src/tui/app/voice_input.rs:275-300,346-355 |
