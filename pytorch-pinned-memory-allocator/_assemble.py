#!/usr/bin/env python3
"""临时：组装 PyTorch pinned memory sections。"""
import json, os, html as H

DIR = r"D:/06_Hermes/articles/pytorch-pinned-memory-allocator"
c = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
t = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))

bid=0; tid={}
for i,x in enumerate(c):
    if x['type']=='h2' and x['text'].strip().lower()=='references':
        continue
    if x['type'] in ('p','h2','li'):
        tid[i]=bid; bid+=1
def tr(i):
    tidx=tid.get(i)
    return t.get(str(tidx),'') if tidx is not None else ''

CODE_STYLE='style="background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,\'Courier New\',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;"'
def code_block(raw):
    return f'<pre {CODE_STYLE}><code>{H.escape(raw)}</code></pre>'

# lead = 前 8 段 p (idx0-7)
lead = [tr(i) for i in range(8) if c[i]['type']=='p' and tr(i).strip()]

# sections
in_ref=False
sections=[]; cur=None; para_list=[]
def flush():
    global cur,para_list
    if cur is None: return
    if para_list:
        sections.append({'type':'h2','title':cur,'paras':para_list})
    para_list=[]; cur=None

for i,x in enumerate(c):
    if i < 8: continue  # lead 已处理
    tp=x['type']
    if tp=='h2':
        flush()
        if x['text'].strip().lower()=='references':
            cur="参考资料"
            in_ref=True
        else:
            cur=tr(i)
    elif tp=='p':
        tx=tr(i).strip()
        if tx: para_list.append(tx)
    elif tp=='code':
        para_list.append(code_block(x['text']))
    elif tp in ('li','ref'):
        if in_ref:
            para_list.append(f"• {x['text']}")  # 保留原文引用
        else:
            tx=tr(i).strip()
            if tx: para_list.append(f"• {tx}")
    elif tp=='img':
        pass
flush()

json.dump({"lead":lead,"sections":sections}, open(os.path.join(DIR,"_sections_preview.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("lead:", len(lead), "段")
print("sections:", len(sections))
print("total paras:", sum(len(s['paras']) for s in sections))
for s in sections:
    print(f"  [{s['title']}] {len(s['paras'])}段")
