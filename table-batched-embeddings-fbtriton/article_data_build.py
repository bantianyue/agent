#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#/C#) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

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
        cur["paras"].append(line[3:].strip())
        prev_was_fig = False
    elif line.startswith("C# "):
        assert cur is not None, "C before first S#"
        fname, lang = line[3:].strip().split("|", 1)
        code = open(os.path.join(D, fname.strip()), encoding="utf-8").read().rstrip("\n")
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
    "title": "PyTorch用FBTriton重写表批embedding:前向更快,反向也赢",
    "summary": [
        {"key": "前向双路径", "body": "通用gather保通用性；E≤64、64≤D≤128等窄条件的小表走直方图+tensor core快速路径，一个program处理16个bag，前向中位数加速1.28倍。"},
        {"key": "反向按run分流", "body": "索引转置+RLE把batch反转为run，按segment length路由到三个kernel；长run切256块split-K，TLX的fence+倒计数、TMA reduce解决跨program同步与合并。"},
        {"key": "赢在阈值", "body": "CUDA在SL=32切cooperative kernel，Triton简单streaming用到256；胜负带里Nsight实测实现带宽5.8倍。307个分片里Unweighted中位数1.13、Weighted 1.22。"},
    ],
    "lead": [
        "推荐系统的embedding查找横跨数千个分片GPU，TBE（Table Batched Embedding）是把多张表的查找与pooling压进一次GPU launch的核心算子。PyTorch团队用FBTriton把整条稀疏路径重写了一遍——普通Python，体量比原来的CUDA模板还小。",
        "结果是前向后向全面超过legacy CUDA kernel：前向中位数1.28倍，反向在307个生产分片上Unweighted中位数1.13、Weighted 1.22。赢的关键不是搬更多字节，而是把策略切换点从SL=32挪到256，砍掉CTA级同步的摊销负担。",
    ],
    "sections": sections,
    "conclusion": [
        "**FBTriton赢在把阈值挪对了地方。**前向双路径各司其职，反向按segment length分流到三个kernel，TLX Blackwell的fence、CLC、TMA reduce补上Triton缺的硬件原语；胜负带（32≤SL<256）里实现带宽5.8倍，307个分片加权中位数1.22。",
        "对做推荐系统与稀疏算子的人，这篇的工程细节可以直接抄：按维度分桶定BLOCK_SIZE、形状留GPU上避免.item()同步、长run切256块。最持久的成果是整条稀疏路径变成普通Python——未来的融合空间才刚打开。",
    ],
    "reference_url": "https://pytorch.org/blog/modernizing-table-batched-embeddings-with-fbtriton/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count} code={code_count}")
print("article_data.json 已生成")
