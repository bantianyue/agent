# -*- coding: utf-8 -*-
# parse content*.txt -> article_data.json
import os,re,json,glob
D=os.path.dirname(os.path.abspath(__file__))
sections=[]; cur=None; paraidx=0

def flush_dangling_after_figs():
    return 0

def parse(lines):
    global cur,paraidx
    for raw in lines:
        line=raw.rstrip()
        if not line.strip(): continue
        if line.startswith('S# '):
            cur={"type":"h2","title":line[3:].strip(),"paras":[],"fig_after":{}}
            sections.append(cur); paraidx=0
        elif line.startswith('T '):
            cur["paras"].append(line[2:].strip()); paraidx=len(cur["paras"])-1
        elif line.startswith('F '):
            body=line[2:].strip()
            sp=body.split('|',1)
            src,cap=(sp[0].strip(), sp[1].strip() if len(sp)>1 else '')
            # 挂在当前最后一条 para 之后
            if not cur or not cur["paras"]:
                cur["paras"].append(''); paraidx=0
            key=str(paraidx)
            cur.setdefault("fig_after",{})[key]=cur.setdefault("fig_after",{}).get(key,[])+[{"src":src,"caption":cap}]
            # 关键: 挂一次后, 再遇到下一图但无新 para 会重复挂到同一 key (多图连排)
            # 处理: 每张图前自动追加一条不可见图? 采用: 在 F 前若无前一 T(紧邻的 F)就插入短文避免连排
            # 我们在 content 已保证每 F 都在一条 T 后; 连续两条 F(如 fig02图2/fig03同T后)→ 会连排!
            # => 自动在图后插一句留白过渡以隔开
            paraidx=len(cur["paras"])-1
    # 后处理: 若某 key 对应>=2 图 → 图连排, 在中间插入分隔段(把后图挪到其+1)
    fix=[]
    for s in sections:
        fa=s.get("fig_after",{})
        newfg={}
        # 重建的 safest: 序列化 每 para i: 先放 text (若存在) 再放 fig 列表逐个夹文字
        # 方案B: 把它转成每一图跟随一个 para 的线性:
        # 在解析时就保证, 这里若某 key 有>=2个fig, 则把除第一个外的每个拆出,后插一条 para '(续上图)'
        seq=[]
        paras=s["paras"]
        for i,p in enumerate(paras):
            seq.append(('T',p))
            if str(i) in fa:
                for g in fa[str(i)]:
                    seq.append(('F',g))
        # rebuild with 图间永不紧紧相邻: that's guaranteed by alternating T/F? but paras may be empty? if two T none
        # 保证图不连排: seq 中 F 相邻则在前一 F 后插 intro para '(承接上图…)' 
        out=[]
        prev=None
        for kind,val in seq:
            if kind=='F' and prev=='F':
                out.append(('T','(承接上图)'))
            out.append((kind,val)); prev=kind
        # 重组为 paras+fig_after
        nparas=[]; nfa={}
        curp=-1
        for kind,val in out:
            if kind=='T':
                nparas.append('(承接上图)' if val=='(承接上图)' else val); curp=len(nparas)-1
            else:
                nfa[str(curp)]=nfa.get(str(curp),[])+[val]
        s["paras"]=nparas; s["fig_after"]=nfa
# meta text
LEAD0=("面试里的最高频答案词,其实是一整套‘把数据搬过机器’的学问。这篇 7 大部分、35 张图的深潜文把 TPU 与 GPU "
"集群的拓扑、带宽层级与四大集合原语(All-Gather/Reduce-Scatter/All-Reduce/All-to-All)绑在一起讲——因为作者说得很直白:集合算法只有在你懂底层物理时才真的成立。")
LEAD1=("全文按 TPU(2D/3D torus,ICI/PCIe/DCN 的带宽金字塔)→ 三+一个原语的 ring/chain/tree 实现 → NVIDIA(DGX fat tree、不等"
"值 bisection、NVLink/SHARP 网内归约、跨 node 分层算法)展开。想推理 transformer 训练/推理的性能,终究得推理数据怎么穿越芯片与集群;本文给的就是这条可以用数字估算的路。")
SUMMARY=[
 {"key":"组织","body":"7 部分长文,35 张配图图注全保留:①TPU 拓扑(superpod/slice/DCN/PCIe/ICI/带宽层级+2 数值例)②All-Gather(1D/2D ring/chain)③Reduce-Scatter 与 All-Reduce(AG 对偶+组合)④All-to-All(=分片式转置,MoE 场景)⑤NVIDIA 拓扑(node/SU/fat tree/bisection 数值)⑥节点内(Ring/Tree/SHARP+multicast)⑦跨节点(分层 All-Gather/All-Reduce/sharded/All-to-All over IB)。"},
 {"key":"核心数字可背","body":"单向 ICI 45GB/s×1μs=45KB(延迟主导分界);DGX H100 node 400GB/s IB 注入;NVSwitch 450GB/s/GPU(全双工);8 颗 node 内向侧 1.8TB/s↔双向 3.6;SU 32 颗 6.4(双向12.8);64/64 切分 25.6(双向51.2);SHARP 理论近2×(8颗~1.75×)、实测~1.3×;recursive doubling tree 步数 log2N。"},
 {"key":"方法提醒","body":"理想带宽模型是大前提:SHARP 实测打折、满 fat tree 才有满 bisection、多 GPU All-Reduce 常到 GB 级才接近峰值。文尾 all-reduce 实测多个复现都只 ~1.3× → 别照抄数字,对具体集群跑 microbenchmark。"},
]
CONCL=[
 "最值得带走的是作者怎么把四原语还原成可背的估算而非魔法。吞吐主导时,torus 上 All-Gather/Reduce-Scatter 一阶通信时间≈D/BW单向;能并行两轴就近似再减半,延迟主导时(log2N 步的 tree、消息 chunk 尺寸)决定主项。GPU 则是两级分域:node 内 NVSwitch 全连(满速直达、无绕行),node 外 InfiniBand 经 SU/spine(fat tree 不超卖才有跨分区的 N×400GB/s)。",
 "作者反复夹一句现实提醒:SHARP 理论 2×实测只 1.3×、混装 fat tree 才满 bisection、GPU 大到 GB 级才拉满带宽——理想模型到真集群之间要靠 microbenchmark 校准,别照搬论文数字。这正是读性能文最该学的习惯。",
]
content_lines=[l for fp in sorted(glob.glob(os.path.join(D,'content*.txt'))) for l in open(fp,encoding='utf-8')]
parse(content_lines)
data={"title":"TPU 与 GPU 集群里的集合通信解剖:4 个原语 + 7 节拓扑到算法的完整地图",
      "reference_url":"https://www.aleksagordic.com/blog/collective-operations",
      "summary":SUMMARY,"lead":[LEAD0,LEAD1],"sections":sections,"conclusion":CONCL}
json.dump(data,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
paras_stuck=sum(1 for s in sections if not s['paras'])
figs=sum(len(v) for s in sections for v in s['fig_after'].values())
print("sections",len(sections),"figs",figs,"chars",sum(len(x) for s in sections for x in s['paras']),"空paras节",paras_stuck)
# sanity 唯一 idx
for i,s in enumerate(sections):
    for k in s['fig_after']:
        if int(k)>=len(s['paras']): print("越界",i,k,len(s['paras']))
