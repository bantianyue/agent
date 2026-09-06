import re, json
from collections import Counter
raw=open('D:/06_Hermes/articles/art_fx_orig.json',encoding='utf-8',errors='replace').read()
raw=re.sub(r"\\\\(?![\\\\\"bfnrt/])", "", raw)
d=json.loads(raw)
a=d['tweet']['article']
blocks=a['content']['blocks']
emap=a['content']['entityMap']
me=a.get('media_entities') or []
url_by_mid={}
for m in me:
    mi=m['media_info']
    if mi.get('original_img_url'):
        url_by_mid[m['media_id']]=mi.get('original_img_url')
    elif mi.get('preview_image',{}).get('original_img_url'):
        url_by_mid[m['media_id']]=mi['preview_image']['original_img_url']
print("media_entities ids:", [m['media_id'] for m in me])
print("cover_media:", a.get('cover_media'))
print()
# ordered walk, print the document structure compactly
def txt(b): return (b.get('text') or '')
btype_cnt=Counter()
img_seq=0
for i,b in enumerate(blocks):
    t=b['type']
    btype_cnt[t]+=1
    if t=='atomic':
        er=b.get('entityRanges',[])
        if er:
            v=emap[int(er[0]['key'])]
            et=v.get('value',{}).get('type'); dd=v.get('value',{}).get('data',{})
        else:
            et=None; dd={}
        if et=='MEDIA':
            mid=dd.get('mediaItems',[{}])[0].get('mediaId')
            img_seq+=1
            cap=(dd.get('caption') or '')[:70]
            print(f'[{i}] AT-IMG#{img_seq} mid={mid} url={url_by_mid.get(mid,"?")[:60]} cap={cap}')
        elif et=='MARKDOWN':
            code=dd.get('markdown','')
            print(f'[{i}] AT-CODE ({len(code)} chars first3lines=')
            print('   | '+code.replace(chr(10),chr(10)+'   | ')[:400])
        elif et=='LINK':
            print(f'[{i}] AT-LINK {dd.get("url","")[:70]}')
        elif et=='DIVIDER':
            print(f'[{i}] AT-DIVIDER')
        else:
            print(f'[{i}] AT-?({et}) text={txt(b)[:60]} ddkeys={list(dd.keys())}')
    elif t in ('header-one','header-two','header-three','unstyled'):
        body=txt(b)
        show=body if len(body)<90 else body[:88]+'…'
        print(f'[{i}] {t.upper():13s} {show}')
    elif t in ('ordered-list-item','unordered-list-item'):
        pre='- ' if t=='unordered-list-item' else 'i. '
        print(f'[{i}] {t:22s} {pre}{txt(b)[:90]}')
