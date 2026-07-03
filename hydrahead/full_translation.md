# HydraHead：从头级功能异质性到专用注意力杂交

## 1 引言

大语言模型（LLM）正从静态问答系统向自主 Agent 转型，这对上下文窗口扩展提出了前所未有的要求。然而标准 Full Attention（FA）的二次复杂度（O(T²)）仍是刚性计算瓶颈。Linear Attention（LA）范式虽提供线性复杂度，但常遭遇"表达力崩塌"——难以维持高精度检索。

这一张力催生了大量混合架构。主流路线是层间设计（layer-wise），在不同层交错不同注意力机制——FA + softmax attention、sliding-window attention 等。部分工作也指出，训练含 LA+FA 的混合模型仍然困难，最终聚焦于 full- 或 sparse-attention 变体，表明注意力杂交的设计空间仍待探索。

**可解释性提供的洞察：** attention head 在功能和重要性上呈现显著多样性。在单个层内，只有少量 head 的 logit 贡献显著，其余近乎 inactive。这些检索关键 head 集中在深层。相比之下，层输出相似度矩阵呈平滑块状结构，缺乏足够的判别信号来指导不同注意力机制的放置。因此 head 是注意力杂交的天然单元：同一层内的不同 head 处理相同输入，但通过不同机制在共享表示空间中运作。

**HydraHead 核心思路：**
1. 用可解释性技术识别关键 head，只保留 FA 给这些 head
2. 在每层内混合 FA 和 LA（GDN），引入 head-wise scale-normalized fusion 缓解异质注意力干扰
3. 三段式迁移学习：参数继承 + 全局蒸馏 + 长上下文微调

**主要发现：**
- HydraHead 在长上下文中达到 SOTA，同时在困难推理任务上 >10% 优于层间杂交 baseline
- 可解释性引导的头选择在极高 LA:FA 比率（如 7:1）下仍能匹配 3:1 层间杂交的性能
- 仅 15B tokens 训练即在 512K NIAH 上比预训练 baseline 提升 69%，接近 Qwen3.5 水平

## 2 相关工作

### 2.1 机械可解释性与头级分析

attention head 是功能有意义的单元——Voita 等识别出三类专用 head；Michel 等表明大多数 head 可被剪枝；Clark 等揭示了头对特定语法关系的注意。Wang 等将 GPT-2 small 的 IOI 电路分解为 26 个 head（7 个功能类）。

### 2.2 线性注意力

从 SSM 视角（Mamba、Mamba-2、Mamba-3）到 fast-weight memory 视角（Linear Transformer、Gated Delta Networks），再到最新解耦擦除/写入的 Gated Deltanet-2。纯线性注意力受限于固定维度循环状态，推动混合设计。

### 2.3 混合 Transformer

三种范式：
- **层间杂交**：MiMo、MiniMax-M1、Qwen 等使用配置化的层间比例；GLM-5 用 NAS 搜索最优布局
- **Token 级杂交**：STILL 用 saliency-based gating 决定每个 token 使用 FA 还是 LA，但 >32K 上下文未报告结果，且稀疏注意力需要完整 KV cache
- **头级杂交**：DuoAttention、Elastic Attention 做 per-head 选择（FA + 稀疏注意力）；Hymba 做 per-head 混合（并行 FA + Mamba 分支后逐元素平均）

### 2.4 驯服 Transformer 到混合架构

跨架构蒸馏方法（T2R、RADLADS、MOHAWK、LoLCATs）为从预训练 FA 模型迁移到混合架构提供了基础。近期工作向多阶段管道和初始化策略发展（HedgeMamba、KL-Guided）。HydraHead 以 HALO 为基础，扩展其高效蒸馏以支持 head 级混合结构。

## 3 预备知识

### 3.1 因果修补方法

**Activation Patching**：替换目标 head 的输出为 corrupted 版本，测量读出的变化。**Path Patching**：限制干预到特定计算路径。

### 3.2 分组查询注意力（GQA）

多头注意力以 GQA 实现，query heads H 被分为 G 组（G<H），每组共享一个 key-value head。

### 3.3 基于 Gated DeltaNet 的线性注意力

标准线性注意力维持矩阵值循环状态 S_t，但缺乏遗忘机制。GDN 引入标量遗忘门 α_t 和学习率 β_t，在线梯度下降视角下更新状态。

## 4 方法

### 4.1 基于因果干预的头重要性评估

三步：
1. Activation patching 测量每头的直接因果效应（接收器）
2. Path patching 追溯上游贡献（发送器）
3. 跨能力融合（多 NIAH 子探测）

关键设计：对称令牌替换作反事实构造；指数衰减的 span-level readout（λ=0.9）；任务一致性因子 κ 降低仅在单一子探测上高分的 head。

### 4.2 头级杂交

**头划分**：将 H 个 query head 分为 FA 组（ℋ_F）和 GDN 组（ℋ_L）
**并行分支计算**：各自独立处理
**Head-wise Scale-normalized Fusion**：每头独立 RMSNorm → 按原始索引 concatenate → 可学习 head-wise 缩放向量 γ 自适应调整贡献
**分支特定优化**：FA 去掉 RoPE 换 log-scale 系数 + 辅助门控分支；GDN 集成 RoPE + 扩张为 MHA 配置

### 4.3 高效混合迁移学习

三段式：
1. **Stage 1**：参数迁移 + 逐层隐藏状态对齐（MSE）
2. **Stage 2**：全局 logits 蒸馏（KL 散度）
3. **Stage 3**：长上下文微调（NTP）

## 5 实验

### 5.1 实验设置

基础模型：Qwen3-1.7B。默认 25% FA / 75% GDN。训练数据：FineWeb-Edu。三段式配置：Stage1（512ctx, 0.3B tokens）、Stage2（512ctx, 1.0B tokens）、Stage3（16384ctx, 1.0B tokens）。

评估：RULER（16K-256K，分 Native 和 Extended 区间）+ 通用推理（ARC、HellaSwag、MMLU、GSM8K、MBPP、BBH 等，分 Easy 和 Hard 两档）。

### 5.2 混合架构对比

HydraHead 在长上下文和通用推理之间达到最佳平衡。相比层间杂交，在困难推理任务上 >10% 优势，同时长上下文性能更优。

### 5.3 结构组件消融

渐进式集成模块：Base Hybrid → +FA NoPE & Scale（长上下文提升显著，推理下降）→ +GDN RoPE → +FA Gate → +GDN MHA → +Query Decomposition（最优配置）。

### 5.4 特征融合设计

对比三个变体：
- 直接拼接（w/o Norm）→ 性能严重下降
- Head-wise Scale Modulation（最优）
- Head-wise Gated Competition（仅原上下文 Multi-Key 有优势）

FA 和 GDN 特征存在显著幅值偏移（深层 GDN RMS 高达 FA 的 6.2 倍），RMSNorm 归一化是关键。

### 5.5 可解释性筛选的有效性

5 种选择策略对比：
- Fixed Allocation（固定分配）
- Layer-wise Random
- Global Random（最差）
- Layer-wise Interpretability
- **Global Interpretability（最优）**

可解释性筛选使 FA 资源集中在真正关键的层和头上。

### 5.6 高混合比的影响

Global-Interp-C（每层至少保留 1 个 FA head）在高比率下提升显著。7:1 比率在长上下文上匹配 3:1 层间杂交，通用推理 +9.66%。

### 5.7 可解释性引导头选择的分析

三个关键发现：
1. **重要性评分稳定** — 仅 6 个校准样本即可稳定排名
2. **检索是 head 定域的，不是 layer 定域的** — 基尼系数平均 0.622，仅 ~6.5% head 是关键检索节点，且分散在各层
3. **因果忠实性验证通过** — 按重要性降序 knockout 准确率快速下降，随机 knockout 基本不变

### 5.8 训练配置优化

扩大数据量和序列长度后 HydraHead 全面获益，层间杂交 HypeNet 提升有限。

### 5.9 扩展到更多训练 tokens

15B tokens 训练后对比开源模型：
- 256K context：HydraHead 在 RULER Single 94.53%/Multi-Key 52.70%，远超所有混合模型
- 通用推理：平均 50.62，最优的 Jet-Nemotron-2B 虽然 +9.69，但在 ≥64K context 差距超过 50%

## 6 结论

本文提出 head 级混合注意力架构，通过可解释性引导的头选择 + head-wise scale-normalized fusion + 三段式迁移学习，在仅 15B tokens 训练下实现接近 Qwen3.5 的长上下文性能，同时保持通用推理能力。

## 局限性与未来工作

模型规模需扩展到 7B/13B+；训练数据量需提升数量级；可解释性选择过程的自动化和任务无关化；支持更多注意力变体的混合（2种以上）。
