# PagedAttention Isn't Gone, It Got Demoted

- Author: @GonnabeNikhil (Nikhil Mourya)
- Published: Sun Sep 06 07:50:40 +0000 2026
- URL: https://x.com/GonnabeNikhil/status/2096506355217809626
- Likes: 32
- Retweets: 0
- Replies: 3
- Bookmarks: 51
- Views: 0

# Ask someone why vLLM is fast and 9 times out of 10 you'll get the same answer: PagedAttention.

It's the term that shipped with the original paper. The one that made it into conference talks. The one people still drop in system-design interviews as if it's the whole story.

It isn't. And it hasn't been for a while.

Open the vLLM repo today and PagedAttention shows up as one entry in a backend registry, sitting next to half a dozen other kernels with names like FlashInfer and FlexAttention. It didn't disappear. It got demoted.

Here's the whole path, from the ground up, of how that happened.

## First: why there's a cache at all

Start from the basics. The fragmentation problem only makes sense once this part is clear.

A transformer generates text one token at a time.

To generate token N, it needs to attend back over tokens 1 through N-1. Naively, that means recomputing the key (K) and value (V) projections for every prior token, at every layer, on every single step.

That's wasteful. Those K and V vectors don't change once a token has been processed. So serving engines cache them instead.

The KV cache stores:

- Every token's key and value vectors

- Per layer

- Per attention head

Each new step only computes K/V for the newest token, then reuses everything else.

This is a real memory cost, not a rounding error. For a mid-size model, a single sequence's KV cache can run into gigabytes. Multiply it out: layers × heads × head dimension × sequence length × two (K and V) × batch size.

Decoding is also memory-bandwidth-bound. Every generated token requires loading the entire KV cache back off the GPU. How efficiently that memory is laid out and read directly determines throughput.

That's the terrain PagedAttention showed up to fix.

## What PagedAttention actually fixed

The problem was narrow and specific: KV cache fragmentation.

Before PagedAttention, serving engines allocated a contiguous chunk of memory for each sequence's KV cache.

That allocation was sized for the maximum sequence length the request might reach. You don't know in advance how long a generation will run, and contiguous memory has to be reserved up front.

Most requests never got close to that maximum. The gap sat reserved and unusable. It's the same internal-fragmentation problem operating systems solved decades ago for process memory.

vLLM's answer was to borrow that fix directly:

- Split the KV cache into fixed-size blocks that can live anywhere in physical memory

- Map logical positions to physical ones with a block table, the same indirection a page table gives a process

- Share blocks across requests that have a common prefix

- Stop reserving memory against a worst case that rarely happens

That's what let vLLM push batch sizes up and become genuinely competitive on throughput.

It was a memory-management fix. Full stop.

It said nothing about how attention itself should be computed once the data was laid out that way. It only changed where the bytes live and how they're addressed.

## The split that happened next

That's the core distinction: where the cache lives, versus how compute happens over it.

It's the seam vLLM's architecture has grown along since.

The current design (v1, not the deprecated v0 path) treats these as two separate concerns with two separate interfaces.

The KV cache manager handles memory:

- Allocating blocks

- Tracking reference counts

- Handling prefix-cache hits

- Deciding what gets evicted

It calls into functions like get_computed_blocks() and allocate_slots(). It doesn't care what kernel eventually reads those blocks.

The attention backend handles compute. Concretely:

- Takes a query vector and the K/V blocks it needs

- Computes softmax(QK^T / sqrt(d)) V

- Returns an output tensor, as fast as the hardware allows

It uses whatever tiling and fusion tricks make the GPU's memory hierarchy happy. It doesn't care how those blocks got allocated, only that it's handed valid pointers to read from.

A model can even mix backends within itself.

vLLM supports per-KV-cache-group backend overrides. A model with both full and sliding-window attention layers can route each group to a different kernel.

## The backend landscape, concretely

This isn't a framing device. It's how the code is laid out. Under vllm/v1/attention/backends/, you'll find, among others:

- flash_attn: FlashAttention, the tiled-softmax kernel that keeps intermediate values in fast on-chip SRAM instead of round-tripping to HBM

- flashinfer: FlashInfer, a broader operator library covering block-sparse paged attention and more

- flex_attention: FlexAttention, which compiles custom attention-mask patterns instead of hardcoding them

- mla: multi-head latent attention, the compressed-KV scheme DeepSeek's architectures popularized

- gdn_attn: GatedDeltaNet-style linear attention

- triton_attn (and the ROCm-side rocm_attn / rocm_aiter_unified_attn): PagedAttention paired with Triton prefix prefill, per vLLM's own docs

PagedAttention hasn't vanished from this list. It's alive inside triton_attn. It's just a backend now, not the backend.

MLA gets its own further split. Prefill and decode behave differently:

- Prefill: processing the prompt, compute-bound

- Decode: generating tokens one at a time, memory-bound

So each phase picks its own backend:

- Prefill backend: FlashAttention, FlashInfer, or TRT-LLM Ragged, selectable independently

- Decode backend: FlashMLA, Triton MLA, CUTLASS MLA, and others

- DeepSeek's newer sparse MLA variants get their own dedicated decode backends again

This is configured through --attention-backend, the VLLM_ATTENTION_BACKEND environment variable, or explicit per-group overrides.

It's not something you infer from benchmarks after the fact.

## Why the split had to happen

Once KV cache fragmentation stopped being the bottleneck, the bottleneck moved into the kernel itself.

No single kernel is optimal everywhere. Two forces drove this.

Hardware diverged.

Hopper and Blackwell have different tensor core generations. They have different native support for low-precision formats too.

The fastest FlashAttention version on one is not the fastest on the other. vLLM's docs specify different default FlashAttention versions per SM generation for exactly this reason, and that's before FlashInfer's separate TensorRT-LLM-backed kernels even enter the comparison.

Attention itself diverged.

- Standard multi-head attention keeps a full K and V vector per token, per head. That's the thing PagedAttention was built to page efficiently.

- MLA compresses each token's K/V into a small shared latent vector, then expands it back out on the fly. That shrinks the cache dramatically, but needs a kernel built around compression, not plain per-head blocks.

- GDN drops the growing cache entirely. It keeps a fixed-size recurrent state that updates per token, closer to an RNN than to attention's usual quadratic lookup.

Three genuinely different memory-access patterns. None of them fit the original PagedAttention kernel.

A single hardcoded PagedAttention kernel, tuned for one GPU generation and one attention shape, was never going to keep up with that spread.

Splitting cache management from kernel selection was the only way to let each side evolve on its own schedule.

## The practical payoff

"Did you turn on PagedAttention" stopped being a meaningful question.

Block-based KV cache management is just how vLLM works now. It's on by default in that sense.

The question that actually moves your throughput number is which combination you've picked:

- KV cache layout

- Cache manager behavior (prefix caching, hybrid sliding-window handling)

- Attention kernel

...for your specific model, on your specific hardware.

Those are independent decisions now. Each has its own defaults, its own override flags, and its own failure modes if you pin the wrong combination.

That's a more complicated question than the old one. It's also the honest one.

Throughput on an H100 running dense attention and throughput on a Blackwell part running MLA are different engineering problems. Pretending one kernel name explains both was always a simplification.

## PagedAttention's actual legacy

None of this makes PagedAttention wrong, or obsolete in any sense worth complaining about.

Every backend in that registry still benefits from the memory-management model it introduced: block-based, non-contiguous, prefix-shareable KV caches are the substrate everything else sits on.

What changed is scope.

PagedAttention used to stand in for the entire inference engine in people's mental model of vLLM.

Now it's one memory strategy among several ways of computing attention over that memory. Attention computation itself became the fast-moving layer, iterating across GPU generations and model architectures faster than the storage model underneath it needs to.

Not a demotion in the sense of failure.

A demotion in the sense that the org chart grew. The problem it solved turned out to be one department, not the whole company.
