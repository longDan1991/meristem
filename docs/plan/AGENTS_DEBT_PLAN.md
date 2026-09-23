# AGENTS 存量违规台账

每一条 `# noqa` 都必须在这里登记：规则、位置、为什么压、什么时候该还。
没有登记的 `noqa` 是创可贴（AGENTS §2 禁止），有登记的是旧账。

## 已登记的旧账

（无）

## 已经清零的

- `E402` tests/ 各文件的 `sys.path.insert(...)` 之后的 import 行 —— 随 `tests/harness.py` 提取清掉：
  sys.path 样板收进 harness（它只 import 标准库，无 E402），测试的 import 全部回到模块顶部、
  不再需要 `# noqa: E402`，整批移除。

- `E402` tree/run.py 中段的 import 块 —— 随 run.py 拆分进 `runtime/`、`protocol/`、`memory/` 时修复。
- `PLC0415` tree/run.py 函数内 `import hashlib`、`from .mine import ...` —— 已提为模块顶层导入。
- `BLE001` 树里所有宽 `except Exception` —— 已改为按具体异常捕获或移除（见下）。
- `F401/F841` —— 已删未用导入/变量。
