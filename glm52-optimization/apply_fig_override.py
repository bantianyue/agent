#!/usr/env python3
# Apply source-correct fig_after overrides to article_data.json (build wipes them).
import json, os
here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, "article_data.json")
d = json.load(open(p, encoding="utf-8"))
# clear all auto-derived fig_after to avoid duplicates
for s in d["sections"]:
    s.pop("fig_after", None)
# source-correct placement
d["sections"][6]["fig_after"] = {
    "0": [{"src": "fig08.png", "caption": "图7：GLM 5.2 NVFP4 在 SGLang 上的性能帕累托（Pareto）曲线。"}],
    "1": [{"src": "fig09.png", "caption": "图8：随输入序列长度变化的消融（ablation）测试（模拟接受长度 5 以提高可复现性）。"}],
}
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("fig_after override applied: fig08/pareto + fig09/ablation -> 性能结果 section")
