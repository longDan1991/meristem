"""入口：把用户的一句话谈成根节点，**当场拿去跑，把结论带回来接着谈**。

它是这个程序**唯一的入口**（`main --intake`）。和"引导 LLM"不是一回事：
那条路要模型猜用户的话**指哪个节点**（路由），这条路只做入口，产物必须过
和分配节点**同一台闸门**（`protocol/gate.py` 的 `clean_spec` + "验收标准必须有
可测物理量"），所以它不可能偷偷塞进树检查不了的东西。

它自己没有手（没有 bash / read / write）。**手在树上**：谈成一个能过闸门的
`root`，就 `run()` 它，把结论作为一条外部观测送回对话，再接着谈。纪律：

  ① **交形式 ≠ 退场。** 每交一个 `root` 就跑一次、结论喂回，然后再次调模型。
     入口永不退场 —— 谈和跑交替进行，直到用户自己在终端上中止。
     所以没有"最终根"与"附加任务"之分：**每个 root 都是任务**。
     行不行不是聊出来的判断，而是树跑出来的事实（§2.7）。
  ② 用不了的东西当场打回，并把**为什么**说给它听，让它自己改 ——
     和树里同一个规矩：摆事实，不用计数器逼停。

**对话的形式不归代码管。** 模型要么在说话（纯文本，直接送给用户），
要么在交形式（`{"root": …}`）。所以这里只有一条识别规则：
**只有带 `root` 键的 JSON 才算形式，其余一律当"话"原样送出去。**
它是在和真人说话，不是在填表 —— 代码不认识"回合数"，也不规定"一次只能问一个"。
"""

from .llm import parse_json
from .protocol.fields import Node
from .protocol.gate import validate_root
from .prompts import INTAKE_SYS
from .runtime.scheduler import run


class _Spoken:
    """把模型吐出来的字转给终端 —— 但**只转「话」那一路**。

    模型要么说话（纯文本），要么交形式（带 root 的 JSON）。形式是给闸门的，
    不是给人看的：直接吐到屏幕上，用户会看到一坨 JSON。所以先按住不吐，
    看清头一个实义字符再定：`{` 就是形式（形式常被包在 ``` 围栏里，围栏先拨开），
    整段不吐；否则是话，把按住的先补吐出去，之后见一个字吐一个字。

    判断只做一次，不再改主意 —— 它和 `root_in` 一样，把「话 / 形式」当作
    模型输出开头就定了的事。（万一判成形式、其实不是，`ask` 那边会把整段
    原样补给人看，不会丢。）
    """

    def __init__(self, write=None):
        self.write = write or (lambda piece: None)
        self.buf, self.state = "", "?"

    def reset(self):
        self.buf, self.state = "", "?"

    def feed(self, piece):
        if self.state == "form":
            return
        if self.state == "talk":
            self.write(piece)
            return
        self.buf += piece
        s = self.buf
        if s.lstrip().startswith("```"):           # 形式常被包在 ```json 围栏里
            nl = s.find("\n")
            if nl < 0:
                return                              # 围栏那一行还没吐完
            s = s[nl + 1:]
        if not s.strip():
            return
        if s.lstrip()[0] == "{":
            self.state, self.buf = "form", ""
            return
        self.state = "talk"
        self.write(self.buf)
        self.buf = ""


def root_in(text):
    """输出里有没有"根的形式"。**只认带 root 键的 JSON** —— 别的都不是形式，
    是话说给用户听的（包括解析不出来的、和解析得出来但没有 root 的）。"""
    try:
        d = parse_json(text)
    except ValueError:
        return None
    if isinstance(d, dict) and isinstance(d.get("root"), dict):
        return d["root"]
    return None


def _run_root(spec, llm, env):
    """把谈成的形式跑成一棵真树，返回它的根（结论在 `root.conclusion`）。

    `env` 是 `main` 交给入口的运行现场（trace / caps / index / budget /
    workers / registry）—— 入口要跑树，就得知道跑在什么环境里；
    这是它区别于"只会说话的提示词"的地方。
    """
    root = Node(name=spec["name"], detail=spec["detail"], notes=spec["notes"],
                accept=spec["accept"], kind=spec["kind"],
                keywords=spec["keywords"], conc_range=spec["conc_range"])
    run(root, llm, env["trace"], registry=env.get("registry"),
        budget=env.get("budget"), workers=env.get("workers", 6),
        caps=env.get("caps"), index=env.get("index"),
        on_beat=env.get("on_beat"), beat=env.get("beat", 60))
    return root


def _result(root):
    """跑完的结论，写成一条能回填给入口的外部观测。

    用词说清楚"这是系统观测、不是用户说的话" —— 模型的对话里
    user 那条通道会同时装"用户"和"世界"，不加标记它会混。
    """
    lines = ["任务执行结果（系统观测，不是用户说的话）:",
             "任务: %s" % root.name,
             "判定: %s" % (root.verdict or "（没有判定）"),
             "结论: %s" % (root.conclusion or "（没有结论）")]
    if root.evidence:
        lines.append("证据: " + "；".join(str(x) for x in root.evidence))
    if root.external:
        lines.append("外部需求: " + "、".join(str(x) for x in root.external))
    return "\n".join(lines)


def intake(llm, msg, ask, env, on_say=None, on_delta=None, on_reasoning=None):
    """和用户谈，谈到形式就跑，跑完把结论带回来接着谈。**只在用户中止时停。**

    ask(text)          -> 用户的回答（真跑时就是 input()，测试里换成脚本）。
                          拿到的是模型那一段话的**原文**，代码不改写它。
    env                -> 运行现场（`trace`/`caps`/`index`/`budget`/`workers`/
                          `registry`），`main` 传进来；入口据此跑树。
    on_say(text)       -> 可选的**旁白**回调：打回理由、"接到任务/跑完了"走这里。
                          模型说的话走 ask 通道 —— 两条通道分开，
                          终端才不会把同一句话显示两遍。
    on_delta(text)     -> 可选的**吐字**回调：模型正在说的话一小口一小口送到这里。
                          交形式那一路不经过它（那是给闸门的，不是给人看的）。
    on_reasoning(text) -> 可选的**思考**回调：模型的 `reasoning_content` 走它。

    用户中止（不再输入）由 ask 那边抛 EOFError/KeyboardInterrupt 出来，
    这里不拦 —— 中止不是结论。
    """
    def say(t):
        if on_say:
            on_say(t)

    spoken = _Spoken(on_delta)
    msgs = [{"role": "system", "content": INTAKE_SYS},
            {"role": "user", "content": msg}]

    while True:
        spoken.reset()
        text = llm.chat(msgs, temperature=0.3, on_delta=spoken.feed,
                        on_reasoning=on_reasoning)
        spec = root_in(text)

        if spec is None:
            # 在说话：原样送到用户面前，代码不改写它、不往里添字。
            # 这里**不过 norm()** —— 那是形式字段的规范化（会压掉换行），
            # 而这是一段说给人听的话，分行是它意思的一部分。
            a = ask(str(text or "").strip())
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user", "content": str(a)})
            continue

        got, why = validate_root(spec)
        if got is None:
            # 交的形式用不了：把原因摆出来让它自己改（不是计数器）
            say("（入口交的东西用不了：%s）" % why)
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user",
                         "content": "这样不行：" + why + " 改一次再给。"})
            continue

        # 形式能过闸门 → 跑它。**这是入口唯一的手**。
        say("（接到任务：%s）" % got["name"])
        root = _run_root(got, llm, env)
        say("（跑完了：%s）" % (root.verdict or "没有判定"))
        # 结论作为**外部观测**回填（user 通道），然后接着调模型 ——
        # 入口会决定是接着讲这个结论，还是再开下一个任务。
        msgs.append({"role": "assistant", "content": text})
        msgs.append({"role": "user", "content": _result(root)})
