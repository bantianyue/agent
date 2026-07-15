DATA = {
    "summary": [
        "8×B300 上达成 500+ TPS：SGLang 把 day-0 的 GLM-5.2 NVFP4 服务栈两周内优化到生产级。",
        "Spec V2 重叠调度消除 GPU 气泡，端到端 TPS 提升 11%。",
        "IndexShare 让 MTP 复用 DSA 索引器 top-k，长上下文下 draft 开销最多降 1.9 倍。",
        "TopK-V2 把 TopK 当选择问题，80K ISL 内核延迟降 2.33 倍，1M ISL 达 10.17 倍。",
        "索引器前导融合把内核数从 12 降到 4；CuteDSL BF16 GEMM 在解码小批量下胜 cuBLAS。",
    ],
    "lead": [
        "GLM-5.2 发布第一天，SGLang 就在 Blackwell 硬件上用 trtllm-gen 内核点亮了 NVFP4 服务。但 day-0 版本只是「能跑」，离生产级还差一口气。",
        "这篇博客复盘了 SGLang 团队在两周内做的一系列优化：从运行时调度到 CUDA 内核，把 8×B300 上的吞吐推到 500+ TPS，同时把长上下文的交互性几乎拉平。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "背景",
            "paras": [
                "GLM-5.2 保留了与早期 GLM 检查点相同的主干：在 DeepSeek-V3 风格的 MoE 之上叠加带稀疏注意力索引器（sparse-attention indexer）的 DSA。它新增了两个主要的架构改动：IndexShare（索引共享，用于 DSA）以及带 IndexShare 和 KVShare 的 MTP。",
                "SGLang 自发布第一天起就在（Grace）Blackwell 硬件上支持 GLM-5.2-NVFP4 检查点，对稀疏注意力和 MoE 都使用 trtllm-gen 内核。为了把这套 day-0 的栈转变为更快、更稳定、更贴近生产的服务路径，我们引入了以下一系列优化。",
            ],
        },
        {
            "type": "h3",
            "title": "零开销调度与 Spec v2",
            "paras": [
                "Spec V2 是 SGLang 针对投机解码（speculative decoding）的重叠运行时（overlap runtime）。当 GPU 在 forward 流上运行当前模型的前向计算时，它会在 plan 流上完成下一步的 KV 分配和元数据准备，从而把 CPU 开销隐藏在前向计算内部。",
                "我们最近默认开启了 Spec V2。理论上，重叠调度器（overlap scheduler）应当让 CPU 在当前这一步 GPU 仍在忙时处理下一步的簿记工作，使迭代之间几乎没有气泡（bubble）。实践中，要完全兑现重叠调度器和 Spec V2 的收益还需要几项优化：我们把 DSA 的 draft-extend 路径改为可 CUDA-graph 化，去掉了 DSA 的 seq_lens_cpu 以省去 D2H 同步，移除了残留的 H2D 同步，并把 _apply_cuda_graph_metadata 里零散的 eager 元数据操作融合起来。当这些 GPU 气泡消失后，我们看到了端到端 TPS 11% 的提升。",
            ],
        },
        {
            "type": "h3",
            "title": "SGLang 中的 IndexShare MTP",
            "paras": [
                "GLM-5.2 带有一个很强的 MTP head，接受长度（accept length）经常达到 5 以上，这在智能体编程（agentic coding）这类低延迟负载上带来显著的提速。为了正确实现 GLM-5.2 的 MTP 行为，我们对 SGLang 的投机解码运行时做了几处改动。",
                "首先，IndexShare 要求 SGLang 在多个 draft 步骤之间复用 DSA 索引器的 top-k：在 draft 第 0 步算出的 top-k 会被保留并传给后续步骤，使它们跳过重新计算索引器的过程。这在长上下文下把 draft 步骤的开销最多降低了约 1.9 倍，且对输出质量没有任何影响。",
                "其次，top-k 需要从正确的位置播种（seed），而在 SGLang 中这个位置是上一次 run_batch 迭代的 draft-extend。由于 Spec V2 是异步运行各步骤的，我们必须把这个种子（seed）通过重叠调度器的 relay buffer 传递，以免它在迭代之间丢失。",
            ],
        },
        {
            "type": "h3",
            "title": "TopK-V2",
            "paras": [
                "DSA 索引器把每个 query 转化为对历史 KV 位置的打分，然后挑选出得分最高的候选用于稀疏注意力。沿用我们在 DeepSeek-V4 博客中提出的“Lightning-TopK”设计，我们把原始的 DSA TopK-V1 内核升级为 TopK-V2，后者把 TopK 当作一个选择问题（selection problem）而非排序问题（sorting problem）来处理。",
                "TopK-V2 对短行和中行使用寄存器驻留（register-resident）或单 CTA 流式路径。对于长行，一组 8 个 CTA 构建本地 10-bit radix 直方图，并在 cluster 内归约以定位阈值 bin。",
                "一次 cluster 级的归约定位到第 2048 大得分所在的 bin；高于它的数值直接输出，而处于边界的候选则经历精确的 FP32 radix 选择。被选中的逻辑位置随后被翻译成物理索引器 KV-cache 槽位。内核随后在 FP32 边界处收集候选，并使用精确的 radix 决胜（tie-break）返回恰好 k 个条目，运行时支持的 k 最大可达 2048。",
                "一个规划内核（planning kernel）根据批次的序列长度分布选择 cluster 截止点（cutoff），并为持久化 cluster 池（persistent cluster pool）构建工作列表，因此这个计划在每个前向时生成，并在各 DSA 层之间复用。TopK-V2 的选择操作和页表变换（page-table transform）也被融合进单个内核以削减延迟。",
                "从基准结果看，TopK-V2 在 80K ISL 下把平均内核延迟从 40.7 µs 降到 17.5 µs，取得 2.33 倍提速。它的优势随上下文长度而增长，在 1M ISL 时达到 10.17 倍（延迟从 372.1 µs 降到 36.6 µs）。这个不断拉大的差距说明，TopK-V2 在长上下文负载上的扩展效率要高得多。",
            ],
        },
        {
            "type": "h3",
            "title": "Indexer Prologue Fusion（索引器前导融合）",
            "paras": [
                "DSA 索引器前导（prologue）准备两路数据流：一路是存放在索引器 KV cache 中的 key 表示，另一路是用于计算稀疏注意力候选的 query 表示。原始实现把它表达为一连串小内核和投影（projection）。",
                "在“融合前”的路径里，key 侧依次运行 wk、LayerNorm、RoPE、Hadamard 变换、FP8 量化以及 cache 存储；query 侧依次运行 wq_b、RoPE、Hadamard 变换、FP8 量化以及 head-gate 缩放。此外，weights_proj 是一个独立的投影，为逐头门控（per-head gate）提供输入。",
                "PR #27705 通过两种方式压缩这条依赖链：",
                "第一，它把 wk 和 weights_proj 融合成一个单一的 BF16 投影，命名为 wk_weights_proj。其输出被拆分成 key 激活值和原始的 head-gate 权重。这移除了索引器路径中一个小的 GEMM，并让 head-gate 权重能被融合后的 query 内核直接复用。",
                "第二，它融合了逐元素（elementwise）的尾部操作：",
                "key 路径：LayerNorm + RoPE + FP8 量化 + 分页索引器 KV cache 存储。",
                "query 路径：RoPE + FP8 量化 + head-gate 缩放。",
                "这张图展示了重要的调度后果。融合前，cache 存储位于 key 侧工作之后，拉长了关键路径（critical path）。融合后，key 侧可以作为包含存储在内的一个内核运行，而 query 侧作为另一个独立的融合内核运行。两侧可以重叠，于是索引器前导从一长串启动（launch）变成了一对更短、更干净的支路。内核总数从 12 降到 4。",
                "融合后的路径还去掉了 Hadamard 变换。对 Q 和 K 施加相同的正交变换（orthonormal transform）能在量化前保持它们的内积不变，因此它的主要影响落在量化表示上。融合后的路径改为直接量化未经变换的激活值。",
                "内核数量的减少直接转化为可测量的解码吞吐提升，尽管这个效应在小批量下更明显（因为此时启动开销占主导）。在批大小为 1 时，解码吞吐提升约 8%，因为索引器前导中那些访存受限（memory-bound）的内核消失了，且从 12 个内核坍缩到 4 个移除了关键路径中占比更大的一部分。在批大小为 128 时，提升较小但依然稳定，约为 5%。",
            ],
        },
        {
            "type": "h3",
            "title": "GEMM 内核改进",
            "paras": [
                "GLM-5.2 中并非每个矩阵乘法都运行在 NVFP4 上。为了保护精度，检查点的量化方案让注意力投影（attention projections）和共享专家 MLP（shared-expert MLP）保持 BF16，只把路由专家（routed experts）量化。PR #30117 为这些 BF16 层新增了一个可选的 CuTe DSL BF16 GEMM 后端，它源自 Flashinfer 的 TGV GEMM，专为这些 BF16 层打造。",
                "这个内核把工作切分到多个 warp 上并分配专门任务：有些 warp 只从内存加载数据，一个 warp 只做矩阵乘，少数 warp 只把结果写回。由于这些是同时运行的独立 warp，加载、计算和存储是重叠进行的，而不是一个接一个地发生。",
                "提速的真正来源在于这个内核对加载操作的流水线化程度有多激进。它不会只加载一块数据（tile）然后等它被用掉再去加载下一块，而是让相当于很多块的数据同时处于传输途中，并为此几乎用满了 GPU 的全部共享内存。在解码运行的小批量下，这些 GEMM 大部分时间都在等内存而非计算，所以内核能提前加载得越远，等待的时间就越少。这就是相对 cuBLAS 这类通用库的主要优势——后者流水线化更保守。",
                "一个调优步骤还会挑选最适合所运行形状的块大小（tile size），并且一个提前测得的启发式规则会在每次调用时决定是使用这个内核还是回退到 cuBLAS。",
                "其中两个 BF16 层在 TP4 下获益明显：融合后的 QKV 投影（M, 2624, 6144，跨 rank 复制）和注意力输出投影 o_proj（M, 6144, 4096，跨 rank 切分）。",
                "扫描整个解码范围 M=1 到 32：融合 QKV 投影在每个批大小下都胜出，相对 cuBLAS 平均 1.08 倍，峰值 1.13 倍。o_proj 在每个批大小下也胜出，平均 1.05 倍，峰值 1.08 倍。在批大小为 1 时，端到端解码提速约为 4%。",
            ],
        },
        {
            "type": "h2",
            "title": "性能结果",
            "paras": [
                "我们在图 7 中收集了 GLM NVFP4 模型在一个 OpenHands 多轮智能体编程负载上的性能结果。每轮对话以约 80K token 的提示开头，每轮输出约 220 个 token，共 13 轮。后续的轮次复用前缀，使整体缓存命中率达到约 92%。我们做了一次并发度扫描，并绘制每 GPU token 吞吐（tok/s/GPU）相对交互性（tok/s/user）的曲线。每张图固定了模型、GPU 系列、精度、负载、服务框架和服务模式，并用 SGLang 的不同版本与自身对比。",
                "有三件事很突出。第一，GLM-5.2 是一个比 GLM-5.1 高效得多的架构。在相同的 SGLang 版本上，GLM-5.2 在 4×GB300 和 8×B300 上分别带来了约 1.4 倍和 1.3 倍的单位用户交互性（per-GPU 吞吐）提升。这个收益来自把 IndexShare 应用到 DSA 层，以及改进了的 MTP head（它复用了 IndexShare 和 KVShare）。第二，自 day-0 以来，单位用户交互性提升了 18–34%。在批大小为 1 时，我们的优化大幅削减了每 token 开销，让我们在 8×B300 上达到了 500+ TPS。第三，我们在高并发吞吐上没有任何妥协，批大小为 8 时的峰值吞吐也提升了 6–11%。",
                "图 8 的 ISL 消融结果直接说明了我们索引器优化的回报。在 day-0 路径上，DSA 索引器必须对一个随上下文增长的得分行排序，所以它的开销随序列长度攀升，单位用户交互性随输入增长而迅速退化。TopK-V2 显著缓解了那个瓶颈，让交互性一路基本保持平坦直到 1M token。",
            ],
        },
        {
            "type": "h2",
            "title": "下一步",
            "paras": [
                "这篇博客主要关注低并发、高缓存命中率场景下的优化。未来，我们会把支持扩展到更高并发的场景：",
                "为更重负载打造更好的内核：用于 prefill 的 ragged TopK-V2，更快的 MQA logits 内核（用于索引器）。",
                "在智能体负载下优化 PD 分离（PD Disaggregation）和专家并行（Expert Parallel）技术。",
                "用 HiCache、HiSparse 和 LayerSplit 技术改善缓存使用。",
                "为 GLM 5.2 支持 DSpark，它有助于在大并发下提升投机解码的接受率。",
            ],
        },
        {
            "type": "h2",
            "title": "致谢",
            "paras": [
                "我们要向以下为 GLM 5.2 NVFP4 模型的支持与优化做出贡献的组织和个人表达谢意。",
                "SGLang 社区/RadixArk：Khoa Pham、Baizhou Zhang、Jimmy Shong、Brayden Zhong、Ziyi Xu、Mohammad Miadh Angkad、Xinyuan Tong、Zhendong Hua、Zijie Xia、Banghua Zhu 以及许多其他人——负责优化与基准测试。",
                "Nvidia：Julien Lin、Zhiyu Cheng、Po-Han Huang、Ryan Stewart、Triston Cao 以及许多其他人——负责 GLM5.2 NVFP4 的 Day-0 支持。",
                "GLM 团队：Yuxuan Zhang——负责在 SGLang 中实现并验证 IndexShare。",
            ],
        },
        {
            "type": "h2",
            "title": "附录：复现",
            "paras": [
                "要复现性能结果，请参考此分支下的自定义脚本。我们使用 SGLang v0.5.15.post1 作为服务环境，并使用 evalscope 作为基准测试客户端。",
                "在负载方面，我们采用 OpenHands 多轮智能体回放，平均输入约 80k token/请求、每轮输出 220 token、每轮对话 13 轮、约 92% 的整体前缀缓存命中率，并且使用真实的 EAGLE 投机接受（speculative acceptance），无模拟。",
            ],
        },
    ],
    "conclusion": [
        "两周内把 day-0 的 GLM-5.2 NVFP4 服务从「能跑」推到 500+ TPS，SGLang 这次优化的主线非常清晰：把所有被 CPU 调度、内核启动、访存等待吃掉的时间，逐项还给了 GPU 计算。",
        "值得注意的关键判断是：加速几乎全部来自容量与调度的改善，而不是单点暴力。Spec V2 吃掉气泡、IndexShare 避免重复计算、TopK-V2 把排序降格为选择、前导融合砍掉启动开销——每一处省下的都是原本就不存在于计算里的浪费。",
        "对做推理服务的团队来说，这篇文章最有价值的不是某个具体内核，而是它的方法论：先用 day-0 栈跑通正确性，再用 profiler 找气泡和启动开销，按瓶颈逐层优化。这种「先跑通、再抠延迟」的路径，比一上来追求极致 kernel 更可复制。",
    ],
    "reference_url": "https://www.lmsys.org/blog/2026-07-13-glm52-optimization",
    "caption_translations": {
        "fig07": "图5：DSA 索引器前导内核：融合前与融合后的对比。",
        "fig08": "图6：CuteDSL BF16 GEMM 相对 CuBLAS GEMM 的提速，跨不同批大小。",
    },
}
