# vLLM x AgentX: Optimizing for Real-World Agentic Serving 

- Author: @vllm_project (vLLM)
- Published: Tue Sep 08 20:51:54 +0000 2026
- URL: https://x.com/vllm_project/status/2097427730983776758
- Likes: 53
- Retweets: 9
- Replies: 1
- Bookmarks: 34
- Views: 0

TL;DR: Agentic workloads are becoming a major source of vLLM traffic. Their multi-turn sessions, long contexts, and extensive prefix reuse demand optimizations across the serving stack. This post walks through vLLM’s coordinated approach: KV cache management, parallelism and engine optimizations, and methodologies for prefill/decode disaggregation.

Measured on AgentX, SemiAnalysis’s public agentic benchmark, vLLM achieves up to 130K total tokens per GPU-second on DeepSeek V4 Pro, and an interactivity of up to 376 tokens per second on MiniMax M3. Across DeepSeek V4 Pro, Minimax M3, and Kimi K3, vLLM delivers a 14.6×–106× serving-cost advantage over Opus 5 API pricing.

## Characterizing agentic workloads: a second look

Since our first post on serving agentic workloads in May, agentic traffic share has continued to grow. As of June 2026, OpenAI reported that Codex generated 64% of combined Codex and ChatGPT output tokens among enterprise customers.

This growing token consumption stresses serving infrastructure along two axes: cost and latency. Cost efficiency determines how many concurrent agents fit in a fixed hardware budget; latency affects how quickly each agent progresses through reasoning and tool-use cycles. Optimizing agentic serving requires improving the latency-cost frontier as a whole.

To evaluate that frontier under representative traffic, SemiAnalysis recently released AgentX, a public benchmark built from real-world agentic coding traces. These traces provide a concrete view of the workload characteristics that serving systems must accommodate, as illustrated in the Figure:

- Long-running, multi-turn sessions. Median 43 turns per session.

- Long contexts with short outputs. Median input 142K tokens, median output 444 tokens.

- Extensive prefix reuse. Prefix-cache hit rate above 96%.

- Subagent-heavy traffic. 44% of sessions contain at least one subagent, with a median of four subagent rollouts among those sessions.

## Challenges in serving agentic workloads

These workload characteristics create three challenges for efficient serving.

1. Prefix cache pressure. Every turn of a multi-turn session replays the full conversation so far. To keep many sessions running at once, the engine has to offload KV caches between turns. This is even more challenging when deployed at scale, as KV cache management, prefix caching, and offloading must take the strain and work efficiently across GPUs, prefill/decode disaggregated instances, and replicas.

2. Execution efficiency. Agentic workloads feature long contexts and tight latency requirements, so the engine has to process more tokens and do more work per token in less time. This requires adapting parallelism, kernels, scheduling, speculative decoding, and other engine optimizations properly to the new request shape.

3. Finding the right P/D ratio. Context lengths and cache hit rates vary wildly across sessions and subagents, and routing must efficiently balance cache affinity and load across ranks. These factors make it difficult to find the optimal P/D ratio under different concurrency for maximized throughput.

## Data plane: keep KV caches warm and close to compute

Hybrid KV cache management: a foundation that keeps evolving

KV cache management has been central to vLLM since PagedAttention, and agentic workloads with long contexts put heavier pressure on KV cache capacity. Modern hybrid models complicate allocation further by combining sliding-window and linear attention with full attention, whose cached blocks differ in size and lifetime.

vLLM’s hybrid KV cache manager tackles the complexity with a simple core idea: having a uniform memory page as the basic allocation unit, then managing those units through one shared block pool.

A shared pool lets vLLM reallocate memory dynamically on demand instead of statically partitioning capacity by attention type. This matters because full-attention KV grows with sequence length, while sliding-window and recurrent state follow different lifetimes and scaling rules. The best partition therefore changes with concurrency, context length, and prefix-reuse patterns.

The abstraction continues to evolve as new architectures expose fragmentation and transfer inefficiencies. For example, DeepSeek V4’s initial KV cache layout fragments different cache types into three size buckets and allocated 92 separate tensors. As shown in the figure below, the fragmentation causes some extra padding waste, and remains inefficient for P/D transfer and KV cache offloading.

The new packed KV cache layout instead, stores cache groups and layers in one contiguous backing allocation per block rather than 92 fragmented ones. This reduces the descriptor and PD transfer overhead, and also permits a smaller allocation unit when the FP4 indexer is enabled, saving roughly 10% of KV cache memory.

Hierarchical KV cache offloading: distributed KV cache pool with smart retention policies

To preserve prefix caches beyond GPU memory capacity and across each engine, vLLM has integrated MooncakeStore to provide a distributed KV cache pool, with details covered in our previous blog. Since the integration, we have seen its increasing adoption, and we keep shipping new features and performance improvements for capacity, efficiency, and retention on agentic workloads.

Model architecture parity. KV cache offloading integration remains a first-class citizen in vLLM with full support for new model architectures including: sparse attention, compressed attention, linear attention, etc. This is done while making sure that other engine features remain fully functional and performant, such as asynchronous scheduling, P/D disaggregation, speculative decoding, parallelism, etc.

Hierarchical KV cache offloading. vLLM supports hierarchical tiers for the distributed KV cache pool to further extend capacity with disks and extra CPU-only nodes. This is achieved with vLLM’s MooncakeStore standalone-store mode, which makes an external Mooncake client own the CPU pool and disk tier, and turns vLLM workers into pure requesters. By launching a standalone Mooncake client on each node, we freely expand the KV cache pool with CPU memory and disks. We have also integrated the distributed shared KV cache pool with routers, such as Dynamo and llm-d, to simplify the routing policy so that requests can get cache hits on any instance.

Performance optimizations. Hybrid models must construct keys and perform lookups separately for each attention type, which multiplies CPU overhead. We reduced this cost through more efficient data structures, asynchronous lookup, work moved off the scheduler’s critical path, and parallel send and receive operations. Implementation details are available in PR#46188, PR#45444, PR#45659, and PR#47317.

Session-aware prefix-cache retention: For hybrid models with linear or sliding-window layers alongside full attention, prefix reuse requires preserving linear state or sliding-window caches. Keeping these snapshots at every token is expensive, so we combine two complementary policies:

1. Interval-based retention automatically preserves prompt-end caches/linear states at each turn. Subsequent turns and forked subagents, which typically replay and extend earlier turn’s context, can then reuse the cached context.However, shared prefixes typically end within a turn, so interval-based retention may not preserve a checkpoint. To capture this reuse, we introduce a second policy:

2. Marconi-style selective retention retains a checkpoint when a prefix is observed a second time. When a request encounters a previously observed prefix without a retained checkpoint, vLLM recomputes the missing state and saves a checkpoint at that boundary. Subsequent requests sharing the prefix can then reuse it.

Together, these policies preserve high cache hit rate and avoid excessive storage overhead for large-scale agentic workloads. Our vLLM Kimi K3 blog explains the technical details in depth.

Execution plane: generate tokens fast

Model-specific parallelism

Modern inference systems expose several axes of parallelism, such as tensor parallelism (TP), data parallelism (DP), expert parallelism (EP), pipeline parallelism (PP), and context parallelism (CP).

Determining the optimal parallelism, however, depends on the model architecture, hardware topology, workload patterns, and latency SLOs. In this section, we examine two representative models on NVIDIA GB/B-series GPUs and AMD counterparts and discuss our optimizations and findings.

Kimi K3

Kimi K3 features multi-head latent attention (MLA) and Kimi delta attention (KDA). Since MLA compresses KV into a single latent space with one head, plain tensor parallelism (TP), which replicates that latent cache across ranks, is not very efficient.

As an alternative to TP, we have found strong performance gains in decode context parallelism (DCP), which shards the cache along the sequence dimension, leaving each rank with 1/N of the KV state. Specifically, DCP offers two benefits for agentic workloads:

- Lower decode latency. MLA attention is memory-bound, and its cost grows with context length. As agentic prefixes grow, attention becomes a larger share of each decode step.

- Higher throughput and KV capacity. Avoiding KV cache replication enables the engine to keep more sequences in flight without stalling on KV admission, and hence achieve higher throughput.

DCP’s tradeoff is extra communication: the KV cache is sharded by sequence, so every MLA decode layer needs a query gather before attention and a partial-output reduction after it.

We carefully optimized the DCP compute path to bypass NCCL operations and avoid such overheads. We leverage symmetric-memory buffers that peer GPUs can directly load/store. Queries are multicast directly into the buffers consumed by attention kernels. Each GPU then writes its partial attention outputs and log-sum-exp (LSE) statistics directly into its peers’ receive slots, where each rank locally merges the results with online softmax. These GPU-to-GPU writes are fused with the computation into the same kernels, cutting the latency by about 13% per layer against the default DCP8 implementation.

A larger scale-up domain can change the best strategy. For example, on an NVL72-class system, wide EP with data parallelism (DEP) can scale better than DCP and deliver higher throughput at the same decode latency SLO. This is because at larger, multi-node DCP sizes, communication cost in sharded attention outweighs the compute it saves. DEP assigns requests and their KV caches to different data-parallel ranks, avoiding DCP’s attention collectives while sharding the MoE experts across ranks.

DeepSeek V4

DeepSeek V4 also has MLA-style KV caches that replicate under TP, leading to inefficient memory use. In addition, its unique compressed sparse attention makes TP head sharding compute inefficient for three reasons:

- The compressor paths produce only one shared KV representation per compressed position rather than independent per-head states. TP therefore cannot shard compute along the KV-head dimension, and every rank repeats the compressor work.

- The indexer, while having 64 heads, produces only one global top-k selection per token. The current TP path therefore replicates the full indexer on every rank, avoiding a dense score reduction before top-k but duplicating the work.

- Sparse MLA is dominated by scanning and gathering top-k KV cache entries, not by attention arithmetic. TP repeats much of this memory-bound work on every rank while dividing only the cheaper head-wise computation.

In our practice, prefill context parallelism (PCP) performs best for long prefills, while data and expert parallelism (DEP) works well across a broader range of serving conditions.

PCP shards the prompt sequence (the query tensor), distributing compressor and indexer work across ranks, while giving sparse MLA a wider, more efficient head-local shape. For a 32K prompt, PCP8 achieves a 2.65x prefill speedup over TP8, substantially reducing TTFT. However, it still replicates decode-side state across ranks, and hence is most suitable for dedicated prefill workers.

DCP is less effective for DeepSeek V4 than for Kimi K3 due to its more complex model architecture (see the bitter lessons).

DEP instead distributes requests and decoded tokens across data-parallel ranks and keeps the attention path completely local. This makes DEP our default for most DeepSeek V4 configurations.

Scheduling mixed agentic traffic at two levels

Agentic serving mixes frequent, append-only requests with long prefix reuse and short prefill, with occasional long fresh prefills spanning tens of thousands of tokens. This creates two scheduling problems: within an instance, a long prefill can block short interactive turns; across DEP ranks, uneven prefill placement creates load imbalance. We address them with two complementary scheduling controls.

Breaking head-of-line blocking

By default, vLLM’s chunked-prefill scheduler follows the first-in, first-out order. One long prefill can claim the entire budget step after step, and the short turns queued on the same rank cannot be scheduled at all until the long prefill finishes. This is known as head-of-line blocking and is illustrated below in the session view of one rank’s queue.

We tackle this issue with a simple scheduling policy: we use --long-prefill-token-threshold to cap how many tokens one request may schedule per step. With a 512-token threshold, a long prefill leaves room for short turns to join the same batch and begin decoding sooner. With DeepSeek V4 Pro on B300s, this increases tokens per GPU-second (TPGS) by up to 93% and improves p90 interactivity by roughly 2.3x. The trade-off is higher TTFT for the long request itself, so TTFT-sensitive deployments should use a higher threshold.

Align DEP prefill schedule cadence

DEP introduces a second inefficiency: MoE all-to-all communication forces ranks to advance in lockstep, so a rank processing prefill work slows the entire group. When prefills arrive on different steps across ranks, this penalty is repeatedly exposed.

To alleviate this imbalance, we set --prefill-schedule-interval to admit prefill work only every Nth engine step, using a counter aligned across data-parallel ranks. This concentrates prefill work onto the same steps across ranks and increases the fraction of intervening steps devoted entirely to decode. The figure below illustrates this cadence across a DEP8 group.

Scaling with optimal P/D disaggregation configurations

Optimizing a single engine is not enough to find the best latency-cost point for a distributed deployment, and more GPUs or disaggregation will not automatically improve the frontier. The prefill and decode stages must be rate-matched.

We use a standardized two-phase rate-matching methodology that can be automated by an agentic workflow:

Phase 1: Saturation profiling. Benchmark prefill-only and decode-only deployments separately, sweeping parallelism strategies (e.g., TP vs. wide-EP) and deployment sizes (8/16/32 GPUs) with increasing concurrency until throughput saturates. The output is a saturation table: max prefill/decode req/s for each (parallelism, size) configuration.

Phase 2: P:D sweep. Derive the P/D ratio from each configuration’s Phase 1 saturation points, then sweep concurrency on the combined disaggregated deployment to collect metrics across the operating range.

Closing the loop: model-specific kernels and community contributions

Agentic workloads also shift kernel bottlenecks toward long-context attention, speculative decoding, and communication. Here we highlight a few changes with measured end-to-end impact. All our kernels are fully open-sourced, and some have already been adopted by other OSS engines.

For MiniMax M3, a CuteDSL long-context indexer improves reported GB300 indexer latency by roughly 3% to 31%, depending on shape. The upstreamed MSA top-k path improves worst-case kernel performance by up to 4x and AgentX end-to-end throughput by roughly 7%; the speculative-verification path improves medium-batch decode performance by about 20% in reported tests.

For Kimi K3, GEMM and reduce-scatter fusion improves sequence-parallel communication, while latent-tail MoE fusion reduces end-to-end latency by roughly 5%.

For DeepSeek V4, community contributions improved MXFP4 MoE and HCA compression (#43584 and #44230), added multi-stream C4A, and improved cluster-based top-k.

## Performance: agentic-first and openly verifiable

We showcase that vLLM is agentic-first with independent validation on SemiAnalysis AgentX, an open dataset built from $3M of real-world agentic coding traces with 1M context, and a public benchmark infrastructure running on >1000 chips and ~2 MW compute.

The figure shows the Kimi K3 dashboard as an example, and both the benchmark and its results are publicly accessible online at the AgentX Dashboard. We strongly recommend checking out the pareto results for the other models and configurations.

In this post, we focus on the results of three open frontier models: DeepSeek V4 Pro, Minimax M3, and Kimi K3. For each model, we display the highest-throughput vLLM configuration that maintains p90 interactivity above 50 tokens per second per user, which is a commonly demanding latency SLO. The table below summarizes the key results.

DeepSeek V4 Pro represents a high-throughput and cost-efficient use case. A 12-chip GB300 PD deployment serves 256 concurrent agent sessions while sustaining 58.3 tokens/s/user at p90. At this operating point, it processes 83K total tokens per GPU second.

MiniMax M3 pushes interactivity further and features high response speed. With only 2 B300s, it sustains 74.2 tokens/s/user at P90 and delivers 70K total TPGS.

Kimi K3, as one of the largest open frontier models, demonstrates the case for frontier intelligence. At 2.8 trillion parameters, it is too large for a conventional single-server deployment; 16 GB300s sustain 62.7 tokens/s/user at P90 while processing 11.8K total TPGS.

Besides performance, we find cost to be a highly relevant metric to users’ daily use and tokenomics. The table below compares the cost of all three open models against Opus 5.

The cost advantage comes from the defining property of agentic traffic: with a theoretical cache hit rate of more than 96%, vLLM effectively reuses prefixes and unleashes serving efficiency across all three models under the same setting as the table above.

For DeepSeek V4 Pro, serving the measured workload costs approximately $28 per hour in GB300 infrastructure TCO. Processing the same token volume with Opus 5 would cost approximately $2,926, even after applying the cache-read price to every theoretically reusable token. MiniMax M3 on B300s shows an 85x cost advantage, while Kimi K3 on GB300s remains 14.6x cheaper despite its substantially larger model size.

We report numbers as of today, but the dashboard is live and interactively accessible to everyone. The AgentX harness is public at SemiAnalysisAI/agentx-harness, and every result above links to its run on the InferenceX dashboard for easy reproduction.

## The bitter lessons: where we failed and what we learned

Every failed idea narrows the search space. We did observe a few cases where plausible intuitions did not survive end-to-end measurement. While we are still improving these features, we’d also like to share what we have learned so far.

Pipeline parallelism (PP) does not fit warm agentic turns

PP, including chunked pipeline parallelism (CPP), performs well on long, fresh prompts. Large prefills provide enough work to keep pipeline stages occupied, and throughput can scale nearly linearly with little communication cost.

Most agentic turns, however, already have system prompts and previous turns cached, and each new request may add only a few hundred or a few thousand tokens. There is not enough fresh computation to fill the pipeline efficiently, and pipeline bubbles consume much of the potential gain.

The lesson is not that PP is ineffective. It is effective for cold, compute-heavy prefills, but it should not be the default for warm, prefix-heavy turns that dominate agentic sessions.

Decode context parallelism (DCP) does not transfer cleanly to DeepSeek V4

DCP works well for pure MLA models (e.g., DeepSeek R1, Kimi K2.5, and K2.7) and hybrid MLA models (e.g., Kimi K3) as elaborated earlier. However, realizing a similar benefit for DeepSeek V4 is way more challenging due to its more complicated attention stack. The compressed sparse attention and highly compressed attention include an indexer, an additional compressor, and the main attention operation. Context parallelism must partition and coordinate all of these sublayers, introducing substantial communication and implementation complexity.

We invested heavily in overlapping communication with computation and optimizing the corresponding kernels. Even after those improvements, DCP only matched DEP rather than surpassing it. The result reinforces a broader point from the execution-plane section: parallelism must follow model architecture. A strategy that succeeds for one latent-attention model may not generalize to another.

Load balance does not guarantee better performance

In aggregated DEP deployments, we observed substantial imbalance in KV cache usage across ranks. The natural response was to balance requests according to queue depth, running tokens, or current KV utilization.

However, in our experiments with AgentX, all of these policies underperformed simple session-aware sticky routing. This is due to cache locality; many agentic sessions have short inter-turn delays, so the next turn frequently arrives while its prefix remains resident on the previous GPU. Moving the session to a less-loaded rank, although its prefix caches are preserved in the distributed KV cache pool, forces the system to retrieve KV caches. The transfer itself is asynchronous and overlaps with computation, yet still not free. Prefetched blocks temporarily occupy GPU KV cache capacity, reducing the number of sequences the destination rank can admit. The system can therefore achieve a more balanced queue while processing fewer concurrent requests overall.

For workloads with short inter-turn delays, preserving session locality is more valuable than perfectly balancing instantaneous load. Routing decisions must account for the state already resident on each worker, not only the amount of queued work.

## The path ahead: planned optimizations and future work

The next step is to make agentic structure explicit throughout the serving stack, and here we exemplify a few in each layer.

In the control plane, we can make routing more explicit for first-turn requests, which tend to need long fresh prefills to fill up the prefix cache, and turn 2+ requests, which get high cache reuse and relatively short append prefill. This separation avoids head-of-line blocking and allows us to configure engine setups and parallelism differently, for example, PCP and CPP, for maximized efficiency on both sides.

In the execution plane and data plane, we are working with the community to support:

- Agent hints. Agentic frameworks or harnesses could carry hints along with the requests, such as session structure, potential branching points and cache positions, tool call latencies, or the lifecycle of sessions, etc. Our first step is to consume these hints with standardized APIs, and then use them to guide the engine on scheduling, cache eviction policies, and other optimizations.

- Programmable KV cache. Different workloads require different placement, retention, replication, and eviction policies. A programmable interface would allow users to control prefetching, eviction, or soft pinning KV caches given the workload patterns.

- Session-based KV cache management. Inter-turn gaps create an opportunity to move the retained KV state toward the worker likely to serve the next turn. Prefetching during this idle interval can hide transfer latency and reduce cold resumptions.

## Acknowledgments

This effort was led by @inferact with extensive support from the vLLM community. We thank @SemiAnalysis_ for developing and operating the open AgentX benchmark and for making its methodology and results reproducible.
