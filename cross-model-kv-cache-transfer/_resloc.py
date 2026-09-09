import json,sys,re
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
def walk():
    for si,s in enumerate(d['sections']):
        for pi,p in enumerate(s.get('paras',[])):
            yield (f'S{si}.{pi}',s.get('title'),p)
for loc,ti,p in walk():
    if '^{' in p or '_{' in p or '\\' in p:
        print('===',loc, ti)
        print(p)
        print()
