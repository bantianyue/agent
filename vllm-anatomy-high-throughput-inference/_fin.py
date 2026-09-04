# -*- coding: utf-8 -*-
"""从 _blocks+_trans 组装 vLLM 全文 article_data.json（一次到位）"""
import json, os
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
bl=json.load(open(base+"/_blocks.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8")); tr={int(k):v for k,v in tr.items()}
figcap=json.load(open(base+"/_figcap.json",encoding="utf-8"))

# 图序号
uni=[]
for b in bl:
    if isinstance(b,dict) and 'FIG' in b and b['FIG'] not in uni: uni.append(b['FIG'])
figfile={s:f"fig{i+1:02d}.png" for i,s in enumerate(uni)}
capfn={uni[k]:figcap.get(f"fig{k+1:02d}.png","") for k in range(len(uni))}

def kind(b):
    if not isinstance(b,dict): return None
    if 'lvl' in b and 'T' in b: return 'lvl'   # heading 块(同时有T为标题文本)
    for k in ('T','LI','Q','C','FIG','TBL'):
        if k in b: return k
    return None

sections=[]
cur=None
def close():
    global cur
    if cur is not None and cur['paras']: sections.append(cur)
    cur=None
def open1(title,lv):
    global cur
    close(); cur={"type":"h2" if lv<=2 else "h3","title":title,"paras":[]}

# 分块出开篇处理
intro_paras=[]   # 首个h2之前块(0..block index of first lvl)
first_head_idx=None
for i,b in enumerate(bl):
    if kind(b)=='lvl':
        first_head_idx=i; break
# intro 块 0..first_head-1
for i in range(0,first_head_idx):
    b=bl[i]; k=kind(b)
    if k in ('T','LI','Q'):
        v=tr.get(i,b.get(k,''))
        if v: intro_paras.append(("· "+v) if k=='LI' else v)

# 主体：从 first_head_idx 逐 h2
mode=""
for i,b in enumerate(bl):
    if i<first_head_idx or kind(b) is None: continue
    k=kind(b)
    if k=='lvl':
        open1(tr.get(i,b.get('T')), b['lvl'])
    elif k=='C':
        lang=b.get('lang','')
        if cur is None: continue
        cur['paras'].append("__CODE__"+(lang+"::" if lang else "")+b['C'].rstrip('\n'))
    elif k=='FIG':
        s=b['FIG']; fn=figfile.get(s)
        cap=capfn.get(s,'')
        if cur is None: continue
        fa=cur.setdefault('fig_after',{})
        key=str(len(cur['paras']))
        fa.setdefault(key,[]).append({"src":fn,"caption":cap})
    elif k=='TBL':
        if cur is None: continue
        cur['table']={"head":b['TBL'][0],"rows":b['TBL'][1:]}
    elif k in ('T','LI','Q'):
        v=tr.get(i,b.get(k,''))
        if not v: continue
        if cur is None: continue
        cur['paras'].append(("· "+v) if k=='LI' else v)
close()

# ---------- 清理尾节：致谢/References 若能删留一个 ----------
# 去掉致谢(Acknowledgements)整节(与读者无关) & References(纯引用链接)
def drop_tail():
    return [s for s in sections if s['title'] not in ('致谢','参考文献')]
sections=drop_tail()

# 找出结语节 Epilogue 译文移到 conclusion
concl=[]
for i,s in enumerate(sections):
    if s['title']=='结语':
        concl=[p.lstrip('· ') for p in s['paras']]
        del sections[i]; break

# 表格中文处理: block list idx 297 的 TBL(行内已译? 原英) - 简单保留(表头加中文)已够: 用英文表保留但 transform cells? 为简单直接给译文(手工表)
# 在 sections 找 table section, 转其 cell (标题行英文残留): 我们给中文表头手动翻译
for s in sections:
    if 'table' in s:
        # 用映射
        h={"Metric":"指标","Definition":"定义"}
        s['table']['head']=["指标","定义"]
        rows=[]
        for r in s['table']['rows']:
            defm={
             "TTFT (time to first token)":"从请求提交到收到第一个输出token的耗时",
             "ITL (inter-token latency)":"相邻两个token之间的耗时(如token i-1 到 i)",
             "TPOT (time per output token)":"一次请求内全部输出token的平均ITL",
             "Latency / E2E (end-to-end latency)":"处理请求的总耗时，即 TTFT + 各 ITL 之和",
             "Throughput":"每秒处理的token数或请求数",
             "Goodput":"满足SLO(如TTFT/TPOT上限)的吞吐——只计达标的请求",
            }
            rows.append([defm.get(r[0],r[0]),
                         (defm.get(r[0],r[0]) if False else r[1]) if False else ({"Time from request submission until the first output token is received":"从请求提交到收到首个输出token"
              ,"Time between two consecutive tokens (e.g., from token i-1 to token i)":"相邻输出token之间的间隔(如token i-1到i)"
              ,"The average ITL across all output tokens in a request":"请求内所有输出token的ITL平均值"
              ,"Total time to process a request, i.e. TTFT + sum of all ITLs, or equivalently the time between submitting request and receiving the last output token":"处理请求的总时长，即 TTFT+各ITL之和，等价于提交到最后一个token的时间"
              ,"Total tokens processed per second (input, output, or both), or alternatively requests per second":"每秒处理的token总数，或每秒请求数"
              ,"Throughput that meets service-level objectives (SLOs) such as max TTFT, TPOT, or e2e latency. For example, only tokens from requests meeting those SLOs are counted":"满足SLO(如TTFT/TPOT/e2e延迟上限)的吞吐；例如只统计达标的请求token"
              }.get(r[1],r[1]))])
        s['table']['rows']=rows

# 每节 paras 过长的 li 保持原文"·"; 表尾
# --- 最终 DATA ---
DATA={
 "title":"Inside vLLM：高吞吐 LLM 推理系统内部解剖（全量含代码与图）",
 "summary":[
   {"key":"引擎内核","body":"LLM 引擎=调度器+KV缓存分块管理+前向采样；V1 调度把 prefill/decode 同批混排，paged attention 按块分配缓存。"},
   {"key":"四大高级特性","body":"分块预填充、前缀缓存（整块哈希命中复用）、引导解码（FSM掩码）、推测解码（小模型提议大模型验证）。"},
   {"key":"如何上规模","body":"MultiProcExecutor 多进程 TP→DP=1 起跑；headless+API 两 node 协作；用 vllm bench 与 roofline 权衡延迟/吞吐。"},
 ],
 "lead":intro_paras,
 "sections":sections,
 "conclusion":concl,
 "reference_url":"https://www.aleksagordic.com/blog/vllm",
}
open(base+"/article_data.json","w",encoding="utf-8").write(json.dumps(DATA,ensure_ascii=False,indent=2))
tot=sum(len(s.get('paras',[])) for s in sections)
figs=sum(len(v) for s in sections for v in s.get('fig_after',{}).values())
print("OK sections:",len(DATA['sections']),"paras:",tot,"figs:",figs,"concl:",len(concl))
print("intro lead paras:",len(DATA['lead']))
