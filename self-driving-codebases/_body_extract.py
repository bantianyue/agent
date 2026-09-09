import sys,re,html
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
h=open(r'D:\06_Hermes\articles\_cur.html',encoding='utf-8',errors='ignore').read()
soup=BeautifulSoup(h,'html.parser')
h1=soup.find('h1'); node=h1
for _ in range(8):
    node=node.parent
    if node is None: break
    if node.name in ('article','main'): break
# traverse article children in order capturing headings, paragraphs, lists, images, code, figures
def clean(x): return re.sub(r'[ \t]+',' ',x).strip()
lines=[]; imgs=[]; codebuf=[]; incode=False
for el in node.descendants:
    if el.name=='figure' or el.name=='img':
        # collect image with container caption later; capture figure-level
        pass
for el in node.find_all(['h2','h3','h4','p','ol','ul','pre','img','figure','figcaption']):
    if el.name=='h2': lines.append('\n## '+clean(el.get_text(' ',strip=True))+'\n')
    elif el.name=='h3': lines.append('\n### '+clean(el.get_text(' ',strip=True))+'\n')
    elif el.name=='h4': lines.append('\n#### '+clean(el.get_text(' ',strip=True))+'\n')
    elif el.name in ('p','figcaption'):
        lines.append(clean(el.get_text(' ',strip=True))+'\n')
    elif el.name in ('ol','ul'):
        for li in el.find_all('li',recursive=False):
            lines.append('* '+clean(li.get_text(' ',strip=True))+'\n')
    elif el.name=='pre':
        lines.append('```\n'+clean(el.get_text('\n',strip=False))+'\n```\n')
    elif el.name=='img':
        src=el.get('src') or el.get('data-src') or ''
        if src and not src.startswith('data:'):
            lines.append(f'\n[IMG {src}]\n')
            imgs.append(src)
# dedupe nested duplicates: we traversed descendants -> p inside article; fine but li nested inside li may double.
out=''.join(lines)
# collapse triple newlines
out=re.sub(r'\n{3,}','\n\n',out)
open(r'D:\06_Hermes\articles\self-driving-codebases\_body_raw.txt','w',encoding='utf-8').write(out)
print('chars',len(out))
print('images found',len(imgs))
seen=set()
for u in imgs:
    if u not in seen:
        seen.add(u)
        print(u[:150])
