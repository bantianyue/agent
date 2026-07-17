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
