# 屏幕 · 界面与外观（界面与外观所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S7：omp 12 条 · jcode 3 条

## 两家在这一刻的对照（事实）

- omp 12 条 / jcode 3 条；omp 是 Settings 全屏面板 + Theme/Show Images/composer 形状选择器；jcode 是 split_view 页、宽度档 Ctrl+1..4、Alt+M 侧栏三态。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Theme 选择器（类） | 【用户看不到】无实例化点（仅 components/index re-export） | 面板标题 Theme；SelectList ≤10 行列出主题名，当前项注 (current)，移动选择即时预览（注：【用户看不到】无实例化点（死路径）） | Esc 取消 | packages/tui/src/overlays/theme-selector.ts:29-79 |
| omp | themePickerOptions()（settings 复用） | Settings→Appearance→Theme 子菜单 | picker：标题=Theme、可搜索、当前项打点、色块 mark、确认按钮 Apply | Esc 关闭 | packages/tui/src/overlays/theme-selector.ts:16-27 |
| omp | snapcompact 形状预览 | Settings→Appearance→snapcompact.shape 高亮某选项时 | 一行 caption「Sample (zoomed) · <shape> · <容量/token>」+ 迷你页图像(≤28 列×14 行) | 无图像能力的终端显示「(graphic sample needs an image-capable terminal)」；渲染中 spinner；失败「(sample render failed)」 | packages/tui/src/overlays/snapcompact-shape-preview.ts:102-123 |
| omp | Settings 全屏面板 | /settings | 全屏：标题边框、tab 行(10 个 tab + Plugins)、搜索横幅(带 match 数)、内容列表(按 section 分组)、Appearance 上的状态行预览、底部键位提示 | Esc 关闭；列表窗口固定 10 行 | packages/tui/src/overlays/settings-selector.ts:615-653,727-779 |
| omp | 搜索模式 | 在设置面板里输入字符 | 跨 tab 的扁平结果列表，每个 tab 一个 heading 行；tab 条把命中的 tab 提前并显示计数 | Esc 退出搜索 | packages/tui/src/overlays/settings-selector.ts:1286-1367 |
| omp | 原生 prefs 页 | 终端支持 prefs | 左侧 tab 导航(带 changed 计数)、当前 tab 的 sections、focus/editing 态、内联编辑器叠加 | Esc 关闭 | packages/tui/src/overlays/settings-selector.ts:801-884 |
| omp | 选择型子菜单弹窗 | 对某设置按确认且选项 ≤12 | 行内 popup 菜单，≤PREFS_MENU_MAX 条；更大的子菜单改开 picker 覆盖页面 | 选择/取消后收起 | packages/tui/src/overlays/settings-selector.ts:74-75 |
| omp | Show Images 选择器 | 【用户看不到】无实例化点 | 面板标题 Show Images；两行 Yes/No 及描述；预选当前值（注：【用户看不到】无实例化点（死路径）） | Esc 取消 | packages/tui/src/overlays/show-images-selector.ts:11-50 |
| omp | SETTING_TABS / TAB_METADATA / TAB_LEADS / TAB_GROUPS | 【用户看不到】驱动 SettingsSelector 的 tab、标题、分组 | 10 个 tab：Appearance/Model/Interaction/Context/Memory/Files/Shell/Tools/Tasks/Providers，各带 icon/label/一句话说明/分组序列（注：【用户看不到】纯定义，驱动 Settings 屏） | — | packages/tui/src/overlays/settings-defs.ts:5-113 |
| omp | composer 形状预览 | Settings→Appearance→composer.shape 高亮选项 | 按候选 shape 渲染：顶部状态条(可选)+输入行+底部条(可选)，标题 omp；原生只写 shape 名 + 只读 prompt | 随选择切换；无上限宽度(只受终端限制) | packages/tui/src/overlays/composer-shape-preview.ts:29-49,122-140 |
| omp | 示例 transcript 文案 | 【用户看不到】被 snapcompact-shape-preview 当样本渲染 | 已被 <out>…</out> 包裹的示例文本（注：【用户看不到】资源） | — | packages/tui/src/overlays/snapcompact-shape-preview-doc.md:1 |
| omp | composer shape 选项注册 | 【用户看不到】喂给 Settings 的 composer.shape 选项与渲染注册 | BUILTIN_COMPOSER_SHAPES / getComposerShapeOptions / installExtensionComposerShape（注：【用户看不到】注册表） | — | packages/tui/src/overlays/composer-shape-registry.ts:4-82 |
| jcode | split_view 页（Split View，ephemeral） | /splitview [on]；不落盘 | 标题 Split View；正文=聊天镜像：提示行 + 逐条 ## Prompt N / ## Response N(.k) / ## <tool 标题> fenced / ## Live response | /splitview off 或消息清空即从 snapshot 移除；内容空时给占位 | crates/jcode-tui/src/tui/app/split_view.rs:8,111,152 |
| jcode | 宽度档 Ctrl+1..4 | Ctrl+数字（无 Alt/Shift） | 预设 25/50/75/100%，状态提示 “Side panel: N%”，同时作用于 diagram 面板比 | 拖拽/±键会标记用户已调，停止自适应 | crates/jcode-tui/src/tui/app/navigation.rs:1319,1042 |
| jcode | Alt+M 侧栏三态循环 | 有 focused 页 | split → fullscreen → hidden；hidden 时保留 last_side_panel_focus_id 以便恢复 | 无页 → 状态提示 no pages；hidden 期间 incoming snapshot 不自动重开 | crates/jcode-tui/src/tui/app/navigation.rs:1092,1107,1136 |
