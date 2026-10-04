# 屏幕 · 账号与计费（账号与计费所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S9：omp 13 条 · jcode 7 条

## 两家在这一刻的对照（事实）

- omp 13 条 / jcode 7 条；omp 是 UsageDashboard（订阅网格、活动热力图、明细报告）+ Login/登出选择器与二次确认；jcode 是 Login/Account picker 全屏 + Usage overlay（注册但无渲染入口的死路径）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | UsageDashboard（/usage） | 输入 /usage（需有 reports 或已存账号，否则只出警告） | 全屏 alt-screen 面板，标题 Usage；网格 + 热力图，Enter 翻转为明细；头部有 Refresh(r) | Esc 关（[推断] matchesSelectCancel）；无数据则不打开 | packages/tui/src/overlays/usage-dashboard.ts:533-535 |
| omp | 订阅网格区 | 打开即见；有账号用量时 | 每个 provider 一张卡：状态点 + 名称 + 窗口行(label/用量条/% left/resets)，≤4 窗(CARD_MAX_WINDOWS)，超出显示 +N more | 每卡最多 4 个窗口，多余折叠为 +N more；窄屏卡片换行(wrap) | packages/tui/src/overlays/usage-dashboard.ts:519-523,1098-1124 |
| omp | 活动热力图区 | 本地 stats DB 有每日活动时 | GitHub 风格 53 周日历热力图(0-1 强度、月列、M/W/F 行、每日 tooltip) + 合计 $ / 请求数 | 无数据整块不渲染(omp.usage.untouched) | packages/tui/src/overlays/usage-dashboard.ts:363-367,1148-1160 |
| omp | 明细报告表 | 在仪表盘上按 Enter 翻转 | 每 provider 一节：table 列 Limit/Account/Left/Resets，下方 limit note | Esc/再按返回网格（[推断]） | packages/tui/src/overlays/usage-dashboard.ts:1302-1318 |
| omp | 选择会话账号 | /session pin（无账号参数） | 面板标题「Select a <provider> account for this session」；行=账号 label，active 项注「active for this session」；≤10 行 | Esc 取消 | packages/tui/src/overlays/session-account-selector.ts:6,17-56 |
| omp | Spend a saved rate-limit reset | /usage reset | 面板标题同名；行：「[provider · #credentialId] 账号名 (active)  可用数」；选中行前缀 cursor，可兑换=accent，不可=dim；≤10 行(RESET_SELECTOR_MAX_VISIBLE) | Esc 取消（已进入确认态时先取消确认）；空列表显示「No provider accounts with saved resets」 | packages/tui/src/overlays/reset-usage-selector.ts:16,76-116 |
| omp | 二次确认提示 | Enter 选中一个 redeemable 账号 | 列表下方 warning 文案「Press enter again to spend …」+ credit 细则 + Esc cancels | 再按 Enter 兑换，Esc/移动取消 | packages/tui/src/overlays/reset-usage-selector.ts:118-130 |
| omp | Select provider to login / logout | /login 或 /logout（未带 provider 参数） | 面板标题随模式变；provider 行=名称 + 凭证来源 tag(runtime/config/oauth/api key/env) + 可用性/校验 spinner；≤10 行(可被 setMaxHeight 压缩到 ≥1) | Esc 取消；login=Sign in(primary)，logout=Sign out(danger) | packages/tui/src/overlays/oauth-selector.ts:27,27-39,92-140,485-515 |
| omp | 原生 picker 形态 | 终端支持 picker | docked picker：标题 Sign in/Sign out、cards 布局、initials 色块 mark、可搜索 | Esc 关闭 | packages/tui/src/overlays/oauth-selector.ts:492-515 |
| omp | 选择登出账号 | /logout 已选定 provider 后 | 面板标题「Select <provider> account to log out」；原生 picker「<provider> accounts / Pick the account to sign out」，cards 布局；≤10 行 | Esc 取消 | packages/tui/src/overlays/logout-account-selector.ts:15,26-46,148-155 |
| omp | Login to <provider> | /login（已选定/指定 provider） | 面板标题 Login to <provider>；内容区=授权 URL(每行独立 OSC8 链接)+「super/ctrl+click to open」提示；设备码场景显示 code + 复制按钮；后续步骤为输入/进度 | Esc/ctrl+c 取消 abort；完成后关闭 | packages/tui/src/overlays/login-dialog.ts:20-52,84-140,320-390 |
| omp | 输入/进度步 | OAuth 回调要求输入或显示进度 | TextFormField(secret 可切换) 或进度文案，置于标题下 | 提交/取消后进入下一步 | packages/tui/src/overlays/login-dialog.ts:21-46,200-320 |
| omp | 用量格式化/折叠 | 【用户看不到】被 usage-dashboard 与 coding-agent 的 renderUsageReports 使用 | formatLimitTitle/collapseSharedUsageReports/summarizeUsageResetCredits/formatUsageResetWindow 等（注：【用户看不到】纯 helper） | — | packages/tui/src/overlays/usage-display.ts:1-53 |
| jcode | Login picker（全屏） | 【用户看不到】[未核实] 生产代码查无 login_picker_overlay=Some，仅测试/bench 可达 | 框“ Login ”；上“Login overview”(Filter + configured/attention/setup/recommended 四计数)；左“Providers (i/N)”列表：名 + ✓/✕ 状态色；右详情；底 Tip 行（注：【用户看不到】死路径(未核实); doubt: 【用户看不到】死路径（生产无赋值点）） | Enter 执行；Esc(有 filter 先清)、q、Ctrl+C 关闭 | crates/jcode-tui/src/tui/login_picker.rs:290；分派 ui.rs:2763 |
| jcode | Login picker·详情面板 | 左列表有选中 provider | 标题=provider 名；状态图标+configured/needs attention/not set up；Provider(+recommended)；Login command“/login id”；Authentication；Detected setup；What you need；Aliases；Numbered accounts supported/not used | 无选中→“No provider selected”；内容溢出逐行裁剪 | crates/jcode-tui/src/tui/login_picker.rs:472 |
| jcode | Account picker·Overview 头 | open_account_center / open_account_add_replace_flow 打开 | 框“ Account Center/Add / Replace Account ”；Overview 区：Filter +“N results”+ Providers 摘要(各 provider 账户数/控制数) + ready/attention/setup/providers(/accounts) 计数 + Defaults provider/model | Filter 为空显示引导句；窄屏换行 | crates/jcode-tui-account-picker/src/overlay.rs:402/458 |
| jcode | Account picker·动作列表（左 58%） | 有过滤结果 | 按 provider 分组头“label - N saved accounts - M other”+ 每行“> 图标 标题 - 副标题(截断)”；图标 *=active/o/+/R/S/./x/- | 溢出窗口滚动；空→“No matching account or provider actions.” | crates/jcode-tui-account-picker/src/overlay.rs:498 |
| jcode | Account picker·详情面板（右 42%） | 选中动作；带 details（用量）时走专用分支 | Provider、Saved accounts N、“Quick switch”账户列表(*/o + [selected])、Selected action(kind 徽标 - 标题)+副标题、Runs 预览命令+说明、Other controls(≤6 项)、末行“Press Enter to run this action.” | 无选中→“No action selected”；Secondary 列表 truncate(6)；用量 details 分支直接铺详情行 | crates/jcode-tui-account-picker/src/overlay.rs:579 |
| jcode | Account picker·底栏提示 | always（框内 rows[2]） | “Focus saved accounts stay surfaced here; click actions to focus them, use Left/Right to jump provider groups, or use `/account <provider> settings`…”；框底键位 “Enter run · Up/Down · Click select · type filter · Esc” | 无（宽度不足折行） | crates/jcode-tui-account-picker/src/overlay.rs:449（底栏）与 :407（title_bottom） |
| jcode | Usage overlay（全屏，注册但无渲染入口） | 【用户看不到】[未核实] 无任何调用点，仅数据模型/测试 | 88%×74% 框“ Usage ”：Overview 计数 + 左列表(状态图标/标题/副标题) + 右详情(状态标签/标题/详情行)（注：【用户看不到】死路径(未核实); doubt: 【用户看不到】死路径） | 不可见（无调用者） | crates/jcode-tui-usage-overlay/src/lib.rs:386 |
