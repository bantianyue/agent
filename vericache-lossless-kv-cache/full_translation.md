# VeriCache: Turning Lossy KV Cache into Lossless LLM Inference

## Abstract

KV Cache 的大尺寸已成为服务长上下文 LLM 的主要瓶颈。许多 KV Cache 压缩方法（token dropping、量化）被提出，但它们本质上都是有损的——尽管短输出的精度下降很小，但随着更多 token 被解码，输出与全量 KV 的偏差越来越大，这会导致代码生成和工具调用中的灾难性失败。

我们提出 VeriCache，第一个确保与全量 KV 解码输出相同、但大体保留了多种 KV Cache 压缩算法高解码吞吐的推理框架。VeriCache 使用压缩 KV Cache 来 Draft token，然后针对全量 KV Cache 验证它们。这看似只是投机解码，但 VeriCache 需要解决一个关键的系统挑战——让全量 KV Cache 不出现在 GPU 内存中，并最小化将其换入做验证的开销。洞察有两方面：(1) 压缩 KV 解码可以与全量 KV 换入并行化，因为一个是 HBM 带宽瓶颈，另一个是 PCIe/网络瓶颈；(2) 压缩 KV Cache 通常产生与全量 KV Cache 相似的输出，允许长 Draft 视野来摊销每次全量 KV 换入的成本。

VeriCache 同时适用于长上下文解码和远程前缀缓存，通过统一的 Compressor Interface 支持 token-dropping 和量化方法的广泛族系，并可与传统投机解码组合。实验表明，VeriCache 在产生相同输出的情况下，实现的吞吐最高可达全量 KV 推理的 4 倍。

## 1. Introduction

最先进 LLM 的上下文长度已超过百万 token。这个增长驱动了许多应用——从仓库级别代码生成、多文档推理到具有长交互历史的 Agent 工作流。

KV Cache 的性能影响体现在单请求和多请求两个维度。在单请求内，每个解码步骤必须从 GPU HBM 读取整个 KV Cache。此外，KV Cache 的大小降低请求吞吐。在跨请求层面，KV Cache 复用很常见，但大 KV Cache 从存储加载到 GPU 的时间可能主导请求延迟。

越来越多的工作通过压缩 KV Cache 来解决这些问题——丢弃 token 或降低精度。两者都带来了显著的效率提升，2-5× 的内存或传输大小减少。

然而，压缩改变了 KV Cache 的内容，导致推理输出偏离全量 KV 的分布。偏差概率随输出 token 增加而累积。对编码和工具调用基准，即使在中等压缩比下，功能准确率也会急剧下降。

这创造了一个二分法：接受有损 KV 并冒输出质量风险，或使用全量 KV 但吞吐低得多。我们提出问题：能否在不影响 LLM 输出的情况下，利用 KV Cache 压缩的吞吐优势？

本文提出 VeriCache，一种受投机解码启发的新推理方案。VeriCache 不直接从压缩 KV Cache 提供 token，而是用它来 Draft token，然后针对全量 KV 验证它们。错误的 token 被纠正，因此最终输出与全量 KV 推理完全相同。

直接应用投机解码不够——token 验证开销可能导致吞吐下降。VeriCache 利用一个关键特性：在 VeriCache 中 Draft 和验证使用完全相同的模型和权重，这与传统投机解码不同。

第一，交叉资源交错。Draft 逐 token 解码，使用 GPU 内存中的压缩 KV，是 GPU 内存带宽密集型。验证需要从次级存储加载全量 KV 到 GPU 并并行验证多个 token，瓶颈在互联带宽和 GPU 算力。将 Draft 和验证分布在不同的硬件资源上，比传统 lock-step 调度利用率更高。

第二，扩展验证周期。VeriCache 的压缩 KV Draft 方案比传统小模型 Draft 方案维持更长接受周期——每轮 25-40 个 vs 只有 2-3 个。

VeriCache 处理长上下文解码和远程前缀缓存，运行时调度器适应硬件和工作负载条件。

与 MagicDec、QuantSpec、SparseSpec 等的区别：先前方案都将全量 KV 保留在 GPU 内存中，限制了压缩的吞吐增益。VeriCache 将 HBM 专门用于压缩 KV，仅在验证时从 host DRAM 重载全量 KV。VeriCache 通过统一 Compressor Interface 支持 7 种现有方法。

VeriCache 基于 vLLM 和 LMCache，实现最高达全量 KV 推理 4 倍的吞吐。

## 2. Background

### 2.1 KV Cache 瓶颈
KV Cache 随上下文长度带来 O(n) 的内存开销和带宽开销。在 Qwen-32B (约64GB权重) 单 H100 80GB GPU 上：2K token 上下文每请求约0.3GB KV，可 batch 约50个请求；100K token 增长到约15GB KV，batch 缩小到 1。

跨请求：长上下文工作负载共享长前缀，但加载预计算 KV 缓存可能成为新瓶颈。从 S3 加载 Qwen-32B 的预计算 KV：10K 上下文约 0.5s，100K 上下文约 5s。

### 2.2 KV Cache 压缩技术
Token dropping 改变 cache 形状；KV quantization 降低每个元素的精度。代表方法包括 H2O、StreamingLLM、KVzip、FastKVzip、KVQuant、KIVI、TurboQuant 等。这些方法本质上都是有损的。

## 3. Motivation: 有损 KV 方法为何失败

### 3.1 语义相似性 ≠ 功能正确性
F1 等 token 级指标对小偏差宽容，但代码生成和工具调用要求精确语法和语义。KVzip 4× 压缩下 F1 仍 > 75%，但代码格式准确率跌到 0%，函数调用准确率 < 10%。

### 3.2 根因：逐 token 偏差积累
压缩 KV 改变了每层注意力权重，用 p_lossy 替代 p_full。与采样噪音不同，这是系统性偏差。每步 KL 约 0.023 nats，250 步后累积到约 6 nats，压缩模型生成全量 KV 输出的概率只有 0.25%。每步 2% 差距放大为 400× 的不匹配。

## 4. KV Cache Verification

### 4.1 概述
VeriCache 将任何有损压缩方法重新用作投机执行层：Draft（用 KV_comp 生成 x 个候选 token）→ Verify（用 KV_full 并行前向传播）→ Accept（从第一个不匹配位置接受并纠正）。

验证需要三大资源：(1) 互联带宽加载全量 KV，(2) GPU HBM 容纳它，(3) GPU 算力做前向传播。

### 4.2 P1: 交叉资源交错
传统 lock-step：所有 Draft x 轮，然后所有验证。VeriCache 打散验证请求，混入 Draft 轮次。Draft 是 HBM 带宽瓶颈，Verify 是 PCIe/算力瓶颈，两者互补。

**长上下文解码**：KV_comp 在 GPU HBM，KV_full 在 CPU 内存。每次验证从 CPU 通过 PCIe 重载到 GPU。单次验证传输约 80ms，打散到每 3 轮插入一次，可与 Draft 计算完全重叠。

**远程前缀缓存**：远端 GPU 用压缩 KV 做 Draft（通过慢链路 BW_l 流式传输），近端 GPU 加载 KV_full（快链路 BW_h）做验证。天然解耦。

### 4.3 P2: 高接受率摊销验证
VeriCache 的接受率在 Draft 长度 30 时仍高于 0.8，接受长度约 19-23 个 token。传统方案只有 2-3 个。与 Eagle 组合后理想加速比达 4.35×。

## 5. VeriCache Runtime

包含资源模型（BW ring 追踪互联带宽，HBM ring 追踪 GPU 内存），请求准入和执行循环，以及调度器如何搜索可行验证时机。

## 6. Compressor Interface

统一接口：任何 token-dropping 或量化方法只要实现该接口就能接入 VeriCache。支持 KVzip、KIVI、KVQuant、TurboQuant、FastKVzip、KVzap、RotateKV 等 7 种以上方法。

## 7. Implementation

基于 vLLM（调度/内存管理）和 LMCache（KV 缓存层）实现，约 5900 行代码。

## 8. Results

### 8.1 评估设置
三模型：Qwen2.5-32B-Coder-1M、Llama-3.1-70B-Instruct-1M、Mistral-Small-24B-Instruct-2501。两个 Pipeline。基准线包括 Full KV、KVzip 4× 压缩、Eagle、SparseSpec、传统投机解码。

### 8.2 与全量 KV 和传统投机解码对比
长上下文解码：VeriCache 在 Llama-70B 上 1.92×-2.73×（256 vs 102 tok/s），Qwen-32B 上最高 4.26×（叠加 Eagle）。
远程前缀缓存：1.33×-2.11×（Llama-70B 485 vs 240 tok/s）。

### 8.3 与有损 KV 对比
VeriCache 的 KL 保持在 0.01 nats 以下，有损方案 14+ nats。函数调用准确率：VeriCache 保持全量 KV 准确率，KVzip 在同样吞吐下下降约 30 个百分点。

## 9. Related Work

三类相关工作：KV Cache 压缩、投机解码、Prefill-Decode 分离架构。

## 11. Conclusion

VeriCache 证明：有损 KV Cache 压缩可以作为无损 LLM 推理引擎的驱动。它将任何压缩方法转化为投机执行层，利用交叉资源交错和长验证窗口，在保持 100% 输出一致性的同时，在长上下文解码上达到 4×、远程前缀缓存上达到 2× 的吞吐。
