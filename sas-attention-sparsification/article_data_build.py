#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
article_data_build.py — 文本 DSL 行文件 → article_data.json

内容写在 content1.txt / content2.txt（按文件名排序），本文件只负责解析与落盘：
    S#  章节标题            → 新 h2 section
    H#  子标题              → 新 h3 section
    T   段落文字            → 追加进当前 section 的 paras
    F   figNN.png|图注       → 挂在「最近一条 T」之后（fig_after）
    C   代码行              → 连续 C 行合并成一个 __CODE__ 段落
    TB# 表头|列|列           → 当前 section 的 table.head
    TR  单元格|单元格        → 当前 section 的 table.rows 追加一行
    #   注释行              → 跳过

用法: python article_data_build.py [article_dir]
"""
import glob
import json
import os
import sys

if len(sys.argv) > 1:
    _dir = os.path.abspath(sys.argv[1])
elif "__file__" in globals():
    _dir = os.path.dirname(os.path.abspath(__file__))
else:
    _dir = os.getcwd()


def parse_content_files(article_dir):
    sections = []
    cur = None
    code_buf = []

    def flush_code():
        if code_buf:
            cur["paras"].append("__CODE__text::" + "\n".join(code_buf))
            code_buf.clear()

    def need_section(prefix):
        if cur is None:
            raise SystemExit(f"❌ 解析错误：{prefix} 行出现在任何 S#/H# 之前")

    files = sorted(glob.glob(os.path.join(article_dir, "content*.txt")))
    if not files:
        raise SystemExit("❌ 找不到 content*.txt")
    for path in files:
        with open(path, encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n").rstrip()
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if line.startswith("S#") or line.startswith("H#"):
                    flush_code()
                    cur = {
                        "type": "h2" if line.startswith("S#") else "h3",
                        "title": line[2:].strip(),
                        "paras": [],
                        "fig_after": {},
                    }
                    sections.append(cur)
                elif line.startswith("T "):
                    flush_code()
                    need_section("T")
                    cur["paras"].append(line[2:].strip())
                elif line.startswith("C "):
                    need_section("C")
                    code_buf.append(line[2:].rstrip())
                elif line.startswith("F "):
                    flush_code()
                    need_section("F")
                    src, _, cap = line[2:].strip().partition("|")
                    idx = max(0, len(cur["paras"]) - 1)
                    cur["fig_after"].setdefault(str(idx), []).append(
                        {"src": src.strip(), "caption": cap.strip()}
                    )
                elif line.startswith("TB# "):
                    flush_code()
                    need_section("TB#")
                    head = [c.strip() for c in line[4:].strip().split("|")]
                    cur["table"] = {"head": head, "rows": []}
                elif line.startswith("TR "):
                    flush_code()
                    need_section("TR")
                    cur["table"]["rows"].append(
                        [c.strip() for c in line[3:].strip().split("|")]
                    )
                else:
                    raise SystemExit(
                        f"❌ {os.path.basename(path)}:{lineno} 无法识别的行: {line[:60]}"
                    )
        flush_code()
    return sections


SECTIONS = parse_content_files(_dir)

DATA = {
    "title": "SAS：让稀疏注意力的选择器端到端学习上下文排序",
    "summary": [
        {
            "key": "端到端排序",
            "body": "把选择器分数当作 log 空间软门控加进注意力 softmax，语言建模损失直接更新选择器，省掉教师注意力与辅助蒸馏。",
        },
        {
            "key": "四个设计选择",
            "body": "门控放进 softmax 内部、用 softmax 归一化、保留连续分数、训练只更新被选中的块，四条都影响排序信号的质量。",
        },
        {
            "key": "低预算收益",
            "body": "1024 token 预算下 MATH500 比 SeerAttention-R 高 6.0 到 7.7 分，GPQA-Diamond 高 10.6 到 15.5 分。",
        },
    ],
    "lead": [
        "解码期的注意力开销随上下文线性增长，累计成本却是平方级。SAS 的做法很直接：推理时照旧用硬 Top-K 选块，训练时给被选中的块加一个连续门控，让语言建模损失把梯度直接送到选择器，不再需要蒸馏稠密注意力。",
    ],
    "sections": SECTIONS,
    "conclusion": [
        "**稀疏注意力的瓶颈往往不在算子，而在排序信号。**用硬 Top-K 选块时，语言建模损失到选择器这一段是断的，蒸馏只能让选择器去模仿稠密模型的注意力分布。SAS 把选择器分数作为 log 空间门控放进 softmax 内部，梯度就直接告诉选择器哪些块真正支撑了预测。四个设计选择里，门控位置、softmax 归一化、连续分数保留了排序信息，只更新选中块的稀疏训练范围则把长序列训练的成本压了下来。",
        "对做长上下文推理和服务的团队，值得关注的是预算收紧时的表现：预算压到 1024 时 SAS 比蒸馏基线高 6 到 15 分，512K 上下文的解码延迟降到稠密注意力的约五分之一。解码步的成本拆解也给出了下一步方向，Top-K 排序与不断增长的选择器打分已经取代注意力计算成为瓶颈，继续做内核优化的收益在这里。",
    ],
    "reference_url": "https://arxiv.org/html/2609.13141v1",
}


def self_check():
    errors = []
    if len(DATA["summary"]) != 3:
        errors.append("summary 必须恰好 3 条")
    fig_files = {os.path.basename(p) for p in glob.glob(os.path.join(_dir, "fig*.png"))}
    used = []
    paras_total = 0
    for s in DATA["sections"]:
        if not s["paras"]:
            errors.append(f"section「{s['title']}」没有正文段落")
        paras_total += len(s["paras"])
        for key, figs in s["fig_after"].items():
            if int(key) >= len(s["paras"]):
                errors.append(f"section「{s['title']}」fig_after key={key} 越界（paras={len(s['paras'])}）")
            for f in figs:
                used.append(f["src"])
                if f["src"] not in fig_files:
                    errors.append(f"图文件缺失: {f['src']}")
                if not f["caption"]:
                    errors.append(f"图注为空: {f['src']}")
    prev = None
    for s in DATA["sections"]:
        for key in sorted(s["fig_after"], key=int):
            for f in s["fig_after"][key]:
                if prev == f["src"]:
                    errors.append(f"相邻重复图: {f['src']}")
                prev = f["src"]
    print(f"sections={len(DATA['sections'])} paras={paras_total} figs={len(used)} "
          f"tables={sum(1 for s in DATA['sections'] if s.get('table'))} "
          f"字符={sum(len(p) for s in DATA['sections'] for p in s['paras'])}")
    print("figs used:", " ".join(sorted(set(used))))
    unused = sorted(fig_files - set(used))
    if unused:
        print("未被引用的图（附录图按计划省略）:", " ".join(unused))
    if errors:
        for e in errors:
            print("❌", e)
        raise SystemExit(1)
    print("✅ 自检通过")


if __name__ == "__main__":
    self_check()
    out = os.path.join(_dir, "article_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=2)
    print(f"✅ 写入 {out}")
