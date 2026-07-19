# LatentMoE: Toward Optimal Accuracy per FLOP and Parameter in Mixture of Experts

## Abstract

**原文：** Mixture of Experts (MoEs) have become a central component of many state-of-the-art open-source and proprietary large language models.

**译文：** 混合专家（MoE）已成为众多最先进的开源与闭源大语言模型的核心组件。

**原文：** Despite their widespread adoption, it remains unclear how close existing MoE architectures are to optimal with respect to inference cost, as measured by accuracy per floating-point operation and per parameter.

**译文：** 尽管被广泛采用，现有 MoE 架构在推理成本（以每浮点运算、每参数的精度衡量）上距离最优还有多远，仍不清晰。

**原文：** In this work, we revisit MoE design from a hardware-software co-design perspective, grounded in empirical and theoretical considerations.

**译文：** 本文从软硬件协同设计的视角重新审视 MoE 设计，并以实证与理论分析为基础。

**原文：** We characterize key performance bottlenecks across diverse deployment regimes, spanning offline high-throughput execution and online, latency-critical inference.

**译文：** 我们刻画了多种部署场景下的关键性能瓶颈，涵盖离线高吞吐执行与在线、时延敏感的推理。

**原文：** Guided by these insights, we introduce LatentMoE, a new model architecture resulting from systematic design exploration and optimized for maximal accuracy per unit of compute.

**译文：** 受这些洞察指引，我们提出 LatentMoE——一种经由系统性设计探索得到、以单位算力下最高精度为优化目标的新架构。

**原文：** Empirical design space exploration at scales of up to 95B parameters and over a 1T-token training horizon, together with supporting theoretical analysis, shows that LatentMoE consistently outperforms standard MoE architectures in terms of accuracy per FLOP and per parameter.

**译文：** 在高达 95B 参数、超过 1T token 训练规模上的实证设计空间探索，辅以理论分析，表明 LatentMoE 在每 FLOP 与每参数的精度上持续优于标准 MoE 架构。

**原文：** Given its strong performance, the LatentMoE architecture has been adopted by the flagship Nemotron-3 Super and Ultra models and scaled to substantially larger regimes, including longer token horizons and larger model sizes, as reported in NVIDIA Nemotron-3 technical report.

**译文：** 鉴于其强劲表现，LatentMoE 架构已被旗舰级 Nemotron-3 Super 与 Ultra 模型采用，并扩展到更大规模（更长的 token 跨度与更大的模型尺寸），详见 NVIDIA Nemotron-3 技术报告。

## 1. Introduction

**原文：** Transformer-based large language models underpin a wide range of modern AI systems, from conversational agents to code generation and scientific reasoning.

**译文：** 基于 Transformer 的大语言模型支撑着从对话助手到代码生成、科学推理的众多现代 AI 系统。

**原文：** As these models continue to scale, practical deployment is increasingly constrained by inference cost, encompassing both computation and memory.

**译文：** 随着模型持续扩大，实际部署日益受限于推理成本——包括计算与显存。

**原文：** As a result, a central objective in modern model design is to maximize achievable accuracy under fixed inference cost constraints.

**译文：** 因此，现代模型设计的核心目标是在固定推理成本约束下最大化可达精度。

**原文：** Mixture-of-Experts (MoE) architectures have emerged as a promising approach towards this goal, enabling models to scale parameter count while keeping the number of Floating-point Operations (FLOPs) per token fixed.

**译文：** 混合专家（MoE）架构成为实现这一目标的有前景路径，它能在保持每 token 浮点运算数不变的同时扩大参数量。

**原文：** Despite their empirical success, the MoE design space remains poorly understood.

**译文：** 尽管经验上成功，MoE 的设计空间仍未被充分理解。

**原文：** Existing MoE architectures are largely motivated by high-level sparsity arguments and are optimized primarily for offline, throughput-oriented settings, with limited consideration of online deployments that impose strict latency, memory bandwidth, and communication constraints.

**译文：** 现有 MoE 架构主要基于高层稀疏性论证，且主要面向离线、吞吐优先场景优化，很少考虑在线部署所施加的严格时延、显存带宽与通信约束。

**原文：** We argue that effective MoE design must be evaluated along two complementary dimensions: accuracy per FLOP and accuracy per parameter.

**译文：** 我们认为，有效的 MoE 设计必须从两个互补维度评估：每 FLOP 精度与每参数精度。

**原文：** While accuracy per FLOP captures computational efficiency, accuracy per parameter reflects memory footprint, memory bandwidth demands, routing-induced communication, and sharding overheads (factors that are often the dominant bottlenecks in interactive, low-latency inference).

**译文：** 每 FLOP 精度反映计算效率，而每参数精度反映显存占用、显存带宽需求、路由引发的通信以及分片开销（这些往往是在交互式低时延推理中的主导瓶颈）。

**原文：** Neglecting these factors can lead to architectures that appear efficient in aggregate compute, yet incur substantial inefficiencies in practical deployment.

**译文：** 忽视这些因素会导致架构在总算力上看似高效，却在实际部署中产生显著低效。

**原文：** In this work, we revisit MoE architecture design from a hardware–software co-design perspective.

**译文：** 本文从软硬件协同设计视角重新审视 MoE 架构设计。

**原文：** Through a systematic analysis of existing MoE systems across the throughput–latency Pareto frontier, we identify key structural bottlenecks arising from expert parameterization, routing-induced all-to-all communication, and memory access patterns.

**译文：** 通过对现有 MoE 系统在"吞吐–时延"帕累托前沿上的系统分析，我们识别出源自专家参数化、路由引发的全互联（all-to-all）通信以及访存模式的关键结构性瓶颈。

**原文：** Combined with detailed accuracy measurements and theoretical analysis, our study identifies structural inefficiencies in prevailing MoE designs that limit achievable accuracy per unit of inference cost.

**译文：** 结合精细的精度测量与理论分析，本研究指出主流 MoE 设计中限制"单位推理成本可达精度"的结构性低效。

**原文：** Guided by these insights, we introduce LatentMoE, a new mixture-of-experts architecture explicitly optimized for both accuracy per FLOP and accuracy per parameter.

**译文：** 受这些洞察指引，我们提出 LatentMoE——一种同时针对每 FLOP 精度与每参数精度显式优化的新混合专家架构。

**原文：** LatentMoE decouples expert routing and computation from the model hidden dimension by projecting incoming activations into a shared low-dimensional latent space prior to expert processing (Figure 1).

**译文：** LatentMoE 通过在专家处理前将输入激活投影到一个共享的低维潜空间，使专家路由与计算解耦于模型隐藏维度（图 1）。

**原文：** The latent dimension serves as a direct control knob for computational cost, communication volume, and expert parameter size.

**译文：** 潜维度是控制计算成本、通信量与专家参数规模的直接旋钮。

**原文：** At iso-FLOP and iso-parameter count, projecting incoming activations into a lower-dimensional latent space enables a proportional increase in both the number of experts and the routing top-k, while maintaining constant inference cost.

**译文：** 在等 FLOP、等参数量下，将输入激活投影到更低维潜空间能在保持推理成本不变的同时，按比例同时增加专家数量与路由 top-k。

**原文：** As we show both theoretically and empirically, simultaneously increasing expert count and combinatorial sparsity diversity improves the effective expressivity of the model, leading to higher achievable accuracy.

**译文：** 我们在理论与实证上都表明，同时增加专家数量与组合稀疏性多样性能提升模型的有效表达能力，从而带来更高的可达精度。

**原文：** Crucially, these gains arise without increasing memory bandwidth demands or communication overheads, making LatentMoE well suited for both latency-critical and throughput-oriented deployments.

**译文：** 关键在于，这些收益不增加显存带宽需求或通信开销，使 LatentMoE 同时适合时延敏感与吞吐优先部署。

**原文：** We validate the LatentMoE concept through pretraining experiments at scales of up to 95B parameters and over 1T tokens.

**译文：** 我们通过高达 95B 参数、超过 1T token 的预训练实验验证 LatentMoE 概念。

**原文：** Across all evaluated regimes, LatentMoE consistently improves upon standard MoE architectures, achieving higher accuracy at fixed inference cost or substantially lower inference cost at fixed accuracy.

**译文：** 在所有评估场景中，LatentMoE 持续优于标准 MoE 架构——在固定推理成本下达到更高精度，或在固定精度下大幅降低推理成本。

**原文：** Given its strong performance, the LatentMoE architecture has been adopted by the flagship Nemotron-3 Super and Ultra models and scaled to substantially larger regimes, including longer token horizons and larger model sizes.

**译文：** 鉴于其强劲表现，LatentMoE 架构已被旗舰级 Nemotron-3 Super 与 Ultra 模型采用，并扩展到更大规模（更长 token 跨度、更大模型尺寸）。

## 2. LatentMoE Core Design Principles

**原文：** Before delving into the specifics of LatentMoE, we first take a systems-level view of what is required to deploy an MoE model that is both accurate and cost-efficient.

**译文：** 在深入 LatentMoE 细节前，我们首先从系统层面审视：部署一个既准确又成本高效的 MoE 模型需要什么。

**原文：** Throughout this section, we use Qwen3-235B-A22B as a running example for our modeling, with N=128 experts, K=8 active experts per token, a hidden dimension d=4096, and an intermediate feed-forward dimension m=1536.

**译文：** 本节以 Qwen3-235B-A22B 为建模运行示例：N=128 个专家，每 token 激活 K=8 个专家，隐藏维度 d=4096，中间前馈维度 m=1536。

**原文：** For concreteness, we consider deployment on NVIDIA GB200 GPUs interconnected by a high-bandwidth NVLink fabric, which provides approximately 1800 GB/s of bidirectional bandwidth per GPU (i.e., BW_NVL=900 GB/s per direction).

**译文：** 具体地，我们考虑部署在由高带宽 NVLink 互联的 NVIDIA GB200 GPU 上，每 GPU 双向带宽约 1800 GB/s（即每方向 BW_NVL=900 GB/s）。

**原文：** To ensure that expert communication remains within a single NVLink domain, experts are distributed via expert parallelism across EP=64 GPUs.

**译文：** 为保证专家通信停留在单一 NVLink 域内，专家通过专家并行分布在 EP=64 个 GPU 上。

**原文：** Attention layers are executed using data parallelism over the same group of GPUs.

**译文：** 注意力层在同一组 GPU 上以数据并行方式执行。

**原文：** Each GB200 GPU delivers a peak FP4 Tensor Core throughput of F=10 PFLOPs and an HBM memory bandwidth of BW_HBM=8 TB/s.

**译文：** 每块 GB200 GPU 提供峰值 FP4 Tensor Core 吞吐 F=10 PFLOPs 与 HBM 显存带宽 BW_HBM=8 TB/s。

### 2.1 Memory Bandwidth Bottleneck

**原文：** In highly interactive (i.e., low-latency) settings that typically use small batch sizes, MoE computation is primarily bottlenecked by memory bandwidth.

**译文：** 在通常使用小批量的高度交互（即低时延）场景中，MoE 计算主要受制于显存带宽。

**原文：** Figure 2 provides a high-level roof-line analysis of performance versus arithmetic intensity.

**译文：** 图 2 给出性能相对算术强度的顶层 roofline（算力–带宽）分析。

**原文：** For a GB200 system, a computation becomes compute-bound only if its arithmetic intensity (i.e., FLOPs per byte) exceeds F/BW_HBM = 10×10^15 / (8×10^12) = 1250 FLOPs/byte.

**译文：** 对 GB200 系统，只有当算术强度（即每字节 FLOP 数）超过 F/BW_HBM = 10×10^15 / (8×10^12) = 1250 FLOPs/字节 时，计算才成为计算受限。

**原文：** Let t_total be the total number of tokens across the EP GPUs prior to MoE routing.

**译文：** 令 t_total 为 MoE 路由前分布在 EP 个 GPU 上的 token 总数。

**原文：** Assuming a uniform distribution of tokens across experts, the number of tokens assigned to a single expert is: t_exp := (t_total · K)/N.

**译文：** 假设 token 在专家间均匀分布，单个专家分到的 token 数为：t_exp := (t_total · K)/N。

**原文：** In the Qwen3-235B-A22B example, with N=128 and EP=64, each GPU hosts N/EP=2 experts; thus each GPU processes approximately 2·t_exp expert tokens per MoE layer.

**译文：** 在 Qwen3-235B-A22B 示例中，N=128、EP=64，每 GPU 承载 N/EP=2 个专家；故每 MoE 层每 GPU 约处理 2·t_exp 个专家 token。

**原文：** The FP4 compute cost for a single expert is C_exp = 2·t_exp·d·m, and the corresponding memory traffic in FP4 precision is given by M_exp = d·m + t_exp·(d+m).

**译文：** 单个专家的 FP4 计算成本为 C_exp = 2·t_exp·d·m，相应的 FP4 精度显存流量为 M_exp = d·m + t_exp·(d+m)。

**原文：** Since each GPU processes two experts in our example, the arithmetic intensity I is given by the ratio of the total compute to the total memory traffic: I = (2·t_exp·d·m)/(d·m + t_exp·(d+m)).

**译文：** 由于示例中每 GPU 处理两个专家，算术强度 I 为总计算与总显存流量之比：I = (2·t_exp·d·m)/(d·m + t_exp·(d+m))。

**原文：** To operate in the compute-bound regime, we require I ≥ 1250.

**译文：** 要进入计算受限区域，需满足 I ≥ 1250。

**原文：** Substituting the Qwen3-235B-A22B parameters yields the condition: t_exp ≥ 1418.

**译文：** 代入 Qwen3-235B-A22B 参数得条件：t_exp ≥ 1418。

**原文：** In typical latency-critical deployments, effective batch sizes are small, resulting in t_exp being on the order of a few hundred tokens—well below the threshold of 1418.

**译文：** 在典型时延敏感部署中，有效批量很小，t_exp 仅数百 token 量级——远低于 1418 阈值。

**原文：** Consequently, MoE experts operate in the memory-bound region of the roofline curve (Figure 2), where performance is limited by weight loading rather than compute capacity.

**译文：** 因此，MoE 专家运行在 roofline 曲线的显存受限区（图 2），性能受限于权重加载而非算力。

**原文：** Design Principle I: In low-latency serving scenarios, MoE inference is typically dominated by the memory-bandwidth cost of loading model weights. Consequently, maximizing accuracy per parameter is critical for applications with high interactivity requirements.

**译文：** 设计原则 I：在低时延服务场景中，MoE 推理通常受模型权重加载的显存带宽成本主导。因此，对高交互需求的应用，最大化每参数精度至关重要。

### 2.2 Communication Bottleneck

**原文：** In throughput-oriented settings, once experts become compute-bound, communication emerges as a significant contributor to end-to-end execution time in distributed settings.

**译文：** 在吞吐优先场景中，一旦专家进入计算受限，通信便成为分布式环境下端到端执行时间的重要贡献者。

**原文：** Expert parallelism mandates all-to-all token routing across devices, imposing an overhead that can control end-to-end execution time.

**译文：** 专家并行要求在设备间进行全互联 token 路由，由此引入的开销可能主导端到端执行时间。

**原文：** The all-to-all communication volume per GPU per MoE layer is given by: M_comm = 2.5 · (N/EP · t_exp · d) = 5 · t_exp · d.

**译文：** 每 GPU 每 MoE 层的全互联通信量为：M_comm = 2.5 · (N/EP · t_exp · d) = 5 · t_exp · d。

**原文：** Here, the factor 2.5 accounts for the mixed-precision traffic (0.5 bytes for FP4 dispatch, 2 bytes for BF16 aggregation).

**译文：** 其中系数 2.5 计入混合精度流量（FP4 分发 0.5 字节，BF16 聚合 2 字节）。

**原文：** On the compute side, the total FLOP count for the two local experts is: C_comp = 2 · (N/EP · t_exp · d · m) = 4 · t_exp · d · m.

**译文：** 在计算侧，两个本地专家的总 FLOP 数为：C_comp = 2 · (N/EP · t_exp · d · m) = 4 · t_exp · d · m。

**原文：** The corresponding compute time is: t_comp = C_comp / F = (4·t_exp·d·m)/F.

**译文：** 相应计算时间为：t_comp = C_comp / F = (4·t_exp·d·m)/F。

**原文：** Similarly, the all-to-all communication time is: t_comm = M_comm / BW_NVL = (5·t_exp·d)/BW_NVL.

**译文：** 类似地，全互联通信时间为：t_comm = M_comm / BW_NVL = (5·t_exp·d)/BW_NVL。

**原文：** Consequently, the ratio of communication time to compute time is: t_comm/t_comp = (5·F)/(4·m·BW_NVL).

**译文：** 因此，通信时间与计算时间之比为：t_comm/t_comp = (5·F)/(4·m·BW_NVL)。

**原文：** Substituting the parameters for the GB200 NVL72 and Qwen3-235B-A22B yields a ratio of approximately 9.

**译文：** 代入 GB200 NVL72 与 Qwen3-235B-A22B 参数，该比值约为 9。

**原文：** This indicates that in the throughput-oriented regime, MoE layers are heavily dominated by all-to-all communication overhead.

**译文：** 这表明在吞吐优先区域，MoE 层严重受制于全互联通信开销。

**原文：** Design Principle II: Improving performance in throughput-oriented MoE deployments requires minimizing the data volume of all-to-all operations. This volume is proportional to (N/EP)·t_exp·d = (t_total·K·d)/EP.

**译文：** 设计原则 II：在吞吐优先 MoE 部署中提升性能，需最小化全互联操作的数据量。该数据量正比于 (N/EP)·t_exp·d = (t_total·K·d)/EP。

**原文：** Consequently, communication overhead can be mitigated by reducing the routed hidden dimension d or the number of active experts K.

**译文：** 因此，可通过降低路由隐藏维度 d 或激活专家数 K 来缓解通信开销。

**原文：** Note that modifying the intermediate dimension m does not affect the token size and thus yields no direct improvement.

**译文：** 注意，修改中间维度 m 不影响 token 大小，故无直接改善。

### 2.3 Model Quality

**原文：** Beyond optimizing inference speed, preserving model quality is paramount.

**译文：** 除优化推理速度外，保持模型质量至关重要。

**原文：** Classical results on Barron functions state that a one-hidden-layer network with u nonlinear units achieves a mean-squared error of O(1/u), independent of the input dimension d.

**译文：** 关于 Barron 函数的经典结论指出，含 u 个非线性单元的单隐藏层网络达到 O(1/u) 的均方误差，与输入维度 d 无关。

**原文：** In an MoE layer, this effective nonlinear budget per token is proportional to the total width of the selected experts: U_eff ∝ K·m.

**译文：** 在 MoE 层中，每 token 的有效非线性预算正比于所选专家的总宽度：U_eff ∝ K·m。

**原文：** This implies that reducing the active experts K or the intermediate dimension m directly penalizes the effective capacity (U_eff), risking model quality degradation.

**译文：** 这意味着减少激活专家 K 或中间维度 m 会直接损害有效容量（U_eff），有损模型质量。

**原文：** Design Principle III: Maintaining model quality requires preserving the effective nonlinear budget, K·m. Consequently, to alleviate memory and communication bottlenecks without sacrificing model quality, we should keep both the number of active experts and the intermediate dimension unchanged.

**译文：** 设计原则 III：保持模型质量需保留有效非线性预算 K·m。因此，要在不牺牲质量的前提下缓解显存与通信瓶颈，应同时保持激活专家数与中间维度不变。

**原文：** Every inference task is characterized by an intrinsic feature rank, r_eff, corresponding to the minimum number of degrees of freedom required to preserve task-relevant information.

**译文：** 每个推理任务都有一个内在特征秩 r_eff，即保留任务相关信息所需的最小自由度数量。

**原文：** Reducing the hidden dimension d below this threshold necessarily discards such information, leading to accuracy degradation.

**译文：** 将隐藏维度 d 降到该阈值以下必然丢弃此类信息，导致精度下降。

**原文：** Design Principle IV: There exists a task-specific feature rank r_eff that imposes a lower limit on the reduction of d. Reducing d below this limit precipitates a collapse in model quality.

**译文：** 设计原则 IV：存在任务特定的特征秩 r_eff，对 d 的压缩设定下界。将 d 压到该限以下会致模型质量崩塌。

**原文：** Additionally, the MoE architecture benefits from combinatorial sparsity, offering C(N,K) possible expert combinations per token.

**译文：** 此外，MoE 架构受益于组合稀疏性——每 token 提供 C(N,K) 种专家组合可能。

**原文：** Increasing the total number of experts N expands this specialization space.

**译文：** 增加专家总数 N 可扩展这一专门化空间。

**原文：** Furthermore, scaling both N and K by a factor α exponentially increases the diversity of expert mixtures: C(αN, αK) ≥ (C(N,K))^α.

**译文：** 进一步，将 N 与 K 同时按因子 α 放大，会指数级增加专家组合多样性：C(αN, αK) ≥ (C(N,K))^α。

**原文：** Design Principle V: Scaling both the number of experts N and top-k per token K enhances model quality by exponentially expanding the space of expert combinations.

**译文：** 设计原则 V：同时放大专家数 N 与每 token 的 top-k K，能通过指数级扩展专家组合空间来提升模型质量。

**原文：** Design Principles I and II indicate that improving inference speed requires reducing both memory bandwidth and communication costs. Memory bandwidth cost scales with d and m, while communication cost scales with K and d.

**译文：** 设计原则 I、II 表明，提升推理速度需同时降低显存带宽与通信成本。显存带宽成本随 d、m 缩放，通信成本随 K、d 缩放。

**原文：** However, Principle III cautions against reducing either K or m, as doing so would likely degrade model quality.

**译文：** 但原则 III 警示不要降低 K 或 m，否则可能损害模型质量。

**原文：** This leaves d as the most promising dimension to reduce, enabling performance improvements in both throughput- and latency-oriented regimes without significant loss in accuracy.

**译文：** 这留下 d 作为最值得压缩的维度，能在两个场景都提升性能且不显著损失精度。

**原文：** Principle IV further establishes a lower bound, (r_eff), on d to prevent quality collapse.

**译文：** 原则 IV 进一步为 d 设定下界 r_eff 以防质量崩塌。

**原文：** Moreover, Principle V suggests that increasing N and K improves model quality.

**译文：** 此外，原则 V 提示增加 N 与 K 能提升质量。

**原文：** Since memory bandwidth and communication costs scale linearly with K, we can simultaneously increase K by a factor α and reduce d by the same factor α (provided d/α ≥ r_eff).

**译文：** 由于显存带宽与通信成本随 K 线性缩放，我们可同时将 K 放大 α 倍、将 d 缩小 α 倍（只要 d/α ≥ r_eff）。

**原文：** We hypothesize, and empirically validate in subsequent sections, that this transformation preserves memory bandwidth and communication costs while improving network expressivity and combinatorial sparsity, yielding higher accuracy per FLOP and per parameter.

**译文：** 我们提出假说并在后续章节实证验证：该变换在保持显存带宽与通信成本的同时，提升网络表达力与组合稀疏性，带来更高的每 FLOP 与每参数精度。

## 3. LatentMoE Architecture

**原文：** Guided by the design principles outlined in Section 2, we introduce LatentMoE, a new MoE architecture designed for efficient scaling.

**译文：** 受第 2 节设计原则指引，我们提出 LatentMoE——一种为高效扩展而设计的新 MoE 架构。

**原文：** LatentMoE first projects each input token x ∈ R^d into a lower-dimensional latent space R^ℓ using a learnable down-projection matrix W_↓ ∈ R^(ℓ×d).

**译文：** LatentMoE 首先用可学习的下投影矩阵 W_↓ ∈ R^(ℓ×d)，将每个输入 token x ∈ R^d 投影到更低维潜空间 R^ℓ。

**原文：** The resulting compressed representation is then routed to the selected experts.

**译文：** 得到的压缩表示随后被路由到所选专家。

**原文：** Each expert E_i(·; ℓ) operates entirely within the latent space and is parameterized by weights W_FC1^(i), W_gate^(i) ∈ R^(m×ℓ) and W_FC2^(i) ∈ R^(ℓ×m).

**译文：** 每个专家 E_i(·; ℓ) 完全在潜空间内运算，由权重 W_FC1^(i)、W_gate^(i) ∈ R^(m×ℓ) 与 W_FC2^(i) ∈ R^(ℓ×m) 参数化。

**原文：** After expert computation, the outputs are aggregated and projected back to the original input dimension using a learnable up-projection matrix W_↑ ∈ R^(d×ℓ).

**译文：** 专家计算后，输出被聚合并用可学习的上投影矩阵 W_↑ ∈ R^(d×ℓ) 投影回原始输入维度。

**原文：** Since we compress only the input dimension d to ℓ while keeping the intermediate dimension m constant, the effective nonlinear budget U_eff remains unchanged.

**译文：** 由于我们仅将输入维度 d 压缩到 ℓ、而保持中间维度 m 不变，有效非线性预算 U_eff 保持不变。

**原文：** While Design Principle III suggests this should theoretically preserve accuracy, in practice, larger models are often easier to train and more robust to hyperparameter variations.

**译文：** 尽管设计原则 III 在理论上应保留精度，实践中更大的模型通常更易训练、对超参变化更鲁棒。

**原文：** To avoid extensive hyperparameter tuning for the compressed model, we leverage Design Principle V by scaling the total number of experts N by a factor α = d/ℓ, thereby expanding the combinatorial specialization space.

**译文：** 为避免对压缩模型做大量超参调优，我们利用设计原则 V，将专家总数 N 按因子 α = d/ℓ 放大，从而扩展组合专门化空间。

**原文：** Crucially, since neither the memory bandwidth cost (in latency-oriented scenarios) nor the communication cost (in throughput-oriented scenarios) depends on N, this scaling adheres to Design Principles I and II, incurring no additional inference overhead.

**译文：** 关键在于，无论显存带宽成本（时延场景）还是通信成本（吞吐场景）都不依赖 N，故该放大符合设计原则 I、II，不带来额外推理开销。

**原文：** Hereafter, we refer to this architecture modification as ℓ-MoE-eff, formally defined as follows: ℓ-MoE-eff(x) := W_↑ · ( Σ_{i∈T_{K,N'}} p'_i E_i(W_↓·x; ℓ) ) + Σ_{j=N'+1}^{N'+S} E_j(x; d).

**译文：** 此后称此架构修改为 ℓ-MoE-eff，形式定义为：ℓ-MoE-eff(x) := W_↑ · ( Σ_{i∈T_{K,N'}} p'_i E_i(W_↓·x; ℓ) ) + Σ_{j=N'+1}^{N'+S} E_j(x; d)。

**原文：** Here, N' = α·N denotes the expanded set of routed experts.

**译文：** 其中 N' = α·N 表示扩展后的路由专家集合。

**原文：** The routed experts E_i(·; ℓ) function within the latent space, while the shared experts E_j(·; d) operate in the original input space.

**译文：** 路由专家 E_i(·; ℓ) 在潜空间内工作，而共享专家 E_j(·; d) 在原始输入空间工作。

**原文：** The routing weights p' = Softmax(W'_r · x) are computed from the original token x ∈ R^d using a learnable weight matrix W'_r ∈ R^(N'×d), and T_{K,N'} denotes the indices of the top-K experts (out of N' total) selected based on their routing scores.

**译文：** 路由权重 p' = Softmax(W'_r · x) 由原始 token x ∈ R^d 经可学习权重矩阵 W'_r ∈ R^(N'×d) 算出；T_{K,N'} 表示按路由分数选出的 top-K 专家（共 N' 个）索引。

**原文：** For simplicity, all operations outside the routed experts—including the MoE routing mechanism and shared experts—continue to operate in the original hidden dimension d, as they do not significantly contribute to the identified memory and communication bottlenecks.

**译文：** 为简洁，路由专家之外的所有操作——包括 MoE 路由机制与共享专家——仍在原始隐藏维度 d 下工作，因为它们对前述显存与通信瓶颈贡献不大。

**原文：** Following the down-projection W_↓, token dispatch and aggregation occur in the latent space R^ℓ.

**译文：** 经下投影 W_↓ 后，token 分发与聚合都在潜空间 R^ℓ 中进行。

**原文：** This reduces the communication volume by a factor of α relative to a standard MoE.

**译文：** 这相对标准 MoE 将通信量缩减 α 倍。

**原文：** Similarly, because the expert weights lie in the latent space (R^(m×ℓ) and R^(ℓ×m)), the memory bandwidth cost for weight loading is also reduced by a factor of α.

**译文：** 类似地，由于专家权重位于潜空间（R^(m×ℓ) 与 R^(ℓ×m)），权重加载的显存带宽成本也缩减 α 倍。

**原文：** Design Principle V further suggests that scaling both N and K by a factor α exponentially increases expert diversity, thereby enhancing model quality.

**译文：** 设计原则 V 还提示将 N 与 K 同时放大 α 倍会指数级增加专家多样性，从而提升质量。

**原文：** Following this principle, the default LatentMoE configuration (a.k.a., ℓ-MoE-acc) is defined as follows: ℓ-MoE-acc(x) := W_↑ · ( Σ_{i∈T_{K',N'}} p'_i E_i(W_↓·x; ℓ) ) + Σ_{j=N'+1}^{N'+S} E_j(x; d), where K' = α·K.

**译文：** 依此原则，LatentMoE 默认配置（即 ℓ-MoE-acc）定义为：ℓ-MoE-acc(x) := W_↑ · ( Σ_{i∈T_{K',N'}} p'_i E_i(W_↓·x; ℓ) ) + Σ_{j=N'+1}^{N'+S} E_j(x; d)，其中 K' = α·K。

**原文：** This formulation differs from ℓ-MoE-eff solely in the number of active experts, utilizing the top-k selection function T_{K',N'}.

**译文：** 该式与 ℓ-MoE-eff 的唯一区别在激活专家数，采用 top-k 选择函数 T_{K',N'}。

**原文：** Since K is increased by a factor of α = d/ℓ, this variant keeps communication cost and memory bandwidth requirements constant relative to a standard MoE.

**译文：** 由于 K 放大了 α = d/ℓ 倍，该变体相对标准 MoE 保持通信成本与显存带宽需求不变。

**原文：** The increased expert diversity and non-linearity budget per token, however, lead to superior model accuracy at iso-inference cost, thereby pushing the Pareto frontier of models to a new level.

**译文：** 但更高的每 token 专家多样性与非线性预算，在等推理成本下带来更优模型精度，从而将模型的帕累托前沿推到新高度。

**原文：** Table 2 summarizes the costs and benefits of the two configurations, ℓ-MoE-eff and ℓ-MoE-acc.

**译文：** 表 2 总结两种配置 ℓ-MoE-eff 与 ℓ-MoE-acc 的成本与收益。

## 4. Evaluation

**原文：** In this section, we conduct a thorough design space exploration to verify the effectiveness of the proposed LatentMoE architecture.

**译文：** 本节通过详尽的设计空间探索验证所提 LatentMoE 架构的有效性。

**原文：** We start by pretraining Transformer MoE models at two different scales: (1) 16B total parameters with 2B active, which we use for conducting ablation studies, and (2) 95B total parameters with 8B active, which we use as a scaling test of the 16B results.

**译文：** 我们首先在两个规模预训练 Transformer MoE：① 总参 16B、激活 2B，用于消融研究；② 总参 95B、激活 8B，用于检验 16B 结果的扩展性。

**原文：** To demonstrate the generalizability of LatentMoE architectures, we further extend our study by training hybrid Mamba-Attention MoE models at scale.

**译文：** 为展示 LatentMoE 架构的通用性，我们进一步训练大规模混合 Mamba-Attention MoE 模型。

**原文：** We use the architecture and hyperparameters from DeepSeek-v2-lite for our 2B active model ablations.

**译文：** 2B 激活模型的消融采用 DeepSeek-v2-lite 的架构与超参。

**原文：** For the 8B active Transformer model, we use a cosine learning rate schedule with a max learning rate of 1.2×10^-3 decayed to a minimum of 3×10^-6.

**译文：** 8B 激活 Transformer 模型采用余弦学习率，峰值 1.2×10^-3 衰减至最低 3×10^-6。

**原文：** The 8B active Hybrid model is trained with a WSD schedule with a max learning rate of 8×10^-4 decayed to 8×10^-6 in the last 15% of training.

**译文：** 8B 激活混合模型采用 WSD 调度，峰值 8×10^-4 在最后 15% 训练衰减至 8×10^-6。

**原文：** Both the 8B active Transformer and hybrid models are trained with a sequence length of 8192, a batch size of 768 (~6 million tokens), and a learning rate warmup of 8.4 billion tokens.

**译文：** 两个 8B 激活模型均以序列长 8192、批大小 768（约 600 万 token）、学习率预热 84 亿 token 训练。

**原文：** The 8B active models use a load balancing loss coefficient of 10^-4 along with DeepSeek's aux-loss-free load balancing strategy to ensure balanced token load throughout training.

**译文：** 8B 激活模型采用 10^-4 的负载均衡损失系数，配合 DeepSeek 的无辅助损失负载均衡策略，保证训练全程 token 负载均衡。

**原文：** Table 3 summarizes the model architecture under study in this paper.

**译文：** 表 3 总结本文所研究的模型架构。

### 4.1 LatentMoE Ablations

**原文：** Design Principle IV hypothesizes that there exists an intrinsic rank r_eff such that compressing the latent dimension to ℓ ≥ r_eff results in negligible information loss.

**译文：** 设计原则 IV 假定存在内在秩 r_eff，将潜维度压缩到 ℓ ≥ r_eff 时信息损失可忽略。

**原文：** To empirically validate this and estimate r_eff, we pretrain and sweep different compression ratios on top of the ℓ-MoE-eff configuration, holding all other hyperparameters constant.

**译文：** 为实证验证并估计 r_eff，我们在 ℓ-MoE-eff 配置上预训练并扫描不同压缩比，其余超参不变。

**原文：** Results in Figure 3 indicate that model quality is preserved for compression ratios α ≤ 4.

**译文：** 图 3 结果表明，在压缩比 α ≤ 4 时模型质量得以保持。

**原文：** Consequently, we adopt α = 4 for all subsequent experiments.

**译文：** 因此我们后续实验统一取 α = 4。

**原文：** We empirically verified that this setting remains effective at larger scales as well (i.e., 95B total and 8B active).

**译文：** 我们实证验证该设置在更大规模（95B 总参、8B 激活）同样有效。

**原文：** In Section 3, we noted that parameter reduction via compression can impede training stability.

**译文：** 第 3 节指出，压缩带来的参数量减少会妨碍训练稳定性。

**原文：** To quantify this, we pretrain the ℓ-MoE-eff LatentMoE variant of the 16B total and 2B active parameter model with the hidden dimension d compressed by a factor of 4, both with and without a compensatory increase in the total number of experts, using the baseline hyperparameters.

**译文：** 为量化这一点，我们用基线超参预训练 16B 总参/2B 激活模型的 ℓ-MoE-eff 变体，将隐藏维度 d 压缩 4 倍，分别在有/无专家总数补偿性增加两种情况下进行。

**原文：** As shown in Figure 4, reducing d without scaling the expert count leads to significant quality degradation, validating the expert scaling strategy employed by LatentMoE.

**译文：** 如图 4 所示，不放大专家数而压缩 d 会导致显著质量退化，验证了 LatentMoE 的专家放大策略。

**原文：** In Section 3, we introduced two LatentMoE variants: ℓ-MoE-eff, designed to improve inference efficiency while maintaining baseline accuracy, and ℓ-MoE-acc, designed to enhance accuracy at a comparable inference cost.

**译文：** 第 3 节提出两个 LatentMoE 变体：ℓ-MoE-eff（在保持基线精度的同时提升推理效率）与 ℓ-MoE-acc（在相近推理成本下提升精度）。

**原文：** Figure 5 compares the validation loss of these configurations against the baseline for the 16B total and 2B active parameter model using a latent dimension of ℓ=512 (α=4).

**译文：** 图 5 以潜维度 ℓ=512（α=4）的 16B 总参/2B 激活模型，对比这些配置与基线的验证损失。

**原文：** Consistent with our expectations, ℓ-MoE-eff matches the baseline accuracy, whereas ℓ-MoE-acc achieves a noticeably lower validation loss.

**译文：** 与预期一致，ℓ-MoE-eff 匹配基线精度，而 ℓ-MoE-acc 取得明显更低的验证损失。

**原文：** We recommend ℓ-MoE-acc for Pareto-optimal accuracy versus inference cost.

**译文：** 我们推荐 ℓ-MoE-acc 作为精度–推理成本的帕累托最优选择。

### 4.2 LatentMoE Scaling Studies

**原文：** Leveraging the insights from the 16B model ablations, we train a 95B parameter Transformer using a LatentMoE configuration with a 4× compression ratio.

**译文：** 借助 16B 模型消融的洞察，我们用 4× 压缩比的 LatentMoE 配置训练 95B 参数 Transformer。

**原文：** Figure 6 presents the validation loss trajectories for ℓ-MoE-eff and ℓ-MoE-acc relative to the baseline.

**译文：** 图 6 给出 ℓ-MoE-eff 与 ℓ-MoE-acc 相对基线的验证损失轨迹。

**原文：** Consistent with the 16BT-2BA results, ℓ-MoE-eff matches the baseline, while ℓ-MoE-acc demonstrates superior results.

**译文：** 与 16BT-2BA 结果一致，ℓ-MoE-eff 匹配基线，而 ℓ-MoE-acc 表现更优。

**原文：** Table 4 shows the downstream task accuracy at the 300B token horizon.

**译文：** 表 4 给出 300B token 跨度下的下游任务精度。

**原文：** We report Code as the average over HumanEval, HumanEval+, MBPP, and MBPP+, Math as the average of GSM8K CoT and MATH-500, and Commonsense understanding as the average of RACE, ARC-Challenge, HellaSwag, and Winogrande.

**译文：** Code 取 HumanEval、HumanEval+、MBPP、MBPP+ 平均；Math 取 GSM8K CoT 与 MATH-500 平均；常识理解取 RACE、ARC-Challenge、HellaSwag、Winogrande 平均。

**原文：** For simplicity, we used the exact same hyperparameters optimized for the baseline Transformer for LatentMoE.

**译文：** 为简洁，LatentMoE 直接沿用为基线 Transformer 优化好的相同超参。

**原文：** Further hyperparameter tuning might lead to even better accuracy.

**译文：** 进一步超参调优可能带来更好精度。

**原文：** To further validate the effectiveness of the LatentMoE architecture, we also pretrain a series of hybrid Mamba-Attention MoE models.

**译文：** 为进一步验证 LatentMoE 架构有效性，我们还预训练了一系列混合 Mamba-Attention MoE 模型。

**原文：** Specifically, we first train a baseline 8B active (73B total) parameter model.

**译文：** 具体地，我们先训练基线 8B 激活（73B 总参）模型。

**原文：** As described in Table 3, each MoE layer in the hybrid architecture contains 128 experts, 6 activated experts, 2 shared experts, and uses an intermediate FFN dimension of 2688.

**译文：** 如表 3 所述，混合架构每层含 128 专家、激活 6、共享 2，中间 FFN 维度 2688。

**原文：** We use Squared-ReLU activation and a model dimension of 4096.

**译文：** 激活函数用 Squared-ReLU，模型维度 4096。

**原文：** We then train the ℓ-MoE-eff and ℓ-MoE-acc LatentMoE variants of the baseline model, using a 4× compression ratio.

**译文：** 随后以 4× 压缩比训练基线的 ℓ-MoE-eff 与 ℓ-MoE-acc 变体。

**原文：** Results after training the above models on 1T tokens are shown in Table 5.

**译文：** 上述模型在 1T token 上训练的结果见表 5。

**原文：** All models are trained with identical hyperparameters.

**译文：** 所有模型以相同超参训练。

**原文：** As shown, the LatentMoE ℓ-MoE-acc variant achieves significantly higher accuracy than the baseline across all tasks, while the ℓ-MoE-eff variant achieves accuracy comparable to or better than the standard granular MoE baseline.

**译文：** 如表所示，LatentMoE 的 ℓ-MoE-acc 变体在所有任务上显著优于基线，而 ℓ-MoE-eff 变体达到与标准细粒度 MoE 基线相当或更好的精度。

**原文：** Overall, the LatentMoE architecture provides a clear advantage in terms of accuracy per FLOP and per parameter compared to granular MoEs, paving the way for higher accuracy at fixed inference cost or lower inference cost at fixed accuracy.

**译文：** 总体而言，相比细粒度 MoE，LatentMoE 架构在每 FLOP 与每参数精度上具有明显优势，为"固定推理成本下更高精度"或"固定精度下更低推理成本"铺路。

### 4.3 Inference Performance

**原文：** As discussed in Section 3, ℓ-MoE-acc is expected to achieve similar inference speed to the standard MoE baseline while attaining higher accuracy.

**译文：** 如第 3 节所述，ℓ-MoE-acc 预期在标准 MoE 基线的相近推理速度下取得更高精度。

**原文：** Our evaluations in Section 4.2 confirmed that ℓ-MoE-acc indeed achieves higher accuracy compared to standard MoE.

**译文：** 第 4.2 节的评估确认 ℓ-MoE-acc 确实比标准 MoE 精度更高。

**原文：** Here, we evaluate ℓ-MoE-acc from the perspective of inference efficiency.

**译文：** 这里我们从推理效率角度评估 ℓ-MoE-acc。

**原文：** Table 6 presents the measured performance of ℓ-MoE-acc compared to standard MoE for the Hybrid-73BT-8BA model on two Hopper H100 GPUs using vLLM with FP8 per-tensor quantization.

**译文：** 表 6 给出在两块 Hopper H100 GPU 上、用 vLLM 以 FP8 逐张量量化运行 Hybrid-73BT-8BA 模型时，ℓ-MoE-acc 相对标准 MoE 的实测性能。

**原文：** We focus our measurements on the hybrid Mamba-Attention baseline, as it represents the most efficient inference architecture.

**译文：** 我们把测量集中在混合 Mamba-Attention 基线，因它代表最高效的推理架构。

**原文：** The measurements show that at higher concurrencies, per-GPU throughput drops by only up to 6%.

**译文：** 测量显示，在较高并发下每 GPU 吞吐仅下降至多 6%。

**原文：** It is important to note that further software optimizations could be performed to mitigate even these small throughput differences between LatentMoE and standard MoE.

**译文：** 需注意，还可做进一步软件优化来弥合 LatentMoE 与标准 MoE 之间这点微小吞吐差异。

**原文：** One proposed optimization is to utilize separate CUDA streams for routed and shared experts, which could reduce end-to-end latency when performing inference with smaller batches or when model dimensions do not saturate the GPU's compute.

**译文：** 一项提议优化是为路由专家与共享专家使用独立 CUDA 流，可在小批量或模型维度未饱和 GPU 算力时降低端到端时延。

**原文：** A second optimization targets the MoE kernels from the CUTLASS library.

**译文：** 第二项优化针对 CUTLASS 库的 MoE 算子。

**原文：** Since LatentMoEs decrease the size of the GEMMs for routed experts, it is important to ensure that inner dimensions remain large enough to fully utilize the GPU and avoid SM-bound workloads.

**译文：** 由于 LatentMoE 缩小了路由专家的 GEMM 规模，需确保内维度足够大以充分利用 GPU、避免 SM 受限。

**原文：** When inner dimensions are small, specialized smaller-matrix GEMM kernels should be used.

**译文：** 内维度较小时，应使用专门的小矩阵 GEMM 算子。

### 4.4 Projected Serving Impact at Trillion-Parameter Scale

**原文：** Inference efficiency can be characterized as a three-dimensional trade-off surface, with accuracy along one axis, throughput per GPU along a second axis, and latency (user interactivity) along the third axis.

**译文：** 推理效率可刻画为三维权衡曲面：一轴为精度，二轴为每 GPU 吞吐，三轴为时延（用户交互性）。

**原文：** Thus far, we have discussed the accuracy of LatentMoE and presented measured performance at the 95B-parameter scale.

**译文：** 至此我们讨论了 LatentMoE 的精度，并给出 95B 参数规模的实测性能。

**原文：** In the following section, we examine a two-dimensional slice of this trade-off at the trillion-parameter scale by projecting throughput per GPU and latency Pareto frontiers for accuracy-matched models.

**译文：** 下节我们在万亿参数规模上考察该权衡的二维切片，对精度匹配模型投影每 GPU 吞吐与时延帕累托前沿。

**原文：** Figure 7 presents the projected throughput-latency Pareto frontiers at trillion-parameter scale.

**译文：** 图 7 给出万亿参数规模下投影的吞吐–时延帕累托前沿。

**原文：** We use a high-fidelity proprietary performance simulator to project end-to-end serving performance for a trillion-parameter class model and its LatentMoE variant.

**译文：** 我们用高保真专有性能模拟器，对万亿参数级模型及其 LatentMoE 变体的端到端服务性能做投影。

**原文：** We simulate over 200K operating points to estimate the throughput per GPU and latency Pareto frontiers shown in Figure 7.

**译文：** 我们模拟超过 20 万个运行点，估计图 7 所示的每 GPU 吞吐与时延帕累托前沿。

**原文：** We consider two traffic patterns. The first is a decode-heavy setting modeled with chunked piggybacking serving. The second is a prefill-heavy setting modeled with disaggregated serving, where prefill and decode are separated to reflect long-context traffic.

**译文：** 我们考虑两种流量模式：其一为 decode 密集、用分块捎带（chunked piggybacking）服务建模；其二为 prefill 密集、用分离式（disaggregated）服务建模，将 prefill 与 decode 分离以反映长上下文流量。

**原文：** The serving strategy is selected following the guidance in Beyond aggregation.

**译文：** 服务策略依 Beyond aggregation 指南选择。

**原文：** We use the effective parameter multiplier to construct an iso-accuracy baseline for inference comparisons.

**译文：** 我们用有效参数乘数构造等精度基线以做推理对比。

**原文：** We benchmark the native Kimi-K2-1T against our proposed variant, Kimi-K2-1T-LatentMoE.

**译文：** 我们将原生 Kimi-K2-1T 与我们提出的变体 Kimi-K2-1T-LatentMoE 做基准对比。

**原文：** Following the "Effective Parameter Count" framework, we posit that a treated model with physical parameters N_treat behaves like a standard dense baseline with effective parameters N_eff.

**译文：** 依"有效参数量"框架，我们认为物理参数为 N_treat 的被处理模型，表现得像有效参数为 N_eff 的标准稠密基线。

**原文：** We assume baseline performance follows a scaling law f(N).

**译文：** 我们假设基线性能遵循缩放律 f(N)。

**原文：** For a treated model achieving score S_treat, the effective capacity is obtained by inverting the baseline scaling law: N_eff = f^-1(S_treat).

**译文：** 对被处理模型取得分数 S_treat，其有效容量由反解基线缩放律得到：N_eff = f^-1(S_treat)。

**原文：** The EPM is defined as the ratio of effective capacity to physical parameters: λ = N_eff / N_treat.

**译文：** 有效参数乘数（EPM）定义为有效容量与物理参数之比：λ = N_eff / N_treat。

**原文：** We use λ to construct an iso-accuracy baseline with parameter count N_iso = λ · N_treat.

**译文：** 我们用 λ 构造等精度基线，参数规模 N_iso = λ · N_treat。

**原文：** For our evaluations, we derive f(N) by fitting a log-linear function to the MMLU accuracy scores of the Qwen-3-Dense model family (0.6B, 1.7B, 4B, 8B, 14B, and 32B): f(N) = a·log N + b where a and b are fitted parameters.

**译文：** 评估中，我们对 Qwen-3-Dense 家族（0.6B、1.7B、4B、8B、14B、32B）的 MMLU 精度拟合对数线性函数得到 f(N)：f(N) = a·log N + b，a、b 为拟合参数。

**原文：** We estimate an Effective Parameter Multiplier of λ ≈ 1.35× for Kimi-K2-1T-LatentMoE.

**译文：** 我们估计 Kimi-K2-1T-LatentMoE 的有效参数乘数 λ ≈ 1.35×。

**原文：** For a 1T-parameter base model, this implies an iso-accuracy scale of N_iso ≈ 1.35T, corresponding to an increase of (1.35 - 1.0)T ≈ 0.35T ≈ 350B parameters.

**译文：** 对 1T 参数基模型，这意味着等精度规模 N_iso ≈ 1.35T，相当于增加 (1.35 - 1.0)T ≈ 0.35T ≈ 350B 参数。

**原文：** Guided by this target, we construct a physical iso-accuracy baseline, denoted Kimi-K2-1.35T, by scaling the native architecture depth from 61 to 80 layers.

**译文：** 依此目标，我们通过将原生架构深度从 61 层扩到 80 层，构造物理等精度基线 Kimi-K2-1.35T。

**原文：** This construction matches the projected effective capacity implied by LatentMoE and enables a direct inference-efficiency comparison against a standard model of comparable predictive power.

**译文：** 该构造匹配 LatentMoE 隐含的投影有效容量，从而能与预测能力相当的标准模型直接比较推理效率。

**原文：** ℓ-MoE-acc achieves an accuracy gain at fixed parameter and FLOP budget.

**译文：** ℓ-MoE-acc 在固定参数与 FLOP 预算下取得精度增益。

**原文：** When we enforce an accuracy-matched comparison using the standard MoE architecture, the required scaling incurs a marked serving penalty.

**译文：** 当我们用标准 MoE 架构做精度匹配对比时，所需扩展带来显著的服务惩罚。

**原文：** Across the projected Pareto frontier (Figure 7), Kimi-K2-1.35T is approximately 1.24×–3.46× slower than Kimi-K2-1T-LatentMoE, indicating that ℓ-MoE-acc provides a more favorable accuracy-latency trade-off than increasing model size through the standard MoE architecture to reach the same accuracy target.

**译文：** 在投影帕累托前沿（图 7）上，Kimi-K2-1.35T 比 Kimi-K2-1T-LatentMoE 慢约 1.24×–3.46×，表明 ℓ-MoE-acc 比"用标准 MoE 扩大模型尺寸以达到同等精度目标"给出更有利的精度–时延权衡。

**原文：** Relative to native Kimi-K2-1T, Kimi-K2-1T-LatentMoE introduces additional computation due to latent projection operators.

**译文：** 相对原生 Kimi-K2-1T，Kimi-K2-1T-LatentMoE 因潜投影算子引入了额外计算。

**原文：** In our projections, native Kimi-K2-1T remains close, within up to ~9% of Kimi-K2-1T-LatentMoE, indicating that projection overhead is small compared to the cost of achieving the same accuracy gain via standard scaling to Kimi-K2-1.35T.

**译文：** 在我们的投影中，原生 Kimi-K2-1T 差距很小（在 ~9% 以内），说明相比通过标准扩展至 Kimi-K2-1.35T 获取同等精度增益的成本，潜投影开销很小。

## 5. Related Work

**原文：** Mixture-of-Experts (MoE) models have become a cornerstone of state-of-the-art large language model services.

**译文：** 混合专家（MoE）模型已成为最先进大语言模型服务的基石。

**原文：** In this work, we challenge the original MoE design paradigm for the first time and introduce an alternative architecture that achieves higher accuracy under both iso-parameter and iso-FLOP constraints.

**译文：** 本文首次挑战原始 MoE 设计范式，提出一种在等参数与等 FLOP 约束下均达更高精度的替代架构。

**原文：** In parallel, the community has developed a rich set of model compression techniques to reduce inference cost, including quantization and sparsity.

**译文：** 与此同时，社区已发展出丰富的模型压缩技术以降低推理成本，包括量化与稀疏化。

**原文：** At the expert level, pruning and merging methods have also been proposed.

**译文：** 在专家层面，也提出了剪枝与合并方法。

**原文：** These approaches are orthogonal to the LatentMoE design and can be composed with it to yield further efficiency gains.

**译文：** 这些方法与 LatentMoE 设计正交，可与其组合带来进一步效率收益。

**原文：** The closest related work to this paper is probably MoLAE.

**译文：** 与本文最接近的相关工作大概是 MoLAE。

**原文：** MoLAE is a post-training compression method built on low-rank approximation of expert weights in a latent space.

**译文：** MoLAE 是一种后训练压缩方法，基于潜空间内专家权重的低秩近似。

**原文：** Although the two methods appear similar at a surface level, LatentMoE makes fundamentally different design trade-offs by coupling expert compression with increased network expressivity and combinatorial sparsity.

**译文：** 尽管表面相似，LatentMoE 做出了根本不同的设计权衡——将专家压缩与提升网络表达力、组合稀疏性相耦合。

**原文：** By contrast, to compensate for accuracy loss caused by latent-space projection, MoLAE introduces grouped latent projections and restricts compression to only part of the experts (FC2).

**译文：** 相反，为补偿潜空间投影造成的精度损失，MoLAE 引入分组潜投影，并将压缩限制在部分专家（FC2）上。

**原文：** These design choices, in turn, forgo communication savings during token dispatch and limit memory bandwidth reduction, ultimately constraining the achievable efficiency gains.

**译文：** 这些设计选择反过来放弃了 token 分发时的通信节省、限制了显存带宽降低，最终约束了可达的效率收益。

**原文：** As discussed in Section 2, efficient MoE serving is not FLOP-bound; reducing FLOPs alone is not enough to improve the Pareto frontier of accuracy vs. throughput vs. latency.

**译文：** 如第 2 节所述，高效 MoE 服务并非 FLOP 受限；仅降低 FLOP 不足以改善"精度 vs. 吞吐 vs. 时延"的帕累托前沿。

**原文：** Concurrent work explores improving model quality under fixed compute by modifying residual connectivity rather than the expert path.

**译文：** 同期工作探索在固定算力下通过修改残差连接（而非专家路径）提升质量。

**原文：** Manifold-Constrained Hyper-Connections (mHC) improves quality under iso-compute by widening the residual stream and increasing residual-path connectivity.

**译文：** 流形约束超连接（mHC）在等算力下通过拓宽残差流、增加残差路径连通性来提升质量。

**原文：** Achieving this requires a materially different residual topology and a learned connection-generation mechanism.

**译文：** 实现这一点需要实质不同的残差拓扑与可学习的连接生成机制。

**原文：** We believe LatentMoE and mHC are complementary and can be stacked on top of one another.

**译文：** 我们认为 LatentMoE 与 mHC 互补，可相互叠加。

## 6. Conclusion

**原文：** We presented LatentMoE, a revised Mixture-of-Experts architecture designed to maximize accuracy per FLOP and per parameter by explicitly accounting for the dominant memory bandwidth and communication bottlenecks in modern inference systems.

**译文：** 我们提出 LatentMoE——一种改良的混合专家架构，通过显式考量现代推理系统中主导的显存带宽与通信瓶颈，最大化每 FLOP 与每参数精度。

**原文：** By projecting tokens into a lower-dimensional latent space, LatentMoE reduces routing all-to-all communication as well as the memory bandwidth and computation required per expert.

**译文：** 通过将 token 投影到低维潜空间，LatentMoE 降低了路由全互联通信，以及每专家所需的显存带宽与计算。

**原文：** These savings are then reinvested into scaling expert count and routing diversity without increasing inference cost.

**译文：** 这些节省随即被再投资于放大专家数量与路由多样性，而不增加推理成本。

**原文：** Across extensive experiments up to 95B parameters, hybrid architectures, and projected trillion-parameter serving scenarios, LatentMoE consistently outperforms standard MoEs on the accuracy–efficiency Pareto frontier.

**译文：** 在高达 95B 参数、混合架构、以及投影的万亿参数服务场景等大量实验中，LatentMoE 在"精度–效率"帕累托前沿上持续优于标准 MoE。
