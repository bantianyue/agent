Title: 400 Tokens per Second on a $12,000 Tenstorrent QuietBox

URL Source: https://medium.com/@arnis.us/400-tokens-per-second-on-a-12-000-tenstorrent-quietbox-425aaf55bbeb

Published Time: 2026-08-31T15:05:26Z

Markdown Content:
[![Image 1: Arni Steingrimsson](https://miro.medium.com/v2/resize:fill:32:32/1*qt32Y2mKBLBosoug-_UDKQ.jpeg)](https://medium.com/@arnis.us?source=post_page---byline--425aaf55bbeb---------------------------------------)

13 min read

1 day ago

_720 MB of on-chip SRAM previews what Galaxy can do for foundation models_

We took Marco-Nano-Instruct, an 8-billion-parameter mixture-of-experts model with roughly 0.6 billion parameters active per token, and pushed its complete autoregressive decode pipeline to 397.7 tokens per second on a Tenstorrent QuietBox (Blackhole) sitting beside the desk.

Press enter or click to view image in full size

![Image 2](https://miro.medium.com/v2/resize:fit:700/1*L4bxSLsU2vQiCgsvzGGTeQ.png)

The trace itself crossed 400, reaching 402.6 tokens per second when replayed without the final token-log delivery. The strongest measured all-DRAM end-to-end result in the project record was approximately 260 tokens per second. Optimizing around Blackhole’s on-chip SRAM moved the system into a different performance class.

This was batch one. There was no speculative decoding, no draft model, no skipped layers, and no hidden second stream inside the per-user number. A token passed through all 28 layers, final normalization, the language-model head, global argmax, and device-side feedback before the next token began.

We used the same families of optimization that high-performance NVIDIA code uses: kernel fusion, asynchronous prefetch and double buffering, carefully sharded dataflow, device-side state, and traced graph replay — the Tenstorrent equivalent of work commonly expressed through custom CUDA kernels, TMA-style movement, and CUDA Graphs. Both DRAM and SRAM paths received that treatment.

SRAM was the additional lever. Instead of fetching the critical recurring data for every token, we kept it beside the Tensix cores that consumed it.

What is the big deal? Marco Nano is small by current foundation-model standards.

That is exactly the point.

We had four Blackhole chips, so we scaled the model down until its critical decode path could fit the available on-chip memory. Tenstorrent scales in the other direction: add chips, add SRAM, add memory bandwidth, add compute, and preserve the programming model. In the coming weeks we will receive a 32-chip Galaxy Blackhole and begin applying the same idea to foundation models.

Tenstorrent already publishes [350 tokens per second for DeepSeek-R1–0528 at 100K context](https://tenstorrent.com/solutions/llm-inference) on Galaxy superclusters. Marco Nano is the desk-scale proof of why that result is architecturally plausible.

This is the territory where Tenstorrent can push performance in a direction NVIDIA’s HBM-centered systems were not designed around: scale the machine until the critical path fits in distributed SRAM, then stop making the expensive external-memory trip.

## What Tenstorrent built

Most people working with AI know NVIDIA. Far fewer know what is inside a Tenstorrent processor, so it is worth starting with the hardware.

Blackhole is a grid of Tensix cores connected by two on-chip networks. Each Tensix core combines:

*   a tile-based matrix engine;
*   a vector engine;
*   programmable RISC-V cores for compute and data movement;
*   local SRAM;
*   hardware-managed circular-buffer flow control.

Two user-programmable data-movement kernels can issue asynchronous reads and writes, address the SRAM and DRAM banks, coordinate through semaphores, and move data while the compute kernel is working. Ethernet controllers and additional RISC-V cores are part of the same architecture rather than peripherals bolted around it.

Press enter or click to view image in full size

![Image 3](https://miro.medium.com/v2/resize:fit:700/1*38EGyIr5yWsE7ElGofA32g.png)

The [Blackhole and TT-Metalium presentation from Hot Chips 2024](https://hc2024.hotchips.org/assets/program/conference/day1/88_HC2024.Tenstorrent.Jasmina.Davor.v7.pdf) describes the chip as a “standalone AI computer.” That is a useful phrase. A Blackhole is not merely a matrix engine waiting for a host to feed it. Compute, data movement, local storage, DRAM control, and networking are all programmable parts of the machine.

The current Blackhole p150 product exposes [120 Tensix cores, 180 MB of SRAM, 32 GB of GDDR6 at 512 GB/s, and 664 TFLOPS at Block FP8](https://docs.tenstorrent.com/aibs/blackhole/). It also has four 800-Gigabit Ethernet ports for direct Blackhole-to-Blackhole connectivity.

The QuietBox packages four Blackhole processors with an AMD EPYC host, 512 GB of system memory, 4 TB of NVMe storage, and the cables needed to connect the cards as a high-bandwidth mesh. [Tenstorrent priced the system at $11,999](https://open.tenstorrent.com/vision/tenstorrent-launches-blackhole-developer-products-at-tenstorrent-dev-day).

Aggregated across its four processors, that is approximately:

![Image 4](https://miro.medium.com/v2/resize:fit:648/1*2DUDvJDqhnfOYGhzJ-QqvA.png)

All of it is locally owned and fully programmable through Tenstorrent’s open-source software stack.

## Why LLM decode is usually a memory problem

Running an LLM has two distinct phases. Prefill processes the input prompt, where many tokens can be evaluated together. Decode generates the answer one token at a time. Each new token depends on the token before it, so at batch one there is very little parallel work across tokens.

That changes the balance of the machine.

During decode, every transformer layer must apply its active weights to a single token. The matrix engines can perform the required arithmetic extremely quickly, but a matrix-vector operation does not reuse each fetched weight very much. If those weights come from external memory, the processor can spend more time waiting for bytes than performing math. Adding more arithmetic throughput does not fix a pipeline whose compute engines are waiting to be fed.

Mixture-of-experts models help because only a subset of the expert weights is active for each token. They do not eliminate the problem. Shared attention weights, the selected experts, the growing KV cache, and other recurring state still have to reach the cores on every decode step.

This is why high-performance inference software uses fusion, prefetching, double buffering, sharding, and graph replay. Those techniques reduce traffic and overlap movement with useful work. But if the same critical data still has to cross the external-memory interface for every token, that interface remains the ceiling.

The hardware question is therefore not only, _How many operations can the chip execute?_ It is also, _How quickly can the chip put the next operands in front of the compute engines?_

That is the context for Tenstorrent’s memory bet.

## The memory bet

Modern AI processors spend much of their time moving tensors rather than multiplying them. The arithmetic units have become faster more quickly than external memory can feed them.

NVIDIA addresses this with HBM: expensive, very high-bandwidth memory placed beside the GPU through advanced packaging. An H100 SXM, for example, provides [80 GB of HBM at 3.35 TB/s](https://www.nvidia.com/en-us/data-center/h100/). That is an enormous off-chip feed, backed by a mature CUDA software stack.

Tenstorrent makes a different trade. Blackhole uses lower-cost GDDR6 for large capacity and distributes a much smaller amount of extremely fast SRAM directly among the compute cores.

The Hot Chips presentation makes the difference visible:

Press enter or click to view image in full size

![Image 5](https://miro.medium.com/v2/resize:fit:700/1*hG60LjGQLqEskQwEvSpgAQ.png)

These are architectural aggregate figures from the full Blackhole design, not a promise that every kernel sees 94 TB/s. SRAM bandwidth scales with the number of cores participating and with the data-movement pattern. A kernel using eight cores sees a small fraction of the chip total; a correctly sharded operation using the grid can expose far more.

That qualification is the whole idea.

Tenstorrent does not automatically turn the SRAM into a cache. The programmer or compiler decides where a tensor lives, how it is sharded, which cores consume it, when it can be overwritten, and which network path moves it. There is more responsibility in the software, but there is also much more control.

The upside is that a tensor already in SRAM does not need to cross an HBM or GDDR interface at all.

> _The highest-bandwidth memory transaction is the one you stop issuing._

## A scaled-down Galaxy experiment

Marco Nano gave us the right shape for the experiment. It is a real 28-layer MoE with 232 experts per layer and eight selected for each token. It exercises attention, a growing KV cache, routing, expert execution, tensor-parallel collectives, and autoregressive feedback — the same categories of work a much larger MoE must perform.

The total model is 8 billion parameters, but only about 0.6 billion are active for a token. That made it possible to reproduce the memory strategy on four chips: retain the critical recurring attention and decode state in SRAM while streaming selected expert weights from GDDR6.

We did use Blackhole’s native low-precision formats: Block FP4 for selected attention and language-model weights, and Block FP8 where the accuracy gates allowed it. Those formats are part of the hardware proposition, not a last-minute benchmark trick. The same model architecture, all 28 layers, and the same autoregressive dependency remained in the path. We did not use speculative decoding to multiply the reported token rate.

The important result is not the placement recipe. It is that the memory hierarchy can be scaled with the model. Four chips were enough to demonstrate it on Marco Nano. A Galaxy supplies 32 chips. Multiple Galaxies extend the SRAM and compute footprint again.

## What it changes in practice

The best measured all-DRAM end-to-end path in our record reached approximately 260 tokens per second. After optimizing the pipeline around persistent SRAM data, the delivered path reached 397.7 tokens per second — about 53% more throughput. Raw trace replay, with no final token-log delivery, reached 402.6.

## Get Arni Steingrimsson’s stories in your inbox

Join Medium for free to get updates from this writer.

Remember me for faster sign in

This is a best-pipeline comparison rather than a claim that one environment flag creates a 53% gain. Both paths used fusion, prefetching, traced replay, sharding, and device-side execution. The difference is what each memory architecture allowed after those conventional optimizations had been applied. The DRAM path still had to move recurring data through external memory. The SRAM path could stop moving it.

A narrower same-layer residency A/B at context 2,048 measured a 1.248-times throughput improvement. That is the clean isolation of memory placement; 397.7 tokens per second is the full-system result after designing the rest of the dataflow around it.

Press enter or click to view image in full size

![Image 6](https://miro.medium.com/v2/resize:fit:700/1*OQ_7y8kW3CeO3HPnwZeSMA.gif)

_Presentation playback at approximately 400 tokens per second. The Iceland copy is curated to make the stream visible; this is a speed visualization, not a model-quality sample._

The headline is the experience:

Press enter or click to view image in full size

![Image 7](https://miro.medium.com/v2/resize:fit:700/1*qsmzbhHT7S0BXOIq6Aw-PA.png)

That changes how the model feels. A long answer arrives almost immediately. A coding agent can inspect, propose, test, and revise without spending most of its loop waiting for inference. An evaluation can explore more prompts. A researcher can try more ablations. An agent can consider more branches before choosing one.

High token throughput is not merely a serving benchmark. It is iteration speed.

And iteration speed compounds. If a person can complete twice as many useful model interactions in an hour, the value is not just the saved seconds. It is the extra experiments that become cheap enough to attempt.

## Why SRAM is more than bandwidth

The distinction is between staging and residency.

Every accelerator stages data. NVIDIA developers use asynchronous copies, TMA, double buffering, kernel fusion, CUDA Graphs, and increasingly sophisticated runtimes to hide HBM traffic behind compute. We used the corresponding techniques in TT-Metal: asynchronous NoC reads, prefetching, fused kernels, sharded layouts, circular buffers, and trace replay.

But staging still moves the bytes. Residency removes the repeated trip.

Blackhole’s SRAM is explicitly managed, so the program decides which recurring tensors remain on chip and which consumers read them directly. Once the pipeline is arranged around that fact, intermediate copies and host synchronization can disappear with the DRAM traffic.

This is the software contract behind Tenstorrent’s hardware. The chip supplies fast local memory, programmable movement, compute, and network width. The program turns them into a continuous pipeline.

## From four chips to 32

The QuietBox is the desk-scale version of the architecture. Galaxy is where the scaling argument becomes interesting.

A Galaxy Blackhole connects 32 Blackhole ASICs in a 6U system. Tenstorrent publishes [23 PFLOPS of Block FP8 compute, 6.2 GB of SRAM at 2.9 PB/s, 1 TB of GDDR6 at 16 TB/s, and a 32 TB/s accelerator fabric](https://tenstorrent.com/hardware/galaxy). The system starts at $160,000. A four-Galaxy supercluster starts at $640,000, and larger configurations extend over standard Ethernet scale-out.

Press enter or click to view image in full size

![Image 8](https://miro.medium.com/v2/resize:fit:700/1*NZZnFoZu7TykXlv06Pju-w.png)

The price grows by about 9.2 times from QuietBox to Galaxy. The processor count grows eight times, SRAM grows about 8.6 times, DRAM capacity grows 7.8 times, and compute grows about 8.6 times. It is a remarkably direct scale-up of the same programming model.

A four-Galaxy supercluster extends that footprint to 128 Blackhole processors, 24.8 GB of on-chip SRAM, 4 TB of GDDR6, and 92 PFLOPS of Block FP8 compute for a published starting price of $640,000. These are aggregate resources rather than a claim of one flat memory space; the performance a model sees depends on its partitioning, communication pattern, and placement.

Multiple Galaxies extend the idea again. The system does not become one magical flat SRAM cache. Instead, it provides more distributed SRAM beside more compute, more DRAM beside that SRAM, and more network links through which regular tensor shards can move.

For a large MoE, the principle is the same as Marco Nano: keep the critical recurring path in distributed SRAM, stream the colder capacity from GDDR6, and add Galaxies when the resident path needs more memory or more compute width.

This is why Tenstorrent’s DeepSeek result matters. It is not only a large number attached to a large machine. It demonstrates that the same memory hierarchy can be expanded until the important working set of a 671-billion-parameter model has enough on-chip capacity and enough parallel consumers to matter.

## The NVIDIA comparison

NVIDIA and Tenstorrent are making different bets.

NVIDIA builds exceptionally powerful accelerators around HBM, NVLink, and a deeply mature proprietary software ecosystem. The strategy is to make external memory as fast as possible and then hide its movement with caching, prefetching, fusion, and scheduling. It works extraordinarily well, but HBM, advanced packaging, and proprietary scale-up infrastructure are expensive.

Tenstorrent uses standard GDDR6 for capacity, SRAM beside the compute for the hottest data, RISC-V control, and Ethernet for scale-out. A p150 card currently lists for $1,399. A complete four-chip QuietBox listed for $11,999. Galaxy starts at $160,000.

If a workload must continually stream its working set from external memory, HBM’s bandwidth is a formidable advantage. But when the critical path stays in SRAM, the contest changes. Blackhole’s published local/sharded SRAM figure is 94 TB/s against 512 GB/s from its own GDDR6 and 3.35 TB/s from an H100’s HBM. Those figures describe different access patterns, but they show the operating region Tenstorrent is building toward.

Perfect HBM prefetch still moves the data through the HBM interface. A resident SRAM pipeline does not issue that transaction. NVIDIA cannot solve that difference merely with another fusion pass; it has to devote more scarce on-chip memory to the working set or keep buying external bandwidth. Tenstorrent starts with a large, programmable SRAM footprint and scales that footprint by adding relatively inexpensive networked chips.

This is not a claim that a QuietBox replaces an H100 on every workload. It is a claim that there is a performance region — recurring working sets that can be distributed across SRAM — where Tenstorrent’s architecture can compete on terms that are difficult and expensive for an HBM-centered system to match.

Marco Nano shows that this is achievable, and measurable, on hardware an individual developer or small team can own.

That ownership changes the economics in a way cloud benchmarks often miss.

There is no per-token invoice. There is no rate limit imposed by an API provider. Private data does not leave the machine. A model can run overnight generating synthetic data, evaluating prompts, searching kernel variants, or supporting agents without anyone deciding whether the next million tokens fit this month’s budget.

The costs do not disappear: hardware, electricity, cooling, engineering time, and maintenance are real. Utilization matters. So does model quality. But the marginal decision changes from “is this call worth paying for?” to “is this experiment worth running?”

For research and product development, that freedom is substantial.

## Performance per dollar is also freedom per dollar

AI infrastructure discussions often reduce economics to cost per million tokens. That is useful for a serving business, but incomplete for someone building with models.

Fast owned inference buys several things at once:

*   interactive latency low enough that long outputs still feel immediate;
*   enough throughput to run broad evaluations instead of spot checks;
*   freedom to generate training and synthetic data locally;
*   predictable capacity for agents and internal tools;
*   privacy for proprietary code, documents, and customer data;
*   the ability to modify the complete stack, down to the kernel;
*   no dependency on a provider’s model availability, pricing, or usage policy.

At roughly 400 tokens per second, a single continuous stream has a theoretical capacity of about 1.44 million tokens per hour. Real utilization will be lower and real workloads include prefill, batching, and orchestration. The number is still large enough to change behavior. Instead of rationing inference, a small team can treat it as an available local resource.

That may be Tenstorrent’s most interesting performance-per-dollar argument. The hardware is inexpensive enough to own, fast enough to change the development loop, and built to scale without replacing the programming model when the workload outgrows the desk.

## The next scale

The QuietBox experiment answered the small version of the question. A recurrent working set can stay in Blackhole SRAM, selected cold weights can stream from GDDR6, and the resulting full-token pipeline can approach 400 tokens per second on a small MoE.

Galaxy lets us ask the large version.

How much of a foundation model’s shared working set can remain resident across 32 chips? How should KV be distributed as context grows? Where should expert prefetch overlap attention? How much batching improves tile utilization without giving up per-user latency? When multiple Galaxies are connected, which tensors should move and which should never leave the SRAM beside their consumer?

Those are software questions enabled by a hardware choice.

HBM-centered systems ask how quickly the accelerator can keep fetching tensors from memory outside the compute grid. Tenstorrent asks how much of that fetch can be eliminated, then supplies SRAM and network capacity that grow as systems are added.

The QuietBox makes that architecture accessible for $12,000. Galaxy carries the same idea to foundation-model scale.

The exciting part is not SRAM by itself. It is what happens when fast memory, programmable data movement, cheap capacity, and scale-out are treated as one computer — and when that computer is affordable enough to own.
