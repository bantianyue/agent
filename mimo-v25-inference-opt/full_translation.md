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

---

## 3 KVCache System Refactor / KVCache 系统重构

EN: The MiMo-V2 and MiMo-V2.5 series were among the earliest models to adopt the Hybrid SWA architecture, but at the time, neither mainstream open-source inference frameworks nor caching systems offered complete SWA support.
中: MiMo-V2 和 MiMo-V2.5 系列是最早采用 Hybrid SWA 架构的模型之一，但在当时，主流开源推理框架和缓存系统都没有完整的 SWA 支持。

EN: When we launched the MiMo API, we chose SGLang v0.5.5 as the serving backend codebase — and immediately encountered a severe challenge.
中: 当我们上线 MiMo API 时，选择了 SGLang v0.5.5 作为服务后端代码库——并立刻遭遇了严峻挑战。

EN: In that version, SGLang's HiCache did not support SWA, or rather, early SWA support was implemented by storing the full KVCache to maintain compatibility.
中: 在那个版本中，SGLang 的 HiCache 不支持 SWA；更确切地说，早期 SWA 支持是通过存储完整 KVCache 来维持兼容性的。

EN: While there were some workarounds to make SWA more usable, we wanted to build a KVCache system with higher performance ceilings and better usability.
中: 尽管有一些 workaround 能让 SWA 更好用，但我们希望构建一个性能上限更高、可用性更好的 KVCache 系统。

### 3.1 SWA KVCache Management / SWA KVCache 管理

#### 3.1.1 KVCache Dual-Pool Design / KVCache 双池设计

EN: Hybrid SWA introduces a fundamental storage conflict: Full Attention layers require storing the full sequence KV (O(N)), while SWA layers only need to maintain KV within the sliding window (O(W)).
中: Hybrid SWA 带来一个根本性的存储冲突：全注意力层需要存储整条序列的 KV（O(N)），而 SWA 层只需要在滑动窗口内维护 KV（O(W)）。

EN: Under a traditional single KV pool design, the system must allocate GPU memory at O(N) for all layers, preventing the window sparsity of SWA from being leveraged — effectively degenerating into a near-full KVCache implementation.
中: 在传统的单一 KV 池设计下，系统必须为所有层按 O(N) 分配 GPU 内存，使 SWA 的窗口稀疏性无法被利用——实质上退化成近乎全量的 KVCache 实现。

EN: A natural solution is to split the KVCache into two independent pools for Full Attention and SWA, with unified abstraction at the system level.
中: 一个自然的解决方案是把 KVCache 拆分为全注意力和 SWA 两个独立池，在系统层做统一抽象。

EN: Physical layer: Maintain separate Full KV pool and SWA KV pool. The SWA pool is sized only for the window and supports independent eviction based on the window, strictly constraining SWA storage to O(W). This mechanism extends to L2 and L3 storage tiers as well.
中: 物理层：维护独立的 Full KV 池和 SWA KV 池。SWA 池只按窗口大小分配，并支持基于窗口的独立淘汰，严格将 SWA 存储约束在 O(W)。该机制同样延伸到 L2 和 L3 存储层级。

EN: Logical layer: Expose a single sequence view to upper layers (prefix tree, scheduler, transport protocol), with the Full Attention index as the authoritative reference and a Full → SWA mapping maintained for transparent tiered storage.
中: 逻辑层：向上层（前缀树、调度器、传输协议）暴露单一的序列视图，以全注意力索引为权威参照，并维护 Full → SWA 映射以实现透明的分级存储。

EN: Scheduling constraints: The system validates both Full KV and SWA KV capacity constraints when admitting requests, avoiding resource misallocation from single-dimensional checks.
中: 调度约束：系统在接入请求时同时校验 Full KV 与 SWA KV 的容量约束，避免单维度检查导致的资源错配。

EN: Data movement: Cross-tier transfers are performed based solely on the SWA mask, ensuring only valid window data is moved and avoiding redundant bandwidth consumption.
中: 数据搬运：跨层级传输仅依据 SWA mask 执行，确保只移动窗口内的有效数据，避免冗余带宽消耗。

EN: Through this design, SWA KVCache achieves strict O(W) storage constraints at the system level, improving overall KVCache capacity efficiency by approximately 7× and unlocking the structural advantages of Hybrid SWA.
中: 通过这一设计，SWA KVCache 在系统层面实现了严格的 O(W) 存储约束，将整体 KVCache 容量效率提升约 7 倍，释放了 Hybrid SWA 的结构性优势。

#### 3.1.2 Layerwise KVCache Prefetch / 分层 KVCache 预取

EN: With the SWA KVCache storage optimization in place, SWA layers only need to prefetch a minimal amount of KVCache.
中: 在 SWA KVCache 存储优化就位后，SWA 层只需预取极少量的 KVCache。

EN: This enables near-perfect overlap between Host-to-Device KVCache prefetch and computation through layerwise scheduling, bringing the cost of cache reads during inference close to zero.
中: 这通过分层调度实现了 Host-to-Device KVCache 预取与计算近乎完美的重叠，将推理期间缓存读取的成本降到接近零。

#### 3.1.3 SWA-Aware Prefix Cache Tree / SWA 感知的前缀缓存树

EN: The traditional RadixAttention hit rule is built on a simple assumption: equal token sequences → equal KV.
中: 传统的 RadixAttention 命中规则建立在一个简单假设上：token 序列相等 → KV 相等。

EN: This assumption holds under Full Attention — as long as two requests share the same token IDs, their corresponding KV is guaranteed to still be in the pool and directly reusable.
中: 这一假设在全注意力下成立——只要两个请求共享相同的 token ID，其对应的 KV 就保证仍在池中、可直接复用。

EN: But this assumption breaks under SWA.
中: 但在 SWA 下这一假设被打破。

EN: The reason is that the logical lifecycle of the prefix tree and the physical lifecycle of SWA KV are misaligned.
中: 原因在于前缀树的逻辑生命周期与 SWA KV 的物理生命周期彼此错位。

EN: Prefix tree node lengths are not constrained by the SWA window — a node's sequence length can be shorter than the window or far longer, and nodes change continuously through request merging, splitting, and removal.
中: 前缀树节点长度不受 SWA 窗口约束——节点序列长度可能短于窗口或远长于窗口，且节点会因请求合并、拆分、移除而不断变化。

EN: As a result, a prefix tree node may still logically represent a complete token sequence, but its corresponding SWA KV may have only the tail portion remaining, or may have been evicted entirely.
中: 结果，前缀树节点在逻辑上仍可能代表一条完整 token 序列，但其对应的 SWA KV 可能只剩尾部片段，或已被整体淘汰。

EN: If the prefix tree still provides reuse length based on the "token equality → hit" rule, the scheduler may receive a pseudo-hit with evicted tail KV — subsequent attention computation would read invalid or overwritten slots, directly degrading model correctness.
中: 若前缀树仍按「token 相等 → 命中」规则提供复用长度，调度器可能收到带已淘汰尾部 KV 的伪命中——后续注意力计算会读到无效或被覆盖的槽位，直接损害模型正确性。

EN: To keep prefix reuse correct and efficient under SWA, the prefix tree semantics must be revised in three ways.
中: 为在 SWA 下保持前缀复用的正确与高效，前缀树语义须从三方面修订。

EN: 1. Matching rules upgraded to "window-safe length": In addition to token equality, the tail W tokens must still have valid slots in the SWA pool. The match length is clipped to this new boundary — anything beyond it is treated as a miss. This ensures that KV retrieved from a hit segment is always valid.
中: 1. 匹配规则升级为「窗口安全长度」：除 token 相等外，尾部 W 个 token 在 SWA 池中仍须有有效槽位。匹配长度被裁剪到这一新边界——超出部分视为未命中。这保证从命中段取回的 KV 始终有效。

EN: 2. Eviction tied to request lifecycle: Completion of each chunk in long prefill, request termination, and every N generated tokens during decode all trigger an out-of-window SWA release. This keeps SWA pool usage constant at W or chunk-level magnitude during long-context/long-output tasks, rather than growing with sequence length.
中: 2. 淘汰绑定请求生命周期：长 prefill 每个 chunk 的完成、请求终止、以及解码阶段每生成 N 个 token，都会触发窗口外 SWA 释放。这使长上下文/长输出任务中 SWA 池用量恒定在 W 或 chunk 级量级，而非随序列长度增长。

EN: 3. Nodes carry dual indices: Each prefix tree node records two sets of information — the Full Attention segment index (determining logical order, participating in Full Attention layer computation) and the SWA segment mapping (determining window safety). Eviction is managed separately: window-outside SWA segments can be evicted independently while preserving Full Attention segments (keeping the prefix reusable by Full Attention layers), or the entire segment can be evicted.
中: 3. 节点携带双索引：每个前缀树节点记录两类信息——全注意力段索引（决定逻辑顺序，参与全注意力层计算）和 SWA 段映射（决定窗口安全性）。淘汰分开管理：窗口外的 SWA 段可独立淘汰而保留全注意力段（使前缀仍可被全注意力层复用），也可整体淘汰。

EN: SWA's compression of KV volume to 1/7 is a capacity-level benefit, while hit rate is a reuse-level benefit. Together, they determine the actual prefill compute cost curve.
中: SWA 把 KV 体量压缩到 1/7 是容量级收益，而命中率是复用级收益。二者共同决定了实际的 prefill 计算成本曲线。

EN: After introducing the "window-safe length" matching rule, the raw hit rate for a given token capacity decreases slightly — but the number of tokens that fit within the same storage budget grows several-fold. Measured against a fixed storage budget, the effective hit rate improves dramatically.
中: 引入「窗口安全长度」匹配规则后，给定 token 容量下的原始命中率略有下降——但同等存储预算下可容纳的 token 数成倍增长。以固定存储预算衡量，有效命中率大幅提升。

#### 3.1.4 KVCache Hit Rate Optimization / KVCache 命中率优化

EN: After all three HiCache tiers are refactored to be SWA-aware, the device, host, and storage backend each maintain their own state of "which positions have valid SWA." However, HiCache's data movement pipeline is asynchronous, caches across deployments differ, and shared prefix lengths across sessions also vary; the Full Attention Cache and valid SWA indices across tiers can easily fall out of sync.
中: 在三个 HiCache 层级全部重构为 SWA 感知后，device、host 与存储后端各自维护「哪些位置有有效 SWA」的状态。但 HiCache 的数据搬运流水线是异步的，各部署的缓存不同，跨会话共享前缀长度也不同；各层级的 Full Attention Cache 与有效 SWA 索引很容易失同步。

EN: According to the SWA-aware prefix cache tree matching rules, if a sequence hits on the Full Attention Cache but misses on the SWA Cache, severe match-length truncation occurs: the more truncation, the longer the recomputation needed, and the lower the SWA Cache optimization effectiveness. We therefore optimized distributed consistency and cache hit rates across different scenarios.
中: 按 SWA 感知前缀缓存树的匹配规则，若某序列在 Full Attention Cache 命中、却在 SWA Cache 未命中，就会出现严重的匹配长度截断：截断越多，需重算的部分越长，SWA Cache 优化效果越差。因此我们针对分布式一致性与各场景下的缓存命中率做了优化。

EN: Device complete, Host deficient. When L3→L2 prefetch only pulls in the tail segment due to bandwidth-latency tradeoffs, or when L1 prefix tree reorganization is not synced to L2/L3, this scenario arises. We proactively check the delta in SWA occupancy between device and host at timing points such as prefix tree node merging and prefill completion, allocate supplementary slots in the host's SWA pool, and asynchronously write device SWA KV via D2H transfer.
中: 「Device 完整、Host 不足」。当 L3→L2 预取因带宽-延迟权衡只拉入尾部段，或 L1 前缀树重组未同步到 L2/L3 时，就会出现这种情形。我们在前缀树节点合并、prefill 完成等时点主动检查 device 与 host 间 SWA 占用的差值，在 host 的 SWA 池中分配补充槽位，并通过 D2H 传输异步写回 device SWA KV。

EN: Host complete, Device deficient. Naturally aligns at the next H2D transfer — no active repair needed.
中: 「Host 完整、Device 不足」。会在下一次 H2D 传输时自然对齐——无需主动修复。

EN: High-frequency sequence L3 prefix eviction. Long sequence heads persist in L1/L2 due to high-frequency access, and cache affinity routes same-prefix requests to the same node. The L3 cache, due to long periods without direct access, may be evicted by the storage eviction policy — prematurely releasing L3 Cache for globally high-frequency sequences and severely degrading cross-machine reuse. We periodically query L3 Cache when accessing L1/L2 Cache to prevent premature eviction.
中: 高频序列 L3 前缀淘汰。长序列头因高频访问常驻 L1/L2，缓存亲和性把同前缀请求路由到同一节点。L3 缓存因长时间无直接访问，可能被存储淘汰策略驱逐——过早释放全局高频序列的 L3 缓存，严重拖垮跨机复用。我们在访问 L1/L2 缓存时周期性查询 L3，以防其被过早淘汰。

EN: Medium/short sequence SWA retention strategy. Based on user request patterns, we retain relatively dense SWA KV Cache at fixed length positions for medium/short sequences. Although increasing SWA density raises the SWA ratio in overall KVCache, it directly benefits scenarios like multi-user shared system prompts.
中: 中/短序列 SWA 保留策略。基于用户请求模式，我们在固定长度位置为中短序列保留较密集的 SWA KV Cache。尽管提高 SWA 密度会增加整体 KVCache 中的 SWA 占比，但能直接利好多用户共享系统提示词等场景。

EN: Through these optimizations, we convert KVCache capacity expansion into longer effective hit lengths, making cross-session long-prefix reuse possible — particularly beneficial for long agent sessions, multi-user shared system prompts, and repeated tool calls to the same codebase.
中: 通过这些优化，我们把 KVCache 容量扩张转化为更长的有效命中长度，使跨会话长前缀复用成为可能——对长 agent 会话、多用户共享系统提示词、以及对同一代码库的重复工具调用尤其有益。

### 3.2 GCache: High-Performance Distributed Cache Infrastructure / GCache：高性能分布式缓存基础设施

EN: GCache is a high-performance general-purpose cache system developed by the Xiaomi storage team, forming a critical part of unified training-inference storage architecture.
中: GCache 是小米存储团队开发的高性能通用缓存系统，是统一训练-推理存储架构的关键组成部分。

EN: Early on, during training scenarios, the storage team recognized that certain open-source caching projects provided limited acceleration for distributed file systems and could not fully exploit performance potential, so they began developing an in-house solution.
中: 早先在训练场景中，存储团队认识到某些开源缓存项目对分布式文件系统加速有限、无法充分释放性能潜力，于是开始自研方案。

EN: Later, with the release of the MiMo large model and the launch of inference services, the team adapted GCache into an independent storage product for model distribution and as the L3 KVCache for the inference engine.
中: 后来，随着 MiMo 大模型发布和推理服务上线，团队把 GCache 改造为独立的存储产品，用于模型分发，并作为推理引擎的 L3 KVCache。

EN: GCache supports both file and KV semantics, multi-level caching across memory/disk/remote tiers, shared-memory persistence and full-path zero-copy, high-concurrency non-blocking IO and RDMA communication, meeting upper-layer services requirements for high throughput and low latency while maintaining excellent scalability.
中: GCache 同时支持文件与 KV 语义、跨内存/磁盘/远程的多级缓存、共享内存持久化与全路径零拷贝、高并发非阻塞 IO 和 RDMA 通信，在满足上层服务高吞吐、低延迟需求的同时保持优异的可扩展性。

#### 3.2.1 Architecture Design / 架构设计

EN: The overall architecture of GCache is shown in Figure 5. GCache has several key features.
中: GCache 的整体架构如图 5 所示。GCache 有几个关键特性。

EN: 1. Decentralized metadata management enables unlimited cluster scaling: Consistent hashing on keys determines storage locations. The Master uses a Raft-based highly-available deployment, but only manages heartbeats and service discovery — IO paths do not pass through the Master.
中: 1. 去中心化元数据管理支持集群无限扩展：对 key 做一致性哈希决定存储位置。Master 采用基于 Raft 的高可用部署，但只管理心跳和服务发现——IO 路径不经过 Master。

EN: 2. Server-side support for both memory and disk caching: Cold data in memory is evicted to disk; hot data on disk is promoted to memory. This approach is highly favorable for inference scenarios, automatically guaranteeing active session performance while reducing costs for long-idle sessions. Cache entries persist to shared memory — no cache loss on service restart. Supports smooth scale-up or scale-down without cache loss.
中: 2. 服务端同时支持内存与磁盘缓存：内存中的冷数据被驱逐到磁盘，磁盘上的热数据被提升回内存。这种方式对推理场景极有利，自动保障活跃会话性能、同时降低长期空闲会话的成本。缓存条目持久化到共享内存——服务重启不丢缓存。支持平滑扩缩容且不丢缓存。

EN: 3. Multi-language SDK with dedicated threads for request slicing and dispatch: These threads do not consume user thread resources; slicing improves concurrency and keeps IO sizes within RDMA-friendly ranges. Threads use async callbacks with flexible callback granularity — single KV level, batch level, or CUDA stream level.
中: 3. 多语言 SDK，配备专用于请求分片与分发的线程：这些线程不占用用户线程资源；分片提升并发、并使 IO 大小保持在 RDMA 友好的区间。线程采用异步回调，回调粒度灵活——可到单 KV 级、批级或 CUDA stream 级。

#### 3.2.2 Network Optimization / 网络优化

EN: Current mainstream GPU machines are equipped with 8× 400G high-performance NICs. However, even with Prefill-Decode (PD)-disaggregated deployment, current inference frameworks struggle to saturate network bandwidth — to the point where the industry is calling for reduced NIC specifications to cut costs.
中: 当前主流 GPU 机器配备 8×400G 高性能网卡。然而即便采用 Prefill-Decode（PD）分离部署，当前推理框架仍难以打满网络带宽——以至于业界开始呼吁降低网卡规格以降本。

EN: To fully exploit high-speed networking, GCache prioritizes GPU NICs over frontend NICs for communication and performs extensive optimizations in the communication module, including NUMA binding and same-rail affinity.
中: 为充分挖掘高速网络，GCache 在通信时优先使用 GPU 网卡而非前端网卡，并在通信模块做了大量优化，包括 NUMA 绑定与同轨亲和（same-rail affinity）。

EN: In benchmarks, with 1MB IO sizes, single-process RDMA read throughput reaches 170 GB/s at only 280 μs latency; under GDR scenarios, due to higher HBM bandwidth, single-process throughput reaches approximately 350 GB/s — more than sufficient for inference framework communication requirements.
中: 基准测试中，在 1MB IO 下，单进程 RDMA 读取吞吐达 170 GB/s、延迟仅 280μs；在 GDR 场景下，由于 HBM 带宽更高，单进程吞吐约 350 GB/s——完全满足推理框架的通信需求。

#### 3.2.3 Storage Cost Optimization / 存储成本优化

EN: 2026 has seen growing industry concern about storage costs. Unlike other vendors using dedicated storage machines, GCache prioritizes co-deployment on GPU machines, taking over a portion of the memory from Prefill and Decode nodes along with the machines' built-in NVMe SSDs — achieving zero additional storage cost.
中: 2026 年业界对存储成本的关注度持续上升。与其他厂商使用专用存储机器不同，GCache 优先与 GPU 机器共部署，接管 Prefill 和 Decode 节点的一部分内存及其内置 NVMe SSD——实现了零额外存储成本。

#### 3.2.4 Reliability Assurance / 可靠性保障

EN: Due to co-deployment, the high failure rate of GPU machines poses a reliability challenge. Since launch, GCache has experienced host machine failures nearly every day.
中: 由于共部署，GPU 机器的高故障率带来了可靠性挑战。自上线以来，GCache 几乎每天都会遇到宿主机故障。

EN: First, the team expended substantial effort hardening fault-handling logic.
中: 首先，团队投入大量精力加固故障处理逻辑。

EN: Second, since keys are fully distributed via consistent hashing, pre-grouping session IDs into logical sets ensures related sessions are spread across different nodes, reducing the blast radius of any single-node failure.
中: 其次，由于 key 经一致性哈希完全打散，把 session ID 预分组为逻辑集合，可确保相关会话分散在不同节点，缩小单节点故障的爆炸半径。

EN: Third, leveraging hardware detection capabilities from the underlying platform enables proactive fault discovery and automated data migration.
中: 第三，借助底层平台的硬件检测能力，可实现主动故障发现和自动数据迁移。

EN: For the rare sudden crashes that cannot be handled proactively, a short SDK timeout allows the inference framework to promptly detect misses and recompute, keeping online inference largely unaffected.
中: 对于少数无法主动处理的突发崩溃，较短的 SDK 超时让推理框架能及时察觉未命中并重算，使在线推理基本不受影响。

EN: Based on these efforts, GCache maintains single-replica storage under co-deployment, without needing multi-replica redundancy for availability — a key factor in its low storage cost.
中: 基于上述努力，GCache 在共部署下维持单副本存储，无需为多副本冗余牺牲可用性——这正是其存储成本低的关键。

### 3.3 Discussion on Cache Hit Rate / 缓存命中率讨论

EN: Thanks to the SWA KVCache optimizations described above — lower storage footprint combined with a more stable, large-capacity GCache as L3 storage — we were able to significantly extend Cache TTL (Time-To-Live) and improve KV Cache hit rates.
中: 得益于上述 SWA KVCache 优化——更小的存储足迹，叠加更稳定、大容量的 GCache 作 L3 存储——我们得以显著延长缓存 TTL（生存时间）并提升 KV Cache 命中率。

EN: KVCache eviction fundamentally stems from storage capacity constraints. As capacity nears saturation, the system prioritizes retaining KV Cache from new requests and evicts previously-accessed entries using LRU-like policies — directly causing a given context to often miss when reused hours later.
中: KVCache 淘汰根本源于存储容量约束。当容量接近饱和，系统优先保留新请求的 KV Cache，并用类 LRU 策略驱逐曾访问过的条目——直接导致某上下文在数小时后复用时常常未命中。

EN: SWA's minimal storage footprint enables the same cost to hold several times more concurrent request caches, while large-capacity L3 further expands available capacity at low cost. The more storage space available, the less pressure on KVCache eviction, and the longer the retention duration.
中: SWA 极小的存储足迹使同等成本能容纳数倍的并发请求缓存，而大容量 L3 进一步以低成本扩张可用容量。可用存储越多，KVCache 淘汰压力越小，保留时长越长。

EN: Longer TTL widens the hit window for historical contexts, and cache hit rates rise accordingly. Additionally, SWA's reduced bandwidth transfer overhead, while not directly affecting TTL, significantly lowers cross-tier data movement costs, ensuring stable and efficient operation of the entire caching system.
中: 更长的 TTL 拓宽了历史上下文的命中窗口，缓存命中率随之上升。此外，SWA 降低的带宽传输开销虽不直接作用于 TTL，却显著削减了跨层级数据搬运成本，保障整个缓存系统稳定高效运行。

EN: Since model launch, we have continuously observed on the server side: under mainstream high-quality harness frameworks, server-side KV Cache hit rates average 93%; for heavy users with sustained high-intensity usage, this metric climbs even higher, reaching 95% or above.
中: 自模型上线以来，我们在服务端持续观察到：在主流高质量 harness 框架（评测框架）下，服务端 KV Cache 命中率平均为 93%；对持续高强度使用的重度用户，这一指标更高，达 95% 以上。

EN: Going forward, we will continue iterating SWA's KV Cache management logic and collaborate with more harness frameworks on harness-inference co-design to further optimize the hit rate ceiling.
中: 未来我们将持续迭代 SWA 的 KV Cache 管理逻辑，并与更多 harness 框架在「评测-推理协同设计」上合作，进一步优化命中率上限。

---

## 4 Scheduling Optimization / 调度优化

EN: In its early stages, the SGLang community's router service was not yet fully mature, with no shared state across instances. If a router service failed unexpectedly or requests were routed to a different router instance, KVCache scheduling would degrade.
中: 在早期阶段，SGLang 社区的路由器服务尚不成熟，实例间没有共享状态。若路由器服务意外故障、或请求被路由到不同路由器实例，KVCache 调度就会退化。

EN: To solve this problem and ensure high availability in large-scale cluster deployments, Xiaomi developed LLM-Router — a dynamically scalable stateless scheduler using Redis as centralized storage, eliminating KVCache degradation after single-service failures and consistently guaranteeing cache hit rates.
中: 为解决该问题、保障大规模集群部署的高可用，小米开发了 LLM-Router——一个使用 Redis 作集中存储、可动态扩缩容的无状态调度器，消除了单服务故障后的 KVCache 退化，持续保障缓存命中率。

### 4.1 KVCache and Load-Affinity Scheduling / KVCache 与负载亲和调度

EN: HiCache is highly sensitive to L2 hit rates. When L2 cache misses, the system must look up and fetch KVCache from L3, waiting for the fetch to complete before inference can begin. Improving L2 hit rates on the router side reduces unnecessary synchronous waits, directly boosting throughput.
中: HiCache 对 L2 命中率高度敏感。当 L2 缓存未命中，系统须从 L3 查找并拉取 KVCache，等待拉取完成才能开始推理。在路由器侧提升 L2 命中率能减少不必要的同步等待，直接提升吞吐。

EN: The router implements KVCache affinity scheduling by maintaining dispatched requests in a Radix prefix tree. Among multiple Prefill instances, it prioritizes nodes that have already cached the current request's prefix while simultaneously balancing load to avoid load skew toward hotspots.
中: 路由器通过在 Radix 前缀树中维护已分发请求，实现 KVCache 亲和调度。在多个 Prefill 实例间，它优先选择已缓存当前请求前缀的节点，同时均衡负载以避免热点倾斜。

EN: After deployment, this strategy improved L2 cache hit rates by approximately 25% and per-node input throughput by approximately 30%. The core formula is roughly as follows.
中: 部署后，该策略使 L2 缓存命中率提升约 25%、单节点输入吞吐提升约 30%。其核心公式大致如下。

### 4.2 TTFT Optimization / TTFT 优化

EN: When model services experience queuing, the traditional FCFS (First Come First Serve) strategy does not consider the priority relationship between requests with higher and lower cache hit rates.
中: 当模型服务出现排队，传统的 FCFS（先到先服务）策略不会考虑高/低缓存命中率请求之间的优先级关系。

EN: Requests that have a higher cache hit rate but require less computation may end up waiting for lower-hit-rate requests to finish inference, causing TTFT P99 to become abnormally long and dragging down average throughput.
中: 命中率更高但计算量更小的请求，可能被迫等待低命中率请求完成推理，导致 TTFT P99 异常拉长、拉低平均吞吐。

EN: To address this, the router gives priority to requests with fewer uncached tokens when scheduling from the waiting queue, preventing cache-friendly requests from being blocked by slower ones and the resulting P99 degradation.
中: 为此，路由器从等待队列调度时优先选择未缓存 token 更少的请求，避免缓存友好型请求被慢请求阻塞、进而造成 P99 劣化。

EN: However, this strategy can lead to starvation of certain requests, so we added a wait-time penalty mechanism to mitigate starvation.
中: 但该策略可能导致某些请求饿死，因此我们加入了等待时间惩罚机制以缓解饿死。

EN: As shown in Figure 6, our results show that this strategy does not degrade service quality for shorter requests, while reducing TTFT P90 by up to 30% for longer ones.
中: 如图 6 所示，结果表明该策略不会降低短请求的服务质量，同时把长请求的 TTFT P90 最多降低 30%。

---

## 5 Prefill Optimization / Prefill 优化

### 5.1 Parallelism Configuration / 并行配置

EN: In theory, a smaller EP (Expert Parallelism) during the prefill stage yields better performance and throughput, in three ways: smaller cross-machine footprint and lower communication overhead; fewer DP (Data Parallelism) instances, reducing the attention load imbalance between DPs; and more experts per machine, improving MoE load balance.
中: 理论上，prefill 阶段更小的 EP（专家并行）能带来更好的性能与吞吐，体现在三方面：更小的跨机 footprint 与更低通信开销；更少的 DP（数据并行）实例，减轻 DP 间的注意力负载不均衡；以及每台机器更多专家，改善 MoE 负载均衡。

EN: However, EP size is constrained by GPU memory, which must accommodate both model parameters and KVCache.
中: 但 EP 大小受 GPU 内存约束——它须同时容纳模型参数和 KVCache。

EN: Previously, the SWA KVCache required storing KVCache for all tokens, forcing EP to be larger; after optimization, only tokens within the SWA window need to be stored, allowing us to reduce EP to half its original size, improving end-to-end performance by approximately 40%.
中: 此前 SWA KVCache 须为所有 token 存储 KV，迫使 EP 更大；优化后只需存储窗口内 token，使我们能把 EP 降到原来的一半，端到端性能提升约 40%。

EN: Going forward, we will continue exploring PP (Pipeline Parallelism) optimizations for the Hybrid SWA structure to further reduce EP size and improve overall throughput.
中: 未来我们将继续探索针对 Hybrid SWA 结构的 PP（流水线并行）优化，进一步缩小 EP、提升整体吞吐。

### 5.2 Length Bucketing Strategy / 长度分桶策略

EN: The MiMo-V2.5 series' hybrid architecture significantly improves compute efficiency over pure GQA, but throughput still degrades noticeably as sequence length increases. Figure 7 shows throughput in Chunked Prefill with a fixed 16K-token compute chunk and prefixes of varying lengths.
中: MiMo-V2.5 系列的混合并行架构比纯 GQA 显著提升了计算效率，但吞吐仍随序列长度增加明显退化。图 7 展示了固定 16K-token 计算块、不同前缀长度下分块 Prefill 的吞吐。

EN: In agentic scenarios, ultra-long requests mostly originate from multi-turn agent interactions with substantial prefix caches.
中: 在 agent 场景中，超长请求大多来自带有大量前缀缓存的多轮 agent 交互。

EN: When requests with significantly different lengths are scheduled to the same model instance, short requests are bottlenecked by long ones, degrading overall throughput in two main scenarios.
中: 当长度差异显著的请求被调度到同一模型实例时，短请求被长请求拖慢，在两类场景下拖累整体吞吐。

EN: 1. DP-Attention synchronization: After each layer's attention computation, multiple DPs must synchronize via collective communication before entering the MoE stage. If long and short requests coexist across DPs in the same EP group, short requests are slowed by long requests' computation.
中: 1. DP-Attention 同步：每层注意力计算后，多个 DP 须通过集合通信同步，才能进入 MoE 阶段。若长短请求在同一 EP 组内跨 DP 共存，短请求会被长请求的计算拖慢。

EN: 2. Chunked Prefill interference: When requests with different prefix lengths are batched into the same chunk, short-prefix requests are dragged down by long-prefix requests' computation.
中: 2. 分块 Prefill 干扰：当不同前缀长度的请求被批量放入同一 chunk，短前缀请求会被长前缀请求的计算拖慢。

EN: To mitigate these load imbalance issues, we adopted a three-tier length bucketing strategy (0–64K / 64K–256K / 256K–1M), aggregating requests with similar load characteristics into the same bucket for computation, significantly improving average production prefill throughput.
中: 为缓解这些负载不均衡问题，我们采用三级长度分桶策略（0–64K / 64K–256K / 256K–1M），把负载特征相近的请求聚到同一桶内计算，显著提升了生产环境平均 prefill 吞吐。

EN: Building on this, we are currently exploring finer-grained, more flexible bucketing mechanisms to adapt to dynamic production workloads.
中: 在此基础上，我们正探索更细粒度、更灵活的分桶机制，以适应动态生产负载。

### 5.3 MoE Load Balancing / MoE 负载均衡

EN: All MiMo-V2.5 series models use the MoE architecture, requiring consideration of expert load balancing during the prefill stage.
中: 所有 MiMo-V2.5 系列模型都采用 MoE 架构，prefill 阶段须考虑专家负载均衡。

EN: Since the pre-training phase introduced load-balancing training objectives and the training process was relatively stable, the model learned a fairly uniform expert routing strategy.
中: 由于预训练阶段引入了负载均衡训练目标、且训练过程相对稳定，模型学到了相当均匀的专家路由策略。

EN: During inference, without enabling any expert load balancing strategy, the average expert load factor per layer (ratio of average token count across all ranks to the maximum token count of any rank in that layer) is approximately 0.85, already indicating a well-balanced distribution.
中: 推理时，在不启用任何专家负载均衡策略的情况下，每层平均专家负载因子（所有 rank 平均 token 数 / 该层任意 rank 最大 token 数）约为 0.85，已表明分布相当均衡。

EN: Therefore, we currently do not incorporate any expert load balancing strategy. We will continue monitoring this metric and introduce related optimizations as needed based on evolving production load patterns.
中: 因此，我们当前不引入任何专家负载均衡策略。我们将持续监控该指标，并依据生产负载的演变按需引入相关优化。

### 5.4 Resolving NUMA Conflicts / 解决 NUMA 冲突

EN: The numa_balancing kernel parameter in certain Ubuntu systems conflicts with SGLang's numa-node configuration, causing sporadic large execution gaps between compute kernels during model inference.
中: 某些 Ubuntu 系统的 numa_balancing 内核参数与 SGLang 的 numa-node 配置冲突，导致模型推理期间计算 kernel 之间间歇性出现大执行间隙。

EN: In multi-node multi-GPU deployments, these gaps appear at random positions across ranks, and each inter-rank synchronization is bottlenecked by the slowest rank — significantly impacting overall inference efficiency.
中: 在多节点多 GPU 部署中，这些间隙在 rank 间随机出现，而每次 rank 间同步都被最慢的 rank 拖住——严重影响整体推理效率。

EN: Disabling the system kernel's numa_balancing parameter resolved the issue, improving end-to-end performance by approximately 10%.
中: 关闭系统内核的 numa_balancing 参数后问题解决，端到端性能提升约 10%。

---

## 6 Decode Optimization / 解码优化

### 6.1 GPU Memory Optimization / GPU 内存优化

EN: In agentic scenarios, multi-turn conversations cause the context to grow continuously, making KVCache GPU memory usage the primary decode bottleneck — once memory is filled by KVCache, batch size cannot expand, GPU compute units are not saturated, and decode throughput is limited, requiring more nodes to maintain throughput and driving up inference costs.
中: 在 agent 场景中，多轮对话使上下文持续增长，令 KVCache 的 GPU 内存占用成为解码的主要瓶颈——一旦内存被 KVCache 填满，batch size 无法扩大，GPU 计算单元无法饱和，解码吞吐受限，需更多节点维持吞吐，推高推理成本。

EN: To increase single-node concurrency, we implemented multiple memory optimizations.
中: 为提升单节点并发，我们实施了多项内存优化。

EN: 1. Decode KVCache SWA support: KVCache effective capacity increased to ~5×.
中: 1. 解码 KVCache SWA 支持：KVCache 有效容量提升到约 5 倍。

EN: 2. PD-disaggregated KVCache preallocation optimization: Moved the preallocation of KVCache for incoming requests from GPU memory to CPU memory, only transferring to GPU memory when decode actually starts, eliminating waste from resource over-provisioning.
中: 2. PD 分离 KVCache 预分配优化：把接入请求的 KVCache 预分配从 GPU 内存移到 CPU 内存，仅在实际开始解码时才搬到 GPU 内存，消除资源过度分配造成的浪费。

EN: 3. CUDA Graph memory tuning: Optimized CUDA Graph parameters to reduce wasted memory, increasing KVCache capacity.
中: 3. CUDA Graph 内存调优：优化 CUDA Graph 参数以减少浪费的内存，增加 KVCache 容量。

### 6.2 MTP Optimization / MTP 优化

EN: The MiMo-V2.5 series natively supports 3-layer MTP (Multi-Token Prediction) to accelerate decode output, but prefill previously did not enable MTP — causing the first 128 decode output tokens to have invalid KVCache in the MTP layers, with very low prediction acceptance rates.
中: MiMo-V2.5 系列原生支持 3 层 MTP（多 token 预测）以加速解码输出，但此前 prefill 未启用 MTP——导致前 128 个解码输出 token 在 MTP 层拥有无效 KVCache，预测接受率很低。

EN: Since agentic scenarios involve mostly short output sequences, this limitation significantly limited MTP's effective speedup.
中: 由于 agent 场景多为短输出序列，这一限制严重制约了 MTP 的有效加速。

EN: By introducing MTP support during prefill with dedicated adaptations and optimizations for HiCache L2/L3, MTP acceleration during the early decode phase improved substantially: 0–128 token speedup reached 2.3×, 128–256 token speedup reached 1.5×, effectively reducing actual decode cost in agentic scenarios.
中: 通过在 prefill 阶段引入 MTP 支持、并对 HiCache L2/L3 做专门适配优化，早期解码阶段的 MTP 加速大幅提升：0–128 token 加速达 2.3 倍，128–256 token 加速达 1.5 倍，有效降低了 agent 场景下的实际解码成本。

---

## 7 Multimodal Inference Optimization / 多模态推理优化

EN: Based on the SGLang community v0.5.7 EPD design, we performed a range of engineering optimizations and stability fixes for EPD disaggregation in the MiMo-V2.5 series, doubling Encoder throughput with no latency regression. We are upstreaming these changes to SGLang (issue #24945). The Encoder performance before and after optimization is summarized in Table 1.
中: 基于 SGLang 社区 v0.5.7 的 EPD 设计，我们对 MiMo-V2.5 系列的 EPD 分离做了一系列工程优化与稳定性修复，在零延迟回退下把 Encoder 吞吐翻倍。我们正把这些改动上游回馈 SGLang（issue #24945）。优化前后的 Encoder 性能见表 1。

### 7.1 Architecture Optimization / 架构优化

EN: Overlap multimodal embedding transfer with inference: In the prefill scheduler's main loop, we support asynchronous replication of multimodal embedding data across TP ranks, overlapping it with prefill inference to reduce GPU idle time.
中: 多模态 embedding 传输与推理重叠：在 prefill 调度器主循环中，我们支持跨 TP rank 异步复制多模态 embedding 数据，与 prefill 推理重叠以减少 GPU 空闲。

EN: Data parallelism for the Encoder: Since the Encoder model is relatively small, setting TP>1 degrades performance. We deploy Encoder with TP=1 while supporting data parallelism, simplifying single-machine 8-GPU deployment and operations.
中: Encoder 数据并行：由于 Encoder 模型较小，设 TP>1 会降性能。我们以 TP=1 部署 Encoder 并支持数据并行，简化单机 8-GPU 部署与运维。

EN: Encoder cross-request batch support: We introduced cross-request batching for the EPD Encoder Server. The Encoder scheduler aggregates concurrent requests by modality, merging multiple requests' image/audio into a single forward pass then splitting and returning results per request, addressing the low GPU utilization caused by per-request encoding.
中: Encoder 跨请求批处理：我们为 EPD Encoder Server 引入跨请求批处理。Encoder 调度器按模态聚合并发请求，把多请求的图像/音频合并进单次前向、再按请求拆分返回，解决了逐请求编码导致的 GPU 利用率低下。

### 7.2 Preprocessing Optimization / 预处理优化

EN: GPU image preprocessing: For large images, executing resize/normalize/patchify on CPU significantly increases end-to-end latency, so we ported preprocessing to GPU, eliminating the CPU bottleneck.
中: GPU 图像预处理：对大图，在 CPU 上做 resize/normalize/patchify 会显著增加端到端延迟，因此我们把预处理移植到 GPU，消除了 CPU 瓶颈。

EN: Parallel image download and decode: We use multi-process downloading and PIL decoding, avoiding delays from serial download and GIL contention.
中: 并行图像下载与解码：我们采用多进程下载与 PIL 解码，避免串行下载与 GIL 竞争带来的延迟。

EN: Multimodal download and forward parallelism: In the initial Encoder implementation, data download and inference were serial both across and within batches, leaving the GPU idle during downloads. We decoupled download from inference with a message queue, overlapping download and inference within a batch.
中: 多模态下载与前向并行：在最初的 Encoder 实现中，数据下载与推理在批次间和批次内都是串行的，下载时 GPU 闲置。我们用消息队列把下载与推理解耦，在批次内重叠下载与推理。

EN: Parallel video decoding: We evenly split frame extraction indices into N chunks, spawning an independent VideoDecoder per chunk and decoding them in parallel threads, reducing end-to-end Encoder latency for a 1-hour video from 156 s to 23 s.
中: 并行视频解码：我们把帧提取索引均匀切为 N 块，每块起一个独立 VideoDecoder 并行解码，把 1 小时视频的端到端 Encoder 延迟从 156 秒降到 23 秒。

### 7.3 Cache Optimization / 缓存优化

EN: Encoder consistent hashing: In multi-Encoder scenarios, Prefill round-robin Encoder selection reduces multimodal cache hit rates. Through consistent hashing, we route requests with the same key to the same Encoder, improving cache hit rate by 30%.
中: Encoder 一致性哈希：在多 Encoder 场景下，Prefill 轮询选 Encoder 会降低多模态缓存命中率。通过一致性哈希，我们把同 key 请求路由到同一 Encoder，命中率提升 30%。

EN: Intra-node Embedding cache sharing: Using shared memory, we enable multimodal cache data sharing across multiple Encoder GPUs on the same node, improving cache hit rate.
中: 节点内 Embedding 缓存共享：借助共享内存，我们让同一节点上多个 Encoder GPU 共享多模态缓存数据，提升命中率。

---

## 8 Afterword / 后记

EN: Looking back, the inference efficiency of the MiMo-V2.5 series did not come from a single breakthrough, but from coordinated optimization across multiple dimensions.
中: 回顾起来，MiMo-V2.5 系列的推理效率并非来自单点突破，而是来自跨多个维度的协同优化。

EN: Hybrid SWA benefits both prefill and decode, but an insufficiently optimized KVCache implementation can actually increase costs in both stages.
中: Hybrid SWA 同时利好 prefill 与 decode，但优化不足的 KVCache 实现反而会在两个阶段都推高成本。

EN: To address this, we systematically refactored KVCache management, tiered caching, and prefix cache trees, tackled the core challenges of SWA-aware KVCache, and optimized scheduling and the Prefill/Decode pipeline.
中: 为此，我们系统性重构了 KVCache 管理、分级缓存与前缀缓存树，攻克了 SWA 感知 KVCache 的核心挑战，并优化了调度与 Prefill/Decode 流水线。

EN: All changes were validated in production, ultimately realizing Hybrid SWA's theoretical efficiency gains.
中: 所有改动都在生产环境验证过，最终兑现了 Hybrid SWA 的理论效率收益。

EN: Only then did Hybrid SWA fully realize its architectural advantage of combined performance and efficiency in long-context inference.
中: 直到那时，Hybrid SWA 才在长上下文推理中充分释放其「性能与效率兼得」的架构优势。

EN: Further optimizations to the MoE configuration and multimodal inference pipeline also substantially boosted serving performance.
中: 对 MoE 配置与多模态推理流水线的进一步优化，也大幅提升了服务性能。

EN: We present the first large-scale engineering implementation that comprehensively covers the Hybrid SWA + MoE + multimodal composite architecture, and pass the resulting cost savings back to users through API price reductions.
中: 我们呈现了首个全面覆盖「Hybrid SWA + MoE + 多模态」复合架构的大规模工程实现，并把由此产生的成本节约通过 API 降价返还给用户。

EN: At the same time, we have contributed a subset of our optimizations to the SGLang open-source community via PRs and will continue advancing more open-source initiatives — with the goal of making engineering optimization less of a barrier, so that these high-performance, high-efficiency composite architectures can be more broadly explored and adopted.
中: 同时，我们已通过 PR 把部分优化贡献给 SGLang 开源社区，并将持续推进更多开源举措——目标是降低工程优化的门槛，让这些高性能、高效率的复合架构能被更广泛地探索与采用。
