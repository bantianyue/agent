# 用 CXL 内存池化打破 AI 内存极限

How Samsung achieved near-DRAM performance while scaling KV Cache capacity for LLM inference.
（三星如何在扩展 LLM 推理 KV Cache 容量的同时，实现接近 DRAM 的性能）

Solving the KV Cache scaling challenge with CXL memory pooling
（用 CXL 内存池化解决 KV Cache 扩展难题）

As generative AI adoption accelerates, the focus of AI infrastructure is shifting beyond training performance. For organizations deploying Large Language Models (LLMs) in production, inference efficiency and scalability have become critical factors in delivering responsive and cost-effective AI services.
随着生成式 AI 的采用加速，AI 基础设施的关注点正从训练性能向外延伸。对于在生产环境中部署大语言模型（LLM）的组织来说，推理的效率与可扩展性已经成为提供响应迅速、成本可控的 AI 服务的关键因素。

One emerging challenge is the rapid growth of KV Cache (Key-Value Cache) requirements. As context lengths increase and the number of concurrent users grows, the memory required for KV cache can quickly exceed available GPU memory and system DRAM resources. This creates a new bottleneck in AI inference infrastructure.
一个正在浮现的挑战是 KV Cache（键值缓存）需求的快速增长。随着上下文长度增加、并发用户数增长，KV cache 所需的内存会迅速超出可用的 GPU 显存与系统 DRAM 资源。这在 AI 推理基础设施中制造了一个新的瓶颈。

To address this challenge, Samsung evaluated CXL-based memory pooling for KV cache offloading, exploring whether it could provide scalable memory expansion while maintaining performance close to that of conventional DRAM.
为应对这一挑战，三星评估了基于 CXL 的内存池化用于 KV cache 卸载，探索它能否在保持接近传统 DRAM 性能的同时，提供可扩展的内存扩展能力。

## Why KV Cache matters（为什么 KV Cache 如此重要）

LLMs rely on KV Cache to store previously computed attention keys and values during inference. By reusing this information instead of recomputing it for every generated token, models can significantly reduce inference latency and computational overhead.
LLM 依赖 KV Cache 来存储推理过程中已计算的注意力键和值。通过复用这些信息，而不是为每个生成的 token 重新计算，模型可以显著降低推理延迟与计算开销。

However, as model sizes, context lengths, and user concurrency continue to grow, KV Cache requirements can easily reach hundreds of gigabytes. Traditional offloading approaches based on SSDs or network-attached memory can alleviate capacity constraints, but often introduce additional latency and bandwidth overhead.
然而，随着模型规模、上下文长度和用户并发度持续增长，KV Cache 需求可以轻松达到数百 GB。基于 SSD 或网络附加内存的传统卸载方案能缓解容量约束，但往往会引入额外的延迟与带宽开销。

## The opportunity of CXL memory pooling（CXL 内存池化的机遇）

Compute Express Link (CXL) is emerging as a key technology for next-generation data center architectures. By enabling memory expansion through a coherent, high-bandwidth interconnect, CXL allows systems to scale beyond the physical limitations of traditional DRAM configurations.
Compute Express Link（CXL）正成为下一代数据中心架构的一项关键技术。通过一致性、高带宽的互连实现内存扩展，CXL 让系统能够突破传统 DRAM 配置的物理限制进行扩展。

When combined with a CXL switch, multiple memory devices can be aggregated into a shared memory pool, enabling flexible memory allocation and significantly increased capacity.
当与 CXL 交换机结合时，多个内存设备可以聚合为一个共享内存池，实现灵活的内存分配与显著提升的容量。

Samsung's CMM-D (CXL Memory Module-DRAM) is designed to enable these memory expansion architectures, offering an attractive solution for memory-intensive workloads such as AI inference.
三星的 CMM-D（CXL 内存模块-DRAM）正是为支持这类内存扩展架构而设计，为 AI 推理等内存密集型负载提供了一个颇具吸引力的方案。

## Evaluating CXL memory for AI inference（为 AI 推理评估 CXL 内存）

The evaluation environment consisted of NVIDIA RTX PRO 6000 Blackwell GPUs, Samsung CMM-D modules connected through a CXL switch and configured as a 1TB CXL memory pool, the vLLM and LMCache software stack, and host-level optimizations based on our techniques.
评估环境由 NVIDIA RTX PRO 6000 Blackwell GPU、通过 CXL 交换机连接并配置为 1TB CXL 内存池的三星 CMM-D 模块、vLLM 与 LMCache 软件栈，以及基于我们自研技术的宿主级优化组成。

The primary question was straightforward: Can a CXL memory pool support large-scale KV Cache offloading while maintaining performance comparable to DRAM?
核心问题直截了当：CXL 内存池能否在支持大规模 KV Cache 卸载的同时，保持与 DRAM 相当的性能？

## Delivering near-DRAM performance at greater scale（在更大规模下交付接近 DRAM 的性能）

The evaluation demonstrated that CXL memory pooling can deliver both near-DRAM performance and substantial memory scalability for AI inference workloads.
评估表明，CXL 内存池化能够为 AI 推理负载同时带来接近 DRAM 的性能与可观的内存可扩展性。

In single-GPU configurations, the optimized CXL memory pool achieved performance comparable to DRAM when used as the LMCache backend. In multi-GPU environments utilizing eight GPUs, the CXL memory pool maintained approximately 92% of DRAM performance while providing significantly greater memory capacity.
在单 GPU 配置下，经优化的 CXL 内存池作为 LMCache 后端使用时，达到了与 DRAM 相当的性能。在采用 8 块 GPU 的多 GPU 环境中，CXL 内存池在提供显著更大内存容量的同时，保持了约 92% 的 DRAM 性能。

The study also compared a 512GB DRAM configuration with a 1TB CXL memory pool under increasing KV Cache demands. As KV Cache requirements exceeded available DRAM capacity, performance degradation occurred due to cache re-computation overhead. In contrast, the CXL memory pool maintained stable performance while accommodating substantially larger KV Cache footprints.
该研究还在不断增长的 KV Cache 需求下，对比了 512GB DRAM 配置与 1TB CXL 内存池。当 KV Cache 需求超出可用 DRAM 容量时，因缓存重算开销出现了性能下降。相比之下，CXL 内存池在容纳大得多的 KV Cache 足迹的同时，保持了稳定的性能。

## The future of memory pooling for AI infrastructure（内存池化在 AI 基础设施中的未来）

Samsung's evaluation shows that CXL-based memory pooling can provide both substantial memory expansion and near-DRAM performance for KV Cache offloading workloads.
三星的评估显示，基于 CXL 的内存池化能够为 KV Cache 卸载负载同时提供大幅的内存扩展与接近 DRAM 的性能。

As the CXL ecosystem continues to mature, memory pooling architectures are expected to become a foundational building block for future AI data centers, enabling more flexible, scalable, and efficient infrastructure deployments.
随着 CXL 生态继续成熟，内存池化架构有望成为未来 AI 数据中心的基石，支撑更灵活、可扩展、高效的基础设施部署。

Learn more（了解更多）

For readers interested in detailed system configurations, optimization techniques, and comprehensive benchmark results, the full white paper provides an in-depth analysis of the evaluation methodology and findings.
对于想了解详细系统配置、优化技术与完整基准测试结果的读者，完整白皮书对评估方法与发现提供了深入分析。

References（参考）

#CXL Memory #KV Cache Offloading #Memory Pooling #CXL #KV Cache #CMM-D #Scalability #TCO
