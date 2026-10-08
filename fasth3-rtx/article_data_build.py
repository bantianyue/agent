#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#/__CODE__) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

sections = []
cur = None
fig_count = 0
prev_was_fig = False
in_code = False
code_buf = []

def flush_code():
    global in_code, code_buf
    if in_code and code_buf:
        cur["paras"].append("__CODE__" + "\n".join(code_buf))
    in_code = False
    code_buf = []

for raw in open(os.path.join(D, "content1.txt"), encoding="utf-8"):
    line = raw.rstrip("\n")
    if not line.strip():
        flush_code()
        continue
    if line.startswith("S# ") or line.startswith("H# ") or line.startswith("T# ") or line.startswith("F# "):
        flush_code()
    if in_code:
        code_buf.append(line)
        prev_was_fig = False
        continue
    if line.startswith("S# "):
        cur = {"type": "h2", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("H# "):
        cur = {"type": "h3", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("__CODE__"):
        assert cur is not None, "CODE before first S#"
        in_code = True
        code_buf = [line[len("__CODE__"):]]
        prev_was_fig = False
        continue
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
flush_code()

for s in sections:
    n = len(s["paras"])
    for k in s["fig_after"]:
        assert int(k) < n, f"fig_after 越界: section={s['title'][:20]} key={k} paras={n}"

DATA = {
    "title": "FastH3 上消费级硬件：单张 RTX 跑 8 步视频生成，剪枝版 Trim 更小更快",
    "summary": [
        {"key": "消费级全跑通", "body": "FastH3 V2 八步带音频视频生成登陆 RTX 5090/4090/PRO 6000、DGX Spark、Apple Silicon Mac；NVFP4 配 Blackwell，FP8 配 4090，INT6 配 Mac。"},
        {"key": "瘦身三板斧", "body": "文本编码器砍 14 层加 LM head，DiT 全层 NVFP4，VAE 换蒸馏轻量版；5090 上 DiT 11.1 GiB 常驻显存，480p 片段 13.4 秒。"},
        {"key": "FastH3 Trim", "body": "按 block 重要性实测剪掉 8 个前半网络 block，timestep 投影 rank-16 分解；NVFP4 下 11.1 GiB，比 base H3 小 4.2 倍，最低 8 GB 显存可跑。"},
    ],
    "lead": [
        "FastH3 V2 八步生成带同步音频的视频，八步就超过 base H3 的质量——此前这需要数据中心 GPU，权重 138 GiB。现在它跑进了单台消费级机器：RTX 5090 13.4 秒出 5 秒 480p 片段，RTX 4090 用 FP8 也能跑，连 Mac 都能跑 INT6 版。",
        "怎么做到的：三个网络分别瘦身，NVFP4 逐层校准 activation scale 防裁剪，5090 上 DiT 常驻显存只流式搬文本编码器。另有实验性剪枝版 FastH3 Trim，去掉 8 个 block 再小一截。下面拆数据、看方法。",
    ],
    "sections": sections,
    "conclusion": [
        "FastH3 上消费级硬件的核心经验是按瓶颈瘦身：BF16 137.7 GiB 里，文本编码器砍层、DiT 全层 4 bit、VAE 换蒸馏版，每一刀都砍在显存占用上；校准过的 activation scale 保住 4 bit 质量；pinned 内存按精确尺寸分配，连主机内存都不浪费。13.4 秒对 26.4 秒说明，DiT 能不能常驻显存是 5090 上的分水岭。",
        "Trim 则验证了另一条路：实测每个 block 的重要性再剪枝，比等间隔删除靠谱；timestep 投影这种低秩结构，用共享基加小投影就能压下来。实验性归实验性，8 GB 显存跑 8 步视频生成，已经把门槛拉到了主流甜点卡。",
    ],
    "reference_url": "https://haoailab.com/blogs/fasth3-rtx/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
