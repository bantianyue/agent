#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

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
        cur["paras"].append(line[3:].strip())
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
    "title": "Avi Chawla：LLM 推理并行策略详解",
    "summary": [
        {"key": "五个问题看懂所有策略", "body": "切分了什么状态、复制了什么、什么数据跨互联、传输频率、改善显存/延迟/吞吐：数据并行、张量并行、流水线并行、上下文并行、专家并行、混合并行逐个用这五个问题拆解，差异一目了然。"},
        {"key": "每种策略只治一种瓶颈", "body": "数据并行主攻吞吐不治延迟；张量并行用最小 TP 度数解决模型放不下；流水线并行跨慢速互联；PCP 治长 prompt 计算、DCP 治 KV 存储；专家并行治 MoE expert 权重；混合按最小 TP、再 PP、最后 DP 的顺序叠。"},
        {"key": "自上而下的决策框架", "body": "单卡放得下先数据并行；放不下找最小 TP；跨节点则 TP 留节点内、PP 跨节点；长 prompt 评估 PCP、KV 受限评估 DCP；MoE 看 expert 权重。每次只加一种并行，实测有效再继续。"},
    ],
    "lead": [
        "4 块 GPU 不是一块大 GPU：4 个独立内存空间加 4 个处理器，跑在某块卡上的 kernel 够不到别的卡上的权重和 KV cache，任何跨卡依赖都要付一次传输或集合通信的代价。推理部署选并行策略，本质上就是在这种约束下做数据放置。",
        "六种主流策略（数据并行、张量并行、流水线并行、上下文并行、专家并行、混合并行）各切分了工作负载的不同维度，也各引入不同的通信模式。下面逐个拆解：切分了什么、复制了什么、通信长什么样、解决哪类瓶颈，最后给出一套自上而下的实用决策框架。",
    ],
    "sections": sections,
    "conclusion": [
        "六种策略各管一类瓶颈：数据并行切请求，主攻吞吐；张量并行切权重矩阵，解决模型放不下；流水线并行按层分组，跨过慢速互联；上下文并行切序列位置，prefill 端治长 prompt 计算、decode 端治 KV 存储；专家并行分散 MoE 的 expert；混合并行按最小 TP、再 PP、最后 DP 的顺序叠加。决策时自上而下走一遍：每次只启用经测量确认能解决当前瓶颈的那一种，benchmark 达标就停。",
        "贯穿始终的工程直觉只有两条：切分省下的显存和算力，必须大于引入的通信、同步与调度开销；满足延迟与吞吐目标的前提下，最简单的布局就是最好的布局。**并行是放置决策，不是 GPU 数量设置。**",
    ],
    "reference_url": "https://x.com/_avichawla/status/2107427400779026843",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
