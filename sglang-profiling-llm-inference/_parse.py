#!/usr/bin/env python3
"""临时脚本：解析 X Article DraftJS → _content.json + 下载全部图片。"""
import json, os, sys, urllib.request, re

DIR = r"D:/06_Hermes/articles/sglang-profiling-llm-inference"
d = json.load(open(os.path.join(DIR, "_tweet.json"), encoding="utf-8"))
a = d['tweet']['article']
blocks = a['content']['blocks']
entity_map = a['content']['entityMap']   # list
media_entities = a.get('media_entities', []) or []

# 建立 media_id -> url 映射
media_url = {}
for m in media_entities:
    mi = m.get('media_info', {})
    url = mi.get('original_img_url') or mi.get('url')
    if url:
        media_url[m.get('media_id')] = url
media_url.update({str(k): v for k, v in media_url.items()})

# 建立 entityMap key -> (caption, mediaId) 映射
entity_info = {}
for e in entity_map:
    v = e.get('value', {})
    data = v.get('data', {})
    cap = data.get('caption') or ''
    items = data.get('mediaItems') or []
    mid = items[0].get('mediaId') if items else None
    entity_info[e.get('key')] = {'caption': cap, 'mediaId': mid}

# 遍历 blocks，顺序输出
content = []
img_idx = 0
for b in blocks:
    btype = b.get('type')
    text = b.get('text', '')
    if btype == 'atomic':
        er = b.get('entityRanges', [])
        if er:
            ekey = str(er[0].get('key'))
            info = entity_info.get(ekey, {})
            mid = info.get('mediaId')
            cap = info.get('caption')
            url = media_url.get(mid) or (media_url.get(str(mid)))
            if url:
                img_idx += 1
                content.append({"type":"img","media_id":mid,"url":url,"caption":cap,"fig":f"fig{img_idx:02d}"})
            else:
                content.append({"type":"img","media_id":mid,"url":None,"caption":cap,"fig":f"fig{img_idx+1:02d}", "MISSING":True})
    elif btype == 'header-two':
        if text.strip():
            content.append({"type":"h2","text":text})
    elif btype == 'unstyled':
        if text.strip():
            # 纯数字/URL 行也保留
            content.append({"type":"p","text":text})

json.dump(content, open(os.path.join(DIR,"_content.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# 汇总
imgs = [c for c in content if c['type']=='img']
paras = [c for c in content if c['type']=='p']
heads = [c for c in content if c['type']=='h2']
print(f"content: {len(content)} blocks | {len(imgs)} img | {len(paras)} para | {len(heads)} h2")
print("images:")
for c in imgs:
    print(f"  {c['fig']} {c.get('url','MISSING')[:70]} | cap: {c['caption'][:50]}")
# 未匹配媒体
missing = [c for c in imgs if not c.get('url')]
print("missing urls:", len(missing))
