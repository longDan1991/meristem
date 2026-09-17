"""提示词。单独放一个目录，因为它们是**协议的一部分**。

每条硬性要求都对应 `tree/run.py` 里的一处代码检查 —— 改一边就得看另一边：

    字数（≤20/240/140…）          →  只是建议。代码既不校、不记、也不切
    "除 notes 外全部必填"        →  _clean_spec：缺一个当场拒
    "必须携带父的可测物理量"      →  inherits + 根锚点，当场拒绝
    "最多一个门槛"                →  门槛先做，不成立则分支作废
    "判定满足必须指得出证据"      →  指不出来就降级为未满足
    keywords                      →  出生时 register() 拿它扫老树 + 能力库
    conc_range                    →  上层给的区间会渲染进下层的形式字段
    外部需求四类                  →  EXTERNAL_CLASSES（tree/node.py）

入口（`prompts/intake.md`）是同一个协议的第一环：它交出来的 `root` 要过
 `_clean_spec` 加"验收标准必须有可测物理量"，所以它不可能塞进树检查不了的东西。

所以改提示词不用碰代码：直接改 `prompts/*.md`。
**自优化回路允许改的也只有这里** —— `PROMPT` 是可变层（见 evolve.py）。

设计与不变量的完整版在 `docs/DESIGN.md`；进度与交接在 `docs/HANDOVER.md`。
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(os.path.dirname(HERE), "prompts")


def load(name):
    with open(os.path.join(PROMPT_DIR, name + ".md"), encoding="utf-8") as f:
        return f.read()


ALLOC_SYS = load("alloc")
LEAF_SYS = load("leaf")
INTAKE_SYS = load("intake")      # 根节点的上层：只用一次，谈定预期就退场

# 可变层：自优化唯一被允许修改的东西。
PROMPT = {"alloc": ALLOC_SYS, "leaf": LEAF_SYS, "intake": INTAKE_SYS}
