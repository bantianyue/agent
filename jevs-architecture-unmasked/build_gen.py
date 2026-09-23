# -*- coding: utf-8 -*-
# build_gen.py — 文本 DSL parser（S#/T/F/K/B 行）+ meta，产出 article_data.json
import os, json

D = os.path.dirname(os.path.abspath(__file__))
sections = []
cur = None

for raw in open(os.path.join(D, "content.txt"), encoding="utf-8"):
    line = raw.rstrip("\n").rstrip()
    if not line.strip():
        continue
    if line.startswith("S# "):
        cur = {"type": "h2", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
    elif line.startswith("T "):
        cur["paras"].append(line[2:].strip())
    elif line.startswith("F "):
        sp = line[2:].strip().split("|", 1)
        idx = len(cur["paras"]) - 1
        if idx < 0:
            cur["paras"].append("")
            idx = 0
        cur.setdefault("fig_after", {})[str(idx)] = cur.setdefault("fig_after", {}).get(str(idx), []) + [
            {"src": sp[0].strip(), "caption": sp[1].strip() if len(sp) > 1 else ""}]
    elif line.startswith("K "):
        sp = line[2:].strip().split("|", 1)
        fn = sp[0].strip()
        lang = sp[1].strip() if len(sp) > 1 else "text"
        code = open(os.path.join(D, fn), encoding="utf-8").read()
        cur["paras"].append("__CODE__" + lang + "::" + code)
    elif line.startswith("B "):
        parts = [p for p in line[2:].strip().split("|")]
        cells = [p.split(";", 1) for p in parts]
        cur["table"] = {"head": cells[0], "rows": [c for c in cells[1:]]}

# 去连排：相邻两图之间插分隔段
for s in sections:
    fa = s.get("fig_after", {})
    seq = []
    for i, p in enumerate(s["paras"]):
        seq.append(("T", p))
        if str(i) in fa:
            seq += [("F", g) for g in fa[str(i)]]
    out = []
    prev = None
    for k, v in seq:
        if k == "F" and prev == "F":
            out.append(("T", "(承接上图)"))
        out.append((k, v))
        prev = k
    np = []
    nfa = {}
    idx = -1
    for k, v in out:
        if k == "T":
            np.append(v)
            idx = len(np) - 1
        else:
            nfa.setdefault(str(idx), []).append(v)
    s["paras"] = np
    s["fig_after"] = nfa

# 越界断言
for s in sections:
    for k in s.get("fig_after", {}):
        assert int(k) < len(s["paras"]), "fig_after 越界: %s in %s (len=%d)" % (k, s["title"], len(s["paras"]))

data = {
    "title": "拆解 Jev 的架构：不生成文本、直接输出概率的决策模型",
    "summary": [
        {"key": "核心结论", "body": "Jev 大概率是因果 transformer：共享状态前缀、隔离问题后缀、直接概率读出，推理止于 prefill。"},
        {"key": "关键实验", "body": "参考卡、无关选项、分箱校准三组探测分别证实全列表读出、选项交互与结果训练的概率。"},
        {"key": "存疑部分", "body": "稀疏 MoE 骨干与读出头形式（槽位头或指针式）无法从 API 外部确证。"},
    ],
    "lead": [
        "Jev 用针对结果训练的决策概率替代生成的置信度文本：输入共享状态、问题与允许答案，并行返回概率分布，不生成任何文本。TypeSafe 不公开研究细节，这里用 API 探测加公开资料，从黑盒外部重构它的架构。",
    ],
    "sections": sections,
    "conclusion": [
        "**Jev 重构的价值不在单个部件多新，而在组合指向同一个结论：决策不必先变成文本。**参考卡、无关选项、分箱校准三组实验从黑盒外部钉住三件事：答案计算看得到完整选项列表、选项之间存在真实交互、概率是针对结果训练出来的；真正悬而未决的只剩稀疏 MoE 骨干，与槽位头还是指针式读出。",
        "对做分类、路由、风控系统的人，值得带走的是把概率当一等公民的设计：prefill 后直接读出、状态只算一次、confidence 字段与预测分布严格分开。评估这类模型时，排列测试与分箱校准应当进清单。",
    ],
    "reference_url": "https://archerhume.com/posts/jevs-architecture-unmasked/",
}

# 校验
n_figs = sum(len(v) for s in sections for v in s.get("fig_after", {}).values())
n_paras = sum(len(s["paras"]) for s in sections)
n_code = sum(1 for s in sections for p in s["paras"] if isinstance(p, str) and p.startswith("__CODE__"))
n_tbl = sum(1 for s in sections if s.get("table"))
body_chars = sum(len(p) for s in sections for p in s["paras"] if isinstance(p, str) and not p.startswith("__CODE__"))
cjk = sum(1 for s in sections for p in s["paras"] if isinstance(p, str) and not p.startswith("__CODE__") for ch in p if "\u4e00" <= ch <= "\u9fff")
print("sections=%d paras=%d figs=%d code=%d table=%d bodychars=%d cjk=%d" % (len(sections), n_paras, n_figs, n_code, n_tbl, body_chars, cjk))
assert n_figs == 5, "应 5 张图"
assert n_code == 4, "应 4 个代码块"
assert n_tbl == 1, "应 1 张表"
assert cjk > 3000, "中文字符不足"

with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("article_data.json written")
