"""共享测试基建：仓库根上路径 + 断言助手。

测试以脚本方式运行（`python3 tests/test_x.py`），sys.path[0] 是 `tests/`；
本模块把仓库根插进 sys.path，测试才 import 得到 `core` / `tools` / `terminal`。

`line` / `OK` 原来在 8 个测试文件里逐字各抄一份，收在这里：行宽统一 %-50s，
没有任何测试依赖具体行宽（`line` 只打点、不参与断言）。
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

OK = []


def line(tag, cond, detail=""):
    """一条断言：✓/✗ 打点，收进 OK 供最后 all() 汇总，并返回布尔值。

    返回值给 `ok &= line(...)` 这种累加写法用（test_protocol）；只看打点的文件
    忽略返回值即可。
    """
    cond = bool(cond)
    print("  %s %-50s %s" % ("✓" if cond else "✗", tag, detail))
    OK.append(cond)
    return cond
