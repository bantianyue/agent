## Data Parallelism

Your browser does not support the audio element.

To add a podcast feeling to your reading experience, feel free to listen to the
NotebookLM hosts discussing the following sections of this book as you're
reading along.

The idea behind data parallelism (DP) is to replicate the model on several GPUs
(we call the replica's “model instances”) and run forward and backward passes on
different micro batches of data in parallel for each GPU, hence the name Data
Parallelism. You've probably already seen Data Parallelism in simple training
examples but as you'll soon see we'll dive quite deeper in this section so stay
tuned even if you know the general approach.

![image.png](/assets/images/dp_diagram.png)

If you are not familiar with distributed communications patterns like broadcast,
gather or all-reduce we put together a small crash course in A0: Parallel
Programming Crash Course.

Using a different micro batch for each GPU means we’ll have different gradients
in each GPU, so to keep the model instances in sync across different GPUs, the
gradients from the model instances will be averaged using an operation called
“all-reduce”, which happens during the backward pass, before the optimizer step.

This involves our first “distributed communication” primitive: _**all-reduce_**
which handles the synchronization and communication between GPU instances and
nodes.

![image.png](/assets/images/dp_overlap1.svg)

A naive DP implementation would just wait for the backward pass the finish so
that we have all gradients, then it triggers an all-reduce over all DP ranks, to
sync these gradients. But such an sequential steps of computation followed by
communication is **A BIG NO!** Because we don’t want our GPUs to stay idle while
communication is happening, like on the above graph.

Instead we should try to overlap communication and computation whenever possible
so that they happen at the same time as much as possible.

Let’s see three optimizations that allow us to do much better than our naive
first implementation!

#### **First optimization:** Overlap gradient synchronization with backward pass

The main drawback of the naive DDP approach we’ve just described is that after
the backward pass (_computation_), we have to wait for gradient synchronization
(_communication_) before updating the parameters. Could we overlap this
communication with our computation? The answer is yes!

As shown in the figure above, the gradients (red boxes) for a layer can be
gathered and summed even before the gradients from earlier layers (red boxes to
the left) have been computed. For example, as soon as the backward pass of the
last layer is complete (last box on the right), those gradients can already be
gathered and summed while the backward computations continue for earlier layers,
moving toward the left.

![image.png](/assets/images/dp_overlap2.svg)

This can be achieved in pytorch by attaching an _all-reduce hook function_ to
each parameter. An all-reduce operation is triggered as soon as the gradient for
that parameter is ready, while gradients for other parameters are still being
computed. This approach overlaps most of the all-reduce operations with gradient
calculations, thereby improving efficiency. Here's a simple function to attach a
hook:

def register_backward_hook(self, hook): """ Registers a backward hook for all
parameters of the model that require gradients. """ for p in
self.module.parameters(): if p.requires_grad is True:
p.register_post_accumulate_grad_hook(hook)

Overlapping computation and communication reduces the time spent waiting for
gradient synchronization across the entire model. Gradient synchronization can
occur (at least partially) in parallel with backward pass, significantly
speeding up data parallelism. Here's a full implementation of naive DP with
synchronization overlap:

👉 Naive DP implementation with overlap in Picotron (Click to expand)

This is our first example of “ _overlapping computation and communication_ ”
which we will discuss several times in this blog post and is an essential
technique to maximal scaling efficiency. But we can improve the efficiency even
further!

#### **Second optimization:** Bucketing gradients

GPU operations are usually more efficient when performed on large tensors rather
than having many operations running on smaller tensors. This is also true for
communication operations. Thus, we can advantageously group gradients into
buckets and launch a single all-reduce for all the gradients within the same
bucket instead of performing independent all-reduce for each gradient. It will
generally look like the following:

![dp_overlap3.svg](/assets/images/dp_overlap3.svg)

Think of it like packing items into boxes before shipping. It's more efficient
to send a few big boxes than many small ones. By performing a single all-reduce
operation for each bucket, we can significantly reduce communication overhead
and speed up the communication operation.

Here's a code implementation with bucketing:

👉 Bucket DP implementation in Picotron (Click to expand)

#### **Third optimization:** Interplay with gradient accumulation

Finally, as we’ve seen before, gradient accumulation works by performing
multiple forward and backward passes before updating the parameters with
`optimizer.step()`. When combining gradient accumulation with data parallelism,
we should be careful when we want to synchronize gradients.

In a naive version, an all-reduce operation is automatically triggered after
each backward pass during the accumulation, which is sub-optimal as a single
reduce after the final step would have the same effect while reducing overhead.

In PyTorch, this is typically solved by adding a [`model.no_sync()`](https://github.com/pytorch/pytorch/blob/5ea67778619c31b13644914deef709199052ee55/torch/nn/parallel/distributed.py#L1408-L1435) decorator, which disables gradient synchronization, on the backward passes which don’t need reduction.

📝 Note

When performing communication operations, tensors must be contiguous in memory
to avoid redundant memory copies. To perform this optimally, we often pre-
allocate continuous buffers of the size of activations or model parameters
specifically for communication. While this speed up communication, it also
contributes in part to the peak memory usage during training.

Now let's have a look what that means for the global batch size.

### Revisit global batch size

We can update our batch size equation with our newly added Data Parallelism and
Gradient Accumulation parameters:

bs = gbs = mbs \times grad\\_acc \times dp

Here grad\\_acc is the number of gradient accumulation steps and dp is the
number of parallel instances used for data parallelism.

Given a targeted global batch size, we can thus trade gradient accumulation
steps for data-parallel processes to speed up training.

In practice, people tend to maximize the number of data-parallel nodes (DP) over
gradient accumulation as much as possible since it's inherently parallel, unlike
the sequential nature of gradient accumulation. Gradient accumulation is then
added on top of data parallelism to achieve the target global batch size when
scaling data parallelism alone is not sufficient before you run out of GPUs.

A good resource for further reading on Data Parallelism is
<https://siboehm.com/articles/22/data-parallel-training>.

Being able to distribute the training over different samples gives us a first
dimension of parallelization, thus making this 1D parallelism (we’ll
progressively cover 4 more dimensions).

### Our journey up to now

Let’s quickly summarize how to setup our first 1D parallel training with a draft
recipe for an optimal data-parallel setup:

  1. We should first determine the best (global) batch size in tokens (`GBST`) either by consulting literature or running experiments measuring model convergence.
  2. We then select a sequence length for training, again by either consulting literature or running experiments. Generally, 2-8k tokens work reliably well for the evaluations we have today (we won’t dive in training recipes here but teams usually increase the sequence at the end of the training, adding some longer-context data samples in the mix to reach the longer context size of today).
  3. We now know the batch size (gbs). We can find the maximum local batch size (mbs) on a single GPU by increasing the local batch size until we run out of memory.
  4. Finally, we determine the number of available GPUs for our target DP. The ratio of GBS to DP gives us the remaining number of gradient accumulation steps needed for the desired GBS. 

For instance DeepSeek and Llama models are trained with a 4k tokens sequence
length during the main pretraining phase.  
  
The reason 2-8k work well for pretraining is that documents that are longer are very rare on the web. See [Harm’s blogpost](https://www.harmdevries.com/post/context-length/) for a detailed analysis.

If the gradient accumulation ratio is lower than one, i.e. we have too many GPUs
a.k.a GPU-rich 🤑 (!), we can either choose to not use all our GPUs, explore a
larger global batch size or test if a lower MBS will speed up training. In the
latter case we’ll end up prioritizing throughput over individual GPU compute
efficiency, using a smaller MBS than possible in order to speed up training.

Time to take a concrete example: Let’s say we want to train a recent model with
a GBS of 4M tokens and a sequence length of 4k. Our batch size will thus be 1024
samples (we pick the closest powers of two). Let's assume we observe that a
single GPU can only fit MBS=2 in memory and we have 128 GPUs available for
training. This means with 4 gradient accumulation steps we’ll achieve our goal
of 1024 samples or 4M tokens per training step. Now what if we suddenly have 512
GPUs available? We can achieve the same GBS and thus identical training by
keeping MBS=2 and setting gradient accumulation steps to 1 and achieve faster
training!

📝 Note

Bear in mind that at the 512+ GPUs scale, depending on the network used, the
communication operations will start to be bound by _ring latency_ (time required
for a signal to propagate once around the ring) which means we can no longer
fully overlap the DP communications. This will decrease our compute efficiency
and hit our throughput. In this case we should start exploring other dimensions
to parallelize on.

While data parallelism nicely overlaps the all-reduce gradient synchronization
with backward computation to save time, this benefit starts to break down at
large scales. Why? Because as we add more and more GPUs (hundreds or thousands),
the overhead of coordinating between them grows significantly and the network
requirements are becoming too large for the benefits. As a result, our setup
will become less and less efficient which each additional GPU we add to the
system.

Lets see this happening in practice with some benchmark:

We see that above some limit, our throughput starts to drop quite significantly
while the memory usage per GPU stays constant and is not affected by adding more
DP ranks.

**Data parallelism was our first (simple) strategy to scale training across more
GPUs. This technique works like gradient accumulation but parallelizes the
forward and backward passes on micro batches, thus increasing throughput!**

The keen reader has already probably noted however that this assumes that we can
fit at least one input sample forward pass (mbs _=1)_ into our GPU memory. This
is not always the case! As we can see, larger models don’t fit into a single
GPU, even with activation recomputation activated:

Tip: you can quickly eyeball the minimal memory required for your model’s
parameters by multiplying by 2 e.g. 70B → 140GB (=133GiB)

We've also seen that Data Parallelism starts to have some limiting communication
overhead above a certain level of scaling. Do we have other options for these
larger models or large batch-size? We do have some solutions thankfully. They
will involve either move some tensors to the CPU or split the
weights/gradients/optimizer-states tensors across GPUs devices! Let's start
diving in them.

There are two main approaches to splitting: parallelism (tensor, context, or
pipeline parallelism) and sharing (DeepSpeed Zero or PyTorch FSDP). Both
approaches are somewhat orthogonal and can actually be combined!

The sharing paradigm is closely related to DP so we’ll have a look at it first
by investigating the ZeRO method!

### ZeRO (**Ze** ro **R** edundancy **O** ptimizer)

In this section we will introduce DeepSpeed ZeRO (**Ze** ro **R** edundancy
**O** ptimizer), a memory optimization technology designed to reduce memory
redundancies in LLM training.

While Data Parallelism is an efficient way to scale training, the naive
replication of optimizer states, gradients, and parameters across each DP rank
introduces a significant memory redundancy. ZeRO eliminates memory redundancy by
partitioning the optimizer states, gradients, and parameters across the data
parallel dimension, while still allowing computation with the full set of
parameters. This sometimes requires more communications between DP ranks which
may or may not be fully overlapped as we’ll see next!

We’ll focus on ZeRO-1 to ZeRO-3 in this blog as it should give a broad view on how it helps reduce memory while showing the tradeoffs to take into account. You can find more ZeRO flavors in the [DeepSpeed docs](https://www.deepspeed.ai/tutorials/zero/).

This approach is organized into three possible optimization stage of ZeRO:

  * ZeRO-1: optimizer state partitioning
  * ZeRO-2: optimizer state + gradient partitioning
  * ZeRO-3 (also called FSDP for “Fully-Sharded Data Parallelism”): optimizer state + gradient + parameter partitioning

When we say partitioning, it means along the DP axis, as ZeRO is part of Data
Parallelism. We’ll see later that we can partition along other axes.

You might be missing the activations among the things we can shard. Since each
DP replica of the model receives a different micro-batch the activations on each
DP rank also differ so they are not duplicated and thus can’t be sharded!

Let’s have a closer look how much we can save with the partitioning of each ZeRO
stage!

#### Memory usage revisited

You likely remember from  our previous section the memory usage of optimizer
states, gradients, and parameters during a standard training. Lets call our
model's parameters count \Psi (previously N but here we use the original ZeRO
paper notation). In Mixed Precision Training (more details in a later section)
with the Adam optimizer, the memory usage for each item we need to store is:

  * Model’s parameters (half precision i.e. bf16/fp16): 2\Psi
  * Model’s gradients (half precision i.e. bf16/fp16): 2\Psi
  * Model’s parameters in fp32 and optimizer states: 4\Psi + (4\Psi + 4\Psi)
  * Model’s gradients in fp32: 4\Psi (optional, only accounted if we want to accumulate grads in fp32)

If we don’t accumulate gradients in fp32 this gives us a total memory
consumption of 2\Psi + 2\Psi + 12\Psi, and if we accumulate it would be 2\Psi +
6\Psi + 12\Psi. Let’s focus for now on the case without fp32 gradient
accumulation for simplicity but you can just add the additional bytes to the
gradient term which are affected by ZeRO-2 and 3.

The idea of ZeRO is to shard these objects across the DP ranks, each node only
storing a slice of the items which are reconstructed when and if needed, thereby
dividing memory usage by the data parallel degree N_d:

![zero_memory.svg](/assets/images/zero_memory.svg)

Here \Psi denotes number of parameters, k denotes the memory multiplier of
optimizer states (k=12 for Adam as we've just seen), and N_d denotes DP degree.

Let’s explain this graph and it’s values by exploring how each ZeRO stage works.
We’ll start with ZeRO-1.

#### ZeRO-1: Partitioning Optimizer States

In vanilla DP, all ranks gather the same gradients after the backward pass and
simultaneously perform identical optimizer steps. This seems like a lot of
duplicated work. Can we avoid it and reduce memory usage at the same time?

In ZeRO-1, the optimizer states are partitioned into N_d equal parts where N_d
is the DP degree. This means that each model replica distributed on each DP rank
only keeps track of \frac{1}{N_d} of the optimizer states. During the
optimization step only \frac{1}{N_d} of the float32 weights are updated.

However during the forward pass, each replica need all the parameters, we thus
need to add an additional **_all-gather_** (the second type of collective
communication primitive we encounter!) after the optimizer step so that each
model replica has the full set of updated weights.

This explains the memory formula of 2\Psi + 2\Psi + \frac{k\Psi}{N_d} that we
saw on the above graph! Here’s a summary of the sequence of operations for a
single training step

  * Forward pass with the same, full set of bf16 parameters on each replica, but different microbatches across replicas
  * Backward pass with the same, full set of gradients on each replica, but different microbatches across replicas
  * Perform an reduce-scatter on the gradients (we'll explain the reduce-scatter primitive in the graph below)
  * Each replica perform an optimizer step on its local optimizer steps (only \frac{1}{N_d} optimizer states) to get updated \frac{1}{N_d} fp32 parameters which can then be converted to \frac{1}{N_d} of the full set of bf16 parameters.
  * Perform an all-gather among the bf16 parameters to send missing slices back to each replica. This is a new operation in ZeRO, and not used in vanilla DP.

Note: reduce-scatter is 2 times faster than all reduce! _Yay, a third
communication primitive!_

You may be wondering what is this "reduce-scatter" operation and how this all
look so lets try to make this more graphical with the figure below. We'll go
over all the steps of a forward/backward pass cycle:

![dp_zero1.gif](/assets/images/dp_zero1.gif)

In terms of practical communications, compared to vanilla DP, Zero-1 change our
"all-reduce" gradient communication to a "reduce-scatter" operation and adds an
all-gather operation over all parameters after the optimizer step. Here is how
it looks:

![dp_zero1_overlap.svg](/assets/images/dp_zero1_overlap.svg)

If you've been following along, you'll recall from vanilla DP that we can
overlap the all-reduce gradient communication with the backward pass
computation. In ZeRO-1, we can also investigate how to efficiently overlap the
newly added all-gather of bf16 parameters. There are two main strategies for
this:

  * During optimizer step: We can initiate the all-gather immediately after the optimizer updates part of the parameters. This allows the communication to potentially overlap with other parameters update.
  * During forward: We can overlap the all-gather of each layer’s parameters with the forward pass.

📝 Note

Unfortunately these techniques are not straightforward to implement and require
sophisticated use of hooks/bucketing. In practice we can just use PyTorch native
ZeRO-3/FSDP implementation and set the FSDPUnit to be the entire model, more
details about this later.

In ZeRO-1 the optimizer states have been partitioned, which means that each
replica only updates \frac{1}{N_d} of the optimizer states. The keen reader must
have noticed that there is no real need to have all gradients on all DP ranks in
the first place as only a subset is needed for the optimization step. Meet
ZeRO-2!

#### ZeRO-2: Adding **Gradient Partitioning**

Since we only need, on each replica, to have the gradient shard corresponding to
the optimizer state shard, it makes sense to shard gradient as well similarly to
the optimizer states. During the backward pass, instead of performing an all-
reduce over the gradients, we only perform a **_reduce-scatter_** operation!
Where we only spread the \frac{1}{N_d} gradients needed in memory, thus saving
more memory compared to ZeRO-1.

In case of FP32 gradient accumulation, we only need to keep \frac{1}{N_d}
fp32_grads where we accumulate the bf16 grads coming from the reduce-scatter.
And in the optimizer step we use the \frac{1}{N_d} fp32_grads.

![dp_zero2.gif](/assets/images/dp_zero2.gif)

It’s easy to see now that sharding the gradients leads to to 2\Psi +
\frac{2\Psi+k\Psi}{N_d} and as N_d is increased we can save up to 8x memory over
the baseline. In terms of communication the same process applies as for ZeRO-1,
with the only difference that we communicate and release on the fly. In total,
ZeRO-2 is thus also equivalent to vanilla DP training w.r.t. communication.

In terms of communication ZeRO-2 is similar to ZeRO-1, they both require a
reduce-scatter for the gradients, and an all-gather over all parameters.

![dp_zero2_overlap.svg](/assets/images/dp_zero2_overlap.svg)

Note: You might notice that there is no real overhead of using ZeRO-2 over
ZeRO-1 and indeed ZeRO-2 is usually the best option.

Now that we’ve sharded gradients as well, are we done or can we keep getting
away with this? Well, sort of. Here comes ZeRO-3!

#### ZeRO-3: Adding **Parameter Partitioning**

For Stage 3 we extend the above approach of sharding optimizer states and
gradients over DP replicas up to sharding the model’s parameters.

📝 Note

This stage is also called FSDP (Fully Shared Data Parallelism) in PyTorch native
implementation. We’ll just refer to ZeRO-3 in this blogpost but you can think of
FSDP wherever you see it.

So how do we do a forward or backward pass in practice if all parts of the model
are distributed? Quite simply we gather them on-demand when we need them. In the
forward pass this looks as follows:

![dp_zero3_fwd.svg](/assets/images/dp_zero3_fwd.svg)

So as we perform the forward pass and sequentially go through the layers we
retrieve the necessary parameters on demand and immediately flush them from
memory when we don't need them anymore. The backward pass works the same way
just inverted in flow and we produce the gradient shards:

![dp_zero3_bwd.svg](/assets/images/dp_zero3_bwd.svg)

The other issue is that we need to do these all-gathers continuously throughout
the forward and backward step, which amounts to 2\cdot \text{num\\_layers} -1
additional all-gathers in **a training step** compared to Zero-2, each comes
with a small **base latency** overhead as we can see in the following figure:

![dp_zero3_overlap.svg](/assets/images/dp_zero3_overlap.svg)

During the forward pass we do all-gather operations for the parameters when we
need them, so a \Psi communication tax. Since we discard the parameters
immediately after we needed them in the forward pass we need one more all-gather
during the backward pass as well incurring another \Psi in communication tax.
Finally we need the same **_reduce-scatter_** as in ZeRO-2 for the gradients
which costs also \Psi in communication and we arrive at a total communication
cost of 3\Psi, compared to 2\Psi for Zero-2.

This may sounds like a lot of communication overhead but it's actually pretty
fine as we can overlap the communication of the parameters for the next layer
with the forward pass of the current layer in what is called **prefetching**.
With prefetching, we will "all-gather" weights for *Layer n+1* while we do the
current forward for _Layer n_ in the forward, and similarly, we will "all-
gather" weights for _Layer n-1_ while doing the backward for _Layer n_. Of
course this overlap only holds true as long as we don’t scale DP too much. (as a
rule of thumb DP shouldn’t exceed 512)

In terms of memory we can see that our equation now reached it’s final form of
\frac{2\Psi +2\Psi+k\Psi}{N_d} which means we can drive memory usage down
indefinitely if we can increase the DP rank, at least for the model related
parameters. Notice how it doesn’t help with the intermediate activations, for
that we can use activation checkpointing and gradient accumulation as we’ve seen
in the previous chapters.

**Let’s summarize our journey into DP and ZeRO so far: we have seen that we can
increase throughput of training significantly with DP, simply scaling training
by adding more model replicas. With ZeRO we can train even models that would
ordinarily not fit into a single GPU by sharding the parameters, gradients and
optimizers states across DP, while incurring a small communications cost.**

If you want to read more about FSDP1, FSDP2 and some of the implementation complexities around them, you should take some time to go over [this nice blog](https://christianjmills.com/posts/mastering-llms-course-notes/conference-talk-012/).

However, there is a limit here, DP only works if a layer of the model fits in a
single GPU and ZeRO can only partition the parameters, gradients, and optimizer
states, but not the activation memory! We recall from the activation memory
discussion that this part of the memory scales with sequence length and batch
size. Naturally we could just limit those, but in practice we don’t want to be
limited by hardware to train with only with a short sequence length.

To overcome this issues, it's time to explore a new, orthogonal axis of
parallelism - Tensor Parallelism (TP). Unlike ZeRO3 which relies on heavy
parameter communication, TP proposes to shard parameters, gradients, optimizer
states AND activations across devices without requiring any communication of
model parameters between GPUs.

What? How is this even possible?! Let's explore this seemingly magical approach
together! 🙂
