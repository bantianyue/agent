import json
d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
art=d['tweet']['article']
blocks=art['content']['blocks']
emap=art['content']['entityMap']
out=[]
fig=0
for b in blocks:
    t=b.get('type'); txt=(b.get('text') or '')
    if t in ('header-one','header-two','header-three'):
        out.append({'type':'text','content':txt.strip()})
    elif t=='atomic':
        er=b.get('entityRanges') or []
        if not er: continue
        ent=emap[int(er[0]['key'])]; data=(ent.get('value') or {}).get('data',{})
        if data.get('mediaItems'):
            fig+=1
            ext='.png' if fig==12 else '.jpg'
            out.append({'type':'figure','img':f'fig{fig:02d}{ext}','caption':'','after_para':None,'hero':False})
        elif data.get('markdown'):
            pass
        elif data.get('url'):
            pass
    else:
        out.append({'type':'text','content':txt})
with open('blocks.jsonl','w',encoding='utf-8') as f:
    for b in out:
        f.write(json.dumps(b,ensure_ascii=False)+'\n')
print('rebuilt blocks.jsonl:',len(out),'blocks, figs:',fig)
