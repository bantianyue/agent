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
        # 首行 __CODE__ 前缀保留给 render 识别，后续行原样拼接
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

missing = []
for s in sections:
    for figs in s["fig_after"].values():
        for f in figs:
            if not os.path.exists(os.path.join(D, f["src"])):
                missing.append(f["src"])
assert not missing, f"图文件缺失: {missing}"

DATA = {
    "title": "PyTorch：Helion 打造高性能可移植的 vLLM Linear Backend",
    "summary": [
        {"key": "一份实现三种变体", "body": "Standard/Split-K/Swap-AB 统一成可调参数，AOT autotuner 按形状选最优，不再手写调度启发式；混合调度把 Helion 约束在 CUDA Graph 内的小 token 区间。"},
        {"key": "Hopper 实测", "body": "kernel 层几何平均 1.11 到 1.18 倍（对 CUTLASS/DeepGEMM/FlashInfer），端到端持续增益、部分负载吞吐超 10%。"},
        {"key": "落地权衡", "body": "延迟关键 kernel 上游维护框架加默认配置、调优下放用户；小辅助 kernel 用 6 个通用配置换可维护性。"},
    ],
    "lead": [
        "vLLM 的量化 linear backend 长期靠 CUTLASS、DeepGEMM、FlashInfer 的手写 kernel。PyTorch 官方博客的新工作把 Helion 接了进来：用一份高层 DSL 实现，通过 autotuning 自动打出超过这些手写库的性能。",
        "关键数字在 Hopper 上：三种 8-bit 量化格式的 kernel 几何平均加速 1.11 到 1.18 倍，端到端 serving 持续增益、部分负载超 10%。下面拆实现、调优与评估。",
    ],
    "sections": sections,
    "conclusion": [
        "Helion 的价值在这次落地里很具体：一份 Pythonic kernel 实现，通过可调参数统一 Standard/Split-K/Swap-AB 三种算法变体，AOT autotuner 按形状逐个挑最优，混合调度把调优与运行都约束在 CUDA Graph 覆盖的小 token 区间。结果是 Hopper 上 kernel 层几何平均 1.11 到 1.18 倍，端到端持续增益、部分负载超 10%。",
        "更值得带走的是权衡框架：细粒度调优的三方取舍里，延迟关键 kernel 值得为性能牺牲开箱易用性（调优下放给用户），小辅助 kernel 则反其道而行之（6 个通用配置）。kernel DSL 的成熟形态，可能不是一个配置打天下，而是自动化工具链加分层配置策略。",
    ],
    "reference_url": "https://pytorch.org/blog/building-a-high-performance-and-portable-vllm-linear-backend-with-helion/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
