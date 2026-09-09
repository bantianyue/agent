import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
def texts():
    for s in d['sections']:
        for p in s.get('paras',[]): yield p
        for fl in (s.get('fig_after') or {}).values():
            for f in fl: yield f['caption']
    for p in d['lead']: yield p
    for p in d['conclusion']: yield p
    for it in d['summary']: yield it['body']
n=0
for t in texts():
    for kw in ['{=}','\\times','\\{','\\}']:
        if kw in t:
            n+=1
            i=t.find(kw)
            print(kw,'>',t[max(0,i-60):i+80]); print()
