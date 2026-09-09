import sys,html,re
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
h=open(r'D:\06_Hermes\articles\_cur.html',encoding='utf-8',errors='ignore').read()
soup=BeautifulSoup(h,'html.parser')
h1=soup.find('h1')
print('h1 text:', h1.get_text(strip=True)[:80] if h1 else None)
# climb to article/main container
node=h1
for _ in range(6):
    node=node.parent
    if node is None: break
    if node.name in ('article','main'): break
print('container:',node.name, node.get('class'))
# extract direct text sequence
def clean(x):
    t=re.sub(r'\s+',' ',x).strip()
    return t
items=[]
for el in node.descendants:
    if el.name in ('p','h2','h3','li') and el.get_text(strip=True):
        items.append((el.name,clean(el.get_text(' ',strip=True))))
for k,t in items[:25]:
    print(k,'|',t[:180])
print('...total blocks',len(items))
