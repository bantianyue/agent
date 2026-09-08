import re,sys
sys.stdout.reconfigure(encoding='utf-8')
html=open('_probe.html',encoding='utf-8').read()
for kw in ['og:image','twitter:image']:
    for mm in re.finditer(r'<meta[^>]+'+kw+r'[^>]+>', html):
        print(mm.group(0)[:200])
# article title h1
h1=re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S)
print('H1:', re.sub(r'<[^>]+>','',h1[0]).strip() if h1 else None)
t=re.findall(r'<title>(.*?)</title>', html, re.S)
print('TITLE:', t[0] if t else None)
# author / date hints
for kw in ['author','published_time']:
    for mm in re.finditer(r'<meta[^>]*'+kw+r'[^>]*>', html):
        x=mm.group(0)
        if 'property' in x or 'name' in x:
            print(x[:180])
