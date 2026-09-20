"""提示词。单独放一个目录，因为它们是**协议的一部分**。

每条硬性要求都对应 `tree/protocol/gate.py` 里的一处代码检查 —— 改一边就得看另一边：

    字数（≤20/240/140…）          →  只是建议。代码既不校、不记、也不切
    "除 notes 外全部必填"        →  clean_spec：缺一个当场拒
    "必须携带父的可测物理量"      →  inherits + 根锚点，当场拒绝
    "最多一个门槛"                →  门槛先做，不成立则分支作废
    "判定满足必须指得出证据"      →  指不出来就降级为未满足
    kind                          →  clean_spec：只能是 dispatch / leaf，不给兜底
    conc_range / lineage          →  上层给的区间、从根到上层的意图链，都会渲染进下层的形式字段
    渲染的段落                     →  文档点名的段落 == 真渲染的段落
                                     （tests/test_protocol.py 的 I 段双向核对）
    收到的行首                     →  就是 name/detail/notes/accept/kind/gate/conc_range 这 7 个键（同构）
    外部需求四类                  →  EXTERNAL_CLASSES（tree/protocol/fields.py）

入口（`prompts/intake.md`）是同一个协议的第一环：它交出来的 `root` 要过
 `clean_spec` 加"验收标准必须有可测物理量"，所以它不可能塞进树检查不了的东西。

节点与模型之间的**通道是工具调用**（`tree/protocol/tool_specs.py`）：
字段的"本质"说明在 schema 的 description 里（provider 会原样喂给模型），
流程与长规则在 `prompts/*.md`。所以改字段含义看 tool_specs.py，
改"什么时候用什么工具/怎么判断"看 md —— 两边都要和 gate.py 对着看。

设计与不变量的完整版在 `docs/DESIGN.md`；进度与交接在 `docs/HANDOVER.md`。
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(os.path.dirname(HERE), "prompts")


def load(name):
    with open(os.path.join(PROMPT_DIR, name + ".md"), encoding="utf-8") as f:
        return f.read()


NODE_SYS = load("alloc")
LEAF_SYS = load("leaf")
INTAKE_SYS = load("intake")      # 唯一入口：谈成一个形式就跑、结论带回再谈

PROMPT = {"alloc": NODE_SYS, "leaf": LEAF_SYS, "intake": INTAKE_SYS}
