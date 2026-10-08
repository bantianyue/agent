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
    "title": "Blackwell 四种量化格式实测：Qwen3-32B 在 RTX PRO 6000 上的精度与吞吐",
    "summary": [
        {"key": "四种格式", "body": "FP8/MXFP8 近乎无损（+0.03/+0.06 PPL），NVFP4 吞吐 2.41 倍代价 +0.41 PPL；MXFP4 因 Marlin fallback kernel 落后，格式规格不等于实测速度。"},
        {"key": "NVFP4 两级缩放", "body": "16 值块配 FP8 块缩放加全局 FP32 缩放，让 4-bit E2M1 在 Blackwell Tensor Core 上跑出 3078.91 tok/s，全程 TTFT 最低。"},
        {"key": "选型结论", "body": "默认 NVFP4-AWQ，保守选 FP8-AWQ，平衡选 MXFP8-AWQ；高负载下量化模型的赢面一半来自 KV cache 省出的并发空间。"},
    ],
    "lead": [
        "Blackwell 上选量化格式不再是省多少显存的单选题。同一张 RTX PRO 6000、同一个 Qwen3-32B，FP8、MXFP8、NVFP4、MXFP4 四种格式省的显存差不多，serving 性能却天差地别：最快的比最慢的多出近一倍吞吐。",
        "实测把账算清楚了：NVFP4-AWQ 以 2.41 倍峰值吞吐、+0.41 PPL 拿下总冠军；FP8 系近乎零代价拿到约 1.7 倍；MXFP4 因为没跑在原生 kernel 上成了反面教材。下面拆机制、摆数字。",
    ],
    "sections": sections,
    "conclusion": [
        "Blackwell 把量化从省显存的妥协变成了近乎免费的 serving 升级：困惑度最多动 +0.44，GSM8K 按噪声处理，峰值吞吐 1.34 到 2.41 倍，TTFT 最多降约 8.4 倍。NVFP4 的两级缩放是 4-bit 可用的关键，16 值块配 FP8 块缩放、再加全局 FP32 缩放，让 E2M1 的 1 个尾数位够用；MXFP4 的对照则说明，格式的纸面规格不等于实测速度，kernel 落地决定一切。",
        "落到选型：默认 NVFP4-AWQ，保守 FP8-AWQ；高并发场景记得量化模型赢的不只是数学，还有 KV cache 省出的并发空间。一个可复用的检查清单：先看 kernel 是否真的走了 Tensor Core（这次 MXFP4 就是反例），再看激活是否一起量化，最后看 TTFT 曲线而不是只看峰值 tok/s。",
    ],
    "reference_url": "https://jarvislabs.ai/blog/blackwell-dtypes-qwen3-32b",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
