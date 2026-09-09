import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
def walk(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items(): yield from walk(v,path+'/'+str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): yield from walk(v,path+f'[{i}]')
    else:
        yield path,obj
for p,v in walk(d):
    if isinstance(v,str):
        m=re.search(r'\\[a-zA-Z]',v)
        if m:
            i=m.start(); print(p,'>',repr(v[max(0,i-80):i+120]))
