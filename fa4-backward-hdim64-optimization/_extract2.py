#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 DOM 顺序提取 WP 正文结构块 -> blocks.jsonl。
只在自己造的『正文起点』(首个 <h1 class="...title-ish"> 或第一个引言 h2 前的段落) 后收集。
对 <table>/<pre>/<img> 做 hoist 成单独块, 其它块从 p/h1-h3 取文本。"""
import re, json
from html.parser import HTMLParser

SRC = r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/_body.html"
OUT = r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/blocks.jsonl"
h = open(SRC, encoding="utf-8", errors="ignore").read()

START_MARK = "Optimization diaries"   # 正文 h1 首词, 遇到它开始收集
SKIP_MARKERS = ("share this","like this","discover more from colfax",
                "subscribe to get the latest","type your email","posted",
                "in","comments","leave a reply","your email address will not",
                "cancel reply","comment *","name ","email ","website ","save my name",
                "copyright © 2023","all rights reserved","back to top",
                "category","tags:","previous post","next post")

class Walker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.on = False
        self.cur = None        # str-buffer block being accumulated: {'type','txt','buf'}
        self.cur_kind = None
        self.hr = 0            # self.closed depth; use stack counters
        self.code_buf = []     # hoisted specials
        self.in_pre = False
        self.in_table = False
        self.stack = []        # list of tagnames currently open
        self.tbl = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); tag=tag.lower()
        cls = a.get('class','')
        self.stack.append(tag)
        if not self.on:
            return
        if tag=='img':
            src=a.get('src','') or a.get('data-src','') or ''
            if 'colfax-logo' in src: return
            alt=a.get('alt','')
            self.blocks.append({'type':'img','src':src,'alt':alt})
        elif tag=='pre':
            self.in_pre=True; self.code_buf=[]
        elif tag=='table':
            self.in_table=True; self.tbl=[]
        elif tag=='tr' and self.in_table:
            self.tbl.append([])
        elif tag in ('td','th') and self.in_table:
            pass
        if self.cur_kind is None and tag in ('p','h1','h2','h3','h4') and not self.in_table:
            self.cur_kind=tag; self.cur=''

    def handle_data(self, data):
        if not self.on: 
            return
        if self.in_pre:
            self.code_buf.append(data); return
        if self.in_table:
            if self.tbl is not None:
                pass
            return
        if self.cur_kind in ('p','h1','h2','h3','h4'):
            self.cur += data

    def handle_startendtag(self,tag,attrs):
        if tag=='img':
            self.handle_starttag('img',attrs)

    def handle_endtag(self, tag):
        tag=tag.lower()
        # trim stack
        try:
            while self.stack and self.stack[-1]!=tag: self.stack.pop()
            if self.stack and self.stack[-1]==tag: self.stack.pop()
        except: pass
        if tag=='pre' and self.in_pre:
            # finalize code
            txt=''.join(self.code_buf)
            txt=txt.replace('&#038;','&').replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&#39;',"'").replace('&nbsp;',' ')
            # unescape html entities minimal
            import html as _h
            txt=_h.unescape(txt)
            self.blocks.append({'type':'code','text':txt})
            self.in_pre=False; self.code_buf=[]; self.cur_kind=None; self.cur=''
            return
        if tag=='table' and self.in_table:
            # we already filled via td closes; but handled via cells
            self.in_table=False; self.tbl=None
            return
        if self.cur_kind==tag and tag in ('p','h1','h2','h3','h4'):
            # unescape
            import html as _h
            raw=_h.unescape(self.cur)
            txt=re.sub(r'\s+',' ',raw).strip()
            self.cur_kind=None; self.cur=''
            if not self.on: pass
            elif tag=='h1':
                self.blocks.append({'type':'h1','text':txt})
            elif txt:
                low=txt.lower()
                if any(m in low for m in SKIP_MARKERS): pass
                else:
                    self.blocks.append({'type':('caption' if tag=='p' and re.match(r'^figure\s*\d',txt,re.I) else ('h2' if tag=='h2' else ('h3' if tag=='h3' else ('h4' if tag=='h4' else 'p'))),'text':txt})
        if not self.on and self.stack==['html']:
            pass

# --- 表格单元格收集: td 之间塞 cell, 在 td 结束时通过 stack 检测? 简化: 在 handle_endtag 中做
#    我们另用 after-feed 的二次正则从原文抠 3 个 table(WordPress 表格 HTML 规整, Caption/头部好解析)
print("walker 分块完成于下方")
w=Walker()
w.feed(h)
