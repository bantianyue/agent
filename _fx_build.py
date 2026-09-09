import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
art=d['tweet']['article']
blocks=art['content']['blocks']
emap=art['content']['entityMap']
me=art['media_entities']
mid2url={str(m.get('media_id')):(m.get('media_info') or {}).get('original_img_url') for m in me}
segs=[]
fig_no=0
for b in blocks:
    t=b.get('type'); txt=(b.get('text') or '')
    if t in ('header-one','header-two','header-three'):
        segs.append(f'\n##H {txt.strip()}\n')
    elif t=='atomic':
        er=b.get('entityRanges') or []
        if not er: continue
        ent=emap[int(er[0]['key'])]; data=(ent.get('value') or {}).get('data',{})
        if data.get('mediaItems'):
            fig_no+=1
            segs.append(f'\n[FIG{fig_no}]\n')
        elif data.get('markdown'):
            segs.append(f'\n```\n{data.get("markdown")}\n```\n')
        elif data.get('url'):
            segs.append(f'\n(LINK {data.get("url")})\n')
    else:
        segs.append(txt+'\n')
open(r'D:\06_Hermes\articles\rlm-agents-ma-diligence\_body.txt','w',encoding='utf-8').write(''.join(segs))
print('figs',fig_no,'chars',sum(len(x) for x in segs))
# download manifest
out=[]
fig=0
for b in blocks:
    if b.get('type')!='atomic': continue
    er=b.get('entityRanges') or []
    if not er: continue
    ent=emap[int(er[0]['key'])]; data=(ent.get('value') or {}).get('data',{})
    if data.get('mediaItems'):
        fig+=1
        mid=str(data['mediaItems'][0].get('mediaId'))
        out.append((fig,mid,mid2url.get(mid)))
open(r'D:\06_Hermes\articles\rlm-agents-ma-diligence\_dl.txt','w',encoding='utf-8').write('\n'.join(f'{a}|{b}|{c}' for a,b,c in out))
print('manifest lines',len(out))
cov=art.get('cover_media') or {}
print('cover', (cov.get('media_info') or {}).get('original_img_url'))
