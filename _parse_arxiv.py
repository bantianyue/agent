#!/usr/bin/env python3
"""解析 arXiv 论文正文主节(Abstract+主节, 跳过附录) -> _content.json"""
import re, json, sys, os
from html.parser import HTMLParser

DIR=sys.argv[1]
raw=open(os.path.join(DIR,"page.html"),encoding="utf-8",errors="replace").read()

# 主文到 References 前
art=raw.find('<article')
refm=re.search(r'<h2[^>]*>\s*<span[^>]*>\s*References\s*</span>',raw)
ref=refm.start() if refm else raw.find('class="ltx_bibliography"',art)
if ref<0: ref=len(raw)
seg=raw[art:ref]

# 公式 -> LaTeX
seg=re.sub(r'<math[^>]*alttext="([^"]*)"[^>]*>.*?</math>', r'\\(\1\\)', seg, flags=re.S)

# 提取结构
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.cur=None; self.buf=[]; self.result=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('h1','h2'):
            self._flush(); self.cur=tag; self.buf=[]
        elif tag=='p':
            self._flush(); self.cur='p'; self.buf=[]
        elif tag in ('li',):
            self._flush(); self.cur='li'; self.buf=[]
        elif tag=='figcaption':
            self._flush(); self.cur='fig'; self.buf=[]
        elif tag in ('math','script','style'):
            self.skip+=1
    def handle_data(self,data):
        if self.cur and self.skip==0: self.buf.append(data)
    def handle_endtag(self,tag):
        if tag in ('h1','h2','p','li','figcaption'):
            if self.cur==tag:
                txt=''.join(self.buf); txt=re.sub(r'\s+',' ',txt).strip()
                if txt: self.result.append({'type':('h2' if tag in('h1','h2') else tag),'text':txt})
                self.cur=None; self.buf=[]
        elif tag in ('math','script','style'): self.skip=max(0,self.skip-1)
    def _flush(self):
        if self.cur:
            txt=''.join(self.buf); txt=re.sub(r'\s+',' ',txt).strip()
            if txt: self.result.append({'type':('h2' if self.cur in('h1','h2') else self.cur),'text':txt})
            self.cur=None; self.buf=[]
p=P(); p.feed(seg)

# 提取摘要
abm=re.search(r'<section[^>]*class="ltx_abstract"[^>]*>(.*?)</section>',raw,re.S)
abstract=''
if abm:
    t=re.sub(r'<math[^>]*alttext="([^"]*)"[^>]*>.*?</math>',r'\1',abm.group(1),flags=re.S)
    t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t).replace('Abstract ','').strip()
    abstract=t

json.dump({"abstract":abstract,"blocks":p.result}, open(os.path.join(DIR,"_content.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
from collections import Counter
print("abstract len:", len(abstract))
print("blocks:", dict(Counter(x['type'] for x in p.result)))
