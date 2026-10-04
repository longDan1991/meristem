# 屏幕 · 仓库（仓库所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S5：omp 21 条 · jcode 2 条

## 两家在这一刻的对照（事实）

- omp 21 条 / jcode 2 条；omp 是完整的 git review 屏（头部、工具栏、diff、hunk、staging 输入、commit 表单、作者头像、空态）；jcode 只有 File 模式右侧 diff 侧栏两处。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | git 头部行 | 始终 | 左 `dir/base +a −d`；中部状态消息（6s）或按键提示；右 类型(UTF-8/Binary/Media) + Stage\|Unstage File + ✕ | 无选中文件时左端 `no file selected` | packages/tui/src/apps/git/git-tui.ts:759 |
| omp | git 工具栏 | 始终 | scope chip + 居中 `↑ ↓` 与 File/Split/Inline/Hunks 四钮 + 右 whitespace(¶/¶+) 与 wrap(⏎) chip | 总宽不足时中部提示截断 | packages/tui/src/apps/git/git-tui.ts:811 |
| omp | git 原生 bar | Tern 渲染 | path+`+a −d`+badge、prev/next chevron、视图 tabs、whitespace/wrap、Stage file、help、close | <100 列时收起 whitespace/wrap | packages/tui/src/apps/git/git-tui.ts:986 |
| omp | diff 面板 | 文件已加载（ready） | split/inline/hunk/file 四模式；行号 gutter；词级高亮；行选择高亮带 | 换文件或换模式整体重画 | packages/tui/src/apps/git/diff-pane.ts:1027 |
| omp | minimap 滚动条 | 有 diff 文档 | 右侧 2 列密度色（删除>新增>改动>上下文，hunk 头 accent），可视区提亮 | 无内容不画 | packages/tui/src/apps/git/diff-pane.ts:1438 |
| omp | hunk 头与按钮 | hunk 视图或 patchTarget 存在 | `@@ -a,b +c,d @@` + 右端 `Discard Hunk`、`Stage\|Unstage Hunk`；选中行前置 `▶ ` | whitespace-ignore（canPatch=false）时不画按钮 | packages/tui/src/apps/git/diff-pane.ts:1288 |
| omp | diff 空/加载态 | 无改动 / 无提交 / 加载中 | 居中 `No changes` / `No commits yet` / `Loading diff…` | 内容到达即换 | packages/tui/src/apps/git/diff-pane.ts:1035 ; git-tui.ts:1082 |
| omp | 媒体/Binary 态 | 二进制或图片文件 | `Binary or media file` + before/after kv（图片预览 / text+字节 / binary / too large / LFS 未取） | 切换文件即换 | packages/tui/src/apps/git/diff-pane.ts:1074 |
| omp | streaming 态 | 文件内容流式加载中 | 渐进 diff 行（先公共行，再增量高亮） | 完成后切 ready | packages/tui/src/apps/git/diff-pane.ts:1187 |
| omp | 侧栏（脏树） | 工作树有改动 | `N file changes on branch` + Path\|Tree；Unstaged/Staged 段；commit 表单 | 提交干净后转干净视图 | packages/tui/src/apps/git/sidebar.ts:950 |
| omp | 段头 Unstaged/Staged | 段存在 | `▾ Unstaged Files (N)` + Stage all/✦；`▾ Staged Files (N)` + Unstage All | 折叠成 `▸`，行移出键盘导航 | packages/tui/src/apps/git/sidebar.ts:1117 |
| omp | 文件/目录行 | 段展开且有条目 | 状态字母 M/A/D/R/?/U + dim 目录 + 文件名 + `+a −d`（删除加删除线） | 空段显示 `no unstaged files` | packages/tui/src/apps/git/sidebar.ts:1198 |
| omp | AI staging 输入行 | 点 Unstaged 头部的 wand ✦ | `/ What should we stage?` 文本框（回车提交 prompt）（注：git review 屏内的 staging 输入） | esc 或提交后收起 | packages/tui/src/apps/git/sidebar.ts:1575 |
| omp | commit 表单 | 脏树 | Amend 勾选 + Commit summary（72 字计数）+ 描述编辑器 + 按钮 `Generate message/Commit/Stage all & commit` | 干净树时不显示 | packages/tui/src/apps/git/sidebar.ts:1234 |
| omp | 生成中状态 | 正在生成提交信息 | 按钮文案 `Generating message…` + spinner，按钮置灰 | 生成结束后恢复 | packages/tui/src/apps/git/sidebar.ts:1234 |
| omp | 侧栏（干净树） | 工作树干净 | HEAD 提交：subject、body（≤8 行）、头像、作者、authored 日期、parents、`N files +a −d · sha`、文件列表 | 出现改动即转脏树视图 | packages/tui/src/apps/git/sidebar.ts:1313 |
| omp | 作者头像 | 干净树提交视图 | 图片协议时作者照片（≤3 行），否则 md5 identicon 色块 | 无 head 时不画 | packages/tui/src/apps/git/sidebar.ts:1686 ; avatar.ts:12 |
| omp | 无提交空态 | 仓库还没有提交 | `No commits yet` | 出现提交即换 | packages/tui/src/apps/git/sidebar.ts:1313 |
| omp | 快捷键面板（?） | 按 `?` | `Keyboard shortcuts`：Move/Stage/View/Commit 四组，键帽 + 说明两列（注：git review 快捷键面板） | `?`/esc/q 关闭 | packages/tui/src/apps/git/help.ts:24 |
| omp | narrow 布局 | 原生终端宽度 <100 列 | 侧栏由右侧改堆在 diff 下方 | 变宽即还原 | packages/tui/src/apps/git/git-tui.ts:902 |
| omp | git 状态行 | 动作后 6 秒内，或 sticky | 头部/bar 中部的状态消息（成功/警告/错误着色） | 6s TTL 或新消息覆盖 | packages/tui/src/apps/git/git-tui.ts:986 |
| omp | git 头部行 | 始终 | 左 `dir/base +a −d`；中部状态消息（6s）或按键提示；右 类型(UTF-8/Binary/Media) + Stage｜Unstage File + ✕ | 无选中文件时左端 `no file selected` | packages/tui/src/apps/git/git-tui.ts:759 |
| omp | hunk 头与按钮 | hunk 视图或 patchTarget 存在 | `@@ -a,b +c,d @@` + 右端 `Discard Hunk`、`Stage｜Unstage Hunk`；选中行前置 `▶ ` | whitespace-ignore（canPatch=false）时不画按钮 | packages/tui/src/apps/git/diff-pane.ts:1288 |
| omp | 侧栏（脏树） | 工作树有改动 | `N file changes on branch` + Path｜Tree；Unstaged/Staged 段；commit 表单 | 提交干净后转干净视图 | packages/tui/src/apps/git/sidebar.ts:950 |
| jcode | File diff 表面（⇧Tab hide） | diff_mode=File 且存在可见 edit 工具消息（且无侧栏页优先） | 占同一右栏；头部 <短路径> +a -d NL edit#k；体内整文件带改动高亮，默认跟随 transcript 滚动 | 无可见 edit → 显示 “No edits visible”；被侧栏页优先抢占同一栏 | crates/jcode-tui/src/tui/ui.rs:2811,3390, crates/jcode-tui/src/tui/ui_file_diff.rs:429,532 |
| jcode | File 模式右侧 diff 侧栏 | diff_mode=File 且有 edit 工具消息 | 右栏整文件内容 + diff 高亮（Normal/Add/Del/Placeholder 行），滚动静默同步到变更处（注：doubt: 仓库 diff 屏） | 无 edit 消息即不占右栏；点击正文焦点移回 chat | crates/jcode-tui/src/tui/ui_file_diff.rs:1 |
