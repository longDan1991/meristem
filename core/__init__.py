"""树包。

litellm 默认每次 import 都去 GitHub 拉模型成本表（常拉不到，白卡几十秒），
所以在 `import litellm` 之前用本地副本钉死它 —— 包内模块都经由本文件初始化。

成本表只服务美元记账与上下文安全，我们全不用，本地副本功能等价、启动快、离线可跑。
想切回拉新鲜表去掉下面这行；网络拉不到就给 litellm 指 `HTTPS_PROXY`。
"""

import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
