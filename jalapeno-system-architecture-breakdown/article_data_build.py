#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

S = []
def h2(t): S.append({"type":"h2","title":t,"paras":[],"fig_after":{}})
def h3(t): S.append({"type":"h3","title":t,"paras":[],"fig_after":{}})
def t(x): S[-1]["paras"].append(x)
def code(x): S[-1]["paras"].append("__CODE__"+x)
def fig(src,cap=""):
    k=str(len(S[-1]["paras"])-1)
    S[-1]["fig_after"].setdefault(k,[]).append({"src":src,"caption":cap})

h2("引言")
t("来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026。")
t("在 Hot Chips 2026 大会尾声，OpenAI 展示了他们的芯片架构 Jalapeno。Jalapeno 是一款通用 AI 推理加速器，主要为 OpenAI 自身的工作负载设计，但也能泛化到前沿模型的工作负载。")
t("多数评论者看到这个标题，会以为 OpenAI 造出了一个能在一夜之间取代 GPU 的魔法黑盒。事实与此相去甚远：这次芯片设计里包含了一整套丰富的系统架构权衡与设计方法上的改进。")
t("本文是一篇针对 Jalapeno 的进阶案例研究，基于他们的演讲材料与相关资料，覆盖整个架构，包括它的动机是什么、领导层可能权衡过哪些取舍与替代方案，以及 AI 在哪里创造了价值。原文目录如下：第一部分是系统规格与约束（系统级权衡的 Pareto 前沿、LLM 请求的延迟、每请求能耗的推理效率；架构观察：理论内存 roofline 高于用户 token 吞吐、prefill/speculate/decode 之间不可预测的工作负载特征、在单芯片上平衡大 KV 状态；影响用户体验的延迟来源：互连的 SOTA 拆解、操作数迟到造成的计算停顿）。第二部分是硬件架构如何协同设计以应对 LLM 工作负载（采用 Broadcom Tomahawk 6 交换机的网络架构与替代方案：两层 Fat-Tree、3D/4D 直连 Torus/Mesh、Dragonfly；多 token 预测的投机解码；芯片的空间架构；芯片设计规格）。第三部分是 AI 如何辅助芯片设计（三种 agentic 编码范式、LLM 到 RTL 的管线、LLM 到高级综合的管线、Agentic Flow，以及为何先进芯片设计还没用上 agentic flow、Jalapeno 如何用 Google XLS 做高级综合、与瀑布式设计方法的对比），这部分为付费内容。第四部分是软件模型调优与性能结果（软件性能调优、前沿模型上的结果），同样为付费内容。")
fig("fig01.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

h2("第一部分：系统规格与约束")
t("在 Hot Chips 上展示的所有芯片架构中，Jalapeno 最集中地体现了 AI 加速器在系统定义与协同设计上面临的复杂权衡。它没有为峰值「展示用」FLOPs 做优化，而是以端到端优化为目标，同时在前沿模型的工作负载之间保持性能均衡。")

h3("Pareto 前沿：系统级权衡")
t("设计定制硅，本质上是在穿越一组紧密耦合的 Pareto 前沿。宏观层面有三层：")
t("智能 vs 服务成本 vs 延迟。在 API 与模型层，采用更多参数、推理树或 MoE 的模型更智能，但会增加内存占用与每个 token 的 FLOP 需求。")
t("吞吐 vs 交互性。在系统与推理层，prefill（计算密集）与 decode（内存密集）之间存在权衡，而批大小会影响两者的平衡。")
t("计算密度（FLOPs/mm²）vs 每比特能耗 vs 光罩限制。在物理硅与封装层，提高片上计算密度受光罩尺寸限制，这迫使设计转向 chiplet：把不同功能分离到合适的制程节点上，再用 2D 互连把它们连起来。")
t("除此之外，还有若干系统级与微架构层面的重要前沿：")
t("内存带宽 vs 容量 vs 每比特能耗。这是经典的「内存墙」权衡：片上 SRAM 带宽极大但面积密度很差，HBM 容量巨大却受散热与边缘布线长度限制，两者必须混用。")
t("交换 radix vs 覆盖距离。在 scale-up 互连中，高 radix 交换机（如 Broadcom TH6）能通过减少网络跳数更好地「集中」多个 GPU；但高 radix 的价值取决于最远那个 GPU 能否连到它，因此铜缆信号完整性的极限与光模块的功耗开销，往往决定了给定网络架构下能合理接入高 radix 交换机的 GPU 数量上限。")
t("可编程性 vs 硅效率。一般来说，为特定任务做得越高效的硅越不通用：GPU 的可编程性很高，而固定功能、效率极高的 ASIC 则相反。")
t("模型精度 vs 计算/内存密度。多数 AI 加速器把精度压到 FP8 甚至 FP4，以提高计算密度、缓解内存带宽压力，但这会缩小动态范围，并给编译器增加复杂度以确保模型精度不受影响。")
t("归根结底：世界上最强的模型能定义「什么是可能的」，但要经济地部署它，需要有效的软硬件协同设计。")
fig("fig02.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")
t("OpenAI 审视了这些前沿，并收敛到其中两个最重要的：端到端请求延迟 vs 以每千瓦混合吞吐衡量的能效；解码速度 vs 以每千瓦混合吞吐衡量的能效。在本文中，作者还会涉及其他若干 Pareto 前沿上的设计考量。")

h3("LLM 请求的延迟")
t("传统半导体厂商倾向于按硬件指标来设计加速器，例如峰值理论 FLOPs（也就是「展示用 FLOPS」）与无约束的批吞吐。OpenAI 把这个范式倒了过来，从最终用户在意的东西出发。他们观察到，用户体验主要由推理延迟决定，而延迟通常用三种方式衡量：")
t("首 token 时间（TTFT）：prefill 阶段的提示处理速度。")
t("每输出 token 时间（TPOT）：decode 阶段的 token 生成速度。")
t("末 token 时间：整个请求的总周转时间。")
t("从 ChatGPT、实时 API 客户端以及内部 agent 工作流的终端用户需求出发，OpenAI 反向推导出严格的 SLA，尤其针对 TPOT 与端到端请求延迟，同时保持对其他前沿模型的通用性。")

h3("推理效率：每请求能耗")
t("在集群层面，推理效率实际上给机架本身的电力系统设定了约束，因为要服务于预期使用它的全部用户。每请求能耗与批大小之间是竞争关系：")
t("更小的批量能在快速互连上带来更低的单用户延迟，但会浪费空闲的计算逻辑，因为内存通道每生成一个 token 都要流式读取数十 GB 的权重。")
t("更大的批量让 ALU 保持忙碌，从而最大化能效，但会给单个用户引入排队延迟。")
t("这两种取舍必须被平衡，既要改善整体用户体验，又要保证经济可行性与电网使用效率。OpenAI 按服务层级通过 SLA 定义端到端延迟目标；在满足该目标之后，再优化计算效率，也就是每瓦每秒请求数。")
fig("fig03.jpg")
h3("架构观察")
t("OpenAI 对可比的 GPU 做了一些架构层面的观察，这些观察影响了他们的芯片与系统架构。")

t("理论内存 roofline 高于用户实际 token 吞吐。OpenAI 对理论内存 roofline 的计算，凸显出理论内存带宽与实际 token 生成速度之间的巨大鸿沟。他们算出：如果 HBM 吞吐是唯一的物理约束，理论上可以达到约每秒 2000 次完整模型权重读取；其假设是 128 颗芯片聚合出 1 PB/s 的 HBM4 带宽、模型是约 1 万亿参数的 FP4 前沿模型。在投机解码的帮助下，这个上限可以推到单用户每秒 5000 到 10000 个 token。")
t("但在现实中，单用户 token 速率徘徊在每秒 20 到 200 个之间。这是被并行带来的各种开销限制的，例如芯片间网络延迟、同步延迟与 NoC 路由争用。这些开销经常导致 HBM 在 token 与 token 之间空转、利用率不足。")
t("为了找回集群的经济性，运营方通常会提高并发请求的批大小，以饱和可用的 HBM 带宽。批处理确实优化了服务器吞吐，但对单个用户的提示速度毫无帮助；而那些用户完全不知道、通常也不关心与自己同批处理的其他请求。")
t("内存带宽还可以继续往上推，但会撞上严重的物理约束，这让 SK Hynix 这样的内存厂商开始研究光互连。")
fig("fig04.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

t("prefill、speculate、decode 三者之间不可预测的工作负载特征。几乎所有 AI 加速器及其周边系统，都要在通用性与专用性之间权衡，才能成功应对 LLM 请求推理所需的、程度各异的工作负载。让加速器 100% 时间满载是最理想的，但实践中很难做到。")
t("上图给出了 LLM 的主要处理阶段：prefill 与 decode，两者之间还有一个可选的第三阶段 speculate。")
t("Prefill 通过接收输入提示 token 来构建注意力上下文，把它们并行送过 transformer 模型，并填充内存中的 KV cache。Prefill 是计算密集的，首 token 时间（TTFT）在此关键；它会压榨计算资源，影响供电网络的 di/dt 与散热，也就是每千瓦吞吐的关键之处；把数据写入内存之前，它还会压榨本地 SRAM 与互连带宽。")
t("Speculate 是一个可选步骤，用一个轻量的「草稿」模型预测接下来 K 个 token（比如 5 到 10 个）。这 K 次前向比较便宜，随后用一次覆盖全部候选 token 的验证前向来确认结果。Speculate 主要用来绕过 decode 阶段的内存带宽墙，它可以采取单 token 或多 token 解码的形式；因为数据包跨阶段传输时通信延迟很关键，所以 speculate 会压榨光模块与 SerDes 系统。")
t("Decode 则自回归地一次生成一个 token 来回应请求。每生成一个输出 token，模型都必须读取模型权重加上累积的 KV cache 来计算注意力并算出一个 token。Decode 基本是内存受限的操作，会给 HBM 带来压力，因为每一次 pass 都需要流式填充目标模型权重（在 MoE 中还要做 All-to-All）。Decode 可以用分组查询注意力（GQA）与投机解码等技术来优化，以绕开内存带宽瓶颈；在 MoE 模型里，decode 还容易让工作负载变得突发。")
fig("fig05.png","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")
t("问题在于，多数工作负载的比例变化极大，要为每一个请求精确预估计算需求非常困难。你或许可以设计高度专用的芯片分别处理每一类工作负载再把它们串起来，但这可能因为加速器空闲而导致计算效率下降；同样，你也可以把三种计算都放在一颗平衡的芯片上，代价是其中一部分可能长期未被充分利用。")
fig("fig06.png","来源：S. Bhoja、A. Ankit，《Raptor: The First 3D-DRAM Accelerator for Generative Inference》，Hot Chips 2026")
t("Ravi Narayanaswami 观察到一个规律：未来不支持某些功能，比内置了但暂时用不上的功能更糟。他提到，机会成本高于边际成本，因为它的「遗憾因子」更大。也就是说，宁可现在就多付一点边际成本，把短期内可能处于「暗硅」状态的功能做进去。")
t("作者对这个观点的理解是：这有点像我们不会为了满足当下的需求，去设计刚性、极致高效、只支持固定选项的 CPU；我们需要在足够通用的芯片上保留可编程性，以应对未来的工作负载。设计新的 AI 加速器时，只盯着当前工作负载的原始性能来「展示」是不够的，还必须考虑长期的不确定性。")

t("在单芯片上平衡大 KV 状态。HBM 与 LLM 模型的规模，给 KV cache 带来了若干挑战：用户的上下文窗口越来越大，传递给模型的文件动辄 10 到上百 GB 每个请求。")
t("一种办法是为每类工作负载构建专用芯片，但这样的 KV cache 仍需通过整条外部网络传输。OpenAI 不认为这是长期解。它认为「暗硅」是比「闲置的专用加速器」更小的恶：独立的加速器会增加额外的硬件复杂度，挤占本可用于其他有用功能的空间；而在单一平衡芯片上，未被激活的模块反而把复杂度降到最低，并把芯片功能对用户「黑盒化」。")
t("OpenAI 采用的是单芯片方案：让 KV cache 紧邻计算、内存与网络，使数据移动在这三部分之间保持平衡。")
fig("fig07.png","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

h3("影响用户体验的延迟来源")
t("OpenAI 想削减的是延迟，更准确地说是尾延迟，以此来提升用户体验。")
t("在 LLM 推理中，数据主要通过 all-reduce、reduce-scatter 这类全局归约操作传输；这些操作跨多个处理器同步并行数据。尾延迟会在数百万次计算中造成「掉队者」效应：最坏的那个数据包拖住整个大计算，而其他数据包都按时到达了。")
t("OpenAI 指出了信号路径与软件层面上的几处延迟来源：网络延迟，即从 A 点到 B 点的信号路径因飞行时间与硬件复杂度带来的各种限制；内存系统，两件事影响内存延迟，一是 HBM 读写本身的固有延迟，通常在 30 到 50 纳秒之间，来自 TSV 堆叠中的信号传输、读取 DRAM 单元本身以及基die的复杂度，二是统一、聚合的内存系统往往有高度争用的路径，源于 NoC 路由、交叉开关交叉点与 bank 冲突。")
fig("fig08.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

t("互连中的长延迟路径。一般来说，任何为了处理高速信号完整性非理想性而增加的电路复杂度都会带来延迟。信号穿过 scale-up / scale-out 网络互连时，每经过一个交换机都会增加延迟。上面给出的是截至 2026 年 2 月的一些 SOTA 参考值：可以看到飞行时间（OpenAI 称之为「硬件光速」）相对于其他来源是很小的。")
t("要最小化来自各类来源的延迟，有几件事可做。Nikola Nedovic 在 ISSCC 2026 论坛「新兴低延迟光互连」上指出了几个方向：网络架构层，提高交换机 radix 以减少数据包经过的网络跳数；机架层，用大规模铜背板直接连接 GPU，而不是走传统的 PCIe 控制器、重定时器与以太网 / InfiniBand 交换机；组件层，优化会引入 10 到 100 纳秒固定延迟的 FEC；芯片层，转向低延迟 CPO 链路，这是目前讨论最多、吸引大量投资的方向，NVIDIA 正在用 WDM 在不提高数据率的前提下扩展吞吐，Marvell 则在用 GeSi 调制器瞄准 OMIB。")
t("作者的观点是，OpenAI 没有采用 CPO，因为它还没有真正为实时部署做好准备，所以他们转向其他手段来优化当下的延迟。")
fig("fig09.jpg","来源：N. Nedovic，《Emerging Low-Latency Optical Connectivity》，ISSCC 2026")

t("操作数迟到造成的计算停顿。上述物理来源在网络中累积的延迟，会让操作数晚于预期到达寄存器。在经典计算机体系结构的意义上，操作数迟到会导致「停顿」，因为 PE 阵列要求数据严格同步锁步；结果是计算单元空转，等待中间操作的结果。")
t("延迟从上一节提到的所有物理效应中累积，也会从网络拥塞与争用中累积，例如两个数据包试图使用同一物理资源：从同一个内存 bank 或输出节点读写。这也是为什么很多人认为互连是扩展 AI 算力的关键瓶颈之一，无论从基础物理还是网络的角度看都是如此。")
fig("fig10.png","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")
h2("第二部分：硬件架构如何与 LLM 工作负载协同设计")
t("这些 Pareto 权衡与架构观察，最终影响了硬件系统架构。OpenAI 使用了 Broadcom 的 Tomahawk 6 交换机，并请 Celestica 做机架级集成。")

h3("采用 Broadcom Tomahawk 6 交换机的网络架构")
t("OpenAI 使用一种「半扁平化」的有界两跳 Clos 拓扑，以获得可预测的延迟。这个网络架构的设计目标，是在处理张量并行与 MoE 并行之间取得平衡，同时让数据包最多只跳两跳。")
t("Jalapeno 与 Broadcom 现有的 Tomahawk 6（TH6）协同设计，后者是世界上第一款 102.4 Tbps 的以太网交换芯片。它采用高 radix 架构，单颗 die 上最多支持 512 个 200GbE 端口（或 128 个 800GbE 端口、64 个 1.6TbE 端口）。")
t("在这里，交换机被组织并连接成两个域：scale-up / 本地域，一颗 TH6 以每颗 800Gbps（4×200G）连接 128 颗 Jalapeno，这个高带宽足以支撑张量并行；全局域，八颗 TH6 在 scale-out 域连接 2048 颗 Jalapeno，确保可预测的延迟与足以支撑 MoE 并行的带宽。这套架构保证任意两颗 Jalapeno 之间最多经过本地与全局 TH6 两跳就能互通。")
t("作者的观点是：他们本来或许可以在 scale-up 域用更好的交换机。Broadcom 的 Tomahawk 6 是一台为 scale-out 设计的 radix 与带宽怪兽，用来减少网络总跳数，但由于硬件复杂度，它的延迟有 600 到 700 纳秒。Tomahawk Ultra 有 250 纳秒的超低固定延迟，但总吞吐只有一半，即 51.2Tbps。")
fig("fig11.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

t("替代方案。他们可能考虑过的其他网络架构包括：")
t("两层 Fat-Tree。它使用两层 spine 与 leaf 交换机，保证跨机架的数据包经过 3 跳（leaf、spine、leaf）跨越两层交换机。NVIDIA GB200 InfiniBand SuperPOD 参考架构就采用这种结构，可以用中等 radix 的交换实现极大的机架级扩展能力。OpenAI 没有采用它，因为与两跳的高 radix 拓扑相比，3 跳会增加尾延迟抖动与更高的功耗。")
fig("fig12.jpg")
t("3D/4D 直连 Torus / Mesh 网络。它在相邻计算节点之间使用直接的点对点链路，Google TPU 8t 就采用这种结构，对张量并行这类静态、规整的数据移动模式很有成本效益。Jalapeno 不用 Torus，因为 Torus 的平均跳数偏高，会造成非常不可预测的链路延迟。")
fig("fig13.jpg","来源：P. Makhija，《TPU Rack Overview》，Hot Chips 2025")
t("Dragonfly 拓扑。在 Dragonfly 中，高 radix 交换机被组织成彼此密集连接的本地组，每个组如同一个「虚拟交换机」，各组之间再全连接到系统中的其他所有组。Google TPU8i 采用这种结构，主要好处是节省光模块成本。Jalapeno 不用 Dragonfly，因为它引入了非均匀的全局路径；缓解拥塞需要 UGAL 这类非最小自适应路由，会增加数据包的不可预测性。")
fig("fig14.jpg","来源：N. Jouppi、S. Lakshmanamurthy，《The Eighth Generation TPU Family: Two Chips Optimized for the Agentic Era》")

h3("用多 token 预测做投机解码")
t("投机解码很像人类猜句子的下一个词。")
fig("fig15.png","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")
t("在常规 prefill-decode 流程的 decode 阶段，自回归生成是串行的：每个 token 都要逐步做一次完整前向与内存访问。这种「一次一个」的方式因为延迟更高、硬件利用率不足，限制了系统效率。")
t("投机解码是一种优化技术，通过同时预测并验证多个 token 来突破内存墙。这里的「trunk」指典型 transformer 架构中的全部层，包含多头注意力、FF 以及 add/norm；输入经过这个 trunk 生成输出 token。投机解码主要有两大类：")
t("单 token 预测：8 次前向产生 8 个不同的 token。")
t("多 token 预测：在廉价的图模型上做 7 次前向，再在大型模型上做 1 次前向。OpenAI 选择了后者，以支撑用户体验、能效要求，并获得更高的 token 吞吐。")
t("尽管 Jalapeno 的微架构是为支持多 token 预测从头设计的，OpenAI 目前仍先跑单 token 预测工作负载来验证硅片。")

h3("芯片架构：空间架构")
t("标准 GPU 使用时间化的 SIMT：庞大的 warp 调度器以锁步方式协调数千个线程的执行。")
t("Jalapeno 采用空间架构：独立的 core slice 被平铺排布，并配有专用的 HBM 接口；这些核连接到专门的集合通信结构，支持直接的核到核流式传输。每个核有自己的专用 L1 内存视图，独立运行本地 tensor、SIMD、标量单元，不必等待中央 warp 控制器派发指令。")
t("为了在保持空间可编程性的同时提供熟悉的 SIMT 接口，OpenAI 设计了自研的 kernel 编程语言 Gluon。Gluon 构建在开源编译器 Triton 之上，但能提供更细粒度的硬件控制。它的设计目标是让软硬件协同设计者能用熟悉的 GPU 抽象（thread block）写代码，而不必手工构造空间数据流图。可以把它理解为一种「混合」方案：保留大多数人熟悉的时间化 SIMT 抽象，同时为本来极难编程的空间架构写代码。")
fig("fig16.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")

h3("芯片设计规格")
t("Jalapeno 采用台积电 3nm 制程，以在端到端工作负载上最大化低精度推理的每瓦吞吐。它以一颗计算 die 搭配六个 HBM4 堆栈，每侧三个。内存系统总共提供 15.4 TB/s 与 216 GiB。Jalapeno 功耗 700W，在 fp4 / fp8 矩阵乘法上达到 3 到 13 PFLOPS/s。")
t("作为对比：在 NVIDIA 功耗 1000W 以上的芯片上，B200 提供 9 PFLOPS/s、B300 提供 15 PFLOPS/s 的 fp4 算力，但要记住 Jalapeno 只做推理。")
t("由 2048 颗芯片组成的 Jalapeno 集群，是一个完整的 pod / 数据中心整行，大约横跨 28 到 32 个机架。整个系统提供 27 EFlops/s、32 PB/s 与 432 TiB。")
t("值得注意的是，大部分与带宽相关的性能提升都可以归因于 HBM4。")
fig("fig17.jpg","来源：R. Ho、R. Narayanaswami、C. Leary，《You Can Just Build Things … Chips》，Hot Chips 2026")
h2("第三部分：AI 如何辅助芯片设计")
t("这一部分在原文中属于付费内容。公开页面能看到的部分是：OpenAI 利用 AI 辅助的高级综合，配合 Google XLS；作者接下来要解释它在「把 AI 应用于芯片设计的三种主要方法」中的位置。")
t("以下小节的标题在原文目录里可见，但正文需要付费订阅才能阅读：三种辅助芯片设计的 agentic 编码范式；LLM 到 RTL 的管线；LLM 到高级综合（HLS）的管线；Agentic Flow；为什么 agentic flow 还没有进入先进芯片设计；Jalapeno 如何用 AI：基于 Google XLS 的高级综合；与「瀑布式」芯片设计方法论的对比。")
t("第四部分同样是付费内容，内容包括软件性能调优以及在前沿模型上的结果。")

h2("作者的话")
t("写完这篇文章之后，作者在想一个问题：AI 究竟应该被更好地用来增强当前「瀑布式」芯片设计方法论中的各个步骤，还是用来促成一套更迭代的方法论。在这次设计中，OpenAI 借助开源工具 Google XLS，用他们的前沿模型辅助了块级的 PPA 优化与形式验证。Google XLS 对缩短时间线确有贡献，但作者认为，工作本身那种迭代的、跨域的（而且往往更混乱的）性质，或许是更重要的因素。")
t("在 Hot Chips 之前，作者通过参加五个技术会议，从底层研究了数据中心的架构；本文中散布着他此前的若干深度分析，它们构成了这里讨论的各种跨域效应的基础。DAC 之后，他写过一篇关于 AI 目前在芯片设计中如何被使用的深度文章，建议读者一读，另外还有一篇 AI 加速器基础入门。")
t("一如既往，如果你是专家并发现本文有错误，请联系作者以便及时更正。")

DATA = {
    "summary": [
        {"key": "设计出发点", "body": "OpenAI 没有为峰值「展示用」FLOPs 优化，而是从 ChatGPT 与实时 API 的用户体验反推：以 TPOT 与端到端延迟定 SLA，满足后再优化每瓦请求数"},
        {"key": "关键架构选择", "body": "半扁平化两跳 Clos 网络（TH6 连接 128 颗本地 + 8 颗组全局域 2048 颗）、多 token 预测的投机解码、空间架构 + 自研 Gluon 语言、单芯片平衡 KV cache"},
        {"key": "规格与对比", "body": "台积电 3nm、6 个 HBM4、15.4 TB/s 与 216 GiB、700W、3 到 13 PFLOPS/s（fp4/fp8）；2048 颗集群提供 27 EFlops/s"},
    ],
    "lead": [
        "在 Hot Chips 2026 尾声，OpenAI 展示了自研推理加速器 Jalapeno。多数评论只看标题，以为这是一个一夜之间取代 GPU 的魔法黑盒；但这篇文章指出，真正的价值在于一整套系统架构权衡与设计方法上的改进。",
        "Jalapeno 没有去追峰值「展示用」FLOPs，而是从最终用户的体验出发：用 TPOT 与端到端请求延迟定义 SLA，在满足 SLA 之后再优化每瓦请求数。它在网络、投机解码、芯片架构与 KV cache 布局上都做了针对性取舍，本文按 OpenAI 的演讲材料逐层拆解。",
    ],
    "sections": S,
    "conclusion": [
        "**这份拆解最值得带走的观点是：AI 加速器的设计应该从用户体验反推，而不是从峰值指标出发。** OpenAI 先把 TTFT、TPOT 与端到端延迟定成 SLA，再在这条约束下优化每瓦请求数，于是有了「半扁平化两跳 Clos」、「多 token 预测优先」、「单芯片承载大 KV cache」这些看起来反常规、但彼此自洽的选择。",
        "另一个反复出现的判断是取舍的顺序感：与其为每类工作负载造专用加速器、再把整个 KV cache 搬过外部网络，OpenAI 宁可让单颗平衡芯片上留一部分「暗硅」；在网络层，他们宁可放弃省成本或省跳数的其他拓扑，也要保住两跳与延迟可预测性。对做系统设计的人来说，这种「先定延迟目标，再谈其他」的顺序比任何单个技术选择都更有借鉴价值。",
    ],
    "reference_url": "https://www.siliconcodesign.com/p/an-advanced-system-architecture-breakdown",
    "title": "OpenAI 推理芯片 Jalapeno 架构拆解：从用户延迟出发的系统协同设计",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA.get("sections", [])), "sections")
