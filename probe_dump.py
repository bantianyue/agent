import re, json
raw=open('D:/06_Hermes/articles/art_fx_orig.json',encoding='utf-8',errors='replace').read()
raw=re.sub(r"\\\\(?![\\\\\"bfnrt/])", "", raw)
d=json.loads(raw)
a=d['tweet']['article']
blocks=a['content']['blocks']; emap=a['content']['entityMap']
out=[]
MEDIA_SEQ=[0]
def tmap(t):
    return {'header-one':'H1','header-two':'H2','header-three':'H3','unstyled':'P','ordered-list-item':'OLI','unordered-list-item':'ULI'}.get(t,t)
btype=0
img=0
for i,b in enumerate(blocks):
    t=b['type']
    if t=='atomic':
        er=b.get('entityRanges',[])
        ent=None
        if er:
            ent=emap[int(er[0]['key'])]
        et=ent.get('value',{}).get('type') if ent else None
        dd=ent.get('value',{}).get('data',{}) if ent else {}
        if et=='MEDIA':
            img+=1
            cap=(dd.get('caption') or '').strip()
            out.append(f'\n=====[IMG#{img} block{i}] caption="{cap}"=====')
        elif et=='MARKDOWN':
            out.append(f'\n=====[CODE block{i}]=====\n{dd.get("markdown","")}')
        elif et=='LINK':
            out.append(f'\n=====[LINK block{i}] {dd.get("url","")}=====')
        elif et=='DIVIDER':
            out.append('\n=====[DIVIDER]=====')
        else:
            out.append(f'\n=====[ATOMIC?{et} block{i}] txt="{b.get("text","")}"=====')
    else:
        out.append(f'\n[{i}|{tmap(t)}] ' + (b.get('text') or '').replace('\n',' / '))
open('D:/06_Hermes/articles/llm-routing-can-cost-more/raw_blocks.txt','w',encoding='utf-8').write('\n'.join(out))
print('wrote raw_blocks.txt', sum(len(x) for x in out),'chars,', len(blocks),'blocks')
