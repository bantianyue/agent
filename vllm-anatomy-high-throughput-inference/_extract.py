# -*- coding: utf-8 -*-
"""从 source.html 提取 DOM顺序内容块(h1-h6/p/li/code/figcaption/pre) 到 _blocks.json"""
import re, html as H, json, sys
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
raw=open(base+"/source.html",encoding="utf-8",errors="ignore").read()

# 定位主内容 (prose)
m=re.search(r'<div class="prose[^"]*">(.*?)</div>\s*</article>', raw, re.S) or \
  re.search(r'<article[^>]*>\s*<header.*?</header>(.*?)(?:<footer|</article>)', raw, re.S)
body = m.group(1) if m else raw

# 清洗导航/脚本位(prose 内不该有) 
def strip_node(tag,text):
    return re.sub(r'<%s[^>]*>.*?</%s>'%(tag,tag),'',text,flags=re.S)

# 按行级 tag 顺序切：把 p,h2,h3,h4,pre,ul/ol,figure,table,blockquote,hr 作为原子段（保留内部）
# 简单的自上而下 token: 用 bs4 抓 body 直接按 document 迭代最稳
import subprocess
# 检查 bs4
try:
    from bs4 import BeautifulSoup
except:
    subprocess.run([sys.executable,"-m","pip","install","beautifulsoup4","-q"],check=True); from bs4 import BeautifulSoup

soup=BeautifulSoup(body,'html.parser')
blocks=[]
for el in soup.find_all(['h1','h2','h3','h4','h5','h6','p','pre','figure','ul','ol','table','blockquote','li']):
    # 跳过嵌套重复(ul里的li,figure里的p会重复先父后子)
    # 只取"顶层块"：没有块级父(除容器) 用 find_all 会含嵌套。手动 walk
    pass

# 方式：直接迭代顶层子元素保留顺序，遇容器向内
def walk(node, out):
    for child in node.children:
        if not getattr(child,'name',None): 
            continue
        name=child.name
        if name in ('h1','h2','h3','h4','h5','h6'):
            lvl=int(name[1])
            txt=child.get_text(' ',strip=True)
            if txt: out.append({"T":txt,"lvl":lvl})
        elif name=='p':
            # 图注可能是 p>img 或 figure;跳过空p
            imgs=child.find_all('img')
            txt=child.get_text(' ',strip=True)
            if imgs and not txt: pass
            elif imgs and txt:  # p内联带图? 罕见自动略，保留文本
                out.append({"T":txt})
            elif txt: out.append({"T":txt})
        elif name=='pre':
            # 代码
            lang=''
            code_el=child.find('code')
            clss=" ".join(code_el.get('class',[])) if code_el else ''
            lm=re.search(r'language-(\w+)',clss)
            if lm: lang=lm.group(1)
            code_txt=H.unescape(child.get_text('\n'))
            if code_txt.strip(): out.append({"C":code_txt.rstrip('\n'),"lang":lang})
        elif name=='figure':
            imgs=child.find_all('img')
            for im in imgs:
                src=im.get('src') or im.get('data-src')
                if src: out.append({"FIG":src})
            cap=child.find('figcaption')
            if cap:
                ct=cap.get_text(' ',strip=True)
                if ct: out.append({"T":ct})
        elif name=='img':
            src=child.get('src')
            if src: out.append({"FIG":src})
        elif name in ('ul','ol'):
            # 每个 li 成段(保留) 或整体 :每 li 一段更好读
            items=[li.get_text(' ',strip=True) for li in child.find_all('li',recursive=False)]
            for it in items:
                if it: out.append({"LI":it})
        elif name=='table':
            rows=[]
            for tr in child.find_all('tr'):
                cells=[" ".join(td.get_text(' ',strip=True).split()) for td in tr.find_all(['td','th'])]
                if cells: rows.append(cells)
            if rows: out.append({"TBL":rows})
        elif name=='blockquote':
            q=child.get_text(' ',strip=True)
            if q: out.append({"Q":q})
        elif name in ('div','section','article','main'):
            walk(child,out)

blocks=[]
walk(soup,blocks)
# 简化 merge: 相邻纯文本段落保留。代码/图/表留下
for b in blocks:
    if 'FIG' in b:
        # src可能相对，补全域名
        pass
json.dump(blocks,open(base+"/_blocks.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("blocks:", len(blocks))
from collections import Counter
print(Counter(list(b.keys())[0] for b in blocks))
# 打印图&代码count
print("图:", sum('FIG' in b for b in blocks), "代码:", sum('C' in b for b in blocks),"h区:", sum('T' in b and 'lvl' in b for b in blocks))
