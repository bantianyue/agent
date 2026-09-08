# The Math Needed for AI Inference Engineering (Complete Roadmap)

- Author: @TheVixhal (vixhaℓ)
- Published: Mon Sep 07 17:07:30 +0000 2026
- URL: https://x.com/TheVixhal/status/2097008871231672595
- Likes: 377
- Retweets: 37
- Replies: 5
- Bookmarks: 887
- Views: 0

In this article, I'm going to break down the essential math you need for AI inference engineering. I'll also share the exact roadmap and resources that helped me personally. Let's get straight to it.

# 1. Numbers and Precision

How the hardware stores a number, and what breaks when it can't

I skipped this at first because it looked like trivia. Then I spent two days debugging a quantized model that was producing nonsense, and the reason was in here. Learn it early.

## 1.1 How a float is built

A floating point number is stored as three parts: a sign bit, some exponent bits, and some mantissa bits. The exponent bits control how large or small a number you can represent. The mantissa bits control how many meaningful digits you keep. 

Every format is just a different split of the available bits between those two jobs, so once you understand the tradeoff you can predict how any format will behave.

## 1.2 The formats you'll run into

- FP32 has 8 exponent bits and 23 mantissa bits. It's the reliable default, and it's slow and memory hungry.

- FP16 halves the memory but only has 5 exponent bits, so the range of values it can hold is small. Values can overflow to infinity or shrink to zero more easily than you'd expect.

- BF16 keeps FP32's 8 exponent bits and gives up mantissa bits instead. You get the same range as FP32 with less precision. Most modern work defaults to it because losing precision adds a bit of noise, while losing range gives you infinities that propagate through everything.

- FP8 comes in two variants, E4M3 and E5M2. The names tell you the split, so E4M3 has 4 exponent bits and 3 mantissa bits.

- INT8 and INT4 are integers, so the spacing between representable values is fixed rather than relative. They need a separate scale factor to represent anything other than small whole numbers.

## 1.3 Rounding and its consequences

Every arithmetic operation rounds the result to the nearest representable value, which introduces a small error. 

Over a long sequence of operations those errors accumulate, which is why summing a long vector in FP16 drifts away from the correct answer, and why fast kernels usually keep the running total in FP32 even when the inputs are lower precision.

You also want to understand overflow and underflow properly. In FP16 a single unusually large activation value can exceed the maximum and turn into infinity, and from there everything downstream is ruined.

## 1.4 Epsilon and cancellation

Machine epsilon is the smallest difference between two representable numbers near 1.0. It's what tells you how close two floats have to be before comparing them stops meaning anything.

Catastrophic cancellation happens when you subtract two numbers that are almost equal. The leading digits cancel out and what's left is mostly rounding error. 

This comes up in normalization layers and in variance calculations, where the textbook formula subtracts two large similar quantities and the numerically stable version rearranges the arithmetic to avoid it.

## 1.5 Stable softmax

Softmax involves computing the exponential of each input. If an input is around 90, its exponential overflows FP32 entirely. 

The standard fix is to subtract the largest input value from all of them before exponentiating, which gives the same answer mathematically because softmax is unchanged by shifting all inputs by a constant.

The general version of this technique is log-sum-exp, and it's worth learning properly rather than just memorizing the softmax fix. It's the basis for computing log probabilities stably, and the online softmax used inside FlashAttention is a variation on the same idea.

# 2. Quantization Math

Storing weights in fewer bits

Quantization is where most of your memory and bandwidth savings come from. The core math is a linear mapping, so it's more approachable than the paper titles suggest.

## 2.1 The mapping

You're taking a range of float values and mapping it onto a small set of integers. Two numbers define the mapping. 

The scale says how much real value each integer step covers, and the zero point says which integer corresponds to actual zero. To quantize you divide by the scale, add the zero point, and round. To dequantize you reverse it.

Almost every quantization method is a different strategy for choosing those two numbers well.

## 2.2 Symmetric and asymmetric

Symmetric quantization fixes the zero point at zero and centers the range on it. The arithmetic is cheaper, and it works well for weights, which tend to be roughly centered already.

Asymmetric quantization lets the zero point move, which handles lopsided distributions better. Activations after a ReLU are never negative, so a symmetric range would waste half its integers on values that never occur.

## 2.3 Granularity

You can use one scale for an entire tensor, one per channel, or one per fixed size group of values such as 64 or 128. 

Finer granularity gives you better accuracy because a few extreme values in one part of the tensor no longer set the scale for everything else. The cost is that you store and handle more scale factors. INT4 methods generally need group-level scales to stay accurate enough to use.

## 2.4 Choosing the range

Before you can quantize you have to decide what float range you're mapping from. The simplest choice is the observed minimum and maximum, but a single extreme value will then stretch the range and leave very little resolution for the values you care about. 

Percentile clipping deliberately cuts off the tails. A more careful approach searches over candidate ranges and keeps whichever gives the lowest error, measured either as squared error or as KL divergence against the original distribution.

Weight ranges you can measure exactly since the weights are fixed. Activation ranges depend on the input, so you need to run a small calibration set through the model and record what you see.

## 2.5 Outliers

In transformers, a small number of activation channels carry values many times larger than everything else. If you understand why one large value destroys your effective resolution for the rest of the tensor, then the motivation behind the various outlier handling methods becomes obvious. 

They either isolate the outlier channels and keep them at higher precision, move the difficulty between weights and activations, or rescale channels so the ranges are more even.

## 2.6 Curvature methods, briefly

The stronger weight quantization methods use information about which weights the output is most sensitive to, approximated with a Hessian. Weights the model barely depends on can be rounded carelessly, and weights it depends on heavily get compensated for.

You don't need to derive the update rules to use these methods, but knowing that the Hessian is being used as a sensitivity estimate explains why they beat plain rounding by a wide margin.

# 3. Linear Algebra for Compute

The same operations, costed out instead of interpreted

If you've done a training roadmap you already know what a matrix multiply means. For inference you need to know what it costs.

## 3.1 Counting the cost of a matmul

Multiplying an m by k matrix with a k by n matrix takes roughly 2 times m times n times k floating point operations, since each output element is a dot product of length k with a multiply and an add per step. Separately, you have to read both input matrices out of memory and write the output back.

Get comfortable estimating both of those by hand for the shapes in your model. Being able to say "this layer should take about this long" before you profile anything is the single most useful habit in this whole area.

## 3.2 Matrix times matrix versus matrix times vector

A matrix times a matrix does a lot of arithmetic per byte of data loaded, because each loaded value gets reused across many output elements. A matrix times a vector does very little arithmetic per byte, because each weight is loaded, used once, and discarded.

Generating one token at a time for a single request is essentially the second case, and that fact explains a large fraction of why serving language models is difficult.

## 3.3 Arithmetic intensity

Arithmetic intensity is the number of operations divided by the number of bytes moved. It's the number you check first.

If intensity is high, the chip's compute rate limits you. If it's low, memory bandwidth limits you and the compute units sit idle waiting for data. Most inference workloads are in the second situation, which is why so much optimization effort goes into moving fewer bytes rather than doing less arithmetic.

## 3.4 How tensors sit in memory

You need to understand row major and column major layout, strides, and what it means for a tensor to be contiguous. You also need to know why transposing a matrix costs real time even though it changes nothing mathematically, and why shapes get padded to specific multiples so the hardware's matrix units can be used at all.

## 3.5 Tiling

Tiling means splitting a large matmul into small blocks that fit into fast on-chip memory, then reusing each block as much as possible before evicting it. The math involved is arithmetic about how much fits in cache and how many times each piece gets reused, and it's the central idea behind every fast kernel you'll read.

## 3.6 Low rank structure and sparsity

The rank of a matrix tells you how much independent information it actually contains. Singular value decomposition lets you approximate a matrix with a lower rank version that takes less memory, which is the basis for low rank compression and for low rank adapters.

An adapter is a low rank update added to the base weights, so understanding rank tells you why merging one into the base model is exact and why serving many adapters simultaneously needs a different approach.

For sparsity, the practical thing to know is that structured patterns like two nonzeros in every group of four have hardware support and give real speedups, while unstructured sparsity often runs slower despite doing less arithmetic, because the indexing overhead outweighs the savings.

# 4. Performance Modeling

Estimating runtime before you measure it

This section has the least to do with machine learning and it's the part I use most often.

## 4.1 The roofline model

If you plot achievable performance against arithmetic intensity, you get two limits. 

There's a sloped line representing memory bandwidth, which caps you when intensity is low, and a horizontal line representing peak compute, which caps you when intensity is high. Every kernel you run sits somewhere under one of those two ceilings.

Learning to place a workload on that chart tells you immediately whether to work on memory access or on arithmetic, which stops you from spending a week optimizing something that was never the constraint.

## 4.2 Bandwidth bound estimates

When you're limited by memory, runtime is approximately the bytes you have to move divided by the memory bandwidth of the device.

Here's the kind of estimate this lets you make. A 7 billion parameter model stored in FP16 takes about 14 GB. To produce one output token you read every weight once, so dividing 14 GB by your GPU's memory bandwidth gives you a floor on the time per token before you account for anything else.

If you redo that division with 4-bit weights, the floor drops by roughly a factor of four, which is why quantization speeds up single-request generation even when the arithmetic is unchanged.

## 4.3 Latency and throughput

Latency is how long one request takes. Throughput is how many requests you finish per second. Increasing the batch size improves throughput and worsens per-request latency, so you're choosing a point on a curve rather than finding a setting that's best at both.

## 4.4 Little's Law

Little's Law says the average number of requests in the system equals the arrival rate times the average time each request spends there.

It's a one-line formula and it answers a very practical question, which is how many requests have to be in flight at once to reach a given throughput. Once you know that number you know how much KV cache memory you need to reserve.

## 4.5 Queueing behavior

You don't need much formal queueing theory, but you do need to internalize one result. As utilization approaches full capacity, waiting time grows without bound rather than linearly. 

Moving a server from 90 percent to 95 percent utilization makes queueing delays much worse than the five point difference suggests, which is the reason capacity planning always leaves headroom.

## 4.6 Amdahl's Law

The speedup you can get from optimizing one stage of a pipeline is limited by what fraction of total time that stage takes. It's a useful thing to compute before you start work on something that turns out to be three percent of your runtime.

## 4.7 Splitting across devices

When a model is split across several GPUs, the devices have to exchange intermediate results. You want a rough sense of what collective operations like all-reduce and all-gather cost, and how that cost grows with the number of devices and the size of the messages.

The failure case worth understanding is splitting a model and getting slower results, which happens when you add communication in order to reduce compute that wasn't limiting you in the first place.

# 5. Transformer Inference Arithmetic

Applying all of the above to the actual workload

## 5.1 Two phases with opposite behavior

Processing the input prompt happens all at once, with every token computed in parallel. There's plenty of arithmetic per byte loaded, so this phase is usually compute bound and the per-token cost is low.

Generating output happens one token at a time, and each step reads the entire set of weights to produce a single token. There's very little arithmetic per byte, so this phase is memory bound and the per-token cost is much higher.

Nearly every serving optimization exists because these two phases want different things from the hardware.

## 5.2 Sizing the KV cache

This calculation decides how many users you can serve at once, so it's worth being able to do from memory. 

The total size depends on the number of layers, the number of key and value heads, the dimension of each head, the bytes per stored element, the sequence length, and the batch size. Multiply those together and include a factor of two because you store both keys and values.

Two things to notice once you've done it. The size grows linearly with both sequence length and batch size, and it doesn't shrink when you quantize the weights. For long context serving the KV cache is a bigger problem than the weights are.

## 5.3 Where attention starts to dominate

The attention score computation grows with the square of the sequence length, while the feed forward layers grow linearly with it. At short sequence lengths the quadratic term is small enough to ignore and the feed forward layers dominate the cost. 

There's a crossover length beyond which attention becomes the main expense, and it's worth knowing roughly where that point falls for the model shapes you work with.

## 5.4 Reducing the number of key and value heads

Grouped query attention and multi query attention keep the full number of query heads but share key and value heads across groups. If you redo the KV cache calculation from 5.2 with the smaller number of key and value heads, the memory saving falls straight out of the arithmetic.

## 5.5 Paging and fragmentation

Instead of reserving one contiguous block of memory per request for the maximum possible sequence length, you can allocate the KV cache in small fixed size blocks as the sequence grows. 

The relevant quantities are how much space is wasted in the last partly filled block of each sequence, what fraction of your reserved memory holds real data, and how much memory two requests that share a prompt prefix can share between them.

## 5.6 Batching over time

Static batching collects a group of requests, runs them together, and waits for all of them to finish. When requests generate different numbers of tokens, the short ones finish early and their slots sit idle while the longest one continues.

Continuous batching adds new requests into free slots as old ones complete. The math is about how full your slots stay over time, and how much of that idle capacity you recover.

# 6. Probability for Decoding

What the sampling settings do to the output distribution

## 6.1 Softmax and temperature

Softmax converts raw scores into a probability distribution. Temperature divides the scores before the softmax is applied. A temperature below one increases the gap between the top choice and the rest, concentrating probability on fewer tokens. 

Above one it flattens the distribution out. As temperature approaches zero you converge on always picking the highest scoring token.

Thinking about this as reshaping a distribution, rather than as a general creativity setting, makes it much easier to reason about why output quality changed.

## 6.2 Cutting off the tail

Top-k keeps the k most probable tokens. Top-p, also called nucleus sampling, keeps the smallest group of tokens whose probabilities add up to p. Min-p keeps tokens whose probability is above some fraction of the top token's probability.

All three discard part of the distribution and then renormalize what's left so it sums to one again. They differ in how they decide where to cut, and specifically in whether the cutoff adapts to how confident the model is at that step.

## 6.3 Entropy and perplexity

Entropy measures how spread out the distribution is at a given step, which makes it a reasonable signal for how uncertain the model is and a useful input to decoding strategies that adapt as they go.

Perplexity is the exponential of the average negative log probability over a dataset. It's the standard number people report when checking whether a quantization or optimization change damaged the model.

## 6.4 KL divergence

KL divergence measures how far one probability distribution is from another. In practice you use it to compare your optimized model's output distribution against the original model's on the same inputs. A small divergence means your speedup came for free. 

A large one means you changed the model's behavior even if the benchmark score happens to look similar.

## 6.5 Speculative decoding

A small fast model proposes several tokens ahead, and the large model verifies all of them in a single pass. The verification step uses rejection sampling, arranged so that the tokens you end up accepting follow exactly the distribution the large model would have produced on its own. That guarantee is the interesting part and it's worth reading the derivation.

The expected speedup is a calculation rather than a guess. It depends on how often the draft tokens get accepted, how many are proposed per step, and the cost ratio between the two models. If you don't do that calculation you can easily build something slower than what you started with.

## 6.6 Reproducibility

Floating point addition isn't associative, so adding the same set of numbers in a different order gives a slightly different result. Changing the batch size changes the order in which values get summed inside the kernels, which changes the last few bits of the logits, which occasionally changes which token gets sampled. 

Same prompt and same seed can therefore give different output at different batch sizes, and this follows from how the arithmetic works rather than from a mistake in the serving code.

# 7. Statistics for Benchmarking

Measuring speed without fooling yourself

Most inference benchmarks you'll see published go wrong in one of the ways below:

## 7.1 Percentiles rather than averages

Report the median, the 95th percentile, and the 99th percentile. An average hides the requests that went badly, and users experience the slow tail rather than the mean.

Keep in mind that estimating a 99th percentile requires a lot of samples. If you ran fifty requests, your p99 is one or two data points and shouldn't be quoted as a measurement.

## 7.2 Report the phases separately

Time to first token measures how long the user waits before anything appears, and it's dominated by prompt processing and by time spent in the queue. Time per output token measures the streaming speed after that, and it's dominated by memory bandwidth. You also want end to end latency and overall throughput.

Because prompt processing and generation have different bottlenecks, a single tokens-per-second figure can hide almost anything, so these get reported separately.

## 7.3 Noise

You want enough basic statistics to tell an improvement from run to run variation. That means standard deviation on your measurements and some form of confidence interval, so that a two percent gain doesn't get announced as a win when the noise between identical runs is five percent.

Also throw away your first few runs. The initial calls include compilation, memory allocation, and cold caches, and mixing them into your averages makes everything look worse and noisier than it is.

## 7.4 Load generation

Sending requests at a fixed rate regardless of whether earlier ones have finished shows you how the system behaves when it can't keep up, including how the queue builds. 

Keeping a fixed number of workers that each wait for a response before sending the next one hides that, because slow responses automatically slow down your sending rate.

The specific trap to read about is coordinated omission. If your load generator blocks while waiting for a slow response, it isn't sending during the exact period when the system was struggling, so the worst latencies never get recorded at all. This quietly invalidates a lot of published numbers.

# 8. Discrete Math and Bit Level Work

Small things that come up once you read real implementations

## 8.1 Bit manipulation

Packing two 4-bit values into a single byte, then masking and shifting to get them back out. It's simple once you've written it once and confusing before that, so write it once.

## 8.2 Powers of two and alignment

Block sizes are 16, 64, or 128 for reasons connected to memory transaction sizes and matrix unit shapes. You need ceiling division, padding up to multiples, and a sense of what alignment requirements exist. The arithmetic is trivial and the performance consequences aren't.

## 8.3 Hashing and cache hit rates

Detecting that two requests share a prompt prefix generally involves hashing blocks of tokens. You want to be able to reason about hit rates and about what a given hit rate does to your effective throughput, plus a basic understanding of tree structures for storing shared prefixes.

## 8.4 Complexity notation

Enough to notice when a scheduler or an eviction policy is doing work that grows quadratically in the number of active requests. You're not writing proofs, you're checking whether something will still be fine at a thousand concurrent requests.

# How I Learned This

I didn't learn any of it in the order above, and you probably won't either. This is the path I'd suggest to someone starting now.

1. Get the framing first

Horace He's post "Making Deep Learning Go Brrrr From First Principles" sorts everything into compute bound, memory bound, and overhead bound. Read it before anything else, because that classification is what you'll use to organize the rest.

Then work through kipply's "Transformer Inference Arithmetic" with a calculator open. It has the actual formulas and the actual numbers, and doing the arithmetic yourself is the difference between recognizing it and knowing it.

2. Learn what the hardware is doing

Programming Massively Parallel Processors by Kirk and Hwu is the standard GPU programming book. Even if you never write a production kernel, the chapters on the memory hierarchy and on tiling change how you think about cost.

The GPU MODE lecture series, previously called CUDA MODE, is free and shows people reasoning through real kernels, which is hard to get from books.

For Computer Architecture: A Quantitative Approach by Hennessy and Patterson, don't try to read it through. The chapters on memory hierarchy and on performance measurement are where roofline reasoning and Amdahl's Law come from, and those are the ones you want.

3. Floating point

David Goldberg's "What Every Computer Scientist Should Know About Floating-Point Arithmetic" is old and still the best thing on the topic. It's dense, so give it two passes rather than trying to absorb it in one.

Then go and break things on purpose. Write short scripts that overflow FP16, that show error accumulating over a long sum, that make naive softmax produce infinities. Fifteen minutes of that taught me more than the reading did.

4. Quantization

Read a survey paper on quantization for efficient inference to pick up the vocabulary, then read the papers behind whichever methods you actually use. Once scale and zero point are solid, most of these papers are readable in one sitting.

The exercise I'd recommend is implementing quantize and dequantize yourself on a single weight matrix, measuring the reconstruction error, then switching from one scale per tensor to one per channel and watching the error drop. That afternoon did more for me than the papers.

5. Serving systems

Read the FlashAttention paper for the tiling and online softmax ideas rather than for the CUDA specifics. Most of what it's doing is reducing memory traffic.

The vLLM paper on PagedAttention is the clearest explanation of why KV cache memory management, rather than raw compute, is what limits how many users you can serve.

The speculative decoding papers are worth reading for the rejection sampling argument, which is a genuinely nice piece of probability.

6. Measurement

Systems Performance by Brendan Gregg has nothing to do with machine learning, which is why it helps. It teaches you to measure honestly, take tail latency seriously, and avoid the standard benchmarking mistakes.

Separately, look up coordinated omission and read whatever you find. It changed how I read every latency number after that.

## The loop that made it stick

Reading got me a certain distance and then stopped working. What actually worked was this:

1. Pick a model, and compute by hand its weight memory, its KV cache per token, and the theoretical minimum time per output token on your hardware.

2. Run it and measure the same quantities.

3. Work out why your prediction was wrong.

The third step is where the learning happens. Every gap between my estimate and the measurement came from something I didn't know about yet, and chasing down that thing taught me more than the original calculation did.

# What You Can Leave Out

Optimization theory beyond the basics isn't needed. Convergence guarantees, convexity, and saddle point analysis matter for training, and for inference the model's weights are already fixed. 

Similarly you can skip most Bayesian statistics and all formal queueing theory beyond Little's Law and the utilization warning in 4.5. Deriving backpropagation is good background but you won't use it here.

The things that look boring and aren't optional are floating point behavior, arithmetic intensity and roofline reasoning, KV cache sizing, and honest measurement with percentiles. Those four come up constantly. The rest of the list is depth you can pick up when a specific problem forces you to.

One last thing that took me a while to accept. A training roadmap is mostly calculus and probability, and this one is mostly counting bytes and estimating time. 

If you came in expecting the first kind of math and feel like you've wandered into a systems course, that's the right feeling and the field really is like that.
