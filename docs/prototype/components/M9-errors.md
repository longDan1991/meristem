# 组件 · M9 出问题的时候（出错时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 11 条 · jcode 10 条

## 两家在这一刻的对照（事实）

- omp 11 条 / jcode 10 条；omp 以错误卡/横幅 + late diagnostics + 错误块格式函数；jcode 以连接类横幅（KV cache 警告/网络重试/Remote 连接丢失/Connection 卡/error 行/File conflict）

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | 粘贴降级错误 | 大粘贴保存为文件失败 | "Failed to save paste to a file — attached as a text chip instead" | 被后续状态覆盖 | packages/coding-agent/src/modes/controllers/input-controller.ts:2571 |
| omp | 回合内联错误块（Error: …） | 回合以 stopReason=error/aborted 结束 | 'Error: ' 首行 + 续行缩进 2 格；最多 8 行，超出行尾 '… +N more lines (ctrl+o to expand)'（注：回合以错误/中止结束时的内联错误块） | Ctrl+O 展开为全文；同一错误被钉在 banner 时不重复显示 | packages/tui/src/chat/assistant-message.ts:1287 |
| omp | 图片不可用占位 | showImages=false 或协议不支持 | imageFallback(mime, 尺寸) 的 muted 文本如 '[image 800x600]' | 协议可用时替换为真实图 | packages/tui/src/chat/bash-execution.ts:186 |
| omp | Write/Edit 的 late diagnostics 内联段 | native 终端、结果后到达 LSP 诊断 | 诊断树追加到所属 edit/write 帧内（每文件一行/多条）（注：LSP 迟到诊断内联进工具帧） | 路由不进任何帧的才落到独立 Late diagnostics 卡 | packages/tui/src/chat/late-diagnostics-message.ts:44 |
| omp | errorBannerContainer / ErrorBannerComponent | 回合以 provider 错误结束 | 红边框钉在编辑器上方：'✘ 首行'，最多 MAX_BANNER_ROWS=4 行；native 有 Details/Dismiss 按钮 | 下一回合开始时清除；native Dismiss 立即消失 | packages/tui/src/overlays/error-banner.ts:26 |
| omp | Late diagnostics 卡 | edit/write 返回后才到的 LSP 诊断（未内联进工具帧） | severity 色卡头 'Late diagnostics (summary)' + 每诊断一行 mono；折叠窗口 5 行（注：迟到 LSP 诊断卡） | 展开显示全树；toolActivityVisible=false 时整卡隐藏 | packages/tui/src/chat/late-diagnostics-message.ts:13 |
| omp | errorBannerContainer | showPinnedError（回合以 provider 错误收尾） | ErrorBannerComponent：红边条+首行错误+'Dismissed when you send your next message.' 底部提示 | 发送下一条/clearPinnedError 即清空 | packages/coding-agent/src/modes/interactive-mode.ts:7253 / tui/src/overlays/error-banner.ts:26 |
| omp | LateDiagnosticsMessageComponent | edit/write 返回后 LSP 迟到诊断；native 优先并入工具卡 | 卡「Late diagnostics (summary)」+每诊断 1 行 mono | 折叠 5 行；hideToolActivity 隐藏 | packages/tui/src/chat/late-diagnostics-message.ts:69 |
| omp | error-block.ts (formatErrorBlock / sanitizeErrorLine) | 内联错误块与固定错误横幅 | 换行到内容宽、最多 maxRows 行，末行「… +N more lines (ctrl+o to expand)」（注：错误块/错误横幅的格式函数） | 超 maxRows 折叠；空文本→「Unknown error」 | packages/tui/src/chrome/error-block.ts:34 |
| omp | 错误横幅 | 一轮以 provider 错误结束时自动钉在输入框上方；下一轮开始清除 | 红边条：首行加粗 + 正文最多 4 行(MAX_BANNER_ROWS) + 底部「Dismissed when you send your next message.」 | 下一轮开始时消失；超出 4 行显示展开提示 | packages/tui/src/overlays/error-banner.ts:11-48 |
| omp | 原生 strip | 原生渲染 | 首行 headline + Details(展开全文)/Dismiss 按钮 | Dismiss 或下一轮 | packages/tui/src/overlays/error-banner.ts:50-90 |
| jcode | streaming KV cache 警告 | detect_kv_cache_problem 命中 | `⚠ {Nk} cache miss · ` 前缀，整行转黄（注：doubt: 缓存告警；也可视为 M6 在动） | 缓存恢复/turn 结束 | crates/jcode-tui/src/tui/ui_input.rs:915-929,1114-1132 |
| jcode | 等待网络重试 | ProcessingStatus::WaitingForNetwork{listener} | `↻ network disconnected, waiting to retry · {listener} · {elapsed}` 黄(+queued)（注：doubt: 断线重试；M6 也含网络/限流） | 网络恢复 | crates/jcode-tui/src/tui/ui_input.rs:936-950 |
| jcode | 实验特性告警（在活动行内） | active_experimental_feature_notice 存在 | ` · ⚠ {notice}` 黄粗体（注：doubt: 活动行内告警，偏 M9 告警） | 特性关闭 | crates/jcode-tui/src/tui/ui_input.rs:996-1002 |
| jcode | 闪烁提示 + 复制徽标 | 检测到 flicker 且未过期 | `⚠ flicker detected (kind)` + `logs: …` + `[Alt][⇧][X]`+复制反馈 | 超 FLICKER_UI_NOTICE_MAX_AGE_MS 消失 | crates/jcode-tui/src/tui/ui_input.rs:1691-1747; ui_frame_metrics.rs:1222-1250 |
| jcode | 🧊 cache cold / ⏳ cache 将过期 | 非处理中且 cache_ttl 通知激活 | 冷=`🧊 cache cold ({tok}) {age}`；将过期=`⏳ cache {t}{tok}` 黄 | TTL 刷新/过期结束 | crates/jcode-tui/src/tui/ui_input.rs:1794-1845 |
| jcode | Remote·连接丢失横幅（系统消息，原地更新） | 断线重连中（非首连失败） | “⚡ Connection lost - retrying (attempt N, Xs) - 原因 · resume: jcode --resume <name>”（SSH 时“… · SSH host · remote session id”） | 重连成功后原地替换为成功/继续消息 | crates/jcode-tui/src/tui/app/remote/reconnect.rs:90/123；写入 :175 |
| jcode | Remote·reload 交接横幅 | 服务端 reload 交接等待中 | “⚡ Server reload in progress - waiting for handoff (Xs) - detail · resume…” | 交接完成或转为重连成功 | crates/jcode-tui/src/tui/app/remote/reconnect.rs:132/169 |
| jcode | Connection 卡 | 断连/重连/reload handoff，或标题为 Connection | 圆角边框卡包裹连接状态正文 | 恢复后由后续消息取代 | crates/jcode-tui/src/tui/ui_messages.rs:2472 |
| jcode | error 行 | role=error，出错时 | 错误文本行 + 行级复制目标 | 无 | crates/jcode-tui/src/tui/ui_prepare.rs:1718 |
| jcode | File conflict · <sender> | 文件冲突告警 | `⚠ ` 放在 icon 之前 + 正文（冲突色）；带文件活动语义（注：doubt: 冲突告警卡） | 同 diff 徽标折叠 | crates/jcode-tui/src/tui/ui_messages.rs:2990 |
