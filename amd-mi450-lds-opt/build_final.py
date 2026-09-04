# -*- coding: utf-8 -*-
"""从 art_step3.frag 一次生成干净 article.html（避免双 soup 污染）"""
import re, os, json
from bs4 import BeautifulSoup

base=r"D:/06_Hermes/articles/amd-mi450-lds-opt"
frag=open(f"{base}/art_step3.frag",encoding="utf-8").read()
soup=BeautifulSoup('<div id="ROOT">'+frag+'</div>','lxml')
root=soup.find('div',id='ROOT')
art=root.find('article') or root
img_map=json.load(open(f"{base}/_imgmap.json",encoding="utf-8"))
TOKEN={'c1':'#515151','cm':'#515151','c':'#515151','k':'#6730c5','kn':'#6730c5','kd':'#6730c5','ow':'#00622f','mi':'#7f4707','mf':'#7f4707','m':'#7f4707','il':'#7f4707','o':'#00622f','p':'#080808','n':'#080808','nn':'#080808','nx':'#080808','x':'#080808','nb':'#7f4707','s':'#00622f','s1':'#00622f','s2':'#00622f','nf':'#005b82','nd':'#005b82','fm':'#005b82','kt':'#6730c5','vi':'#005b82','err':'#a40000'}

# 1) 代码高亮 + token 颜色
for h in art.find_all('div',class_=re.compile(r'highlight')):
    h['style']="background:#f3f4f5;border-radius:4px;overflow-x:auto;"
    pre=h.find('pre')
    if pre:
        pre['style']="padding:14px 16px;line-height:1.5;white-space:pre;overflow-x:auto;font-size:13px;font-family:Consolas,Monaco,'Courier New',monospace;"
    for sp in h.find_all('span'):
        for c in (sp.get('class') or []):
            if c in TOKEN and not sp.get('style'):
                sp['style']=f"color:{TOKEN[c]};"; break

# 2) 正文变量 code 带背景
for code in art.find_all('code'):
    if code.find_parent(class_=re.compile(r'highlight')): continue
    cls=code.get('class') or []
    if any(c in ('literal','docutils','pre') for c in cls):
        code['style']=code.get('style','')+";background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#222832;font-size:13px;font-family:Consolas,Monaco,monospace;"

# 3) 图片
for img in art.find_all('img'):
    src=img.get('src',''); fn=src.rsplit('/',1)[-1]
    target=None
    for k,v in img_map.items():
        if k.rsplit('/',1)[-1]==fn or k==src: target=v; break
    if not target and fn in img_map.values(): target=fn
    if target: img['src']=target
    img['style']="max-width:100%;height:auto;"

# 4) figure caption
for fig in art.find_all('figure'):
    cap=fig.find('figcaption')
    if cap: cap['style']="font-size:12px;color:#666;text-align:center;margin-top:6px;padding:0 10px;line-height:1.5;"

# 5) 表格
for tb in art.find_all('table'):
    tb['style']="border-collapse:collapse;width:100%;font-size:13px;margin:12px 0;"
    for td in tb.find_all(['td','th']):
        td['style']="border:1px solid #ddd;padding:6px 10px;text-align:left;"
    for th in tb.find_all('th'):
        th['style']=th.get('style','')+";background:#f3f4f5;font-weight:bold;"

# 6) 清理
for sel in ['a.headerlink','input','script','style','aside','nav','footer','.onlyprint']:
    for el in art.select(sel): el.decompose()

# 7) 链接 -> 文字
for link in art.find_all('a'):
    t=link.get_text().strip()
    if t:
        link.replace_with(BeautifulSoup(f"<span style='color:#0a7d91;'>{BeautifulSoup(t,'html.parser').get_text()}</span>",'lxml'))

# 8) 段落已带 style（step3 里没有，这里统一）—— 但 step3 段落原本无 style
for p in art.find_all('p'):
    if not p.get('style'):
        p['style']="font-size:15px;line-height:1.8;margin:12px 0;color:#222832;"
for h in art.find_all(['h1','h2','h3','h4']):
    lv=int(h.name[1]); sz={1:'26px',2:'21px',3:'17px',4:'15px'}[lv]
    h['style']=f"font-weight:bold;font-size:{sz};margin:22px 0 10px;color:#111;"
for ul in art.find_all(['ul','ol']):
    ul['style']="margin:10px 0 10px 22px;padding-left:16px;"
for li in art.find_all('li'):
    li['style']="font-size:15px;line-height:1.8;color:#222832;margin:4px 0;"
for sd in art.find_all(['strong','b']): sd['style']="font-weight:bold;color:#111;"

# 9) 参考区
ref=("""<section style="margin-top:30px;padding:16px;background:#f5f0eb;border-radius:8px;font-size:13px;color:#555;line-height:1.8;">
<strong>📌 来源</strong><br>原文：A Deep Dive into LDS Optimizations on AMD Instinct MI450 GPUs（AMD ROCm Blogs）<br>作者：Ognjen Plavsic、Nicola Zaghen、Lixun Zhang<br>链接：https://rocm.blogs.amd.com/software-tools-optimization/mi450-lds-optimization/</section>""")
body=str(art)+ref
final=(f'<section style="font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">{body}</section>')
open(f"{base}/article.html","w",encoding="utf-8").write(final)
# 校验
import re as _re
def _cnt(p): return len(_re.findall(p,final))
print(f"N len={len(final)} h1={_cnt('<h1')} h2={_cnt('<h2')} h3={_cnt('<h3')} img={_cnt('<img')} pre={_cnt('<pre')} table={_cnt('<table')} figure={_cnt('<figure')}")
print("code变量bg:", final.count('#f3f4f5'))
print("html标签泄漏:", _cnt(r'<html'), _cnt(r'<body'), _cnt(r'<head'))
print("a标签泄漏:", _cnt(r'<a '))
print("参考区:", '来源' in final)
print("laTeX残留:", _cnt(r'\\\('), _cnt(r'\\frac'))
