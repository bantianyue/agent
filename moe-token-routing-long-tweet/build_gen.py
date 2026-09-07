# -*- coding: utf-8 -*-
import os,json
D=os.path.dirname(os.path.abspath(__file__))
sections=[]; cur=None
for raw in open(os.path.join(D,'content.txt'),encoding='utf-8'):
    line=raw.rstrip()
    if not line.strip(): continue
    if line.startswith('S# '):
        cur={"type":"h2","title":line[3:].strip(),"paras":[],"fig_after":{}}
        sections.append(cur)
    elif line.startswith('T '):
        cur["paras"].append(line[2:].strip())
    elif line.startswith('F '):
        sp=line[2:].strip().split('|',1)
        idx=len(cur["paras"])-1
        if idx<0: cur["paras"].append(''); idx=0
        cur.setdefault("fig_after",{})[str(idx)]=cur.setdefault("fig_after",{}).get(str(idx),[])+[{"src":sp[0].strip(),"caption":sp[1].strip() if len(sp)>1 else ''}]
# 去连排
for s in sections:
    fa=s.get("fig_after",{}); seq=[]
    for i,p in enumerate(s["paras"]):
        seq.append(('T',p))
        if str(i) in fa: seq+= [('F',g) for g in fa[str(i)]]
    out=[]; prev=None
    for k,v in seq:
        if k=='F' and prev=='F': out.append(('T','(承接上图)'))
        out.append((k,v)); prev=k
    np=[]; nfa={}; idx=-1
    for k,v in out:
        if k=='T': np.append(v); idx=len(np)-1
        else: nfa.setdefault(str(idx),[]).append(v)
    s["paras"]=np; s["fig_after"]=nfa
data={"title":"一个 MoE token 被路由到专家时,到底发生了什么(8 步原子拆解)",
 "reference_url":"https://x.com/navaneethvb/status/2094708652724883845",
 "summary":[
   {"key":"一句话","body":"社区科普作者 @navaneethvb 用 8 步把『token 过 MoE 层』拆到原子级:来的不是词而是 hidden 向量→router 逐专家打分→不同 token 选中不同专家→运行时 permute 按专家分组做 grouped GEMM→跨卡时变专家并行+all-to-all→输出逆排列送回→按 router 分数加权合成一个 hidden state。全推约 690 词+1 架构图。"},
   {"key":"核心机制","body":"真正被路由的是向量打过分的 hidden state;router 分同时是权重。top-2 只激活每 token 的少数专家。多 GPU 时各卡持不同专家,一个 token 想要不同卡上的专家就得趟一遍 all-to-all 通信;专家跑的是 grouped GEMM;结束后结果按原 permute 反转归还,再按路由分(如 E2:0.71、E4:0.52)加权合并。"},
   {"key":"来源与性质","body":"普通 X 长推(regular tweet +1 图),非厂商口径;文内数字为教学性示意值(top-2 打分与 GPU 分配表),非实测基准。与 MoE 工业实现细节(负载均衡、aux loss、capacity factor、token drop)不冲突,属直觉入门。",
   }],
 "lead":[
   "面试被问『MoE 怎么加快推理』时,标准答案常是稀疏激活——但很少有人把『一个 token 被路由到 expert 时到底发生什么』讲到原子级。这条 X 长推正好补上:从向量打分、permute 分组、跨卡 all-to-all,到 grouped GEMM、结果归还与加权合并,8 步拆得明明白白。",
   "本条为 @navaneethvb 的 ~690 词长文+1 图的全文中译;编译保留了 Top-2 打分、按专家分组与 GPU=专家 等全部示意表,配图为原文自带的架构图(转 PNG)。",
 ],
 "sections":sections,
 "conclusion":[
   "这条推文最值得带走的是那个清醒的结尾认知:MoE 稀疏路由的新鲜机制其实只有『router 与权重早已学出来』这一步——剩下 8 步到 5 步的变换(打分、按组重排、必要时跨卡的 all-to-all、grouped GEMM、逆置换还输出、按权重合成)全是明确的工程操作,让人意识到稀疏模型在生产里的难点大多在『如何把搬移与并行做对、做快』。",
   "提醒读者:里头的 0.71/0.52 之类是作者的示意数值,用来讲权重为何是权重;真实 router 给分、Top-k 选取、capacity/drop 与负载均衡的处理要复杂数档。把它当直觉入门,别当成实现规格。原推可回 X 查看原文与讨论。",
 ],
}
json.dump(data,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
figs=sum(len(v) for s in sections for v in s['fig_after'].values())
print("sections",len(sections),"figs",figs,"chars",sum(len(x) for s in sections for x in s['paras']))
for i,s in enumerate(sections):
    for k in s['fig_after']:
        if int(k)>=len(s['paras']): print("越界",i,k,len(s['paras']))
