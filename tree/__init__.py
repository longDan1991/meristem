"""树包。

导入任何 `tree.*` 子模块前，先把 litellm 的**本地成本表**开关钉死：
否则 litellm 每次 import 都会去 GitHub 拉模型成本表（国内经常拉不到，
启动白白卡几十秒还刷三条告警）。放在这里是因为它必须先于
`import litellm` 生效，而包内所有模块都经由本文件初始化。

**这张表是什么 / 为什么用本地**：litellm 维护的"模型 → 每百万 token 价格 +
上下文窗口"映射（GitHub 上 3818 条，包内自带同一份的本地备份）。它只服务
美元成本记账 / 按钱设预算 / 上下文长度安全 —— 我们全不用，所以拉不拉
新鲜表无所谓，本地副本功能等价、启动快、离线可跑。

**想切回"拉新鲜表"**：去掉下面这行即可（或设成非 True）。若网络拉不到
（GitHub 被墙），给 litellm 指代理：`HTTPS_PROXY=http://127.0.0.1:7890`
（mihomo 规则分流时，GitHub 走代理、国内端点照旧直连）。
"""

import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
