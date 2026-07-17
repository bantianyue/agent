# 全文翻译（逐句对照）

**原文：** Thinking Machines Lab (TML) has released Inkling, an open-source transformer-based mixture-of-experts (MoE) model with 975B total parameters and 41B active parameters per token.
**翻译：** Thinking Machines Lab（TML）发布了 Inkling，一个开源的、基于 transformer 的混合专家（MoE）模型，总参数 975B，每 token 激活参数 41B。

**原文：** Its scale and strong benchmark results raise a practical serving challenge: delivering fast, efficient inference across accelerator platforms.
**翻译：** 它的规模与强劲的基准测试成绩带来了一个实际的部署挑战：如何跨加速器平台实现快速、高效的推理。

**原文：** TokenSpeed partnered with TML to deliver Day 0 inference support for Inkling.
**翻译：** TokenSpeed 与 TML 合作，为 Inkling 提供 Day 0（首发日）推理支持。

**原文：** TokenSpeed's modular architecture and unified kernel API enable support for both NVIDIA (G)B200/(G)B300 and AMD MI350X/MI355X in their native NVFP4 and MXFP4 formats, respectively.
**翻译：** TokenSpeed 的模块化架构与统一 kernel API，能够同时支持 NVIDIA (G)B200/(G)B300 与 AMD MI350X/MI355X，分别使用其原生的 NVFP4 与 MXFP4 格式。

**原文：** See the TokenSpeed deployment guide to get started.
**翻译：** 参见 TokenSpeed 部署指南开始上手。

**原文：** This post walks through Inkling's architecture and native FP4 checkpoints, the inference-engine and kernel work behind cross-platform support, and an early end-to-end performance snapshot.
**翻译：** 本文梳理 Inkling 的架构与原生 FP4 检查点、支撑跨平台支持的推理引擎与 kernel 工作，以及一个早期的端到端性能快照。

**原文：** We are continuing to optimize every layer of the stack—pushing tokens toward the speed of light.
**翻译：** 我们仍在持续优化技术栈的每一层——把 token 推向光速。

**原文：** Native MXFP4 weights for AMD.
**翻译：** 面向 AMD 的原生 MXFP4 权重。

**原文：** We used AMD Quark to produce and publish an Inkling MXFP4 checkpoint for MI350X/MI355X, providing an AMD-native alternative to the NVFP4 release.
**翻译：** 我们使用 AMD Quark 生成并发布了面向 MI350X/MI355X 的 Inkling MXFP4 检查点，提供了 NVFP4 版本的 AMD 原生替代方案。

**原文：** A flat KV cache architecture for increasingly complex attention.
**翻译：** 面向日益复杂注意力的扁平 KV 缓存架构。

**原文：** We designed a flat cache layout with heterogeneous views for full attention, sliding-window attention, and convolution states, keeping allocation and scheduling unified without wasting memory on uniform page sizes.
**翻译：** 我们设计了一种扁平缓存布局，为全注意力、滑动窗口注意力与卷积状态提供异构视图，在保持分配与调度统一的同时，不会因统一页大小而浪费显存。

**原文：** Unified multi-silicon development with TokenSpeed Kernel.
**翻译：** 借助 TokenSpeed Kernel 实现统一的多芯片开发。

**原文：** One kernel API spans NVIDIA and AMD, letting us reuse model and integration logic, specialize only where it matters, and move quickly across accelerator architectures.
**翻译：** 一个 kernel API 横跨 NVIDIA 与 AMD，让我们可以复用模型与集成逻辑，只在关键处做专门优化，并快速迁移到不同加速器架构。

**原文：** A faster CuteDSL decode kernel for NVIDIA.
**翻译：** 面向 NVIDIA 的更快 CuteDSL 解码 kernel。

**原文：** We wrote a decode-specialized attention kernel that maps short-query, long-KV workloads onto the GPU more efficiently than a prefill-oriented path.
**翻译：** 我们编写了一个专用于解码的注意力 kernel，相比面向 prefill 的路径，它能更高效地把短查询、长 KV 的工作负载映射到 GPU 上。

**原文：** High-performance Gluon attention for AMD.
**翻译：** 面向 AMD 的高性能 Gluon 注意力。

**原文：** We built dedicated prefill and decode attention kernels in Gluon, using persistent prefill and split-K decode designs to deliver strong performance on AMD GPUs.
**翻译：** 我们在 Gluon 中构建了专用的 prefill 与 decode 注意力 kernel，采用 persistent prefill 与 split-K decode 设计，在 AMD GPU 上实现强劲性能。

**原文：** Model with Native FP4 Quantization
**翻译：** 原生 FP4 量化的模型

**原文：** Inkling is a transformer-based MoE model that interleaves full and sliding-window attention.
**翻译：** Inkling 是一个基于 transformer 的 MoE 模型，交替使用全注意力与滑动窗口注意力。

**原文：** The model comprises 66 layers with 256 routed experts, activating 6 routed experts and 2 shared experts per token, for a total of 975 billion parameters.
**翻译：** 模型共 66 层，含 256 个路由专家，每 token 激活 6 个路由专家与 2 个共享专家，总参数达 9750 亿。

**原文：** Its benchmark results are competitive with other open-source models:
**翻译：** 其基准测试成绩与其他开源模型相当：

**原文：** The reference checkpoint uses BF16, and an NVFP4-quantized version runs on NVIDIA GPUs.
**翻译：** 参考检查点使用 BF16，NVFP4 量化版本在 NVIDIA GPU 上运行。

**原文：** To support AMD GPUs, we used AMD Quark to quantize the model to MXFP4 for MI350X/MI355X and published the resulting checkpoint at lightseekorg/Inkling-MXFP4.
**翻译：** 为支持 AMD GPU，我们使用 AMD Quark 将模型量化为面向 MI350X/MI355X 的 MXFP4，并将生成的检查点发布于 lightseekorg/Inkling-MXFP4。

**原文：** In our evaluations, the NVFP4 and MXFP4 checkpoints stayed close to the BF16 baseline in quality while enabling higher serving performance:
**翻译：** 在我们的评测中，NVFP4 与 MXFP4 检查点在质量上接近 BF16 基线，同时实现了更高的服务性能：

**原文：** Accelerated Inference with Native Kernels
**翻译：** 借助原生 Kernel 加速推理

**原文：** TokenSpeed's modular architecture separates the model layer, scheduler, and kernel subsystems behind clear boundaries.
**翻译：** TokenSpeed 的模块化架构将模型层、调度器与 kernel 子系统在清晰边界后分离。

**原文：** Enabling Inkling is therefore a systematic process: we write accelerator-agnostic model logic, reuse the existing scheduler, and use the unified kernel API to bring up NVIDIA and AMD support from the same model integration.
**翻译：** 因此启用 Inkling 是一个系统性过程：我们编写与加速器无关（accelerator-agnostic）的模型逻辑，复用现有调度器，并用统一 kernel API 从同一套模型集成中同时拉起 NVIDIA 与 AMD 支持。

**原文：** From that common baseline, we add inference-engine techniques and native kernels tailored to each accelerator architecture.
**翻译：** 在这个共同基线之上，我们再加入针对每种加速器架构定制的推理引擎技术与原生 kernel。

**原文：** Flat cache layout for heterogeneous states
**翻译：** 面向异构状态的扁平缓存布局

**原文：** Inkling inference carries three persistent states: growing KV state for the full-attention layers, bounded KV state for the sliding-window layers, and window state for convolutions.
**翻译：** Inkling 推理携带三种持久状态：全注意力层不断增长的 KV 状态、滑动窗口层有界的 KV 状态，以及卷积的窗口状态。

**原文：** Maintaining a separate memory pool for each state would fragment cache memory and complicate scheduling.
**翻译：** 为每个状态维护独立的内存池会导致缓存内存碎片化，并使调度复杂化。

**原文：** A single pool with a uniform page shape, however, would pad smaller sliding-window and convolution entries to the footprint of the largest full-attention page.
**翻译：** 然而，单一池子配统一页形状，会把较小的滑动窗口与卷积条目填充到最大全注意力页的体积，造成浪费。

**原文：** TokenSpeed instead uses a single flat paged pool with heterogeneous views.
**翻译：** TokenSpeed 改用单一扁平分页池配合异构视图。

**原文：** Similar high-level principles have also been explored in recent community work such as Jenga in vLLM, which separates physical memory allocation from logical memory organization.
**翻译：** 类似的高层原则也在近期的社区工作中被探索，例如 vLLM 中的 Jenga，它将物理内存分配与逻辑内存组织分离。

**原文：** The figure below shows the resulting layout.
**翻译：** 下图展示了最终的布局。

**原文：** Inkling's 66 layers form 11 repeating units, each containing five sliding-window layers and one full-attention layer.
**翻译：** Inkling 的 66 层构成 11 个重复单元，每个单元含 5 个滑动窗口层与 1 个全注意力层。

**原文：** Alongside six KV convolutions and six hidden-state convolutions, each unit maps to one slab.
**翻译：** 连同 6 个 KV 卷积与 6 个隐状态卷积，每个单元映射到一个 slab（条带）。

**原文：** A block ID selects the same fixed-size slot across all 11 slabs.
**翻译：** 一个 block ID 在所有 11 个 slab 中选择相同大小的固定槽位。

**原文：** Because the states have different per-token footprints, that slot can hold 256 tokens of full-attention KV, 128 tokens of sliding-window KV or KV-side convolution state, or 16 tokens of hidden-state convolution state.
**翻译：** 由于各状态每 token 占用不同，该槽位可容纳 256 个 token 的全注意力 KV、128 个 token 的滑动窗口 KV 或 KV 侧卷积状态，或 16 个 token 的隐状态卷积状态。

**原文：** This keeps the allocation unit uniform without forcing the logical page sizes to be uniform.
**翻译：** 这保持了分配单元统一，又不必强制逻辑页大小也统一。

**原文：** The figure below shows the cache-management hierarchy.
**翻译：** 下图展示了缓存管理层次结构。

**原文：** A coordinator fans each request out to the cache groups, and each group maintains its own per-request BlockTable.
**翻译：** 一个协调器把每个请求分发给各缓存组，每个组维护自己的按请求 BlockTable。

**原文：** Table entries hold reference-counted BlockRefs into one shared block pool, while page ID k maps directly to row k in the physical slabs.
**翻译：** 表项持有指向同一共享块池的引用计数 BlockRef，而 page ID k 直接映射到物理 slab 中的第 k 行。

**原文：** The group managers control matching and eviction policy, but memory ownership remains centralized, allowing freed pages to be reused across groups safely and immediately.
**翻译：** 组管理器控制匹配与淘汰策略，但内存所有权保持集中，使释放的页能被安全地、立即跨组复用。

**原文：** Together, the physical layout and management hierarchy provide heterogeneous cache views over one shared allocator and one scheduling model.
**翻译：** 物理布局与管理层次结构一起，在单一共享分配器与单一调度模型之上提供了异构缓存视图。

**原文：** CuteDSL attention for NVIDIA GPUs
**翻译：** 面向 NVIDIA GPU 的 CuteDSL 注意力

**原文：** Attention accounts for a significant share of Inkling's compute, but prefill and decode present very different kernel shapes.
**翻译：** 注意力占据了 Inkling 计算的很大一部分，但 prefill 与 decode 呈现出截然不同的 kernel 形态。

**原文：** During prefill, the query (Q) sequence is long, giving a FlashAttention-style kernel enough parallelism to tile along the Q sequence length.
**翻译：** 在 prefill 期间，查询（Q）序列很长，使 FlashAttention 风格的 kernel 有足够并行度沿 Q 序列长度分块。

**原文：** We therefore reuse TML's FlashAttention-4 (FA4) attention path for prefill, which was developed by Colfax Research.
**翻译：** 因此我们复用 TML 的 FlashAttention-4（FA4）注意力路径用于 prefill，该路径由 Colfax Research 开发。

**原文：** During decode, the query is typically only one or a few tokens while the KV cache can be very long.
**翻译：** 在 decode 期间，查询通常只有一或两个 token，而 KV 缓存可能非常长。

**原文：** A prefill-style kernel remains organized around large Q tiles, leaving many compute lanes underused.
**翻译：** 偏好 prefill 风格的 kernel 仍围绕大 Q 分块组织，导致许多计算通道未被充分利用。

**原文：** Our dedicated decode kernel instead streams over the long KV sequence and packs the small query/prediction dimension more efficiently into each CTA tile, improving GPU utilization for short-query decode.
**翻译：** 我们的专用 decode kernel 改为在长 KV 序列上流式处理，并把小的查询/预测维度更高效地打包进每个 CTA 分块，提升了短查询 decode 的 GPU 利用率。

**原文：** To support relative bias, which is applied before softmax, the FA4 prefill path uses a separate ShearingBias preprocessing kernel.
**翻译：** 为支持在 softmax 之前施加的相对偏置，FA4 prefill 路径使用了一个独立的 ShearingBias 预处理 kernel。

**原文：** Its cost can be amortized across many query rows.
**翻译：** 其开销可在众多查询行上摊薄。

**原文：** During decode, the query dimension is small enough to compute relative indices directly inside the online softmax loop.
**翻译：** 在 decode 期间，查询维度足够小，可直接在在线 softmax 循环内计算相对索引。

**原文：** Gluon attention for AMD GPUs
**翻译：** 面向 AMD GPU 的 Gluon 注意力

**原文：** For AMD GPUs, we extend TokenSpeed's existing Gluon attention kernels to cover Inkling's prefill and decode workloads.
**翻译：** 对 AMD GPU，我们扩展了 TokenSpeed 现有的 Gluon 注意力 kernel，以覆盖 Inkling 的 prefill 与 decode 工作负载。

**原文：** These kernels use a persistent loop for prefill and split-K for decode.
**翻译：** 这些 kernel 在 prefill 上使用 persistent 循环，在 decode 上使用 split-K。

**原文：** Because they implement the unified kernel API alongside the NVIDIA backend, the model code remains accelerator-neutral while the AMD path can use specialized, high-performance kernels with minimal integration work.
**翻译：** 因为它们与 NVIDIA 后端一同实现了统一 kernel API，模型代码保持与加速器无关（accelerator-neutral），而 AMD 路径能以最小集成工作量使用专门的、高性能的 kernel。

**原文：** End-to-End Performance Preview
**翻译：** 端到端性能预览

**原文：** On a multi-turn agentic workload with 50K+ token contexts, 10–15 turns per conversation, and an approximately 90% cache-hit rate, TokenSpeed runs Inkling NVFP4 on four NVIDIA B200 GPUs at 317 tokens/s per user at concurrency 1, with MTP (multi-token prediction, 3 draft steps) advancing about 3.3 tokens per iteration.
**翻译：** 在一个多轮 agentic 工作负载上（50K+ token 上下文、每次对话 10–15 轮、缓存命中率约 90%），TokenSpeed 在 4 张 NVIDIA B200 GPU 上以 NVFP4 运行 Inkling，在并发 1 时达到每用户 317 tokens/s，其中 MTP（多 token 预测，3 个 draft 步）每轮迭代推进约 3.3 个 token。

**原文：** With MTP off, the engine sustains 152 tokens/s per user at concurrency 1 (6.6 ms per iteration) and 122 tokens/s per user at concurrency 4, where system throughput reaches 40K tokens/s.
**翻译：** 关闭 MTP 时，引擎在并发 1 时维持每用户 152 tokens/s（每轮迭代 6.6 ms），在并发 4 时维持每用户 122 tokens/s，此时系统吞吐量达 40K tokens/s。

**原文：** At batch size 1, the 3/1/4, 5/1/6, and 8/1/9 MTP configurations—corresponding to 3, 5, and 8 draft steps—deliver 317.5, 342.5, and 354.6 tokens/s per user, respectively.
**翻译：** 在 batch size 1 时，3/1/4、5/1/6、8/1/9 三种 MTP 配置——分别对应 3、5、8 个 draft 步——分别带来每用户 317.5、342.5、354.6 tokens/s。

**原文：** Compared with 152.4 tokens/s with MTP off, they improve decode throughput by 2.08×, 2.25×, and 2.33×.
**翻译：** 相比关闭 MTP 时的 152.4 tokens/s，它们将 decode 吞吐提升了 2.08×、2.25× 与 2.33×。

**原文：** The MXFP4 checkpoint also makes it practical for agentic serving on AMD.
**翻译：** MXFP4 检查点也让在 AMD 上做 agentic 服务变得切实可行。

**原文：** It lets the 975B-parameter model run on four MI355X GPUs while preserving enough cache capacity for 50K+ token contexts and multi-turn conversations.
**翻译：** 它让这个 975B 参数的模型能在 4 张 MI355X GPU 上运行，同时保留足够缓存容量支撑 50K+ token 上下文与多轮对话。

**原文：** Moreover, as TokenSpeed keeps the model logic and scheduling separate from the kernel implementation, AMD can reuse the same MTP path as NVIDIA, without touching the model layer.
**翻译：** 此外，由于 TokenSpeed 将模型逻辑与调度同 kernel 实现分离，AMD 可以复用与 NVIDIA 相同的 MTP 路径，而无需改动模型层。

**原文：** In our early MI355X run, MTP raises per-user decode speed from 2.4x to 1.5x across batch sizes 1–4:
**翻译：** 在我们早期的 MI355X 运行中，在 batch size 1–4 范围内，MTP 将每用户 decode 速度从 2.4x 提升至 1.5x：

**原文：** These early B200 and MI355X results are a starting point.
**翻译：** 这些早期的 B200 与 MI355X 结果只是一个起点。

**原文：** We are continuing to optimize TokenSpeed's scheduling, cache management, and vendor-native kernels across NVIDIA and AMD—pushing tokens toward the speed of light.
**翻译：** 我们仍在持续优化 TokenSpeed 在 NVIDIA 与 AMD 上的调度、缓存管理与厂商原生 kernel——把 token 推向光速。
