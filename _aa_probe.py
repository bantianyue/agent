import re,sys
sys.stdout.reconfigure(encoding='utf-8')
h=open('_aa_abs.html',encoding='utf-8',errors='ignore').read()
t=re.search(r'<title>(.*?)</title>',h,re.S)
print('TITLE:', t.group(1).strip()[:250] if t else None)
ab=re.search(r'<blockquote class="abstract[^>]*>(.*?)</blockquote>',h,re.S)
if ab: print('ABS:', re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',ab.group(1))).strip()[:500])
for m in re.finditer(r'<h1 class="title[^>]*>(.*?)</h1>',h,re.S):
    print('H1:', re.sub(r'<[^>]+>','',m.group(1)).strip()[:250])
