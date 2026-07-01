# full_translation.md — LongCat-2.0

## 引言

美团正式发布并开源 LongCat-2.0，一个大规模 MoE 语言模型，**总参数 1.6T（万亿），每词元约激活 48B（480 亿）参数**——相比前代 LongCat 模型有大幅提升，并伴随多项架构改进。

完整训练和大规模部署全部构建在 **AI ASIC 超算集群**之上。预训练跨越数百万加速器小时、超过 35 万亿词元，**全程无回滚或不可恢复的 Loss 尖峰**——证明团队有能力在替代硬件平台上进行前沿规模训练。

为增强模型的长程任务能力，团队引入 **LongCat Sparse Attention (LSA)**，并用数千亿词元的 **100 万上下文**数据训练 LongCat-2.0。结合专门的后训练，使 LongCat-2.0 在编码和 Agent 任务上表现强劲。

LongCat-2.0 已深度集成 Claude Code、OpenClaw 和 Hermes 等主流框架，在代码理解、仓库级编辑、自动任务执行和 Agent 工作流方面均表现优异。

## 架构

架构设计继承自 LongCat-Flash，在参数效率和长上下文训练/推理速度上进一步推进。

### LongCat Sparse Attention (LSA)

LSA 是 DeepSeek Sparse Attention 的演进版本，采用更轻量的索引器，加速长上下文处理而不牺牲模型质量。三个正交的效率改进：

1. **Streaming-aware Indexing (SI)** — 重塑词元选择预算，将硬件对齐的连续访问与动态随机选择结合，将碎片化内存访问转化为可预测的顺序读取，实现 HBM 合并访问和高有效带宽。
2. **Cross-Layer Indexing (CLI)** — 利用相邻层之间注意力显著性的经验稳定性分摊索引开销：单次索引传递服务多个连续层的推理（通过训练期间的跨层蒸馏实现）。
3. **Hierarchical Indexing (HI)** — 粗到细的两阶段评分方案（先通过块级近似评分做粗召回，再在召回的候选集中做细粒度词元选择），缩小每个查询的索引器候选空间。HI 以训练无关方式应用，仅对选定的超长上下文任务启用。

三个组件正交设计，可独立开关。

LSA 扩展到了 3 步 Multi-Token Prediction (MTP) 模块用于加速推测解码。CLI 在 draft 和 target 模型中有不同应用：target 模型中每两个连续层共享一次索引传递；多步 MTP 中所有三个 draft 步共享一次索引传递。

### N-gram Embedding

继承自 LongCat-Flash-Lite。通过 N-gram 词元组合将嵌入空间扩展约 100 倍。配置：n-gram size=5，包含 **135B N-gram Embedding 参数**。遵循以下缩放原则：

- **MoE 稀疏度已过甜点区**：模型稀疏度已达约 97%（即使不考虑 N-gram Embedding），再扩展 135B expert 参数的增益可忽略不计；N-gram Embedding 的同等参数规模带来的收益远超标准 expert。
- **N-gram Embedding 占比约束在最优范围**：缩放实验表明超过 50% 时优势下降。LongCat-2.0 中严格控制在 10% 以下。

推理时，将参数从 expert 转移到 N-gram Embedding 可减少大批量解码的内存 I/O，加速生成。

## AI ASIC 超算集群上的可扩展基础设施

训练与部署构建在数万 AI ASIC 超算集群上。相比成熟的 NVIDIA GPU 生态系统，支持软件生态仍较薄弱，团队在构建稳定、安全、可扩展的基础设施上投入了大量精力。

### 训练

超过 5 万 AI ASIC 上预训练，两大挑战：模型规模和集群规模。

**确定性与可靠性：** 通信和计算路径都强制确定性，覆盖 Embedding、FA(Flash Attention)、LSA 和 MoE 层。所有归约型算子采用二叉树分段累加策略减少浮点误差累积。在选定计算密集型算子中引入位翻转检测及时捕获硬件异常。

故障恢复方面，端到端监控驱动故障识别、流量切换和恢复——隔离故障链路对训练无感知影响，修复后的链路只有通过压力测试才能重新加入。

**大规模训练（6D 并行）：** 加速器单设备内存远小于 H800（80 GB），内存是首要瓶颈。
- TP/CP/EP/DP/PP + **EMBP**（针对 N-gram Embedding 并行加速）
- **Superpods**：最多 48 台机器的物理单元，内部全互联高带宽，之间 RoCE 互联。同规模和环境下提升约 30% 预训练吞吐。
- 内存优化：ZeRO-1、选择性重计算、OOM 感知卸载、将 padding tokens 路由到 zero-expert
- Muon 优化器：在超大规模部署，涵盖 TP 并行优化、DP 状态冗余消除、高效对称矩阵乘法 kernel

**长上下文训练：**
- LSA 算子与正向优化：自研确定性注意力算子（dense-warmup + sparse 阶段），前向-only dense-warmup 策略计算 KL Loss 和梯度
- 1M 上下文扩展：基于 all-gather 的 CP 方案，可扩展至 CP>512，实现原生 1M 长度训练
- 计算-通信重叠：shortcut-layer 架构使 MoE 通信与并行分支计算重叠，LSA top-k 索引计算与 KV all-gather 重叠

### 推理

为 1.6T 模型在 1M token 上下文中提供服务，HBM 容量、I/O 带宽和节点间互联带宽都是严峻挑战。

**模型级优化：**
- Attention：absorb computation mode（prefill 和 decode 阶段）、索引器与 MLA prolog 流水线化、KVP 分片 KV-cache
- ScMoE：在加速器上利用显式每核控制，实现 dense 和 MoE 分支的完全并行执行

**加速器导向优化：**
- **Super Kernel**：减少 graph mode 下内核内启动开销
- **Weight Prefetch**：利用较大的 L2 cache 预取权重，在前一算子计算中隐藏 I/O 延迟
- **Scale Up/Out**：P/D 节点间 KV-cache 传输利用内置 200 Gbps 网卡，逐层传输；KV-cache store 利用 host RDMA

**部署与服务：**
- **PD 分离部署**：Prefill 节点用多节点 CPP 缩小 EP 域 + Attention SP 处理长序列；Decode 节点用 KVP 分片 KV-cache + EP128 降低每设备内存和 I/O
- **EPLB (Expert-Parallel Load Balancing)**：异步统计收集和放置计算，离关键路径

## 多教师学习（后训练）

后训练流水线引入三类专家组的 **MOPD 架构**：

1. **Agent Experts** — 复杂真实场景中的自主任务执行，在代码、工作、搜索等细粒度垂直领域达 SOTA。优化端到端成功率 + 原子能力（精确工具调用、多轮 API 参数解析、自纠错机制）
2. **Reasoning Experts** — 深度逻辑推理，自适应计算，数学、STEM 和多跳推理任务
3. **Interaction Experts** — 人类对齐与用户体验，细粒度指令遵循、事实幻觉抑制、安全机制

**MOPD 架构**整合三种专家能力，使最终模型兼具强大的 Agent 执行、深度推理和高质量交互。

## 评测

| 基准 | LongCat-2.0 | Gemini 3.1 Pro | GPT-5.5 | Claude Opus 4.6 | Opus 4.7 | Opus 4.8 |
|---|---|---|---|---|---|---|
| Terminal-Bench 2.1 | 70.8 | 70.7* | 73.8* | - | 71.7* | 78.9* |
| SWE-bench Pro | 59.5 | 54.2* | 58.6* | 57.3* | 64.3* | 69.2* |
| SWE-bench Multilingual | 77.3 | 76.9* | - | 77.8* | 80.5* | 84.8* |
| FORTE | 73.2 | 70.3 | 77.8 | 73.2 | 77.6 | 77.2 |
| BrowseComp | 79.9 | 85.9* | 84.4* | 84.0* | 79.3* | 84.3* |
| RWSearch | 78.8 | 76.3 | 85.3 | 81.3 | 79.3 | 77.3 |
| GPQA-diamond | 88.9 | 94.3* | 93.6* | 91.3* | 94.2* | 92.4 |

标 * 为外部报告值。LongCat-2.0 在 SWE-bench Pro (59.5)、FORTE (73.2)、RWSearch (78.8) 上超过 Gemini 3.1 Pro；在 Terminal-Bench 和 BrowseComp 上与顶级闭源模型有差距但具竞争力。
