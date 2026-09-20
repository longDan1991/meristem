"""executor：模型写的**一段代码**跑在一个 CPython 子进程里，工具通过 fd 协议回调宿主。

为什么不是沙箱（Monty 那类）：叶子本来就有 bash —— 任意宿主机执行。
给"编排代码"加沙箱等于给一个已经握着钥匙的人装防盗门，代价却是那套
Python 子集（没有 pandas / numpy / glob / async with），而我们整个项目
就在那个世界里。所以这里用**同一个信任级别**：子进程就是一个普通 CPython，
和 bash 跑起来的东西一样。

协议（stdout 一行一个 JSON，注意**不是** stderr）：

    子 → 宿主   {"call": "<tool_id>", "args": {...}}
    宿主 → 子   {"result": ...} / {"error": "..."}

子进程的 `print` 走 stderr —— **整份 stderr 就是观测**，不截断（跑出多少
就是多少，完整流到压缩层），成败判定用 `tools.ok_obs`（工具出错 / exit 码）。

两件事是刻意的：
  · 观测落**文件**不落管道：子进程话多的时候，管道写满就会把它卡死。
  · 超时在**子进程里**触发（SIGALRM）：`while True: pass` 这类纯 Python
    死循环能被它打断，而且"超时"是以一条观测的形式告诉模型的，不是静默杀掉。
    等宿主的那段时间**不算**进去 —— 一条跑 20 分钟的 bash 不该吃掉代码的额度。

产出是怎么报上来的：子进程把 `open(..., 'w')` / `os.open(..., O_WRONLY)` 的路径
记下来，收尾时一次性报回宿主。所以看得见的是**这一层**（它是常见情形：代码里
直接写文件），而子进程自己再起的孙子进程写的看不见 —— 跟以前靠解析命令是同一个
盲区（`effects.effects_of` 也只看命令里写明的目标），不是新引入的。
"""

import ast
import asyncio
import json
import os
import signal
import subprocess
import sys
import time

from ..config import SNIPPET_DIR
from ..tools import ok_obs

# 一段代码自己能跑多久（不含等宿主的时间）。这是**活性兜底**，不是预算：
# 一个死循环会把整个节点钉死，和 bash 必须有超时是同一件事。
SNIPPET_TIMEOUT = 600
# 宿主侧的硬杀线：子进程连 SIGALRM 都没被中断（卡在 C 里）时，最后一道。
HOST_GRACE = 30

PRIMITIVES = ("bash", "read", "write")

# 三只手永远都在（它们是**逃生口**：没做过的事只能靠它们，做过的事靠 cap）。
# 每行后面那句就是模型在代码里看到的用法 —— 和 `prompts/leaf.md` 说的同一套。
PRIMITIVE_BINDINGS = (
    'bash  = _api("bash")    # bash(cmd="...", timeout=120)：默认 120 秒，上限 3600 秒',
    'read  = _api("read")    # read(path="...", offset=0, limit=2000)：返回里写清还有多少字',
    'write = _api("write")   # write(path="...", content="...")',
)

# 拼在模型代码前面的那段。它定义 `_call` / `_api` / `search_tools`，
# 以及几行 `<名字> = _api("<tool_id>")` 的绑定（由 `Box.bindings` 生成）。
# 超时从环境变量读，免得往这段源码里做模板替换。
BOOTSTRAP = '''\
import atexit
import builtins
import functools
import json
import os
import signal
import sys
import time

_budget = float(os.environ.get("TREE_SNIPPET_TIMEOUT") or 0)
_deadline_at = time.monotonic() + _budget


def _rearm():
    left = _deadline_at - time.monotonic()
    signal.alarm(max(1, int(left)))


def _deadline(signum, frame):
    _report_writes()
    sys.stderr.write("\\n[超时] 这段代码已经跑了 %g 秒（不含等工具的时间），被中止了。"
                     "要跑很久的事：用 bash 起后台任务（nohup ... > run.log 2>&1 &）再轮询。\\n"
                     % _budget)
    sys.stderr.flush()
    os._exit(124)


if _budget:
    signal.signal(signal.SIGALRM, _deadline)
    _rearm()

_stdout = sys.stdout          # 协议通道（真的 fd 1）
sys.stdout = sys.stderr       # 模型的 print 进观测


def _call(tool, **args):
    """一次调用交给宿主，等它的回答。等的时候时钟不走 —— 那不是代码在跑。"""
    global _deadline_at
    signal.alarm(0)
    t0 = time.monotonic()
    _stdout.write(json.dumps({"call": tool, "args": args}, ensure_ascii=False) + "\\n")
    _stdout.flush()
    line = sys.stdin.readline()
    _deadline_at += time.monotonic() - t0
    _rearm()
    if not line:
        raise RuntimeError("宿主不再回答了（这段代码已被中止，或宿主已经退出）")
    reply = json.loads(line)
    if "error" in reply:
        raise RuntimeError(reply["error"])
    return reply["result"]


def _api(tool):
    return functools.partial(_call, tool)


def search_tools(query):
    """运行时找工具：命中什么，就当场装成可调用的函数。"""
    r = _call("search", query=query)
    for t in r["tools"]:
        globals()[t["name"]] = _api(t["id"])
    names = ", ".join(t["name"] for t in r["tools"]) or "(没有命中可以调用的工具)"
    return "已装成函数: %s" % names + chr(10) + r["text"]


# 自己报产出：宿主据此知道“这个节点写了什么”，不需要去 diff 整个工作区
# （工作区是共享的，diff 会把别的节点写的算到它头上）。
_wrote = []
_reported = [False]


def _report_writes():
    if _reported[0]:
        return
    _reported[0] = True
    if _wrote:
        try:
            _call("wrote", paths=_wrote)
        except Exception:
            pass


_builtin_open = builtins.open


def _traced_open(file, mode="r", *a, **kw):
    if (isinstance(file, (str, bytes, os.PathLike))
            and any(c in str(mode) for c in "wax+")):
        _wrote.append(os.fspath(file))
    return _builtin_open(file, mode, *a, **kw)


builtins.open = _traced_open
_os_open = os.open


def _traced_os_open(path, flags, *a, **kw):
    if (isinstance(path, (str, bytes, os.PathLike))
            and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)):
        _wrote.append(os.fspath(path))
    return _os_open(path, flags, *a, **kw)


os.open = _traced_os_open
atexit.register(_report_writes)

'''


def _with_result(src):
    """最后一行是个表达式就把它打出来 —— 和别处的 code-mode 手感一致：
    中间结果留在子进程，只有最后那个值回到观测里。解析不了就原样交给子进程
    去报 SyntaxError（错误要由它来说，别在这里吞掉）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return src
    last = tree.body[-1]
    if (isinstance(last.value, ast.Call)
            and isinstance(last.value.func, ast.Name)
            and last.value.func.id == "print"):
        return src                      # 已经是 print(...)，再包一层只会回一个 None
    tree.body.pop()
    call = ast.Expr(value=ast.Call(
        func=ast.Name(id="print", ctx=ast.Load()),
        args=[ast.Call(func=ast.Name(id="repr", ctx=ast.Load()),
                       args=[last.value], keywords=[])],
        keywords=[]))
    tree.body.append(call)
    return ast.unparse(tree)


def _header(tools, box):
    caps = box.bindings(tools)
    hint = ("# 上面的 %d 行是检索命中的现成做法；想再找就调 search_tools(\"...\")"
            % len(caps)) if caps else \
           "# 本次没有命中现成工具；用 bash / read / write 动手，或 search_tools(\"...\") 再找"
    return (BOOTSTRAP + "\n".join(list(PRIMITIVE_BINDINGS) + caps) + "\n"
            + hint + "\n\n")


async def _pump(proc, box, hands, calls, wrote, trace, node_id, deadline):
    """边读边答。**不能攒着一起处理** —— 子进程发完一次调用就阻塞着等回答。

    用 `read(65536)` 攒着拆行，而不是 readline：管道有数据不等于有一整行，
    子进程死在半行上时 readline 会永久阻塞，一个节点就此卡死。
    返回是否宿主侧超时。
    """
    buf, timed_out = b"", False
    while True:
        try:
            chunk = await asyncio.wait_for(proc.stdout.read(65536), timeout=1.0)
        except asyncio.TimeoutError:
            if proc.returncode is not None:
                break                       # 子进程已退出，只是缓冲里没剩数据
            if time.monotonic() > deadline:
                timed_out = True
                break
            continue
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            await _answer(proc, line.decode("utf-8", "replace"),
                          box, hands, calls, wrote, trace, node_id)
    return timed_out


def _kill(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except OSError:
        proc.kill()


def _observe(log_path, timed_out, rc):
    """观测 = 子进程的 stderr（+ 超时 / 退出码这两条事实）。

    不截断：跑出多少就是多少，完整流到压缩层。超时/退出码是运行事实，照记。
    """
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            out = f.read()
    except OSError:
        out = ""
    out = out.strip()
    if timed_out:
        out = (out + "\n[宿主侧超时] 这段代码超过 %d 秒被硬杀（连 SIGALRM 都没被打断）。"
               % (SNIPPET_TIMEOUT + HOST_GRACE)).strip()
    if rc:
        out = (out + "\n[exit=%d]" % rc).strip()
    return out or "(没有输出)"


async def run(code, tools, box, hands, trace=None, node_id=None, cwd=None):
    """跑一段模型写的代码。返回 (观测文本, 这次真的发生过的调用列表)。

    调用列表的每一项是 (tool, args, obs)，形状和旧的动作记录一样 ——
    能力挖掘（`mine.caps_from_node`）读的就是它，所以学能力的回路没变。
    真异步（P4）：`asyncio.create_subprocess_exec`，不占线程。
    """
    os.makedirs(SNIPPET_DIR, exist_ok=True)
    stamp = "%d_%d" % (time.time_ns(), os.getpid())
    script = os.path.join(SNIPPET_DIR, "snippet_%s.py" % stamp)
    log = os.path.join(SNIPPET_DIR, "snippet_%s.log" % stamp)
    with open(script, "w", encoding="utf-8") as f:
        f.write(_header(tools, box) + _with_result(code))

    env = dict(os.environ, TREE_SNIPPET_TIMEOUT=str(SNIPPET_TIMEOUT),
               PYTHONIOENCODING="utf-8")
    calls, wrote, timed_out = [], [], False
    rc = 0
    try:
        logf = open(log, "wb")
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, script, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=logf, cwd=cwd, env=env,
                start_new_session=True)
            try:
                timed_out = await _pump(
                    proc, box, hands, calls, wrote, trace, node_id,
                    time.monotonic() + SNIPPET_TIMEOUT + HOST_GRACE)
                if timed_out:
                    _kill(proc)
                rc = await asyncio.wait_for(proc.wait(), timeout=10)
            except asyncio.TimeoutError:
                _kill(proc)
                rc = await proc.wait()
            finally:
                # 编程错误从上面冒出来时也要收尾：子进程不许留下（fail fast，
                # 但别把一个跑着的进程挂在后面）。
                if proc.returncode is None:
                    _kill(proc)
                    await proc.wait()
                try:
                    proc.stdin.close()
                except (OSError, ValueError):
                    pass
        finally:
            logf.close()
        obs = _observe(log, timed_out, rc)
    finally:
        for p in (script, log):
            try:
                os.remove(p)
            except OSError:
                pass                          # 清理失败不值得让这一回合失败
    return obs, calls, wrote


async def _answer(proc, line, box, hands, calls, wrote, trace, node_id):
    """把子进程的一次调用转给宿主，并把结果写回去。"""
    try:
        req = json.loads(line)
    except ValueError:
        return                                # 不是协议行就不理它
    tool = str(req.get("call") or "")
    args = req.get("args") or {}
    try:
        reply, event = await _dispatch(tool, args, box, hands, calls, wrote)
    except (ValueError, KeyError, OSError) as e:
        # 参数不对 / 世界不给做 → 变成子进程里的一个异常，模型看得见并据此改路。
        # **编程错误不在里面**（TypeError 之类照旧往上炸，§2）。
        reply, event = {"error": "%s: %s" % (type(e).__name__, e)}, None
    if trace is not None:
        # obs 一并落盘：离线挖能力（`mine.mine_trace`）读的就是它 ——
        # "成功的命令"这个判据在观测里（工具出错 / exit 码）。
        trace.add(node_id, "code_call",
                  {"tool": tool, "args": args, "obs": reply.get("result"),
                   "error": reply.get("error")})
        if event:
            trace.add(node_id, "cap_outcome", event)
    try:
        proc.stdin.write((json.dumps(reply, ensure_ascii=False) + "\n").encode())
        await proc.stdin.drain()
    except (OSError, ValueError):
        pass                                  # 子进程已经死了：没有下家了


async def _dispatch(tool, args, box, hands, calls, wrote):
    """执行一次调用。返回 (给子进程的回复, 要记进 trace 的复用事件)。"""
    if tool in PRIMITIVES:
        obs = str(await hands.run(tool, args))
        calls.append((tool, args, obs))
        event = None
        if tool == "bash":
            # 把配方照抄到 bash 里跑，也算用过了那条能力（自清洁靠它）
            ok = ok_obs(obs)
            eid = box.note_reuse(args.get("cmd"), ok)
            event = {"cap": eid, "ok": ok} if eid else None
        return {"result": obs}, event
    if tool == "wrote":
        # 子进程自己报它写了哪些文件（代码里直接 open 的那部分）
        wrote.extend(args.get("paths") or [])
        return {"result": None}, None
    if tool == "search":
        tools, text, _ = box.search(args.get("query", ""))
        return {"result": {"tools": tools, "text": text}}, None
    if tool.startswith("cap:"):
        obs, cmd = await box.call(tool, args)
        calls.append(("bash", {"cmd": cmd}, obs))
        return {"result": obs}, {"cap": tool.split(":", 1)[1], "ok": ok_obs(obs)}
    return {"error": "没有这个工具: %s（只有 %s，以及上面列出的 cap）"
                     % (tool, " / ".join(PRIMITIVES))}, None
