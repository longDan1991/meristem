# 屏幕 · 模型与给养（选模型、给模型喂料所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S2：omp 10 条 · jcode 1 条

## 两家在这一刻的对照（事实）

- omp 10 条 / jcode 1 条；omp 的模型选择体系很厚（Thinking Level、Switch Model 浮层、Models hub、Roles、provider 刷新、ModelBrowser），jcode 只有 Model Status overlay（/provider-test-coverage）一处。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Thinking Level 选择器 | 【用户看不到】packages/*/src 内无实例化点 | 面板标题 Thinking Level；SelectList 列出各 thinking 等级，预选当前等级，picker 形态标题 Thinking level（注：【用户看不到】无实例化点（死路径）） | Esc 取消 | packages/tui/src/overlays/thinking-selector.ts:13-64 |
| omp | Switch Model 浮层 | alt+p 或 /switch；临时模型选择 | 底部锚定非全屏浮层：搜索行 + 模型列表 + 两行详情；当前模型高亮预选；前导 @ 搜索 ctrl+p 快捷角色 | Esc 关闭；高度占终端 40%(HEIGHT_FRACTION)，列表窗口最少 5 行 | packages/tui/src/overlays/model-picker.ts:81-114,94-113,395-470 |
| omp | 底部 hint 行 | 按模式(session/role/task)变化 | 「↑↓ 角色 · enter apply role model · type to search · esc close」等 | 模式切换即刷新 | packages/tui/src/overlays/model-picker.ts:94-108 |
| omp | Models 全屏 hub | /model 或 alt+m（showModelHub，全屏 alt-screen + 鼠标跟踪） | 全屏「Models」：左侧 sidebar(Roles n/m、All models N、Recent N、各 provider) + 右侧 body(状态行、kind tabs、模型列表)；焦点 scope/list 用 ←/→ 或 Tab 切换 | Esc 关闭(dispose) | packages/tui/src/overlays/model-hub.ts:283-300,313-360,638-644 |
| omp | Roles 视图 | sidebar 选中 Roles | 角色行(Model/Thinking 列)，≥PRESERVED 滚动窗口跟随光标；可赋值/循环 | Esc 返回 | packages/tui/src/overlays/model-hub.ts:232-235,344-352 |
| omp | provider 刷新 | 选中某 provider（首次自动刷新）或按 F5 | 状态行 spinner + 每个 provider 的匹配数/模型列表 | 刷新完成后 spinner 消失 | packages/tui/src/overlays/model-hub.ts:276-290,207-232 |
| omp | 原生 picker 形态 | 终端支持 picker | sheet「Models」：scopes、kind tabs、模型 rows、preview=side；roles 时 noun=roles | Esc 关闭 | packages/tui/src/overlays/model-hub.ts:3019-3027,3147-3164 |
| omp | ModelBrowser 列表块 | 宿主(model hub/agents hub/model picker)展示模型时 | 固定高度块：搜索行 + 空白 + 列表窗口(maxVisible 默认 10) + 空白 + 两行详情 | 行宽 <76 无 perf 列；≥76 显示 t/s；≥96 显示 TTFT | packages/tui/src/overlays/model-browser.ts:812-819,827-870 |
| omp | 模型行 / 详情 | 列表渲染 | 行：模型名 + selector(可点复制) + current badge + 角色 badge + description；原生列 Int/t/s/Ctx/$/M | 窄屏按 priority 逐列丢弃；详情区固定 3 行 | packages/tui/src/overlays/model-browser.ts:685-690,1936-1990 |
| omp | model 字符串/后缀解析 | 【用户看不到】解析 provider/model、:thinking 后缀、@upstream 路由 | parseModelString/splitThinkingSuffix/splitUpstreamRouting/formatModelSelectorValue（注：【用户看不到】纯解析 helper） | — | packages/tui/src/overlays/model-selector.ts:1-140 |
| jcode | Model Status overlay（/provider-test-coverage） | /provider-test-coverage [provider model]；有/无验证台账 | 框“ /provider-test-coverage ”；“Model Status”+副标题，正文按 pass绿/fail红/warn黄/dim灰着色；底部“↑/↓…c copy…q/Esc” | q/Esc 关闭；c 复制全文；↑↓/PgUp/PgDn/g/G 滚动 | crates/jcode-tui/src/tui/ui_overlays.rs:665；分派 ui.rs:2738 |
