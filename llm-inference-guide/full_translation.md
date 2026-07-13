A first-principles tour of what happens between your prompt and the streamed response: tokenization, embeddings, attention, the prefill/decode split, KV caching, and quantization.
---
You type a prompt. A few hundred milliseconds later, words start streaming back at you one at a time. Feels simple. It isn't.What happens between your keystroke and that first token is one of the most carefully engineered pipelines in modern computing. And the strangest part? The model does two completely different jobs to answer you, with two different bottlenecks, on the same GPU, in the same request.Once you see it, you'll never look at a generate() call the same way again.
## The mental model
An LLM is a neural network that predicts the next token. Just one token. Then it takes that token, sticks it onto the end of your prompt, and predicts the next one. Then repeats it.That's it. That's the whole loop.The interesting question is: how does it predict that next token, and why does the **second token** come out **much faster** than the first?
## Step 1: Your text becomes numbers
Neural networks don't read English. They read vectors. So the first thing that happens to your prompt is **tokenization**, which chops your text into pieces and assigns each piece an integer ID.Most modern LLMs use a scheme called Byte Pair Encoding. The idea: start with raw characters, then merge the most common adjacent pairs over and over until you have a vocabulary of ~50,000 chunks. Common words like the get one token. Rare words like unhappiness get split into pieces like un + happi + ness.
```python
prompt = "How does inference work?"
ids = tokenizer.encode(prompt)
# ids -> [2437, 1374, 32278, 670, 30]
```
This step matters more than people realize. Languages that weren't well-represented in the tokenizer's training data get chopped into more pieces, which means more tokens, which means higher cost and slower responses for the same sentence.
## Step 2: Each token becomes a vector
Each integer ID gets looked up in a giant matrix called the embedding table. If your model has a vocabulary of 50K and a hidden dimension of 4,096, the table has shape [50000, 4096]. Pick a row, get a vector.
```python
# embedding_table has shape [vocab_size, hidden_dim]
vectors = embedding_table[ids]   # shape: [num_tokens, 4096]

```
These vectors aren't random. During training, the model nudged them around so that semantically similar tokens ended up near each other in this 4,096-dimensional space. king and queen are neighbours. python and snake are neighbours along one axis, python and javascript along another.The embedding layer is also where **position information** gets injected, because attention itself doesn't know which token came first. Modern models use schemes like RoPE that rotate the vectors based on their position in the sequence.
[IMAGE: 2050928191561482240]

## Step 3: Layers of attention
Now the real work begins. Your sequence of vectors gets fed through a stack of **transformer layers**, often 32 or more, one after the other. Each layer does roughly the same thing:Mix information across tokens using **self-attention**.Mix information within each token using a **feed-forward network**.Self-attention is the part worth understanding deeply. For every token, the layer produces three new vectors by multiplying with three learned weight matrices:
```python
# x is the input to this layer, shape [num_tokens, hidden_dim]
Q = x @ Wq # queries
K = x @ Wk # keys
V = x @ Wv # values
```

[IMAGE: 2050926705385287680]
Now you have three views of every token. The trick: each token uses its **query** to look at every other token's **key**, and the strength of the match decides how much of that other token's **value** to mix in.
```python
# scores: how much each token attends to every other token
raw     = Q @ K.T
scaled  = raw / sqrt(hidden_dim) # keeps softmax stable
weights = softmax(scaled) # one row per token, sums to 1
attention_output  = weights @ V

```
Here's a visual representaion of the above process:
[IMAGE: 2050927172437905408]
That's the magic. A token decides what context it needs by looking around and pulling in whatever it finds useful. Stack 32 layers of this and you get a model that can track references across thousands of tokens.After attention, each token's vector goes through a small two-layer feed-forward network that does most of the model's actual "knowing." Attention moves information around. The feed-forward network processes it.
## Step 4: Predict the next token
After the final layer, the model takes the vector for the last position, projects it back to vocabulary size, and applies softmax to get a probability over every possible next token. Sample from that distribution, and you have your first generated token.Now we hit the interesting part.
## The two phases nobody tells you about
Generating a 200-token response isn't one task. It's two tasks that look nothing alike under the hood.
[IMAGE: 2050916062749982720]

### Phase 1: Prefill
When you submit a prompt, the model has to process all of your input tokens before it can generate anything. The good news: it can do this in parallel. Every token's Q, K, and V get computed at the same time. Attention runs as a big matrix-by-matrix multiplication.GPUs love this. Matrix-matrix multiplication is what they were built for. The bottleneck here is raw arithmetic throughput: the GPU is pinned at high utilization, doing math as fast as the silicon allows.The metric for this phase is **Time to First Token (TTFT)**. It's the idle time before the first word shows up on your screen.
```python
# Prefill: process the whole prompt in one shot
hidden = embed(prompt_tokens) + positions
for layer in model.layers:
    Q, K, V = project(hidden)             # for ALL tokens at once
    hidden  = attention(Q, K, V) + hidden
    hidden  = feedforward(hidden) + hidden
    cache_kv(layer, K, V)                 # save for later
first_token = sample(project_to_vocab(hidden[-1]))

```

### Phase 2: Decode
Once the first token is out, the model switches modes. To generate token 51, it only needs to compute Q, K, and V for that one token. The previous 50 tokens? Their K and V vectors haven't changed. Recomputing them would be wasted work.
[IMAGE: 2050925588274384896]
So the model loops, one token at a time:
```python
# Decode: one token per iteration
token = first_token
steps = 0
while token != STOP and steps < MAX_STEPS:
    x = embed(token) + position(steps)
    for layer in model.layers:
        q, k, v = project(x)
        K_all, V_all = caches[layer].append(k, v) # cached history + new
        x = layer.forward(q, K_all, V_all, x)  # attention + FFN, residuals
    token = sample(project_to_vocab(x))
    steps += 1
    yield token
```
Notice what changed. Instead of multiplying a matrix of queries against a matrix of keys, you're multiplying a single query vector against a matrix of keys. The arithmetic is tiny.But the GPU still has to load every weight matrix from memory and every cached K and V from memory to do that tiny computation. Suddenly the bottleneck flips. The chip has plenty of compute headroom and is just sitting there waiting for memory to deliver the next chunk of data.This is why **decode is memory-bound, prefill is compute-bound.** Same model, same hardware, totally different performance characteristics.The metric here is **Inter-Token Latency (ITL)**: the gap between consecutive tokens streaming out. Low ITL is what makes a model feel fast.
## The KV cache: the optimization that makes this whole thing viable
That append_to_cache line above is doing all the heavy lifting. Without it, generating a 1,000-token response would mean recomputing attention for the entire growing sequence at every step. Quadratic complexity and it's painfully slow.With it, you save the K and V matrices once and reuse them forever. Here's the rough shape of what's happening:
```python
# One KVCache per transformer layer 
class KVCache:
    def __init__(self):
        self.K = None # all keys seen so far,   shape [tokens, dim]
        self.V = None # all values seen so far, shape [tokens, dim]

    def append(self, k_new, v_new):
        if self.K is None:
            self.K, self.V = k_new, v_new # first token
        else:
            self.K = concat([self.K, k_new], axis=token_axis)
            self.V = concat([self.V, v_new], axis=token_axis)
        return self.K, self.V # full history so far
```
The speedup is huge. Think 5x or more for long generations. But there's a price: the cache lives in GPU memory, and it grows with every token. Every layer keeps its own K and V tensors. For a 13B model, you're looking at roughly 1 MB per token. A 4K-token context burns through 4 GB of VRAM just on the cache.This is why long contexts feel slow and expensive. It's not the model running out of brainpower. It's the cache running out of room.The fixes are creative: quantize the cache to INT8 or INT4, drop tokens outside a sliding window, share K and V across attention heads (grouped-query attention), or page the cache like an operating system pages memory (PagedAttention, the trick behind vLLM).
## Frontier research: shrinking the cache itself
Quantization and paging treat the cache as a fixed cost. DeepSeek's V4 series, previewed in late 2025, takes a more aggressive line: redesign attention so the cache is small from the start.Their hybrid scheme combines two compressed attention variants, one sparse, one dense, both operating on a heavily compressed KV stream. At a one-million-token context, V4-Pro reports around 10% of the cache size and 27% of the per-token compute of its predecessor.The takeaway isn't the specific architecture. It's that the KV cache has become the bottleneck the field is now optimizing the model around. When attention itself is being redesigned to minimize the cache, you know the constraint has shifted.Worth a read if you want to see where long-context inference is heading. The full tech report is here: **DeepSeek-V4 paper**
[IMAGE: 2050883466112483328]

## Quantization: trading bits for speed
Training needs precision. Inference doesn't.Most production deployments run in FP16 or BF16 instead of FP32, which halves memory and roughly doubles throughput on Tensor Cores. Aggressive setups go further, quantizing weights to INT8 or even INT4.The math is straightforward. A 7B-parameter model takes:28 GB at FP3214 GB at FP167 GB at INT83.5 GB at INT4That last number is why you can run a 7B model on a laptop GPU. Methods like GPTQ and AWQ pick per-channel scaling factors so the lossy compression hurts quality as little as possible. Done well, INT4 can land within a percentage point of the original on most benchmarks.
## Putting it all together
Here's the full journey of one prompt, end to end:**Tokenize.** Text becomes integer IDs.**Embed.** IDs become vectors. Position information gets folded in.**Prefill.** Every layer runs over every input token in parallel. Compute-bound. The KV cache gets populated. First output token pops out.**Decode loop.** For each new token: project Q for the new token, attend over the cached K and V, run the feed-forward network, sample. Append the new K and V to the cache. Memory-bound.**Detokenize.** Token IDs get mapped back to characters and streamed to your screen.Modern serving frameworks like vLLM, TensorRT-LLM, and Text Generation Inference wrap this loop with continuous batching (tokens from multiple users get interleaved on the same GPU step), speculative decoding (a small model drafts tokens, the big model verifies), and clever memory management. That's how a single GPU serves dozens of concurrent users.
[IMAGE: 2050929751758700546]

## What this should change about how you think
A few practical takeaways once the picture clicks:**Long prompts are expensive in TTFT, long outputs are expensive in ITL.** They stress different things. Optimize for the one your users actually feel.**Context length isn't free.** Doubling it doesn't just double compute; it bloats the KV cache and starves your batch size.**Quantization is the highest-leverage knob you have.** Going FP16 to INT8 often cuts latency in half with negligible quality loss.**GPU utilization can be misleading.** A model that pegs the GPU during prefill might be at 30% during decode. The fix isn't more compute; it's faster memory or a smaller cache.The transformer architecture gets all the attention, but inference performance lives or dies on the boring stuff. Memory layout. Cache management. Bit widths. The art is squeezing the most from the hardware you've got.Now when someone tells you their model is slow, you'll know which question to ask first: is it slow to start, or slow to stream?
---
If you liked this article, let me know in the comments.It gives me a signal that I should create more content like this.Thanks for reading!Cheers! :)