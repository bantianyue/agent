# -*- coding: utf-8 -*-
"""重新提取 9 段代码（get_text() 无 separator）+ 写回干净 file 供校验"""
import re, json, os
from bs4 import BeautifulSoup
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
h=open(base+"/source.html",encoding="utf-8",errors="ignore").read()
pres=re.findall(r'<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>',h,re.S)
os.makedirs(base+"/codes_ext",exist_ok=True)
ok=[]
for idx,raw in enumerate(pres):
    txt=BeautifulSoup(raw,'html.parser').get_text()
    # 去掉首尾多余空行
    while txt and txt[0] in '\r\n': txt=txt[1:]
    while txt and txt[-1] in '\r\n': txt=txt[:-1]
    ok.append(txt)
    open(base+f"/codes_ext/code{idx+1}.tm.txt","w",encoding="utf-8").write(txt)
    open(base+f"/codes_ext/code{idx+1}.raw.txt","w",encoding="utf-8").write(BeautifulSoup(raw,'html.parser').get_text('\n'))
print("正确提取",len(ok),"段")
for i,t in enumerate(ok,1):
    print(f"\n--- code{i} ---")
    print(t[:240])
