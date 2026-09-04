# -*- coding: utf-8 -*-
import re
h=open('article.html',encoding='utf-8').read()
seq=[]
for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>',h,re.S):
    seq.append((m.start(),'H',re.sub(r'<[^>]+>','',m.group(1))[:16]))
for m in re.finditer(r'<p[^>]*>(.*?)</p>',h,re.S):
    t=re.sub(r'<[^>]+>','',m.group(1)).strip()
    seq.append((m.start(),'P',t[:16]+('…' if len(t)>16 else '')))
for m in re.finditer(r'<img[^>]*src="([^"]+)"',h):
    seq.append((m.start(),'IMG',m.group(1).split('/')[-1]))
seq.sort()
# detect adjacent IMG without P between
out=[]; prev_kind=''
nrun=0
for _,k,label in seq:
    pass
# just print blocks condensed
for i,(_,k,label) in enumerate(seq):
    if k=='H': out.append('['+label+']'); 
    elif k=='P': out.append('¶')
    else: out.append('FIG'+label.replace('.png',''))
s='\n'.join(out)
# walk to find runs of FIG separated by no ¶
import re as rr
res=rr.findall(r'(FIG\d+)',s)
print('图中顺序:',res)
# consecutive figs w/o ¶ between
clean=s.split('\n')
bad=[]
prev=''
for ln in clean:
    if ln.startswith('FIG'):
        if prev.startswith('FIG'): bad.append(prev+' & '+ln)
    prev=ln
print('相邻无文本图对:', bad if bad else 'NONE')
