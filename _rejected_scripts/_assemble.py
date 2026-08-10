#!/usr/bin/env python3
"""组装 minimax-m3-inference -> build。"""
import json, re, os

DIR = r"D:/06_Hermes/articles/minimax-m3-inference"
content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
bidmap = json.load(open(os.path.join(DIR, "_bidmap.json")))
trans = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))
def tr(i):
    bid = bidmap.get(str(i))
    return trans.get(str(bid), '') if bid is not None else ''
def is_cn(s): return len(re.findall(r'[\u4e00-\u9fff]', s)) > 0

# 去重标题+目录 heading 文本 + lead 显式收集
LEAD_IDX=set([3,4,5,6,7,8,9,10])
SKIP=set([0,1,2])
lead = []
for i in sorted(LEAD_IDX):
    if i < len(content) and content[i]['type']=='p':
        t=tr(i).strip().rstrip('#').strip()
        if t and not t.startswith('#'): lead.append(t)

# sections
sections=[]; cur=None; paras=[]; fig_list=[]
def flush():
    global cur,paras,fig_list
    if cur is None: return
    if paras or fig_list:
        fa={}
        for pi,ff in fig_list: fa.setdefault(str(pi),[]).extend(ff)
        s={'type':'h2','title':cur,'paras':paras}
        if fa: s['fig_after']=fa
        sections.append(s)
    paras=[]; fig_list=[]; cur=None

CODE='style="background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,\'Courier New\',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;"'
for i,x in enumerate(content):
    if i in SKIP or i in LEAD_IDX: continue
    t=x['type']
    if t=='h2':
        flush(); cur=tr(i).strip().rstrip('#').strip()
    elif t=='p':
        txt=tr(i).strip().rstrip('#').strip()
        if txt and not txt.startswith('#'):
            paras.append(txt)
    elif t=='code':
        raw=x['text'].strip()
        paras.append(f'<pre {CODE}><code>{raw}</code></pre>')
    elif t in ('li','h3','h4'):
        txt=tr(i).strip()
        if txt: paras.append(txt)
flush()

# 挂图：4张性能图到"性能预览"节末尾
for si,s in enumerate(sections):
    if '性能预览' in s['title']:
        n=len(s['paras'])
        s['fig_after']={f"{n-1}":[
            {"src":"fig07.png","caption":""},
            {"src":"fig06.png","caption":""},
            {"src":"fig08.png","caption":""},
        ]}
        break

json.dump({"lead":lead,"sections":sections}, open(os.path.join(DIR,"_sections_preview.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("lead:", len(lead))
print("sections:", len(sections))
print("total paras:", sum(len(s['paras']) for s in sections))
allf={f["src"] for s in sections for v in s.get("fig_after",{}).values() for f in v}
print("figs in sections:", sorted(allf), "| disk:", sorted(f for f in os.listdir(DIR) if f.startswith('fig')))
for s in sections: print(f"  [{s['title'][:20]}] {len(s['paras'])}段")
