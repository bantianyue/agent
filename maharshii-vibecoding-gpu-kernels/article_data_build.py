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
    "title": "maharshi：vibecoding GPU kernel 实战经验",
    "summary": [
        {"key": "可验证循环", "body": "选算子、写第一版、编译检查、对照参考实现查正确性、测基准、看 roofline，四层嵌套回路；正确性循环是核心，快但错的 kernel 毫无价值。"},
        {"key": "第一版靠上下文", "body": "Triton 大模型裸写即可；CuTeDSL 更细粒度，需要把 cutlass 仓库（Layout Algebra、Copy/GEMM atoms、内存层级、示例）放进上下文目录供 agent 查阅。"},
        {"key": "验证是瓶颈", "body": "正确性看 MAE/MSE/PSNR/余弦相似度；rung 装饰器组织测试；转储 PTX/SASS 让 agent 内联更底层代码；NCU 进循环做 profile。2 到 3 周工作可压到 1 到 2 天。"},
    ],
    "lead": [
        "手写 GPU kernel 需要耐心和投入，maharshi（fal）一直在用 Claude Opus 5、GPT 5.6 Sol 这类大模型直接生成 kernel，下面是他沉淀下来的实战经验。",
        "核心判断：写 GPU kernel 是“非常容易验证”的任务，天然适合 agent 的可验证反馈循环。下面拆解四个嵌套回路、第一版的上下文准备、测试基准与 profile 方法，保留全部实操细节。",
    ],
    "sections": sections,
    "conclusion": [
        "vibecoding GPU kernel 的完整配方：可验证循环定骨架，第一版靠上下文目录喂饱 agent，正确性测试用慢参考实现卡死标准，benchmark rung 与 PTX/SASS 转储给优化提供抓手，NCU profile 进循环。布局索引这些难点 agent 已能解决，2 到 3 周压到 1 到 2 天。",
        "但瓶颈转移到了验证环节：没有唯一正确做法，harness 越好流程越快。**把 agent 当可引导的聪明助手，而不是全自主主体——人的 GPU 基本功依然必要。**",
    ],
    "reference_url": "https://x.com/maharshii/status/2086442755748970889",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
