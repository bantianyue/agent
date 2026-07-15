要点速览

- 500+ TPS：8×B300上达成500+ TPS：SGLang把day-0的GLM-5.2 NVFP4服务栈两周内优化到生产级。- Spec V2：重叠调度消除GPU气泡，端到端TPS提升11%。- IndexShare：让MTP复用DSA索引器top-k，长上下文下draft开销最多降1.9倍。- TopK-V2：把TopK当选择问题，80K ISL内核延迟降2.33倍，1M ISL达10.17倍。- 内核融合：索引器前导融合把内核数从12降到4；CuteDSL BF16 GEMM在解码小批量下胜cuBLAS。

GLM-5.2发布第一天，SGLang就在Blackwell硬件上用trtllm-gen内核点亮了NVFP4服务。但day-0版本只是「能跑」，离生产级还差一口气。
这篇博客复盘了SGLang团队在两周内做的一系列优化：从运行时调度到CUDA内核，把8×B300上的吞吐推到500+ TPS，同时把长上下文的交互性几乎拉平。

背景
GLM-5.2保留了与早期GLM检查点相同的主干：在DeepSeek-V3风格的MoE之上叠加带稀疏注意力索引器（sparse-attention indexer）的DSA。它新增了两个主要的架构改动：IndexShare（索引共享，用于DSA）以及带IndexShare和KVShare的MTP。
SGLang自发布第一天起就在（Grace）Blackwell硬件上支持GLM-5.2-NVFP4检查点，对稀疏注意力和MoE都使用trtllm-gen内核。为了把这套day-0的栈转变为更快、更稳定、更贴近生产的服务路径，我们引入了以下一系列优化。
零开销调度与Spec v2
Spec V2是SGLang针对投机解码（speculative decoding）的重叠运行时（overlap runtime）。当GPU在forward流上运行当前模型的前向计算时，它会在plan流上完成下一步的KV分配和元数据准备，从而把CPU开销隐藏在前向计算内部。
我们最近默认开启了Spec V2。理论上，重叠调度器（overlap scheduler）应当让CPU在当前这一步GPU仍在忙时处理下一步的簿记工作，使迭代之间几乎没有气泡（bubble）。实践中，要完全兑现重叠调度器和Spec V2的收益还需要几项优化：我们把DSA的draft-extend路径改为可CUDA-graph化，去掉了DSA的seq_lens_cpu以省去D2H同步，移除了残留的H2D同步，并把 _apply_cuda_graph_metadata里零散的eager元数据操作融合起来。当这些GPU气泡消失后，我们看到了端到端TPS 11% 的提升。

SGLang中的IndexShare MTP
GLM-5.2带有一个很强的MTP head，接受长度（accept length）经常达到5以上，这在智能体编程（agentic coding）这类低延迟负载上带来显著的提速。为了正确实现GLM-5.2的MTP行为，我们对SGLang的投机解码运行时做了几处改动。
首先，IndexShare要求SGLang在多个draft步骤之间复用DSA索引器的top-k：在draft第0步算出的top-k会被保留并传给后续步骤，使它们跳过重新计算索引器的过程。这在长上下文下把draft步骤的开销最多降低了约1.9倍，且对输出质量没有任何影响。
其次，top-k需要从正确的位置播种（seed），而在SGLang中这个位置是上一次run_batch迭代的draft-extend。由于Spec V2是异步运行各步骤的，我们必须把这个种子（seed）通过重叠调度器的relay buffer传递，以免它在迭代之间丢失。
TopK-V2
DSA索引器把每个query转化为对历史KV位置的打分，然后挑选出得分最高的候选用于稀疏注意力。沿用我们在DeepSeek-V4博客中提出的“Lightning-TopK”设计，我们把原始的DSA TopK-V1内核升级为TopK-V2，后者把TopK当作一个选择问题（selection problem）而非排序问题（sorting problem）来处理。

TopK-V2对短行和中行使用寄存器驻留（register-resident）或单CTA流式路径。对于长行，一组8个CTA构建本地10-bit radix直方图，并在cluster内归约以定位阈值bin。
一次cluster级的归约定位到第2048大得分所在的bin；高于它的数值直接输出，而处于边界的候选则经历精确的FP32 radix选择。被选中的逻辑位置随后被翻译成物理索引器KV-cache槽位。内核随后在FP32边界处收集候选，并使用精确的radix决胜（tie-break）返回恰好k个条目，运行时支持的k最大可达2048。

一个规划内核（planning kernel）根据批次的序列长度分布选择cluster截止点（cutoff），并为持久化cluster池（persistent cluster pool）构建工作列表，因此这个计划在每个前向时生成，并在各DSA层之间复用。TopK-V2的选择操作和页表变换（page-table transform）也被融合进单个内核以削减延迟。

从基准结果看，TopK-V2在80K ISL下把平均内核延迟从40.7 µs降到17.5 µs，取得2.33倍提速。它的优势随上下文长度而增长，在1M ISL时达到10.17倍（延迟从372.1 µs降到36.6 µs）。这个不断拉大的差距说明，TopK-V2在长上下文负载上的扩展效率要高得多。
Indexer Prologue Fusion（索引器前导融合）
DSA索引器前导（prologue）准备两路数据流：一路是存放在索引器KV cache中的key表示，另一路是用于计算稀疏注意力候选的query表示。原始实现把它表达为一连串小内核和投影（projection）。

图5：DSA索引器前导内核：融合前与融合后的对比。
在“融合前”的路径里，key侧依次运行wk、LayerNorm、RoPE、Hadamard变换、FP8量化以及cache存储；query侧依次运行wq_b、RoPE、Hadamard变换、FP8量化以及head-gate缩放。此外，weights_proj是一个独立的投影，为逐头门控（per-head gate）提供输入。
PR #27705通过两种方式压缩这条依赖链：
第一，它把wk和weights_proj融合成一个单一的BF16投影，命名为wk_weights_proj。其输出被拆分成key激活值和原始的head-gate权重。这移除了索引器路径中一个小的GEMM，并让head-gate权重能被融合后的query内核直接复用。
第二，它融合了逐元素（elementwise）的尾部操作：
key路径：LayerNorm + RoPE + FP8量化 + 分页索引器KV cache存储。
query路径：RoPE + FP8量化 + head-gate缩放。
这张图展示了重要的调度后果。融合前，cache存储位于key侧工作之后，拉长了关键路径（critical path）。融合后，key侧可以作为包含存储在内的一个内核运行，而query侧作为另一个独立的融合内核运行。两侧可以重叠，于是索引器前导从一长串启动（launch）变成了一对更短、更干净的支路。内核总数从12降到4。
融合后的路径还去掉了Hadamard变换。对Q和K施加相同的正交变换（orthonormal transform）能在量化前保持它们的内积不变，因此它的主要影响落在量化表示上。融合后的路径改为直接量化未经变换的激活值。
内核数量的减少直接转化为可测量的解码吞吐提升，尽管这个效应在小批量下更明显（因为此时启动开销占主导）。在批大小为1时，解码吞吐提升约8%，因为索引器前导中那些访存受限（memory-bound）的内核消失了，且从12个内核坍缩到4个移除了关键路径中占比更大的一部分。在批大小为128时，提升较小但依然稳定，约为5%。
GEMM内核改进
GLM-5.2中并非每个矩阵乘法都运行在NVFP4上。为了保护精度，检查点的量化方案让注意力投影（attention projections）和共享专家MLP（shared-expert MLP）保持BF16，只把路由专家（routed experts）量化。PR #30117为这些BF16层新增了一个可选的CuTe DSL BF16 GEMM后端，它源自Flashinfer的TGV GEMM，专为这些BF16层打造。
这个内核把工作切分到多个warp上并分配专门任务：有些warp只从内存加载数据，一个warp只做矩阵乘，少数warp只把结果写回。由于这些是同时运行的独立warp，加载、计算和存储是重叠进行的，而不是一个接一个地发生。
提速的真正来源在于这个内核对加载操作的流水线化程度有多激进。它不会只加载一块数据（tile）然后等它被用掉再去加载下一块，而是让相当于很多块的数据同时处于传输途中，并为此几乎用满了GPU的全部共享内存。在解码运行的小批量下，这些GEMM大部分时间都在等内存而非计算，所以内核能提前加载得越远，等待的时间就越少。这就是相对cuBLAS这类通用库的主要优势，后者流水线化更保守。
一个调优步骤还会挑选最适合所运行形状的块大小（tile size），并且一个提前测得的启发式规则会在每次调用时决定是使用这个内核还是回退到cuBLAS。
其中两个BF16层在TP4下获益明显：融合后的QKV投影（M, 2624, 6144，跨rank复制）和注意力输出投影o_proj（M, 6144, 4096，跨rank切分）。
扫描整个解码范围M=1到32：融合QKV投影在每个批大小下都胜出，相对cuBLAS平均1.08倍，峰值1.13倍。o_proj在每个批大小下也胜出，平均1.05倍，峰值1.08倍。在批大小为1时，端到端解码提速约为4%。

图6：CuteDSL BF16 GEMM相对CuBLAS GEMM的提速，跨不同批大小。
性能结果
我们在图7中收集了GLM NVFP4模型在一个OpenHands多轮智能体编程负载上的性能结果。每轮对话以约80K token的提示开头，每轮输出约220个token，共13轮。后续的轮次复用前缀，使整体缓存命中率达到约92%。我们做了一次并发度扫描，并绘制每GPU token吞吐（tok/s/GPU）相对交互性（tok/s/user）的曲线。每张图固定了模型、GPU系列、精度、负载、服务框架和服务模式，并用SGLang的不同版本与自身对比。

图7：GLM 5.2 NVFP4在SGLang上的性能帕累托（Pareto）曲线。
有三件事很突出。第一，GLM-5.2是一个比GLM-5.1高效得多的架构。在相同的SGLang版本上，GLM-5.2在4×GB300和8×B300上分别带来了约1.4倍和1.3倍的单位用户交互性（per-GPU吞吐）提升。这个收益来自把IndexShare应用到DSA层，以及改进了的MTP head（它复用了IndexShare和KVShare）。第二，自day-0以来，单位用户交互性提升了18–34%。在批大小为1时，我们的优化大幅削减了每token开销，让我们在8×B300上达到了500+ TPS。第三，我们在高并发吞吐上没有任何妥协，批大小为8时的峰值吞吐也提升了6–11%。

图8：随输入序列长度变化的消融（ablation）测试（模拟接受长度5以提高可复现性）。
图8的ISL消融结果直接说明了我们索引器优化的回报。在day-0路径上，DSA索引器必须对一个随上下文增长的得分行排序，所以它的开销随序列长度攀升，单位用户交互性随输入增长而迅速退化。TopK-V2显著缓解了那个瓶颈，让交互性一路基本保持平坦直到1M token。
下一步
这篇博客主要关注低并发、高缓存命中率场景下的优化。未来，我们会把支持扩展到更高并发的场景：
为更重负载打造更好的内核：用于prefill的ragged TopK-V2，更快的MQA logits内核（用于索引器）。
在智能体负载下优化PD分离（PD Disaggregation）和专家并行（Expert Parallel）技术。
用HiCache、HiSparse和LayerSplit技术改善缓存使用。
为GLM 5.2支持DSpark，它有助于在大并发下提升投机解码的接受率。
致谢
我们要向以下为GLM 5.2 NVFP4模型的支持与优化做出贡献的组织和个人表达谢意。
SGLang社区/RadixArk：Khoa Pham、Baizhou Zhang、Jimmy Shong、Brayden Zhong、Ziyi Xu、Mohammad Miadh Angkad、Xinyuan Tong、Zhendong Hua、Zijie Xia、Banghua Zhu以及许多其他人，负责优化与基准测试。
Nvidia：Julien Lin、Zhiyu Cheng、Po-Han Huang、Ryan Stewart、Triston Cao以及许多其他人，负责GLM5.2 NVFP4的Day-0支持。
GLM团队：Yuxuan Zhang，负责在SGLang中实现并验证IndexShare。
附录：复现
要复现性能结果，请参考此分支下的自定义脚本。我们使用SGLang v0.5.15.post1作为服务环境，并使用evalscope作为基准测试客户端。
在负载方面，我们采用OpenHands多轮智能体回放，平均输入约80k token/请求、每轮输出220 token、每轮对话13轮、约92% 的整体前缀缓存命中率，并且使用真实的EAGLE投机接受（speculative acceptance），无模拟。

结语

两周内把day-0的GLM-5.2 NVFP4服务从「能跑」推到500+ TPS，SGLang这次优化的主线非常清晰：把所有被CPU调度、内核启动、访存等待吃掉的时间，逐项还给了GPU计算。值得注意的关键判断是：加速几乎全部来自容量与调度的改善，而不是单点暴力。Spec V2吃掉气泡、IndexShare避免重复计算、TopK-V2把排序降格为选择、前导融合砍掉启动开销，而每一处省下的都是原本就不存在于计算里的浪费。对做推理服务的团队来说，这篇文章最有价值的不是某个具体内核，而是它的方法论：先用day-0栈跑通正确性，再用profiler找气泡和启动开销，按瓶颈逐层优化。这种「先跑通、再抠延迟」的路径，比一上来追求极致kernel更可复制。

【传送门】
【Agent for AI Infra三】摩尔线程MusaCoder国产算子生成超过Opus4.7：数据合成-SFT-RL全栈拆解
榨干GPU性能：流水线解码消除GPU气泡，推理吞吐提升35%
小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损集成
NVIDIA TriAttention解读: KV Cache压缩最大的问题不是算法而是两个Infra问题
小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读
TokenSpeed-Kernel：把推理内核做成一等公民
阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT
腾讯混元hy3大模型技术之TurnOPD：回合感知的在线策略蒸馏，长程Agent提速2.29倍
智谱GLM 5.2 RL: 单Rollout异步优化SAO稳定训练1000步全面超越GRPO
万亿参数RL实战：如何用28个H200节点训GLM-5
蚂蚁CausalMix: 将数据混合从超参搜索转换成因果推断
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
Google新论文RubricEM: 评分标准引导的深度研究Agent训练框架
Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍

参考：https://www.lmsys.org/blog/2026-07-13-glm52-optimization