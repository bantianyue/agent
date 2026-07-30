#!/usr/bin/env python3
"""
article_data_build.py — SLAI T-Rex: Full-Parameter Post-training of DeepSeek-V4 on Ascend SuperPOD
基于 arXiv 2607.20145，完整覆盖原文结构和细节。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "SLAI T-Rex：在 Ascend SuperPOD 上全参数后训练万亿级 DeepSeek-V4 模型",

    "summary": [
        {"key": "系统优化", "body": "在 Ascend CloudMatrix384 SuperPOD（910C NPU）上全参数训练 1.6T DeepSeek-V4-Pro，通过多层次优化实现 34.22% MFU，相比基线提升 2.93 倍"},
        {"key": "AuraKernel", "body": "运筹学（OR）驱动的 AscendC 内核优化 agent，通过 OR 求解器自动优化 tile 选择和长时间跨度的内核搜索"},
        {"key": "领域适配", "body": "面向运筹学（OR）的 CPT→SFT 后训练工作流，在 B4O 基准上平均精度 71.81%，超越 GPT-5.4-Mini 3.98 个百分点，超越基础 DeepSeek-V4-Flash 11.27 个百分点"},
    ],

    "lead": [
        "万亿参数级 MoE 模型的后训练一直紧密绑定在 CUDA 或 TPU 基础设施上。**在 SIMD 架构的 AI 芯片（如 Ascend NPU）上做全参数后训练，是否可行？**",
        "SLAI T-Rex 给出了肯定的答案。这篇系统性的报告展示了在 Ascend CloudMatrix384 SuperPOD（910C NPU）上对 DeepSeek-V4 系列进行全参数后训练的完整工程实践。**Pro 版本验证了基础设施可扩展性，Flash 版本验证了领域适配能力。**",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "万亿参数级训练的瓶颈分析",
            "paras": [
                "DeepSeek-V4-Pro 拥有 1.6 万亿参数，集成了大规模 MoE 层和混合稀疏注意力。在 256 卡 Ascend 910C 上的 profiling 显示，训练 inefficiency 有两张互补的面孔：",
                "**通信瓶颈**：通信占设备内核时间的 52.2%（40.76 秒/步）。其中 Tensor/Data Parallelism（AllReduce/AllGather）占 48.4%，Pipeline Parallelism（Send/Recv）占 36.7%，Expert Parallelism（AllToAllV）占 14.5%。问题是通信不是带宽受限的，而是调度受限的——同步等待和流调度的开销远大于实际数据传输。",
                "**计算瓶颈**：在设备端，少量大算子（Cube 内核）和大量小算子（Vector 内核的「长尾」）共同占据设备时间。Vector 内核的碎片化启动和内存移动开销是性能瓶颈的关键。",
            ],
            "figs": [
                {"src": "fig_ch2.1-fig_overview_v0.png", "caption": "万亿参数 LLM 在 Ascend SuperPOD NPU 上的训练延迟分解：(a) 端到端训练流水线中的延迟分布，(b) 平均延迟分解（计算、通信、NPU 空闲气泡）。"},
                {"src": "fig_ch2.2.1-bottleneck_anatomy_v3.png", "caption": "瓶颈分析：(a) 步时间分解为计算、暴露通信和流水线气泡，(b) 大 Cube 内核与小 Vector 内核的启动次数与设备时间占比对比，(c) Vector 内核的流水线占用分析。"},
            ],
        },
        {
            "type": "h2",
            "title": "多层次并行与通信优化",
            "paras": [
                "论文提出了端到端的 SuperPOD 感知训练优化框架，覆盖三个层面：",
                "**并行策略优化**：针对万亿参数 MoE 模型，设计了多维并行（TP+PP+DP+EP）的联合优化方案。通过分析 MoE 路由的异构性（Attention、路由、Dispatch、Expert FFN、Combine 各有不同的计算和通信强度），提出动态重叠调度策略。",
                "**通信编排**：关键创新是将通信与计算深度重叠。由于 MoE 的 token 路由在步间有负载变化，重叠窗口既不均匀也不稳定。论文通过细粒度的流调度和计算-通信依赖分析，将暴露通信时间大幅压缩。",
                "**内存管理**：针对 Ascend 软件管理内存层次的特点，设计了显式的数据移动编排，减少 MTE（Memory Transfer Engine）的等待时间。",
            ],
            "figs": [
                {"src": "fig_ch2.2-train_framework.png", "caption": "Ascend SuperPOD 上的训练框架架构：多维并行、通信编排和内存管理的协同设计。"},
                {"src": "fig_ch2.2-cover_dispatch_sync.png", "caption": "dispatch 与同步的通信重叠优化策略，掩盖通信时间。"},
                {"src": "fig_ch2.2-etp.png", "caption": "Expert Tensor Parallelism 的通信优化方案。"},
            ],
        },
        {
            "type": "h2",
            "title": "AuraKernel：OR 驱动的 AscendC 内核优化 Agent",
            "paras": [
                "AuraKernel 是论文中的核心创新——**基于运筹学（OR）的 AscendC 内核优化 agent**。与主要依赖 harness 构建和循环级工程的现有内核 agent 不同，AuraKernel 将 OR 求解器引入内核优化工作流。",
                "核心思路是将 Ascend 的 Cube 单元 tile 优化问题建模为 OR 问题：给定算子形状、内存层次约束（L0/L1/UB/L2/HBM）、数据依赖关系，OR 求解器自动搜索最优的 tile 划分方案。",
                "AuraKernel 包含三个关键组件：**OR 求解器**负责 tiling 优化，**AscendC Harness**提供编译和 profiling 环境，**迭代优化循环**根据实际运行时间反馈调整搜索方向。与手动优化和启发式优化相比，OR 求解器能更系统地探索 Ascend 的内核搜索空间。",
                "论文进一步引入了**算子融合与重写（Operator Fusion and Rewrite）**策略。通过分析 Ascend NPU 的算子链执行模式，将多个连续的 Vector 内核融合为单个更高效的复合内核，减少内核启动开销和内存移动。同时，针对 Attention 机制中的 RoPE、Softmax 等关键算子，设计了 NPU 感知的重写优化，将计算从低效的 Vector 单元迁移到高效的 Cube 单元。",
            ],
            "figs": [
                {"src": "fig_aurakernel.png", "caption": "AuraKernel 架构：OR 求解器驱动的 AscendC 内核优化 agent，包含 OR 求解器、AscendC Harness 和迭代优化循环。"},
                {"src": "fig_ai_workflow.png", "caption": "AuraKernel 的优化工作流：从算子 profiling 到 OR 建模再到自动 tiling 搜索的完整流程。"},
                {"src": "fig_fig_fusion_time_breakdown.png", "caption": "算子融合的时间分解：AuraKernel 优化前后的性能对比。"},
                {"src": "fig_fig_fusion_trace_schematic.png", "caption": "算子融合的 trace 示意图：优化前后的计算与通信重叠情况。"},
                {"src": "fig_ch2.3.3-operator_chain_fusion_atlas.png", "caption": "Ascend NPU 上的算子链融合策略：将多个 Vector 算子融合为高效复合内核。"},
                {"src": "fig_ch2.3.3-rope_mechanisms.png", "caption": "RoPE 算子的 NPU 感知重写优化：将计算从 Vector 迁移到 Cube 单元。"},
                {"src": "fig_ch2.3.3-mhc_mechanisms.png", "caption": "MHC（Multi-Head Cache）机制的 NPU 优化实现。"},
            ],
        },
        {
            "type": "h2",
            "title": "最终性能：34.22% MFU 与 2.93 倍提升",
            "paras": [
                "通过 AuraKernel 在内核级的优化与系统级的多层次优化协同，DeepSeek-V4-Pro 在 Ascend SuperPOD 上实现了 **34.22% 的 MFU（Model FLOPs Utilization）**，相比默认基线提升了 **2.93 倍**。",
                "MFU 是衡量训练系统效率的核心指标，34.22% 在 SIMD 架构的 NPU 上是相当可观的数字。作为对比，同等规模的 GPU 集群通常在 40-50% 范围。考虑到 Ascend 910C 的 SIMD 架构与 GPU 的 SIMT 架构在灵活性上的本质差异，这个结果展示了 Ascend SuperPOD 在万亿参数级训练上的潜力。",
                "Ablation 实验显示，各优化模块的贡献如下：通信-计算重叠优化贡献了最大的 MFU 提升（约 1.5 倍），AuraKernel 内核优化贡献了约 1.3 倍，并行策略优化和内存管理优化贡献了约 1.1 倍。这些优化是累乘的，最终实现了 2.93 倍的总提升。",
            ],
            "figs": [
                {"src": "fig_overview_infra_and_acc.png", "caption": "Ascend SuperPOD 上的基础设施优化与加速效果概览：MFU 从基线提升 2.93 倍至 34.22%。"},
                {"src": "fig_ablation.png", "caption": "Ablation 实验：各优化模块对 MFU 提升的贡献分解。"},
            ],
        },
        {
            "type": "h2",
            "title": "运筹学（OR）领域适配：CPT→SFT 工作流",
            "paras": [
                "除了 Pro 版本的基础设施验证，论文还在 DeepSeek-V4-Flash 上验证了 **OR 领域适配的后训练工作流**，覆盖 solver-grounded 数据构建、SFT 数据清洗、CPT-to-SFT 迁移和基准评估。",
                "**两阶段适配策略**：论文采用 Continued Pre-Training（CPT）→ Supervised Fine-Tuning（SFT）的渐进式工作流。CPT 阶段让模型学习 OR 领域的数学建模先验知识——包括约束矩阵结构、目标函数形式、变量类型定义等。SFT 阶段则对齐具体的 solver 交互格式和输出标准化。",
                "**CPT 数据构建**：从公开的 OR 资源（NL4OPT、OptiBench、B4O 等基准）中收集领域数据，同时使用 solver 验证过的合成优化文档进行数据增强。数据涵盖四种任务类别（线性规划、整数规划、混合整数规划、约束规划）和三种问题表示（自然语言描述、数学公式、代码模板）。",
                "**SFT 数据管线**：通过自蒸馏（Self-Distillation）生成高质量的 OR 建模 SFT 数据。核心组件包括：solver-grounded 数据构建（利用 solver 的执行结果验证数据的正确性）、contract-aware 清洗（基于合同语义的一致性检查）、CoT 增强（将建模过程拆解为逐步的 Chain-of-Thought）。",
                "**关键发现**：SFT 提供了监督任务对齐，将 B4O-Feasible 从 60.47% 提升到 65.93%，B4O-ORGEval 从 34.26% 提升到 48.73%。而 CPT 初始化后的 SFT 进一步将两者提升到 **71.22% 和 59.39%**，说明 CPT 贡献了 OR 领域建模的先验知识，提高了 solver 面向的可行性和结构等价性。",
                "在多个 OR 评估指标上聚合，模型平均精度达到 **71.81%**，超越 GPT-5.4-Mini 3.98 个百分点，超越基础 DeepSeek-V4-Flash 11.27 个百分点。进一步分析表明，CPT 建立的先验知识对 SFT 的增益是互补的——CPT 主要提升结构等价性（solver 输出的语法正确性），SFT 则主要提升可行性（solver 输出的语义正确性）。",
            ],
            "figs": [
                {"src": "fig_data_engine.png", "caption": "OR 领域的数据引擎：solver-grounded 数据构建、自蒸馏 SFT 数据生成、contract-aware 清洗的完整流水线。"},
                {"src": "fig_flywheel.png", "caption": "OR 领域适配的飞轮效应：从数据构建到训练到评估的闭环迭代。"},
                {"src": "fig_50k_sft_stability_paper.png", "caption": "50K SFT 训练稳定性分析：loss 曲线、梯度范数和学习率调度的变化。"},
                {"src": "fig_base_error_family_bars.png", "caption": "基础模型在不同 OR 设置下的错误类型分布。"},
            ],
        },
    ],

    "conclusion": [
        "SLAI T-Rex 是**首个公开的、在 Ascend SuperPOD 上全参数后训练万亿参数 MoE 模型的完整工程研究**。核心成果包括：",
        "**系统层面**：通过多层次优化实现了 34.22% MFU（2.93 倍提升），证明 SIMD 架构的 NPU（Ascend 910C）可以胜任万亿参数级 LLM 的后训练任务。",
        "**算法层面**：AuraKernel 将 OR 求解器引入 AscendC 内核优化，为 AI 芯片上的自动内核优化提供了新范式。算子融合与重写策略进一步释放了 NPU 的计算潜力。",
        "**应用层面**：OR 领域适配的 CPT→SFT 工作流超越了 GPT-5.4-Mini，展示了在长尾工业决策领域（如调度、运输、供应链管理）的应用前景。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.20145",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")