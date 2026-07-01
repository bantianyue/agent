## 实时推理数据训练 Draft 模型：Baseten 将 Speculative Decoding 接受率提升 20%

Draft 模型（如 EAGLE-3、DFlash）能加速大模型推理，吞吐量提升 2-3 倍，同时降低延迟。但让这些 draft 模型与多样化的 base 模型和动态流量模式保持对齐，是一个不小的工程挑战。

Baseten 构建了一套分布式训练流水线来解决这个问题。它从实时推理中直接提取 hidden states，用这些状态即时训练 draft 模型，无需离线存储数据。

在实际部署中，这套方案将接受率中位数提升了 **20%**，部分受限流量模式的提升甚至超过 **100%**。这些增益直接转化为更强的 speculative decoding 加速比和更高的服务效率。

---

### 传统方法的四大瓶颈

传统训练 draft 模型的方法面临几个痛点：

**1. 存储开销**：将 hidden states 保存下来做离线训练，在生产规模的流量下不可扩展。Kimi K2 的单条样本就可能超过 2GB，而完整的 draft 训练需要数百万条。

**2. 算力瓶颈**：生成 draft 模型输入所需的 hidden states 代价极高，尤其是超长上下文的巨型模型。

**3. 对齐漂移**：对 base 模型做 fine-tuning 或 RL 时，如果不同时重新训练 draft 模型，其接受率往往会下降。

**4. 数据合规**：在零数据保留（ZDR）环境中，存储数据做离线训练几乎不可行。

### 实时训练架构

Baseten 的分布式训练流水线直接使用推理过程中的实时 hidden states 来训练 draft 模型，对 serving 路径增加的开销极小。

这套架构绕过了数据存储需求，缩短了为新 base 模型训练 draft 模型所需的时间，同时让模型能持续适应特定流量模式。

---

## 工程实现：如何做到最小开销

### 推理路径优化：GPU 执行、内存和网络

Baseten 将训练流水线原生构建在 Baseten Inference Stack 中，作为 Speculation Engine 的一部分，运行在已高度优化的同一推理引擎之上。系统需要持续提取训练数据，但不能拖慢推理。

为了不引起延迟尖峰，他们将所有网络通信和数据缓冲卸载到专用的后台进程。配合 overlap scheduler 循环中精细的 CUDA event 同步，系统可以持续提取 hidden states，而不会阻塞主执行线程。

为了节省内存，推理端发送未过滤的迭代数据，接收端再统一聚合。额外空间消耗与 `max_num_tokens_per_iter` 成正比，而非 `max_sequence_length`。这对长上下文推理节省了大量空间。

### 训练路径优化

训练端将数据加载器与核心训练循环完全解耦。流水线使用 mmap-backed 数组将训练数据直接缓冲到 paged memory 中。

与推理端类似，额外的 GPU 和 pinned memory 消耗与 `max_num_tokens_per_iter` 成正比。完整的请求数据不会在 device memory 或 pinned memory 中物化，而是在 pageable memory 中组装，进入训练循环前才做 pin 操作。

### 基础设施方案

Baseten 还分享了几个用于这个项目的关键框架：

- **UCXX**：跨节点传输大型张量需要专门的网络基础设施。他们用 UCXX Python bindings 高效处理异步 RDMA 传输。

- **Trio（结构化并发）**：在几十上百个节点的规模下，硬件故障和抢占是常态。Baseten 用 Trio 构建了重试和恢复路径，将故障隔离在有限范围内，防止部分节点掉线或瞬时网络故障影响推理。另外，他们把 Trio 的 guest loop mode 与 PyTorch 同步点（如 `torch.cuda.synchronize()`）整合，可以在不创建新线程的情况下运行异步循环，从而最小化 GIL 竞争。

---

**一点观察：** Baseten 展示的是一种实用主义思路，不追求完美离线训练，而是用在线数据持续优化。20% 的接受率提升在 spec decode 场景下相当可观，而且天然解决了数据存储和合规问题。

<span style="font-size:12px;color:#888888;">参考：https://x.com/rachelrapp/status/2070493769690910913</span>
