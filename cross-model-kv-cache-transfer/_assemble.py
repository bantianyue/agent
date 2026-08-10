#!/usr/bin/env python3
"""临时：组装 arXiv 论文 sections。"""
import json, re, os, html as H

DIR = r"D:/06_Hermes/articles/cross-model-kv-cache-transfer"
c = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
t = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))
def tr(i): return t.get(str(i),'').strip()

# lead：content[0]=摘要 + content[2-3]=引言背景
lead = [tr(0)]
for i in [2,3]:
    if tr(i): lead.append(tr(i))

# sections：从 h2 "1 Introduction" 开始
sections=[]; cur=None; paras=[]; fig_list=[]
def flush():
    global cur,paras,fig_list
    if cur is None: return
    if paras or fig_list:
        fa={}
        for pi,figs in fig_list: fa.setdefault(str(pi),[]).extend(figs)
        s={'type':'h2','title':cur,'paras':paras}
        if fa: s['fig_after']=fa
        sections.append(s)
    paras=[]; fig_list=[]; cur=None

for i,x in enumerate(c):
    if i==0: continue  # 摘要已入 lead
    tp=x['type']
    if tp=='h2':
        flush(); cur=tr(i)
    elif tp=='h3':
        # h3 子节标题作为段落（加粗前缀）
        h=tr(i)
        if h: paras.append(f"<strong>{h}</strong>")
    elif tp=='p':
        txt=tr(i)
        if txt: paras.append(txt)
    elif tp=='fig':
        file_ = x.get('file')
        if file_:
            # 有图 → 挂图
            pi=max(0,len(paras)-1) if paras else 0
            cap = tr(i)
            fig_list.append((pi,[{"src":file_,"caption":cap}]))
        else:
            # Table 标题 → 段落文本
            txt=tr(i)
            if txt: paras.append(f"■ {txt}")
flush()

json.dump({"lead":lead,"sections":sections}, open(os.path.join(DIR,"_sections_preview.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("lead:", len(lead), "段")
print("sections:", len(sections))
print("total paras:", sum(len(s['paras']) for s in sections))
allfigs={f["src"] for s in sections for v in s.get("fig_after",{}).values() for f in v}
disk=set(f for f in os.listdir(DIR) if f.startswith('fig'))
print("figs:", sorted(allfigs), "| match:", allfigs==disk)
# 越界
ok=True
for si,s in enumerate(sections):
    n=len(s.get('paras',[]))
    for k in s.get('fig_after',{}):
        if int(k)>=n: print(f"!! 越界 sec{si}"); ok=False
print("bounds:", "OK" if ok else "VIOLATION")
for s in sections:
    print(f"  [{s['title'][:25]}] {len(s['paras'])}段 figs={sum(len(v) for v in s.get('fig_after',{}).values())}")
