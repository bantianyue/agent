#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json, html as _h
h=open(r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/raw.html",encoding='utf-8',errors='ignore').read()
body=h  # 全文喂 pre 提取 (pre 只在正文/评论, 已是代码)

# 1) 提取所有 <pre> 块 (带 unescape) 及其紧前一段可定位文本
pres=re.finditer(r'(?s)<pre[^>]*>(.*?)</pre>', body)
codes=[]
for m in pres:
    raw=m.group(1)
    raw=_h.unescape(re.sub(r'<[^>]+>','',raw))
    codes.append(raw)
print("=== pre代码块数:",len(codes))
for i,c in enumerate(codes,1):
    open(f"_code{i}.txt","w",encoding="utf-8").write(c)
    print(f"----- code{i} ({len(c)} chars) -----")
    print(c)

# 2) 提取每个正文图 的 原始上传URL (去 resize/ssl query)
print("\n=== 正文图原始URL(去query)===")
imgs=re.finditer(r'<img[^>]*src="(https://i0\.wp\.com/[^"]+)"',body)
seen=set()
for m in imgs:
    u=m.group(1)
    if 'colfax-logo' in u or u in seen: continue
    seen.add(u)
    # 原始: i0.wp.com/.../uploads/YYYY/MM/file.png?resize=..&ssl=1 -> strip query
    base=u.split('?')[0]
    if base not in seen:
        print(base)
        seen.add(base)
open(r"D:/06_Hermes/articles/fa4-backward-hdim64-optimization/_pre_checked.txt","w",encoding="utf-8").write("\n".join(f"CODE{i}\n{''.join(c for c in codes[:i])}" for i in range(len(codes))))
print("done")
