import re,sys,html
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
raw=open('_sm.html',encoding='utf-8',errors='ignore').read()
soup=BeautifulSoup(raw,'html.parser')
main=soup.find('main') or soup.find('article') or soup
def strip_tags(f):
    s=re.sub(r'<br\s*/?>','\n',f); s=re.sub(r'<[^>]+>','',s); return html.unescape(s)
out=[]
for el in main.find_all(['h1','h2','h3','h4','p','li','pre','img','table','blockquote']):
    if el.name in ('h1','h2','h3','h4'):
        t=re.sub(r'\s+',' ',el.get_text(' ',strip=True))
        if t: out.append('\n'+'#'*int(el.name[1])+' '+t+'\n')
    elif el.name=='pre':
        out.append('[CODE]\n'+strip_tags(str(el)).strip('\n')+'\n[/CODE]\n')
    elif el.name=='img':
        out.append(f'[IMG {el.get("src")}]\n')
    elif el.name=='table':
        rows=[]
        for tr in el.find_all('tr'):
            rows.append(' | '.join(re.sub(r'\s+',' ',strip_tags(str(c))).strip() for c in tr.find_all(['td','th'])))
        out.append('[TABLE]\n'+'\n'.join(rows)+'\n[/TABLE]\n')
    else:
        t=re.sub(r'\s+',' ',el.get_text(' ',strip=True))
        if t: out.append(t+'\n')
txt=''.join(out); txt=re.sub(r'\n{3,}','\n\n',txt)
open('_sm_body.txt','w',encoding='utf-8').write(txt)
print('chars',len(txt))
print('code blocks:',txt.count('[CODE]'))
