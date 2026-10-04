# 屏幕 · 首启与帮助（首启与帮助所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S12：omp 15 条 · jcode 16 条

## 两家在这一刻的对照（事实）

- omp 15 条 / jcode 16 条；omp 是 setup splash/wizard（场景全屏、compact/startup splash、溶解转场、Model/Glyph/Composer/Theme 场景）；jcode 是 Changelog/Help overlay 与 Onboarding（遥测声明、Login 导入、Telemetry 子页）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | setup splash（场景全屏） | 向导 phase=splash（2.6s） | 2x π 标志 + 对角渐变/闪光、波纹水面、星空，底部 `press enter to skip` | 按键或到时后溶解进场景 | packages/tui/src/setup/scenes/splash.ts:122 |
| omp | compact splash | 窗口 <56x22 | 居中标志（≥14 行用 2x）+ `O h   M y   P i` + skip 提示 | 同 splash 退出条件 | packages/tui/src/setup/scenes/splash.ts:212 |
| omp | startup splash（独立） | 首启且配置允许、交互非续话 | 同一 splash 动画；enter/space/esc 可跳过 | 到时或按键后撤 overlay | packages/tui/src/setup/startup-splash.ts:65 |
| omp | wizard 场景框 | phase=scene（或 transition 结束） | 居中 logo + APP_NAME + `Setup step i of N` + 标题/副标题 + 场景 body + 居中键提示 | 换场景或进 outro | packages/tui/src/setup/wizard-overlay.ts:277 |
| omp | transition 溶解 | splash→场景的 0.42s | 逐行自顶向下把 splash 翻成场景（带抖动） | progress=1 进 scene | packages/tui/src/setup/wizard-overlay.ts:180 |
| omp | setup outro | 所有场景跑完（1.2s） | 星空 + 标志 + `✓ Setup saved` + `Handing off to the normal CLI…` + 进度扫条 | 到时回正文 CLI | packages/tui/src/setup/scenes/outro.ts:36 |
| omp | Sign in 场景 | minVersion 1 且需登录（需 TTY） | 提示 `Pick a provider to sign in…` + OAuth provider 列表 + 状态区；可连多个（注：setup 向导里的登录场景；疑点：登录亦近 S9） | esc 跳过，子场景结束 | packages/tui/src/setup/scenes/sign-in.ts:150 |
| omp | 登录中面板 | 正在走 OAuth | spinner `Signing in to X` + Browser login 链接（可 alt+c 复制）+ 本机 shortcut + code 输入框 + 进度行（注：setup 登录中面板；疑点：亦近 S9） | 登录成功/失败/取消后收起 | packages/tui/src/setup/scenes/sign-in.ts:226 |
| omp | 登录结果状态行 | 登录有结果 | `✓ Signed in to X` + `Credentials saved to …` / `Login failed: …` / `Login cancelled.`（注：setup 登录结果；疑点：亦近 S9） | 下次操作替换 | packages/tui/src/setup/scenes/sign-in.ts:325 |
| omp | Model 场景 | minVersion 1 | intro（搜索提示，或发现中/保存中 spinner）+ 模型浏览器（最多 10 行，enter 保存为默认） | 保存成功即结束该步 | packages/tui/src/setup/scenes/model.ts:66 |
| omp | Glyph 场景 | minVersion 1 且终端未确认 glyph protocol | 提示 `If a row shows boxes, tofu…` + 3 行预设（Nerd Font/Unicode/ASCII + 样字），数字 1-3 直选预览 | 回车保存；esc 跳过 | packages/tui/src/setup/scenes/glyph.ts:84 |
| omp | Composer 场景 | minVersion 2 | 提示 + shape 列表 + `Preview:` 真实 composer/状态行预览 | 回车保存；esc 跳过 | packages/tui/src/setup/scenes/composer.ts:80 |
| omp | Theme 场景 | minVersion 1 | 提示两行 + 预览块（success/warning/error/accent + 状态行 mock + 编辑器 mock）+ curated 6 项列表 | 回车保存；esc 跳过还原 | packages/tui/src/setup/scenes/theme.ts:252 |
| omp | 全部主题模式 | 选中 `Browse all…` | 列表换为全部主题（≤10 行）+ `Browsing all themes · esc returns to curated choices` | esc 回 curated | packages/tui/src/setup/scenes/theme.ts:191 |
| omp | 加载主题中 | 进入全部主题并加载 | `Loading themes…` + spinner 取代列表 | 加载完换回列表 | packages/tui/src/setup/scenes/theme.ts:252 |
| jcode | Changelog overlay | /changelog；无条目时显示占位句 | 全屏框“ Changelog {N%} ”；版本组头“vX · 时间”+ 每条“• 主题”；底行滚动/复制提示 | Esc/q；溢出滚动，标题显示百分比 | crates/jcode-tui/src/tui/ui_overlays.rs:15；分派 ui.rs:2714 |
| jcode | Help overlay（Commands 区） | /help、/?、/commands（远程同） | 框“ Help {N%} ”；逐行“/cmd  描述”（Commands 区在首） | Esc/q；溢出滚动，标题百分比 | crates/jcode-tui/src/tui/ui_overlays.rs:138；分派 ui.rs:2726 |
| jcode | Help overlay（Session/Memory & Swarm/Auth & Accounts/System 分区） | 同上 | 分区标题 + 逐行 /cmd 描述；System 区在远程时追加远程命令 | Esc/q；溢出滚动 | crates/jcode-tui/src/tui/ui_overlays.rs:138 |
| jcode | Help overlay（Navigation / Diagrams & Diffs / Input & Editing 键位分区） | 同上 | 每行“键位(22列)  说明”；含按终端配置动态生成的键标签 | Esc/q；溢出滚动 | crates/jcode-tui/src/tui/ui_overlays.rs:138 |
| jcode | Help“More commands”区 | 存在已注册但未列入手工分区的命令 | 标题“More commands” + 逐行“/cmd  描述” | 无（全部列出） | crates/jcode-tui/src/tui/ui_overlays.rs:440 |
| jcode | Help“Skills”区 | available_skills() 非空 | 标题“Skills” + 逐行“/skill  Activate skill” | 无（全部列出） | crates/jcode-tui/src/tui/ui_overlays.rs:453 |
| jcode | Onboarding·顶部遥测声明 | onboarding_welcome_active()（首启或预览） | 3 行 dim 居中：“jcode collects anonymous usage statistics (version, OS, session / activity, and crash reasons). No code, prompts, or personal data. / Change anytime: /telemetry …” | 窄屏逐行省略号；高<6 行整体降级为极简 | crates/jcode-tui/src/tui/ui_onboarding.rs:356 |
| jcode | Onboarding·标题+键盘提示 | 同上，且高度足够 | “Welcome to jcode onboarding”(居中加粗) + “Use your keyboard to navigate.” | 高度不足先丢标题块（保 body） | crates/jcode-tui/src/tui/ui_onboarding.rs:678（标题 :382，提示 :395） |
| jcode | Onboarding·Login body（默认/导入中/导入失败） | 未登录：默认、importing、error(可选 H 让本机 agent 修) | “First, log in to get started. / Press Enter to pick who to log in with…”、“Importing your logins…”、“We couldn't import those logins.”+原因+“Press Enter…” | Esc 跳过（“Esc to skip onboarding (log in later with /login).”） | crates/jcode-tui/src/tui/ui_onboarding.rs:405（Login 分支） |
| jcode | Onboarding·LoginImport 摘要屏 | 检测到可导入登录（prompt 非 choosing） | “Choose how to get started. We found N existing logins:”+ ✓ 逐条“Provider (source)”+ pills“Import/Jcode subscription/Import less/Telemetry”+价格句 | 选 pill 进入对应子流程；Esc 跳过 | crates/jcode-tui/src/tui/ui_onboarding.rs:405（summary 分支）；列表 :230，pills :141 |
| jcode | Onboarding·LoginImport 逐条 Yes/No | 选“Import less”进入 choosing 模式 | “Import:”+ Continue pill + 每登录一行：`>`光标 + “Provider (source)”+ Yes/No 两列 ●/○（默认 Yes） | Enter 提交导入；Esc 跳过；行数多则整体居中区压缩 | crates/jcode-tui/src/tui/ui_onboarding.rs:264 |
| jcode | Onboarding·LoginOpenAi 询问 | 检测到 Codex 登录，询问是否用 OpenAI 登录 | “Log in to OpenAI?”+ Yes/No 圆角 pills（选中为亮色实心） | Esc 跳过 | crates/jcode-tui/src/tui/ui_onboarding.rs:405（LoginOpenAi 分支） |
| jcode | Onboarding·ContinuePrompt | 检测到最近外部 CLI 会话 | “Continue where you left off in {cli}?”+ Yes/No pills +“Opens the resume menu automatically in {N}s…” | 倒计时自动进 resume；Esc 跳过 | crates/jcode-tui/src/tui/ui_onboarding.rs:405（ContinuePrompt 分支） |
| jcode | Onboarding·Suggestions 屏 | 走到 OnboardingPhase::Suggestions（空会话建议） | 逐行“[i] 标签”或“/cmd (type /cmd)”；>1 条时“Press 1-N or type anything to start” | 输入任意内容/按数字即开始或结束 onboarding | crates/jcode-tui/src/tui/ui_onboarding.rs:405（Suggestions 分支） |
| jcode | Onboarding·Telemetry 设置子页 | 摘要屏选“Telemetry” | “Telemetry settings”+ 3 个 pill(Share full transcripts / No prompts or transcripts / Send nothing) + 每项一行说明；若环境已禁用加提示 | Esc 返回摘要屏；“Change this later with /telemetry.” | crates/jcode-tui/src/tui/ui_onboarding.rs:166 |
| jcode | Remote·帮助里的远程命令行 | is_remote 且 /help | System 区追加“/client-reload Force reload client binary”“/server-reload …”“/continue …” | 非远程不显示 | crates/jcode-tui/src/tui/ui_overlays.rs:405 |
