#!/usr/bin/env python3
"""
article_data_build.py — nvidia-rubin-architecture 精简编译版
===========================================================
原文：Inside NVIDIA Rubin GPU Architecture: Powering the Era of Agentic AI
来源：NVIDIA Developer Blog
风格：精简章节、讲重点、简洁专业
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "架构定位", "body": "Rubin GPU 专为 Agentic AI 设计，相比 Blackwell 实现每瓦 Agentic 吞吐 10x 提升"},
        {"key": "核心创新", "body": "3360 亿晶体管、HBM4 22 TB/s、第三代 Transformer Engine 50 PFLOPS NVFP4、NVLink 6 3600 GB/s"},
        {"key": "系统设计", "body": "Vera Rubin NVL72 机架级集成+DSX MaxLPS 电源优化，同功耗可多部署 40% GPU"},
    ],

    "lead": [
        "Agentic 工作负载不再是单次提示和响应的简单循环，而是持续的推理过程：**推理、规划、使用工具、验证中间结果、在超长上下文中执行复杂的多步任务。** 这要求低延迟、高解码吞吐、高效长上下文注意力、大 KV cache 容量，以及跨紧密耦合 GPU 域扩展模型的能力。",
        "NVIDIA Rubin GPU 正是为此设计。**相比 Blackwell，Rubin 实现了每瓦 Agentic 吞吐最高 10x 的提升。** 增强的 Tensor Core、新的 HBM4 内存子系统、以及第三代 Transformer Engine（提供高达 50 PFLOPS NVFP4 性能），共同加速 Agentic 工作负载。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "芯片架构概览",
            "paras": [
                "Rubin GPU 由两颗**光罩限制计算芯片（reticle-limited compute dies）**构成，通过高速片间互联 NV-HBI（NVIDIA High-Bandwidth Interface）统一封装。3360 亿晶体管、224 个流式多处理器（SM）、896 个 Tensor Core，提供原始计算密度。",
                "第三代 Transformer Engine 可在多种数值格式间灵活切换精度，支持高达 **50 PFLOPS 的 NVFP4 推理性能**，同时保持精度。",
                "内存方面：**288 GB HBM4**，12-Hi 堆叠，提供 **22 TB/s 峰值带宽**。互联方面：NVLink 6 提供 3600 GB/s scale-up 带宽，NVLink-C2C 提供 1800 GB/s CPU-GPU 一致性互联，PCIe Gen 6 x16 提供 256 GB/s 主机连接。",
                "此外，**TEE-I/O 机密计算**为 AI Factory 中静态、传输中和使用中的数据提供安全保障。",
            ],
            "figs": [
                {"src": "fig00.png", "caption": "图 1：Rubin GPU 芯片架构，展示 GPC、HBM 控制器、L2 缓存、NVLink 等模块"},
            ],
        },
        {
            "type": "h2",
            "title": "推理关键路径加速",
            "paras": [
                "峰值算力本身不足以加速 Agentic 推理。**实际性能取决于 GPU 如何高效搬运数据、执行矩阵运算、处理长上下文注意力、以及在依赖 kernel 之间切换。** Rubin 在以下关键路径上做了针对性优化。",
            ],
        },
        {
            "type": "h3",
            "title": "MoE 权重和 Token 搬运",
            "paras": [
                "混合专家（MoE）模型将 token 动态路由到多个专家网络。随着专家数量增长，**高效定位和搬运专家权重变得越来越重要。**",
                "Rubin 增强了 Tensor Memory Accelerator（TMA），支持**内联描述符更新**。kernel 可以为共享相同布局的 tensor 保留一个统一描述符，在 TMA 指令中直接覆盖内存指针和步长（stride），无需在内存中修改描述符。",
                "这意味着：**Blackwell 需要为每个专家维护一个描述符，Rubin 只需一个描述符供所有专家共享。** 专家越多，省下的元数据管理开销越大。",
            ],
            "figs": [
                {"src": "fig01.png", "caption": "图 2：Rubin 简化 MoE 描述符共享——Blackwell 每专家一个描述符 vs Rubin 所有专家共享一个"},
            ],
        },
        {
            "type": "h3",
            "title": "GEMM 指令吞吐翻倍",
            "paras": [
                "矩阵运算（GEMM）是推理的核心。Rubin Tensor Core 将单个 warp 级矩阵指令的 K 维度（累加维度）处理能力**提升到 Blackwell 的两倍**——在 Rubin 上只需 2 次迭代完成的工作，Blackwell 需要 4 次。",
                "这相当于**GEMM 指令吞吐翻倍**，在大 Batch 推理和专家并行场景中效果显著——每次矩阵运算可处理更大 K 维度，减少迭代次数和调度开销。",
            ],
            "figs": [
                {"src": "fig02.png", "caption": "图 3：Rubin 的 K 维度指令吞吐——比 Blackwell 翻倍"},
            ],
        },
        {
            "type": "h3",
            "title": "自适应压缩稀疏性",
            "paras": [
                "Agentic 推理中，长上下文导致 attention 和 MLP 激活值占据大量内存带宽和存储。Rubin 引入**自适应压缩和稀疏性**，对每个 Transformer 层的 attention 和 MLP 激活阶段应用。",
                "在推理时，密集激活张量被转换为带有元数据的稀疏张量，跳过零值或接近零值的元素。自适应之处在于**压缩率和稀疏率根据每层的内容分布动态调整**，非静态固定。这减少了需要搬运的数据量，间接提高了有效内存带宽利用率。",
            ],
            "figs": [
                {"src": "fig03.png", "caption": "图 4：自适应压缩稀疏性——密集矩阵转为带元数据的稀疏矩阵，应用于 attention 和 MLP 激活"},
            ],
        },
        {
            "type": "h3",
            "title": "生产者-消费者数据流加速",
            "paras": [
                "推理 kernel 以流水线方式执行，前一个 kernel 的输出是后一个 kernel 的输入。Blackwell 中，消费者 kernel 的线程块在生产者 kernel 的线程块完成后才能开始——即使生产者只完成了一部分。",
                "**Rubin 引入了数据驱动轮询（data-driven polling）**：消费者线程块不需要等待整个生产者 kernel 完成，一旦生产者线程块完成其输出数据的部分，消费者就可以立即开始读取并处理。这使得 kernel 间的流水线重叠更细粒度，减少了端到端延迟。",
            ],
            "figs": [
                {"src": "fig04.png", "caption": "图 5：Blackwell vs Rubin 的生产者-消费者时间线——Rubin 使用数据驱动轮询更早启动消费者"},
            ],
        },
        {
            "type": "h2",
            "title": "内存与通信子系统",
            "paras": [
                "随着模型、上下文窗口和 GPU 域的增长，**数据搬运变得与计算同等重要**。Rubin 在内存和通信方面做了以下创新。",
            ],
        },
        {
            "type": "h3",
            "title": "NVLink Counted Writes",
            "paras": [
                "当通信直接融合在 GPU kernel 内部时，kernel 不会停止并将控制权交回 CPU——它直接通过 NVLink 将数据写到另一个 GPU，或执行规约操作，同时计算仍在进行。",
                "Rubin 引入了 **counted writes** 用于设备发起的 NVLink 通信。传统方案需要内存屏障、确认信号和原子标志；Rubin 只需一个计数器更新，接收 GPU 即可高效跟踪传输完成。这**减少了 GPU 间数据搬运的同步延迟**。",
            ],
            "figs": [
                {"src": "fig05.png", "caption": "图 6：Rubin 使用 counted writes 加速 NVLink 通信——减少同步开销"},
            ],
        },
        {
            "type": "h3",
            "title": "HBM4 内存子系统",
            "paras": [
                "**推理的解码阶段本质上是内存子系统受限的。** Agentic 工作负载通过长上下文、大 KV cache 和交互式 token 生成，放大了这一约束。",
                "Rubin 的 HBM4 将接口宽度相对于 HBM3e 翻倍，结合新的内存控制器、深度生态协同以及紧耦合的计算-内存集成，提供 **22 TB/s 内存带宽——Blackwell 的 2.8 倍**。同时提供单 GPU 最高 **288 GB HBM4 容量**，支持更大的模型驻留、更长的上下文和大 KV cache 而无需卸载。",
                "**容量和带宽的角色不同但互补：** 容量支持模型驻留和更大 KV cache（减少卸载）；带宽支撑逐 token 生成阶段（快速搬运权重和 KV 状态）；TMA 和内存局部性策略帮助软件高效利用内存子系统。",
            ],
            "figs": [
                {"src": "fig06.png", "caption": "图 7：Blackwell 到 Rubin 的内存带宽演进——8 TB/s 到 22 TB/s"},
            ],
        },
        {
            "type": "h2",
            "title": "能效与机架级设计",
            "paras": [
                "Agentic AI 基础设施需要优化的不止是单个 GPU，而是**整个 AI Factory 的功耗、散热、网络和机架级资源利用**。",
            ],
        },
        {
            "type": "h3",
            "title": "Intelligent Power Smoothing",
            "paras": [
                "AI 工作负载的功耗需求剧烈波动，产生瞬时峰值，导致可用容量被闲置。Vera Rubin 电源使用**SoC（荷电状态）智能功率平滑**来吸收这些波动，平均功耗降低约 10%，50ms 峰值功耗降低约 20%。",
            ],
            "figs": [
                {"src": "fig07.png", "caption": "图 8：GPU 功率曲线——电容器覆盖峰值、填充空闲低谷，维持更平稳的持续交流功率输入"},
            ],
        },
        {
            "type": "h3",
            "title": "DSX MaxLPS",
            "paras": [
                "在 AI Factory 层面，NVIDIA DSX MaxLPS 将功率平滑扩展到 GPU 之间、机架之间和整个工作负载。结合 45°C 液冷和 DSX OS 调度层，**在相同功耗预算下可多部署最多 40% 的 GPU**，同时对工作负载性能影响最小。",
            ],
            "figs": [
                {"src": "fig08.png", "caption": "图 9：DSX MaxLPS 在相同功耗预算下支持最多 40% 更多 GPU"},
            ],
        },
    ],

    "conclusion": [
        "NVIDIA Rubin GPU 专为 Agentic AI 的执行模式而设计——**长上下文推理、多步生成、分布式 MoE 解码、低延迟交互**，所有这些必须连续在大规模运行。",
        "其计算、内存、网络、机架级、功耗、散热和软件层经过精心协同设计，让 AI Factory 中更多部分执行有用工作，而非等待数据、通信或功耗限制。结果是：**在固定功耗包络内，产出更多有用 token 和完成的 AI 工作**——一个为 Agentic 时代打造的架构。",
    ],

    "reference_url": "https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/",
    'title': '深入 NVIDIA Rubin GPU 架构：为 Agentic AI 时代打造',
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
