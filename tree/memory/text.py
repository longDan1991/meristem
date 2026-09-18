"""词法匹配：拉丁词 + 两位以上数字 + 多字中文词。索引与能力库共用同一套。

分词就是 `jieba.cut`，不再自己加规则；只留**一道闸：单字不算词**。

为什么必须有这道闸（实测教训，DESIGN §5.1）：jieba 会把虚字（的/到/和/在）
切成单字，也会把标点 / 空格 / 单个数字切成单 token。虚字和单数字几乎出现在
所有文本里，收进来会让任何两句话都能对上 —— 查询"算 1 到 100 的和"会命中
"构建币种名称到的映射表"、"净值为 1"这类无关节点。多字词和成形的拉丁词才携带信息。
"""

import jieba

# 首次建词典会打 "Building prefix dict..."，压掉：这不是我们该给用户看的东西。
jieba.setLogLevel(60)


def tokens(text):
    out = set()
    for tok in jieba.cut(text or ""):
        tok = tok.strip().lower()
        if len(tok) <= 1 or not tok.isalnum():
            continue
        out.add(tok)
    return out


def overlap(q, hay):
    """两个 token 集的重合度。

    中文词直接重合 + 拉丁词/数字允许前缀匹配（http↔https, broker↔mock_broker）。
    """
    n = len(q & hay)
    ql = {t for t in q if t.isascii() and len(t) >= 4}
    hl = {t for t in hay if t.isascii() and len(t) >= 4}
    for a in ql:
        if any(b != a and (b.startswith(a) or a.startswith(b)) for b in hl):
            n += 1
    return n
