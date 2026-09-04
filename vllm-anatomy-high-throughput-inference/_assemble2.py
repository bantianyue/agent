# -*- coding: utf-8 -*-
"""vLLM 博客全保留 → article_data.json（确定性组装）"""
import json, os
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
bl=json.load(open(base+"/_blocks.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8")); tr={int(k):v for k,v in tr.items()}
dlm=json.load(open(base+"/_dl_map.json",encoding="utf-8"))
# DOM 图顺序 list
out=[]
for b in bl:
    if isinstance(b,dict) and 'FIG' in b: out.append(b['FIG'])
order=[]
for s in out:
    if s not in order: order.append(s)
figfile={s:f"fig{i:02d}.png" for i,s in enumerate(order,1)}

def txtx(b):
    for k in ('T','LI','Q'):
        if k in b: return k, b[k]
    return None,None

sections=[]           # final
cur=None              # working section
def close():
    global cur
    if cur is not None and cur['paras']: 
        sections.append(cur); 
    cur=None
def newc(title,lv):
    global cur
    close(); cur={"type":"h2" if lv<=2 else "h3","title":title,"paras":[]}
    return cur

# 若某 fig 接着插：cur 记录每 fig 用的位置 key(段落后)= paras 索引。
# encoding paras 与 fig: 我们用 fig_after 记 段后,累积构造
# 组装单前端遍历
PRE_HEAD=""
pre=[]
first=True
for i,b in enumerate(bl):
    lvl = b.get('lvl') if isinstance(b,dict) else None
    if lvl:
        title=tr.get(i,b.get('T',''))
        newc(title,lvl)
        first=False
        continue
    if 'FIG' in b:
        if cur is None:  # fig 在第一个标题前(不应); fallback
            newc("图",2)
        fa=cur.setdefault('fig_after',{})
        key=str(len(cur['paras']))
        fa.setdefault(key,[]).append({"src":figfile[b['FIG']],"caption":"图"})
        continue
    if 'C' in b:
        if cur is None: continue
        cur['paras'].append("__CODE__"+((b.get('lang','')+"::") if b.get('lang') else "")+b['C'].rstrip('\n'))
        continue
    if 'TBL' in b:
        if cur is None: continue
        head=b['TBL'][0]; rows=b['TBL'][1:]
        # 保留英文原cell(指标缩写) + 手动汉化说明?
        # 直接一个 section? cell内容需要人工汉化,先放原表
        cur['table']={"head":head,"rows":rows}
        continue
    if 'T' in b or 'LI' in b or 'Q' in b:
        kind,txt=txtx(b)
        if not txt: continue
        # 跳过 References 长 URL 段?保留至文末单独 append 也可. 保留所有
        t = tr.get(i)
        if t is not None: out_t=t
        else: out_t=txt
        if out_t:
            if cur is None:
                cur=newc("",2)  # 首个heading前块归"开篇"汇到 sections[0]
            if kind=='LI':
                out_t=("· "+out_t) if lvl is None else out_t
            cur['paras'].append(out_t)
# close tail
close()
print("sections:",len(sections),"paras总和:",sum(len(s.get('paras',[])) for s in sections),
      "fig_after:", sum(len(s.get('fig_after',{})) for s in sections),"表:",sum('table' in s for s in sections))
# 存中间结构便于检视
json.dump(sections,open(base+"/_sec_ready.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
# 标题纯净检查(第一个可能空title 若有)
for s in sections:
    if not s['title']: print(" 空title节 paras首部:",str(s['paras'][0])[:40])
