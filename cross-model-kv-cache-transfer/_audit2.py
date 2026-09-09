import re,sys,json
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
# find latex remnants in sections
n=0
for s in d.get('sections',[]):
    for p in s.get('paras',[]):
        if r'\(' in p or r'\text' in p:
            n+=1
            if n<=6: print('LATEX>', p[:400].replace(chr(10),' ')); print('---')
print('total paras with latex:',n)
# english-heavy paragraphs (sentence mostly latin)
import unicodedata
def lat_ratio(t):
    L=len(re.findall(r'[A-Za-z]',t)); C=len(re.findall(r'[\u4e00-\u9fff]',t))
    return L/(C+1)
m=0
for s in d.get('sections',[]):
    for p in s.get('paras',[]):
        # check longest english run
        runs=re.findall(r'[A-Za-z][A-Za-z ,.;:\'\"()\-]{40,}',p)
        for r in runs[:1]:
            if lat_ratio(p)>0.3:
                m+=1
                if m<=8: print('EN>',p[:300].replace(chr(10),' ')); print('---')
                break
print('english-heavy paras:',m)
