import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
blob=json.dumps(d,ensure_ascii=False)
mm=list(re.finditer(r'\\[a-zA-Z]',blob))
print('blob raw count:',len(mm))
for m in mm:
    print(repr(blob[max(0,m.start()-50):m.start()+70]))
# also count single backslash occurrences
print('single backslash count in raw string fields:')
def walk(o):
    if isinstance(o,dict):
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
    elif isinstance(o,str):
        yield o
for t in walk(d):
    if '\\' in t:
        print('  field has backslash:', repr(t[:200]))
