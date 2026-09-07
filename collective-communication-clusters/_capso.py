# -*- coding: utf-8 -*-
# Collective Communication (TPU+GPU) 全图 35 + details —— 单 big builder
# 标记法: paras 为字符串或 dict {FIG:('figNN.png', caption)} 顺序内联为 h3"插图"
import os,json
D=os.path.dirname(os.path.abspath(__file__))
S=[]
def h2(t): S.append({"type":"h2","title":t,"paras":[],"fig_after":{}}); return S[-1]
def put(sec,*items):
    # 顺序写入; text 进 paras; {F: (src,cap)} 追加为图+摘要节点
    for it in items:
        if isinstance(it,str): sec["paras"].append(it)
        else:  # 图 token -> paras 里放占位小标题不挂图, 另行收集最后批量挂
            sec["_figs"].append(it)
def figs(sec, n):
    # 在每个 sec paras 末尾按 _figs 挂 fig_after key=n(n=n 段后)
    idx=int(len(sec["paras"]))
    arr=[]
    for (src,cap) in sec["_figs"]: arr.append({"src":src,"caption":cap})
    if arr: sec["fig_after"][str(idx)]=arr  # 全放最后段后(连排问题) —— 需避免多图连排! 改逐图隔文字
# 用精确方案：每幅图单独建 h2/h3 段, paras=一句引导+图即上文。
# 下面直接构造，最稳。
lead=[
 "面试/系统设计最常被人拿来撑场的『All-Gather、Reduce-Scatter、All-Reduce、All-to-All』，在这篇里被装进真正的机器里讲：TPU 是 2D/3D torus、GPU 是 fat tree + NVLink/InfiniBand 分域。作者的立场很直白——集合算法只有在你看得懂底层拓扑时才真有意义。文中 35 张图把每个原语在真实拓扑上的走法画得清清楚楚，图注与主论同保留。",
 "想推理现代 transformer 训练/推理的性能，迟早得推理『数据在集群里怎么动』。这篇从 TPU v5e 超级片讲到 NVIDIA DGX H100 SuperPod，从 ICI/PCIe/DCN 的带宽层级，到单向/双向 ring、chain/path、recursive doubling(tree)与 hierarchical(跨 node/SU/spine) 各种算法，再到 SHARP 网内归约与 fat tree 不超卖逻辑。文里那套『D/BW + 延迟×跳数』的估算式都交代清楚。"
]
summary=[
 {"key":"结构","body":"65 分钟级的深度长文，7 大部分：①TPU 拓扑(superpod/slice/DCN/PCIe/ICI/带宽层级+2 个数值例子) ②All-Gather(1D/2D ring/chain) ③Reduce-Scatter & All-Reduce(与 AG 对偶、如何拼) ④All-to-All(=一个分片式转置, MoE 场景) ⑤NVIDIA GPU 拓扑(node/SU/fat tree/bisection 数值) ⑥节点内 GPU 集合(ring/tree/SHARP/网内 multicast) ⑦跨节点分层算法(All-Gather/All-Reduce/sharded AR/All-to-All over IB)。共 35 幅带中文图注示意图。"},
 {"key":"推荐读法","body":"先把每段的『带宽×延迟』心中换成一条链路估算式：双向 ICI 45GB/s×1μs=45KB，约略等于一笔消息 chunk 大小时延迟就压不住了——这决定你该用 ring 还是 tree。TPU 用 45 GB/s ICI；GPU 每 DGX node 400 GB/s IB 注入、node 内 NVSwitch 全连 450 GB/s/GPU(全双工)。"},
 {"key":"三句带走","body":"① ring 是物理最近邻，在 TPU 是 ICI 路径、在 GPU 是 NVSwitch 上人为挑的逻辑序；tree 只要 log2N 步、可管延迟，但大 size 上 ring 更好流水并常有更高有效带宽(NCCL 会按消息大小与拓扑选 ring/tree/hybrid)。② SHARP 让 switch 直接网内归约，理论上把 All-Reduce 提到接近 2×，但减少与 multcast 不完美重叠，实测常见只 ~1.3×。③ 别假设一条带宽打天下：不超卖 fat tree 才有 N×400 GB/s 的跨分区带宽、跨 node 的分层集合要两次穿越(nvswitch+IB)。"}
]
concl=[
 "这套『把 4 个原语放进真实机器』的讲法，最珍贵的可能是作者展示如何把它还原成几条可背的等式而不是魔法：在吞吐主导区,torus ring 上 All-Gather 的一阶时间 ≈ D/BW(单向),用两轴并行就再近似砍半；延迟主导时(消息 chunk 小到每次传输只盖几十 KB)，1μs 每跳的延迟就开始改你的主项，于是 log2N 步的 tree 与合理选择消息大小变得重要。GPU 那边则多了『分域』——node(NVSwitch 内)与跨 node(InfiniBand/SU/spine)两级，分层算法与 rail 感知 rank 摆放决定你是否真吃得到 N×400 GB/s。",
 "我对读者的一句提醒：文中的理想带宽模型是大前提——SHARP 理论 2×实测 ~1.3×、混装 fat tree 才拿满 bisection、多 GPU All-Reduce 要到 GB 级才贴近峰值带宽,这些『现实打折』最好都按你真实集群跑 microbenchmark 校准,别照抄数字。图 1-35 与正文一起,构成一份可直接对照线宽/跳数的动手地图。"
]
# ---------------- section list 构造 ----------------
def h2s(t): 
    o={"type":"h2","title":t,"paras":[],"fig_after":{}};S.append(o);return o
def txt(sec,*ts): sec["paras"]+=list(ts)
def fg(sec, idx, src, cap, leadtxt=None):
    if leadtxt: txt(sec,leadtxt)
    sec["fig_after"][str(idx)]=[{"src":src,"caption":cap}]
s=h2s("为什么关心集合通信")
txt(s,"2026 训练/服务 transformer 是分布式问题。按数据并行 → 反向梯度同步 all-reduce;张量并行/FSDP → forward/backward 大量 all-gather+reduce-scatter;MoE 专家并行 → all-to-all。懂性能就要懂数据怎么在集群流动。本文按 TPU/GPU 两大类讲拓扑,再讲原语与算法(主 ring;小消息适合 tree/log2 步),分七部分。")

s=h2s("TPU 集群拓扑:Superpod · Slice · DCN · PCIe · ICI")
txt(s,"TPU 直连近邻,每颗 4/6 邻居:2D torus(v2/v3/v5e/v6e)、3D torus(v4p/v5p/TPU7x/8t)。(8i 推理芯片用 boardfly high-radix,跳过。)2D torus=带 wrap 边界的网格→甜甜圈直觉;3D 三轴都 wrap。")
fg(s,0,"fig01.png","图1·TPU 连接类别：2D(torus4)/3D(torus6)。")
fg(s,0,"fig03.png","图3·3D torus 六邻居 ±x/y/z(示意)。")
fg(s,0,"fig02.jpg","图2·2D torus 直觉:i 时刻网格带环绕边界(甜甜圈覆盖示意)。")
# 图2其实放在文字"找感觉"后——此处独立小段
txt(s,"每个 TPU 芯片通过 ICI(片间互联)连邻居。最大 ICI-island 叫 TPU Pod(常也叫 superpod)。例:v4 pod=16³=4096;v5p=16×20×28=8960。对比 GPU:scale-up domain 传统很小(常见单 NVLink 域 8 GPU;GB200 NVL72 到 72)。6 邻居的 pod,最小满 3D torus 是 4×4×4 立方;若小 slice(如 2×2×2)失去 wrap → 变 mesh,该轴向 ring 类集合约 2× 慢。slice=单 pod 内经 ICI 连通的一块(如 v5e 2×2/2×4/8×8);如果你的应用通信重,应挑保留 torus 的 slice 形状(如 4×4×8)。")
fg(s,1,"fig04.png","图4·v5e 16×16 superpod 拓扑。")
txt(s,"v5e 是 16×16 2D torus(wrap 在 16 时成环)；更小 slice 如 8×16 会在短边失去 wrap(again ≈2× 惩罚)。跨单 pod 用 DCN(data-center networking),吞吐远低于 ICI——太多流量跨 pod 边界会成为训练瓶颈。多个 pod 经共享 DCN fabric 连成更大集群。")
fg(s,2,"fig05.png","图5·多个 pod 经 DCN 骨干相连。")
txt(s,"图内细看:0 行连回 15 行、0 列连回 15 列→为何是 torus 而非 mesh;torus 限制了路径长——数据常得经中间 TPU 转发。例:TPU(15,15)→(2,15) 最短路经 wrap:(15,15)→(0,15)→(1,15)→(2,15),而绕远要过 (14,15)(13,15)…. (另有 twisted-torus 细节调 DCN 连接以便 All-to-All,略。) 每颗 chip 也经 PCIe 接一块『专属』CPU host(v5e:1 host 接 2×4=8 chips → host↔8 芯片间 8 条 PCIe)。注意跨 pod 数据要先过 PCIe 才上 DCN→DCN 比 PCIe 更慢。跨 pod 流量:源 chip HBM→PCIe→源 host→DCN→目标 host→PCIe→目标 chip HBM。结论:离计算 die 越近越快、越往外越慢。")
fg(s,3,"fig06.png","图6·v5e 集群带宽层级：Die/HBM > ICI > PCIe > DCN。",None)
txt(s,"场景 1:要一块 (2048,2048) bf16 矩阵(8 MiB)从 (3,3)→(0,0)，两条经 ICI 平行路径各 6 跳。忽略了链路延迟——ICI 实际约 1μs/跳；本例两路并行各 6 跳≈加 6μs，在所传大块面前可忽略，但小消息不可忽略→要知道自己在延迟主导还是吞吐主导。估法:单向 ICI 45 GB/s 下 1μs 能流多大数据?45GB/s×1μs=45 KB。消息 chunk 与这相当(ca.几十KB)就意味着延迟很关键——忽略 1μs/跳会大幅估错，纯带宽近似不再成立。")
fg(s,4,"fig07.png","图7·把一块 8 MiB bf16 经两条 ICI path 在 4×4 v5e mesh 里搬动。")
txt(s,"场景 2(PCIe+ICI+HBM→VMEM 齐算):有一 (128·1024, 128·1024) bf16 矩阵分到 4×4 slice,每 chip 持 (32·1024,32·1024) 子矩阵且已下放到 host DRAM。问把它整块搬到 TPU(0,0) 并和一条 (128·1024,128) 向量做 matmul 要多久?(VMEM=片上快速 SRAM,≈程序员可管 shared memory,直连 matmul/systolic。)思考图:8。")
fg(s,5,"fig08.png","图8·把分片矩阵 gather 到 TPU(0,0) 用于 matmul。")

s=h2s("All-Gather:1D/2D ring 与 chain")
txt(s,"动机:某并行维度把矩阵 A 分片在各 chip,每 chip 需完整 A 才能各自算 matmul → 需要把各分片聚齐到每 chip。")
fg(s,0,"fig09.png","图9·All-Gather 动机:收集 A 的各片让每芯片能本地跑 matmul。")
txt(s,"高效做法常见 ring。先搞清 ring 从哪来:16×16 v5e torus 两条轴向自然各成 1D 双向 ring。为便于看图改小为 8 颗(假装 8 也行 wrap)。")
fg(s,1,"fig10.png","图10·16×16 torus 沿两轴各现 1D 双向 ring。")
fg(s,1,"fig11.png","图11·简化为 8-chip ring。")
fg(s,1,"fig12.png","图12·双向 1D ring 上的 All-Gather(zoom 追一片)。
同一节 fig_after 多图同 index → 需要 index 唯一
我拆段:fig10→idx1；fig11 另立 para"),None)
PYDEBUG_MARK
