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
        body=line[2:].strip(); sp=body.split('|',1)
        src=sp[0].strip(); cap=sp[1].strip() if len(sp)>1 else ''
        # 挂在最后一段之后(保证上文), 若无段落则单列
        idex=len(cur["paras"])-1
        if idex<0:
            cur["paras"].append(''); idex=0
        cur.setdefault("fig_after",{})[str(idex)]=cur.setdefault("fig_after",{}).get(str(idex),[])+[{"src":src,"caption":cap}]
# 后处理: 相邻两图(同一 key>1 图 或连续挂了但中间无文字)拆开
for s in sections:
    fa=s.get("fig_after",{})
    seq=[]
    for i,p in enumerate(s["paras"]):
        seq.append(('T',p))
        if str(i) in fa:
            seq.extend(('F',g) for g in fa[str(i)])
    out=[]; prev=None
    for k,v in seq:
        if k=='F' and prev=='F':
            out.append(('T','(承接上图)')); 
        out.append((k,v)); prev=k
    np=[]; nfa={}
    idx=-1
    for k,v in out:
        if k=='T':
            np.append(v); idx=len(np)-1
        else:
            nfa.setdefault(str(idx),[]).append(v)
    s["paras"]=np; s["fig_after"]=nfa
data={"title":"传统以太为何喂不动 AI 工厂？Spectrum-X Ethernet 如何重写规则",
      "reference_url":"https://developer.nvidia.com/blog/giga-scale-ai-ethernet-evolution-spectrum-x-ethernet-rewrites-rules/",
      "summary":[
        {"key":"主线","body":"Scale-out 网络取代单机算力成为新一阶瓶颈。作者(Scot Schultz)先讲为什么传统『拿来就用的以太网』在高熵网页流量里的成功经验,被 AI 那种低熵、大象流、同步突刺的负载物理性地按在地上摩擦(ECMP 哈希撞车、有损耗、慢拥塞控制 + 多租户 80% 带宽坍塌的 DeepSeek-V3 实测),再拆 NVIDIA 的三层控制环(网内自适应路由/目标 CC/卡上 PLB),最后解到 Multiplane 拓扑为何能到 12.8 万端点又不堆层。全文图注、数据、白皮书引用都来自 NVIDIA 方测量。"},
        {"key":"三句带走","body":"① 传统以太是用『均衡高熵小流』的思维做静态哈希(ECMP),AI 只有少量同步大象流,一场哈希撞车/一处链路 flap 就能以 straggler 拖垮整次集合。② Spectrum-X 把一套『快速反应拥塞』切成三段互不干扰的硬件环:网内 AR(JSQ 逐包选路几百ns)、仅在 AR 耗尽时才打 ECN 的 CC、主机边缘 per-plane 有状态 PLB(先滤拥塞失效平面、再选最浅队——把交换机的 JSQ 复刻到卡上)。③ 端口 800Gbps 拆四 ×200Gbps 独立 2 层 fat-tree plane,靠光 shuffle 在主机边缘留满路径多样性,达到 12.8 万端点不堆层;PLB 让坏 plane 被隔,失效时其余 plane 仍满血 → 10% 链路失效带宽只按比例掉 11%(传统以太崩 50%+)。"},
        {"key":"提醒","body":"厂商稿:核心数据(NVIDIA 厂内/研究集群实测+NSX 高保真仿真)未独立复现;『2.68ms vs 1.08s』『735→668ms』诸数对厂商有效,跨厂/跨规模需以官方白皮书实验条件核对。"},
      ],
      "lead":[
        "当训练扩到几十万颗 GPU,机房真正的瓶颈往往不再是单卡,而是把它们连起来的网。这篇 NVIDIA 技术长文把矛头对准长久以来『免费又管用』的传统以太网,讲清它为什么在 AI 负载面前撞物理墙,以及 Spectrum-X Ethernet 如何用『交换机+SuperNIC 一起设计』与三套硬件控制环把规则重写。",
        "全文为厂商第一人称技术博客(标注作者 Scot Schultz)直出 HTML,含 5 张正文测算图(隔离/拓扑/韧性/负载/failover)+可参照的硬数据;编译按图文 100% 保真处理,数据以原文白皮书口径为准。",
      ],
      "sections":sections,
      "conclusion":[
        "这篇的价值不在替 NVIDIA 背书,而在它把『AI 网络为什么不能沿用云网络』这套理由讲得格外清楚:不是网速不够,而是『少量同步大象流 + 灾难性的 straggler』让静态哈希、有损重传、软件拥塞控制在 AI 负载下全部错位。Spectrum-X 的真正卖点可以压缩成一句——把拥塞反应从『秒/毫秒+软件』推到『亚μs+硬件』,并按 plane 隔离让一处故障不污染全局(坏 plane 降 20%,好 plane 仍 100%)。",
        "留给读者三句判断:① 一切厂商数据都标注测量者(NVIDIA NSX 仿真/自测集群),跨厂或换规模请认准 WHITE PAPER 的实验条件再信;② Multiplane 的价值前提是『流量能每包被智能分摊』——无感知喷洒在真实链路 flap 下反而把局部故障放大成全局瓶颈,这是架构比较里最被低估的一环;③ 对正在搭 AI 工厂的人,决定性指标不是单一 P99 或吞吐峰值,而是『在 10% 链路失效与多租户噪音下,你的训练步时间还稳不稳』。",
      ]
     }
json.dump(data,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
import re
figs=sum(len(v) for s in sections for v in s['fig_after'].values())
print("sections",len(sections),"figs",figs,"bodychars",sum(len(x) for s in sections for x in s['paras']))
for i,s in enumerate(sections):
    for k in s['fig_after']:
        if int(k)>=len(s['paras']): print("越界!!",i,k,len(s['paras']))
