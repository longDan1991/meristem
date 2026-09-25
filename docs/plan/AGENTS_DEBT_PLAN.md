# AGENTS 存量违规台账

每一条 `# noqa` 都必须在这里登记：规则、位置、为什么压、什么时候该还。
没有登记的 `noqa` 是创可贴（AGENTS §2 禁止），有登记的是旧账。

## 已登记的旧账

- `F401` tools/defs.py `from tools import bash as _bash  # noqa: F401` ——
  import 的副作用：工具靠 `@mcp.tool` 在**自己所在模块**注册（bash 住在 `tools/bash.py`），
  defs 必须 import 它才会注册（`tools/__init__` 不能自己拉 defs：那会和 `core.runtime` /
  `core.prompts` 转成环 —— defs 依赖 runtime.ops，runtime 依赖 prompts，prompts 依赖 tools）。
  别名 `_bash` 无使用者，noqa 是明确意图不是创可贴；
  `__all__` 会把 re-export 语义扩散到整个模块，不值。若哪天工具改成自动发现（按模块扫描注册），
  这条 import 连同 noqa 一起移除。

## 已经清零的

- `E402` tests/ 各文件的 `sys.path.insert(...)` 之后的 import 行 —— 随 `tests/harness.py` 提取清掉：
  sys.path 样板收进 harness（它只 import 标准库，无 E402），测试的 import 全部回到模块顶部、
  不再需要 `# noqa: E402`，整批移除。
- `BLE001` 树里所有宽 `except Exception` —— 已改为按具体异常捕获或移除。
- `F401/F841` —— 已删未用导入/变量。
