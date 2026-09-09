import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
print('sections:',len(d['sections']))
for i,s in enumerate(d['sections']):
    print(f'=== S{i} type={s.get("type")} title={s.get("title")!r} nparas={len(s.get("paras",[]))}')
print('--- S3 paras ---')
for i,p in enumerate(d['sections'][3].get('paras',[])):
    print(f'[{i}]',p[:150].replace(chr(10),' '))
