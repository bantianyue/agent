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
    "title": "Aleph Alpha分层扩展预训练:16卡定配置,512卡只掉6%",
    "summary": [
        {"key": "三个自由度", "body": "并行方案×激活检查点×局部batch size，三者经内存互相咬合：selective-AC在92%显存处TPS峰值，full-AC在60到94%宽区间都快；FSDP组加大省内存但加通信。"},
        {"key": "16卡定配置", "body": "目标规模1/32的sweep缩小搜索空间：no-AC过早OOM，selective-AC峰值batch约18，full-AC约38；8到16卡经IB扩展无损耗。"},
        {"key": "512卡35.3%", "body": "最终selective-AC、batch 22、FSDP=128、DP=4：26.7k TPS、35.3% MFU，16到512卡单卡效率只掉6%，20T token 17天训完。"},
    ],
    "lead": [
        "只堆卡不调软件，训练效率很快就会崩；前沿实验室愿意为MFU里几个百分点投入大量人力。可调的效率超参数太多，大规模网格搜索贵得离谱。分层扩展这套方法把30B-A3B MoE从16张卡扩到512张B200，做到35.3% MFU，只比完美线性低6%。",
        "方法叫分层扩展：先在16卡上把搜索空间大幅缩小（并行方案×激活检查点×局部batch size），用PyTorch profile确认compute-bound，再把结论带到32倍的目标规模。很多思路与规模无关，没有几百张卡也用得上。",
    ],
    "sections": sections,
    "conclusion": [
        "**扩展预训练，先缩搜索空间再加卡。**Aleph Alpha用16卡（目标1/32）定下并行方案、AC技术、局部batch边界，profile确认前后向compute-bound；128卡定FSDP上限128、selective-AC胜出；512卡FSDP=128、DP=4收官：35.3% MFU，离完美线性只差6%。",
        "对做预训练的人，这套方法论可以直接复用：北极星指标用TPS而非MFU，目标显存占用放在92%附近，gbs=lbs×卡数×梯度累积的硬约束先立好；权重在反向与前向之间常驻内存，还能再拿到2到3%。Kolibri的训练链路是这套方法的完整实践记录，两篇对照看。",
    ],
    "reference_url": "https://aleph-alpha.com/en/blog/scaling-pre-training-in-practice-a-hierarchical-approach/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
