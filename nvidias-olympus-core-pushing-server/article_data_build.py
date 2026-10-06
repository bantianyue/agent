#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/T#/F#/Q#) -> article_data.json ."""
import json, os, re, sys

D = os.path.dirname(os.path.abspath(__file__))
QUOTE_STYLE = ('<span style="display:block;background:#f5f8fb;border-left:3px solid #0F4C81;'
               'padding:10px 14px;border-radius:4px;">')

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
    elif line.startswith("T# "):
        assert cur is not None, "T before first S#"
        cur["paras"].append(line[3:].strip())
        prev_was_fig = False
    elif line.startswith("Q# "):
        assert cur is not None, "Q before first S#"
        q, attr = line[3:].split("|", 1)
        card = QUOTE_STYLE + q.strip() + "<br/>" + attr.strip() + "</span>"
        cur["paras"].append(card)
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

# 越界断言
for s in sections:
    n = len(s["paras"])
    for k in s["fig_after"]:
        assert int(k) < n, f"fig_after 越界: section={s['title'][:20]} key={k} paras={n}"

# 图文件存在性
missing = []
for s in sections:
    for figs in s["fig_after"].values():
        for f in figs:
            if not os.path.exists(os.path.join(D, f["src"])):
                missing.append(f["src"])
assert not missing, f"图文件缺失: {missing}"

DATA = {
    "title": "NVIDIA Olympus推进服务器单线程性能边界",
    "summary": [
        {"key": "10宽SMT服务器核", "body": "3.3GHz低主频下靠超大乱序结构实现极高IPC，SPEC CPU2026单线程逼近桌面旗舰，显著领先Neoverse V2/N2。"},
        {"key": "空间多线程", "body": "SMT采用静态切分：后端队列、执行单元、L1D/L2全部对半分给双线程；整数负载收益比肩Zen 5，后端受限浮点负载偶发负收益。"},
        {"key": "实测反推", "body": "分支预测、取指带宽、存储转发、TLB与缓存层次全部基于硬件微基准实测；Vera相对Grace是核心更快、数量更多的全面跃升。"},
    ],
    "lead": [
        "服务器芯片的单线程性能长期弱于同时代桌面芯片：核心数越多，分给每核心的功耗越少，连接众多核心的复杂互联延迟也越高。不过这一趋势正在收窄。AMD近两代服务器芯片不断推高频率，NVIDIA的Olympus则是另一条激进路线：不拼频率，拼每周期性能。",
        "Olympus借鉴了Arm Cortex X925的思路，但走得更远：结构全面放大，并引入同步多线程（SMT）。最终成品是一个怪物级核心，在服务器领域极具统治力，单线程表现已经非常接近桌面处理器。",
    ],
    "sections": sections,
    "conclusion": [
        "**低主频加超大乱序结构这条路走通了。**3.3GHz、10宽发射、1021项重排序缓冲，Olympus用极致的每周期性能把服务器单线程推到桌面级；分支预测、取指、访存转发全部基于实测反推，数据扎实。",
        "空间多线程是最大胆的一赌：静态对半切分换来设计简单与天然公平，整数负载收益比肩Zen 5；但后端受限的浮点负载出现负收益，暴露了锁死一半资源的结构性代价。对做CPU微架构与性能分析的人，这组实测数据值得细读：第一代SMT的取舍全部摊在明面上。",
    ],
    "reference_url": "https://chipsandcheese.com/p/nvidias-olympus-core-pushing-server",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
