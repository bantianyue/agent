# -*- coding: utf-8 -*-
"""核对正文「图N」引用与 fig 资产的编号是否一致,并做写作规则自检。"""
import json
import re
import sys

ART = r"D:\06_Hermes\articles\mimo-v26-scaling-rl"
j = json.load(open(ART + r"\article_data.json", encoding="utf-8"))

caps = {}
for s in j["sections"]:
    for k, items in (s.get("fig_after") or {}).items():
        idx = int(k)
        if idx >= len(s["paras"]):
            print(f"[FAIL] fig_after 越界: section={s['title']} key={k} paras={len(s['paras'])}")
        for it in items:
            n = int(re.search(r"(\d+)", it["src"]).group(1))
            caps[n] = (it["src"], it["caption"])

declared = set(caps)

body = []
for s in j["sections"]:
    body.extend(s["paras"])
body.extend(j["lead"])
body.extend([x["body"] for x in j["summary"]])
body.extend(j["conclusion"])
text = "\n".join(body)

refs = set()
for m in re.finditer(r"图(\d+)", text):
    refs.add(int(m.group(1)))

print("figs on disk:", sorted(declared))
print("referenced  :", sorted(refs))
print("missing caption for refs:", sorted(refs - declared))
print("figs never referenced   :", sorted(declared - refs))

# 图注编号 vs 文件名编号
for n in sorted(caps):
    src, cap = caps[n]
    m = re.match(r"图(\d+)[:：]", cap)
    if not m or int(m.group(1)) != n:
        print(f"[FAIL] caption 编号与文件名不一致: {src} {cap[:30]}")

# 写作规则自检
checks = {
    "第一人称": r"[我们]|咱们",
    "破折号": r"—|--",
    "搬运痕迹": r"原文|原作者|编译|译自|全中文|本文|这篇|本报告|该报告",
    "括号解说(中文括号)": r"（",
    "星号残留": r"^\*[^*]|\*{1}[^*\s]",
    "裸@": r"@",
}
for name, pat in checks.items():
    hits = []
    for i, p in enumerate(body):
        for m in re.finditer(pat, p):
            hits.append((i, p[max(0, m.start() - 18):m.end() + 18]))
    if hits:
        print(f"[WARN] {name}: {len(hits)}")
        for h in hits[:6]:
            print("      ", h[1].replace("\n", " "))

print("sections:", len(j["sections"]), "paras:", len(body))
print("ascii double quote in content:",
      sum(p.count('"') for p in body))
print("halfwidth ( in content:", sum(p.count("(") for p in body))
