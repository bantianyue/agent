# A4Q: Attention With 4-bit Q — Blackwell 消费级 GPU 的原生 NVFP4 Attention Kernel

## TL;DR

Attention With 4-bit Q (A4Q) 是一个用于 sm120/sm121 的新 kernel，将作为贡献提交给 vLLM（待一些社区工作先落板）。

## 为什么做这个？

NVIDIA 为 TensorRT-LLM 预编译了 13,453 个 attention kernel，但这些大多是为数据中心构型编译的（sm100a、sm100f、sm103a）。在 RTX 5090、RTX PRO 6000 或 DGX Spark 上，没有你的架构目录。消费级 Blackwell 需要自己的 attention 路径——这就是 A4Q 要填补的空白。

当前，在 sm120/121 上，4-bit KV cache 通过一个 fp16 转换链解包，每次 tensor-core 操作要烧约 9 条指令。现有的 fp4 路径上，prefill attention 比纯 bf16 attention 慢 1.8 倍——你读了四分之一的数据，却花了近两倍的时间。

## A4Q 做了什么

新的 A4Q kernel 直接在消费级 Blackwell 的 block-scaled fp4 MMA 上运行 QKᵀ：从缓存直出，零反量化，整个 Gemma 家族都可受益。

## 关键结果

**实测收益——在宽 KV 模型上**：
- Gemma-4-26B-A4B：100k context 下 decode 加速 **2.01×**
- Gemma-4-31B：100k context 下 decode 加速 **1.44×**
- 均运行在 DGX Spark 上，NVFP4 KV 双端，batch-1 steady state

**KV 宽度法则**：端到端收益完美按 KV 宽度（num_kv_heads × head_dim）排序：
- ≥4096 → 胜出（两个 Gemma-4）
- ≤1024 → 不显著（Nemotron Mamba 混合、Qwen 线性注意力混合）

**kernel 层面**：QKᵀ kernel 比现行 fp4 路径快 8.9×（100k 时 12×），胜过 bf16——但这是在宽 KV（16 heads）下测得的。端到端收益只在 attention 是 step 的实质开销且 heads 很宽时才体现。

**正确性与内存**：六个模型（Gemma-4、Nemotron-3、两个 Qwen）以 NVFP4 权重复 + NVFP4 KV 运行时，passkey 12/12，GSM8K 持平，每个模型都获得 4× KV 内存节省（更多 context 能塞下）。

**算术精度**：QK 路径与反量化参考在 max_abs_diff = 0.0 上完全一致。唯一的近似来自将 Q 量化到 4-bit——模型层面完全无法察觉。

## 构建过程

Jetha Chan 用 AI 构建了整个项目。Claude Fable 负责分析、规划和 kill criteria 设计；Claude Opus 4.8 负责工程：kernel 和手写 PTX、CUDA 量化器、反汇编、评估电池、认证。GPT 5.5（Codex 中）正在将 A4Q 移植到 llama.cpp。

从带宽研究、质量探测、单元测试、kernel、CUDA 量化器、vLLM 接线到端到端评估——**一天内完成，GPU 租用费 $5.34**。

## 技术细节

### 问题根源：消费级 Blackwell 缺少 QMUL4 指令

NVIDIA 的数据中心 Blackwell (sm100) fp4-KV attention kernel 使用一条叫做 QMUL4 的指令做反量化——四个 e2m1 值 × 一个广播 fp8 scale，产生四个 fp8 值，一条指令搞定。但在消费级 Blackwell (sm120/121) 上：
- QMUL4 指令不存在
- 编译器发出三条指令的转换链：fp4→fp16 转换，fp16→bf16 转换，然后乘法应用 block scale
- 大约每两个值 3 条指令，加上一堆 nibble 洗牌
- 约 9 条非 MMA 指令对应每一条 MMA 指令——kernel 90% 的时间在做算术杂务

### NVIDIA 给的"一个奇招"

消费级 Blackwell 有一个相关硬件：`mma.sync with kind::mxf4nvf4.block_scale`。这是一个 tensor-core 矩阵乘法，两个操作数都是 fp4，硬件沿 reduction 维度每 16 个值应用一个 fp8 scale 因子，累加在 fp32 中。

NVFP4 cache 格式正是：fp4 值，每 16 个元素沿 head 维度放一个 fp8 scale。对于 QKᵀ，reduction 维度就是 head 维度——cache 格式和 MMA 的 scale 布局完美对齐。K 可以从 cache 字节直接进入 tensor core，无需任何反量化指令。

### 质量门控：上线前的两次检查

第一关：确认问题不是带宽瓶颈。实测：Gemma-27B 在 RTX PRO 6000 上 bf16 attention 达到 ~1,600 GB/s 有效 cache 带宽，fp4 kernel 在 batch 1 只达到了 11%。不是 memory bound——是淹死在转换指令中。

第二关：质量检查。Claude 捕获了真实 Gemma-3-27B 服务中的 Q/K/V 激活（全部 62 层），测量了 per-16-block fp4 Q 在已运行 fp4 K 基础上的影响。结果：几乎没有影响。K 量化是主导误差项，Q 的平均 argmax 一致性变化约 -0.012，全局 attention 层（实际承载长上下文的层）仅 -0.005。

### A4Q 的实现

A4Q 替换了一个函数：`compute_qk` 不再将 fp4 通过转换链扩展为 bf16 MMA，而是将相同的共享内存字节直接送入 block-scaled MMA。Q 从一个小的量化 kernel 预打包到达（每行一个 warp，8k context 下 43 微秒——不到 attention 时间的 2%）。

手写 PTX MMA 的 per-thread fragment layout 和 scale-factor register mapping 一次通过——Claude 从 CUTLASS atom 中复制了精确布局，在 100 行的独立单元测试中验证，再触及真实 kernel。

单元测试返回 bit-exact，集成 kernel 也一样：在反量化输入上对比 reference 得出 max_abs_diff = 0.0。

## 模型兼容性

六个模型在 NVFP4 中的表现：

| 模型 | attention 几何 | passkey | GSM8K (A4Q on) | GSM8K (A4Q off) |
|------|---------------|---------|----------------|-----------------|
| Gemma-4-26B-A4B | MoE, 512-wide VO-split | 12/12 | 0.973 | 0.980 |
| Gemma-4-31B-IT | dense, 512-wide VO-split | 12/12 | 0.987 | 0.987 |
| Nemotron-3-Nano-30B-A3B | MoE, head-128 | 12/12 | 0.940 | 0.947 |
| Nemotron-3-Super-120B-A12B | MoE, head-128 | 12/12 | 0.973 | 0.987 |
| Qwen3.6-35B-A3B | MoE, head-256, linear-attn hybrid | 12/12 | 0.980 | 0.973 |
| Qwen3.5-122B-A10B | MoE, head-256, linear-attn hybrid | 12/12 | 0.967 | 0.973 |

## 端到端解码速度（DGX Spark sm121）

| 模型 | 32k | 64k | 100k |
|------|-----|-----|------|
| Gemma-4-31B-IT | 1.16× | 1.30× | 1.44× |
| Gemma-4-26B-A4B | 1.42× | 1.67× | 2.01× |
| Nemotron-3-Nano-30B | 0.88× | 0.88× | 1.01× |
| Qwen3.6-27B | 0.98× | 1.00× | 1.00× |
| Qwen3.6-35B-A3B | 0.99× | 0.98× | 0.96× |

## 代码状态

目前尚未提交合并：
- A4Q 依赖于早期 vLLM 工作：FlashInfer #3684（Gemma-4 的 asymmetric VO-split NVFP4 paged prefill）
- 该 PR 上游已开放但暂挂——一组重叠的 NVFP4-paged-KV PR 先落地，完成后 #3684 在其上 rebase，A4Q kernel 叠在上面
- 两个 half 已在 jethac/flashinfer (a4q-integration) 和 jethac/vllm 上推送，以 sm120 + sm121 wheel 形式分发
