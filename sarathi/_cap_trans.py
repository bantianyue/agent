# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
import llm_utils

ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
figmap = json.load(open(os.path.join(ART, "_figmap.json"), encoding="utf-8"))

# unique figure captions in fig order
seen = {}
caps = []
for it in items:
    if it["kind"] != "figure":
        continue
    pass
# use figmap src order
src2cap = {}
for it in items:
    if it["kind"] == "fig" and it["src"] not in src2cap:
        src2cap[it["src"]] = it["caption"]

paras = []
for m in figmap:
    cap = src2cap.get(m["src"], "")
    paras.append({"id": int(m["fig"][3:5]), "type": "text", "content": cap})

EXTRA = ("这些是学术论文的图注。翻译成简洁中文，保留所有数字与符号（如 200×、1K、256、A6000、LLaMA-13B），"
         "术语按：prefill=预填充、decode=解码、chunk=分块、batch size=批大小、sequence length=序列长度、"
         "pipeline bubble=流水线气泡、throughput=吞吐、arithmetic intensity=算术强度、tile quantization=分块量化、"
         "self-attention=自注意力、end-to-end=端到端、speedup=加速比、cdf=累积分布。"
         "保留 (a)(b)(c) 与 Figure N 的编号标记，格式写成「图 N：描述」。不要输出英文原文，不要加解释。")

out = llm_utils.translate_batch(paras, batch_size=10, system_extra=EXTRA)
res = {o["id"]: o["content"] for o in out}
json.dump(res, open(os.path.join(ART, "_captions.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(ART, "_captions_out.txt"), "w", encoding="utf-8").write(
    "\n".join("%s -> %s" % (k, v) for k, v in sorted(res.items())))
print("ok")
