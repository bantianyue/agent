import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
art=d['tweet']['article']
c=art['content']
print('content type:',type(c))
if isinstance(c,dict):
    print('content keys:',list(c.keys()))
    blocks=c.get('blocks',[])
    print('blocks:',len(blocks))
else:
    print('content sample:',str(c)[:500])
me=art.get('media_entities',{})
print('media_entities keys:',list(me.keys())[:10], 'n=',len(me))
for k,v in list(me.items())[:8]:
    mi=v.get('media_info',{})
    orig=mi.get('original_img_url') or (v.get('preview_image') or {}).get('original_img_url')
    print(' media',k,'type',v.get('media_type'),'orig',orig)
cm=art.get('cover_media')
print('cover:',cm)
