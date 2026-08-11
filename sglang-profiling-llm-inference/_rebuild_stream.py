#!/usr/bin/env python3
"""sglang 重建 v2：严格按 _tweet.json 原文 block 流生成 sections（100% 一致图文序）。
文本→译文(按内容匹配译文key)，图→按block顺序fig01-17，h2→节标题，代码块→保留。
"""
import json, os, re, difflib

base = r"D:/06_Hermes/articles/sglang-profiling-llm-inference"
t = json.load(open(base+"/_tweet.json", encoding="utf-8"))
a = t['tweet']['article']
blocks = a['content']['blocks']
em = a['content'].get('entityMap', [])
emap = {}
for e in em: emap[str(e.get('key'))] = e['value']
trans = json.load(open(base+"/_translations.json", encoding="utf-8"))

# 图锚点: block# -> (caption_en, caption_zh?, localId)
# fig 顺序(下载已按原文block顺序): block25→fig01...block92→fig17
fig_order = []  # (block#, localId, caption_en)
for i,b in enumerate(blocks):
    for er in b.get('entityRanges',[]):
        ent = emap.get(str(er.get('key')))
        if ent and ent.get('type')=='MEDIA':
            local = ent['data'].get('mediaItems',[{}])[0].get('localMediaId')
            cap = ent['data'].get('caption','').strip()
            fig_order.append((i, str(local), cap))
fig_order.sort()
print("图锚点数:", len(fig_order), "顺序:", [x[1] for x in fig_order])

# 图caption翻译(从译文里找, 译文key是text-only序号, 图caption嵌在其中)
# 直接用中文图注地图
zh_caps = {}
def find_zh_caption(en_cap):
    if not en_cap: return ''
    en_norm = re.sub(r'[^\w\u4e00-\u9fff]','',en_cap.lower())
    for k,v in trans.items():
        zh_norm = re.sub(r'[^\w\u4e00-\u9fff]','',str(v).lower())
        if en_norm and en_norm == zh_norm:
            return v
    return ''

# 文本块译文匹配: 译文key是text-only序号, 与原文全部block需要对齐。
# 我们建立 "原文block# -> 内容" ，译文key按 text-only 非空块顺序对应。
# 原文中可翻译文本块(非图锚, 非空) 依序 = 译文的0..N
text_blocks = []  # 原文block#, 按text-only序
for i,b in enumerate(blocks):
    is_img_anchor = i in [x[0] for x in fig_order]
    txt = b.get('text','').strip()
    if txt and not is_img_anchor:
        text_blocks.append(i)
assert len(text_blocks) == len(trans), f"文本块{len(text_blocks)} vs 译文{len(trans)}"
# 建立 block# -> 译文
block2trans = {}
for idx, bnum in enumerate(text_blocks):
    key = list(trans.keys())[idx]
    block2trans[bnum] = trans[key]
print("文本块映射:", len(block2trans), "块")

# 保存映射
json.dump({"fig_order":fig_order,"block2trans":block2trans,
           "zh_caps":zh_caps}, open(base+"/_stream_map.json","w"), ensure_ascii=False, indent=1)
print("已写 _stream_map.json")
# 打印对照确认
for bnum,txt in block2trans.items():
    print(f"  block[{bnum}] {str(txt)[:50]}")
