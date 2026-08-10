#!/usr/bin/env python3
"""临时：解析 arXiv 论文 → _content.json（正文主节，公式↔LaTeX）"""
import re, json
from html.parser import HTMLParser

DIR = r"D:/06_Hermes/articles/cross-model-kv-cache-transfer"
raw = open(DIR + "/page.html", encoding="utf-8", errors="replace").read()

art = raw.find('<article')
ref = raw.find('References', 200000)
# 更精确：找 References h2 位置
refm = re.search(r'<h2[^>]*>\s*<span[^>]*>\s*References\s*</span>\s*</h2>', raw)
ref = refm.start() if refm else (raw.find('class="ltx_bibliography"', art))
if ref < 0: ref = len(raw)
seg = raw[art:ref]

# 公式: <math alttext="X">...</math> → ⟦X⟧
INLINE_MATH = r'\\(%s\\)'
def math_repl(m):
    return f'\\({m.group(1)}\\)'
seg = re.sub(r'<math[^>]*alttext="([^"]*)"[^>]*>.*?</math>', math_repl, seg, flags=re.S)

# 提取摘要（Abstract）
abm = re.search(r'<section[^>]*class="ltx_abstract"[^>]*>(.*?)</section>', seg, re.S) or \
      re.search(r'<section[^>]*id="abstract"[^>]*>(.*?)</section>', seg, re.S)
abstract = ''
if abm:
    abtxt = re.sub(r'<[^>]+>', ' ', abm.group(1))
    abstract = re.sub(r'\s+', ' ', abtxt).replace('Abstract ', '').strip()

# 提取结构：h2/h3 分节，p 段落，figure 图注
content = []  # {type:h2/h3/p/fig, text}
i = 0
# 收集所有 (start, tag, tagdata) 
events = []
for m in re.finditer(r'<(h2|h3|p|figure)\b[^>]*?(/?)>', seg):
    events.append((m.start(), m.group(1), m.group(2)=='/', seg[m.end():]))
events.sort()

# 用栈式遍历分段补充（简化：顺序扫描主要标签）
# 这里简单方案：找 h2/h3 边界，段落用 <p>
pos = 0
sections = []  # (type, title/text, items[])
cur = None
items = []
def flush():
    global cur, items
    if cur is not None and (items or cur[0] in ('h2','h3')):
        sections.append((cur, items))
    items=[]
para_iter = re.finditer(r'<p[^>]*>(.*?)</p>', seg, re.S)
heading_iter = list(re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', seg, re.S))
fig_iter = list(re.finditer(r'<figcaption[^>]*>(.*?)</figcaption>', seg, re.S))

all_marks = sorted([(m.start(),'h',m.end(),m) for m in heading_iter] +
                   [(m.start(),'p',0,m) for m in para_iter] +
                   [(m.start(),'f',0,m) for m in fig_iter])
# 按顺序组装
stack=[]
for start,kind,end,m in all_marks:
    pass  # this approach too complex; use sequential

# 简化顺序法：直接按 parse 顺序输出
out=[]
def push_text(txt, t2):
    txt=re.sub(r'\s+',' ',txt).strip()
    if t2=='p' and txt: out.append({'type':'p','text':txt})
    elif txt: out.append({'type':t2,'text':txt})

# 重新用 HTMLParser 精确处理，顺序敏感
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.cur=None; self.buf=[]; self.result=[]; self.skip=0
        self.stack=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='h2':
            self._flush(); self.cur='h2'; self.buf=[]
        elif tag=='h3':
            self._flush(); self.cur='h3'; self.buf=[]
        elif tag=='p':
            self._flush(); self.cur='p'; self.buf=[]
        elif tag=='figcaption':
            self._flush(); self.cur='fig'; self.buf=[]
        elif tag in ('math','script','style'):
            self.skip+=1
    def handle_data(self, data):
        if self.cur and self.skip==0:
            self.buf.append(data)
    def handle_endtag(self, tag):
        if tag in ('h2','h3','p','figcaption'):
            if self.cur==tag:
                txt=''.join(self.buf)
                txt=re.sub(r'\s+',' ',txt).strip()
                if txt: self.result.append({'type':tag,'text':txt})
                self.cur=None; self.buf=[]
        elif tag in ('math','script','style'):
            self.skip=max(0,self.skip-1)
    def _flush(self):
        if self.cur:
            txt=''.join(self.buf); txt=re.sub(r'\s+',' ',txt).strip()
            if txt: self.result.append({'type':self.cur,'text':txt})
            self.cur=None; self.buf=[]

p=P()
p.feed(seg)

result = []
if abstract:
    result.append({'type':'abstract','text':abstract})
result.extend(p.result)

json.dump(result, open(DIR+"/_content.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
from collections import Counter
print("abstract:", len(abstract))
print("content:", dict(Counter(x['type'] for x in result)))
print("\n结构预览(前30):")
for x in result[:30]:
    print(f"  [{x['type']}] {x['text'][:60]}")
