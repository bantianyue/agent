[](https://www.perplexity.ai/hub)Products[Enterprise](https://www.perplexity.ai/enterprise)[Customers](https://www.perplexity.ai/hub/customers)[Pricing](https://www.perplexity.ai/hub/pricing)Resources[Try Perplexity](https://www.perplexity.ai/)

[Blog](https://www.perplexity.ai/hub/blog)[Research](https://www.perplexity.ai/hub/blog/category/research)Optimizing On-Device Inference for Apple Silicon

# Optimizing On-Device Inference for Apple Silicon

A custom local engine that improves prefill and decode throughput.

Sep 1, 2026

Authors Perplexity Engineering

Contents

1.   00 Introduction
2.   01 Qwen-specific optimization opportunities on Apple silicon
3.   02 Optimization strategy
4.   03 Prefill: reuse weights and keep routing on the GPU
5.   04 Decode: minimize the bytes moved per token
6.   05 Limits of further optimization
7.   06 End-to-end performance
8.   07 Built for the local platform

0% read

[Hybrid Compute on Apple silicon](https://www.perplexity.ai/hub/products/hybrid-compute) orchestrates a task between frontier intelligence in the cloud and a local model on the Mac. Cloud models handle research and reasoning, while a local model works with private files and apps on the Mac.

For this division of labor to feel seamless, local inference must keep pace with the rest of the task. That requires an engine that can process prompts quickly and sustain a high token-generation rate.

Lily, our lightweight local inference engine, is built specifically for Apple silicon and [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), with separate optimizations for prefill and decode. The engine will be open-sourced soon.

## Introduction

A common way to run LLMs on a Mac is with [MLX](https://github.com/ml-explore/mlx), Apple’s open-source machine learning framework for Apple silicon. Its companion library, [MLX-LM](https://github.com/ml-explore/mlx-lm), adds the components needed to load and generate text with a wide range of language models. Together, MLX and MLX-LM provide an off-the-shelf, general-purpose stack for local LLM inference.

Qwen3.6-35B-A3B is a sparse, hybrid model: it uses mixture-of-experts (MoE) routing and combines fixed-size recurrent states with full attention. These architectural choices reduce the amount of computation required, but they also create irregular workloads. Tokens route to different expert weights, and recurrent states are sequential in nature.

MLX-LM already selects optimized kernels for inference phases and common workload shapes, but its reusable operations must support many model architectures. An engine dedicated to Qwen can specialize at the model and runtime level, coordinating kernels, data movement, and scheduling around the model’s fixed structure.

Lily implements this specialization end to end in a single process. A Rust runtime loads the model checkpoint and manages the session state and generation loop, an OpenAI-compatible chat-completions API accepts requests and streams tokens, and custom Metal kernels execute Qwen-specific operations. Neither PyTorch nor MLX is in the execution path.

![Image 1](https://cdn.sanity.io/images/aqo64vfr/production/bc66a9239d6809e82a9c61b663ace26b7d7ab109-2804x3036.png?w=1680&q=90&fit=max&auto=format)

FIG. 01 Where generality and specialization sit in the two inference stacks. MLX-LM describes the model as composable MLX array operations, which MLX schedules through reusable kernels. Lily instead places the model structure, phase-specific execution plans, and kernel selection in a single Rust runtime built around Qwen and Apple silicon.

We measure prefill and decode performance separately. Prefill throughput captures how quickly the engine processes the prompt; decode throughput captures how quickly it generates output tokens.

We benchmark Qwen3.6-35B-A3B on a single MacBook Pro powered by an M5 Max with a 40-core GPU and 128 GB of unified memory. Across ten prompt lengths for prefill and ten context lengths for decode, from 256 to 128K tokens (K = 1,024), the engine averages 1.23× MLX-LM’s prefill throughput and 1.35× its decode throughput. At a 4K-token prompt and a 4K-token decode context, the custom engine reaches 5,749.9 prefill tokens per second and 186.6 decode tokens per second, compared with 4,737.5 and 140.9 for MLX-LM. Across a multi-turn session, these time savings accumulate with each additional model call.

![Image 2](https://cdn.sanity.io/images/aqo64vfr/production/afff86322e6682ce5b23f4cb5f64b3c9df2ed1c9-2560x1672.png?w=1680&q=90&fit=max&auto=format)

FIG. 02 Arithmetic mean throughput across ten equally weighted lengths from 256 to 128K tokens. Lily averages 4,156 prefill tokens/s versus 3,388 for MLX-LM (1.23×), and 170.0 decode tokens/s versus 126.4 (1.35×). Prefill varies prompt length; decode varies context length.

Next, we explain how Qwen’s architecture creates model-specific optimization opportunities on Apple silicon. We then walk through the resulting prefill and decode changes. We also cover where additional optimization stops paying off before closing with an end-to-end comparison against MLX-LM.

## Qwen-specific optimization opportunities on Apple silicon

### Qwen creates three distinct workload shapes

Qwen3.6-35B-A3B contains 35 billion parameters but activates only about 3 billion for each token. A router scores 256 expert subnetworks and selects eight, alongside one shared expert that processes every token. This sparse MoE design reduces computation but produces uneven work: experts receive different numbers of tokens, and each token requires weights from a different combination of experts.

Qwen also combines 10 full-attention layers with 30 [Gated DeltaNet](https://arxiv.org/abs/2412.06464) layers. These two layer types retain earlier information in different ways.

The attention layers use [grouped-query attention (GQA)](https://arxiv.org/pdf/2305.13245). Qwen has 16 query heads and two key–value (KV) heads, with eight query heads sharing each KV head. Sharing makes the KV cache smaller and allows cached data to be reused across query heads. The cache still stores new keys and values for every token, so each decode step reads more data as the context grows.

Gated DeltaNet instead compresses earlier information into a fixed-size recurrent state. A learned gate controls how much of the existing state to retain, while a delta update incorporates information from the current token. The model defines these updates recurrently, so each token depends on the state produced by the preceding token. During prefill, however, an engine can evaluate the same computation in two ways. It can scan through the tokens directly while carrying the state forward, or reorganize the updates into blocks that expose more matrix operations and token-level parallelism. Which approach is faster depends on the model dimensions, workload, and hardware.

Together, these structures create three computational patterns: uneven expert groups, attention over a growing cache, and a fixed-size recurrence that can be evaluated directly or in blocks.

### Apple silicon provides different paths for different workloads

Prefill processes many prompt token activation rows at once. The local workload considered here typically decodes one request at a time (batch 1) and processes one new row per step. This difference changes how the same model weights are used. Prefill can reuse each block of weights across hundreds or thousands of rows. Decode largely cannot, since each new token requires another pass through the weights.

Apple silicon places the CPU and GPU behind unified memory, a single physical memory pool accessible to both. This allows the model to remain resident without maintaining a separate GPU copy, but it does not make data movement free. Reading weights and intermediate values still consumes memory bandwidth, while registers and other on-chip storage are faster but much smaller.

The M5 GPU also provides different compute paths. Prefill’s linear layers use general matrix–matrix multiplication (GEMM), applying a weight matrix to many rows at once. Compatible GEMMs can use the [Neural Accelerator](https://www.apple.com/newsroom/2025/10/apple-unleashes-m5-the-next-big-leap-in-ai-performance-for-apple-silicon/) in each GPU core through [Metal 4 tensor operations](https://developer.apple.com/documentation/metal/running-inline-ml-operations-in-a-shader-with-metal-4). Batch-1 decode instead uses general matrix–vector multiplication (GEMV), applying the same weights to one row. With little weight reuse, GEMV is limited mainly by memory bandwidth and is better suited to the GPU’s vector arithmetic logic units (ALUs) than to Neural Accelerators designed for matrix operations with greater data reuse.

These execution paths are not unique to Lily. MLX operates over the same unified memory and selects optimized matrix and vector kernels according to the workload shape. MLX-LM’s [Qwen implementation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/models/qwen3_5.py) already groups expert work, evaluates Gated DeltaNet with a fused recurrent Metal kernel, and uses GQA-aware attention. These capabilities are the shared starting point for efficient Qwen inference on Apple silicon.

## Optimization strategy

Lily’s narrower scope allows it to coordinate these shared execution paths around Qwen’s exact architecture and dimensions. It uses phase-specific GPU paths, maps Qwen’s expert, recurrent, and attention workloads to minimize data movement, and selects kernels and layouts from the measured workload shape. The strategy has three parts:

1.   **Match the GPU path to the inference phase.** Use matrix-oriented execution when prefill can reuse weights across many rows, and vector-oriented execution when batch-1 decode processes one row at a time.
2.   **Map Qwen’s structure onto the GPU while minimizing data movement.** Keep weights compressed until they are used, organize routed expert work without returning to the CPU, retain Gated DeltaNet state on chip through its recurrent scan, and reuse the KV data shared by grouped-query attention.
3.   **Adapt kernels to the workload shape.** Within each phase, select tile sizes, execution layouts, and attention paths from the available row count, the rows’ distribution across experts, the operation’s dimensions, and the current context length.

The following sections explain these choices. For optimizations evaluated in matched ablations on an M5 Max, we estimate their effects by comparing otherwise identical engine configurations that differ only in the optimization under study. Because these experiments compare versions of our engine against itself, they explain mechanisms rather than decompose the final results against MLX-LM.

## Prefill: reuse weights and keep routing on the GPU

Prefill exposes many token rows at once, but Qwen routes those rows unevenly across experts and updates recurrent state through the sequence. Its optimizations fall into three groups: organize sparse expert work around the routed rows, keep the Gated DeltaNet scan on chip, and divide long prompts into bounded chunks.

![Image 3](https://cdn.sanity.io/images/aqo64vfr/production/e1fd11bf881d254b2beeb366398469832ea0e19e-2976x1830.png?w=1680&q=90&fit=max&auto=format)

FIG. 03 Execution and data residency for one bounded prefill chunk through a Qwen layer. Attention extends the KV cache, while Gated DeltaNet carries its working recurrent state in registers. Expert-routing metadata remains on the GPU, Q4 weights stay packed until they are dequantized inside the grouped GEMM, and temporary activations are limited to the current chunk.

### Optimize sparse expert computation

#### Dequantize weights during matrix multiplication

The Qwen3.6-35B-A3B checkpoint uses groupwise affine 4-bit quantization. Each weight is stored as a 4-bit integer code, while every group of 64 weights shares a bfloat16 scale and bias used to reconstruct its values. This reduces the 35-billion-parameter model from roughly 70 GB of bfloat16 weights to a 19.4 GB checkpoint, making it practical to keep the model resident on the Mac.

The Metal 4 tensor operation used for matrix multiplication consumes bfloat16 operands rather than the packed 4-bit representation. Before multiplication, the GPU must reconstruct the weights in bfloat16. The optimized grouped GEMM in Lily performs this conversion one small weight tile at a time and holds the result in on-chip threadgroup memory only long enough to multiply it by the routed activation rows. Accumulation uses 32-bit floating point, and the output is written in bfloat16. The complete expanded weight array is never created in unified memory.

In the ablation, dequantization runs as a separate operation: it expands the 4-bit weights into a bfloat16 array in unified memory, after which the matrix kernel reads that array back. At a 512-token prompt, moving dequantization into the grouped GEMM increased end-to-end prefill throughput by 77.4% by eliminating this intermediate write and read.

#### Keep expert routing on the GPU

The grouped GEMM needs the activation rows assigned to each expert to be stored together. After selecting eight experts per token, a histogram counts how many assignments went to each expert. A prefix scan turns those counts into starting offsets, a scatter step places rows into their expert groups, and a block map lists the fixed-size matrix blocks that the grouped GEMM must process.

The optimized path keeps this entire sequence in one command buffer, an ordered batch of GPU operations, for each prompt chunk. An ablation instead pauses so the CPU can inspect the routing intermediates and submit the next operation. Keeping the histogram and prefix scan on the GPU adds two kernels but removes CPU–GPU synchronization inside each MoE layer.

At a 512-token prompt, enabling GPU-resident routing increased end-to-end prefill by 89%. This also shows why kernel count alone can be misleading: the faster route launches more kernels but never waits for the CPU inside the layer.

#### Match tile size to expert load

At a 2K-token prompt, routing every token to eight of 256 experts produces 16,384 token–expert assignments, or an average of 64 activation rows per expert. The actual distribution is uneven: some experts receive many rows, while others receive few.

The grouped GEMM divides each expert’s output into tiles, which are small rectangular blocks of a matrix multiplication’s output. Each tile is assigned to one GPU threadgroup. On Apple silicon’s GPUs, a threadgroup contains one or more simdgroups, each consisting of 32 threads that execute instructions in lockstep.

Larger tiles spread setup cost across more rows and expose more parallel work, but part of a large tile remains idle when an expert receives only a few rows. Tile size and simdgroup count are therefore coupled.

An ablation fixes the tile at 16 rows. Against that control, enabling the 32-row tile with four simdgroups improved end-to-end prefill by 13.2% at 2K tokens.

### Keep recurrent state on chip

During prefill, each Gated DeltaNet layer scans the prompt in order while carrying its recurrent state forward. With register residency disabled, the ablation uses a blockwise scan. At a 2K-token prompt, that path moves 256 MiB (mebibytes) of state per layer and repeatedly stops cooperating threads at barriers, synchronization points where all participating threads must wait for one another.

The recurrent state is a matrix. The optimized kernel assigns each column to one simdgroup. The simdgroup divides the column among its threads, loads the column into their registers once, and carries the state through the entire scan. The threads exchange intermediate results through simdgroup operations rather than threadgroup memory, on-chip storage shared across a threadgroup. The completed state is written back only after the scan.

The state and its gate use a 32-bit floating-point format because small rounding errors compound across sequential updates. Query and key activations remain in bfloat16.

At a 2K-token prompt, enabling the register-resident scan improved end-to-end prefill by 5.6%. Expert GEMMs accounted for about 90% of prefill time. The sequential scan does not expose enough reusable matrix work to benefit from the Neural Accelerators.

### Bound temporary memory with prompt chunking

The runtime processes a long prompt as a sequence of bounded chunks rather than keeping temporary data for every prompt token in memory at once. Model weights remain resident in unified memory, while the recurrent state and KV cache carry context from one chunk to the next. No earlier context is discarded.

Without chunking, temporary activation arrays grow with the full prompt and compete with model weights, recurrent state, and the KV cache for unified memory. Chunking keeps only one segment’s temporary values live at a time, then releases or reuses that storage before processing the next segment. This caps peak working memory and allows the engine to process longer prompts without changing the model’s output.

Chunked prefill is popular in many engines and is crucial for serving long multi-turn trajectories in these memory-constrained environments. Total prefill time for attention layers remains quadratic on prompt length, with some added overhead from repeated KV loads of earlier chunks.

## Decode: minimize the bytes moved per token

Batch-1 decode processes one new row at a time. With little weight reuse, its throughput depends mainly on how many bytes the engine moves for each token. The decode changes fall into four groups: optimize the one-row weight path, keep each step on the GPU, reduce intermediate and state traffic, and read the attention cache efficiently.

![Image 4](https://cdn.sanity.io/images/aqo64vfr/production/fb7b5bfd9773215bbe840649c09360f4965d5759-3040x2126.png?w=1680&q=90&fit=max&auto=format)

FIG. 04 Data flow for one batch-1 decode step and two mechanisms that reduce idle time and cache traffic. (A) The GPU streams Q4 weights and model state through attention, Gated DeltaNet, routing, and fused expert kernels, then writes the selected token directly into the next step’s input slot while sending a copy to the CPU. (B) Dependency-aware scheduling allows independent kernels to overlap. (C) GQA packing lets four query heads share each KV-row load, reducing eight independent requests to two shared loads.

### Optimize the one-row weight path

MLX already dispatches one-row work to specialized matrix–vector kernels. Because Lily does not use MLX, the custom runtime must provide the same basic strategy. Our row-parallel GEMV is designed for one activation row. A simdgroup cooperates on the output while reading different parts of the weight matrix in parallel.

### Keep each decode step on the GPU

#### Keep the token handoff on the GPU

Each decode step ends by selecting the next token; the following step begins with that token as input. Sending the selection to the CPU and then back to the GPU adds a synchronization point to every token. Our runtime instead alternates between two command buffers and two GPU-resident token slots. The GPU selects the highest-scoring token and writes its token ID directly into the input slot for the next decode step, while the CPU prepares subsequent work.

#### Overlap independent GPU work

In one recorded batch-1 decode step, generating a token launched 795 GPU kernels. Their dependencies formed 555 sequential stages, leaving some kernels free to run concurrently. Metal’s serial execution mode nevertheless ran every kernel in order.

The optimized decode path records the actual data dependencies in a concurrent Metal pass. Independent kernel launches can run at the same time when GPU resources allow. A barrier is inserted only when later work requires an earlier result.

### Reduce intermediate and state traffic

Separate kernels often materialize an intermediate: one kernel writes a temporary result to memory, and the next reads the result back. The optimized decode path fuses four chains: the two expert input projections with their gated activation; the expert output projection with its routing score and the shared-expert result; query and key preparation before attention; and the recurrent update with its normalization. Each fused kernel keeps temporary values in registers instead of sending them through memory.

Fusion also shortens the dependency graph: when an intermediate write disappears, so does the barrier that protected its consumer.

### Read the attention cache efficiently

#### Coalesce attention-cache reads

Attention reads keys and values from the KV cache during every decode step. In the ablation, neighboring GPU threads do not always request neighboring bytes, forcing the memory system to serve more separate transactions. Enabling coalesced loads makes adjacent threads request adjacent bytes so the hardware can combine their reads.

On the bfloat16 configuration, coalescing increased key bandwidth from 33.8 to 47.9 GB/s, increased value bandwidth from 42.0 to 61.8 GB/s, and improved end-to-end decode by 2.1% at a 3,840-token context.

#### Pack query heads to reuse KV rows

Grouped-query attention lets eight query heads share one KV head. In the ablation, each query head runs in a separate simdgroup, so all eight independently request the same cached KV row. The optimized kernel packs four query heads into one threadgroup, which loads each KV row once and reuses it across four attention calculations. A second threadgroup handles the remaining four heads.

This technique, commonly called GQA packing, performs the same arithmetic and produces identical output bytes while reducing eight independent KV requests to two shared loads. Against the unpacked ablation, it improved end-to-end decode throughput by 23.8% at a 32K-token context.

#### Switch attention layouts at long contexts

Every decode step in a full-attention layer scans the existing KV cache. A fixed-block layout divides that cache into equal pieces that the GPU can process in parallel. Its extra scheduling is not worthwhile when the cache is small, but the fixed-block layout balances the work more evenly as the context grows.

For this model, the runtime keeps the general attention path below 32K tokens and uses the fixed-block path at 32K or longer. The switch applies when each head has 256 values and eight query heads share a KV head; other shapes remain on the general path. An ablation disables this switch and always uses the general path. Enabling the fixed-block route improved end-to-end decode by 7.7% at 32K, 27.4% at 64K, and 40.2% at 128K.

## Limits of further optimization

Some changes improved an isolated operation but did not improve end-to-end inference.

[Speculative decoding](https://arxiv.org/abs/2211.17192), which uses a smaller model to propose tokens for the full model to verify, made batch-1 decode 18% slower. Verification processed groups of two to five rows, an inefficient shape for this hardware, and the rows often selected different experts, increasing the amount of expert-weight data read. Reducing the drafter’s output vocabulary improved drafter throughput by 4.7–5.1%, but did not make the complete speculative loop faster. This result is workload-specific: our batched [Qwen deployment on Blackwell](https://www.perplexity.ai/hub/blog/hosting-qwen-on-blackwell) uses speculative decoding under different conditions.

Other experiments included reducing GPU launches, overlapping entire phases, using larger prefill tiles, applying broader fusion, accelerating the router, and combining the output projection with token selection. None improved the complete inference loop.

Measurements of the hardware limits also showed little remaining headroom in the main prefill and decode operations. The MoE GEMMs and GEMVs reached 97.9% and 90.3% of the fastest sustained weight-read rates for their access patterns. Removing arithmetic from the sparse GEMV changed throughput by only 0.2%, confirming that weight reads rather than computation were the limiting resource. Prefill’s matrix multiplication similarly reached 93% of the theoretical matrix limit in isolation and 80–86% inside the tested models.

## End-to-end performance

The end-to-end comparison loads identical 4-bit checkpoint bytes in both engines and runs one request at a time on one 40-core, 128 GB M5 Max. Within each round, the two engines run in alternating order to reduce bias from background load and changes in chip temperature. We compare against MLX-LM’s fastest direct-generation path, not its server, so the measurement focuses on model execution rather than serving overhead.

The sweep covers ten prompt lengths for prefill and ten context lengths for decode, from 256 to 128K tokens. Prefill throughput first rises as the engine spreads fixed setup costs across more tokens. Prefill peaks around a 4K-token prompt, then falls because the ten full-attention layers perform more work as the prompt grows. Decode remains nearly flat at short contexts and declines once reading the growing KV cache becomes significant. The custom engine is faster at every recorded length.

Because specialized execution can change the order of floating-point operations, we also checked numerical consistency against MLX-LM. In a teacher-forced comparison, both engines predicted the next token from the same reference prefix at each of 192 positions, preventing earlier differences from affecting later inputs. Lily’s perplexity was only 0.04% higher, and it selected the same top-ranked token at 96.35% of the tested positions.

![Image 5](https://cdn.sanity.io/images/aqo64vfr/production/a4876ec95b8b62e88a1a75b429b546b60c3952d1-2560x1672.png?w=1680&q=90&fit=max&auto=format)

FIG. 05 Prefill throughput by prompt length and decode throughput by context length for Qwen3.6-35B-A3B Q4, batch 1, on one 40-core, 128 GB M5 Max. Across ten lengths from 256 to 128K tokens, Lily is faster at every recorded point: 1.12–1.42× MLX-LM’s prefill throughput and 1.31–1.37× its decode throughput. The comparison uses MLX-LM’s fastest direct-generation path. Both horizontal axes use logarithmic scales; neither vertical axis starts at zero.

## Built for the local platform

Apple silicon is not a smaller datacenter GPU. It is a complete local inference platform with its own hardware and software characteristics. Unified memory gives a single node a very high ceiling on how much model and state it can hold. The M5 Neural Accelerators absorb the dense matrix work in prefill. The vector ALUs handle the bandwidth-bound, low-reuse remainder in decode.

Qwen adds further opportunities for specialization: keep expert routing and recurrent state on the GPU, eliminate unnecessary intermediates, overlap independent work, reuse shared KV data, and adapt kernels to the workload shape.

With model- and platform-specific optimization, one Mac can run a large sparse model efficiently. Future work will widen coverage across models, chips, and serving workloads, and turn the mechanisms validated here on one configuration into more general runtime policy.

The broader principle is to match the engine to both the model’s architecture and the hardware’s specific compute and memory paths. As frontier open-weight models and hardware evolve, high-performance local inference will increasingly depend on engines tailored to both rather than ones that abstract away their differences.

Share this post

[](https://perplexity.ai/)

### Products

*   [Search](https://perplexity.ai/hub/products/search)
*   [Computer](https://perplexity.ai/products/computer)
*   [Comet](https://perplexity.ai/comet)
*   [API](https://perplexity.ai/api-platform)
*   [Deep Research](https://perplexity.ai/hub/products/deep-research)

### Solutions

#### By Size

*   [Enterprise](https://perplexity.ai/enterprise)

#### By Industry

*   [Finance](https://www.perplexity.ai/hub/solutions/finance)
*   [Legal](https://perplexity.ai/enterprise/use-cases/legal)
*   [Consulting](https://perplexity.ai/enterprise/use-cases/consulting)
*   [Healthcare](https://perplexity.ai/enterprise/use-cases/health)
*   [Tech](https://perplexity.ai/enterprise/use-cases/tech)
*   [Government](https://perplexity.ai/enterprise/use-cases/government)
*   [Education](https://perplexity.ai/enterprise/use-cases/education)
*   [Advertising](https://perplexity.ai/enterprise/use-cases/advertising)

#### By Team

*   [Marketing](https://perplexity.ai/enterprise/use-cases/marketing)
*   [Sales](https://perplexity.ai/enterprise/use-cases/sales)
*   [Product](https://perplexity.ai/enterprise/use-cases/product)
*   [IT](https://perplexity.ai/enterprise/use-cases/information-technology)

### Pricing

*   [Pro](https://perplexity.ai/pro)
*   [Max](https://perplexity.ai/max)
*   [Enterprise](https://perplexity.ai/enterprise/pricing)
*   [API](https://docs.perplexity.ai/docs/getting-started/pricing)

### Resources

*   [Blog](https://www.perplexity.ai/hub/blog)
*   [Guides](https://perplexity.ai/enterprise/guides)
*   [Customers](https://www.perplexity.ai/hub/customers)
*   [Academy](https://www.perplexity.ai/hub/academy)
*   [Workshops](https://www.perplexity.ai/hub/workshops)
*   [API docs](https://docs.perplexity.ai/docs/getting-started/overview)
*   [Help Center](https://perplexity.ai/hub/helpcenter)
*   [Research blog](https://research.perplexity.ai/)
*   [Security](https://perplexity.ai/hub/security)
*   [Trust center](https://trust.perplexity.ai/)

### Company

*   [Careers](https://perplexity.ai/hub/careers)
*   [Brand Guidelines](https://live.standards.site/perplexity/)
*   [Supply Store](https://perplexity.supply/)
*   [Privacy Policy](https://www.perplexity.ai/hub/legal/privacy-notice)
*   [Terms & Conditions](https://www.perplexity.ai/hub/legal/terms-of-service)

*   [](https://x.com/perplexity_ai)
*   [](https://discord.gg/perplexity-ai)
*   [](https://instagram.com/perplexity)
*   [](https://threads.net/@perplexity)
*   [](https://linkedin.com/company/perplexity-ai/)
*   [](https://www.youtube.com/channel/UCYqxnCFtaC4-iC_bwt2bRLg)

[![Image 6](https://pplx-marketing-static.perplexity.ai/assets/apple-app-store-BC0fmJ99.svg)](https://pplx.ai/tm5vnAY)[![Image 7](https://pplx-marketing-static.perplexity.ai/assets/google-app-store-_ij3hvf8.svg)](https://pplx.ai/PQ1sogC)

Perplexity ©2026

![Image 8](https://edge.perplexity.ai/image)