# -*- coding: utf-8 -*-
import json, re

d = json.load(open("article_data.json", encoding="utf-8"))

def fix(t):
    t = t.replace("``", "\u201c").replace("''", "\u201d")
    t = re.sub(r"(\d+)\^th 个 token", r"第 \1 个 token", t)
    t = t.replace("3.%", "3%").replace("（ 64）", "（不小于 64）")
    t = t.replace("配置 2\u00d7 块 GPU", "配置两倍的 GPU")
    t = t.replace("veRL (2\u00d7)", "veRL（两倍 GPU）")
    t = re.sub(r"(\d(?:\.\d+)?[–-]\d(?:\.\d+)?)\s*\u00d7", r"\1 倍", t)
    t = re.sub(r"(\d(?:\.\d+)?)\s*\u00d7", r"\1 倍", t)
    t = t.replace("投机", "推测")
    # 中文之间的多余空格
    t = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", t)
    t = re.sub(r"\s+(?=[，。、；：）%])", "", t)
    t = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", t)
    t = re.sub(r"  +", " ", t)
    return t

def walk(o):
    if isinstance(o, str): return fix(o)
    if isinstance(o, list): return [walk(x) for x in o]
    if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
    return o

d = walk(d)
json.dump(d, open("article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
s = json.dumps(d, ensure_ascii=False)
for pat in ["\u00d7", "``", "^th", "3.%", "（ 64", "\u6295\u673a"]:
    print(repr(pat), s.count(pat))
print("cjk-cjk spaces:", len(re.findall(r"[\u4e00-\u9fff]\s+[\u4e00-\u9fff]", s)))
print("body chars:", sum(len(p) for sec in d["sections"] for p in sec["paras"]))
