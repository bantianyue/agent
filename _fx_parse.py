import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
art=d['tweet']['article']
blocks=art['content']['blocks']
emap=art['content']['entityMap']
me=art['media_entities']
mid2url={}
for m in me:
    mi=m.get('media_info') or {}
    u=mi.get('original_img_url')
    if not u and (m.get('preview_image') or {}).get('original_img_url'):
        u=m['preview_image']['original_img_url']
    mid2url[str(m.get('media_id'))]=u
segs=[]
for bi,b in enumerate(blocks):
    t=b.get('type'); txt=(b.get('text') or '')
    if t=='header-two' or t=='header-three' or t=='header-one':
        segs.append(('H',txt.strip())); 
    elif t=='atomic':
        er=b.get('entityRanges') or []
        if not er: segs.append(('EMPTY',txt)); continue
        ent=emap[int(er[0]['key'])]
        val=ent.get('value',{})
        typ=ent.get('type')
        data=val.get('data',{})
        if data.get('mediaItems'):
            mi=data['mediaItems'][0]
            mid=str(mi.get('mediaId'))
            cap=(mi.get('caption') or '')
            segs.append(('IMG',mid,cap,mid2url.get(mid)))
        elif data.get('markdown'):
            segs.append(('CODE',data.get('markdown','')[:80]))
        elif data.get('url'):
            segs.append(('LINK',data.get('url')))
        else:
            segs.append(('OTHER',txt,typ))
    else:
        segs.append(('P',txt))
print('segs total:',len(segs))
from collections import Counter
print(Counter(s[0] for s in segs))
for i,s in enumerate(segs):
    if s[0]=='H': print('###',i,s[1])
for i,s in enumerate(segs):
    if s[0]=='P':
        print(f'[{i}] P:',s[1][:130])
    elif s[0]=='IMG':
        print(f'[{i}] IMG:',s[1],'cap:',(s[2] or '')[:80],'url:',(s[3] or '')[-40:])
    elif s[0] in ('CODE','LINK','EMPTY','OTHER'):
        print(f'[{i}] {s[0]}:',str(s[1])[:80])
