#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article_data_build.py — trace-as-state-long-context

文本 DSL 行文件模式：正文内容在 content1.txt（S#/T/F/TB/TR 行），本文件只做解析与组装。
被 write-article-data.py 用 exec() 执行 → 运行时没有 __file__，因此路径写死。
"""
import os

HERE = r"D:\06_Hermes\articles\trace-as-state-long-context"


def read_lines(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if line.strip():
                out.append(line)
    return out


S = []
cur = None
tbl_head = None
tbl_rows = []
fig_count = 0


def flush_table():
    global tbl_head, tbl_rows
    if cur is not None and tbl_head is not None:
        width = len(tbl_head)
        for r in tbl_rows:
            assert len(r) == width, f"表格列数不一致: {cur['title']} / {r}"
        # 模板每个 section 只渲染一张表（sec.table 单值）→ 一节两张表会静默覆盖
        assert "table" not in cur, f"同一节出现两张表会被覆盖: {cur['title']}"
        cur["table"] = {"head": tbl_head, "rows": tbl_rows}
    tbl_head = None
    tbl_rows = []


for ln in read_lines(os.path.join(HERE, "content1.txt")):
    if ln.startswith("S# "):
        flush_table()
        cur = {"type": "h2", "title": ln[3:].strip(), "paras": [], "fig_after": {}}
        S.append(cur)
    elif ln.startswith("T "):
        flush_table()
        assert cur is not None, "T 行出现在任何 S# 之前"
        cur["paras"].append(ln[2:].strip())
    elif ln.startswith("F "):
        assert cur is not None and cur["paras"], "F 行出现时前面没有正文段落"
        name, _, caption = ln[2:].partition("|")
        name = name.strip()
        idx = len(cur["paras"]) - 1
        cur["fig_after"].setdefault(str(idx), []).append(
            {"src": name, "caption": caption.strip()}
        )
        fig_count += 1
    elif ln.startswith("TB "):
        flush_table()
        tbl_head = [c.strip() for c in ln[3:].split("|")]
        tbl_rows = []
    elif ln.startswith("TR "):
        tbl_rows.append([c.strip() for c in ln[3:].split("|")])
    else:
        raise ValueError("无法识别的行: " + ln[:60])

flush_table()

# ── 组装自检：fig_after 越界 / 图数 / 表格列数 ──
paras_total = 0
tables_total = 0
for sec in S:
    paras_total += len(sec["paras"])
    for k in list(sec["fig_after"].keys()):
        assert int(k) < len(sec["paras"]), f"fig_after 越界: {sec['title']} key={k} paras={len(sec['paras'])}"
    if "table" in sec:
        tables_total += 1
disk_figs = sorted(f for f in os.listdir(HERE) if f.startswith("fig") and f.endswith(".png"))
used_figs = sorted({g["src"] for sec in S for lst in sec["fig_after"].values() for g in lst})
print(f"[build] sections={len(S)} paras={paras_total} tables={tables_total} figs={fig_count}")
print(f"[build] disk figs={disk_figs}")
print(f"[build] used figs={used_figs}")
assert fig_count == len(used_figs), "有图被重复引用"
assert used_figs == disk_figs, f"磁盘图与引用图不一致: {set(disk_figs) ^ set(used_figs)}"

DATA = {
    "title": "推理轨迹前置到长上下文之前：Trace as State 把 GraphWalks 准确率从 29.2% 提到 81.8%",
    "summary": [
        {"key": "核心机制", "body": "把第一遍的推理轨迹序列化成文本状态代理，放在长上下文之前重读一遍，让第一遍才发现的任务状态在第二遍开始时就能用。"},
        {"key": "关键数据", "body": "三个模型乘三个长上下文数据集共 27 组组合，trace as state 有 26 组高于 trace append；GraphWalks Parents 上 GLM-5.2 的精确匹配从 66.4% 直接到 100%。"},
        {"key": "理论依据", "body": "条件状态更新任务中，条件在前与条件在后在最坏情况下相差指数级的工作记忆，顺序本身就是一个可优化的变量。"},
    ],
    "lead": [
        "长上下文推理的瓶颈未必是窗口长度。解题需要的任务状态，常常要到读完整段上下文之后才出现，而因果注意力让这个状态无法回头影响前面已经形成的表示。把第一遍的推理轨迹放到长上下文之前再读一遍，DeepSeek V4 Pro 在 GraphWalks Parents 上的精确匹配从 29.2% 提升到 81.8%。",
    ],
    "sections": S,
    "conclusion": [
        "**长上下文推理的瓶颈常常不在窗口长度，而在顺序**：同一份推理轨迹、同一段上下文，把轨迹挪到上下文之前，GraphWalks Parents 上的精确匹配就从 29.2% 升到 81.8%。",
        "**① 顺序决定信息何时可用。** 因果注意力让已经形成的表示无法回头修改，把第一遍才发现的任务状态前置，等于让第二遍从更高的起点重新读一遍上下文。",
        "**② 起作用的是同一道题的轨迹，不是脚手架。** 随机轨迹比不给轨迹更差，只反馈答案也远不如反馈推理过程，说明收益来自题目相关的状态信息，而不是文本格式本身。",
        "**③ 代价同样明确。** 多一遍传递意味着更多 token 与更长延迟，状态前置还会削弱多轮场景下的键值缓存复用，轨迹本身有错时反馈也会失真。",
        "对做长上下文推理的人来说，值得先试的不是继续加长窗口，而是给已有的推理产物换一个位置：轨迹前置、问题前置、答案前置各试一遍，成本只是一次额外传递，收益却可能是一个档位。",
    ],
    "reference_url": "https://arxiv.org/html/2609.02702v1",
}
