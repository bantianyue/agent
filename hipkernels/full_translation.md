# 迈向更好的 AMD GPU HIP Kernel 生成：合成数据、多Agent搜索与强化学习

## TLDR

本文探索如何让语言模型更擅长为 AMD GPU 生成高性能 HIP kernel。核心贡献：
1. 一个包含 500 个新 PyTorch 参考任务的合成数据集，通过 mutation、composition 和 constraint-based generation 三种模式生成，覆盖更广泛的工作负载
2. 一个多 Agent 优化流水线用于 HIP kernel 生成，包含专门化的任务生成、PyTorch-to-HIP 翻译、硬件评估和进化优化 Agent
3. 一个基于小规模开源模型（Qwen2.5-Coder-14B-Instruct）的框架，先做 SFT 再做 GRPO RL。SFT 帮助模型学到正确的 HIP 模式，RL 通过直接奖励正确性和 MI350X GPU 上的加速效果进一步提升性能

结果表明编译通过率和正确率在所有 KernelBench 层级上都有提升，RL 贡献了最大增益。但实现有意义的 PyTorch 加速仍需更深的硬件意识和优化推理。

## 动机

每个现代 AI 工作负载的性能瓶颈都在 kernel 质量。编写高性能 kernel 需要对硬件、底层语言和优化技术的深度熟悉，而这些技能在 NVIDIA CUDA 生态之外极度稀缺。

AMD 的 HIP 是这种匮乏的典型例子。它是一种编译器验证的底层编程语言，开源训练数据相对稀少，但它的目标加速器正越来越多地出现在生产 AI 集群中。这种不对称可以被经验性地观察到：SOTA 语言模型通常能生成流畅的 CUDA，但在生成 HIP 时，模型可能幻觉 API 或发出看似合理但编译失败或多 seed 正确性检查失败的 kernel。

## 方法

本文研究了三个互补的思路：(1) 用合成 PyTorch 工作负载扩展任务空间，(2) 通过多 Agent 进化搜索优化 kernel，(3) 用 SFT + GRPO RL 训练小规模开源模型（Qwen2.5-Coder-14B-Instruct）。所有方法在 KernelBench 扩展至 AMD MI350X GPU 上评估编译、正确性和运行时性能。

### 1. 合成数据生成

本文用 Gemini-2.5-Flash 驱动的多 Agent 流水线生成了一组经过验证的 HIP kernel 及其对应的 PyTorch 参考实现。该流水线包含 8 个协作者 Agent：

- **Task Generator**：将 PyTorch 参考封装为结构化任务，通过 mutation、composition 和 constraint-based generation 三种模式合成新的参考模块
- **Translator**：从 PyTorch 参考生成第一个可工作的 HIP kernel，失败时用验证器的错误信息重试
- **Correctness Verifier**：确定性正确性门控，拒绝 shortcut pattern，跨多个 seed 运行候选 kernel 与 PyTorch 参考对比
- **Evolutionary Optimizer**：迭代采样新候选 kernel，以最相似的先前验证 kernel、当前最佳 kernel 和历史失败记录为条件
- **Plausibility Screener**：基于 LLM 的评审者，对每个候选 kernel 的编译可能性和合理性打分
- **Hardware Evaluator**：在 AMD MI350X GPU 上编译每个幸存候选 kernel，检查正确性并测量运行时
- **Archive Manager**：持久化每个候选 kernel 及其标签、分数和运行时，输出 SFT 和 RL 训练记录
- **Offline Auditors**：配对生成器和审计器，运行精心设计的正确/错误/欺骗性测试用例

三种任务生成模式：
- **Mutation**：修改现有 KernelBench 问题的计算属性
- **Composition**：从 14 个算子的模板库中随机组合出新工作负载
- **Constraint**：通过自然语言约束描述直接指定工作负载

### 2. SFT

在合成语料上微调 Qwen2.5-Coder-14B-Instruct，3 个 epoch，batch size 2，学习率 2e-5。

### 3. RL

使用 GRPO，每个 prompt 生成 4 个候选 kernel。采用 TRLOO 进行优势估计。奖励信号包括在 AMD MI350X 硬件上执行 kernel 的结果。三个关键修改：多轮 episodes、reward smoothing 和总结 Agent注入失败经验。

## 结果与讨论

### 编译结果

编译通过率：从 baseline 到 SFT 再到 GRPO，所有 KernelBench 层级都有显著提升。

Baseline 模型的 kernel 语法上看似正确，但编译失败的原因是更深层的理解错误——无效内存访问和错误 API 使用。SFT 后模型学到了常见的 HIP 实现模式，并对"什么应该被优化"有了更好的判断力。RL 强化了 SFT 中出现的成功模式，模型学会了哪些修改是安全的。

### 正确性结果

正确率：SFT 下 Level 2 为 13%，RL 下提升到 60%。RL 帮助 Level 2 最大，因为 Level 2 任务围绕简单的融合机会构建。

Level 3 仍然困难，因为需要保留整个模型的完整行为。

### 模型学到的优化模式

- 算子融合（最常见）
- 共享内存归约
- 分块矩阵乘法
- 选择性优化

### 性能结果

RL 虽然提升了编译和正确率，但有意义的性能加速仍然难以实现。Level 2 最好，约 60% 的正确 kernel 匹配了 PyTorch 性能。没有 kernel 实现大的性能提升。原因是模型学到的是局部优化策略，而非替换昂贵的算子。

### 与先前工作的比较

AMD 的工作在 24 个任务的基准上评估 PyTorch-to-HIP 翻译。KernelArena 在 41 个问题的 KernelBench-HIP 子集上报告结果，Opus 4.5 的中位加速比为 1.37x。但这些工作使用不同的基准、不同的 GPU 和昂贵的 frontier 模型，与本文不可直接比较。

## 结论

合成 kernel 生成、多 Agent 进化搜索和 SFT+GRPO RL 在小型开源模型上带来了 HIP kernel 编译和正确率的有意义提升，RL 贡献最大。PyTorch 加速仍是一个更难的目标。将 ROCm profiler 信号引入奖励是自然的下一步。

## 未来工作

更大的合成数据集是否带来更多提升？失败驱动的后训练——用更强的模型和 test-time scaling 反复尝试失败问题并将成功方案加回训练集。
