#!/usr/bin/env python3
"""
article_data_build.py — Ascend to Science: Exploration of AI Chips for Scientific Computing
精简编译模式，基于 arXiv 2607.20120 论文。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "华为昇腾 NPU 做科学计算行不行？这篇论文给出了 5 个应用案例的答案",

    "summary": [
        {"key": "核心问题", "body": "AI 加速器（Ascend 910 NPU）能否在低精度张量引擎上高效运行科学计算负载？答案是：需要弥合精度、执行和数据移动三大鸿沟"},
        {"key": "三大鸿沟", "body": "执行鸿沟（Cube 适合稠密矩阵，Vector 处理不规则操作）、精度鸿沟（FP16/BF16 vs FP64）、数据移动鸿沟（软件管理内存层次 vs 自动缓存）"},
        {"key": "五大案例", "body": "HPL-MxP（混合精度 HPC 基准）、LRSVD（异构低秩分解）、SGEMM-cube（FP32 模拟）、PQSim（量子模拟）、SMC-X（蒙特卡洛），均实现了可竞争的精度和性能"},
    ],

    "lead": [
        "AI 加速器的崛起正在重塑计算系统的形态。当旗舰级超算系统越来越贵、越来越以 AI 为中心时，**科学计算社区面临一个现实问题：原本为 AI 设计的张量加速器，能否有效运行科学计算负载？**",
        "来自鹏城实验室的研究团队在 Ascend 910 系列 NPU 上进行了系统性探索。他们从**三个核心鸿沟**（精度、执行、数据移动）出发，通过五个代表性应用案例，展示了在 AI 原生 NPU 上运行科学计算负载的可行性与优化路径。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "三大鸿沟：AI 芯片与科学计算的根本矛盾",
            "paras": [
                "论文首先识别了在 AI 加速器上运行科学计算负载面临的三类根本性挑战：",
                "**执行鸿沟（Execution Mismatch）**：AI 加速器擅长大规模稠密、规整、高算术强度的张量运算（Cube 单元），但科学计算中大量存在的是内存受限、规约密集型或不规则操作，其性能不随张量吞吐量线性增长。",
                "**精度鸿沟（Precision Gap）**：科学计算通常依赖 FP64 或数值稳定的 FP32，而现代 AI 处理器从 FP16/BF16 低精度执行中获得效率优势。",
                "**数据移动鸿沟（Data-Movement Gap）**：科学计算的多级数据重用、不规则控制流和通信密集型执行，与 AI 架构的显式管理内存层次和 Tile 中心执行模型不匹配。",
                "Ascend 910 系列基于 DaVinci 架构，每个 AI Core 包含一个 Cube Core（稠密张量）和两个 Vector Core（通用向量处理），配合软件管理的 L0/L1/UB/L2/HBM 多级内存层次。这种架构使得 Cube 友好型内核（如 GEMM）受益巨大，而 Vector 主导或内存受限的内核则面临挑战。",
            ],
            "figs": [
                {"src": "fig_NPU_arch_910B.png", "caption": "Ascend 910B NPU 的 DaVinci 架构图：包含 Cube Core、Vector Core 和软件管理的多级内存层次（L0/L1/UB/L2/HBM）。"},
                {"src": "fig_ascend_stack.png", "caption": "Ascend 软件栈架构：从 Bisheng C++ 编程接口到 CANN 运行时再到硬件层。"},
            ],
        },
        {
            "type": "h2",
            "title": "内核级分析：Cube 与 Vector 的不对称性",
            "paras": [
                "论文对代表性科学计算内核（GEMM、SYRK、GEMV、DOT 等）进行了 Roof-line 模型分析。结果显示，**GEMM 类算子可以在 Cube 单元上达到 compute-bound，而矩阵-向量运算（GEMV）等则受限于内存带宽，与问题规模无关地保持低算术强度。**",
                "这意味着科学计算内核在 Ascend NPU 上不会均匀受益——有些能充分利用 Cube 的吞吐量优势，有些则受限于 Vector 单元和内存层次。理解这种不对称性，是后续应用优化的基础。",
            ],
            "figs": [
                {"src": "fig_blas_kernels.png", "caption": "BLAS 内核在 Ascend 910A 上的性能对比：GEMM 类内核充分利用 Cube 单元，而 GEMV 等受限于内存带宽。"},
                {"src": "fig_kernel_roofline.png", "caption": "Roof-line 模型分析：不同内核的算术强度与性能关系，揭示 Cube 与 Vector 执行的不对称性。"},
            ],
        },
        {
            "type": "h2",
            "title": "应用一：HPL-MxP — 混合精度 HPC 基准",
            "paras": [
                "HPL-MxP（Mixed-precision HPL）是评估混合精度计算能力的 HPC 基准。论文在 Ascend 910A 上实现了 CPU-NPU 协同的混合精度方案：**低精度 LU 分解在 NPU 的 Cube 单元上执行，高精度迭代求精在 CPU 上运行，两者通过异步通信重叠来隐藏数据传输开销。**",
                "在 8 卡 Ascend 910A 上，该方案实现了 **344.1 TFLOPS 的有效 FP64 性能**（MxP 模式），混合精度求解器实现了 1.08×10⁻¹² 的可靠残差。系统通过 Sliding Window LU 技术将通信与计算深度重叠，使通信开销仅占总执行时间的 0.1-2%。",
            ],
            "figs": [
                {"src": "fig_hpl_mxp_perf.png", "caption": "HPL-MxP 在 Ascend 910A 上的性能扩展：8 卡达到 344.1 TFLOPS 有效 FP64 性能。"},
                {"src": "fig_MxP_workflow-rev.png", "caption": "HPL-MxP 的混合精度工作流：低精度 LU 分解（NPU）→ 高精度迭代求精（CPU）→ 异步通信重叠。"},
            ],
        },
        {
            "type": "h2",
            "title": "应用二：LRSVD — 异构低秩 SVD 分解",
            "paras": [
                "低秩 SVD 是科学计算和数据分析中的核心操作。论文设计了**异构阶段放置方案**：将精度敏感的阶段（如随机投影、QR 分解）分配给 CPU 执行，精度容忍阶段（如矩阵乘法）分配给 NPU 的 Cube 单元。",
                "在 Ascend 910A 上，LRSVD 实现了**315-530 GFLOPS 的性能**，与 CPU 基线相比加速 2.5-4.5 倍。热力图分析显示，NPU 加速的矩阵乘法阶段占据了大部分计算时间，而 CPU 执行的精度敏感阶段在整体时间中占比很小。",
            ],
            "figs": [
                {"src": "fig_lrsvd-workflow-rev.png", "caption": "LRSVD 的异构工作流：随机投影和 QR 在 CPU 上执行，矩阵乘法在 NPU Cube 上加速。"},
                {"src": "fig_lrsvd_heatmap.png", "caption": "LRSVD 执行时间热力图：NPU 加速的矩阵乘法阶段占据主导，CPU 阶段占比很小。"},
            ],
        },
        {
            "type": "h2",
            "title": "应用三：SGEMM-cube — 低精度 Cube 模拟 FP32",
            "paras": [
                "SGEMM-cube 解决了一个核心问题：**如何在仅支持 FP16/BF16 的 Cube 单元上实现 FP32 精度的矩阵乘法？** 方案是使用 FP16 输入调用 Cube 引擎，然后通过输出格式转换和误差校正来恢复 FP32 精度。",
                "在 Ascend 910A 上，这种方法实现了**2.5-3.5 TFLOPS 的有效 FP32 性能**，优于 FP32 在 Vector 单元上的直接执行。精度分析显示，基于 FP16 Cube 的模拟乘法与 FP32 参考值的相对误差在 1×10⁻⁶ 量级，完全满足大多数科学计算应用的要求。",
            ],
            "figs": [
                {"src": "fig_sgemm_cube_workflow.png", "caption": "SGEMM-cube 的工作流：FP16 Cube 执行 + 输出格式转换 + 误差校正以实现 FP32 精度。"},
                {"src": "fig_sgemm_cube_perf_large_font.png", "caption": "SGEMM-cube 在 Ascend 910A/B/C 上的性能对比：相比 Vector 单元 FP32 执行有显著优势。"},
                {"src": "fig_sgemm_cube_accuracy_large_font.png", "caption": "SGEMM-cube 的精度分析：相对误差在 1×10⁻⁶ 量级，满足大多数科学计算需求。"},
            ],
        },
        {
            "type": "h2",
            "title": "应用四与五：PQSim 量子模拟 + SMC-X 蒙特卡洛",
            "paras": [
                "PQSim 和 SMC-X 代表了**带宽受限和不规则负载**如何在 AI NPU 上运行。",
                "**PQSim（量子电路模拟）**：这是一个带宽密集型负载，模拟量子态向量需要在内存中反复读写大规模状态向量。论文通过精心设计的数据布局和向量化指令，将量子门操作映射到 Ascend 的 Vector 单元，实现了与 GPU 基线可比的性能。在 28-qubit 规模下，单门操作延迟低于 20μs，接近 NVIDIA A100 的水平。",
                "**SMC-X（序贯蒙特卡洛）**：这是一个高度不规则的负载，包含动态粒子分裂、自适应重采样和可变工作负载。论文通过将不规则计算「规整化」为 NPU 友好的模式，利用 Vector 单元处理粒子操作，在 Ascend 910A 上实现了与 CPU 基线相比 2-3 倍的加速。",
            ],
            "figs": [
                {"src": "fig_PQSim_workflow_new.png", "caption": "PQSim 量子电路模拟的工作流：将量子门操作映射到 NPU Vector 单元。"},
                {"src": "fig_PQSim_perf.png", "caption": "PQSim 性能：28-qubit 规模下单门操作延迟低于 20μs，接近 A100 水平。"},
                {"src": "fig_NPU_flowchart_SMCX-large.png", "caption": "SMC-X 的 NPU 映射流程图：将不规则蒙特卡洛计算规整化为 NPU 友好的模式。"},
                {"src": "fig_Fig_SMC-X.png", "caption": "SMC-X 在 Ascend 910A 上的性能：相比 CPU 基线加速 2-3 倍。"},
            ],
        },
        {
            "type": "h2",
            "title": "总结：五个案例的通用优化原则",
            "paras": [
                "论文从五个应用案例中提取了可迁移的优化原则，这些原则不限于 Ascend 平台，也适用于其他张量中心型 AI 加速器：",
                "**精度感知的数值重构**：通过混合精度策略（如迭代求精）或精度模拟（如 FP16→FP32 模拟），在低精度硬件上实现高精度结果。",
                "**异构执行放置**：将精度敏感的阶段分配到高精度单元（CPU），精度容忍的阶段分配到高吞吐单元（NPU Cube）。",
                "**执行重构**：将不规则计算规整化为张量友好的模式，或将带宽密集型计算通过缓存感知的 Tile 切分来匹配内存层次。",
                "**显式数据移动编排**：通过软件管理的多级内存层次和通信-计算重叠，隐藏数据移动开销。",
            ],
        },
    ],

    "conclusion": [
        "这篇论文的核心结论是：**AI 原生的 NPU（如 Ascend 910）在经过适当的数值重构、执行放置和数据移动编排后，可以成为科学计算的有效平台。** 五个应用案例——HPL-MxP、LRSVD、SGEMM-cube、PQSim、SMC-X——覆盖了从稠密线性代数到量子模拟再到蒙特卡洛的广泛科学计算负载，均展示了在 Ascend NPU 上实现数值稳健、性能可竞争且可扩展的结果。",
        "当然，论文也坦诚地指出了局限性：所有实验在 Ascend 平台（910A/910B/910C）上进行，结论可能不直接推广到其他厂商的 NPU 或 GPU；数值稳健性依赖于精心设计的混合精度策略，对舍入误差更敏感的应用可能需要额外的算法重构。",
    ],

    "reference_url": "https://arxiv.org/abs/2607.20120",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")