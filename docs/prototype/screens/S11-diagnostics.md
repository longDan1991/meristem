# 屏幕 · 诊断与调试（诊断与调试所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S11：omp 39 条 · jcode 2 条

## 两家在这一刻的对照（事实）

- omp 39 条 / jcode 2 条；omp 条目最多：ps 进程表、cleanse、checker、Repair、if-bench、Debug/Recent Logs 诊断工具齐备；jcode 只有 observe 页与 Visual debug overlay。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | ps 头部 | 表格视图 | 左 `omp ps · N processes in M scopes (kind)`；右 `updated X ago` 或 updating | 换视图即换标题 | packages/tui/src/apps/ps-top.ts:632 |
| omp | 进程表 | 表格视图且有 broker scope | 每 scope 一个标题块 + 表头 NAME/STATE/PID/UPTIME/RESTARTS/FLAGS/COMMAND + 每进程一行；选中行反显 `❯` | 随刷新增删行；空 scope 显示 no processes | packages/tui/src/apps/ps-top.ts:645 ; ps-data.ts:92 |
| omp | 终结态进程行 | state=exited/failed | 整行 dim；STATE 显示 `exited(143)` | 进程被清理后消失 | packages/tui/src/apps/ps-data.ts:61 |
| omp | ps 空态 | 没有任何 broker scope | 居中 `No broker scopes` + 提示按 a 看全部 scope | 出现 scope 即消失 | packages/tui/src/apps/ps-top.ts:531 |
| omp | ps 状态行 | 动作后 5 秒内 | `stop x…` / `Restarted name: ready pid=…` / `x kill failed: …`，按语调着色 | 5s TTL 后清空 | packages/tui/src/apps/ps-top.ts:640 |
| omp | ps 页脚键提示 | 始终 | `↑↓ select · enter info · l logs · s stop · x kill · r restart · a all scopes · q quit` | 换视图换提示 | packages/tui/src/apps/ps-top.ts:645 |
| omp | Kill 确认行 | 指针点 Kill（键 x 不确认） | `Kill name (pid N)? It stops at once, without cleanup.` + Cancel / Kill | Cancel 或确认后消失 | packages/tui/src/apps/ps-top.ts:486 |
| omp | ps info 视图 | enter/i 或双击行 | name + 状态徽标 + Command/Directory/PID/Exit/Restarts/Owner/Flags 网格 + Up for；Back/Logs | esc/q 回表格 | packages/tui/src/apps/ps-top.ts:573 |
| omp | ps logs 视图 | 按 l | `logs name · state` + 1s 轮询、尾随的日志体 | esc/q 回表格并停止轮询 | packages/tui/src/apps/ps-top.ts:606 |
| omp | ps 原生页（Tern） | Tern 渲染路径 | head（计数、scope tabs、刷新/spinner、关闭）+ 每 scope 分组 list + 状态 + 动作条 | 同 ANSI 视图切换 | packages/tui/src/apps/ps-top.ts:351 |
| omp | ps 原生进程行 | Tern 表格 | name + launch command + `state · pid · uptime · N restarts · flags` + 状态图标 | 行随 list 增删 | packages/tui/src/apps/ps-top.ts:814 |
| omp | cleanse 目标选择器 | `omp cleanse` 交互式且未指定目标 | `Run all N discovered checkers` + 每个 checker（label + `lang — cmd`）+ `Describe what to fix…`，最多 12 行（注：独立 omp cleanse 工具屏内的目标选择） | 选中或取消即关闭 | packages/tui/src/apps/cleanse-picker.ts:27 |
| omp | cleanse 自由描述输入 | 选中 `Describe what to fix…` | 提示 `Describe what to detect and fix (e.g. "ts errors"):` + 输入框（注：独立工具屏内的描述输入） | 提交或取消 | packages/tui/src/apps/cleanse-picker.ts:63 |
| omp | cleanse 阶段行 | 模型解析 / checker 发现中 | spinner + phase 文案（转瞬）（注：诊断进行中的阶段行） | 阶段结束即清 | packages/tui/src/apps/cleanse-board.ts:264 |
| omp | checker 运行行 | 每个 checker 运行中 | spinner + label + 已用时长（注：checker 运行行） | checker 完成后移除 | packages/tui/src/apps/cleanse-board.ts:264 |
| omp | checker verdict 行 | checker 完成 | `✓ label clean · 1.2s` 或 `● label N issues · 时`，上滚为固定行（注：checker 结果行） | 永久保留在 scrollback | packages/tui/src/apps/cleanse-board.ts:123 |
| omp | Repair 头 | 进入修复阶段 | `Repairing [██░] 3/8 · 2 running · 12k tok · $0.01 · 1m02s`；native 用 meter `3/8 lanes`（注：修复阶段进度头） | repairFinished 时消失 | packages/tui/src/apps/cleanse-board.ts:232 |
| omp | repair agent 行 | 每个修复子代理运行中 | spinner + 名 + 文件(`a.ts +2`) + 最新 intent + 当前工具+args + 工具数 + 时长（注：修复子代理运行行） | agentFinished 即移除该行 | packages/tui/src/apps/cleanse-board.ts:383 |
| omp | repair agent 原生 lane | Tern 且支持 agent 节点 | `agent` 行：task=文件、status、model、tool+intent+age、retry、tokens/cost/工具数/时长（注：修复子代理原生 lane） | 同上 | packages/tui/src/apps/cleanse-board.ts:408 |
| omp | repair outcome 行 | 子代理结束 | `✓ name files · 3 tools · 12k tok · 8s` / `✗ name files <错误>`（注：修复子代理结果行） | 永久滚动行 | packages/tui/src/apps/cleanse-board.ts:498 |
| omp | 非 TTY 行协议 | 非交互终端 | `[start] name: files (weight N)` / `[done] name (model)` / `[fail] name: msg`（fail 走 stderr）（注：非交互输出行） | 逐行输出，无重绘 | packages/tui/src/apps/cleanse-board.ts:322 |
| omp | if-bench 头部 | 有模型在跑 | spinner + `if-bench · N live · X actions · L=… nya{1,…} · 时长`（注：独立 if-bench 工具屏头部） | 无 live 行即消失 | packages/tui/src/apps/if-bench-board.ts:162 |
| omp | 模型 turn ladder 行 | 每个模型运行中 | spinner + label + 梯形格（█通过 / spinner 当前 / ▚失败 / ░剩余，≤28 格）+ `turn x/y · N acts · 时长 · cat@pos`（注：模型 turn 梯形格） | 模型结束后移除整行 | packages/tui/src/apps/if-bench-board.ts:216 |
| omp | 模型 verdict 行 | 模型跑完 | `✓ label 5/10 turns · 12 actions · 1.2s/turn · 3k tok · $0.02` 或 `✗ … broke on turn 7: <原因>`（注：模型结果行） | 永久保留 | packages/tui/src/apps/if-bench-board.ts:235 |
| omp | 失败原因文案 | 有 failure | wrong array / no cat sound / wrong array + no cat sound / no <result> block / provider error（注：失败原因） | 随 verdict 一起永久 | packages/tui/src/apps/if-bench-board.ts:235 |
| omp | 失败明细行 | 有 failure | `expected <…>` + `actual …`（provider 只一行），各 120 列截断（注：失败明细） | 永久保留 | packages/tui/src/apps/if-bench-board.ts:272 |
| omp | 非 TTY 回合行 | 非交互输出 | `[turn N] label N acts cat@pos PASS/FAIL 1.2s`（FAIL 走 stderr）（注：非交互回合行） | 逐行输出 | packages/tui/src/apps/if-bench-board.ts:106 |
| omp | 总排行榜 | 跑完的收尾（json=false） | 表 model/turns/actions/broke on/per turn/tokens/cost，第一名绿色（注：最终排行榜） | 一次性输出 | packages/tui/src/apps/if-bench-board.ts:281 |
| omp | Debug 菜单 | `/debug`（或 TUI 调试键） | `Debug Tools` 面板：13 项 SelectList，窗口 7 行 | 选中或 esc 关闭 | packages/coding-agent/src/debug/index.ts:41 |
| omp | Recent Logs 面板 | 菜单 `View: recent logs` | 标题 Recent Logs；头 2 行（showing/selected/expanded 统计 + filter/pid）；体滚动行；脚 2 行（状态 + 键提示） | esc 关闭回菜单 | packages/tui/src/apps/debug/log-viewer.ts:909 |
| omp | 日志行 | 有日志条目 | `❯/•/空` + `▸/▾` 折叠标记 + 内容；展开为多行 JSON 缩进 | 被过滤掉的行隐藏 | packages/tui/src/apps/debug/log-viewer.ts:913 |
| omp | 会话边界警告 | 存在早于本进程的日志 | `### WARNING - Logs above are older than current session!` | 无更早日志不插 | packages/tui/src/apps/debug/log-viewer.ts:25 |
| omp | Load older 行 | 还有更早条目 | `### MOVE UP TO LOAD MORE...`，可选中，回车加载 | 无更早则消失 | packages/tui/src/apps/debug/log-viewer.ts:27 |
| omp | Logs picker sheet | Tern 且支持 picker | `Recent logs`：query 过滤、每行 message/detail/time/pid/level dot、`This session` 分组、下方 JSON 预览 | esc 关闭 | packages/tui/src/apps/debug/log-viewer.ts:765 |
| omp | Raw Provider Stream 面板 | 菜单 `View: raw SSE stream` | 标题 Raw Provider Stream；头 counters（events/records/dropped）；体 SSE 文本跟随尾部；脚 Copy raw/关闭 | esc 关闭 | packages/tui/src/apps/debug/raw-sse.ts:251 |
| omp | SSE 空态 | 尚未捕获任何帧 | 居中 `No raw SSE frames captured yet` + 说明 | 有帧即换 | packages/tui/src/apps/debug/raw-sse.ts:251 |
| omp | Terminal Protocol Test 块 | 菜单 `Test: terminal protocols` | SGR 样式 + truecolor 色条、OSC8 链接、OSC66 2x/3x 大字、Graphics 图片、Notification 结果行 | 留在正文滚动区 | packages/tui/src/apps/debug/protocol-probe.ts:186 |
| omp | Terminal State 块 | 菜单 `View: terminal state` | Detected/Geometry/Multiplexer + Subprotocols + Scrollback + 检测环境变量 | 留在正文滚动区 | packages/tui/src/apps/debug/terminal-info.ts:89 |
| omp | debug 面板外框 | log-viewer / raw-sse 视图 | 圆角面板 + 分隔线 + accent 滚动条，头/体/脚三段 | 关视图即撤 | packages/tui/src/apps/debug/viewer-frame.ts:42 |
| jcode | observe 页（Observe，ephemeral） | /observe on；只跟最新一条非 bookkeeping 工具调用/结果 | 标题 Observe；- Tool/Status/Returned to context N tok · N chars[ large]；## Tool input(JSON) / ## Tool output(fenced)（注：doubt: 观察工具活动，探针类） | off 即移除；等新活动时显示 Waiting 占位 | crates/jcode-tui/src/tui/app/observe.rs:7,46,208,243 |
| jcode | Visual debug overlay | 视觉调试开启（/debug-visual） | messages/queued/status/picker/input/donut 六色框 + 每个 widget:<kind> 框 | 关闭调试；chunks<5 不画 | crates/jcode-tui/src/tui/ui_overlays.rs:734；分派 ui.rs:3553 |
