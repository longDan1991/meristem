#!/usr/bin/env python3
"""工具层的纪律测试（修"叶子把同一文件读了 25 次"的 bug 换来的）。

  · read 是翻页不是截断：报出总量、本段区间、怎么取下一段（A/B）
  · bash 输出不截断：跑出多少就是多少（C）
  · bash 必须带超时，超时是可见的事实（D）
  · bash 输出不被压缩、逐字到达，rm 真删文件（E）
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from harness import OK, line
import tools.bash as T      # bash 工具独立在 tools/bash.py
import tools.defs as TD     # read / 取回工具在 tools/defs.py
import tools.skills as TS   # Agent-Reach skill：SkillProvider 挂载 + read_skill 桥


class _Store:
    """最小假 store：bash / read / write 只用到 registry 和 record。"""

    def __init__(self):
        self.registry = {"n": None}

    def record(self, *a, **k):
        pass


class _Loop:
    def __init__(self):
        self.store = _Store()
        self.say = None


def bash(*a, **k):
    """bash 是真异步，测试里用同步壳调它，返回模型看到的观测文本。"""
    return asyncio.run(T.bash(*a, _b=(_Loop(), "n"), **k))["text"]


def read(*a, **k):
    return asyncio.run(TD.read(*a, _b=(_Loop(), "n"), **k))["text"]

def main():
    p = "/tmp/_t_tools.txt"
    with open(p, "w") as f:
        f.write("\n".join("第%d行" % i for i in range(1, 1201)))   # ~ 9000 字

    print("=" * 78)
    print("A. read 报出总量 / 本段区间 / 怎么取下一段")
    head = read(p)
    print("  %s" % head.split("\n")[0])
    line("有总量", "共" in head and "字" in head)
    line("有本段区间", "本段" in head)
    line("说清还有多少字", "还有" in head and "未显示" in head)
    line("给出翻页办法", "offset=" in head)

    print("=" * 78)
    print("B. read 能翻页，翻到的是不同的内容")
    tail = read(p, offset=4000)
    print("  第二段开头: %s" % tail.split("\n")[1])
    line("两段内容不同", tail.split("\n")[1] != head.split("\n")[1])
    line("翻到末尾时明说已到末尾", "未显示" not in read(p, offset=20000))

    print("=" * 78)
    print("C. bash 输出不截断：跑出多少就是多少")
    big = bash("python3 -c \"print('x' * 70000)\"")
    line("70000 字完整返回（没有截断标记）", len(big) >= 70000 and "截断" not in big,
         "%d 字" % len(big))

    print("=" * 78)
    print("D. bash 必须带超时，而且超时是可见的 / 可调的 / 会连子进程一起杀")
    out = bash("echo 先打一行; sleep 30", timeout=2)
    print("  超时观测（末两行）: %s" % " / ".join(out.strip().splitlines()[-2:]))
    line("明说是超时，不是「工具出错」", "[超时]" in out and "工具出错" not in out)
    line("已经产生的输出被带回来了", "先打一行" in out)
    line("说了上限和怎么跑更久", "上限" in out and "nohup" in out)

    # 留不留孤儿：子进程 3 秒后去碰一个文件，没被一起杀就会看到它
    orphan = "/tmp/_t_orphan_%d" % os.getpid()
    if os.path.exists(orphan):
        os.remove(orphan)
    bash("sh -c 'sleep 3; touch %s' & echo 起了个子进程; sleep 30" % orphan,
           timeout=1)
    time.sleep(4)
    line("超时把子进程也一起杀了（没留孤儿）", not os.path.exists(orphan))

    # 把上限改小，否则要等一小时才能验这一条
    _saved = (T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX)
    T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX = 1, 2
    try:
        o1 = bash("sleep 30", timeout=99999)
        line("超上限会被夹住并明说", "被夹到上限" in o1 and "99999" in o1)
        o2 = bash("sleep 30")          # 不给 timeout → 用默认
        line("不给 timeout 也一定有超时（走默认）", "[超时]" in o2 and "上限" in o2)
        o3 = bash("sleep 2", timeout=0)  # 0 = 不限时（对齐 oh-my-pi：禁用 deadline）
        line("timeout=0 不限时（不被夹成默认）", "[超时]" not in o3)
    finally:
        T.BASH_TIMEOUT, T.BASH_TIMEOUT_MAX = _saved

    print("=" * 78)
    print("E. bash 输出不压缩：逐字到达、没有取回标记")
    edir = "/tmp/_t_tools_ls_%d" % os.getpid()
    if not os.path.isdir(edir):
        os.makedirs(edir)
    for i in range(300):
        with open(os.path.join(edir, "f_%03d.txt" % i), "w") as f:
            f.write("x" * 100)
    obs = bash("ls -la %s" % edir)
    line("bash 输出不被压缩（没有 [压缩] / 取回标记）",
         "[压缩]" not in obs and "hash=" not in obs)
    line("bash 输出逐字保留（300 个文件的行都在）",
         "f_000.txt" in obs and "f_299.txt" in obs)

    print("=" * 78)
    print("E2. bash 的 rm 真的把文件删掉")
    victim = os.path.join(edir, "victim.txt")
    with open(victim, "w") as f:
        f.write("要被删掉的东西")
    bash("rm %s" % victim)
    line("文件确实被删了", not os.path.exists(victim))

    print("=" * 78)
    print("F. 会话池：并发 bash 真并行（持久 shell 忙时降级 one-shot）")
    async def _two():
        return await asyncio.gather(
            T.bash("sleep 0.8", _b=(_Loop(), "n")),
            T.bash("sleep 0.8", _b=(_Loop(), "n")))
    t0 = time.monotonic()
    asyncio.run(_two())
    line("两条并发 bash 并行完成（<1.5s 而非串行 1.6s）",
         time.monotonic() - t0 < 1.5, "%.2fs" % (time.monotonic() - t0))

    print("=" * 78)
    print("G. 通用 skill 加载：SKILLS_DIRS 扫描 + read_skill 按需读")

    # 临时 skills 根目录，两个 skill（目录名 = skill 名；frontmatter 的 name/description
    # 是检索面；缺 description 时 fastmcp 退回正文首行）
    root = tempfile.mkdtemp(prefix="_t_skills_")
    os.makedirs(os.path.join(root, "demo-a", "references"))
    with open(os.path.join(root, "demo-a", "SKILL.md"), "w") as f:
        f.write("---\nname: demo-a\ndescription: 演示技能 A，用于读网页\n---\n# A 路由表\n用 curl 读网页。")
    with open(os.path.join(root, "demo-a", "references", "web.md"), "w") as f:
        f.write("# A 重试链\nr.jina.ai 挂了换 readability。")
    os.makedirs(os.path.join(root, "demo-b"))
    with open(os.path.join(root, "demo-b", "SKILL.md"), "w") as f:
        f.write("---\nname: demo-b\n---\n# B 技能\n无 description 时取正文首行。")
    with open(os.path.join(root, "secret.txt"), "w") as f:
        f.write("绝密内容")

    dp = SkillsDirectoryProvider(roots=root)
    m = FastMCP("t")
    m.add_provider(dp)
    line("扫描出两个 skill（目录名 = skill 名）",
         [n for n, _ in TS.discovered(dp)] == ["demo-a", "demo-b"])
    line("description 是检索面（frontmatter 的 description 进清单）",
         any(d == "演示技能 A，用于读网页" for _, d in TS.discovered(dp)))
    line("缺 description 的 skill 退回正文首行",
         any("B 技能" in d for _, d in TS.discovered(dp)))
    a = asyncio.run(TS._read_skill(m, "skill://demo-a/SKILL.md"))
    line("skill://<名>/SKILL.md 按需读得到", "A 路由表" in a and "curl" in a)
    web = asyncio.run(TS._read_skill(m, "skill://demo-a/references/web.md"))
    line("skill 子文件读得到（模板 URI）", "A 重试链" in web)
    man = asyncio.run(TS._read_skill(m, "skill://demo-a/_manifest"))
    line("_manifest 给出文件清单", '"references/web.md"' in man and '"SKILL.md"' in man)
    b = asyncio.run(TS._read_skill(m, "skill://demo-b/SKILL.md"))
    line("第二个 skill 同样可读", "B 技能" in b)
    bad = asyncio.run(TS._read_skill(m, "skill://demo-a/references/nope.md"))
    line("读不存在的文件 → 带上下文的错误", "工具出错" in bad and "nope.md" in bad)
    esc = asyncio.run(TS._read_skill(m, "skill://demo-a/../secret.txt"))
    line("越过 skill 根读父级文件被拒（没泄漏）",
         "工具出错" in esc and "绝密" not in esc)
    empty = asyncio.run(TS._read_skill(m, "skill://demo-a/"))
    line("空路径（skill://demo-a/）→ 契约错误不炸穿", "工具出错" in empty and "文件路径" in empty)
    oth = asyncio.run(TS._read_skill(m, "skill://nosuch/SKILL.md"))
    line("没注册的 skill 读不到（错误带上下文）", "工具出错" in oth and "nosuch" in oth)
    nores = asyncio.run(TS._read_skill(FastMCP("empty"), "skill://demo-a/SKILL.md"))
    line("没挂载 provider → 读不到也给上下文", "工具出错" in nores)
    shutil.rmtree(root)

    print("=" * 78)
    print("全部通过" if all(OK) else "有失败项")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
