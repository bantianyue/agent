# -*- coding: utf-8 -*-
import json, re
d = json.load(open("article_data.json", encoding="utf-8"))
REPL = [
 ("veRL（两倍 GPU） 配置了原始 trace 中 veRL 所用 GPU 数量的 2 倍倍，代表像 RLBoost 那样使用更多 GPU 加速 RL 时的最优性能。",
  "veRL（两倍 GPU）为 veRL 配置了原始 trace 所用 GPU 数量的两倍，代表像 RLBoost 那样用更多 GPU 加速 RL 时的最优性能。"),
 ("veRL（两倍 GPU） 配置了原始 trace 中 veRL 所用 GPU 数量的 2 倍倍",
  "veRL（两倍 GPU）为 veRL 配置了原始 trace 所用 GPU 数量的两倍"),
 ("即使与使用两倍 GPU 的 veRL（两倍 GPU） 相比", "即使与使用两倍 GPU 的 veRL 相比"),
 ("提升长尾请求请求的接受率", "提升长尾请求的接受率"),
 ("对于 32B 训练，0.5B 是加速的甜点值。", "对于 32B 训练，0.5B 是加速效果最好的选择。"),
 ("对于32B训练，0.5B是加速的甜点值。", "对于 32B 训练，0.5B 是加速效果最好的选择。"),
]
def walk(o):
    if isinstance(o, str):
        for a, b in REPL: o = o.replace(a, b)
        return o
    if isinstance(o, list): return [walk(x) for x in o]
    if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
    return o
d = walk(d)
# 合并被脚注拆开的一句（draft 方法列举）
for sec in d["sections"]:
    ps = sec["paras"]
    for i in range(len(ps) - 1):
        if ps[i].endswith("选取可用的草稿器") and ps[i+1].startswith("在后训练 pipeline 之前"):
            ps[i] = ps[i][:-len("草稿器")] + "草稿器：" + ps[i+1].replace("在后训练 pipeline 之前：", "")
            ps[i+1] = ""
    sec["paras"] = [p for p in ps if p.strip()]
json.dump(d, open("article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
s = json.dumps(d, ensure_ascii=False)
for pat in ["2 倍倍", "请求请求", "甜点值"]:
    print(pat, s.count(pat))
print("paras:", sum(len(x["paras"]) for x in d["sections"]))
