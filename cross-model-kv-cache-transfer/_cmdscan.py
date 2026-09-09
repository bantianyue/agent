import re,json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
blob=json.dumps(d,ensure_ascii=False)
cmds=sorted(set(re.findall(r'\\[a-zA-Z]+\{?',blob)))
print(len(cmds),'commands')
for c in cmds: print(c)
print('delims:', re.findall(r'\\[()\[\]]',blob)[:10])
print('^_ counts:', blob.count('^{'), blob.count('_{'), blob.count('^') ,blob.count('_'))
