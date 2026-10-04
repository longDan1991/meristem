# 组件 · M10 我站在哪、花了多少（位置与用量时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 68 条 · jcode 22 条

## 两家在这一刻的对照（事实）

- omp 68 条 / jcode 22 条；omp 覆盖状态栏各 segment（model/mode/path/git/usage/cache/time/separator 配置）+ turn usage 行；jcode 以输入下方 overscroll 状态行 + 数据闸挂件（Overview/UsageLimits/KvCache/ModelInfo/Compaction/GitStatus/Commits）+ /usage 卡

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Editor 顶边框状态内容 | 状态行以 top-border/top-rule-chip 附着，或宿主提供 provider | 边框线内嵌一段已着色的状态串（ANSI）（注：状态串附着在输入框顶边框上，属状态/事实带） | 超出可用宽由 provider 自决截断 | packages/tui/src/components/editor.ts:1364 |
| omp | TranscriptStatusBlock（紧凑状态行） | 背景作业完成/文件提及/launch 完成等 | 每行由若干主题化 part 用空格拼；native 每行一个 wrap=word 的 text（注：紧凑状态行原语，用于后台作业完成/文件提及等；疑点：亦近 M8） | 行数即 blocks 数；无内容则不挂 | packages/tui/src/chrome/transcript-status.ts:23 |
| omp | modelCycleContainer + segment-track（ctrl+p 切模型角色） | cycle 模型角色后 4 秒内 | 空行 + 一行 segment 轨道：位置配色标签，当前段反白 powerline chip（两侧三角）（注：模型角色切换的段轨道 HUD） | MODEL_CYCLE_TRACK_CLEAR_MS=4000 后自动清除（重绘清空重挂） | packages/coding-agent/src/modes/interactive-mode.ts:4073 |
| omp | 空闲吞吐行（renderIdleStatusHud） | 无 working 行但有速率/标题要显示 | 空行 + 右对齐 '<throughput 图标> N.N tok/s'（band 模式再接标题）（注：空闲时右对齐 tok/s 速率行） | 无 trailer 返回 undefined（不占行） | packages/coding-agent/src/modes/interactive-mode.ts:1341 |
| omp | Compaction 分隔条 + ctrl+o 详情 | 发生压缩（remote/soft/snapcompact/handoff/legacy） | 一行 '──── 📷 remote-compacted · 256K→20K · ctrl+o ────'；展开是 customMessageBg 框里的摘要 Markdown（注：上下文压缩后的分隔条） | 窄到放不下则只留裸 label；对话正文保留不删 | packages/tui/src/chat/compaction-summary-message.ts:195 |
| omp | Handoff 分隔条 | handoff 策略压缩（customType=handoff 且 display） | divider '⧉ handed-off'，展开 'Handoff context' + 文档（注：handoff 策略压缩后的分隔条） | 无 handoff 内容时展开显示 '_No handoff content._' | packages/tui/src/chat/compaction-summary-message.ts:262 |
| omp | Cache-miss 标记 | 上一回合 warm cache 被读、本回合 cacheRead 归零且 cacheWrite>0 | 短左对齐 divider '──── ⊘ cache miss · 50.9k tokens'（注：cache miss 分隔线 + token 数） | 仅首个断点出现一次；后续冷回合不重复 | packages/tui/src/chat/cache-invalidation-marker.ts:126 |
| omp | Served-model 标记 | 响应实际由与请求不同的模型提供（首次该组合） | warning 色 divider '⚠ served X · requested Y · via provider/upstream'（注：实际提供模型与请求模型不同的警示线） | 同组合只播报一次；无法分类的 id 不算 | packages/tui/src/chat/served-model-marker.ts:96 |
| omp | pi | 恒在；回合中→spinner+回合计时；聚焦子agent→ghost+id | 空:品牌图标；跑:盲文spinner+'12s/5m/1h'；聚焦:ghost图标+agentId | 仅被宽度裁，左组内缘先丢 | packages/tui/src/status-line/segments.ts:203 |
| omp | status | 有 hook/扩展 setStatus 文本时；否则不画 | 各状态去控制符后用'·'拼接，accent 上色 | 无状态即空 | packages/tui/src/status-line/segments.ts:248 |
| omp | model | 恒在（无模型显示 no-model） | 模型名(去'Claude ')+'· 思考级'/'⟳ auto'/' off'+fast图标+advisor眼+slow标签 | 随模式被宽度丢弃 | packages/tui/src/status-line/segments.ts:338 |
| omp | mode | plan/prewalk/goal/vibe/loop 任一激活才画 | 按优先取一:Plan(暂停黄)/Prewalk/Goal+预算/Vibe/Loop+限次+条件摘要 | 无模式即空 | packages/tui/src/status-line/segments.ts:486 |
| omp | path | 恒在 | worktree→项目名；否则 folder 图标+缩略 cwd+' ↳ repo根' | 先缩到≥8格再丢，比其它左段后丢 | packages/tui/src/status-line/segments.ts:564 |
| omp | git | 有分支或有 staged/unstaged/untracked 统计 | branch图标+branch，空格后 *未暂存 +已暂存 ?未跟踪；dirty 用 warning 色 | 非 repo/无分支即空 | packages/tui/src/status-line/segments.ts:627 |
| omp | pr | 当前分支有 PR | PR图标+'#123'（终端超链接） | 无 PR 即空 | packages/tui/src/status-line/segments.ts:697 |
| omp | subagents | 运行中子 agent 数>0 | agents 图标+数量 | =0 即空 | packages/tui/src/status-line/segments.ts:714 |
| omp | token_in | 输入 token>0 | ↑ + 数字 | =0 即空 | packages/tui/src/status-line/segments.ts:729 |
| omp | token_out | 输出 token>0 | ↓ + 数字 | =0 即空 | packages/tui/src/status-line/segments.ts:731 |
| omp | token_total | in+out+cacheWrite+编排 总和>0 | tokens 图标+总量（不含 cacheRead） | =0 即空 | packages/tui/src/status-line/segments.ts:733 |
| omp | token_rate | 测得 tok/s 非空 | throughput 图标+'12.3 tok/s' | 无采样即空 | packages/tui/src/status-line/segments.ts:758 |
| omp | cost | 有可计费项（自费/订阅/子agent/advisor） | $金额(3位小数)+子agent/advisor 分摊 | 无花费即空 | packages/tui/src/status-line/segments.ts:818 |
| omp | context_pct | 恒在（窗口未知时退化） | context 图标+百分比/窗口数字；>100% 红；auto 图标(推测脉冲) | 窗口=0 时显示窗口数字而非百分比 | packages/tui/src/status-line/segments.ts:832 |
| omp | context_total | contextWindow>0 | context 图标+窗口大小 | 窗口=0 即空 | packages/tui/src/status-line/segments.ts:889 |
| omp | time_spent | 累计活跃时长≥1000ms | time 图标+'3m12s'（只算 agent_start→end 并集） | <1s 即空 | packages/tui/src/status-line/segments.ts:913 |
| omp | time | 恒在 | time 图标+时钟（12/24h，可带秒） | 仅宽度 | packages/tui/src/status-line/segments.ts:945 |
| omp | session | 恒在 | session 图标+会话 id 前 8 位（无则 'new'） | 仅宽度 | packages/tui/src/status-line/segments.ts:955 |
| omp | hostname | 恒在 | host 图标+主机名首段 | 仅宽度 | packages/tui/src/status-line/segments.ts:970 |
| omp | cache_read | cacheRead>0 | cache 图标+数字 | =0 即空 | packages/tui/src/status-line/segments.ts:984 |
| omp | cache_write | cacheWrite>0 | cache 图标+数字 | =0 即空 | packages/tui/src/status-line/segments.ts:986 |
| omp | cache_hit | cacheRead>0 | cache 图标+命中率如 '98.12%' | =0 即空 | packages/tui/src/status-line/segments.ts:993 |
| omp | session_name | 会话已命名（或 preview 有标题） | 标题，accent 上色，去控制符 | 未命名即空；先截到 8 格再整体丢 | packages/tui/src/status-line/segments.ts:1021 |
| omp | usage | 有 5h/1d/7d/mo 配额或 reset credits | '5h 42% (1h20m)' 等点分窗口 + '✦ n' 重置额度/过期 | 无配额即空 | packages/tui/src/status-line/segments.ts:1189 |
| omp | collab | collab 会话中 | '⇄ collab:N'（host）或 '⇄ collab guest:N' | 非协作即空 | packages/tui/src/status-line/segments.ts:1039 |
| omp | stream | 有观众流或正在 /record | '● LIVE N'、'● REC'（可同时） | 两者都无即空 | packages/tui/src/status-line/segments.ts:1055 |
| omp | vim | tui.vimMode 开且 display≠none | INSERT/NORMAL/VISUAL/V-LINE(+' NL'选中行)+待输入回显 | 关闭即空 | packages/tui/src/status-line/segments.ts:1104 |
| omp | default | statusLine.preset 默认值 | 左 pi,vim,model,mode,collab,stream,path,git,pr,context_pct,cost；右 session_name；powerline-thin | 宽度不足按段优先级丢 | packages/tui/src/status-line/presets.ts:4 |
| omp | minimal | preset=minimal | 左 vim,path,git；右 session_name,mode,context_pct；slash 分隔 | 同上 | packages/tui/src/status-line/presets.ts:17 |
| omp | compact | preset=compact | 左 vim,model,mode,git,pr；右 session_name,cost,context_pct；不显思考级 | 同上 | packages/tui/src/status-line/presets.ts:30 |
| omp | full | preset=full | 左 pi,vim,hostname,model,mode,path,git,pr,subagents；右 session_name,cache_hit,token_in/out,token_rate,cache_read,cost,context_pct,time_spent,time；powerline | 同上 | packages/tui/src/status-line/presets.ts:43 |
| omp | nerd | preset=nerd（全 Nerd Font 图标） | 在 full 基础上加 session、cache_write、context_total；带秒；powerline | 同上 | packages/tui/src/status-line/presets.ts:64 |
| omp | ascii | preset=ascii（无 Nerd Font 依赖） | 左 vim,model,mode,path,git,pr；右 session_name,token_total,cost,context_pct；ascii 分隔 | 同上 | packages/tui/src/status-line/presets.ts:87 |
| omp | custom | preset=custom 且未覆盖段 | 用 CUSTOM_STATUS_LINE_DEFAULTS：左 vim,model,mode,path,git,pr；右 session_name,token_total,cost,context_pct；powerline-thin | 同上 | packages/tui/src/status-line/presets.ts:99（默认值 schema.ts:27） |
| omp | separator=powerline | settings statusLine.separator=powerline | 实心箭头分隔+两端 powerline 端帽（需不透明底色） | 透明模式丢弃端帽 | packages/tui/src/status-line/separators.ts:6 |
| omp | separator=powerline-thin | 默认 / 未知样式回退 | 细箭头分隔+端帽 | 透明模式丢弃端帽 | packages/tui/src/status-line/separators.ts:29 |
| omp | separator=slash | settings 选 slash | 以 '/' 分隔，无端帽 | — | packages/tui/src/status-line/separators.ts:13 |
| omp | separator=pipe | settings 选 pipe | 以 '\|' 分隔，无端帽 | — | packages/tui/src/status-line/separators.ts:17 |
| omp | separator=block | settings 选 block | 以 '█' 分隔，无端帽 | — | packages/tui/src/status-line/separators.ts:21 |
| omp | separator=none | settings 选 none | 以空格分隔 | — | packages/tui/src/status-line/separators.ts:23 |
| omp | separator=ascii | settings 选 ascii | ASCII 箭头分隔，无端帽 | — | packages/tui/src/status-line/separators.ts:25 |
| omp | contextLine=off | statusLine.contextLine=off（或窗口未知） | 左右组之间一条纯 accent 实线，无尺度反馈 | — | packages/tui/src/status-line/component.ts:3011 |
| omp | contextLine=percentage | mode=percentage | 已用部分 accent，剩余用 border 色 | — | packages/tui/src/status-line/component.ts:3007 |
| omp | contextLine=annotated | mode=annotated 且 autoCompact 开、格宽≥8 | 在 percentage 上叠加推测起点/自动压缩阈值两个图标标记 | 格宽<8 或边界不可知则不画标记 | packages/tui/src/status-line/component.ts:3011-3050 |
| omp | contextLine=embedded | 默认值；左或右含 context 段且有非 context 段 | annotated 基础上把 context 百分比+窗口数字吸进标尺（超100% 红、破窗右移） | 空间不够则省标签，仅一格里退回单格标尺 | packages/tui/src/status-line/component.ts:2799,2996 |
| omp | 贴法 top-border | composer.shape=box | 状态条嵌进编辑器顶部圆角边框，左右两组夹一条 context 标尺 | — | packages/tui/src/components/composer/box.ts:13 / component.ts:3177 |
| omp | 贴法 top-band | composer.shape=band（默认） | 输入框上方一条 flush、软左端帽的通栏状态带；session_name 移到工作行右侧 | band 下 title 不进带 | packages/tui/src/components/composer/band.ts:14 / component.ts:3180 |
| omp | modelCycleContainer | ctrl+p/快捷键切换角色模型后 | Spacer+角色 chip 轨道（renderSegmentTrack，activeIndex 实心） | 4s 后自动清空 | packages/coding-agent/src/modes/interactive-mode.ts:4067,4090 |
| omp | ServedModelMarkerComponent | 响应模型≠请求模型（可分类、且该对首次出现） | 短分隔线「──── ⚠ served X · requested Y · via P/up」 | 每对(provider,req,served)只现一次 | packages/tui/src/chat/served-model-marker.ts:78 |
| omp | CacheInvalidationMarkerComponent | 上轮 cacheRead≥2048、本轮 cacheRead=0 且 cacheWrite>0、复算≥2048 | 短分隔线「──── ⊘ cache miss · 50.9k tokens」 | 单次出现；无 token 时省 tokens 段 | packages/tui/src/chat/cache-invalidation-marker.ts:78 |
| omp | CompactionSummaryMessageComponent | 发生 compaction（remote/soft/handoff/snapcompact/shake） | 分隔条「📷 <方法> · 256K→20K · ctrl+o」；展开摘要 markdown | 常驻；太窄退化为裸标签 | packages/tui/src/chat/compaction-summary-message.ts:195 |
| omp | HandoffSummaryMessageComponent | customType=handoff 且 display | 分隔条「⌂ handed-off」；展开「Handoff context」+文档 | 常驻；太窄退化为裸标签 | packages/tui/src/chat/compaction-summary-message.ts:267 |
| omp | TranscriptStatusBlock | 由通知/后台活动构造时 | 每行若干带色 part 以空格连接；rowsOnly 树形连接符仅 ANSI 画 | 常驻；行内 wrap 换行 | packages/tui/src/chrome/transcript-status.ts:23 |
| omp | MessageDividerComponent | 水印分隔线（cache miss / served model 复用） | 空行+「──── label」短左对齐线；native 可为 inline 图标行 | 窄于标签时截断；truncateWhenNarrow=false 保裸标签 | packages/tui/src/chrome/message-divider.ts:31 |
| omp | SegmentTrack (renderSegmentTrack/describeSegmentTrack) | plan-mode 模型档滑块、ctrl+p 角色循环状态 | 一行彩色分段，活动段为 powerline chip（bg+对比前景+两端三角）（注：模型档滑块/角色循环的段轨道） | 单行，超宽截断 | packages/tui/src/chrome/segment-track.ts:86 |
| omp | format.ts (renderAsciiBar/describeAsciiBar/formatProviderName/formatCoarseDuration) | `/context`、用量报告等文本中 | 「[██░░] 50%」进度条一行；native progress 节点（label 百分比）（注：进度条行，用于 /context 与用量报告） | 固定宽度参数（默认 24） | packages/tui/src/chrome/format.ts:59 |
| omp | context-thresholds | 从不直接上屏 | 按用量算 level/tone/meter 阈值(50/70/90% 或 150k/270k/500k)与格式化文本（注：从不直接上屏，用量阈值计算） | n/a | packages/tui/src/chrome/context-thresholds.ts:31 |
| omp | omp.turn.usage 行 / TurnUsageTally | 一轮结束(最后一条 assistant 消息，非 toolUse stop)时出现在 transcript | 一行：prompt→yield 墙钟(elapsedMs) + input/output tokens + cost($)（注：一轮结束在 transcript 里的内联用量行（时长/token/花费），疑点：亦近 S9） | 随 transcript 滚动；elapsedMs 任一端缺失则不显示该段 | packages/tui/src/overlays/usage-row.ts:39-57 |
| omp | Move to directory | /move | 卡片标题 Move to directory；Path 输入行 + 实时过滤的目录建议列表(≤15 行)，选中行 ▶ 前缀（注：/move 改工作目录的小浮层，path/工作目录相关） | Esc 取消；无匹配显示「No matching directories」 | packages/tui/src/overlays/move-overlay.ts:37-44,39-160,202 |
| omp | 交互键位 | 输入/上下键/Tab/Enter | ↑↓选择建议，Tab 接受高亮建议，Enter 确认当前输入(或空输入时的建议)（注：/move 交互键位） | 确认或取消后关闭 | packages/tui/src/overlays/move-overlay.ts:24-36,86-125 |
| omp | separator=pipe | settings 选 pipe | 以 '｜' 分隔，无端帽 | — | packages/tui/src/status-line/separators.ts:17 |
| jcode | 会话状态行（overscroll，输入下方 1 行） | 恒显示（宽>0） | dir · branch · git ±n · context k/k ▰▰▱▱ % · auth · provider · model effort | 窄屏按阶梯丢：auth→git→bar→branch→provider→%→git→branch→effort→dir | crates/jcode-tui/src/tui/ui_input.rs:1946-1990,1996-2036,2152-2180 |
| jcode | Overview（Overview / Overview · todos / Overview · memory） | has_data_for 要求明细 section≥2（runtime/todos/background/usage/kv/compaction/git，queue_mode 也算 1）；右侧、最小高 8 | 多页轮播（每 30s 翻页）：CompactOnly 汇总 / TodosExpanded / MemoryExpanded；底部 ●○ 页点；体内各行按 section 拼（Runtime、Todos、背景、Usage、KV cache、Changes） | 页高 > 可用高则退回 CompactOnly，再不行整块消失；show_dots 只在 >1 页时；body 行 truncate 到 inner.height | crates/jcode-tui/src/tui/info_widget.rs:757-800, crates/jcode-tui/src/tui/info_widget_overview.rs:26,103, crates/jcode-tui/src/tui/info_widget.rs:1268 |
| jcode | UsageLimits（<Provider> limits / 💰 $x / Copilot tokens） | usage_info.available；左侧、最小高 3；订阅额度 ≥50% 提前（effective_priority 3），≥80% 提到 1 | 每窗口一行：7 字标签+▰▱条+“62% left · 4h5m”；CostBased 单行 in/out，$ 总额在顶边；Copilot 单行 in+out | 窄时先丢 reset 倒计时、再丢条长度；available=false 即消失 | crates/jcode-tui/src/tui/info_widget.rs:830, crates/jcode-tui/src/tui/info_widget_usage.rs:11,164 |
| jcode | KvCache（KV cache） | cache_hit_info 有值；左侧、最小高 3，记忆处理中会提优先级 | 顶边 KV cache N% yield；体行 last N% · session N%；miss 行 N> 12k miss (reason) 最多 5 行；底边合计 missed 或 no misses（注：doubt: cache 事实；亦涉 M9 缓存） | miss 列表 >5 只留 5 行，左下 +N more；无 cache 遥测即消失 | crates/jcode-tui/src/tui/info_widget.rs:1560,1642 |
| jcode | ModelInfo（Runtime） | runtime_has_data：service tier(OpenAI)/upstream/transport/tps(>0.1)/session 名或 count>1；左侧、最小高 1 | 边框 Runtime 左上、⏱ N tok/s 右下；体行图标+文本：⚡ fast tier/☁ via X/↔ websocket/⏱ N tok/s/◆ session · N sessions | token/s 独占时留在体内不进边框；无任何 runtime 事实即消失（模型/上下文/分支属状态行，不在此） | crates/jcode-tui/src/tui/info_widget_model.rs:14,31,91 |
| jcode | Compaction（Compaction compacting/compacted） | compaction_info 有值（本会话原生压缩或已压缩>0）；左侧、最小高 3；compacting 时优先级提到 2 | 边框：Compaction + 状态词（琥珀 compacting/绿 compacted），右上 mode；体行 “N old · N active · ~N summary tok” | 仅 1 体行自适应宽度截断；无压缩信息即消失 | crates/jcode-tui/src/tui/info_widget.rs:1534,1547 |
| jcode | GitStatus（Changes） | git_info.dirty_files 非空；左侧、最小高 1 | 边框 Changes 左上、+A −D 全量右上、（有）agent 圆点图例右下、+N more 左下；体行 `M● path  +84 −12`（最多 5 文件）（注：doubt: git 事实带；亦涉 S5 仓库） | 超 5 个文件折 +N more；窄时先丢 +/− 计数再截路径；无脏文件（仅 ahead/behind）即消失 | crates/jcode-tui/src/tui/info_widget.rs:842, crates/jcode-tui/src/tui/info_widget_git.rs:13,107,122 |
| jcode | Commits（Commits） | 最新提交 unpushed 或 <24h（COMMITS_FRESH_SECS）；左侧、最小高 1 | 边框 Commits 左上、↑N unpushed 右上、+N more 左下；体行 `● hash subject  +a −r  2m`（最多 5 行）（注：doubt: git 事实带；亦涉 S5 仓库） | 超 5 行折 +N more；窄时先丢 +/− 统计、再丢时间；陈旧且已推即消失 | crates/jcode-tui/src/tui/info_widget.rs:846, crates/jcode-tui/src/tui/info_widget_commits.rs:10,31,39,55 |
| jcode | 数据闸 has_data_for / available_widgets | 每帧算：按 all_by_priority 过滤 has_data_for，再按 effective_priority 排序放置 | 15 个 kind 的 15 条数据判据（见①）；AmbientMode/Tips 恒 false | 无一命中则整块 margin 挂件区为空 | crates/jcode-tui/src/tui/info_widget.rs:749,881,889 |
| jcode | 静态优先级 priority() | 无动态状态时使用 | Diagrams0 > Workspace1 > Overview2 > Todos3 > Usage5 > KvCache6 > Memory7 > Model8 > Compaction9 > Background10 > Git11 > Commits/Swarm12 > Ambient13 > Tips14 | 低优先级后放，空间不够就没槽 | crates/jcode-tui/src/tui/info_widget.rs:124-142,187-203 |
| jcode | 动态优先级 effective_priority() | 每帧 | Memory 处理中→0；Usage≥80%→1、≥50%→3；Compaction 进行中→2；Swarm 在管 agent→3 | — | crates/jcode-tui/src/tui/info_widget.rs:844-880 |
| jcode | 侧别 preferred_side() | Phase 2 打分 +1000 | 右：Diagrams/Workspace/Overview/Todos/Memory；左：其余(Swarm/Compaction/Background/Ambient/Usage/KvCache/Model/Tips/Git/Commits) | 偏侧无槽时落另一侧 | crates/jcode-tui/src/tui/info_widget.rs:145-163 |
| jcode | 最小高度 min_height() | Phase 2 要求 pocket 高 ≥ min_height+2（边框）且宽 ≥24 | Diagrams10、Overview8、Todos/Memory/Swarm/Compaction/Ambient/Usage/KvCache/Tips3、Background2、Workspace/Model/Git/Commits1 | 不足则本轮不放置 | crates/jcode-tui/src/tui/info_widget.rs:166-184, crates/jcode-tui/src/tui/info_widget_layout.rs:9,11 |
| jcode | 空间常量 MIN/MAX | 每帧 | MIN_WIDGET_WIDTH=24、MAX_WIDGET_WIDTH=40、MIN_WIDGET_HEIGHT=5；centered 模式才启用左侧 margin | 宽<24 的 pocket 不承载；>40 截到 40 | crates/jcode-tui/src/tui/info_widget_layout.rs:6,8,10,131 |
| jcode | Phase 1 锚定（resident） | 上一帧已有 anchor 且 kind 仍有数据 | 钉在同一 transcript 行(content_top)随滚动漂移；宽只缩不涨；被宽行盖住则原地隐藏 | 隐藏 >MAX_HIDDEN_FRAMES=120 帧才弃锚重新安置 | crates/jcode-tui/src/tui/info_widget_layout.rs:17,240-345 |
| jcode | Phase 2 贪婪安置 | 无锚（新出现/被弃） | 在空矩形里选 (偏侧+1000 − 面积/10) 最高；坐在 pocket 底部；剩余空间继续留给下一个挂件 | 无 pocket 即本轮不显示 | crates/jcode-tui/src/tui/info_widget_layout.rs:347-440 |
| jcode | Overview 合并抑制 | Overview 被放置或仅隐藏中 | is_overview_mergeable 的 8 个(Todos/Swarm/Background/Compaction/Model/Usage/KvCache/Git)全部不出现 | Overview 真正无槽时才回退显示这些小挂件 | crates/jcode-tui/src/tui/info_widget.rs:238-249, crates/jcode-tui/src/tui/info_widget_layout.rs:225,349 |
| jcode | 总开关 toggle_enabled / is_enabled | 用户关闭挂件 | calculate_placements 直接返回空 | 关闭期间无挂件 | crates/jcode-tui/src/tui/info_widget.rs:1005,1014,982 |
| jcode | Usage 卡（/usage 的实际呈现） | /usage（先加载卡，随后原地 upsert）；无连接 provider | 圆角框“Usage”：`# Refreshing usage (c/t)` / `# Usage updated · N source(s)`；每 provider 一行 `+ / ~ / ! 名称 - N% used`；每限额“名称: ▓▓░░ 14格 · resets in …”；extra key: value；error:/hard limit/no data；空→“# No connected providers”（注：doubt: 用量卡；亦涉 S9） | 同标题“Usage”卡原地替换内容；不截获输入 | crates/jcode-tui/src/tui/ui_messages.rs:686；内容 crates/jcode-tui/src/tui/app/model_context.rs:1198 |
| jcode | Remote·顶栏 client 徽标/连接图标/服务器身份 | is_remote（含 SSH） | 状态项“client”（replay 时为“replay”）；会话名图标 + 连接图标；服务器名/图标/版本，有更新时附加提示（注：doubt: 顶栏身份状态） | 窄屏省略/截断 | crates/jcode-tui/src/tui/ui_header.rs:645-661 |
| jcode | usage 卡 | role=usage（/usage 等，仅显示不入模型上下文） | 圆角边框卡，标题 Usage + token/额度统计 | 无 | crates/jcode-tui/src/tui/ui_messages.rs:686 |
| jcode | overscroll 状态行 | 始终存在（输入下方 1 行） | dir · branch · git(`~m +s ?u ↑a ↓b`) · context bar ▰▱ +% · auth · provider · model · effort | 按宽逐级降级：先丢 auth → git 合并为 ±N → context 只留百分比 → branch 截 12 字 → 丢 provider | crates/jcode-tui/src/tui/ui_input.rs:1946 |
