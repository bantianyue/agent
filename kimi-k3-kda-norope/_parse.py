#!/usr/bin/env python3
"""临时脚本：解析 Kimi K3 X 长文 DraftJS → _content.json + 下载图。"""
import json, os, sys, subprocess

DIR = r"D:/06_Hermes/articles/kimi-k3-kda-norope"
d = json.load(open(os.path.join(DIR, "_tweet.json"), encoding="utf-8"))
a = d['tweet']['article']
blocks = a['content']['blocks']
entity_map = a['content']['entityMap']  # list, indexed by atomic entityRanges[0].key
media_entities = a.get('media_entities', []) or []

media_url = {m.get('media_id'): (m.get('media_info',{}).get('original_img_url') or m.get('media_info',{}).get('url')) for m in media_entities}

content = []
img_idx = 0
for b in blocks:
    btype = b.get('type'); text = b.get('text','')
    if btype == 'atomic':
        er = b.get('entityRanges',[])
        if not er: continue
        key = er[0].get('key')
        ent = entity_map[key] if (key is not None and 0<=key<len(entity_map)) else None
        if not ent: continue
        v = ent.get('value',{}); etype = v.get('type'); data = v.get('data',{})
        if etype == 'MEDIA':
            items = data.get('mediaItems') or []
            mid = items[0].get('mediaId') if items else None
            url = media_url.get(mid)
            cap = data.get('caption') or ''
            if mid and url:
                img_idx += 1
                content.append({"type":"img","fig":f"fig{img_idx:02d}","url":url,"caption":cap,"mid":mid})
            else:
                content.append({"type":"img","fig":f"fig{img_idx+1:02d}","url":url,"caption":cap,"mid":mid})
        elif etype == 'LINK':
            content.append({"type":"link","text":data.get('url') or ''})
        else:
            content.append({"type":"other","etype":etype,"text":text[:40]})
    elif btype == 'header-two':
        if text.strip(): content.append({"type":"h2","text":text})
    elif btype == 'ordered-list-item':
        if text.strip(): content.append({"type":"oli","text":text})
    elif btype == 'unordered-list-item':
        if text.strip(): content.append({"type":"uli","text":text})
    elif btype == 'unstyled':
        if text.strip(): content.append({"type":"p","text":text})

json.dump(content, open(os.path.join(DIR,"_content.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

from collections import Counter
print(Counter(c['type'] for c in content))
imgs=[c for c in content if c['type']=='img']
print("imgs:", len(imgs), "all url:", all(c.get('url') for c in imgs))
print("missing url:", sum(1 for c in imgs if not c.get('url')))
