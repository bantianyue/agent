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

## Tensor Parallelism

Your browser does not support the audio element.

To add a podcast feeling to your reading experience, feel free to listen to the
NotebookLM hosts discussing the following sections of this book as you're
reading along.

So we have sharded the model’s parameters, gradients and optimizers states with
ZeRO but we hit a limit once activation memory overtakes our memory budget.
Welcome Tensor Parallelism (TP), a method which shards weights, gradients, and
optimizers states as well as activations and without the need to gather them all
prior to the computation. Seems like a dream! Let’s first have a look at how
Tensor Parallel works with simple matrix multiplications.

Tensor Parallelism leverages the mathematical properties of matrix
multiplication A \times B. To understand how it works, let's examine two
fundamental equations that make this parallelization possible:

\begin{aligned} &\text{1.} \quad A\cdot B = A \cdot \begin{bmatrix} B_1 & B_2 &
\cdots \end{bmatrix} = \begin{bmatrix} AB_1 & AB_2 & \cdots \end{bmatrix} \\\
&\text{2.} \quad A\cdot B =\begin{bmatrix} A_1 & A_2 & \cdots \end{bmatrix}
\begin{bmatrix} B_1 \\\ B_2 \\\ \vdots \end{bmatrix} = \sum_{i=1}^n A_i B_i
\end{aligned}

This means that we can compute matrix product by either 1) multiplying each
column of B individually or 2) multiplying each row individually and combining
the results. In a neural network, the matrix multiplication is more often
represented in the following format: X \times W, where:

  * X represents the input or activation values
  * W represents the weight of the `nn.Linear`

In practice a small example of the operation looks like this:

![TP diagram](/assets/images/tp_diagram.svg)

Let’s see how we can parallelise this operation! In tensor parallelism, tensors
will be split into N shards along a particular dimension and distributed across
N GPUs. Matrices can be split either on the column part or row part leading to
row and column parallelism. One thing we’ll see in the following is that
choosing row or column sharding will require different communications
primitives.

Our first option is to use column-wise sharding (also called **_column-
linear_**): We'll copy the complete input matrices to each worker, requiring an
operation called **_broadcast_** , and split the weight matrix into columns. The
inputs are then multiplied with the partial weight matrices, and the results are
finally combined using an **_all-gather_** operation.

![image.png](/assets/images/tp_diagram2.png)

Here's the code implementation of column wise tensor parallelism:

👉 Column parallel TP implementation in Picotron (Click to expand)

The second option is called row-wise sharding (also called **_row-linear_**): As
the attentive reader might guess, row-linear means that we split the weight
matrix into chunks of rows. However, this also requires us to split the inputs,
which needs a **_scatter_** operation rather than a broadcast as used in column-
linear sharding. The results on each worker are already in the right shape but
need to be summed for the final result, thus requiring an all-reduce operation
in this scenario.

We see here our fourth distributed primitive: **_scatter_**!

![image.png](/assets/images/tp_diagram3.png)

Here's the implementation for row-wise tensor parallelism:

👉 Row parallel TP implementation in Picotron (Click to expand)

Now that we have the basic building blocks of TP, let's have a look at how we
can effectively combine them inside a transformer layer!

### Tensor Parallelism in a Transformer Block

To come up with a strategy to follow, let’s move from a toy example to a real
model building block. A Transformer model is made of two main building blocks :
Feedforward layers (MLP) and Multi-Head Attention (MHA). We can apply tensor
parallelism to both.

The Feedforward part can be parallelized by having a “Column linear” followed by
a “Row Linear” which amounts to a broadcast to copy the input and an all-reduce
in forward. Note that the broadcast isn’t needed in actual training where we can
make sure inputs are already synced across TP ranks. This setup is more
efficient than starting with "Row Linear" followed by "Column Linear" as we can
skip the intermediate all-reduce between both splitted operations.

![image.png](/assets/images/tp_diagram4.png)

Now that we’ve found an efficient schema for the Feedforward part of the
transformer, let’s take a look at the multi-head attention block (MHA).

We can generally follow a similar approach where Q, K, and V matrices are split in a column-parallel fashion, and the output projection is split along the row dimension. With multi-head attention, the column-parallel approach has a very natural interpretation: each worker computes the attention for an individual or a subset of heads. The same approach works as well for [**_multi-query_** (MQA)](https://arxiv.org/abs/1911.02150) or [**_grouped query attention_** (GQA)](https://arxiv.org/abs/2305.13245) where key and values are shared between queries. 

It's worth noting however that the tensor parallelism degree should not exceed
the number of Q/K/V heads because we need intact heads per TP rank (otherwise we
cannot compute the attentions independently on each GPU and we'll need
additional communication operations). In case we’re using GQA, the TP degree
should actually be smaller than the number of K/V heads. For instance, LLaMA-3
8B has 8 Key/Value heads, so the tensor parallelism degree should advantageously
not exceed 8. If we use TP=16 for this model, we will need to duplicate the K/V
heads on each GPU and make sure they stay in sync.

![image.png](/assets/images/tp_full_diagram.png)

Finally note that Tensor Parallelsim is still not a silver bullet for training.
We’ve added several distributed communication primitive directly in the
computation path of our model which are therefore hard to fully hide/overlap
with computation (like we did in ZeRO), our final performances will be the
results of a tradeoff between the computation and memory gains and the added
communication overhead. Let's illustrate this:

![Forward pass in Tensor Parallelism](/assets/images/tp_overlap.svg)

It's possible to partially hide this communication by performing block matrix
multiplication coupled with async communication/computation.

Looking at the timeline of operations in tensor-parallel MLP (same applies for
Attention), we can better understand the tradeoffs involved. In the forward of
each decoder layer, we hit a synchronization point with the AllReduce operation
that cannot be overlapped with computation. This _exposed communication_
overhead is necessary to combine partial results across tensor-parallel ranks
before the final LayerNorm can be applied.

For example, Megatron-LM/Nanotron implement a partial overlapping of all-gather
with FC1 computation where a portion of the matrix multiplication result will
start to be sent to the other GPU while the other part is still being computed.

Tensor parallelism does help reduce activation memory for the matrix
multiplications since the intermediate activations are sharded across GPUs.
However, we still need to gather the full activations for operations like
LayerNorm, which means we're not getting the full memory benefits we could.
Additionally, TP introduces significant communication requirements that heavily
depend on the network infrastructure. The inability to fully hide this
particular AllReduce behind computation means it directly adds to the critical
path of forward propagation.

This area of research is still an active area of research, with recent work like
Domino  exploring novel techniques to maximize this overlap.

Let's take a better look at the trade-off as we scale the TP degree:

While increasing TP leads to reduced per-GPU throughput (left), it enables
processing of larger batch sizes (right), illustrating the trade-off between
computational efficiency and memory availability in distributed training.

In practice and as we see above on the left plot, the communication overhead of
tensor parallelism becomes particularly noticeable as we scale beyond 8 GPUs.
While tensor parallelism within a single node can leverage fast NVLink
interconnects, going across nodes requires slower network connections. We
observe significant drops when moving from TP=8 to TP=16, and an even steeper
decline from TP=16 to TP=32. At higher degrees of parallelism, the communication
overhead becomes so high that it quickly dominates the computation time.

This being said, tensor parallelism provides important benefits for memory usage
by distributing model parameters, gradients, optimizer states and activations
(to some extent) across GPUs. Let's examine this effect on a 70B parameter
model:

Increasing tensor parallelism reduces the memory needed for model parameters,
gradients and optimizer states on each GPU to the point where we can start
fitting a large model on a single node of 8 GPUs.

Is there a way to get even more benefits from this technique? We've seen that
layer normalization and dropout still require gathering the full activations on
each GPU, partially negating the memory savings. We can do better by finding
ways to parallelize these remaining operations as well.

📝 Note

One interesting note about layer normalization in tensor parallel training -
since each TP rank sees the same activations after the all-gather, the layer
norm weights don't actually need an all-reduce to sync their gradients after the
backward pass. They naturally stay in sync across ranks. However, for dropout
operations, we must make sure to sync the random seed across TP ranks to
maintain deterministic behavior.

Let's explore next a small and natural extension to tensor parallelism, called
**Sequence Parallelism** which does exactly that.

### Sequence Parallelism

**Sequence parallelism (SP)** involves splitting the activations and
computations for the parts of the model not handled by tensor parallelism (TP)
such as Dropout and LayerNorm, but along the input sequence dimension rather
than across hidden dimension.

📝 Note

The term Sequence Parallelism is a bit overloaded: the Sequence Parallelism in
this section is tightly coupled to Tensor Parallelism and applies to dropout and
layer norm operation. However, when we will move to longer sequences the
attention computation will become a bottleneck, which calls for techniques such
as Ring-Attention, which are sometimes also called _Sequence Parallelism_ but
we’ll refer to them as _Context Parallelism_ to differentiate the two
approaches. So each time you see sequence parallelism, remember that it is used
together with tensor parallelism (in contrast to context parallelism, which can
be used independently).

This is needed because these operations require access to the full hidden
dimension to compute correctly. For example, LayerNorm needs the full hidden
dimension to compute mean and variance:

\text{LayerNorm}(x) = \gamma \cdot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} +
\beta

where \mu = \text{mean}(x) and \sigma^2 = \text{var}(x) are computed across
hidden dimension h.

So even though these operations are computationally cheap, they still require
significant activation memory since they need the complete hidden dimension. SP
allows us to shard this **memory** burden across GPUs by splitting along the
sequence dimension instead.

In practice we’ll go from the left diagram to the right:

![ in forward: f = no-op ; f* = all-reduce ; g = all-gather ; g* = reduce-
scatter

            in backward: f = all-reduce ; f* = no-op ; g = reduce-scatter ; g* = all-gather
           SP region needs full hidden_dim](/assets/images/tp_sp_diagram.png)

The diagram shows how we transition between tensor-parallel and sequence-
parallel regions using different collective operations (labeled "f" and "g").
The key challenge is managing these transitions efficiently while keeping memory
usage low and maintaining correctness.

In the forward pass:

  * "f" is a no-op (no operation) because activations are already duplicated across ranks
  * "f*" is an all-reduce to synchronize activations and ensure correctness

In the backward pass:

  * "f*" is a no-op because gradients are already duplicated across ranks
  * "f" is an all-reduce to synchronize gradients

These operations "f" and "f*" are called **conjugate** pairs because they
complement each other - when one is a no-op in forward, the other is an all-
reduce in backward, and vice versa.

For sequence parallelism (SP), we use different operations labeled "g" and "g*".
Specifically, we avoid using all-reduce in the SP region since that would
require gathering the full activations and increase our peak memory usage,
defeating the purpose of SP.

So what is actually happening here? As a famous LLM would say, let’s take it
step-by-step:

**Initial LayerNorm (SP Region)**

  * Input tensors X1 _and X2_ (b,s/2,h) enter LayerNorm, already split across sequence dimension
  * Each GPU computes LayerNorm independently on its sequence chunk and give Y1 _and Y2_

**First Transition (SP → TP)**

  * "g" operation (all-gather) combines Y1 _and Y2_ back to full sequence length
  * Restores Y (b,s,h) since column linear needs full hidden dimension h

**First Linear (TP Region)**

  * A1 is a column-linear, so it splits Y along the hidden dimension
  * GeLU is applied independently on each GPU
  * Z1* is (b,s,h/2)

**Second Linear (TP Region)**

  * B1 is a row-linear, so it restores the hidden dimension
  * W1 is (b,s,h)

**Final Transition (TP → SP)**

  * "g*" operation (reduce-scatter) which reduces for previous row-linear correctness while scattering along sequence dimension
  * W1* is (b,s/2,h)

![image.png](/assets/images/tp_sp_diagram_zoomed.png)

A key advantage of sequence parallelism is that it reduces the maximum
activation size we need to store. In tensor parallelism alone, we had to store
activations of shape (b,s,h) at various points. However, with sequence
parallelism, the maximum activation size is reduced to \frac{b \cdot s \cdot
h}{tp} since we always either split along the sequence or hidden dimensions.

It’s a bit difficult to keep track of all the parts that are sharded differently
in TP and TP/SP - believe us, we find it hard to map as well so we made this
small table to summarize how the activations (aka `hidden_states` ) shape change
across hidden dimension h and sequence dimension s during a forward pass:

Region | TP only | TP with SP  
---|---|---  
Enter TP (Column Linear) | h: sharded (weight_out is sharded)  
s: full | h: sharded (weight_out is sharded)  
s: **all-gather** to full  
TP Region | h: sharded  
s: full | h: sharded  
s: full  
Exit TP (Row Linear) | h: full (weight_out is full + **all-reduce** for correctness)  
s: full | h: full (weight_out is full + **reduce-scatter** for correctness)  
s: **reduce-scatter** to sharded  
SP Region | h: full  
s: full | h: full  
s: sharded  
  
And for the embedding layer:

Region | Vanilla TP | TP with SP  
---|---|---  
Embedding Layer (Row Linear sharded on vocab) | h: full (weight_out is full + **all-reduce** for correctness)  
s: full | h: full (weight_out is full + **reduce-scatter** for correctness)  
s: **reduce-scatter** to sharded  
  
By using sequence parallelism, we can achieve even greater activation memory
savings, allowing us to push our batch size and sequence length further than
what would be possible with tensor parallelism alone. Let's see what that means
for our previous 70B model example:

As we can see, we've again strongly reduced the maximum memory usage per GPU,
allowing us to fit sequence lengths of 16k tokens with TP/SP=16, an improvement
over the vanilla TP case! (TP=16 is still a bit large as we've seen in the
previous section, but we'll see how we can improve this in the next section).

One question you may be asking yourself is whether using TP+SP incurs more
communication than vanilla TP? Well, yes and no. In the forward pass of a
vanilla TP we had two all-reduce per transformer block, and in SP we have two
all-gather and two reduce-scatter per transformer block. So SP does twice the
number of communication operations as TP. But since an all-reduce operation can
be broken down into to an all-gather + reduce-scatter (see the A quick focus on
Ring AllReduce section in the appendix) they’re actually equivalent in terms of
communication. Same reasoning for backward as we just use the conjugate of each
operation (no-op ↔ allreduce and allgather ↔ reducescatter).

If you’ve been paying close attention, you’ll notice that we’re talking about 4
comms ops in each layer (2 for Attention and 2 for MLP). This is how the MLP
profiling looks like when using Tensor + Sequence Parallelism:

![tp_sp_overlap.svg](/assets/images/tp_sp_overlap.svg)

Just like vanilla TP, TP+SP can’t easily be overlapped with compute, which makes
throughput heavily dependent on the communication bandwidth. Here again, like
vanilla TO, TP+SP is usually done only within a node (keeping the TP degree
under the number of GPU per nodes, e.g. TP≤8).

We can benchmark how this communication overhead becomes increasingly
problematic as we scale up tensor parallelism. Let’s measure the throughput and
memory utilization as we scale TP with SP for a 3B model with 4096 seqlen:

Here again, there's a trade-off between computational efficiency (left) and
memory capacity (right). While higher parallelism degrees enable processing of
significantly larger batch sizes by reducing the activation memory, they also
reduce per-GPU throughput, in particular above a threshold corresponding to the
number of GPUs per node.

Let’s summarize our observations:

  * for both methods we notice the biggest performance drop when we move from TP=8 to TP=16, because that’s when we move from only communicating within a single node (NVLink), to communicating inter-nodes (EFA)
  * the memory savings in activations when using TP with SP helps us fit far bigger batches than TP alone

**We have seen how TP helps us shard activations across several GPUs by
splitting the attention and feedforward operations along the hidden dimension
and how SP is a natural complement for the remaining operations by splitting
along the sequence dimension.**

📝 Note

Since LayerNorms in the SP region operate on different portions of the sequence,
their gradients will differ across TP ranks. To ensure the weights stay
synchronized, we need to all-reduce their gradients during the backward pass,
similar to how DP ensures weights stay in sync. This is however a small
communication overhead since LayerNorm has relatively few parameters.

However, there are two limits to TP and SP: 1) if we scale the sequence length
the activation memory will still blow up in the TP region and 2) if the model is
too big to fit with TP=8 then we will see a massive slow-down due to the inter-
node connectivity.

We can tackle problem 1) with Context parallelism and problem 2) with Pipeline
parallelism. Let’s first have a look at Context parallelism!

## Context Parallelism

With Tensor Parallelism and Sequence Parallelism, we can reduce the memory
requirements per GPU significantly as both model weights and activations are
distributed across GPUs. However, when training models on longer and longer
sequences (e.g. when scaling to 128k or more tokens per sequence) we might still
exceed the memory available on a single node as we still have to process a full
sequence length when we're inside the TP region.

Moreover, even if we use full recomputation of the activations (which comes at a
heavy compute overhead of ~30%), we still need to hold in memory some
activations at the layer boundaries which scale linearly with sequence length.
Let's take a look and see how Context Parallelism can help us:

The core idea of Context Parrallelism is to apply a similar idea to the Sequence
Parallelism approach (aka to split along the sequence length) but to the modules
where we already apply Tensor Parallelism. We will thus split these modules
along two dimensions, thereby also reducing the effect of sequence length. You
will find this approach quite intuitive after all we’ve already convered but...
there is a trick to it so stay awake!

For Context Parallelism; just like Sequence Parallelism, we’ll split the input
along the sequence dimension but we now apply this splitting along the full
model, instead of only the sequence parallel regions of the model as we’ve done
previous with Tensor + Sequence Parallelism.

Splitting the sequence doesn't affect most modules like MLP and LayerNorm, where
each token is processed independently. It also doesn’t require expensive
communication like TP, as only the inputs are split and not the weight matrices.
Just like data parallelism, after computing the gradients, an all-reduce
operation is initiated to synchronize the gradients across the context
parallelism group.

There is one important exception though as we we need to pay particular
attention to the **Attention blocks** (haha.. pun intended :D). In the attention
module each token needs to access key/value pairs from **all** other sequence
tokens or in the case of causal attention at least attends to each previous
token.

Because Context Parallelism splits the inputs along the sequence dimension
across GPUs, the attention module will require full communication between GPUs
to exchange the necessary key/value data.

That sounds very expensive if we do it naively. Is there a way to do this rather
efficiently and fast! Thankfully there is: a core technique to handle this
communication of key/value pairs efficiently is called _Ring Attention_.

📝 Note

Context Parallelism shares some conceptual similarities with Flash Attention
(see later for more details) - both techniques rely on online softmax
computation to reduce memory usage. While Flash Attention focuses on optimizing
the attention computation itself on a single GPU, Context Parallelism achieves
memory reduction by distributing the sequence across multiple GPUs.

### Discovering Ring Attention

In this implementation of the attention mechanism, each GPU first initiates an
asynchronous communication operation to send its key/value pairs to other GPUs.
While waiting for the other GPUs data, it computes the attention score for the
portion of the data it already has in memory. Ideally, a next key/value pair is
received from another GPU before this computation finishes, allowing the GPU to
start the next round of computation immediately after it finishes its first
computation.

Let's illustrate this. We'll suppose we have 4 GPUs and an input of 4 tokens.
Initially, the input sequence is split evenly along the sequence dimension, so
each GPU will have just one token along with its corresponding Q/K/V values.
Leyt's say Q1, K1, and V1 represent the query, key, and value of the first
token, which are located on the 1st GPU. The attention calculation will take 4
time steps to complete. At each time step, each GPU performs these three
successive operations:

  1. Send “current keys and values” to the next machine except during the last time step in a non-blocking manner so we can starts the following step before this step is finished
  2. Locally compute the attention score on the “current keys and values” it already has, which typically involves performing Softmax(\frac{QK^T}{\sqrt{d}}) * V.
  3. Wait to receive keys and values from the previous GPU and then circle back to step 1. where “current keys and values” are now the key/values just received from the previous GPU.

We perform these 3 steps four times to complete the attention calculation.

The whole process with 4 GPUs is shown in the following animation:

![ring-attention.gif](/assets/images/ring-attention.gif)

It's probably obvious to you on this animation why the authors chose to call
this approach Ring Attention.

There is one big problem though which is that a naive implementation of Ring
Attention lead to some strong imbalance between GPU coming from the shape of the
causal attention matrix. Let’s take a look at the SoftMax computation by
considering the attention score matrix with the causal attention mask:

![cp_attnmask.svg](/assets/images/cp_attnmask.svg)

The SoftMax is computed row-wise, which means whenever a GPU has received all
the tokens of a row it can be computed. We see that GPU1 can immediately compute
it as it starts with tokens 1-4 and GPU1 actually doesn’t need to receive any
information from any other GPUs. However, GPU2 will need to wait for the second
round to also receive 1-4 and thus have all values for tokens 1-8. Also, GPU1
seems to perform much less work than all the other GPUs.

Let’s see if we can balance our computations better:

### Zig-Zag Ring Attention – A Balanced Compute Implementation

We need a better way to distribute the input sequences. This can be achieved by
assigning the tokens not purely sequential to the GPUs but by mixing the
ordering a bit such that we have a good mix of early and late tokens on each
GPU. This approach is called Zig-Zag attention and in this new arrangement, the
attention mask will show an even distribution of computation but if you count
the number of colored squares, you’ll see that the computation is now balanced
across all GPUs.

![cp_zigzagmask.svg](/assets/images/cp_zigzagmask.svg)

At the same time we’ll also see that in order to complete all rows, each GPU
will need information from all the other GPUs.

We have two general ways to overlap computation and communication, either by
performing a general all-gather, regrouping all the KV on each GPUs at the same
time (in a Zero-3 type of way) or we gather them one-by-one from each GPU to
each GPU as needed:

![cp_overlap_allgather.svg](/assets/images/cp_overlap_allgather.svg)

![cp_overlap_all2all.svg](/assets/images/cp_overlap_all2all.svg)

The key difference between these two implementations lies in their communication
patterns and memory usage:

**1\. AllGather Implementation:**

  * All GPUs simultaneously gather the complete key/value pairs from all other GPUs
  * Requires more temporary memory as each GPU needs to store the full KV pairs at once
  * Communication happens in one step but with larger memory overhead

**2\. All-to-All (Ring) Implementation:**

  * GPUs exchange KV pairs in a ring-like pattern, one chunk at a time
  * More memory efficient as each GPU only needs to store one additional chunk temporarily
  * Communication is spread out and overlapped with computation, though with some additional base latency overhead from multiple communication steps

The All-to-All approach generally offers better memory efficiency at the cost of
slightly more complex communication patterns, while the AllGather approach is
simpler but requires more temporary memory during the attention computation.

We've now seen how we can split a model across one node with TP to tame large
models and that we can use CP to tame the activation explosion with long
sequences.

However, we still know that TP doesn't scale well across nodes, so what can we
do if the model weights don't easily fit on 1 node? Here come another degree of
parallelism, our forth one, called **Pipeline Parallelism** , to the rescue!
