#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 DOM 顺序提取 WP 正文结构块: 标题/p段落/表格/图(+图注)/pre代码。
输出 blocks.jsonl(json 每行一块), 全局保持源文顺序。"""
import re, json, sys
from html.parser import HTMLParser

SRC = r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/_body.html"
OUT = r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/blocks.jsonl"

h = open(SRC, encoding="utf-8", errors="ignore").read()

# 定位正文容器 entry-content
m = re.search(r'<div[^>]*class="[^"]*(?:entry-content|post-content|td-content)[^"]*"[^>]*>(.*)</div>\s*</article>|(?s)<article[^>]*>(.*)</article>', h)
if m:
    body = m.group(1) or m.group(2)
else:
    body = h
# 清理前面的 header/logo 区: 正文真正的 h1 = "Optimization diaries:..."
body = re.sub(r'<figure[^>]*class="[^"]*(?:wp-block-|align)[^"]*".*?</figure>', '', body, flags=re.S)  # not reliable

# ---- HTMLParser (DOM 序, 自带深度判断) ----
class Walker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []          # all structural blocks in order
        self.cur = None           # block being built
        self.depth = 0
        self.skip_depth = None    # inside something we hoist
        self.text_buf = []
        # html -> parent chain for depth of headings under figure/caption etc
        self.tagstack = []

    def _cur(self): return self.cur

    def handle_starttag(self, tag, attrs):
        self.tagstack.append(tag)
        a = dict(attrs)
        cls = a.get('class','')
        tagl = tag.lower()
        # hoist table & pre & img at any depth into explicit blocks
        if tagl == 'img' and self.skip_depth is None:
            src = a.get('src','') or a.get('data-src','')
            # skip the colfax logo (footer header)
            if 'colfax-logo' in src:
                return
            # full-size source: drop ?resize & ssl query later during download
            alt = a.get('alt','')
            # push inline figure-ish
            self.blocks.append({'type':'img','src':src,'alt':alt,'w':a.get('width'),'caption':''})
        elif tagl == 'pre' and self.skip_depth is None:
            if self.cur: self._end_cur()
            self.cur = {'type':'code','html':[]}; self.skip_depth = self.depth
            self.text_buf=[]
        elif tagl in ('h1','h2','h3','h4') and self.skip_depth is None:
            if self.cur: self._end_cur()
            self.cur = {'type':'h'+tagl[1],'text':''}; self.text_buf=[]
        elif tagl == 'p' and self.skip_depth is None:
            if self.cur: self._end_cur()
            self.cur = {'type':'p','text':''}; self.text_buf=[]
        elif tagl == 'table' and self.skip_depth is None:
            if self.cur: self._end_cur()
            self.cur = {'type':'table','rows':[],'currow':[],'in_td':False,'buf':[]}
            self.skip_depth = self.depth
        elif tagl in ('li',) and self.skip_depth is None and (self.cur and self.cur['type'] not in ('table',)):
            pass
        # else: pass through into text_buf accumulation only if we have a simple block
        self.depth += 1
        # 捕获 code 内含文字: handled by handle_data via cur

    def handle_endtag(self, tag):
        self.depth -= 1
        tagl = tag.lower()
        if self.skip_depth is not None:
            if self.cur and self.cur['type']=='code' and tagl=='pre':
                txt=''.join(self.text_buf)
                self.cur['code']=txt
                self.blocks.append(self.cur); self.cur=None; self.skip_depth=None; self.text_buf=[]
            elif self.cur and self.cur['type']=='table':
                if tagl=='table':
                    self.blocks.append(self.cur); self.cur=None; self.skip_depth=None
                elif tagl=='tr':
                    self.cur['rows'].append(self.cur['currow']); self.cur['currow']=[]
                elif tagl=='td' or tagl=='th':
                    cell=''.join(self.cur['buf']).strip()
                    self.cur['currow'].append(cell); self.cur['buf']=[]
            else:
                # nested inside skip block but closing at created depth -> finalize simple text blk
                if self.cur and self.cur.get('type') in ('p','h2','h3'):
                    if self.depth<= self._start_depth:
                        pass
            return
        if self.cur and tagl in ('p','h1','h2','h3','h4') and self.cur.get('type')==(('h'+tagl[1]) if tagl in('h1','h2','h3','h4') else 'p'):
            self._finalize_text()

        if self.tagstack: self.tagstack.pop()
    def _start_depth(self): return getattr(self,'sd',1)
    def handle_data(self, data):
        if self.skip_depth is not None:
            if self.cur and self.cur['type']=='code':
                self.text_buf.append(data)
            elif self.cur and self.cur['type']=='table':
                self.cur['buf'].append(data)
            return
        if self.cur and self.cur.get('type') in ('p','h2','h3') :
            self.cur['text'] += data

    def _finalize_text(self):
        t=self.cur
        if t and t.get('text',t.get('type','')).strip():
            st=t.get('text','').strip() if t.get('type')=='p' else t.get('text','').strip()
            t['text']=st
            self.blocks.append(t)
        self.cur=None
    def _end_cur(self): self._finalize_text()

w=Walker()
w.feed(body)

# 过滤: 合并连续空 / 丢弃极短纯文本噪音(如 'Share this:', 'Like this:', 'Discover more', 'Posted in', email订阅)
import unicodedata
keep=[]
skip_words=('share this','like this','discover more from','subscribe to get','type your email','leave a reply','your email address')
for b in w.blocks:
    if b['type']=='p':
        tx=re.sub(r'\s+',' ',b['text']).strip()
        if not tx or any(s in tx.lower() for s in skip_words) or len(tx)<3:
            continue
        b['text']=tx
    keep.append(b)

# caption 关联：WP 里 <figure> 内 img 后常跟 <figcaption>。简化——手动在后面段落里带 Figure 识别见检查。
for i,b in enumerate(keep):
    if b['type']=='p' and re.match(r'^Figure\s+\d+[\.:]', b['text'], re.I):
        b['type']='caption'
        # 绑到前一张 img
        for j in range(i-1,-1,-1):
            if keep[j]['type']=='img':
                b['after_img']=True
                break

with open(OUT,'w',encoding='utf-8') as f:
    for b in keep:
        f.write(json.dumps(b,ensure_ascii=False)+'\n')
print(f"blocks={len(keep)}")
from collections import Counter
print(Counter(b['type'] for b in keep))
for i,b in enumerate(keep):
    if b['type'] in ('h2','h3'):
        print(f"[{i}] {b['type']} {b['text'][:60]}")
