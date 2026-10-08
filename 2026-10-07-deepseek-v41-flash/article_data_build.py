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
    "title": "vLLM：DeepSeek-V4.1-Flash 发布三周，Agentic 吞吐做到 5 倍",
    "summary": [
        {"key": "SWA bounded replay", "body": "只重放最后 128 token 并截断窗口，换掉 SWA KV 的存储与 prefill 代价；decoder 侧 21 到 39 层只跑最后 128 token，长 prompt 跳过近半模型；breakable PIECEWISE 让修剪层也能进 CUDA graphs，prefill 计算降 30 到 40%。"},
        {"key": "Kernel 融合与并行", "body": "Mega-mHC、Mega-Gate、MegaAttention（NVFP4 KV 小 45%）、WO-A 融合 kernel、mHC 多流并行、稀疏 MQA logits、Engram 异步预取；单项加速 1.14 到 2.1 倍，GSM8K/GPQA 精度无损。"},
        {"key": "AgentX 实测", "body": "GB300 NVL72 上，相对 day-0 实现低延迟 1.9 倍、高吞吐 5.3 倍；100K 吞吐附近 TTFT 降近 70%，固定吞吐下 P90 TTFT 从 1.86 秒到 0.32 秒。"},
    ],
    "lead": [
        "DeepSeek-V4.1-Flash 发布才三周，Inferact 和 vLLM 社区已经把 AgentX 上的 agentic 吞吐做到了 day-0 的 5 倍，低并发延迟也快了 1.9 倍。",
        "两类优化：SWA bounded replay 拿近似换效率，长 prompt 直接跳过近半个模型；一连串 kernel 融合与并行把剩下的计算压干。下面按原文结构拆解，保留全部机制与性能数字。",
    ],
    "sections": sections,
    "conclusion": [
        "三周 5 倍的核心是两层叠加：模型侧的 SWA bounded replay 把 SWA KV 的存储与 prefill 代价换成一次 128 token 重放，decoder 侧 21 到 39 层只跑最后 128 token；引擎侧用 breakable PIECEWISE 把修剪层装进 CUDA graphs，再用 Mega 系列融合 kernel、mHC 多流、NVFP4 把计算压干。GSM8K/GPQA 精度无损是前提。",
        "对做推理部署的人，两个配置结论可以直接拿走：低延迟用 TP4 配 FlashInfer，高吞吐用 DEP2 配 DP attention 避开 KV 复制；V4.1 的内存效率已经高到整个 AgentX 都不需要 KV offload。**近似但可控的 replay，加上激进的融合，是这三周 5 倍的完整配方。**",
    ],
    "reference_url": "https://vllm.ai/blog/2026-10-07-deepseek-v41-flash",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
