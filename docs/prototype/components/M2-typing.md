# 组件 · M2 打字的时候（输入时屏上出现的东西）

> 这一面回答的是**用户在什么时候看到了什么**（不是"代码里重不重用"）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
>
> omp 49 条 · jcode 26 条

## 两家在这一刻的对照（事实）

- omp 49 条 / jcode 26 条；omp 覆盖面最广：编辑器 chrome、多种补全（单词/弹窗/命令/@/^/#/emoji/URL/skill/模型/附件 chip）、拼写与形状配置；jcode 集中在多行 composer 的 prompt 前缀、hint 行、命令联想与 Ctrl+R 历史搜索浮层

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Editor 外框（composer shape） | 常驻；样式为 box/band/claude/pi/rule/field/rail/borderless | 顶/底 chrome + 左右边框 + 提示符 gutter，内容区按宽折行 | 无（样式/宽度变即重绘） | packages/tui/src/components/editor.ts:1303 |
| omp | Editor placeholder | 编辑器为空且无补全弹窗（看子代理时换 "Message <agent>"） | 光标行右侧 dim 一行右对齐文案 | 与光标间距 < PLACEHOLDER_MIN_GAP 整条不画 | packages/tui/src/prompt/custom-editor.ts:54 |
| omp | 内联提示 inlineHint | 无 placeholder 且光标行尾可容纳 | 光标后 dim 一行（选中候选的 hint，否则 provider 的） | 行满则截断；按键即重算 | packages/tui/src/components/editor.ts:1394 |
| omp | 单词补全 ghost text | 光标在行尾、引擎非 off、模型返回预测词 | 光标后 dim 补全词；Tab 接受并补空格，→ 接受不补 | 输入与该词分歧即撤下 | packages/tui/src/components/editor.ts:4686 |
| omp | 光标字形 | 聚焦时；Vim 模式与挂起命令改变字形 | 插入点细竖条；行尾反显末字素；Vim 非插入为方块 | 失焦不画；窄行改反显末字素 | packages/tui/src/components/editor.ts:1235 |
| omp | 硬件光标形状（DECSCUSR） | 每次 vim 模式/挂起命令/选区变化 | Vim 非插入=block，Vim 插入=bar，非 Vim=default | 形状未变由终端去重 | packages/coding-agent/src/modes/interactive-mode.ts:5395 |
| omp | Composer 提示（COMPOSER_HINTS） | 编辑器空；未学会(uses<3)：←←看运行中代理 / 键改 thinking | 同行右对齐 "键 + dim 斜体动作" | uses≥3 或条件不成立即消失 | packages/tui/src/prompt/composer-hints.ts:52 |
| omp | 提示框边框配色 | bash/python/vim 模式或会话/thinking 状态变化 | 边框整体换色（bash/python/vim/thinking 提示）（注：边框随 bash/python/vim/thinking 模式换色，属输入区模式指示） | 无内容时回落到会话强调色 | packages/coding-agent/src/modes/interactive-mode.ts:3653 |
| omp | 补全弹窗列表 omp.select | 触发前缀命中且候选≥1；max=min(autocompleteMaxVisible,终端行-已渲染行-2) | 光标下方 N 行，选中行 `>`+高亮，label（+图标）+描述列 | Esc/接受/前缀消失即关；max 至少 3 | packages/tui/src/components/editor.ts:1616 |
| omp | 弹窗搜索状态行 | 有 query、候选数>maxVisible、或有待确认项 | "  Search: <q>" / "  Type to search" / 待确认 item 的确认文案 | 无 query 且不溢出则不画 | packages/tui/src/components/select-list.ts:712 |
| omp | 弹窗滚动条 | 可视行数超过 maxVisible | 右侧 1 列滑轨 + thumb | 不溢出则不留该列 | packages/tui/src/components/select-list.ts:472 |
| omp | 弹窗空/无匹配行 | 过滤后 0 个候选 | "  No matching items"（有 query）或 "  No items" | 有候选即消失 | packages/tui/src/components/select-list.ts:396 |
| omp | 拼写替换弹窗（assist 态） | 按下 spellingSuggestions 键且光标词有替换候选 | 同弹窗外形，候选项为替换词 | 任意非接受键即取消 | packages/tui/src/components/editor.ts:4453 |
| omp | Slash 命令补全 | 行首 `/` 或行中 skill 语境；参数可续接补全 | label+描述；主列 12–32 宽，描述可折行≤2 行 | 无匹配/接受/前缀消失 | packages/tui/src/components/editor.ts:115 |
| omp | @ 文件引用补全 | `@` token 结束于光标；Tab 可强制文件补全 | 文件/目录项，按 live token 就地收窄 | 收窄为空则弹窗隐藏但仍开着 | packages/tui/src/components/editor.ts:110 |
| omp | ^ 模型提及补全 | 空白后 `^query` | ≤20 项：model 图标 + selector，描述为显示名 | 前缀消失/无候选 | packages/tui/src/prompt/model-mention-autocomplete.ts:12 |
| omp | # 提示动作补全 | `#query`（query 内无空白） | 7 行候选：Copy current line/whole prompt、Undo、移动光标到消息起止/行起止 | 无匹配则落回其它来源 | packages/tui/src/prompt/prompt-action-autocomplete.ts:284 |
| omp | #<数字> GitHub 引用补全 | 独立 `#<正整数>`，可带 pr/pull/issue 前置词 | 无限定时 2 行："PR #N"、"Issue #N"；带 pr/issue 限定时 1 行 | 非独立 token 即落回 # 菜单 | packages/tui/src/prompt/github-ref-autocomplete.ts:74 |
| omp | :emoji 短码/颜文字补全 | `:name`，名字≥1 个字母 | ≤12 项："😀  :joy:" 或 "😀  :-)"（颜文字优先） | 无匹配即不弹 | packages/tui/src/prompt/emoji-autocomplete.ts:157 |
| omp | scheme:// 内部 URL 补全 | 已注册 scheme + `://` token 结束于光标 | ≤25 项：label + description，子序列匹配排序 | 无候选不弹；接受后补尾空格 | packages/tui/src/prompt/internal-url-autocomplete.ts:120 |
| omp | Skill chip（`✳ name`） | 已知 skill 的 `/skill:<name>` 后跟空白 | 软胶囊 chip，已知 skill 可点 file:// 链接 | 名字不完整则保持原文 | packages/tui/src/prompt/composer-attachments.ts:68 |
| omp | 模型 chip | 可提及的 `^provider/id` 后跟空白 | 软胶囊 chip（statusLineModel 配色） | 不在可折叠草稿内则保持原文 | packages/tui/src/prompt/composer-attachments.ts:87 |
| omp | 附件 chip token（`▣ #N`） | 粘贴图片/视频/大段文本后 | 缓冲区内原子 token，按附件序号取专属颜色 | 整块删除（原子 token） | packages/tui/src/prompt/composer-attachments.ts:112 |
| omp | 展开标记 `[Image #N, WxH]` / `[Paste #N]` | 提交时展开；恢复历史草稿时折叠回 chip | 内联标记，图片带粗体下划线可点链接 | 删除 token 即丢弃该附件 | packages/tui/src/prompt/composer-attachments.ts:220 |
| omp | Emoji 内联替换 | 打全 `:name:` 或颜文字后紧跟空格 | `:joy:` 直接变 😂；`;) ` 变 😉（保留尾随空格） | 不存在（已替换） | packages/tui/src/prompt/emoji-autocomplete.ts:200 |
| omp | 队列简写 `->` / `=>` | 草稿以 -> 或 => 开头 | 首行换成 dim "Queueing ➤" + 余文 | 删除前缀即恢复原文 | packages/tui/src/prompt/custom-editor.ts:851 |
| omp | 队列编号列表 marker | 草稿是顺序数字/罗马/字母列表 | marker（`1.`/`i.`/`a.`）取 accent 色，其余原文 | 非顺序列表即不着色 | packages/tui/src/prompt/custom-editor.ts:856 |
| omp | 图片/视频卡 | 有被引用的图片/视频附件；卡间距 2 格 | 12x4 内容 + 1 格圆角边框；顶部标题、中部缩略图（Kitty 占位符，否则居中图标）、底部说明 | 超宽直接不画（不换行） | packages/tui/src/prompt/attachment-chips.ts:110 |
| omp | 文本粘贴卡 | 有被引用的 paste chip | 前 4 行 ×12 列 muted 片段 | 同上，放不下省略 | packages/tui/src/prompt/attachment-chips.ts:143 |
| omp | 卡上标题 `<icon> #N` | 每张卡 | 边框内居中置顶；有文件链接时可点 | 宽度不足居中截断 | packages/tui/src/prompt/attachment-chips.ts:158 |
| omp | 卡下说明 | 每张卡 | `WxH`（图/视频）或 `+N lines` / `N chars`（粘贴） | 尺寸未知则留空 | packages/tui/src/prompt/attachment-chips.ts:150 |
| omp | 拼写错误标记 | typo 检测命中（设置开启） | 红色波浪下划线（无 styled underline 时用平直下划线） | 改对或关闭设置即消失 | packages/tui/src/prompt/macos-spelling.ts:9 |
| omp | 自动更正 | 开 autocorrect 且输入越过一个词 | 词被就地替换 | —（就地替换） | packages/tui/src/components/editor.ts:3082 |
| omp | Viewing 子代理头部 omp.composer.focus | 焦点在子代理会话 | 一行 "Viewing subagent <id>…" + focus 操作链接（注：输入区顶部的焦点指示，指示正在查看哪个子代理；疑点：亦近 M11 子 agent） | 回主会话即消失 | packages/tui/src/prompt/custom-editor.ts:1078 |
| omp | Shell/Python 模式 chip omp.composer.mode | 草稿以 `!`/`!!`/`$`/`$$` 开头 | bash/python 标签（配色区分）；`!!`/`$$` 另加 eye-off（不发给模型） | 删掉 sigil 即消失 | packages/tui/src/prompt/custom-editor.ts:1221 |
| omp | Composer bar omp.composer.bar | 常驻（原生渲染面） | 模型 chip、effort chip/meter、状态事实、用量、Send（运行中变 Stop） | 收窄时由终端截断 | packages/tui/src/prompt/custom-editor.ts:1211 |
| omp | shape=box | composer.shape=box | attachment=top-border，bottomBar=none，两行圆角框，状态嵌顶边框（注：输入框形状+状态附着方式；归输入框形态） | — | packages/tui/src/components/composer/box.ts:12 |
| omp | shape=band | composer.shape=band（默认） | attachment=top-band，bottomBar=none，软帽状态带，无边框 | — | packages/tui/src/components/composer/band.ts:13 |
| omp | shape=claude | composer.shape=claude | attachment=top-rule-chip，bottomBar=left，上下横线，右组做成顶线 chip，左组落底栏 | — | packages/tui/src/components/composer/claude.ts:14 |
| omp | shape=rule | composer.shape=rule | attachment=top-rule-chip，bottomBar=left+gap，单条顶线 dock 状态、底栏带空行 | — | packages/tui/src/components/composer/rule.ts:30 |
| omp | shape=pi | composer.shape=pi | attachment=none，bottomBar=full，横线框，状态整条在底栏 | — | packages/tui/src/components/composer/pi.ts:13 |
| omp | shape=borderless | composer.shape=borderless | attachment=none，bottomBar=full，无边框，状态整条在底栏 | — | packages/tui/src/components/composer/borderless.ts:13 |
| omp | shape=field | composer.shape=field | attachment=none，bottomBar=full+gap，填充单行域+accent 端帽，底栏上方空一行 | — | packages/tui/src/components/composer/field.ts:17 |
| omp | shape=rail | composer.shape=rail | attachment=none，bottomBar=full+gap，填充单行+accent 竖轨，底栏上方空一行 | — | packages/tui/src/components/composer/rail.ts:16 |
| omp | setEditorComponent(factory) | 扩展替换编辑器 | 整个输入区换成自定义 CustomEditor；undefined 还原内置编辑器（注：替换整个输入区为自定义编辑器） | factory=undefined | packages/coding-agent/src/modes/controllers/extension-ui-controller.ts:164 / modes/types.ts:374 |
| omp | attachmentChipsContainer | 编辑器里已暂存附件（图片/视频/粘贴块） | AttachmentChipsBand：每附件一张 12x4 圆角卡（缩略图/前几行+尺寸或 +N lines 说明） | 无附件即空；放不下的卡直接省略不换行 | packages/coding-agent/src/modes/interactive-mode.ts:1870 / tui/src/prompt/attachment-chips.ts:53 |
| omp | editorContainer（新发现） | 恒在——输入区 | 装 CustomEditor；transient 时内联对话框/多行草稿换入此处（注：输入区容器） | transient 结束收回 | packages/coding-agent/src/modes/interactive-mode.ts:1879-1880 / modes/types.ts:128 |
| omp | skillPromptTitleInput / titleTextFromSkillPrompt | 从不直接上屏（纯字符串函数） | 产出 `/skill:<name>` 标题文本，供队列 chip 与 rewind 草稿（注：从不直接上屏，纯字符串函数） | n/a | packages/tui/src/chat/skill-title-input.ts:2 |
| omp | select-list-mouse-routing | 从不直接上屏 | 鼠标坐标做 line-1 偏移后转发给 SelectList（注：从不直接上屏，SelectList 鼠标路由） | n/a | packages/tui/src/chrome/select-list-mouse-routing.ts:4 |
| jcode | input box（多行 composer） | 始终显示；空/多行/粘贴大段 | 行首 {prompt编号}{prompt字符}+正文；软换行 | 可见行 = 换行数，上限 10 行 | crates/jcode-tui/src/tui/ui.rs:3009-3015 |
| jcode | prompt 前缀 `> `（默认） | 普通聊天输入且未处理中 | `> `，user_color | 进入其它模式即替换 | crates/jcode-tui/src/tui/ui_input.rs:415-425 |
| jcode | prompt 前缀 `… `（处理中） | is_processing 且输入非空/有内容 | `… `，queued_color | 处理结束回 `> ` | crates/jcode-tui/src/tui/ui_input.rs:419 |
| jcode | prompt 前缀 `» `（技能） | active_skill 存在 | `» `，accent_color | 技能退出后回 `> ` | crates/jcode-tui/src/tui/ui_input.rs:421 |
| jcode | prompt 前缀 `$ `（shell 本地/远端） | 输入以 `!` 开头则进 shell 模式 | `$ ` + 绿色 110,214,151，hint 区分本地/服务端 | 删掉 `!` 前缀即回聊天 | crates/jcode-tui/src/tui/ui_input.rs:36-55,415-419 |
| jcode | prompt 编号（彩虹色） | 始终，编号=已显示用户消息数+1 | 首行显示数字，rainbow_prompt_color | 随下一条用户消息 +1 | crates/jcode-tui/src/tui/ui_input.rs:433-435,2922-2926 |
| jcode | 续行缩进 | 输入软换行/含 \n | 第 2+ 行以 prompt_len 个空格缩进 | 无 | crates/jcode-tui/src/tui/ui_input.rs:2929-2932 |
| jcode | hint 行 · shell mode | 输入匹配 `!cmd`（本地/远端） | `shell mode · Enter runs locally\|on server`，shell 绿 | 非 shell 模式或浮层开启 | crates/jcode-tui/src/tui/ui_input.rs:50-55,2489-2497 |
| jcode | hint 行 · 新会话路由 | next_prompt_new_session_armed | `↗ Next prompt opens a new session` 浅蓝 | 取消路由/提交后 | crates/jcode-tui/src/tui/ui_input.rs:2498-2506 |
| jcode | hint 行 · Ctrl/Cmd+Enter | 处理中且输入非空 | queue 模式=`to send now`，否则 `to queue`，dim | 输入清空/处理结束 | crates/jcode-tui/src/tui/ui_input.rs:2507-2517 |
| jcode | hint 行高度占位 | 上述任一 hint 出现 | input_height = 输入行数 + 1 | palette 激活时返回 0（不占位） | crates/jcode-tui/src/tui/ui_input.rs:394-408 |
| jcode | send-mode 指示（右下角） | 输入区末行，图标非空即显示 | $=shell · ↗=新会话 · ⏳=queue mode · 󰌘ws/󰆍subprocess/󰖟http | 无连接且非上述模式则不画 | crates/jcode-tui/src/tui/ui_input.rs:2948-2987 |
| jcode | 光标 | 始终 | frame.set_cursor_position 落在文本列 | 无 | crates/jcode-tui/src/tui/ui_input.rs:2630-2647 |
| jcode | 输入选区高亮 | copy_selection_range 为 Input pane | 选中行高亮（排除 prompt 前缀） | Esc/复制后清除 | crates/jcode-tui/src/tui/ui_input.rs:2594-2627 |
| jcode | 占位 `[pasted N lines]` | 粘贴 ≥5 行文本 | 输入内联占位符 | 提交时展开为原文 | crates/jcode-tui/src/tui/app/input.rs:872-883,2995-3003 |
| jcode | 占位 `[image N]` | 粘贴/拖入图片 | 输入内联占位符，N=已挂图片序号 | 提交时作为附件发送 | crates/jcode-tui/src/tui/app/input.rs:2985-2990,762-765 |
| jcode | 拖入文件路径 chip | 拖入非图片文件 | 输入内联路径文本（引号/转义） | 提交时解析 | crates/jcode-tui/src/tui/app/input.rs:681-697 |
| jcode | 📋 stash 徽标 | has_stashed_input（Ctrl+S 存过草稿） | `📋 stash` 黄 | 取回/清空 stash | crates/jcode-tui/src/tui/ui_input.rs:1847-1853; app/state_ui_runtime.rs:468-484 |
| jcode | 命令联想浮层 | 输入 `/` 前缀（Chat 需非处理中；Slash 恒可）且 suggestions 非空 | 命令+描述行，匹配字高亮；1 条时单行 | 无匹配/非命令态/Esc | crates/jcode-tui/src/tui/ui_input.rs:121-130,215-254,256-321 |
| jcode | 联想窗口 ≤8 行 + `+N more` | 候选 >8 | 滚动窗口 8 行，末行尾追 `+N more` | 候选变少 | crates/jcode-tui/src/tui/ui_input.rs:62-68,294-320; app.rs:134 |
| jcode | 浮层定位（下方优先/贴底翻上） | 始终 | 输入下方有空则向下，贴屏底则向上覆盖正文末几行 | 窗口高为 0 不画 | crates/jcode-tui/src/tui/ui_input.rs:69-118 |
| jcode | Ctrl+R 历史搜索浮层 | prompt_history_search 打开 | `(history search) {query}█  ↑↓ select · ↵ insert · Esc cancel` + ≤8 条匹配(+`+N more`) | Enter 采纳/Esc 还原草稿 | crates/jcode-tui/src/tui/ui_input.rs:132-212; app/prompt_history.rs:258-264 |
| jcode | 历史搜索空态 | query 空 / 无匹配 | `type to search history` / `no matches` dim | 有匹配 | crates/jcode-tui/src/tui/ui_input.rs:147-155 |
| jcode | 历史搜索实时预览 | 移动选中项 | 选中匹配回填到输入框（readline 式） | Esc 还原 | crates/jcode-tui/src/tui/app/prompt_history.rs:297-315 |
| jcode | 命令联想 palette（slash 建议） | 输入以 / 开头且建议非空（Chat 模式还需非处理中）；模型 picker 打开时改为模型行 | 浮于输入框上方/下方：选中行亮“/cmd  描述”，匹配字符高亮；多条时首/末行“↑N more/↓N more”，空列表不画 | 最多 8 行(COMMAND_SUGGESTION_VISIBLE_LIMIT)，随输入实时收/换 | crates/jcode-tui/src/tui/ui_input.rs:215（行构造 :256）；常量 crates/jcode-tui/src/tui/app.rs:134 |
| jcode | Ctrl+R prompt history 搜索浮层 | Ctrl+R / Cmd+R（跨会话合并历史） | 首行“(history search) query█  ↑↓ select · ↵ insert · Esc cancel”；下最多 8 条匹配，选中“▸”，溢出“+N more”；空 query→“type to search history”，无匹配→“no matches” | Enter 插入选中并关闭；Esc 取消；同浮于输入框附近 | crates/jcode-tui/src/tui/ui_input.rs:132；分派 ui.rs:3564（状态 crates/jcode-tui/src/tui/app/prompt_history.rs:258） |
| jcode | hint 行 · shell mode | 输入匹配 `!cmd`（本地/远端） | `shell mode · Enter runs locally｜on server`，shell 绿 | 非 shell 模式或浮层开启 | crates/jcode-tui/src/tui/ui_input.rs:50-55,2489-2497 |
