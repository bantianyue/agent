# -*- coding: utf-8 -*-
"""构建 Akshay X Article 中文版（80%内容保留+代码块+封面，正文图占位说明）"""
import json, os, re
base=r"D:/06_Hermes/articles/x-akshay-fwa"
d=json.load(open(r"D:/06_Hermes/articles/x_fast.json",encoding="utf-8"))
c=d['tweet']['article']['content']
em={str(e['key']): {'type':e['value']['type'],'data':e['value']['data']} for e in c['entityMap']}
blocks=c['blocks']
all_zh=json.load(open(base+"/_all_zh.json",encoding="utf-8"))
meta=json.load(open(base+"/_meta.json",encoding="utf-8"))

OUT=[]
def add(s): OUT.append(s)
def para(t): add(f'<p style="font-size:15px;line-height:1.95;color:#333;margin:11px 0;text-align:justify;">{t}</p>')
def li(t,ordered=False):
    tag='ol' if ordered else 'ul'
    return t
# 需要按块顺序渲染，包含列表容器。用流式累计。

# 结构化: 每个块生成 DOM 片段，列表连续则包<li>
h=[]
def h1(t): h.append(f'<h1 style="font-weight:bold;font-size:25px;color:#111;margin:14px 0 6px;line-height:1.4;">{t}</h1>')
def sub(t): h.append(f'<p style="background:#f0f7ff;border-left:4px solid #0a7d91;border-radius:4px;padding:10px 12px;margin:12px 0;font-size:14px;color:#0b3d6e;font-weight:bold;">{t}</p>')

# 主标题
h1(meta['title'])
add(f'<div style="margin:0 0 10px;font-size:14px;color:#888;">by <strong>{meta["author"]}</strong> {meta["handle"]} · 原文为英文，本文为全中文编译（内容保留≥80%）<br>👍 {meta["likes"]} · 🔁 {meta["retweets"]} · 👀 {meta["views"]}</div>')
# 封面
add(f'<img src="imgs/cover.png" style="max-width:100%;margin:6px 0;border-radius:6px;"/>')

def code_block(md):
    # markdown 含 ```lang ... ``` 提取
    m=re.search(r'```(\w*)\s*\n(.*?)\n```', md, re.S)
    lang=m.group(1) if m else ''
    code=m.group(2) if m else md
    es=code.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return f'<pre style="background:#0d1117;color:#c9d1d9;border-radius:6px;padding:14px 16px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;line-height:1.6;margin:12px 0;"><code>{es}</code></pre>'

ti=0
for bi,b in enumerate(blocks):
    ty=b['type']
    if ty=='atomic':
        er=b.get('entityRanges',[])
        if er:
            k=str(er[0].get('key'))
            e=em.get(k)
            if e:
                if e['type']=='MARKDOWN':
                    add(code_block(e['data'].get('markdown','')))
                elif e['type']=='MEDIA':
                    # 图下载不到，放占位说明（原文配图）
                    add(f'<div style="background:#fff8e6;border:1px dashed #e0c060;border-radius:6px;padding:12px;margin:12px 0;font-size:13px;color:#8a6d1d;text-align:center;">📷 此处为原文图示（X 登录后补图）——原图：图表 / 示意</div>')
        continue
    # 文本块：用文本序号 ti 取翻译
    text=b.get('text','').strip()
    zh=all_zh.get(str(ti), text)
    ti+=1
    # 跳过空（cover 前的 description 之类已处理）
    if ty in ('unstyled',):
        if text=='': continue
        para(zh)
    elif ty=='header-one':
        h1(zh)
    elif ty in ('unordered-list-item','ordered-list-item'):
        bullet='·' if ty=='unordered-list-item' else '◆'
        add(f'<p style="font-size:15px;line-height:1.85;color:#333;margin:4px 0 4px 18px;text-align:left;">{bullet} {zh}</p>')
    elif ty=='blockquote':
        add(f'<div style="background:#f7f7f7;border-left:4px solid #ccc;border-radius:4px;padding:10px 12px;margin:10px 0 10px 10px;font-size:14px;color:#555;">{zh}</div>')

# 结尾
add('<p style="font-size:15px;line-height:1.95;color:#333;margin:12px 0;text-align:justify;">🙏 感谢阅读。敬请期待更多内容！</p>')
add('<div style="margin-top:26px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;line-height:1.7;">'
    '<strong>📌 来源</strong><br>X 长文《Static vs. Dynamic vs. Continuous Batching in LLMs, clearly explained》<br>'
    '作者：Akshay 🚀（@akshay_pachaar）· 本文为全中文编译（内容保留≥80%）<br>'
    '原帖：https://x.com/akshay_pachaar/status/2094490705024676272</div>')
add('</section>')
html=''.join(OUT)
open(base+"/article_zh.html","w",encoding="utf-8").write(html)
zh=len(re.findall(r'[\u4e00-\u9fff]',html))
en=len(re.findall(r'[A-Za-z]{3,}', re.sub(r'<[^>]+>',' ',html)))
print(f"✅ len:{len(html)} 中文:{zh} 英文词(技术/代码):{en}")
print("代码块:", html.count('<pre'), "| 图占位:", html.count('此处为原文图示'), "| 封面:", html.count('cover.png'))