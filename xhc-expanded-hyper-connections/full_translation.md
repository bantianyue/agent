1 Introduction

Large language model architectures have advanced rapidly through improved attention mechanisms, Mixture-of-Experts, and scaling in width, depth, and data. Yet the residual stream that carries token representations across layers remains largely unchanged: it still operates as a single identity pathway, offering no learnable control over cross-layer information flow. Hyper-Connections (HC) challenge this design by replacing the single stream with N parallel residual streams governed by learnable mixing matrices. Building on HC, Manifold-Constrained HC (mHC) makes multi-stream residual training stable at scale and represents the state-of-the-art variant. Residual-stream expansion increases the persistent state of models with modest additional FLOPs, offering a form of memory scaling beyond width and depth. The strong gains observed when expanding from N=1 to N=4 in prior results suggest that this is a promising scaling axis. However, existing HC-family methods typically stop at N=4. We study this through mHC, the state-of-the-art HC formulation at scale. Our experiments in Figure 1 show that naively increasing N further yields rapidly diminishing returns: loss improves only marginally from N=4 to N=16, while training FLOPs increase by 32%, leaving this scaling axis largely unrealized.

We argue that this benefit-cost imbalance is not incidental, but stems from two distinct bottlenecks: one limits the benefit of larger N, while the other increases its cost. The first is an information bottleneck: each stream is meant to store a different weighted history of layer outputs, but each layer injects only a single write-back signal into the multi-stream state. As N grows, forming meaningful and diverse stream histories requires richer write-back information than this single signal can provide, making additional streams increasingly redundant. The second is a computational bottleneck: in mHC, the dominant cost comes from generating the residual mapping through an input-dependent projection. Because this projection predicts N² coefficients from an NC-dimensional residual state, its cost scales as O(N³C), making the cost of expansion grow much faster than its performance benefit. Together, these bottlenecks explain why simply adding more streams does not translate into proportionally more useful capacity. They also clarify what it would take to make expansion rate a true scaling axis: the model must supply more diverse write-back information while avoiding the cubic cost of scaling.

We therefore propose xHC (Expanded Hyper-Connections), the first method to achieve meaningful expansion of HC-family models beyond N=4. Building on the stable multi-stream formulation of mHC, xHC makes large-N expansion both effective and affordable through two complementary designs. To increase the benefit of larger N, xHC introduces temporal feature augmentation along the causal token sequence: it enriches the write-back signal with low-cost features from neighboring tokens, using multi-scale causal convolutions to supply more diverse information as the number of streams grows. To control the cost of larger N, xHC introduces a sparse residual-stream architecture that activates only k out of N streams for residual mixing and write-back, while keeping the read path dense so that every layer can still access the full N-stream state. These two designs are structurally decoupled yet highly synergistic: as N grows, temporal augmentation becomes more useful because additional streams require richer write-back information, while sparse residual updates become more valuable because they substantially reduce the extra FLOPs introduced by large-N expansion.

Empirically, xHC delivers substantial gains over both mHC and the vanilla residual baseline. As shown in Figure 2, xHC consistently improves both pre-training loss and downstream performance at the 18B MoE scale. It reaches a lower final training loss than mHC and the vanilla baseline (1.758 vs. 1.776 and 1.799), and improves the average downstream score from 44.8 with mHC to 48.8, while adding only 4.1% training FLOPs relative to the vanilla baseline. xHC also remains effective when the backbone is trained with Muon, indicating that its gains are not specific to AdamW.

More importantly, xHC changes the benefit-cost tradeoff of scaling the expansion rate itself. As shown in Figure 1, on a 2.5B MoE model, increasing N from 4 to 16 in mHC reduces loss by only 0.006 while increasing training FLOPs by 32%. In contrast, increasing N from 4 to 16 in xHC reduces loss by 0.012 with only 4% extra FLOPs. This shows that xHC makes larger N substantially more cost-effective, turning residual-stream expansion into a practical scaling axis.

This improved benefit-cost tradeoff also translates into better compute efficiency across model scales. Our scaling-law experiments in Figure 4 show that, to reach the same loss, the vanilla requires 1.50× compute of xHC and mHC requires 1.19× compute of xHC. This confirms that the improvement is systematic rather than confined to a specific model size.

3 Method

We first recap the HC formulation and its manifold-constrained variant, then analyze why scaling the expansion rate saturates in existing designs. We then present xHC, which uses two coordinated designs to make large-N expansion effective and affordable: temporal feature augmentation enriches the write-back signal, while a sparse residual-stream architecture reduces the cost of large-N residual mixing.

Why Scaling N Saturates in mHC

Understanding this saturation is essential for turning residual-stream expansion from a small-N improvement into a practical scaling axis. Prior results show that early residual-stream expansion is highly effective: increasing N from 1 to 4 brings substantial gains at modest FLOPs cost (less than 2%). This suggests that scaling N could improve model performance by increasing residual memory, providing an axis orthogonal to width and depth. However, existing HC-family methods typically stop at N=4, leaving open whether this axis remains meaningful at larger N. To answer this, we sweep N in {2,4,8,16,32} in mHC under matched training recipes. As shown in Figure 1, scaling beyond N=4 quickly runs into diminishing returns: increasing N from 4 to 16 reduces loss by only 0.006, while training FLOPs increase by 32%. This unfavorable benefit-cost tradeoff motivates us to examine what prevents larger N from translating into useful capacity. We identify two bottlenecks behind this saturation.

Information Supply Bottleneck. In mHC, each of the N streams accumulates a distinct weighted combination of historical layer outputs. However, the write-back to stream i at layer l takes the form where the newly injected information is spanned by only one write-back component, out: different streams can assign different weights to this component, but cannot draw from different components. This can be sufficient at small N, but as N grows, additional streams need more diverse write-back components to form non-redundant histories. Without such diversity, extra streams become increasingly redundant.

Cost Bottleneck. The second bottleneck is on the cost side. In mHC, generating from the NC-dimensional state requires predicting N² coefficients, leading to an O(N³C) input-dependent projection cost. This makes large-N expansion increasingly expensive even when the additional performance gain is marginal. Concretely, mHC at N=16 adds roughly 32% extra FLOPs relative to its N=4 setting for only limited loss reduction on 2.5B MoE, as shown in Figure 1.

The two bottlenecks compound: the information bottleneck limits the benefit of larger N, while the cost bottleneck increases its price. Together they collapse the return on investment of scaling N.

xHC: Expanded Hyper-Connections

xHC addresses both bottlenecks to make expansion rate N a practical scaling axis. It enriches write-back signals with local contextual features and adopts an asymmetric sparse residual-stream architecture: only k active streams undergo residual mixing and write-back, while dense read keeps every layer connected to all N streams. This reduces the dominant generation cost from O(N³C) to O(k³C), with k=4 and N=16 in our main setting.

Enriching the Write-Back Signal

Temporal Feature Augmentation. As analyzed, large-N expansion saturates because each layer provides only a single write-back component to all streams. A direct fix would be to compute a separate output for each stream, but this would multiply the layer FLOPs by N. Instead, xHC enriches the write-back basis by borrowing low-cost local contextual information from neighboring tokens. We aggregate this local information with lightweight causal depthwise 1D convolutions, which preserve autoregressive order and add small overhead.

We apply r causal depthwise convolutions with kernel sizes to the layer output. Different kernel sizes capture neighboring-token information at different contextual ranges, providing multi-granularity write-back components that expand the write-back basis beyond a single layer output. We concatenate these components with the original output. In our main setting, r=3 with kernel sizes {4,8,12}, so K_r=4. The convolutions are per-channel and causal, adding only parameters per layer. We apply temporal augmentation only after MLP layers: attention already mixes positions, and adding temporal augmentation after attention empirically destabilizes training.

Gram-Schmidt Orthogonalization. Because depthwise convolutions operate channel-wise, their outputs can retain a strong component aligned with the original layer output. If these correlated components are directly combined, the augmented write-back signal may contain redundant components and amplify the original direction in an uncontrolled manner. We therefore apply modified Gram-Schmidt orthogonalization over the K_r components. After orthogonalization, we redefine and use these orthogonalized components for all subsequent write-back operations.

Sparse Residual-Stream Architecture

The cost bottleneck comes from residual mixing over all N streams. xHC reduces this cost by updating only k active streams out of N, while keeping dense read access to the full N-stream state. We describe the forward pass in three steps: routing, reading, and writing.

Stream Routing. A router selects the k streams to update at each sublayer. The router observes the full N-stream state and produces per-stream importance scores. We use sigmoid rather than softmax to reduce winner-take-all routing. For stability, we use a fixed-plus-routed scheme: m streams are always active with routing weight 1, while the remaining k-m active streams are selected by TopK routing over the non-fixed streams.

Dense Read. A naive sparse variant would sparsify both reading and writing, but this can disconnect cross-layer information flow: streams updated at one layer may not be selected for reading by the next. xHC therefore keeps the read path dense. Thus every layer can access the full N-stream state, preserving cross-layer information flow even though only k streams are updated.

Sparse Residual Update. In mHC, and are generated from the full N-stream state. xHC instead applies the same generators only to the active state. The post-mapping generalizes the mHC form from to, so that each active stream can independently combine the augmented write-back components. This reduces the dominant residual-mapping generation cost from O(N³C) to O(k³C) while retaining the Sinkhorn constraint on the active stream subset.

Why Both Designs Are Needed

The two designs address complementary bottlenecks. Temporal feature augmentation makes additional streams more informative, but alone leaves dense residual mixing expensive. Sparse residual updates make large N affordable, but alone leave the write-back signal information-limited. Together, they make large-N expansion both meaningful and affordable, with ablations confirming that neither design alone recovers the full benefit of xHC.

4 Experiments

We evaluate xHC through language model pre-training experiments across model scales, compute budgets, expansion rates, ablation settings, and optimizer choices.

Experimental Setup

We conduct experiments in the language model pre-training setting using Mixture-of-Experts (MoE) Transformer models. Unless otherwise stated, we apply xHC and mHC to the same DeepSeekMoE-style Transformer backbone. Specifically, the backbone uses grouped-query attention (GQA) and 144 experts with top-8 routing. We report main downstream results at two MoE scales: an 18B-total, 1.7B-activated model and a 28B-total, 2.7B-activated model. We additionally use a 10B MoE model for ablations and a 2.5B MoE model for N-sweep experiments. Unless otherwise specified, xHC uses N=16 total streams with k=4 active streams. All models are trained with a context length of 8192 tokens.

Main Results

We compare xHC against mHC and the vanilla residual baseline on 18B and 28B MoE models. xHC outperforms both mHC and the vanilla baseline across both scales. At 18B, the average score improves from 44.8 with mHC to 48.8 with xHC. At 28B, the average score improves from 50.5 to 53.6 (+3.1) over mHC. The consistent improvements on the 28B MoE model further demonstrate that xHC remains effective in larger pre-training regimes.

Scaling Laws

The downstream results establish the advantage of xHC at two discrete scales. We next ask whether this advantage persists across a broader compute range. To fit scaling laws, we train a separate suite of four models for each method under matched recipes. Figure 4 shows that xHC traces a lower fitted loss curve than both mHC and the vanilla baseline across the measured compute range. The resulting matched-loss comparison shows that the baseline and mHC require about 1.50× and 1.19× the compute of xHC, respectively.

Scaling the Expansion Rate

We evaluate whether xHC turns the expansion rate N into a meaningful scaling axis. We sweep N in {2,4,8,16} in xHC on a 2.5B MoE model, and compare against mHC at matched expansion rates. In mHC, all N streams participate in dense residual mixing, so the residual-mixing overhead grows rapidly with N. In xHC, increasing N enlarges residual-memory capacity while the sparse update cost remains controlled by k. Figure 1 plots language modeling loss during training against training FLOPs as N increases. Under xHC, loss decreases consistently from N=2 to N=16, with each doubling of N yielding a clear improvement at small additional FLOPs. In contrast, mHC shows rapid saturation.

Ablation Study

Ablation studies use a 10B MoE model trained under a matched data budget. Incremental Construction: we start from mHC at N=16 and incrementally add the two ingredients of xHC. Adding temporal feature augmentation improves validation loss from 1.998 to 1.984, confirming the benefit of enriching the write-back signal at large N. Adding the sparse residual-stream architecture then preserves this validation loss (1.983) while reducing FLOPs overhead from 20.1% to 3.3%.

Information Bottleneck Ablations. We add temporal feature augmentation alone to dense mHC at N in {4,8,16}. Figure 5 shows that the loss gap relative to mHC becomes increasingly negative as N grows. This trend is consistent with our diagnosis that the information bottleneck becomes more severe at larger expansion rates.

Sparse Architecture Ablations. Removing both Dense Read and fixed streams exposes the risk of information disconnection, degrading loss to 1.997. Dense Read mitigates this by letting every layer access all N streams. Fixed streams further stabilize sparse updates by providing guaranteed write targets. The active-stream budget k controls the sparsity-quality tradeoff: k=2 under-provisions active streams (1.991), k=8 yields a marginal gain (1.982) at higher cost, and k=4 balances the two. Sigmoid routing outperforms Softmax (1.983 vs 1.988).

Compatibility with Muon Optimizer

The experiments above use AdamW. We further evaluate xHC under Muon, which uses Newton-Schulz iteration to construct orthogonalized matrix updates. When training with Muon, we make two practical adaptations. First, we remove Gram-Schmidt (GS) orthogonalization from temporal feature augmentation. Second, we apply Muon only to the backbone attention and MLP projection matrices, while keeping xHC-specific routing and mapping projections under AdamW. xHC maintains substantial gains over the Muon baseline across benchmarks, indicating that the architecture is compatible with Muon and remains effective beyond AdamW.

5 Practical Deployment

This section examines the practical training efficiency of xHC. We first analyze its computation and memory-access overhead, then introduce xHC-Flash to reduce repeated full-state accesses.

Efficiency Analysis

The FLOPs overhead of xHC is modest: with our default N=16, k=4 setting, xHC adds 3.0% training FLOPs at the 28B scale. The primary source of runtime overhead for HC-family methods is often memory traffic rather than arithmetic FLOPs. With N=16 and k=4, xHC averages 55C reads and 18.5C writes per sublayer, for a total of 73.5C. This is approximately 2.2× the 34C required by mHC at its standard N=4 setting, primarily because xHC performs two full-state reads.

xHC-Flash: A Lightweight Variant

To reduce xHC's memory traffic, we introduce xHC-Flash, which amortizes full-state operations across consecutive sublayers. Sharing within one block reduces the per-sublayer traffic from 73.5C to 51C. Its natural four-sublayer extension, xHC-Flash-4sub, further reduces the traffic to 40C. At this level, its traffic is comparable to that of mHC at N=4 (34C), and it retains most of xHC's performance gains.

Performance. xHC-Flash matches full xHC in validation loss (1.983) while reducing I/O from 73.5C to 51C. xHC-Flash-4sub further reduces I/O to 40C, comparable to the 34C of mHC at N=4, while maintaining a clear loss advantage over mHC (1.984 vs 2.004).

Infrastructure Design

A direct implementation of xHC consists of many small, largely memory-bound operators. Our implementation targets the default N=16 and k=4 configuration and organizes these operations into two stages: mapping generation and mapping application. Within each stage, operations sharing the same inputs are fused to reduce memory traffic and kernel launches.

End-to-end throughput. We measure wall-clock training throughput on the 18B MoE model. Our reimplemented mHC (N=4) fused kernels add approximately 15% training overhead over the baseline. xHC-Flash-4sub adds approximately 11% overhead on top of mHC. With pipeline-communication overlap, such as DualPipe, the effective end-to-end overhead can be further reduced. For inference prefill at 2K tokens, mHC adds 11.4% extra overhead over the vanilla baseline, while xHC-Flash-4sub adds 12.9%.

6 Conclusion

We presented xHC, a method for making residual-stream expansion in HC-family models effective and affordable beyond the common N=4 setting. We showed that directly scaling N in mHC is limited by two bottlenecks: insufficient write-back information and the cubic cost of residual-mapping generation. xHC addresses these bottlenecks with temporal feature augmentation and a sparse residual-stream architecture that preserves dense read access while updating only k active streams. Across language model pre-training experiments, xHC scales to N=16 with k=4, significantly outperforms mHC and the vanilla baseline on 18B and 28B MoE models, improves matched-loss compute efficiency, and remains effective under Muon. xHC-Flash and fused kernels further reduce the memory and implementation overhead needed for practical large-N training. These results support expansion rate as a practical scaling dimension for HC-family models.
