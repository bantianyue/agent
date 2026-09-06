import re, json, os
base='D:/06_Hermes/articles/llm-routing-can-cost-more'
raw=open('D:/06_Hermes/articles/art_fx_orig.json',encoding='utf-8',errors='replace').read()
raw=re.sub(r"\\\\(?![\\\\\"bfnrt/])", "", raw)
d=json.loads(raw)
a=d['tweet']['article']
blocks=a['content']['blocks']; emap=a['content']['entityMap']
me=a.get('media_entities') or []
info_by_mid={}
for m in me:
    mi=m['media_info']
    u=(mi.get('original_img_url') or '') or (mi.get('preview_image',{}) or {}).get('original_img_url','')
    if not u and mi.get('variants'):
        u=mi['variants'][0].get('url','')
    info_by_mid[m['media_id']]={'url':u,'typename':mi.get('__typename')}
# walk atomic media in block order
used=[]
covered=set()
for i,b in enumerate(blocks):
    if b['type']!='atomic': continue
    er=b.get('entityRanges',[])
    if not er: continue
    v=emap[int(er[0]['key'])]
    if v.get('value',{}).get('type')=='MEDIA':
        mid=v['value']['data'].get('mediaItems',[{}])[0].get('mediaId')
        used.append((i,mid))
        covered.add(mid)
print("body MEDIA blocks:", len(used))
print("used mids:", [m for _,m in used])
print("media_entities mids:", [m for m in info_by_mid])
print("unused media_entities:", [m for m in info_by_mid if m not in covered])
# dump info to json for then download separately after we decide naming
open(base+'/used_media.json','w').write(json.dumps([{'block':i,'mid':mid,'info':info_by_mid[mid]} for i,mid in used],indent=1))
print("cover url:", a.get('cover_media',{}).get('media_info',{}).get('original_img_url'))
