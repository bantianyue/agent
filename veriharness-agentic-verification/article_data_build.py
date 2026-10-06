#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

BENCH_TABLE = {
    "head": ["Benchmark", "任务数", "领域", "交付物", "评分方式"],
    "rows": [
        ["APEX-Agents (v1.0)", "480", "银行/法律/咨询", "备忘录、模型、答案", "专家细则"],
        ["Workspace-Bench Lite", "100", "重文件workspace", "文档与文件", "细则裁判"],
        ["WorkBuddy Bench", "200", "代码/办公/网页", "补丁与办公文件", "复合验证器"],
        ["SpreadsheetBench 2", "321", "商业表格", "工作簿", "重算比对"],
        ["JobBench", "65", "35个白领职业", "多文件交付物", "细则裁判"],
    ],
}

RESULTS_TABLE = {
    "head": ["方法", "平均", "APEX", "WSB", "WorkBuddy", "SB-2", "JobBench"],
    "rows": [
        ["Flash · 单rollout", "47.2", "48.1", "56.5", "73.2", "27.3", "30.9"],
        ["Flash · 多数投票", "47.5", "47.3", "57.0", "74.0", "27.0", "32.4"],
        ["Flash · LLM-as-a-Verifier", "49.5", "49.8", "60.4", "75.3", "30.2", "31.9"],
        ["Flash · Agentic verifier（有环境访问）", "49.4", "49.0", "60.1", "75.1", "30.9", "31.8"],
        ["Flash · VeriHarness（选择）", "51.6", "53.3", "62.0", "77.8", "31.5", "33.5"],
        ["Flash · VeriHarness（修订）", "53.4", "54.8", "65.4", "78.2", "32.2", "36.2"],
        ["Opus · VeriHarness（选择）", "53.7", "41.2", "65.0", "83.0", "33.4", "46.1"],
        ["Opus · VeriHarness（修订）", "56.1", "47.5", "67.3", "83.7", "34.3", "47.6"],
        ["相对单rollout增益（修订）· Flash", "+6.2", "+6.7", "+8.9", "+5.0", "+4.9", "+5.3"],
        ["相对单rollout增益（修订）· Opus", "+6.4", "+11.7", "+6.8", "+4.7", "+4.2", "+4.8"],
    ],
}

sections = []
cur = None
fig_count = 0
prev_was_fig = False

for raw in open(os.path.join(D, "content1.txt"), encoding="utf-8"):
    line = raw.rstrip("\n")
    if not line.strip():
        continue
    if line.startswith("S# "):
        cur = {"type": "h2", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("H# "):
        cur = {"type": "h3", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("T# "):
        assert cur is not None, "T before first S#"
        body = line[3:].strip()
        if body == "TBL#benchmarks":
            cur["table"] = BENCH_TABLE
        elif body == "TBL#mainresults":
            cur["table"] = RESULTS_TABLE
        else:
            cur["paras"].append(body)
        prev_was_fig = False
    elif line.startswith("F# "):
        assert cur is not None, "F before first S#"
        assert not prev_was_fig, "相邻 F 行：多图连排，需在内容文件里插 T 段隔开"
        rest = line[3:].strip()
        src, cap = rest.split("|", 1)
        i = max(0, len(cur["paras"]) - 1)
        key = str(i)
        cur["fig_after"].setdefault(key, []).append({"src": src.strip(), "caption": cap.strip()})
        fig_count += 1
        prev_was_fig = True
    else:
        print(f"未知行前缀，已跳过: {line[:40]}", file=sys.stderr)

for s in sections:
    n = len(s["paras"])
    for k in s["fig_after"]:
        assert int(k) < n, f"fig_after 越界: section={s['title'][:20]} key={k} paras={n}"

missing = []
for s in sections:
    for figs in s["fig_after"].values():
        for f in figs:
            if not os.path.exists(os.path.join(D, f["src"])):
                missing.append(f["src"])
assert not missing, f"图文件缺失: {missing}"

DATA = {
    "title": "VeriHarness扩展长时任务的Agentic验证",
    "summary": [
        {"key": "验证带进环境", "body": "不靠投票或裁判打分：分歧解决器拿竞争性claim对源文件、数据、任务约束；共识挑战器设想共识值可能错在哪再检验。同一模型、同一工具，不借更强裁判。"},
        {"key": "两路调查再裁决", "body": "分歧与共识检查跑在独立上下文，互不挤占；全新上下文复核两份证据记录，输出base rollout、修订计划、未决claim清单，修改全程可追溯。"},
        {"key": "数据与自我演进", "body": "5个benchmark、2个模型上selection全部第一；证据修订相对单rollout平均+6.2/+6.4分。从空库演化的skill超过人工库，约2.6万个rollout已开源。"},
    ],
    "lead": [
        "多数投票选出的答案，可能是错的；所有rollout一致的答案，也可能是错的。在Claude Opus 4.8的十rollout池子里，34%的一致取值被判错误，分歧claim里74%含有正确候选。长时agent的交付物越做越复杂，验证正在成为与生成并列的核心挑战。",
        "VeriHarness给出一种不依赖更强裁判的验证方案：让生成器自己的模型当验证器，给它workspace、证据工具、可复用的验证skill，把rollout间的分歧与共识逐条拿到环境证据面前检验，再裁决、再修订。",
    ],
    "sections": sections,
    "conclusion": [
        "**验证能力不必等更强的模型。**VeriHarness用生成器自己的模型解决分歧、挑战共识：5个workspace benchmark、2个模型上selection全部第一；证据支撑的修订让相对单rollout的平均增益在两个模型上都超过6分；从失败反馈演化出的skill在held-out任务上超过人工编写的库。",
        "对做长时agent与test-time scaling的人，这套harness是即插即用的验证底座：协议与skill不绑定某一家agent实现，Gemini CLI、Claude Code、Codex里都能跑。约2.6万个rollout（成本超10万美元）已开源，是研究agentic验证的现成材料。下一步值得看的是验证记录能否变成训练长时agent的claim级监督信号。",
    ],
    "reference_url": "https://arxiv.org/html/2610.00972v1",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
