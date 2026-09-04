# -*- coding: utf-8 -*-
"""PyTorch 2.14 release blog - extract ordered body to _blocks.json, protect inline <code>"""
import re, html as H, json, os
from bs4 import BeautifulSoup
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
raw=open(base+"/source.html",encoding="utf-8",errors="ignore").read()
m=re.search(r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*)',raw,re.S)
seg=m.group(1)
for c in [r'<footer',r'id="comments"',r'class="entry-footer"',r'<div[^>]*class="[^"]*related-post',r'Newsletter']:
    mm=re.split(c,seg,flags=re.I)
    if len(mm)>1: seg=mm[0]
soup=BeautifulSoup(seg,'html.parser')

# 占位: inline code 收集 & 遮蔽 (让 get_text 后能被还原, 用不可见分隔标记)
CT={
 'PLACEHOLDER_START':'\uE000','PLACEHOLDER_END':'\uE001',
}
# 遍历, 用直接结构化: 对每个顶层块 find recursion。简化: 直接 walking soup children 顶层
def gtext(el):
    """取段落文本, 把 <code>..</code> 内容包占位符保护成可翻译但返原——实际上翻译不应动它,我们单独替换"""
    out=[]
    for node in el.descendants:
        pass
    return el.get_text(' ',strip=True)

blocks=[]
# 完整文档序
for el in soup.find_all(['h1','h2','h3','h4','h5','p','ul','ol','li','pre','blockquote','table']):
    if el.find_parent(['h1','h2','h3','h4','h5','p','ul','ol','li','pre','blockquote','table']) is not None:
        # 跳过被嵌套(父仍有同类容器) 防止 li in ul 等重复
        if el.name in ('li','p') and el.find_parent(['ul','ol']) is not None and el.name=='li':
            pass
    pass

# 逐顶层容器迭代顺序 (walk recursion)
def walk(node,out):
    for child in node.children:
        if not getattr(child,'name',None): continue
        nm=child.name
        if nm in ('h1','h2','h3','h4','h5','h6'):
            lv=int(nm[1]); txt=child.get_text(' ',strip=True)
            if txt: out.append({'H':lv,'T':txt})
        elif nm=='p':
            txt=child.get_text(' ',strip=True)
            if txt: out.append({'P':txt})
        elif nm=='pre':
            ct=''.join(child.stripped_strings) if child.stripped_strings else child.get_text('',strip=False)
            if ct.strip(): out.append({'C':ct,'lang':''})
        elif nm=='blockquote':
            q=child.get_text(' ',strip=True)
            if q: out.append({'Q':q})
        elif nm in ('ul','ol'):
            for li in child.find_all('li',recursive=False):
                t=li.get_text(' ',strip=True)
                if t: out.append({'LI':t})
        elif nm=='table':
            rows=[]
            for tr in child.find_all('tr'):
                cs=[" ".join(td.get_text(' ',strip=True).split()) for td in tr.find_all(['td','th'])]
                if cs:rows.append(cs)
            if rows: out.append({'TBL':rows})
        elif nm in ('div','section','article'):
            walk(child,out)
blocks=[]
walk(soup,blocks)
json.dump(blocks,open(base+"/_blocks.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
from collections import Counter
print("blocks:",len(blocks),Counter(list(b.keys())[0] for b in blocks))
# head count
print("标题块:",sum('H' in b for b in blocks))
# lang
cs=[b for b in blocks if 'C' in b]
print("code块:",len(cs))
for c in cs[:1]: print("code样本",c['C'][:150])
json.dump(blocks,open(base+"/_blocks.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
