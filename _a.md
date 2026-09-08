# Attention Mechanisms in LLMs, clearly explained

- Author: @akshay_pachaar (Akshay 🚀)
- Published: Sat Sep 05 12:36:36 +0000 2026
- URL: https://x.com/akshay_pachaar/status/2096215921568498042
- Likes: 519
- Retweets: 83
- Replies: 6
- Bookmarks: 823
- Views: 0

Self-attention → Cross-attention → Multi-Head Attention → MQA → GQA → FlashAttention → Sparse attention → PagedAttention → RadixAttention, explained with illustrations.

Every model card advertises its attention mechanism.

Multi-Query Attention, Grouped-Query Attention, and Multi-Head Latent Attention are listed alongside parameter counts and benchmark scores.

They all exist because of the same constraint. Storing attention state for long sequences and large batches runs you out of GPU memory.

And today we break down each of them, in the order they arrived and the flaw each one fixed.

Let’s begin!

# Why attention exists

Early sequence models like Recurrent Neural Networks (RNNs) passed a fixed-size hidden state from token to token.

The further apart two tokens were, the weaker the connection. Long-range dependencies faded.

Attention solves this directly. Instead of passing state through a bottleneck, every token gets to look at every other token and decide how relevant each one is.

Nothing is hidden behind a summarization step.

That directness is what makes transformers powerful. It is also what makes them expensive. The cost lives in the memory required to store what every token has seen.

# The constraint that drives everything

Every time the model attends, it needs to remember what every previous token looked like.

During prefill, the model processes your entire prompt at once and computes a key vector and a value vector for each token at each layer.

These get stored in what’s called the KV cache so that decode steps can attend over them without recomputing from scratch.

The cache grows with every token generated. For a 70B model at BF16, a single 128K-token context holds roughly 40 GB of KV cache, comparable to the model weights themselves at 4-bit quantization.

The constraint is not compute and not the math in the attention formula. It is the memory that stores what attention has already seen.

# Self-attention and causal attention

Self-attention lets each token attend to every other token in the same sequence.

The model computes a query, key, and value for each token, then uses query-key dot products to decide how much each token should attend to every other one.

This is the base operation inside every transformer layer.

Causal attention is self-attention with a triangular mask applied. Each token can only attend to tokens that came before it, never future ones.

This is what makes decoder-only generation possible, because without the mask the model would see the answer before producing it.

Cross-attention is different in kind. The queries come from one sequence, the keys and values come from a second sequence.

This is how encoder-decoder models like T5 and Whisper connect the encoder’s output to the decoder. In decoder-only models like Llama and GPT, cross-attention does not appear at all.

# Multi-Head Attention

Multi-Head Attention (MHA) is the original design from the 2017 Transformer paper.

Each attention head gets its own independent set of query, key, and value weight matrices. With 32 heads, you have 32 independent KV projections per layer.

The benefit is expressiveness. Different heads learn to track different kinds of relationships simultaneously. One head might track syntactic structure, another semantic proximity, another long-range coreference.

The cost is memory. Every head maintains its own KV cache. A model with 32 layers and 32 heads per layer stores 1,024 separate KV tensors per token per request.

GPT-3 uses 96 heads per layer. At a 128K-token context on a model that size, the KV cache alone fills a GPU before the batch grows at all.

That memory cost is what every design after MHA is built to reduce.

# Multi-Query Attention

Multi-Query Attention (MQA) takes the most direct route. All query heads still have their own weight matrices, but every query head shares a single key head and a single value head.

The KV cache shrinks by a factor equal to the number of heads. Where MHA stores 32 separate KV projections, MQA stores one.

Decode gets faster because you are loading far fewer bytes from HBM per step, which matters because decode is memory-bandwidth-bound.

The quality cost is real. Forcing all query heads to share one key and one value loses some of the expressiveness MHA provides.

Falcon, PaLM, and early Gemini variants used MQA and accepted this tradeoff for the throughput gain.

What MQA gives up in quality, the next design largely recovers.

# Grouped-Query Attention

Grouped-Query Attention (GQA) sits between MHA and MQA.

Query heads are divided into groups, and each group shares one key head and one value head. The groups are independent of each other.

With 32 query heads and 8 KV groups, you store 8 KV projections instead of 32, a 4x reduction in KV cache size compared to MHA, while recovering most of the quality that MQA trades away.

This balance is why GQA has become the default for almost every major open-weight model released in recent years. Llama 2 70B uses 8 KV groups. Llama 3, Mistral, Mixtral, Gemma, and Qwen all use GQA.

The original GQA paper showed it matches MHA quality at a fraction of the memory cost, and that has held up across model families.

GQA reduces the number of KV heads stored. What comes next compresses the heads themselves.

# Multi-Head Latent Attention

Multi-Head Latent Attention (MLA) is DeepSeek’s contribution, introduced in DeepSeek-V2 in May 2024.

Where MQA and GQA reduce the number of KV heads, MLA compresses the full-dimensional key and value vectors into a low-rank latent space before caching them. At attention time, those latent vectors get decompressed back to full dimension.

The cached object is the latent vector, not the full KV tensors. This makes the cache footprint smaller than even GQA while preserving more of the expressiveness that MQA sacrifices.

The tradeoff is compute. Decompressing at every attention step adds FLOPs. But at inference, memory bandwidth is the bottleneck far more often than compute, so smaller cache beats extra math in most real serving configurations.

DeepSeek-V2, V3, and R1 all use MLA. On DeepSeek-V2’s benchmarks, MLA matched or exceeded MHA quality while cutting the KV cache to roughly 5-13% of what MHA would require at the same model size.

MHA, MQA, GQA, and MLA are all decisions about what to store. The next technique is about how expensively you compute it.

# FlashAttention

FlashAttention does not change what attention computes. It changes how the computation accesses memory.

Standard attention builds the full N x N attention matrix, writes it to HBM, reads it back for the softmax, writes the result again, then reads it again for the weighted sum.

For a 4K-token sequence, that matrix is 4,096 x 4,096 values. Moving it in and out of HBM repeatedly is what makes attention the bottleneck for long contexts.

FlashAttention tiles the computation. It processes the attention matrix in blocks that fit in on-chip SRAM, computes the softmax incrementally without materializing the full matrix, and writes the output to HBM once.

The math is identical. The memory traffic is not.

Every major serving engine uses FlashAttention kernels by default today. It is not a new attention type. It is the standard kernel for executing whatever attention type your model uses.

MHA, GQA, and MLA answer what to store and how to compress it. FlashAttention answers how to compute it efficiently.

Sparse attention takes a different angle. Not which tokens to cache, but how many tokens to attend to at all.

# Sparse attention

Full attention is O(N²) in sequence length. For a 1M-token context, the attention matrix has a trillion entries. Even with FlashAttention reducing memory traffic, computing attention over that many tokens is not tractable.

Sparse attention skips large portions of the attention matrix. Instead of every token attending to every other token, only a selected subset of pairs gets computed.

Sliding Window Attention (SWA) is the simplest variant. Each token attends only to the most recent W tokens. Local context is preserved; distant context is dropped.

Mistral uses SWA on some layers, alternating with full attention on others to maintain both local precision and some global reach.

Native Sparse Attention (NSA) is DeepSeek’s 2025 contribution, distinct from MLA. Rather than applying sparsity post-hoc at inference, NSA trains the model with sparse attention from the start.

Each layer combines three parallel branches: compressed coarse-grained attention for global context, selective fine-grained attention for important token blocks, and sliding window attention for local context. The model learns during pretraining which tokens matter.

NSA matches full-attention quality on most benchmarks while running substantially faster on long sequences.

Qwen2.5-1M uses a sparse attention approach for its million-token context window because at that length full attention consumes over 90% of the forward pass time.

Trained-in sparsity is proving to be the most principled answer to long-context scaling.

# The serving layer

Everything above lives inside the model weights. PagedAttention and RadixAttention live in the serving engine, and they are answers to the same KV cache pressure at a different level.

When a request arrives, the serving engine needs to allocate GPU memory for its KV cache. The naive approach reserves contiguous memory for the maximum possible sequence length.

A request allowed to generate up to 4,096 tokens gets 4,096 slots reserved upfront, whether it uses 40 or 4,000 of them.

This approach wastes 60-80% of GPU memory. Fragmentation between requests makes it worse.

PagedAttention, the mechanism vLLM runs, manages the KV cache the way an OS manages virtual memory. Fixed-size blocks are allocated on demand.

A block table maps each request’s logical blocks to whatever physical blocks happen to be free. There is no pre-allocation, no fragmentation, and memory waste drops below 4%.

RadixAttention, the mechanism SGLang runs, takes the next step. When multiple requests share a common prefix, like a long system prompt sent to every user, the KV blocks for that prefix only need to be computed once.

RadixAttention stores KV blocks in a radix tree indexed by token sequence. A new request walks the tree, finds the longest matching prefix, reuses those blocks, and computes only the genuinely new suffix.

On multi-turn workloads, RadixAttention hits 75-95% cache hit rates. A system prompt served to thousands of users gets computed once and reused until evicted by the LRU policy.

PagedAttention and RadixAttention do not change which attention mechanism your model uses. A Llama 3 model with GQA runs fine under either engine. The two layers are independent.

# Putting it together

The through-line across all of them is the same pressure. KV cache memory is the bottleneck, and every design here is a different move against it.

MQA, GQA, and MLA reduce how much you store per token, each trading a different amount of quality for memory.

FlashAttention reduces how expensively the computation accesses memory, without touching the math at all.

Sparse attention reduces how many tokens you attend to, which is the only answer that scales to million-token contexts.

PagedAttention and RadixAttention work at the serving layer, cutting waste in allocation and reuse rather than in the model itself.

Knowing which of these is the binding constraint in your setup is what determines which one actually moves the number for you.

Thanks for reading. That's all for today.

Cheers! :)
