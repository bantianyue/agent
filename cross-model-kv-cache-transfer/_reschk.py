import re,json,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
blob=json.dumps(d,ensure_ascii=False)
for pat in [r'.{60}\^\{.{10}',r'.{60}_\{.{15}']:
    for m in re.finditer(pat,blob):
        print('RES>', m.group(0)[-90:]); print()
# show a few converted formula paragraphs
def showpara(p):
    print('P>',p[:500]); print()
for s in d['sections']:
    for p in s.get('paras',[]):
        if '𝒮' in p or 'ℝ' in p or 'ₛ' in p or '^' in p or '_' in p:
            showpara(p); break
    else:
        continue
    break
