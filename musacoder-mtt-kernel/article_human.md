<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>核心贡献</strong>：MusaCoder是首个在国产摩尔线程（Moore Threads）MUSA GPU上完成全栈训练的原生GPU核函数生成模型，从数据合成、SFT/RFT到执行反馈强化学习全部在国产硬件上闭环。<br><br>
- <strong>执行反馈闭环</strong>：自研MooreEval验证环境对编译、数值正确性、性能提速和「禁用PyTorch算子回调」做硬性校验，作为RL的可执行奖励信号，全程反作弊。<br><br>
- <strong>三项RL稳定机制</strong>：PrimeEcho锁定首轮生成质量、Buffered Dynamic Retry把全失败组变可学习样本、MirrorPop更准估计离策略漂移以稳定更新。<br><br>
- <strong>结果</strong>：MusaCoder-27B-RL在KernelBench严格协议下Pass@8达93.2%、Avg.@8达88.6%，超过Claude Opus 4.7（87.2%/77.3%），Faster Rate 15.0%，全部跑在64台MTT S5000上。
</div>
</div>

---

## 1引言

现代神经网络越来越依赖高度优化的GPU核函数（kernel）来榨干加速器硬件性能。NVIDIA的cuBLAS、cuDNN等厂商库和CUTLASS这类静态模板，在常规算子（GEMM、卷积）上接近最优，但**跟不上前沿模型里长尾算子融合（operator fusion）爆发式增长的节奏**。把高层张量计算直接翻译成优化的底层设备代码，这种「原生GPU核函数生成」变得越来越关键。最近大语言模型（LLM）在这方面展现出替代人工核函数工程的潜力。

但用LLM把PyTorch语义翻译成可执行的GPU核函数，这件事本身就极难。和通用代码生成不同，从零合成核函数的初始成功率极低：没有领域知识打底，现成LLM经常搞错GPU执行语义、数学推导和多维索引映射。同时，GPU核函数必须满足严格的correctness约束，要能编译、在边界情况下数值稳定、符合硬件执行语义。任何微小的逻辑或数学错误都会导致编译失败、非法内存访问或数值错误。

近两年，带执行反馈的强化学习（RL）在代码生成里被广泛采用，但把它搬到核函数生成上有三大难关。**第一，奖励稀疏**：生成核函数失败率极高，常常整组rollout全失败，几乎给不出有效学习信号。**第二，奖励黑客**：模型倾向于走捷径，用高层API回调（比如直接调现成PyTorch算子）冒充自定义核函数。**第三，验证昂贵且异步**：编译吃CPU，验证正确性和测性能吃GPU，两类资源不对称，同步执行会互相拖累。

## 2相关工作

GPU核函数生成已成为代码合成的重要方向。它比通用程序合成更苛刻：生成的核函数必须编译通过、数值正确、不触发被禁的高层框架回调，并在真实硬件上跑出可测量的提速。

现有高性能GPU计算分两派。一派依赖厂商库（cuBLAS、cuDNN）和模板框架（CUTLASS），它们在GEMM、卷积上表现极好，但要支撑快速演进的模型架构、新算子和融合计算模式，往往要大量人工工程。现代模型以SwiGLU、分组查询注意力（GQA）为代表的新计算模式，刷新速度常常超过厂商库的更新周期。

另一派是社区投入重兵的「裸金属代码生成」（原生核函数合成）：用深度学习编译器和领域特定语言（DSL）从计算图直接生成底层代码，以及用LLM驱动核函数生成加迭代修复。本文的MusaCoder属于后者，区别是它把整条训练链路（数据、SFT、RL、验证）完全建在国产MUSA加速器上，而非NVIDIA CUDA。

## 3数据合成流水线

现有的PyTorch-to-CUDA数据集适合KernelBench式warmup，但不足以支撑全栈后训练：长尾算子覆盖有限、缺少可复用的验证资产、且可能依赖厂商库实现而非原生核函数。MusaCoder把SFT数据构建成**分阶段的能力搭建过程**（图3）。

**阶段1：任务扩展与基础算子正确性增强。** 用开源任务、GitHub模块、NNSmith生成的图、定向基础算子变体、GPU核函数知识问答和自动生成的单元测试，扩大PyTorch-to-CUDA/MUSA任务覆盖。

**阶段2：结构化推理与空间逻辑约束。** 加入显式张量元数据和六步推理模板，减少在形状推断、标量公式、索引、边界处理和避免回调上的常见失败。

**阶段3：多轮RL准备与环境反馈解析。** 合成reviewer、性能分析、优化重写和多轮修复数据，让模型在RL之前就能读懂编译/运行时错误、正确性mismatch和性能反馈。

通过这三阶段，MusaCoder的SFT数据从简单的翻译对，演进成融合了算子知识、结构化推理、自动验证和执行反馈解析的丰富语料，为后续RFT和RL提供强而稳的初始化。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig03.png)
<span style="font-size:12px;color:rgb(153,153,153);">图3：SFT数据构建流水线的三阶段演进</span>

## 4方法

### 4.1总览

MusaCoder的训练分三个递进阶段：监督warmup、任务对齐、执行反馈驱动的强化学习（RL）。

先用上一节合成的多源数据做多任务监督微调（SFT），让模型熟悉PyTorch-to-CUDA/MUSA任务格式、常见原生核函数实现模式、CUDA扩展样板、bug review、反馈理解和性能profiling。这一阶段的目标不是直接搜最优核函数，而是为后续可验证训练阶段建立稳健的代码生成先验。

SFT之后做拒绝采样微调（RFT）把模型拉近最终任务。从SFT检查点出发，对每个PyTorch工作负载采样多个候选实现，用MooreEval过滤出「可解析、可编译、数值正确、满足任务约束」的正样本。和标准RFT只保留单一最优解不同，MusaCoder采用**保多样性过滤**：把同一prompt下生成的正确实现聚类，训练时从这个正样本池里随机采样监督目标。这既提升RFT样本正确性，又防止模型过早塌缩进一小撮固定实现模板，为后续RL保留必要的探索空间。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig02.png)
<span style="font-size:12px;color:rgb(153,153,153);">图2：MusaCoder训练流水线总览，从多源语料到执行反馈RL</span>

和开放式代码生成不同，核函数任务能通过真实编译、执行、正确性验证和性能测量拿到程序化反馈。MooreEval不仅验证候选代码能否编译、输出是否对齐PyTorch参考、是否取得实测性能增益，还执行严格的反黑客协议：通过静态规则和运行时profiling，检测被禁的PyTorch/aten::* 计算回调，防止模型在ModelNew.forward() 里直接调现成PyTorch算子来冒充自定义核函数。只有真正用原生核函数执行核心计算、且同时满足正确性与合法性约束的候选，才拿到正奖励。

基于MooreEval返回的结构化验证遥测，MusaCoder把核函数生成建模成可验证RL问题，依次执行单轮RL和多轮反馈RL。单轮RL直接优化模型在无反馈下首轮写出正确、合法、高效核函数的能力；多轮反馈RL进一步训练模型**智能体式地**利用真实执行反馈做迭代修bug和性能优化。为稳健编排这个闭环，论文提出三个关键机制：

- **PrimeEcho**：在利用多轮修复信号的同时，维持对首轮生成质量的优化压力，平衡最终成功率与推理效率。
- **Buffered Dynamic Retry（BDR）**：把全失败组转换成带执行反馈的可学习修复任务，缓解难样本上的奖励稀疏。
- **MirrorPop**：提出新的序列级离策略（off-policy）度量，更准确估计策略漂移幅度，从而可靠地屏蔽严重离策略样本，稳定RL更新。

三者合力保证RL期间的有效探索、目标一致性和更新稳定性。

### 4.2监督Warmup与任务对齐

**多任务SFT。** 不做单一的翻译任务，而是构建跨多个互补类别的多任务语料：核函数生成数据给直接合成能力；Reviewer数据提升语义错误检测和修bug；Profiling/NCU数据帮模型读懂性能反馈、定位执行瓶颈；知识问答强化GPU编程概念和PyTorch张量语义；优化重写数据教模型把低效实现改成优化核函数。多任务监督让模型不仅学会生成核函数，还学会分析、调试和优化它们。

**数据混合与先验诊断。** 训练前先建一个小规模先验诊断集，评估基础模型在不同算子族上的初始能力：用torch.profiler在一批PyTorch参考模型上跑单次前向，提取实际调用的aten::* 算子，按算子类别统计聚合、重采样，构建算子分布均衡的小评估集。然后用MooreEval测基础模型在各算子族上的编译率、正确率和性能指标。诊断结果指导SFT阶段的数据采样：对基础模型薄弱的算子族（卷积、reduction、归一化、softmax、广播、复杂索引）做上采样；对简单逐元素运算、激活等稳定任务适当下采样。

**多轮样本的损失掩码。** 多轮SFT样本里，历史轮次只作上下文输入，损失只在模型最后一轮的回答上计算。

**保多样性拒绝微调（RFT）。** 如前所述，从同一prompt的正确实现池随机采样监督目标，避免模板塌缩。

### 4.3 MooreEval：验证器与奖励环境

MooreEval是一个可扩展的、基于执行的评测环境，负责编译、验证、profiling和奖励生成的核函数。它的架构要点是**把编译和执行彻底解耦**：编译候选源码主要吃CPU核、主机内存、编译器进程和文件系统IOPS，而验证语义正确性和profiling执行效率独占GPU算力和设备显存。把这两类不对称操作绑在同一个同步线程里，必然造成严重的资源争用（GPU在编译瓶颈时空转，或CPU在长时间GPU执行扫掠中饿死）。MooreEval让两个资源域独立扩展、独立调度。

**结构化验证协议。** 严格要求的候选实现必须：成功解析并编译；在随机输入上通过shape、dtype和数值正确性检查，对齐PyTorch参考；且不在ModelNew.forward() 里调用被禁的PyTorch/aten::* 计算回调。只有同时过正确性和合法性检查的，才进入性能测试。性能测量在warmup后重复运行、用同步CUDA event计时，降低异步执行和初始化开销带来的方差。

**奖励设计。** 通过静态规则加运行时profiling检测回调作弊；只有真实原生核函数且正确又合法，才给正奖励。

**多轮训练反馈生成。** MooreEval返回的结构化遥测（部分正确性塑形、结构违规惩罚、实证提速奖励）既用于单轮评分，也作为多轮RL下一轮的修复信号。

### 4.4强化学习

**单轮RL warmup。** 第一阶段单轮GRPO，提升模型在零反馈下直接生成正确、合法、高效核函数的能力。

**多轮反馈RL。** 从单轮检查点进入多轮RL，引入MooreEval的在线反馈作为后续轮的修正信号。多轮rollout最多3轮模型回答，任一轮通过验证即提前终止。下图展示多轮RL的rollout过程和奖励设计。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig04.png)
<span style="font-size:12px;color:rgb(153,153,153);">图4：多轮RL的rollout过程</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig05.png)
<span style="font-size:12px;color:rgb(153,153,153);">图5：多轮奖励设计</span>

**PrimeEcho：首轮锚定的多轮奖励。** 多轮RL的策略梯度损失只在首轮模型回答上计算，后续轮只参与轨迹评估和奖励计算。PrimeEcho（默认 α=0.75）在利用多轮修复信号的同时，维持对首轮生成质量的优化压力，平衡最终成功率和推理效率。

### 4.5 RL稳定技术

**Buffered Dynamic Retry（BDR）。** 把全失败组转换成带执行反馈的可学习修复任务，从长尾失败样本里回收训练信号，缓解奖励稀疏。

**MirrorPop离策略序列掩码。** 标准离策略序列掩码在跨序列平均有符号对数比率（或相乘比率）时，正负偏离会互相抵消，让一个严重离策略的序列看起来接近策略内。MirrorPop提出新的序列级离策略度量，更准确估计策略漂移幅度，从而可靠屏蔽严重离策略样本，稳定RL更新。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig19.png)
<span style="font-size:12px;color:rgb(153,153,153);">图11：vanilla离策略序列掩码中的抵消现象，红token表示 ρt>1，绿token表示 ρt<1</span>

## 5实验

### 5.1训练细节

微调两个基础检查点：MusaCoder-9B从Qwen3.5-9B初始化，MusaCoder-27B从Qwen3.6-27B初始化，两者走同一训练流水线。优化器用AdamW，学习率1e-5，warmup比例3%，权重衰减0.01，bf16精度；最大序列长度40K，全局batch size 256，训练1个epoch。多轮SFT样本用损失掩码：历史轮只作上下文，损失只在末轮回答上算。SFT基于DeepSpeed的ZeRO/offload支持长上下文。

RL阶段用两阶段GRPO：单轮GRPO提升零反馈首轮生成能力；多轮RL从单轮检查点引入MooreEval在线反馈作修正信号，最多3轮、任一轮通过即终止。两轮rollout group size均为8，训练batch size 64，用SGLang异步模式；训练采样温度0.9、top-p 0.95，验证采样温度0.7、top-p 0.7。多轮RL默认用PrimeEcho奖励（α=0.75），策略梯度损失只在首轮回答上算。RL基础设施基于Megatron + SGLang：Megatron管actor和reference模型的分布式训练，SGLang管高吞吐异步rollout；27B模型引入张量并行分摊激活显存。RL学习率1e-6，warmup 0.1，权重衰减0.1，梯度裁剪0.5，最大prompt 8K、最大回答32K。

**全部实验跑在64台摩尔线程MTT S5000机器上，每台8张80GB加速卡。** 这一国产硬件集群稳健支撑了端到端训练闭环：长上下文SFT、异步rollout、MooreEval在线验证、GRPO策略更新。在国产硬件上同时跑通9B和27B模型的有监督微调和执行反馈强化学习，说明该平台不仅能做标准LLM微调，也能扛住涉及大规模代码生成、编译执行反馈和在线奖励计算的复杂RL负载。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig18.png)
<span style="font-size:12px;color:rgb(153,153,153);">图10：MooreEval架构，可扩展的、基于执行的核函数编译/验证/profiling/奖励环境</span>

### 5.2评测设置

在KernelBench基准上评测MusaCoder的PyTorch-to-CUDA/MUSA核函数生成能力，统一用MooreEval协议验证所有模型。和原版评测脚本不同，这里严格要求候选实现能解析编译、通过shape/dtype/数值正确性检查、且不在ModelNew.forward() 里调被禁的PyTorch/aten::* 回调。

每个任务采样8个候选（温度0.7），报告两类指标。**Pass Rate衡量正确性**：Pass@8表示8个候选里至少有一个过MooreEval验证；Avg.@8是8个样本里通过验证的平均占比。**Faster Rate衡量性能**：候选必须先过正确性和合法性检查，再相对对应基线取得超过1.1× 的运行时加速才计入「更快」。Faster Rate同时报告相对PyTorch eager和torch.compile的结果，1.1× 阈值过滤掉测量噪声带来的微小差异。

对比对象包括前沿代码模型（Claude Opus 4.7、GLM-5.1、Kimi K2.6、DeepSeek-V4-Pro/ProMax）和底层基础模型（Qwen3.5-9B、Qwen3.6-27B），全部在相同prompt模板、采样配置、验证脚本和硬件环境下评测。

### 5.3 KernelBench主结果

基础模型在严格可执行验证下原生核函数生成能力很有限：Qwen3.5-9B只有23.6% Overall Pass@8、7.05% Avg.@8；Qwen3.6-27B提升到67.2%/35.60%，但仍落后于强通用代码模型。监督对齐后，MusaCoder-9B-SFT把Overall Pass@8提到69.6%、Avg.@8到61.60%；MusaCoder-27B-SFT达84.8%/79.40%。说明SFT/RFT数据流水线显著提升了任务格式遵循和单样本正确性稳定性。

执行反馈RL进一步提升两个规模。**MusaCoder-9B-RL把Overall Pass@8从69.6% 拉到83.6%、Avg.@8从61.60% 到77.20%，在同一严格验证器下正确性已逼近Claude Opus 4.7。** 27B模型取得最佳整体正确性：MusaCoder-27B-RL达93.2% Pass@8、88.60% Avg.@8，相对Claude Opus 4.7在Pass@8上绝对领先6.0点、Avg.@8领先11.30点。Level 3（最难的复杂形状推理、索引、多算子负载）上优势更明显：Pass@8从Claude的54% 提到72%，Avg.@8从39.25% 提到65.75%。

Faster Rate比正确性更苛刻。基础模型极少产出加速核函数：Qwen3.5-9B相对Eager仅0.9%、相对Compile 0.5%；Qwen3.6-27B为3.4%/1.6%。MusaCoder-9B-RL性能已略超Claude Opus 4.7，达12.6%/7.9%（Claude 11.8%/7.5%）。**MusaCoder-27B-RL性能增益最强，Faster Rate达15.0%（vs Eager）/9.2%（vs Compile），相对Claude Opus 4.7绝对提升3.2和1.7点。** 整体说明执行反馈训练不仅提升功能正确性，也提升了生成「有可测量运行时收益的原生核函数」的概率。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig01.png)
<span style="font-size:12px;color:rgb(153,153,153);">图1：KernelBench性能对比</span>

### 5.4消融与RL训练分析

#### 5.4.1多轮RL评测指标

为区分模型的零样本生成能力和多轮反馈修复能力，多轮评测同时报告首轮指标和最佳轮指标。首轮准确率衡量零反馈下单次正确合成核函数的能力，是多轮RL优化中最关键的约束指标之一；最佳轮准确率衡量模型能否在最多T轮反馈内最终修复一个失败，主要反映模型利用MooreEval反馈持续修复的智能体能力。评测还报告首轮分数和最佳轮分数（保留部分正确性塑形、结构违规惩罚、实证提速奖励等细粒度遥测），以及「到成功所需轮数」的分布，观察策略是偏向即时零样本成功还是过度依赖延迟的反馈修复。

#### 5.4.2组件消融

表2报告主训练组件的消融。各组件都有贡献，但作用面不同：RFT改善监督任务对齐，单轮warmup给多轮RL更强初始化，PrimeEcho控制多轮奖励目标，BDR从难样本回收信号，MirrorPop稳定离策略更新。

去掉RFT，MusaCoder-SFT的Overall Pass@8从84.8% 降到82.6%、Avg.@8从79.40% 降到75.10%（分别掉2.2和4.30点），Faster Rate vs Eager从6.3% 降到5.8%、vs Compile从4.1% 降到3.8%。去掉单轮warmup，27B-RL从93.2%/88.60% 降到90.8%/84.25%。去掉PrimeEcho降到88.4%/83.50%，去掉BDR降到88.6%/83.20%，去掉MirrorPop降到86.0%/80.75%。**每一项机制都在最终正确性上有可测量的正向贡献，其中MirrorPop对稳定性的影响最大。**

| 设置 | Overall Pass Rate | Overall Faster Rate | Pass@8 | Avg.@8 |
|------|------|------|------|------|
| MusaCoder-SFT | 84.8 | 79.40 | — | — |
| w/o RFT | 82.6 | 75.10 | 5.8 | 3.8 |
| MusaCoder-RL | 93.2 | 88.60 | 15.0 | 9.2 |
| w/o Single-turn Warmup | 90.8 | 84.25 | 14.2 | 8.6 |
| w/o PrimeEcho | 88.4 | 83.50 | 13.9 | 8.4 |
| w/o Buffered Dynamic Retry | 88.6 | 83.20 | 13.8 | 8.2 |
| w/o MirrorPop | 86.0 | 80.75 | 13.1 | 7.8 |

#### 5.4.3单轮RL warmup的作用

单轮warmup给多轮RL提供了更强的初始化，避免模型在毫无首轮能力时直接进入多轮修复、被奖励稀疏拖垮。

#### 5.4.4多轮RL训练动态

下图展示多轮评测指标的各项面板：包括轮次数分布、奖励、以及首轮与最佳轮的正确性对比。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig06.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7（a）：多轮评测中模型回答的轮次数分布</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig07.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7（b）：多轮评测中的奖励曲线</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig08.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7：跨KernelBench级别的多轮评测指标（score）</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig09.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7：跨KernelBench级别的多轮评测指标（accuracy）</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig10.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7：跨KernelBench级别的多轮评测指标（到验证通过的轮数）</span>

图8的BDR消融显示不同反馈设置下训练奖励的走势。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig11.png)
<span style="font-size:12px;color:rgb(153,153,153);">图8：不同反馈设置下Buffered Dynamic Retry的消融</span>

图9的MirrorPop训练动态（训练奖励、熵、梯度范数、响应长度裁剪比、离策略度量）显示，MirrorPop相比vanilla形式更稳地控制离策略更新。

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig12.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（a）：MirrorPop训练动态，训练奖励</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig13.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（b）：MirrorPop训练动态，熵</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig14.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（c）：MirrorPop训练动态，梯度范数</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig15.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（d）：MirrorPop训练动态，响应长度裁剪比</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig16.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（e）：离策略度量，Vanilla形式</span>

![](D:/06_Hermes/articles/musacoder-mtt-kernel/fig17.png)
<span style="font-size:12px;color:rgb(153,153,153);">图9（f）：离策略度量，MirrorPop形式</span>

#### 5.4.5 BDR的效果

表3的BDR效果显示，从单轮RL最佳检查点继续训练时，BDR把全失败组转成可学习修复任务，回收了长尾难样本的训练信号。

#### 5.4.6 MirrorPop的效果与MUSA评测

表4的MUSA KernelBench评测显示，在摩尔线程MUSA原生基准上，MusaCoder同样取得领先的正确性和性能，验证了整条流水线在国产硬件上的端到端有效性。MUSA基准下各组件趋势与CUDA侧一致，MirrorPop对离策略稳定性的增益在国产硬件上同样成立。

## 6结语

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
MusaCoder真正的看点不是「又一个核函数生成模型」，而是它把数据合成、SFT/RFT、执行反馈RL、验证器整套链路首次完整地跑在了国产MUSA硬件上，用64台MTT S5000扛住了编译执行反馈闭环，这比单点指标更有产业意义。<br><br>
MooreEval的「反回调作弊」硬约束是它可信的关键：没有这层，模型大可以偷调现成PyTorch算子冒充核函数，benchmark数字会虚高却毫无价值。<br><br>
三项RL稳定机制（PrimeEcho/BDR/MirrorPop）值得单独关注，它们解决的是「奖励稀疏 + 离策略不稳定」这个把核函数RL训崩的老大难问题，方法论上对其它执行反馈RL场景也有迁移价值。<br><br>
局限在于评测仍集中在KernelBench，且Faster Rate绝对数值偏低（最高15%），说明「能跑对」和「跑得快」之间仍有巨大鸿沟，离真正替代手写优化核函数还有距离。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OHfR5G47CWXXNjhFcH3HBw" target="_blank" data-linktype="2">GPT-Realtime 2.0只用声音控制电脑</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/QzUgNaCON_w0ZxTyYnDyDw" target="_blank" data-linktype="2">号外！OpenClaw之父刚刚开源Agent Loop工程：每5分钟自动修Bug</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/FkaboLbPXA36kHkDgv8aSQ" target="_blank" data-linktype="2">Interpreter Skills：当Agent Skill从说明书变成可执行代码</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Gjvh6axvYjjgRFDCNFwwew" target="_blank" data-linktype="2">国内用Claude Opus的秘密：美国田纳西-非洲吉布提-深圳写字楼,扒一扒灰产背后的经济学</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/olxLm3almopaba6J2JeFrA" target="_blank" data-linktype="2">Anthropic：如何用Claude实现95%自动化数据化分析</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/crfkhSIuMZJxjNA0Md8dXw" target="_blank" data-linktype="2">李飞飞：世界模型的功能分类</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/4Iz5SjE4D240EL4MmKrWZQ" target="_blank" data-linktype="2">OpenAI Dreaming记忆系统：从记住你到理解你</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到4GHz麒麟，一张时间表看清未来十年芯片路线</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2606.04847v1</span>