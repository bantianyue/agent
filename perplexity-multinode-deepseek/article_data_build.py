# perplexity multinode deepseek builder (parser content.txt)
import os,json,re
D=os.path.dirname(os.path.abspath(__file__))
S=[]; cur=None
for raw in open(os.path.join(D,'content.txt'),encoding='utf-8'):
    l=raw.rstrip()
    if not l.strip(): continue
    if l.startswith('S# '): cur={"type":"h2","title":l[3:].strip(),"paras":[],"fig_after":{}};S.append(cur)
    elif l.startswith('T '): cur["paras"].append(l[2:].strip())
    elif l.startswith('F '):
        b=l[2:].strip().split('|',1); idx=len(cur["paras"])-1
        if idx<0: cur["paras"].append(''); idx=0
        cur.setdefault("fig_after",{})[str(idx)]=cur.setdefault("fig_after",{}).get(str(idx),[])+[{"src":b[0].strip(),"caption":b[1].strip() if len(b)>1 else ''}]
# anti co-Figure
for s in S:
    fa=s.get("fig_after",{});seq=[]
    for i,p in enumerate(s["paras"]):
        seq.append(('T',p))
        if str(i) in fa: seq += [('F',g) for g in fa[str(i)]]
    out=[];pr=None
    for k,v in seq:
        if k=='F' and pr=='F': out.append(('T','(承上)'))
        out.append((k,v));pr=k
    np=[];nf={};ix=-1
    for k,v in out:
        if k=='T': np.append(v);ix=len(np)-1
        else: nf.setdefault(str(ix),[]).append(v)
    s["paras"]=np;s["fig_after"]=nf
lead=["Latency 与 throughput 常被当作不可兼得：加 batch 抬吞吐却加延迟，加张量并行降延迟却削副本、把吞吐带下去。Perplexity 的这份工程总结给出一个反直觉却好用的结论——对 DeepSeek-V3/R1 这种 MoE，只要把 expert 摊开到更多 GPU/多节点，大多数场景能同时拿到更高的吞吐和更低的延迟，因为每 token 只激活 37B/671B，『摊得越宽、单卡显存带宽压力越低』。",
"本文是其对 DeepSeek 671B 部署的完整技术拆解：DP/TP/EP 怎么组合、单节点(8×H200)对多节点(至多 16×H100)在 Pareto frontier 上的实测差异(EP128 在同等输出速度下吞吐可达 5×)，再到 Dispatch/Microbatch 重叠、Roofline 分析与量化/FlashInfer/CUDA-Graph/MoE-router 一系列落地斟酌。"]
d={"title":"MoE 的反常识：DeepSeek 671B 多节点部署让延迟与吞吐同时变好 — Perplexity 部署复盘",
"reference_url":"https://www.perplexity.ai/hub/blog/lower-latency-and-higher-throughput-with-multi-node-deepseek-deployment",
"summary":[
 {"key":"核心结论","body":"DeepSeek-V3/R1(671B 总参、每 token 激活 37B、256 routed+1 shared expert)在多节点(更多 GPU)下通常可同时提吞吐与降延迟：把 expert 摊到越多卡、每卡需要读的权重越少、显存带宽压力越小。EP128 在相同输出速度下比单节点(EP8/8×H200)吞吐高到 5×;Pareto frontier 随 EP 升高整体向右上移。大 batch(每卡64)时单节点反而略高(因 NVLink>IB+实现限制)。"},
 {"key":"怎么叠","body":"MLA 用 DP(每 DP group 整份 MLA、不同输入)+可选 TP(MLA 的 latent 共享无法 TP 切,各 rank 都存 kv 参数与 KVCache 副本);MoE 用 EP(每卡管 256/EP 个 routed + 1 shared)。EP=DP×TP(如 16 机 EP128=DP32×TP4)。"},
 {"key":"关键技术","body":"Dispatch/Combine 两个自研 NVSHMEM AllToAll kernel(已开源 pplx-kernels)取代 torch.all_to_all_single(省去跨 DP group 整型 batch 的 allreduce+padding);Dispatch Overlap(shared expert 放本地免通信)+microbatching(层拆 5 段、两 micro 错 3 段交替)实测 MicroBatch 把单 MoE 层从 2667→1896μs(-29%)但 batch<32 可能为负;DeepGEMM/Triton+Split-K、SiLU/CUDA graph、MLA 的 qkv fusion(30.2μs→16.7μs)+FlashInfer;future=Prefill Disaggregation/EAGLE/GB200。"},
],
"lead":lead,
"sections":S,
"conclusion":[
 "被 dense 模型锁死的『低延迟与高吞吐二选一』，在 MoE 里其实有一根杠杆可撬：显存带宽。decode 阶段被带宽而非算力卡住，而专家铺得越开、每卡要读的专家权重越少、等效可用的带宽越大。于是文中几乎每一组数字——EP128 的 GroupGEMM 比 EP8 少一半(555→270μs)、同一输出速度吞吐 5×、microbatch 把 Combine 从 1012→237μs——都指向同一件事：把每卡工作量铺开,别让一两张卡成为带宽短板。",
 "回到工程提醒：这些数字成立在『他们自己的通信 kernel 只到 IB 一半、GEMM 亦未到 roofline 上限』的前提下,真实收益仍要看你的网络与 kernel;microbatch 在 batch<32 会亏、Dispatch Overlap 才省 0.6%,都不是免费。多节点的 5× 优势建立在把 AllToAll 写对、把显存预算留给 40GB KV、Cache 的前提下——对想叠到 GB200 NVL72 的人来说,EP/DP 与预填充分离的选择会再变。"],
}
json.dump(d,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
figs=sum(len(v) for s in S for v in s.get('fig_after',{}).values())
print('sections',len(S),'figs',figs)
pv=0
for s in S:
    for k in s['fig_after']:
        if int(k)>=len(s['paras']): pv+=1
print('越界',pv)
