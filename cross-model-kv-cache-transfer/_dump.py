import json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
for si in [1,2]:
    print(f'############ S{si} {d["sections"][si]["title"]} ############')
    for pi,p in enumerate(d['sections'][si]['paras']):
        print(f'--- [{pi}] ---')
        print(p)
        print()
