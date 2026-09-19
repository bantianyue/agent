# -*- coding: utf-8 -*-
import json, re
d = json.load(open("article_data.json", encoding="utf-8"))
REPL = [
 ("[-10pt]", ""), ("[-5pt]", ""), ("[-18pt]", ""), ("[-1.8ex]", ""),
 ("Algorithm算法", "算法"), ("我们的 runtime（）高效支持", "我们的运行时高效支持"),
 ("先对 draft window 内给定 n 个 token 时接受个 token 的概率建模",
  "先对 draft window 内给定 n 个 token 时接受其中若干 token 的概率建模"),
 ("给定 n 个 token 时接受个 token", "给定 n 个 token 时接受其中若干 token"),
]
def walk(o):
    if isinstance(o, str):
        for a, b in REPL: o = o.replace(a, b)
        o = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", o)
        o = re.sub(r"\s+(?=[，。、；：）%])", "", o)
        o = re.sub(r"（\s+", "（", o)
        o = re.sub(r"\s+（", "（", o) if "（" in o else o
        o = re.sub(r"  +", " ", o)
        return o
    if isinstance(o, list): return [walk(x) for x in o]
    if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
    return o
d = walk(d)
json.dump(d, open("article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
s = json.dumps(d, ensure_ascii=False)
print("[-10pt]:", s.count("[-10pt]"), "接受个:", s.count("接受个"), "Algorithm算法:", s.count("Algorithm算法"))
print("cjk-cjk:", len(re.findall(r"[\u4e00-\u9fff]\s+[\u4e00-\u9fff]", s)), "（ :", s.count("（ "))
