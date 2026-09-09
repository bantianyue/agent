import re,sys,html
sys.stdout.reconfigure(encoding='utf-8')
h=open('_cur.html',encoding='utf-8',errors='ignore').read()
for kw in ['<title>','og:title','og:description','article:published_time']:
    for m in re.finditer(r'<meta[^>]*'+kw+r'[^>]*>',h):
        print(m.group(0)[:300])
t=re.findall(r'<title>(.*?)</title>',h,re.S)
print('TITLE:',html.unescape(t[0]) if t else None)
print('og:image:', re.findall(r'property="og:image" content="([^"]+)"',h)[:1])
