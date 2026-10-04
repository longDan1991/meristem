# 屏幕 · 工具与权限（工具与权限所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S4：omp 2 条 · jcode 1 条

## 两家在这一刻的对照（事实）

- omp 2 条 / jcode 1 条；omp 是 Add MCP Server 向导（18 步表单），jcode 是 SSH 模式专属权限/登录提示。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| omp | Add MCP Server 向导 | /mcp add（mcp-command-controller 挂载 wizard） | 面板标题 Add MCP Server；原生 md 居中 modal sheet「Add MCP server」；逐步：输入步(标题+字段+错误/提示行)或选择步(标题+选项列表+footer 提示) | Esc 逐步回退/取消；async 步显示进行中 | packages/tui/src/overlays/mcp-add-wizard.ts:302-303,165-166,376-500 |
| omp | 步骤清单(18 步) | 按向导推进 | name→transport→command→args→url→auth-method→oauth-error→oauth-auth-url→oauth-token-url→oauth-client-id→oauth-client-secret→oauth-scopes→apikey→auth-location→env-var-name→header-name→scope→confirm | 每步完成即进入下一步；Esc 返回上一步(首步取消) | packages/tui/src/overlays/mcp-add-wizard.ts:96-114,517-523 |
| jcode | SSH 模式专属提示 | is_ssh_remote（经 /ssh 进入） | 顶栏“/login to authenticate on {host}”；本地命令被拦时状态行“X is unavailable in SSH mode. Nothing was changed on this computer…”；SSH 登录流程状态/卡片（“SSH login: …”）（注：doubt: SSH 远端；亦涉 S8） | 回到本地会话即消失 | crates/jcode-tui/src/tui/ui_header.rs:869；crates/jcode-tui/src/tui/app/commands_dispatch.rs:123；crates/jcode-tui/src/tui/app/auth_remote.rs:210 |
