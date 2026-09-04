# -*- coding: utf-8 -*-
"""vLLM全保留文章数据组装器 -> 产出 article_data.json (DATA 字典)"""
import json, os, re
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
bl=json.load(open(base+"/_blocks.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8"))
tr={int(k):v for k,v in tr.items()}
dlm=json.load(open(base+"/_dl_map.json",encoding="utf-8"))
order=[]
for b in bl:
    if 'FIG' in b and b['FIG'] in dlm: order.append(b['FIG'])
seen=set();o=[]
for s in order:
    if s not in seen: seen.add(s);o.append(s)
order=o
figfile={s:f"fig{i:02d}.png" for i,s in enumerate(order,1)}
figcap={s:"图 %d"%i for i,s in enumerate(order,1)}   # placeholder; 稍后人工

sections=[]           # list of dict
sec_paras=[]          # working paras for current section
sec_figslots={}       # section_idx -> {para_index: [chunks]} ; 但 fig在 paras 前后插
# 直接构造: paras + 一组 (pos,url) 到 section级记录，渲染阶段合并
cur={}
open_head=False

# 辅助收集节段落数组：
# 把 blocks转成流：遇h2新节；h1也为h2节标题
last_h=None

def push_para(x):
    cur['paras'].append(x)

# 便于 fig_after: 每条fig记 para_idx_after (数组里已push元素数为index呢: 图插在"N段之后"，fig_after key=它前段落的index)
sections=[]
active=None

# 第一个 h2 前的内容 -> 开篇 section
def new_sec(title,level=2):
    return {"type":"h2" if level<=2 else "h3","title":title,"paras":[]}

idx=0
# 找第一个 head idx
secs=[]
# 先清空? 简化方案：手动按原文 H2 划节(17节) :其中有些 content intro在 h2前已收集为section0。
# 定义 h2 中文标题用 tr 的译
cur_sec=None
pending_buf=[]
res=[]

# 一键: 拆分平坦 seq
seq=[]
for b in bl:
    if 'lvl' in b:
        seq.append(("H",b['lvl'],tr.get(b.index_ ,b['T'])))  # 占位有误
    else: seq.append(("X",b))
