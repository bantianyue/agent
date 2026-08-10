#!/usr/bin/env python3
"""通用解析技术文章 HTML -> _content.json + 下载图。
用法: python _parse.py <dirname> <title_css|auto>
"""
import re, sys, os, json, subprocess
from html.parser import HTMLParser

DIR = sys.argv[1]
raw = open(os.path.join(DIR, "page.html"), encoding="utf-8", errors="replace").read()

# 定位正文容器：优先 <main>，再 <article>，否则全文
m = re.search(r'<main[^>]*>(.*?)</main>', raw, re.S)
if not m: m = re.search(r'<article[^>]*>(.*?)</article>', raw, re.S)
body = m.group(1) if m else raw

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.cur=None; self.buf=[]; self.stack=[]
        self.skip=0; self.in_pre_code=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag in ('h1','h2','h3','h4'):
            self._flush(); self.cur='h'+tag[1]; self.buf=[]
            self.stack.append('h')
        elif tag=='p':
            self._flush(); self.cur='p'; self.buf=[]; self.stack.append('p')
        elif tag=='pre':
            self._flush(); self.cur='pre'; self.buf=[]; self.stack.append('pre')
        elif tag=='li':
            self._flush(); self.cur='li'; self.buf=[]; self.stack.append('li')
        elif tag=='img':
            self._flush()
            self.out.append(('img', d.get('src') or '', d.get('alt') or ''))
        elif tag in ('script','style','nav','header','footer','noscript'):
            self.skip+=1
    def handle_data(self, data):
        if self.cur and self.skip==0: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag in ('h1','h2','h3','h4','p','pre','li'):
            if self.stack and self.stack[-1]==('h' if tag in('h1','h2','h3','h4') else tag):
                self.stack.pop()
                # pre 去代码高亮包裹
                txt=''.join(self.buf)
                if self.cur=='pre':
                    txt=re.sub(r'<[^>]+>','',txt)  # inner spans
                txt=re.sub(r'\s+',' ',txt) if self.cur!='pre' else txt
                txt=txt.strip()
                if txt: self.out.append((self.cur, txt))
                self.cur=None; self.buf=[]
        elif tag in ('script','style','nav','header','footer','noscript'):
            self.skip=max(0,self.skip-1)
    def _flush(self):
        if self.cur:
            txt=''.join(self.buf)
            if self.cur=='pre': txt=re.sub(r'<[^>]+>','',txt)
            txt=re.sub(r'\s+',' ',txt) if self.cur!='pre' else txt
            txt=txt.strip()
            if txt: self.out.append((self.cur,txt))
            self.cur=None; self.buf=[]

p=P(); p.feed(body)

# 转 content
content=[]
for t,val in p.out:
    if t=='img':
        # 已单独收集为 img (src,alt)
        if isinstance(val,str):
            content.append({'type':'img','src':val,'caption':''})
    elif t in ('h1','h2','h3','h4'):
        if val: content.append({'type':('h2' if t in('h1','h2') else t), 'text':val})
    elif t=='pre':
        content.append({'type':'code','text':val})
    elif t in ('p','li'):
        if val: content.append({'type':t,'text':val})

# 图已经是 ('img',src,alt) 格式 需要重新对齐：上面 handle 里 img 直接 append tuple
# 修正：重新处理 out
content=[]
imgs=[]
for item in p.out:
    if item[0]=='img':
        imgs.append(item)
    else:
        t,val = item
        if t in ('h1','h2','h3','h4'):
            content.append({'type':('h2' if t in('h1','h2') else t),'text':val})
        elif t=='pre':
            content.append({'type':'code','text':val})
        elif t in ('p','li'):
            if val: content.append({'type':t,'text':val})

json.dump(content, open(os.path.join(DIR,"_content.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(imgs, open(os.path.join(DIR,"_imgs.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
from collections import Counter
print(DIR)
print("content:", dict(Counter(x['type'] for x in content)), "| img总数:", len(imgs))
