import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
art=d['tweet']['article']
c=art['content']
blocks=c['blocks']
me=art.get('media_entities') or []
print('media_entities n=',len(me))
for v in me[:10]:
    print('type',v.get('media_type'),'| id',v.get('media_id'),'| orig',(v.get('media_info') or {}).get('original_img_url'))
print('cover:',art.get('cover_media'))
print('---- block types ----')
from collections import Counter
print(Counter(b.get('type') for b in blocks))
for i,b in enumerate(blocks[:20]):
    t=b.get('type')
    txt=(b.get('text') or '')
    ent=len(b.get('entityRanges') or [])
    print(i,t,repr(txt[:80]),'ents',ent)
