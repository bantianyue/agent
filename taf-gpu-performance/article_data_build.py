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
    "title": "AMD TAF：Peak FLOPs 与 MAF 之外的第三个 GPU 性能指标",
    "summary": [
        {"key": "三个指标各答一问", "body": "Peak FLOPs 定理论天花板，MAF 测已测 GEMM 里的最高持续吞吐，TAF 在测试前固定的 10 个 DeepSeek V3 形状上测 FLOP 加权持续吞吐，MI325X 上约 MAF 的 74% 到 81%。"},
        {"key": "方法论", "body": "5 组 (N,K) 对各在 M=32 与 M=32768 下测，mblas-bench 每形状跑 30 秒，F_i = 2 × M_i × N_i × K_i，TAF 取 FLOP 加权调和平均。"},
        {"key": "MI325X 实测", "body": "FP16 606 TFLOPs，BF16 616 TFLOPs，非缩放 FP8 1143 TFLOPs；正态分布初始化，老 trig_float 结果不可直接对比。"},
    ],
    "lead": [
        "一个 FLOPs 数字讲不全 GPU 的性能故事：理论天花板、最高持续吞吐、真实形状上的持续吞吐，是三个不同的问题。AMD ROCm 博客这个系列的前两篇讲了 Peak FLOPs 与 MAF，这篇引入第三个指标 TAF（Typical Attained FLOPs）。",
        "TAF 的思路很实在：测试前先固定一组来自真实负载的 GEMM 形状，每个形状跑满 30 秒，最后按 FLOP 加权调和平均，不给挑最优形状留操作空间。MI325X 的实测数字和解读方法，下面逐一拆开。",
    ],
    "sections": sections,
    "conclusion": [
        "TAF 的价值不在数字本身，而在它把持续吞吐从最好情况拉回了典型情况：10 个固定形状、FLOP 加权、全部计入，MI325X 的 TAF 落在 MAF 的七到八成。这不是性能损失，而是度量口径的诚实度——选卡、看基准时，先问清楚这个数字回答的是哪个问题。",
        "对推理 serving 的选型来说，TAF 更接近 decode 阶段 GEMM 部分的实际预期，但它依然只是算力侧指标：显存带宽、KV cache、通信与软件栈的效率，仍然要靠应用级基准验证。",
    ],
    "reference_url": "https://rocm.blogs.amd.com/artificial-intelligence/taf-blog/README.html",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
