# 完整翻译：Improving DeepEP MoE Load Balance in SGLang with Waterfill and LPLB

## TL;DR

混合专家（MoE）模型依赖专家并行（EP）在多个 GPU 上扩展推理。在 SGLang 中，DeepEP 和 EPLB 提供 EP 下的高性能服务，但 token 路由不均衡导致 rank 负载不均。

本博客介绍两种调度时负载均衡特性：

- **Waterfill**：轻量级共享专家负载均衡方法，通过 DeepEP 调度共享专家到低负载 rank。在两台 Hopper GPU 上，DeepSeek-V3/R1 风格负载吞吐提升 +1.48% 至 +4.66%。DeepSeek V4 最佳点从 49,253 tok/s 到 51,677 tok/s（+4.92%）。
- **LPLB**：基于线性规划的冗余专家副本负载均衡器，解决逐层调度优化问题。同配置下吞吐提升 +0.84% 至 +7.34%。

## 引言

大型 MoE 模型（DeepSeek-V3/R1、DeepSeek V4）使用稀疏专家激活增加模型容量，推理时 EP 将专家分布到 GPU 上并将 token 路由到对应 rank。这减少了单 GPU 内存压力，但引入核心问题：**路由器不生成完美均衡的专家流量**。当某些专家收到远多于其他专家的 token 时，EP 组等最忙 rank。静态放置（如 EPLB）可改善长期分布，但单批次的剩余不均衡依然存在。

SGLang 的两种调度时方法：**Waterfill**（聚焦共享专家路径）和 **LPLB**（聚焦跨冗余副本 token 路由）。

## 背景：DeepEP MoE 推理中的负载不均衡

DeepEP 为 EP 提供优化的 token 调度和合并内核。典型 DeepSeek 风格 MoE 层中，每个 token 路由到几个**路由专家**，部分模型还包括**共享专家**（对每个 token 都应用）。

路由专家是稀疏的（不同 token 选不同专家），共享专家是密集的（整个批次都有），冗余专家（EPLB 引入）提供多个物理副本，创造了调度时均衡机会——不改变模型逻辑即可选择哪个物理副本处理 token。

静态放置不消除所有运行时不平衡。Waterfill 和 LPLB 都旨在减少调度时不均衡，保持模型语义。

### Waterfill 调度策略

如果共享专家总是在每个 rank 本地计算，过载 rank 继续过载，轻载 rank 帮不上忙。Waterfill 将共享专家视为可调度槽位：路由专家选定后估计每 rank 路由负载，将共享专家分配给低负载 rank——类似往不平坦容器中倒水。

算法：1) 统计每 EP rank 的路由负载。2) 用该计数作负载分数——动态模式下 SGLang 先跑一次 EP 组集体通信以使用全局路由负载向量加本地批次大小。3) 为每个 token 加一个共享槽位，计算目标水位线 H = ceil((sum(L_r) + N) / R)。4) 低于水位线的 rank 有 slack：S_r = max(H - L_r, 0)。5) 每个 token 以正比于 slack 的概率采样目标 rank，带小的本地 rank 偏好。全零时回退到较轻的候选 rank。

通信权衡：若每个 token 可发共享工作到任意 EP rank，均衡自由度更高但 all-to-all 通信可能增加。通信保守的候选集将共享专家保持在 token 已访问的 rank 上（源 rank 为回退）。全 rank 模式提供更多自由度。

![img1](img1.png)
图 1. Waterfill 将共享专家工作从过载 rank 转移到较轻的 rank

### 共享专家融合作为使能机制

共享专家融合将共享专家表示为同一 DeepEP MoE 布局中的另一个专家槽位。DeepSeek V3/R1 中每个 rank 保留额外共享槽位，使路由专家和共享专家共享同一 dispatch、grouped-GEMM 和 combine 流程。Waterfill 拆为两个 PR：[#20089](https://github.com/sgl-project/sglang/pull/20089)（固定本地分配融合）和 [#19290](https://github.com/sgl-project/sglang/pull/19290)（负载感知调度）。

## LPLB：基于 LP 的冗余专家副本负载均衡

EPLB 为热门逻辑专家创建冗余副本，默认均匀分配各副本 token。当实时批次偏离校准分布时（单批次集中不同专家、数据集漂移、再平衡周期长），均匀分配不再最优。LPLB 在调度时查实际每专家 token 数，**最小化每 rank 最大负载**——不移动权重、不改 top-k，仅选择各副本接收的流量量。

LP 公式：目标最小化峰值 M（所有 rank 最大负载）。每 rank 约束：(冗余副本负载)+(单副本固定负载)+slack=M。冗余专家守恒：各副本负载之和=专家总观察负载。决策变量仅为复制专家的每副本负载、每 rank slack 和 M——单副本非变量，LP 规模只与冗余专家数和 rank 数成正比。

约束矩阵离线部分（副本→逻辑映射、每 rank 副本所有权、slack/−M 列）启动时预计算一次。每批次只更新右侧（负载数据）。Big-M 列保持系统可行。

DP-attention 中不同 EP rank 运行不同前向模式，无 rank 见全局分布。方案：每 rank 统计本地每逻辑专家 token → 所有 EP rank all-reduce（空闲贡献零）→ 每 rank 从相同输入独立求解同一 LP → 相同解，不需广播。LP 通过融合 IPM 内核在 GPU 上求解（`cuSOLVERDx`/`cuBLASDx`），每批次三个 CUDA kernel 启动完成。

LP 返回的每副本划分归一化为概率分布（`log2phy_prob`），替换现有的均匀随机 `dynamic` 策略。

![img2](img2.png)
图 2. LPLB 将复制专家流量向较轻的 rank 转移

### Waterfill vs LPLB

| 维度 | Waterfill | LPLB |
|------|-----------|------|
| 目标 | 共享（密集）专家 | 已复制的路由专家 |
| 决策 | 哪个 rank 执行共享槽位 | 复制专家 token 如何分配给各副本 |
| 方法 | 基于 rank 负载的低谷填充启发式 | 每层 min-max LP，GPU 求解 |
| 前提 | 共享专家融合 | 存在 EPLB 冗余副本 |
| 成本 | 接近零 | 每层一次 all-reduce + LP 求解 |

互补关系：Waterfill 消共享专家不均衡，LPLB 消路由副本间不均衡。

LPLB 在中等规模服务中最有效——流量有结构性、批次偏离离线分布但结构足够使最优分配降低峰值。批次极大高度多样时剩余不均衡少；流量基本不变时均匀分配已足够。

## 评估

DeepSeek-V3/R1（FP8，两台 Hopper，16 GPU，TP16/DP16/EP16，DP attention，DeepEP normal）

| 数据集 | 基线设置 | 基线 | Waterfill | 增益 | LPLB | 增益 |
|--------|----------|------|-----------|------|------|------|
| MMLU | 无 EPLB | 28,968 | 29,697 | +2.52% | — | — |
| MMLU | EPLB red0 | 30,392 | 31,424 | +3.40% | 29,938 | -1.50% |
| MMLU | EPLB red16 | 30,638 | 31,483 | +2.76% | 31,104 | +1.52% |
| MMLU | EPLB red32 | 30,714 | 31,169 | +1.48% | 31,547 | +2.72% |
| GPQA | 无 EPLB | 23,201 | 24,283 | +4.66% | — | — |
| GPQA | EPLB red0 | 26,322 | 26,970 | +2.46% | 25,899 | -1.61% |
| GPQA | EPLB red16 | 26,124 | 26,683 | +2.14% | 26,350 | +0.86% |
| GPQA | EPLB red32 | 25,975 | 26,655 | +2.62% | 26,193 | +0.84% |
| GSM8K | 无 EPLB | 29,649 | 30,892 | +4.19% | — | — |
| GSM8K | EPLB red0 | 33,058 | 34,529 | +4.45% | 32,744 | -0.95% |
| GSM8K | EPLB red16 | 34,026 | 35,226 | +3.53% | 35,474 | +4.26% |
| GSM8K | EPLB red32 | 33,988 | 35,070 | +3.19% | 36,482 | +7.34% |

![img3](img3.png)
图 3. Waterfill 在 MMLU/GPQA/GSM8K 上一致提升吞吐

![img4](img4.png)
图 4. LPLB 在 red16/red32 时提升吞吐，red0 仅有开销

DeepSeek V4 Flash（MMLU 14,042 prompt，batch=512，concurrency=128）

| 配置 | 基线 | Waterfill | 增益 |
|------|------|-----------|------|
| 无 EPLB | 45,951 | 47,876 | +4.19% |
| EPLB red0 | 49,253 | 51,677 | +4.92% |
| EPLB red16 | 50,006 | 51,655 | +3.30% |
| EPLB red32 | 50,167 | 51,813 | +3.28% |

![img5](img5.png)
图 5. DeepSeek V4 Flash 上 Waterfill 一致有效

精度验证：Waterfill 不改逻辑 top-k，仅改共享专家物理 placement。LPLB 不改 top-k，所有副本同权重，与 EPLB/dynamic 相同的精度保证。

## 如何使用

**Waterfill：** `--enable-deepep-waterfill`（需 `--moe-a2a-backend deepep` + `--enable-dp-attention`）。DeepSeek V4 通过 `HashTopK` 路径支持（#25391）。

**LPLB：** `--ep-dispatch-algorithm lp`（需 `--ep-num-redundant-experts` 创建冗余副本）。无冗余专家时 LPLB 无收益。

## 致谢

感谢 SGLang 维护者和审阅者的讨论与集成支持：[#20089]、[#19290]、[#25391]、[#24515]。NVIDIA 团队（Xuting Zhou、Fei Liang、Aichen Feng）和 SGLang 团队（Cheng Wan）。感谢 DeepSeek 开源 LPLB（deepseek-ai/LPLB）。
