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
    "title": "Signal65：NVFP4 在 GB300 NVL72 上用四分之一 GPU 跑起 2.4 万亿参数模型",
    "summary": [
        {"key": "四分之一卡", "body": "Qwen3.8-2.4T-A95B 的 NVFP4 版在 16 张 GPU 上跑出 1,133 output TPS，是 BF16 版在 64 张卡上 1,221 的 93%；单 GPU 吞吐 3.7 倍。"},
        {"key": "高负载拉大差距", "body": "同一 16 卡上，NVFP4 比 FP8 在 40 并发下高 41%，120 并发下 2.9 倍；NVFP4 吞吐随负载近乎翻倍，FP8 基本持平。"},
        {"key": "成本账", "body": "每输出 token 的 GPU-hours，NVFP4 比 BF16 降 73%、比 FP8 降 29%；64 卡容一份 BF16 模型，可容四份 NVFP4。"},
    ],
    "lead": [
        "Signal65 的 PINNACLE 基准出了第二批机架级结果，跑在 NVIDIA GB300 NVL72 上，主角是 NVFP4：2.4 万亿参数 MoE 模型 Qwen3.8-2.4T-A95B，只用四分之一的 GPU，跑出 BF16 版本 93% 的吞吐。",
        "下面拆解测试方法、三组对比数字、更小 footprint 的价值，以及各旗舰模型在机架上的占位，保留全部实测数据。",
    ],
    "sections": sections,
    "conclusion": [
        "NVFP4 在 GB300 NVL72 上的完整账：16 卡等于 64 卡 BF16 的 93% 吞吐，单 GPU 产出 3.7 倍，每输出 token 成本降 73%。高负载下对 FP8 的领先从 41% 拉大到 2.9 倍，量化在 agentic 高并发场景的收益最明显。",
        "值得留意的两点：第一，仅调 serving 配置就曾在同一硬件上带来 64% 吞吐提升，说明机架级系统里配置调优本身就是一门手艺；第二，PINNACLE 接下来把 footprint 节省表述为“每机架可服务的 agent 数”，量化从省显存变成了可算的容量账。",
    ],
    "reference_url": "https://x.com/Signal_65/status/2107651870911078661",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
