#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#/C#) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

PROTOCOL_TABLE = {
    "head": ["操作", "说明"],
    "rows": [
        ["upload", "上传源代码、张量、字节、编译产物或文件。"],
        ["get_function", "从已上传的模块或库中选取命名函数/对象。"],
        ["run", "带参数调用函数，绑定返回值。"],
        ["return", "从响应中选取此前的值、文件或目录。"],
    ],
}

sections = []
cur = None
fig_count = 0
code_count = 0
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
        if body == "TBL#protocol":
            cur["table"] = PROTOCOL_TABLE
        else:
            cur["paras"].append(body)
        prev_was_fig = False
    elif line.startswith("C# "):
        assert cur is not None, "C before first S#"
        fname, lang = line[3:].strip().split("|", 1)
        code = open(os.path.join(D, fname.strip()), encoding="utf-8").read().rstrip("\n")
        # __CODE__ 前缀段落：render 自动转 <pre><code> 并做高亮与空格保护
        cur["paras"].append("__CODE__" + lang.strip() + "::" + code)
        code_count += 1
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
    "title": "MLC KCoral面向Agentic GPU编程的轻量评测服务器",
    "summary": [
        {"key": "解耦GPU执行", "body": "Agent本地生成代码，评估请求发往KCoral server；调度器把请求派到最空闲GPU独占执行，bubblewrap毫秒级隔离，哈希缓存跳过重复上传。"},
        {"key": "CPU-GPU解耦", "body": "cpu_only标志让编译不占GPU，或拆成独立CPU/GPU服务；单B200上混合负载吞吐2.58倍，matmul评估4.86倍，计时保真度与本地一致。"},
        {"key": "开箱即用", "body": "pip安装，CLI封装python/ncu/compute-sanitizer；TIRx-harness已将其作为默认评估后端，KDA即将集成。"},
    ],
    "lead": [
        "机器学习系统随着AI的快速发展越来越重要，GPU内核是这些系统的核心。AI agent能自动开发GPU内核：反复生成代码、运行、检查正确性与性能、再改进。CAKE、Kernel Design Agents（KDA）等近期工作展示了agent在GPU内核开发上日益增长的能力。",
        "内核agent负载快速增长带来新挑战：高效管理与共享GPU资源。Agent只在循环的评估阶段需要GPU，给每个agent独占一块GPU会浪费算力；共享GPU提升利用率，但需要协调以避免评估间相互干扰。KCoral是一个轻量benchmark server，把GPU执行从agent循环里解耦出来：agent在自己的workspace里写代码，把评估请求发给KCoral，server调度GPU、执行、返回结果。",
    ],
    "sections": sections,
    "conclusion": [
        "**把GPU从agent循环里摘出来，是规模化内核agent实验的关键一步。**KCoral用标准化协议加轻量server解决三件事：多agent共享GPU不打架、编译不占GPU、计时保真不丢优化信号；单B200上2.58倍吞吐、99.7%逼近理论上限的数据很有说服力。",
        "对做GPU内核agent与RL后训练的人，KCoral是现成的评估底座：pip安装、CLI零学习成本、TIRx-harness已默认集成。下一步值得看的是多节点Router在大规模rollout下的调度表现，以及KDA集成后的实际收益。",
    ],
    "reference_url": "https://blog.mlc.ai/2026/10/05/kcoral-lightweight-benchmark-server-for-agentic-gpu-programming",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count} code={code_count}")
print("article_data.json 已生成")
