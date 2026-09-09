import json,re
d=json.load(open('article_data.json',encoding='utf-8'))
def clean(t):
    t=t.replace('{=}','=').replace('\\times','×').replace('\\,','')
    t=t.replace('\\{','{').replace('\\}','}')
    t=re.sub(r'\{([+\-=])','\\1',t)
    t=re.sub(r'([+\-=])\}',lambda m:m.group(1),t)
    t=t.replace('{+}','+').replace('{-}','-').replace('{=}','=')
    return t
for s in d['sections']:
    s['paras']=[clean(p) for p in s.get('paras',[])]
    for fl in (s.get('fig_after') or {}).values():
        for f in fl: f['caption']=clean(f['caption'])
d['lead']=[clean(p) for p in d['lead']]
d['conclusion']=[clean(p) for p in d['conclusion']]
for it in d['summary']: it['body']=clean(it['body'])
json.dump(d, open('article_data.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
blob=json.dumps(d,ensure_ascii=False)
print('clean done')
for pat in [r'\\[a-zA-Z]',r'\{[+\-=]',r'\^\{',r'_\{',r'\\,','{=}']:
    print(pat, len(re.findall(pat,blob)))
