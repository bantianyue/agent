import json
f='D:/06_Hermes/articles/llm-routing-can-cost-more/article_data.json'
d=json.load(open(f,encoding='utf-8'))
for s in d['sections']:
    n=len(s.get('paras',[]))
    fa=s.get('fig_after') or {}
    newfa={}
    for k in list(fa):
        kk=int(k)
        if kk>=n:
            kk=n-1
        # merge into existing key if collision
        if str(kk) in newfa:
            newfa[str(kk)] = newfa[str(kk)] + fa[k]
        else:
            newfa[str(kk)] = fa[k]
    if fa: s['fig_after']=newfa
refs={}
for s in d['sections']:
    for k,v in (s.get('fig_after') or {}).items():
        for fg in v:
            refs[fg['src']]=refs.get(fg['src'],0)+1
json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print("fig refs:", refs)
for s in d['sections']:
    n=len(s.get('paras',[]))
    for k in (s.get('fig_after') or {}):
        if int(k)>=n: print("STILL OUT", s['title'], k, n)
print("done")
