import re,sys,html
sys.stdout.reconfigure(encoding='utf-8')
h=open('_sm.html',encoding='utf-8',errors='ignore').read()
t=re.search(r'<title>(.*?)</title>',h,re.S)
print('TITLE:',html.unescape(re.sub(r'\s+',' ',t.group(1))) if t else None)
print('h1/h2/h3:')
for m in re.finditer(r'<h([123])[^>]*>(.*?)</h\1>',h,re.S):
    txt=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',m.group(2)))).strip()
    if txt: print('  '*(int(m.group(1))-1)+f'H{m.group(1)}: {txt[:85]}')
print('imgs',len(re.findall(r'<img',h)),'pre',len(re.findall(r'<pre',h)),'svg',len(re.findall(r'<svg',h)))
for m in re.finditer(r'<img[^>]+src="([^"]+)"',h):
    print('IMG>', m.group(1)[:110])
