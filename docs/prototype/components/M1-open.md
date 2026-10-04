# 组件 · M1 开场与空闲（还没输入时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 6 条 · jcode 6 条

## 两家在这一刻的对照（事实）

- omp 6 条 / jcode 6 条；omp 把开场 welcome 拆成多个小节逐块铺开（品牌/版本/Tips/LSP/Recent/Tip）；jcode 没有整块开场，只在空闲时偶发提示（历史提醒/tip/动画行）

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Welcome 品牌列 omp.welcome.brand | 会话启动（含 intro 动画） | "Welcome back!" 居中 + omp logo（终端内置图像，渐变着色） | intro 结束后缓存为静止帧 | packages/tui/src/prompt/welcome.ts:240 |
| omp | Welcome 版本行 | 会话启动 | dim mono 版本号 | 常驻 | packages/tui/src/prompt/welcome.ts:268 |
| omp | Tips 小节 | 会话启动 | 4 个 keycap：# 提示动作 / / 命令 / ! bash / $ python | 常驻 | packages/tui/src/prompt/welcome.ts:269 |
| omp | LSP servers 小节 | 会话启动且 lspServers !== null（null 隐藏整节） | 最多 4 行：● 状态 + 名字 + ≤3 个 fileType badge；无则 "No LSP servers" | 空槽补空行以固定高度 | packages/tui/src/prompt/welcome.ts:276 |
| omp | Recent sessions 小节 | 会话启动 | 最多 4 行：名字 + (timeAgo)；无则 "No recent sessions" | 超槽不画 | packages/tui/src/prompt/welcome.ts:307 |
| omp | Tip 行 | 会话启动；[NEW] tip 抽样权重×4 | "Tip: …" 一行；[NEW] tip 带彩虹闪光 "NEW!"；unicode 预设 10% 显示 nerdfont 唠叨 | 常驻 | packages/tui/src/prompt/welcome.ts:633 |
| jcode | 空闲 · 会话历史提醒 | 未处理且总 token 达标（≥context/250k，宽≥64，进入 token 窗口且 300s 周期内 10s 窗口） | `⚠ Session history: {tokens} tokens processed{and N compacts}; /clear…` | 超时/超窗口，或 >3×context/3 次压缩转红 | crates/jcode-tui/src/tui/ui_input.rs:578-618,1079-1105 |
| jcode | 空闲 · 偶发 tip | 未处理，动画周期 90s 内 [28s,40s) | `💡 {tip}` dim，宽<16 不显示 | 周期窗口外 | crates/jcode-tui/src/tui/info_widget_tips.rs:3-6,58-77 |
| jcode | 空闲 · 空行 | 未处理且无上述内容 | 空 Line | — | crates/jcode-tui/src/tui/ui_input.rs:1096-1104 |
| jcode | 空闲 donut 动画行 | 空闲动画激活 | 14 行动画，随 composer 变高而收缩（注：doubt: 空闲动画；亦涉 M12 动画） | 输入变高时按 composer_growth 缩减 | crates/jcode-tui/src/tui/ui_animations.rs:281-288 |
| jcode | Tips（💡 Did you know?） | 【用户看不到】已被硬禁用：widget_disabled 恒真 → 永不作为 margin 挂件出现 | (渲染函数存在) 顶边 💡 Did you know?、体内按宽折行的轮换提示——但不可达（注：【用户看不到】死路径(已被硬禁用); doubt: 【用户看不到】死路径；空闲提示挂件） | 恒不出现；提示改由状态行偶发显示 | crates/jcode-tui/src/tui/info_widget.rs:732,1539, crates/jcode-tui/src/tui/info_widget_tips.rs:58,107, crates/jcode-tui/src/tui/ui_input.rs:1054 |
| jcode | idle donut / orbit_rings | 空屏 idle 且 display.idle_animation=true 且未 processing/无流式且终端聚焦 | 输入下方最多 14 行动画（变体随机：donut 或 orbit_rings，可用 disabled_animations 禁） | composer 变高即从预留高度扣减，最低 0 行；开始对话即消失 | crates/jcode-tui/src/tui/ui_animations.rs:281 |
