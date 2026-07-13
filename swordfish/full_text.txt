Title: Swordfish, a Weight-Quantized GEMM Family for NVIDIA Blackwell

URL Source: https://blog.alpindale.net/posts/swordfish/

Published Time: 2026-07-12T00:00:00Z

Markdown Content:
The [Blackwell](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/) family of NVIDIA GPUs introduced native acceleration for the FP4 datatype, specifically NVFP4 and MXFP4, with block scales applied inside the tensor core at up to four times the [BF16](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format) rate, and ever since, NVFP4 has become one of the most popular quantization formats for both weights and activations in LLMs. Before this, the most popular way to run models at lower precisions (aside from [GGUF](https://github.com/ggml-org/llama.cpp)), was to use models quantized using [GPTQ](https://arxiv.org/abs/2210.17323), [AWQ](https://arxiv.org/abs/2306.00978), and the like. They did, however, keep activations typically in half (bf16/fp16) precision. No tensor core support exists for these weight-only quantization formats, so running it fast has always meant writing a dedicated kernel. The initial GPTQ kernels were quite inefficient, which led to Frantar et al. introducing the [Mixed-precision Auto-Regressive LINear](https://arxiv.org/abs/2408.11743) (Marlin; I bet you didn’t know that’s what it stands for!) kernels back in 2024. This kernel did exceptional well on Ampere GPUs, and was later adopted and modified by the [vLLM](https://github.com/vllm-project/vllm) team to serve their needs. The vLLM team also later introduced the [Machete](https://github.com/vllm-project/vllm/pull/7174) kernel for the [Hopper](https://www.nvidia.com/en-us/data-center/technologies/hopper-architecture/) GPU architecture, making use of the newly introduced [WGMMA](https://nvlabs.github.io/cuda-oxide/advanced/matrix-multiply-accelerators.html#wgmma-hopper-sm-90) feature.

Swordfish is the Blackwell entry in that lineage of kernels. It’s written for only the datacenter-grade GPUs in the Blackwell family such as B200 and the Jetson Thor (sm100 and sm110) and does not include support for the consumer-grade ones such as RTX 5090 or RTX 6000 Pro Blackwell (sm120). Below is a detailed introduction to the programming, tricks, and other efforts that made it possible. On a B200, the Swordfish kernel sustains 1,444 TFLOPs with inline INT4 dequantization, or 90% of cuBLAS dense BF16 on the same shapes. On the Jetson Thor, its decode runs at 90-97% of the DRAM roofline.

## What changes on Blackwell

Datacenter Blackwell gave us the fifth-generation tensor core (`tcgen05`), which was instrumental for Swordfish. Special handling is needed for it, as outlined below:

**No mixed-input MMA.** The instruction accepts f16/bf16, tf32, int8, the fp8/fp6/fp4 group, and block-scaled MX types. An int4-by-bf16 product is inexpressible, so CUDA cores must dequantize weights before the MMA consumes them. Where that dequantized operand lives and how many instructions produce it become very important design choices.

**Accumulators live in Tensor Memory.** Each SM has 256 KB of TMEM, 512 columns by 128 datapaths. A single thread issues the MMA asynchronously, results accumulate in TMEM, and dedicated load instructions read them back in the epilogue. Warp-register accumulator fragments and the Ampere habit of interleaving MMA with epilogue math in the same registers are both gone.

**One MMA spans two SMs.** Under `cta_group::2` a single instruction computes a tile across an SM pair, with operand delivery and synchronization semantics specific to the paired mode.

The warp-level `mma.sync` path still works on Blackwell and works quite well. Because of that, the decode kernels below stay on `mma.sync` but prefill adopts `tcgen05`, as we need all the compute power we can get for it.

## A single layout with three consumers

Decode is very memory-bound. The active batch is small, so every weight byte is read once per step. Prefill amortizes each weight tile over thousands of tokens and, as a consequence, is very compute-bound. Very large batches are so compute-bound that dequantizing the whole weight once and calling the dense library wins outright.

Swordfish therefore compiles three paths against one packed tensor, prepacked once at model load. A family of decode kernels, hand-written CUDA and PTX around `mma.sync.m16n8k16`, does all the work up to roughly a hundred rows. A prefill mainloop, a fork of the CUTLASS 4.4 sm100 mixed-input collective, drives `tcgen05` through TMA-fed warp-specialized pipelines. A dense tier dequantizes the weight into a scratch fp16/bf16 tensor with one coalesced kernel and hands the GEMM to cuBLAS.

### The packed format

Int4 storage is indexed as `(n_block, k_block, word)` with extents `(N/64, K/64, 512)`, and int8 as `(N/64, K/32, 512)`. Each block is a contiguous 2,048-byte run holding a 64x64 (int4) or 32x64 (int8) tile as four 512-byte sub-tiles that keep Marlin’s 16x64 fragment permutation verbatim.

The layout is built around three invariants: a 32-bit word dequantizes into `mma.sync` fragment registers with four `LOP3` and zero cross-lane shuffles, and a lane fetches its complete weight-fragment group, eight packed words, in one 256-bit access. On top of those, each block occupies a linear byte range, which lets the prefill path hand the whole tensor to TMA as a dense byte array; the nibble permutation stays confined inside 32-bit words, where no byte-level copy can observe it.

![Image 1: Packed weight format](https://blog.alpindale.net/images/packed_format.png)_The three views of one tensor. The decode path reads words and 256-bit lane groups, and the prefill path reads whole blocks._

Dequantization uses the magic-number idiom. For bf16

```
lop3.b32  lo, q,       0x000f000f, 0x43004300, 0xea;
lop3.b32  hi, q >> 4,  0x000f000f, 0x43004300, 0xea;
// packed bf16x2 results; one hsub2 of {136, 136} removes the exponent
// bias and the +8 zero-point together
```

recovers four of the word’s eight nibbles as two bf16x2 pairs, and a second `LOP3` pair over `q >> 8` completes the word, so eight int4 values cost four logic ops plus one `hmul2` per pair. The int8 variant runs the same idiom over byte lanes with a 128 bias. AWQ zero points arrive as scale-shaped rows holding the prescaled value (8 − zp) · s, so the scale multiply and the zero-point add fuse into one `hfma2` per pair. Channelwise checkpoints replicate their single scale row to group 128 at load. Prefill and the dense tier consume the replicated rows as ordinary group-128 metadata, while decode keeps `group_size = -1`, reads scale row zero once, and skips group bookkeeping entirely.

### Runtime dispatch

The regime boundaries live inside the C++ operator, where the true runtime M decides per call and per captured CUDA graph. A Python-side branch gets traced by `torch.compile` at one representative batch size and baked into the compiled graph, while routing every subsequent call through whichever kernel the trace saw.

Decode always handles M ≤ 55. It keeps M < 96 whenever the prefill grid’s column count, one CTA per 128 output columns, would underfill the SMs, and on datacenter parts it keeps K-heavy narrow-N shapes (K ≥ 2N) through M = 127, where a single underfilled `tcgen05` wave loses to Stream-K. Prefill requires fp16 or bf16 activations, int8 group size 128 or int4 group size 32, 64, or 128, and K and N divisible by 128; ineligible combinations stay on decode at any M. The dense tier preempts both. On datacenter parts it engages at M ≥ 1024 for int8, at M ≥ 4096 for int4, and at M ≥ 512 for activation-reordered weights when N ≤ 2K. On Thor it serves int8 only, from M ≥ 2048 on ordinary shapes and from M ≥ 8192 on K-heavy ones.

![Image 2: Dispatch map](https://blog.alpindale.net/images/dispatch_map.png)_Kernel ownership along the M axis. Hatched spans are the conditional regions described above._

## Decode, counting memory-pipe slots

Profiling an early revision against Marlin at M = 1, K = N = 4096 showed DRAM traffic that differed by only two sectors and 41 percent more LSU wavefronts on the Swordfish side. A wavefront is one issue slot of the load-store pipeline, and that pipeline serves every shared-memory access, global load, and atomic, so staging, scale gathers, and the epilogue all compete with the weight stream for the same issue capacity. The final mainloop machinery, shared by every decode kernel in the family, treats those slots as the scarce resource.

*   **Self-slot `cp.async` staging.** Each lane copies exactly the bytes it will later consume into its own shared-memory slot, up to five stages deep. Staging stays lane-local end to end, the mainloop runs free of warp synchronization, and in-flight bytes wait in the async queue, costing zero registers. Activation slices ride the same commit groups as the weights, so one wait covers both.
*   **`ldmatrix.x4` activation fragments.** One instruction replaces eight scalar shared loads and lands the m16k16 tile in tensor-core register order.
*   **Arithmetic hygiene.** A `%`-indexed stage ring compiles to magic-number division. Compare-and-wrap indexing plus incremental 32-bit address cursors remove three divisions and all 64-bit multiplies per tile from the hot loop.
*   **Cooperative scale loads.** One 4-byte access per lane covers a 64-wide scale row, `shfl` broadcasts the pairs, and the next group’s row is prefetched a full group early so its latency hides under compute.
*   **`red.global.add` epilogues.** Partial tiles merge into zeroed output via packed-pair `red.global.add.noftz`, deleting cross-warp shared-memory reductions and their barriers and making any split of the K axis free. On our toolchain `atomicAdd(half2*)` compiles to a compare-and-swap loop, so the kernels emit `red.global` through inline PTX.
*   **`evict_first` on the weight stream.** Weights are read once per launch. Marking their copies evict-first preserves L2 for activation rows and scales, which are re-read once per column, and improves throughput on every measured shape.

![Image 3: Decode mainloop animation](https://blog.alpindale.net/images/decode_mainloop.gif)_One warp’s mainloop. The stage ring fills, then every iteration issues one copy and consumes the oldest ready slot, and the accumulated tile flushes through `red.global` at the end with no barriers anywhere._

Two support kernels keep the output path on the compute engine. Zeroed outputs come from a grid-stride store kernel. On the measured runtime a captured `cudaMemsetAsync` node executed on the copy engine, and at one memset per GEMM the compute-to-copy transitions idled the GPU for about 90 microseconds per decoded token on a small model. Activation-reordered checkpoints run a prep kernel that writes the column-sorted activation copy and zeroes the output in one launch, with one thread per element and coalesced `g_idx` loads, so the sort costs a single graph node.

The decode window splits into three regimes.

**M ≤ 16.** One CTA of four warps owns an n64 column, the warps split K contiguously so each sees every scale group exactly once, and a `blockIdx.z` split-K slices the K axis when columns alone leave SMs idle. The split heuristic is occupancy-derived on datacenter parts. On few-SM parts it stops splitting once the columns fill the machine, because further slices shorten the latency-bound per-warp chains and add a zeroing launch. Forced splits measure 8 to 15 percent slower at M = 1 on Thor’s 20 SMs, and on B200’s 148 SMs the same sweep runs two to three times slower when held to split 1 than at the occupancy-derived depth.

**M 17 to 48.** The same shape wants different morphologies on the two targets. Datacenter parts run the fused atomic kernel, two m16 tiles per CTA through M = 32 and three through M = 48, with one weight stream shared by the four warps, dequantized once and fanned out across the tiles. Few-SM parts run the Stream-K kernel with claims issued per CTA over n256 column quads. The four warps take four adjacent n64 columns over a common k-range, which amortizes claim bookkeeping four ways, keeps the four weight streams walking consecutive blocks, and holds every warp’s activation slices L2-resident; widths short of a quad fall back to warp-granular claims. Each choice beats the other’s morphology on its own hardware by measured margins up to 25 percent.

**M ≥ 49 through the prefill crossover.** Persistent Stream-K handles this regime. One unit of flat work is one k-slice of one (m-group, column) tile, each warp claims a contiguous run of units, and accumulators flush through the atomic epilogue at claim boundaries, so a tile’s K axis may be covered by any number of warps with no locks and no fixup pass. Four m16 tiles fuse per claim through M = 64, amortizing each dequantized fragment across four MMAs, and three-tile fusion carries the shapes the crossover leaves behind.

Int8 halves the weight rows per staged kilobyte, so the 8-bit variants run thinner k16 staging units, deeper pipelines in the same shared memory, and a two-unit step that processes two staged slices per pipeline wait. Profiles of the single-unit form showed one short dequant chain exposed to staging latency at every step, and the two-unit step took the worst 8-bit cell from 0.66x to 1.03x of Marlin.

On Thor at M = 1 the family sustains 231 to 249 GB/s of weight bandwidth across Llama layer shapes, or 90 to 97 percent of the platform’s practical DRAM ceiling.

## The dense tier

From about a thousand rows the problem is compute-bound and the fused mainloops leave dense-library performance on the table. The dense tier dequantizes the packed tensor into a scratch fp16/bf16 weight with one kernel launch and calls `cublasGemmEx`. The dequant kernel gives each warp a 16x64 sub-tile, unpacks through the same LOP3 path, stages through a shared tile padded from 64 to 72 elements per row, and writes 16-byte runs. With an unpadded 128-byte row stride, every same-column store across rows lands on one shared-memory bank, 1.6 million conflicts per launch at 4096x4096; the padding removes them and puts the kernel on the DRAM roofline. Activation-reordered checkpoints fold the permutation into the dequantized-weight write addresses, so the activations are consumed unpermuted and the separate prep launch is gone.

The crossover thresholds in the dispatch section come from measurement on both targets. A fused mainloop reads int4 weights at a quarter of the dense tier’s fp16 weight traffic, and on Thor the tier’s cuBLAS rate never overcomes that gap, so int4 stays fused there at every M. At int8 the traffic gap halves and the dense tier overtakes the fused path. Activation-reordered weights cross earliest because the tier absorbs the sort that costs the fused paths a prep launch and gather-heavy scale handling.

## Prefill on tcgen05

### The collective fork

The CUTLASS 4.4 mixed-input sm100 collective already has the right skeleton we want. A TMA warp loads operands, a Transform warp group dequantizes into a shared-memory compute buffer, an MMA warp feeds `tcgen05`, and mbarrier pipelines decouple the three. The stock version expects canonical column-major weights and re-permutes on ingest, so Swordfish forks it at two seams. TMA stages the packed tensor as raw 2,048-byte blocks, and the Transform stage consumes packed words in Marlin tile order, dequantizes, scales, and writes K-major fragments into the `tcgen05`-legal buffer with lane-local 32-bit stores. The pipelines and the MMA stage remain basically unchanged. Zero points ride the scale pipeline as a second scale-shaped tensor and add one FMA in the Transform stage. The fork doesn’t seem to diverge at all against a dense reference GEMM and outruns the stock collective by 11 percent at M ≥ 1024, the direct payoff of skipping the canonical-layout work.

![Image 4: Prefill collective](https://blog.alpindale.net/images/prefill_pipeline.png)_The forked collective on one SM pair. Each CTA transforms its half of the weight tile, one 2-SM TMA delivers both activation halves, and the leader issues the MMA over both compute buffers._

The UMMA descriptor consumes shared-memory offsets in the byte domain, while evaluating the compute buffer’s flagged `ComposedLayout` applies its swizzle in the element domain. Descriptor addressing therefore needs the byte-domain form, which for this atom has the closed expression `offset ^ ((n % 8) << 3)`. We static-assert that expression against the layout, and replacing generic `crd2idx` addressing with it made the Transform stage 40 percent faster.

### Two SMs per MMA

`cta_group::2` computes a 256-row weight tile across an SM pair, each CTA holding half of the dequantized weights, the leader issuing the instruction. The implementation carries weights as operand A through the Transform stage and activations as operand B. Three 2-SM details determine correct construction, partitioning, and operand delivery, and each requires a one-line change.

1.   The convenience builder `sm100_make_trivial_mixed_input_tiled_mma` has no branch for 2-SM atoms with smem-sourced A. The atom exists with full traits, `SM100_MMA_F16BF16_2x1SM_SS`, and direct `make_tiled_mma` construction works.
2.   `partition_shape_A/B` take CTA-local shapes for 2-SM atoms. The 256-row instruction tile partitions per-CTA to 128 rows, and passing the full tile fails overload resolution with errors that never mention shapes.
3.   The activation operand is split across the pair by the instruction’s B-layout, `Shape<_2, Shape<N/2, K>>`, and the leader’s MMA reads the peer CTA’s shared memory for the second half. `SM100_TMA_2SM_LOAD` exists precisely for this, as it delivers both halves with one instruction, and its single arrival on the leader’s barrier covers both CTAs’ bytes. An ordinary per-CTA TMA fails in one of two ways: when the barrier expects the paired transaction count, the kernel hangs. When it expects per-CTA arrivals, the leader’s MMA reads the peer’s half before delivery and nondeterministically corrupts output rows confined to that half. Both signatures point at the copy atom.

### Instruction width

With the pair correct, B200 throughput saturated near 1,090 TFLOPS from M = 2048 up and held flat across sweeps of Transform width, pipeline depth, and K-tile granularity. Widening the MMA from 256x128 to 256x256, the shape cuBLAS and the [qutlass](https://github.com/IST-DASLab/qutlass) project select for large M, raised the ceiling in one step. Per-instruction issue overhead capped the narrow tile, and doubling the work per instruction removed the cap.

| M (K=4096, N=28672) | 256x128 | 256x256 |
| --- | --- | --- |
| 512 | 879 | 1,139 |
| 1024 | 1,029 | 1,406 |
| 2048 | 1,056 | 1,395 |
| 4096 | 1,089 | 1,444 |
| 8192 | 1,093 | 1,442 |

_Effective TFLOPS on B200 including inline dequantization. Dense bf16 cuBLAS measures 1,604 to 1,629 on these shapes, placing the quantized path at 90 percent of the dense library._

Each CTA allocates two 256-column accumulator stages, exhausting its 512-column TMEM address space exactly. Int4 instantiates both widths for each activation dtype and group size and dispatches per shape. Int8 compiles only 256x128, because the wide tile’s input staging exceeds the shared-memory budget at 8 bits and the doubled weight stream pressures the K pipeline the way K-heavy shapes do. K-heavy int4 shapes (K ≥ max(2N, 8192)) starve the wide tile’s K pipeline and also run 256x128; both targets show the effect at K = 14336.

Two platform details round out prefill. On Thor a large-M launch thrashes the 32 MB L2 once the activation slab outgrows it, causing a two-thirds throughput loss at M = 2048, K = 14336, so the launcher chunks M to fit. The 256-wide tile lifted most Thor shapes to 96 to 175 TFLOPS against a 127 TFLOPS dense bf16 ceiling. Bandwidth-bound shapes exceed dense because int4 weights cross the memory bus at a quarter of the dense cost, which makes quantization a throughput feature in its own right on this class of hardware.

## Fused MoE

Expert layers reuse the decode machinery over token-sorted work. `moe_align_block_size` sorts (token, expert) pairs into blocks of 16 rows, widening to 32 once average tokens per expert clears a threshold, and a persistent Stream-K kernel claims flat (block, column, k-slice) units exactly as the dense Stream-K does, with three indirections added. Block rows gather activations through the sorted token ids, `expert_ids` selects the weight tensor’s expert slab, and router weights fold into the epilogue as a per-row multiply. One kernel shape serves 60-expert top-4 routing at batch one, where most blocks hold a single real row, through full prefill batches. At high tokens per expert the layer leaves the fused kernel by the same logic as dense layers, running per-expert `tcgen05` launches on few-SM parts and, on datacenter parts, a transposed variant of the dense-tier dequant that materializes expert weights in the [N, K] order the stock bf16 fused-MoE kernels consume.

## End-to-end results

We benchmarked six modes, using one public checkpoint per mode, against every mixed-precision backend that runs on this hardware, with prefix caching off, 1,024-token prompts, and 128 output tokens. The table shows Swordfish tokens per second at batch 32, with the multiple over Marlin, the strongest baseline across modes, in parentheses.

| Mode, model | B200 prefill | B200 decode | Thor prefill | Thor decode |
| --- | --- | --- | --- | --- |
| GPTQ int4, Llama-8B | 89.5k (3.4x) | 7,176 (1.00x) | 7.1k (2.4x) | 790 (0.99x) |
| AWQ int4+zp, Qwen-3B | 193.7k (3.2x) | 10,426 (1.06x) | 15.1k (2.3x) | 1,846 (0.97x) |
| GPTQ int8, Qwen-3B | 193.5k (3.8x) | 10,129 (1.10x) | 14.0k (2.7x) | 1,458 (1.01x) |
| act_order, Mistral-7B | 87.7k (3.5x) | 7,163 (1.14x) | 6.1k (2.2x) | 836 (0.98x) |
| Fused MoE, Qwen1.5-MoE | 148.9k (2.2x) | 5,928 (1.03x) | 12.0k (1.6x) | 639 (0.98x) |
| Channelwise int8, TinyLlama | 494.2k (3.5x) | 20,547 (1.21x) | 37.1k (2.3x) | 3,365 (1.00x) |

The same sweep at batch 1 favors Swordfish more strongly. Single-request decode wins or ties every mode on both machines, 1.10x to 1.34x over Marlin on B200 and 1.00x to 1.06x on Thor, and single-request prefill runs 1.4x to 2.8x.

![Image 5: B200 throughput](https://blog.alpindale.net/images/swordfish_b200.png)![Image 6: Thor throughput](https://blog.alpindale.net/images/swordfish_thor.png)

Against the wider field the margins grow. [Exllama](https://github.com/turboderp/exllama) reconstructs fp16 weights and runs dense GEMM above a row threshold, which keeps its large-batch prefill within 10 percent of Swordfish while its decode runs at a quarter to a third. [AllSpark](https://github.com/vllm-project/vllm/pull/12931), an Ampere channelwise-int8 kernel, matches Swordfish within two percent on its one supported mode and supports none of the other five. [Humming](https://github.com/vllm-project/vllm/pull/34556) trails 2x to 3x at prefill where its configurations compile, and the Triton and [Conch](https://github.com/stackav-oss/conch) kernels trail 2x to 5x throughout.

At Thor batch 32, four decode modes trail Marlin by up to three percent. That workload lands in the M 17 to 48 window on a 20-SM part, the regime Marlin’s 256-thread tiles were tuned for, and per-kernel results there range from 0.94x to 1.22x. Complete requests at those settings finish faster on Swordfish regardless, because prefill runs 1.6x to 2.7x ahead.

Speedups compress as context grows, since attention cost grows quadratically while GEMM cost grows linearly, shrinking the quantized GEMM’s share of wall clock. At 131k-token prompts the B200 prefill advantage measures 1.5x.

## Numerical behavior

Every configuration passes prepack tests and GEMM correctness tests against dequantized references on both sm100 and sm110, and the prefill collective additionally matches its dense reference GEMM. For generation we compared greedy decoding across backends over mixed prompts with top-2 logprobs recorded per step. Half the completions were token-identical for all 128 steps. Every divergence in the rest occurred where the top two tokens were exactly tied or one bf16 quantum apart, and a control showed Swordfish diverging from its own reruns at the same rate it diverges from Marlin. Within this test, divergence appeared only where the ranking was already unstable, and the residual variation is argmax tie-breaking under reordered floating-point sums.

The atomic epilogues reorder sums, so greedy output varies across runs at exact ties. `APHRODITE_SWORDFISH_DETERMINISTIC=1` selects shared-memory reduction epilogues for the atomic decode window, restoring run-to-run bit stability with a 5 to 25 percent decode throughput loss on affected shapes, which is why atomics stay the default. The `tcgen05` prefill is deterministic in either mode.

## Scope

Swordfish today supports symmetric GPTQ int4 (`uint4b8`) and int8 (`uint8b128`), AWQ uint4 with zero points, activation reordering, fused MoE, fp16 and bf16 activations, and group sizes 32, 64, 128, and channelwise. Activation reordering across row-parallel tensor-parallel shards and W4A8 activation quantization fall back to Marlin automatically. Consumer Blackwell (sm120) is a different SM and is unsupported. Long term, checkpoints converted to the native NVFP4 or MX formats shed the Transform stage entirely, and where conversion preserves acceptable accuracy we expect it to become the preferred 4-bit path on this architecture.

## Availability

Swordfish is available in [Sonar](https://github.com/dphnAI/sonar) (previously known as Aphrodite Engine), and it was added in [dphnAI/sonar#1707](https://github.com/dphnAI/sonar/pull/1707). Swordfish is selected automatically on supported hardware and checkpoints, and it can be forced with `--linear-backend swordfish` and `--moe-backend swordfish`. It builds on Marlin by Elias Frantar and collaborators, on Machete by the Neural Magic team, on NVIDIA’s CUTLASS, and on the qutlass project, whose sm100 configurations pointed us at the instruction-width ceiling. All measurements used locked clocks, cold-weight rotation, and median timing across repeated runs on a B200 and a Jetson Thor devkit.
