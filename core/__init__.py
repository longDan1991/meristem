"""树包。

包内模块都经由本文件初始化。`core/llm.py` 用官方 openai SDK 直连 OpenAI 兼容
端点，import 无任何网络副作用——不再需要 litellm 时代"import 前钉死本地模型
成本表（它默认每次去 GitHub 拉，拉不到白卡几十秒）"的 hack。
"""
