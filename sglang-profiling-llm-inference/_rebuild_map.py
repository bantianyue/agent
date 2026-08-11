#!/usr/bin/env python3
"""sglang 重建：从 _tweet.json 的 article.content.blocks 严格按原文流生成图文序。
100% 保持一致：段落顺序、h2/h3标题、代码块、图片插入位置、图片caption 全部来自原文。
"""
import json, os

base = r"D:/06_Hermes/articles/sglang-profiling-llm-inference"
t = json.load(open(base+"/_tweet.json", encoding="utf-8"))
a = t['tweet']['article']
blocks = a['content']['blocks']
em = a['content'].get('entityMap', [])
emap = {}
for e in em: emap[str(e.get('key'))] = e['value']

# 1) 建 localMediaId -> (media_id, url, caption) 映射
me = a.get('media_entities', [])
mid2url = {}
for m in me:
    mid = str(m.get('media_id'))
    mi = m.get('media_info',{})
    url = mi.get('original_img_url') or ''
    if mid and url: mid2url[mid]=url

# 2) 图插入位置: block# -> (localMediaId, caption)
img_pos = {}
local_to_mid = {}
for i,b in enumerate(blocks):
    for er in b.get('entityRanges',[]):
        ent = emap.get(str(er.get('key')))
        if ent and ent.get('type')=='MEDIA':
            cap = ent['data'].get('caption','')
            mits = ent['data'].get('mediaItems',[{}])
            local = mits[0].get('localMediaId') if mits else None
            md = mits[0].get('mediaId') if mits else None
            local_to_mid[str(local)] = str(md)
            img_pos[i] = (str(local), cap.strip())

# 3) 逐 block 生成 segment 流
# 磁盘 fig 命名与 localId 的映射 (来自 _content.json caption 顺序)
# fig01=local40, fig02=local32, fig03=local52, fig04=local44, fig05=local38,
# fig06=local34, fig07=local42, fig08=local46, fig09=local26, fig10=local36,
# fig11=local28, fig12=local48, fig13=local56, fig14=local54, fig15=local50,
# fig16=local30, fig17=local24(local24 缺失已补下载, local56 原图是 fig13)
local2fig = {
 '40':'fig01.jpg','32':'fig02.png','52':'fig03.jpg','44':'fig04.png','38':'fig05.png',
 '34':'fig06.jpg','42':'fig07.jpg','46':'fig08.jpg','26':'fig09.jpg','36':'fig10.jpg',
 '28':'fig11.jpg','48':'fig12.jpg','56':'fig13.png','54':'fig14.jpg','50':'fig15.jpg',
 '30':'fig16.jpg','24':'fig17.jpg'}

print("=== 磁盘fig核对 ===")
disk = sorted(f for f in os.listdir(base) if f.startswith('fig') and (f.endswith('.png') or f.endswith('.jpg')))
missing = [f for f in local2fig.values() if f not in disk]
print("需要17张, 磁盘:", len(disk), "缺:", missing)

# 保存映射供下一步用
json.dump({"local2fig":local2fig,"img_pos":{str(k):v for k,v in img_pos.items()},
           "local_to_mid":local_to_mid,"mid2url":mid2url},
          open(base+"/_imgmap.json","w"), ensure_ascii=False, indent=1)
print("已写 _imgmap.json")
