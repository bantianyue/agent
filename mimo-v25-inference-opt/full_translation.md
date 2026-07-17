# Full-Pipeline Inference Optimization for MiMo-V2.5 Series: Pushing Hybrid SWA Efficiency to the Limit
# 小米 MiMo-V2.5 系列全链路推理优化：把混合 SWA 效率推到极限

> 逐句对照完整中文翻译。原文 = arxiv 2607.13095v1。

---

## Title / 标题

EN: Full-Pipeline Inference Optimization for MiMo-V2.5 Series: Pushing Hybrid SWA Efficiency to the Limit
中: 小米 MiMo-V2.5 系列全链路推理优化：把混合滑动窗口注意力（Hybrid SWA）的效率推到极限

EN: MiMo Team, Xiaomi
中: 小米 MiMo 团队

---

## Abstract / 摘要

EN: We present a full-pipeline inference optimization for the MiMo-V2.5 model family, which combines Hybrid Sliding Window Attention (Hybrid SWA), sparse Mixture-of-Experts (MoE), and multimodal encoders.
中: 我们提出了面向 MiMo-V2.5 模型家族的全链路推理优化方案，该家族结合了混合滑动窗口注意力（Hybrid SWA）、稀疏专家混合（MoE）以及多模态编码器。

EN: While Hybrid SWA can ideally reduce both attention compute and KVCache storage significantly compared to Full Attention, realizing these gains in production requires substantial engineering effort.
中: 虽然理论上 Hybrid SWA 相比全注意力（Full Attention）能大幅降低注意力计算量和 KVCache 存储，但在生产环境中真正兑现这些收益，需要大量的工程投入。

EN: We systematically optimize the KVCache system with layerwise prefetch, SWA-aware prefix cache trees, and specialized placement strategies, achieving strict O(W) SWA storage and high cache hit rates.
中: 我们通过分层预取（layerwise prefetch）、SWA 感知的前缀缓存树（SWA-aware prefix cache trees）以及专用放置策略，系统性地优化了 KVCache 系统，实现了严格的 O(W) SWA 存储开销和较高的缓存命中率。

EN: We further build GCache, a high-performance distributed cache infrastructure with RDMA-optimized networking, and develop a KVCache-affinity router to reduce computation while preserving load balancing.
中: 我们进一步构建了 GCache——一个具备 RDMA 优化网络的高性能分布式缓存基础设施，并开发了 KVCache 亲和性路由器（KVCache-affinity router），在保持负载均衡的同时减少计算量。

EN: We also optimize for multimodal inputs, including GPU image preprocessing, parallel video decoding, and multimodal cache sharing.
中: 我们还针对多模态输入做了优化，包括 GPU 图像预处理、并行视频解码以及多模态缓存共享。

EN: Together, these optimizations constitute the first large-scale LLM serving system in production that efficiently covers the Hybrid SWA + MoE + multimodal composite architecture.
中: 综上，这些优化构成了业界首个高效覆盖「Hybrid SWA + MoE + 多模态」复合架构的大规模生产级 LLM 服务系统。

---

## 1 Introduction / 引言

EN: The MiMo-V2.5 model family, including MiMo-V2.5 and MiMo-V2.5-Pro, combines several architectural design choices: Hybrid Sliding Window Attention (Hybrid SWA) compresses KVCache storage to roughly 1/7 that of Full Attention; sparse MoE activation cuts per-token compute while preserving model capacity; and multimodal encoders enable cross-modal understanding across vision, audio, and video.
中: MiMo-V2.5 模型家族（包括 MiMo-V2.5 和 MiMo-V2.5-Pro）融合了若干架构设计选择：Hybrid SWA 把 KVCache 存储压缩到全注意力的约 1/7；稀疏 MoE 激活在保持模型容量的同时削减了每 token 的计算量；多模态编码器则实现了视觉、音频、视频跨模态理解。

EN: Together, these features give the MiMo-V2.5 series significant performance and efficiency potential in long-context and multimodal scenarios.
中: 这些特性共同赋予 MiMo-V2.5 系列在长上下文和多模态场景下的显著性能与效率潜力。

EN: From the outset, our goal was clear: train a model that is both powerful and efficient for long-context reasoning.
中: 从一开始我们的目标就很明确：训练一个既强大又高效、擅长长上下文推理的模型。

EN: These two objectives are inherently in tension.
中: 这两个目标本质上彼此冲突。

EN: Strong reasoning requires modeling long-range dependencies, which typically demands larger-scale attention computation and higher KVCache overhead.
中: 强推理能力需要对长程依赖建模，这通常要求更大规模的注意力计算和更高的 KVCache 开销。

EN: In traditional Full Attention architectures, both attention compute and KVCache storage grow rapidly with context length, making long-context training and inference prohibitively expensive.
中: 在传统全注意力架构中，注意力计算量和 KVCache 存储都随上下文长度快速膨胀，使长上下文训练和推理成本高到难以承受。

EN: Hybrid SWA works by interleaving local Sliding Window Attention (SWA) with global Full Attention across layers: most layers compute attention only within a local window, while a small number of key layers retain a global view.
中: Hybrid SWA 的做法是在各层之间交错安排局部滑动窗口注意力（SWA）与全局全注意力：大多数层只在局部窗口内计算注意力，而少数关键层保留全局视野。

EN: In theory, this structure reduces attention complexity to near-linear while preserving the ability to model long-range dependencies.
中: 理论上，这种结构把注意力复杂度降到近线性，同时保留了对长程依赖建模的能力。

EN: However, theoretical architectural advantages do not automatically translate into production efficiency.
中: 然而，理论上的架构优势并不会自动转化为生产环境的效率。

EN: Hybrid SWA introduces new complexity in managing KVCache hit rates, prefix matching, and maintaining dual-semantic consistency between Full Attention and SWA layers.
中: Hybrid SWA 在管理 KVCache 命中率、前缀匹配、以及维持全注意力层与 SWA 层之间的双语义一致性方面，引入了新的复杂性。

EN: Real engineering systems face further challenges — data movement across multi-level storage, misaligned async prefetch and scheduling, difficulty synchronizing distributed cache states — that prevent theoretical gains from being directly achieved.
中: 真实工程系统还面临更多挑战——多级存储间的数据搬运、异步预取与调度错位、分布式缓存状态难以同步——这些都阻碍了理论收益的直接兑现。

EN: Beyond Hybrid SWA, MoE imposes significant demands on distributed scheduling and load balancing, while the multimodal encoders remain a throughput bottleneck in large-image and long-video scenarios.
中: 除了 Hybrid SWA，MoE 对分布式调度和负载均衡提出了很高要求，而多模态编码器在大图、长视频场景下仍是吞吐瓶颈。

EN: Scheduling strategy and the Prefill/Decode execution pipeline also require careful optimization.
中: 调度策略以及 Prefill/Decode 执行流水线同样需要精细优化。

EN: This article presents an end-to-end engineering practice for the inference system of the MiMo-V2.5 series, covering KVCache management, tiered caching systems, SWA-aware prefix cache trees, scheduling strategies, Prefill/Decode execution pipelines, and multimodal optimizations — systematically realizing the architecture's theoretical efficiency potential (especially Hybrid SWA) in production.
中: 本文呈现了 MiMo-V2.5 系列推理系统的端到端工程实践，覆盖 KVCache 管理、分级缓存系统、SWA 感知前缀缓存树、调度策略、Prefill/Decode 执行流水线以及多模态优化——在生产环境中系统性兑现了该架构的理论效率潜力（尤其是 Hybrid SWA）。

---

## 2 Background / 背景

EN: Before diving into specific optimizations, let's first quantify the theoretical efficiency bounds of Hybrid SWA — the architectural rationale behind the design choice and the baseline against which all subsequent optimizations are measured.
中: 在深入具体优化之前，我们先量化 Hybrid SWA 的理论效率边界——这是该设计选择的架构依据，也是衡量后续所有优化的基线。

### 2.1 Compute Analysis / 计算量分析

EN: Taking MiMo-V2.5-Pro as an example, the model has 70 layers in total: 10 Full Attention layers and 60 SWA layers, with a sliding window size of 128.
中: 以 MiMo-V2.5-Pro 为例，该模型共 70 层：10 个全注意力层、60 个 SWA 层，滑动窗口大小为 128。

EN: Compared to Full Attention, the compute cost of Hybrid SWA is illustrated in the figure below.
中: 下图展示了相比全注意力，Hybrid SWA 的计算开销。

EN: SWA layers account for 6/7 of all layers, so the total compute of the Hybrid SWA architecture is roughly 1/7 that of Full Attention.
中: SWA 层占全部层数的 6/7，因此 Hybrid SWA 架构的总计算量约为全注意力的 1/7。

EN: In Chunked Prefill scenarios, where prefill is largely compute-bound, this directly translates to a proportional reduction in prefill cost.
中: 在分块 Prefill（Chunked Prefill）场景下，prefill 主要受计算约束，这直接等比转化为 prefill 成本的下降。

### 2.2 KVCache Storage Analysis / KVCache 存储分析

EN: Since SWA layers only need to retain KV within the sliding window — not for the full sequence — KVCache memory usage similarly drops close to 1/7.
中: 由于 SWA 层只需在滑动窗口内保留 KV（而非整条序列），KVCache 内存占用同样降到了接近 1/7。

EN: The decode phase is predominantly memory-bound, and its latency is proportional to the combined bytes read for model parameters and KVCache.
中: 解码阶段主要受内存带宽约束，其延迟与读取模型参数和 KVCache 的总字节数成正比。

EN: For long sequences, KVCache volume can far exceed model parameters, so the reduction in KVCache storage translates almost directly into a reduction in decode cost in long-sequence scenarios (except for models with sparse attention, which reduces per-token KV access).
中: 对于长序列，KVCache 体量可能远超模型参数，因此在长序列场景下，KVCache 存储的削减几乎直接转化为解码成本的下降（稀疏注意力模型会削减每 token 的 KV 访问，除外）。

EN: KVCache storage varies substantially across model architectures.
中: 不同模型架构的 KVCache 存储差异显著。

EN: Figure 2 compares representative models in two parameter-scale groups: models below 500B parameters and models above 500B parameters.
中: 图 2 在两个参数量级组内对比了代表性模型：500B 参数以下组与 500B 参数以上组。

EN: The model configurations are obtained from their official checkpoints.
中: 模型配置取自各自的官方 checkpoint。

EN: Within their respective groups, MiMo-V2.5 and MiMo-V2.5-Pro have the second-lowest estimated KV cache memory requirements, behind only DeepSeek-V4-Flash and DeepSeek-V4-Pro, respectively.
中: 在各自组内，MiMo-V2.5 和 MiMo-V2.5-Pro 的预估 KV 缓存内存需求均为第二低，仅分别高于 DeepSeek-V4-Flash 和 DeepSeek-V4-Pro。

EN: It is worth noting that actual cost differences do not strictly correspond to KVCache size ratios, as there are fixed compute and memory access costs independent of sequence length.
中: 值得注意的是，实际成本差异并非严格对应 KVCache 大小比例，因为存在与序列长度无关的固定计算和内存访问开销。

EN: However, in long-context scenarios, the overall trend holds: the gains are marginal for short sequences, but the longer the sequence, the greater the inference cost advantage.
中: 不过在长上下文场景下，整体趋势仍然成立：短序列收益有限，但序列越长，推理成本优势越大。
