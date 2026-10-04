# 屏幕 · 协作与多端（协作与多端所在的整块）

> 这一面回答的是**用户在什么时候看到了什么**（不是“代码里重不重用”）。
> 状态：两家的全貌（先例），**不含我们的判断**。
> 逐条出处是仓根相对全路径；「【用户看不到】」= 代码里没有实例化点的死路径（也是证据）。
> S8：omp 0 条 · jcode 2 条

## 两家在这一刻的对照（事实）

- omp 0 条 / jcode 2 条；omp 无 S8 条目；jcode 是 WorkspaceMap 与 Remote·workspace 模式（/workspace）。

## 条目

| 家 | 块 | 什么时候看到 | 看到什么 | 什么时候消失 | 出处 |
|---|---|---|---|---|---|
| jcode | WorkspaceMap（Workspace） | workspace 客户端启用且 visible_rows 非空；优先右侧、最小高 1（+2 边框） | 边框 Workspace；体内一格一会话的方块地图（preferred_size = 最大列数×1 + 列间距、行数×1），聚焦格加粗 | rows 空即消失；受最宽 40、最窄 24 裁切，多出的格被区域裁剪 | crates/jcode-tui/src/tui/info_widget.rs:756, crates/jcode-tui-workspace/src/workspace_map_widget.rs:12, crates/jcode-tui/src/tui/info_widget.rs:1248 |
| jcode | Remote·workspace 模式（/workspace） | /workspace on/add 等（远程共享会话） | 侧栏 Workspace 地图 widget（工作区行+会话瓦片，当前项高亮）；状态通知“Workspace mode enabled/disabled”+ status_summary 消息 | /workspace off；未启用时 widget 不出现 | crates/jcode-tui/src/tui/app/remote/workspace.rs:46/67/94；行数据 crates/jcode-tui/src/tui/app/tui_state.rs:1700 |
