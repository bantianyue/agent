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
    "title": "PyTorch加速器集成工作组2026上半年硬件支持进展",
    "summary": [
        {"key": "CRCR跨仓库CI", "body": "PR打开即并行触发下游仓库CI，OIDC鉴权回调，结果秒级汇入HUD大盘；四级allowlist从通知到阻塞检查渐进接入。"},
        {"key": "测试/性能/编译/分布式", "body": "60万用例去硬件耦合（276文件已迁移），OpenReg参考后端覆盖profiling、OCCL分布式与torch.compile集成。"},
        {"key": "厂商中立", "body": "统一测试工作流、参考实现与CI看板，加速器厂商无需改上游代码即可接入；H2继续扩展子系统覆盖。"},
    ],
    "lead": [
        "加速器集成工作组在新硬件架构如何接入开源AI生态的标准化上扮演关键角色。算力平台在云、端、专用芯片间持续分化，工作组建立厂商中立的集成机制，消灭定制补丁，减少生态碎片化。这篇博客总结2026年上半年的进展：关键基础设施改进、统一测试工作流，以及覆盖整个PyTorch平台的参考后端。",
    ],
    "sections": sections,
    "conclusion": [
        "**厂商中立的集成机制是这半年最大的资产。**CRCR、测试重构、OpenReg、OCCL、编译后端参考——每条工作流都在回答同一个问题：新硬件如何不靠定制补丁接入PyTorch。",
        "对加速器厂商，这是上手路线图：从OpenReg抄集成模式，用hw_classification跑测试，用OCCL理解分布式契约。对PyTorch生态，这是护城河：参考实现跑在CI里，上游演进不再悄悄break下游。H2看点是未分级测试清零与hw_classification接入CI调度。",
    ],
    "reference_url": "https://pytorch.org/blog/pytorch-hardware-enablement-updates-from-the-acceleration-integration-working-group/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
