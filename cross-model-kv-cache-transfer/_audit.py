import re,sys,html
sys.stdout.reconfigure(encoding='utf-8')
h=open('article.html',encoding='utf-8').read()
imgs=re.findall(r'<img',h)
print('imgs:',len(imgs),'figs:',len(re.findall(r'fig\d+\.png',h)))
print('h2:',len(re.findall(r'<h2',h)),'h3:',len(re.findall(r'<h3',h)))
print('figcaption:',len(re.findall(r'<figcaption',h)))
# text stats
txt=re.sub(r'<[^>]+>','',h)
txt=html.unescape(txt)
cjk=len(re.findall(r'[\u4e00-\u9fff]',txt))
lat=len(re.findall(r'[A-Za-z]',txt))
print(f'cjk={cjk} latin={lat} ratio_lat={lat/(cjk+1):.2f}')
for pat in [r'\\\(',r'\\\[',r'\\frac',r'\\text',r'\\mathrm',r'\\sum',r'\$',r'\[IMAGE',r'__CODE__',r'WECHATIMGPH_',r'{\\displaystyle']:
    print(pat, len(re.findall(pat,h)))
for kw in ['原文','原作者','翻译','搬运','本文','本博客','英文原文']:
    print('kw',kw, txt.count(kw))
# images mmbiz not here (draft); check html img src list
print('img srcs:', sorted(set(re.findall(r'src="([^"]+)"',h)))[:20])
