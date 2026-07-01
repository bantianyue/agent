# DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation

## 基于置信度调度的半自回归推测解码

辛晨1,2,∗，余兴凯2,∗，邵晨泽2,∗，李佳时2,∗，熊云帆2,∗
钱毅2，朱嘉琦2，马士荣2，张小康2，叶嘉晟2，陈钦宇2，
邓承奇2，余吉平2，代大迈2，张正彦2，魏宜轩2，谭宜轩2，
杨文凯2，徐润欣2，吴宇2，徐哲安2，王玄宇2，陈沐阳2，
田瑞2，毕晓2，郝哲文2，陈少远2，曹焕琦2，张文涛2，
徐安义2，张会帅1，赵东岩1，梁文峰2

1北京大学
2DeepSeek-AI
{chengxin, xingkai, shaochenze, js.li, yunfanxiong}@deepseek.com

## 摘要

推测解码通过将草稿生成与目标验证解耦来加速大语言模型（LLM）推理。虽然最近的并行草稿模型能够在单次前向传播中高效地生成长token序列，但由于缺乏token间依赖关系，它们遭受着快速的接受率衰减问题。此外，不加区分地验证这些扩展块会将关键的批次容量浪费在高拒绝风险的token上，严重损害高并发服务系统的吞吐量。我们提出DSpark，一个将高吞吐并行生成与自适应、负载感知验证相统一的推测解码框架。为了保持草稿质量，DSpark采用半自回归架构——将并行骨干网络与轻量级序列模块相结合——以引入块内依赖建模并缓解后缀衰减。为了优化系统效率，DSpark采用置信度调度的验证机制，基于估计的前缀生存概率和引擎特定的吞吐量配置文件，动态地为每个请求调整验证长度。在跨多个领域的离线基准测试中，DSpark在接受长度上显著超越了最先进的自回归和并行草稿模型。当部署在DeepSeek-V4服务系统中面对真实用户流量时，DSpark成功缓解了验证浪费。与已建立的生产基线（MTP-1）相比，DSpark在匹配的吞吐水平下将每用户生成速度提升了60%-85%。更重要的是，通过在严格的交互性约束下防止严重的吞吐量退化，它实现了以前无法达到的性能层次，移动了我们服务系统的Pareto前沿。为了促进社区的进步，我们开源了DSpark检查点以及DeepSpec，一个算法驱动的推测解码训练仓库。

## 1. 引言

大语言模型（LLM）以自回归方式生成文本：每个新token都需要以所有前面token为条件进行一次完整的前向传播，这使得推理延迟与输出长度成正比。由此导致的低GPU利用率和用户感觉到的高等待时间构成了生产级LLM服务的主要瓶颈，特别是在对延迟敏感的场景中，如实时对话助手和多轮Agent工作流。推测解码（Chen et al., 2023; Leviathan et al., 2023）提供了一种原则性的解决方案：一个轻量级的草稿模型提出一个候选token块，然后完整尺寸的目标模型通过拒绝采样在一次前向传播中验证整个块，接受与目标分布一致的最长前缀并附加一个奖励token。由于验证是并行的，且接受规则精确地保持了目标分布，推测解码在没有任何质量损失的情况下加速了生成。

草稿模型的设计决定了草稿延迟与接受率之间的权衡。早期的草稿模型是自回归的（Cheng et al., 2024; Li et al., 2024b），每个位置都以前面采样的token为条件。然而，它们的草稿延迟随块大小线性增长，迫使这些方法使用短块和浅层架构。为了打破这种顺序瓶颈，并行草稿模型（Cai et al., 2024; Chen et al., 2026; Liu et al., 2026a）作为引人注目的替代方案出现：所有草稿位置在单次前向传播中产生，使得草稿延迟几乎与块大小无关。这种结构优势理论上允许并行草稿模型高效地生成更长的草稿块。

然而，充分释放大型并行草稿块的潜力引入了两个关键瓶颈——一个在生成质量方面，另一个在系统效率方面。首先，由于并行草稿模型独立预测每个位置，它们无法建模块内的token间依赖关系。这种独立性导致多模态冲突和后期的快速接受率衰减（Gu et al., 2018; Huang et al., 2022b）。其次，确定最优验证长度仍然是一个挑战。虽然并行生成可以轻松产生长草稿块，但不加区分地验证所有提议的token会降低系统吞吐量，特别是在高并发工作负载下（Hu et al., 2026; Liu et al., 2024c）。理想的验证长度沿两个维度变化。数据方面，像代码这样的结构化请求自然比开放式对话维持更高的接受率（Abramovich et al., 2026; Xia et al., 2024）。系统方面，在轻负载下验证额外的token几乎免费。然而，在重负载下，验证高拒绝风险的token会占用关键批次容量，而这些容量本可以用于服务其他活跃请求（Liu et al., 2024b; Wu et al., 2025）。

为了解决这些瓶颈，我们提出了DSpark，一个将高吞吐并行生成与自适应、负载感知验证相统一的推测解码框架。其核心是，DSpark旨在通过两种互补机制来解决草稿生成和验证中固有的权衡。

*   首先，为了克服token间依赖关系的缺失，DSpark采用了一种半自回归架构。它保持计算开销大的草稿骨干网络完全并行，仅附加一个轻量级串行输出头来注入局部转移信息。这种设计保留了并行模型的草稿速度，同时显著缓解了后缀衰减。
*   其次，为了解决系统级瓶颈，DSpark采用了置信度调度的验证机制。通过将一个估计每个位置前缀生存概率的置信度头与一个硬件感知调度器相结合，DSpark动态地为每个请求定制验证长度。该调度器利用实时引擎吞吐量配置文件，将目标验证预算仅引导至具有最高预期收益的token。

我们通过受控的离线基准测试和生产规模的在线部署对DSpark进行了广泛评估。在受控的离线基准测试中——涵盖数学推理、代码生成和日常对话——DSpark持续优于强基线。具体来说，在Qwen3-4B、8B和14B目标模型（Yang et al., 2025）上，它相对于自回归的Eagle3（Li et al., 2026b）将宏平均接受长度提升了30.9%、26.7%和30.0%，相对于并行的DFlash（Chen et al., 2026）分别提升了16.3%、18.4%和18.3%。在顶级指标之外，我们细粒度的逐位置分析揭示了不同草稿模型的独特生成特征，实证地展示了DSpark如何成功地将并行模型的高初始token容量与自回归模型的后缀连贯性相结合。

除了离线评估，我们还将DSpark部署在DeepSeek-V4（DeepSeek-AI, 2026）服务系统中，以评估其在真实用户流量下的性能。与之前的MTP-1生产基线（DeepSeek-AI, 2024）相比，DSpark显著拓宽了系统的操作范围。具体来说，在匹配的总吞吐能力下，它持续地将每用户生成速度提升60%-85%（V4-Flash）和57%-78%（V4-Pro）。此外，在严格的SLA（服务等级协议）条件下——例如Flash的120 TPS和Pro的50 TPS——基线容量严重恶化，而DSpark减轻了验证开销以维持稳健的吞吐量。通过克服这一性能悬崖，DSpark解锁了以前无法实现的严格交互性层次，有效地移动了LLM服务的Pareto前沿。

为了促进开源社区的集体进步，我们将公开我们的成果。具体来说，我们发布了针对DeepSeek-V4-Flash（预览版）和DeepSeek-V4-Pro（预览版）模型的训练好的DSpark检查点。此外，我们开源了DeepSpec，一个算法驱动的训练仓库，包括Eagle3、DFlash和DSpark。这些成果旨在支持关于高效LLM服务的进一步研究。

## 2. 背景

### 2.1. 推测解码

自回归语言模型每次前向传播生成一个token，使得推理延迟与输出长度成正比。推测解码（Chen et al., 2023; Ge et al., 2022; Leviathan et al., 2023）通过轻量级草稿模型M_d加速目标模型M_t的推理。在每个解码周期中，草稿模型提出γ个候选token x_1, ..., x_γ。目标模型在单次前向传播中验证所有候选，接受与其自身分布一致的最长前缀。

具体来说，在每个草稿位置k，目标模型计算其自身分布p^t_k并与草稿分布p^d_k进行比较。token x_k以概率min(1, p^t_k(x_k)/p^d_k(x_k))被接受。验证从左到右进行：在位置k的第一次拒绝会丢弃所有后续token x_{k+1}, ..., x_γ，无论其质量如何。

设τ表示每个周期接受的token数，T_draft和T_verify分别表示草稿和验证过程的实际时间。每个生成token的平均延迟为：

L = (T_draft + T_verify) / τ    (1)

因此，加速归结为三个杠杆：降低T_draft（更快地草稿），提高τ（更好地草稿），或减少有效的T_verify（更智能地验证）。

### 2.2. 草稿模型架构

草稿模型的设计决定了T_draft和τ如何权衡。现有方法分为两类。

**自回归草稿模型。** 自回归草稿模型顺序地生成草稿token，每个位置以前面采样的token为条件（DeepSeek-AI, 2024; Li et al., 2024b,c, 2026b; Zhang et al., 2025）。这种显式依赖提供了强大的建模能力，但草稿成本随块大小线性增长：T_draft ∝ γ，这迫使自回归草稿模型使用小的γ和浅层架构以保持T_draft较低。为了补偿短块，基于树的验证（Miao et al., 2024）将候选扩展为树并通过树注意力验证多条路径，但大量验证token降低了总体服务吞吐量。

**并行草稿模型。** 并行草稿模型在单次前向传播中产生所有γ个草稿token，使得T_draft几乎与块大小无关（Cai et al., 2024; Chen et al., 2026; Li et al., 2025a; Liu et al., 2026a; Sandler et al., 2026）。这允许使用更大的块（例如，γ=16）而不会成比例地增加延迟。

其中，DFlash（Chen et al., 2026）是一个最先进的并行草稿模型，它以其草稿模型为条件，从目标模型（KV注入）中提取丰富的上下文特征。在预填充期间，来自一组目标层{l_1, ..., l_m}的隐藏状态被拼接并投影到草稿隐藏空间中：

H_ctx = RMSNorm(W_c [H^(l_1); ...; H^(l_m)])    (2)

其中W_c ∈ R^{d×md}是一个共享投影。这些上下文特征通过沿键和值的序列维度与草稿块表示拼接，注入到每个草稿层中：

K_i = [W^K_i H_ctx; W^K_i H_d],
V_i = [W^V_i H_ctx; W^V_i H_d]    (3)

块内的所有位置彼此之间以及与注入的目标上下文之间进行双向注意力计算。草稿模型共享目标模型的嵌入层和语言模型头（两者均已冻结）。它接受一个锚点token后跟γ个mask token嵌入作为输入，并在单次前向传播中为所有mask位置产生logits。由于无论块大小如何，草稿只需要一次前向传播，DFlash在相同的延迟预算下可以比自回归草稿模型承担更深的架构和更大的块。

## 3. 架构

DSpark的概览如图1所示。回顾公式1，推测解码的每token延迟为L = (T_draft + T_verify)/τ。自回归草稿模型实现了高τ但付出了T_draft ∝ γ的代价；并行草稿模型将T_draft压缩到单次前向传播，但因每个位置独立预测而牺牲了τ。同时，固定长度的验证将T_verify浪费在几乎肯定会被拒绝的低置信度后缀token上。DSpark通过两个互补组件解决了这些局限性：

*   **半自回归生成（第3.1节）。** 一个并行骨干网络处理草稿计算的主要部分，使T_draft几乎与γ无关。然后一个轻量级序列块在草稿token之间注入依赖关系，以最小的额外延迟提高τ。
*   **置信度调度的验证（第3.2节）。** 一个置信度头估计每个位置的接受概率，一个硬件感知调度器使用这些估计来修剪低置信度的后缀token，减少不必要的验证计算。

在组合中，这两个组件使DSpark能够更好地草稿并更智能地验证。下面我们详述每个组件。

### 3.1. 半自回归生成

并行草稿模型在一次前向传播中产生所有γ个草稿logits，因此每个预测不能以块中其他地方采样的token为条件。当上下文允许多种合理的续写时，例如"of course"和"no problem"，并行草稿模型可能产生不连贯的组合，如"of problem"或"no course"，因为每个位置对所有可能的先行词进行边际化，而不是以实际采样的那个为条件（Gu et al., 2018; Huang et al., 2022a）。因此，接受率沿块快速衰减，浪费了草稿和验证计算。因此，我们采用了一种半自回归结构，将草稿生成分为两个阶段：

**并行阶段。** 一个并行骨干网络（在我们的实例化中为DFlash (Chen et al., 2026)）在整个块上运行一次前向传播，产生隐藏状态h_1, ..., h_γ和基础logits U_1, ..., U_γ。我们对原始DFlash骨干网络做了一个小修改：我们不输入一个锚点token加γ个mask token并仅预测mask位置，而是将锚点本身作为第一个预测位置，因此γ个输入token（锚点 + γ-1个mask）产生γ个草稿logits。这减少了草稿计算，同时保持了类似的草稿质量。

**序列阶段。** 序列阶段为基础logits补充一个前缀相关的转移偏置B_k(x_0, x_<k, x_k)，允许每个草稿位置以块内先前采样的token为条件。序列阶段不是定义一个全局归一化的能量模型，而是通过自回归分解引入一个因果块分布：

P(X | x_0) = ∏_{k=1}^{γ} p_k(x_k | x_0, x_<k),
p_k(v | x_0, x_<k) = exp(U_k(v) + B_k(x_0, x_<k, v)) / Σ_{u∈V} exp(U_k(u) + B_k(x_0, x_<k, u))    (4)

这里，x_0表示来自上一个验证周期的锚点token，U_k是并行骨干网络在位置k产生的基础logit向量，V是词汇表。在推理时，序列块根据p_k(· | x_0, x_<k)从左到右采样。由于这个采样过程本质上是顺序的，该块必须在计算上轻量（T_sequential ≪ T_parallel），以便整体草稿延迟仍由并行阶段主导。下面我们描述序列块的两种实例化。

*   **Markov头。** 最简单的实例化将B_k限制为仅依赖于紧邻的前一个token，将其简化为一个一阶转移B(x_{k-1}, x_k)。原则上这是一个完整的V×V矩阵B；我们通过低秩分解B = W_1 W_2来近似它，其中W_1 ∈ R^{V×r}，W_2 ∈ R^{r×V}。给定前一个token x_{k-1}，位置k的转移偏置为：

    B(x_{k-1}, ·) = W_1[x_{k-1}] W_2 ∈ R^V    (5)

    其中W_1作为嵌入查找表，W_2作为logit投影。低秩分解（默认r=256）使存储和每步计算都很小，使得序列循环即使对于大型词汇表也很高效。回到之前的例子：一旦位置1采样了"of"，Markov头就会提升"course"并抑制"problem"在位置2的概率，这减轻了跨模态冲突。

*   **RNN头。** Markov头在一步之外没有记忆——位置k无法访问x_{k-1}之前的token。RNN头通过维护一个循环状态s_k来缓解这一点，该状态累积块内的完整前缀历史。在每个步骤中，该模块将当前状态s_{k-1} ∈ R^r、前一个token嵌入W_1[x_{k-1}] ∈ R^r和骨干网络隐藏状态h_k ∈ R^d拼接成一个输入向量z_k = [s_{k-1}; W_1[x_{k-1}]; h_k] ∈ R^{2r+d}，然后应用一个门控更新：

    s_k = σ(W_g z_k) ⊙ s_{k-1} + (1 - σ(W_g z_k)) ⊙ tanh(W_c z_k),
    B_k(x_<k, ·) = W_2^⊤ tanh(W_o z_k)    (6)

    其中W_g, W_c, W_o ∈ R^{(2r+d)×r}通过一个单一的线性投影联合参数化，该投影被分割为门控、候选和输出分量。状态s_0初始化为零。

### 3.2. 置信度调度的验证

半自回归架构使DSpark能够高效地生成大型草稿块。然而，产生更多的草稿token并不自动转化为更高的端到端加速。不加区分地验证整个草稿块实际上会降低整体系统吞吐量，特别是在高并发场景中（Hu et al., 2026; Liu et al., 2024c）。

这种性能瓶颈源于两个相互作用的因素。首先，在数据方面，草稿接受率在不同领域间固有地变化：像代码这样的结构化文本自然产生高接受率，而开放式对话有显著较低的接受率（Abramovich et al., 2026; Xia et al., 2024）。其次，在系统方面，验证额外token的实际成本严格取决于引擎负载。在轻系统负载下，额外的验证即使被拒绝也产生最小的惩罚。然而，在高并发部署中，每次不必要的验证都占用目标模型批次容量，这些容量本可以用于服务其他活跃请求（Liu et al., 2024b; Wu et al., 2025）。

因此，充分释放大型草稿块的潜力需要一个统一的机制，该机制将目标模型计算仅引向具有正预期收益的token。DSpark通过将一个预测前缀生存概率的置信度头（第3.2.1节）与一个基于当前系统负载动态确定最优验证长度的硬件感知前缀调度器（第3.2.2节）相结合来实现这一点。

#### 3.2.1. 置信度头

受Huang et al. (2024); Wang et al. (2026)的启发，置信度头为每个草稿位置k输出一个标量估计c_k ∈ (0, 1)。关键的是，c_k建模了位置k的草稿token在目标验证中存活的概率（给定块中所有前面的token已被接受）。该架构采用一个轻量级线性投影后跟一个sigmoid函数：

c_k = σ(w^⊤ [h_k; W_1[x_{k-1}]])    (7)

其中h_k是骨干网络的隐藏状态，W_1[x_{k-1}]是来自前一个草稿token的Markov嵌入。我们使用逐步解析接受率c*_k来监督c_k。该率由草稿分布p^d_k与目标分布p^t_k之间的总变差距离决定：

c*_k = 1 - (1/2) ‖p^d_k - p^t_k‖_1    (8)

**事后校准。** 与基于阈值的验证启发式方法（Huang et al., 2024; Li et al., 2024b; Zhang et al., 2026b）不同——它们只需要置信度分数正确地对草稿token质量进行排序——我们的硬件感知调度方法（在第3.2.2节中详述）精确地需要累积接受概率的绝对量级来计算预期接受长度τ。由于神经网络的置信度估计往往过于自信（Guo et al., 2017; Ovadia et al., 2019），直接使用原始置信度分数会扭曲吞吐量估计，导致次优调度。

为了解决这个问题，我们引入了顺序温度缩放（STS）。因为每个c_i建模一个条件概率，链式法则规定一个草稿前缀被接受的联合概率分解为累积乘积 ∏_{i≤k} c_i。使用一个保留的验证集，STS从左到右连续校准这个联合概率。具体来说，在每个位置k ∈ {1, ..., γ}，我们执行一个简单的1D网格搜索，找到使累积乘积的期望校准误差（ECE）(Naeini et al., 2015) 最小化的最优温度标量，同时保持所有前面位置的已校准分数不变。关键的是，温度缩放是一个保序变换：它纠正预测概率以匹配经验接受率，而不会破坏置信度头学习到的相对草稿token排名。

#### 3.2.2. 硬件感知前缀调度器

**算法1 硬件感知前缀调度器**
**需要：** 活跃请求 r ∈ {1, ..., R}；每个请求的置信度序列 c_{r,1}, ..., c_{r,γ}；分析得到的步曲线 SPS(B)
**确保：** 选定的每个请求前缀长度 ℓ*_1, ..., ℓ*_R

1: for r = 1 to R do
2:    计算前缀生存概率：a_{r,j} ← ∏_{i≤j} c_{r,i} for j = 1, ..., γ
3: end for
4: 构建候选空间 E ← {(r, j) | a_{r,j} > 0} 并按 a_{r,j} 降序排序
5: 初始化状态：ℓ_r ← 0 for all r；批次大小 B ← R；预期接受 τ* ← R
6: 初始化跟踪：Θ_best ← R · SPS(R)；选定的长度 ℓ*_r ← 0 for all r
7: for each (r, j) ∈ E in sorted order do
8:    ℓ_r ← j; B ← B + 1; τ* ← τ* + a_{r,j}
9:    当前吞吐量 Θ ← τ* · SPS(B)
10:    if Θ > Θ_best then
11:        Θ_best ← Θ; 更新选定长度 ℓ*_r ← ℓ_r
12:    else
13:        break
14:    end if
15: end for
16: return (ℓ*_1, ..., ℓ*_R) 达到 Θ_best

先前的方法（Huang et al., 2024; Li et al., 2024b）通常应用一个静态阈值到置信度分数来确定验证长度。虽然在孤立的单请求假设下有效，但在高并发生产系统中，静态阈值可能是次优的，因为验证一个草稿token的效用严重依赖于当前系统负载。

为了解决这个问题，我们将验证长度选择形式化为一个全局吞吐量最大化问题（算法1）。考虑一批R个活跃请求。对于请求r，令c_{r,1}, ..., c_{r,γ}为逐位置置信度估计，令ℓ_r ∈ {0, ..., γ}为调度的验证长度。由于推测解码动态地只接受作为连续前缀的草稿token，位置j的token的生存概率是累积乘积 a_{r,j} = ∏_{i≤j} c_{r,i}。

在单次验证步骤中，发送给目标模型的总批大小（以token计）为 B = Σ_{r=1}^R (1 + ℓ_r)，预期成功接受的token数为 τ = Σ_{r=1}^R (1 + Σ_{j=1}^{ℓ_r} a_{r,j})。令 SPS(B) 表示引擎吞吐量（以每秒步数计）对于给定前向传播批大小B。关键的是，这个容量曲线在引擎初始化时被分析一次，并存储为一个轻量级成本表。然后，我们的调度器旨在通过动态选择验证长度ℓ_1, ..., ℓ_R来最大化预期的系统级token吞吐量 Θ = τ · SPS(B)。

尽管找到Θ的全局最大值看起来是一个组合搜索，但目标结构允许一个高效的贪心解。因为a_{r,j}关于j单调非增（即 a_{r,j} ≤ a_{r,j-1}），将请求r的验证长度从j-1扩展到j的边际预期接受token增益正好是a_{r,j}。这种单调性确保按a_{r,j}全局排序候选token自然尊重块内前缀依赖关系。因此，如果总的验证批大小B是固定的，最优分配{ℓ_r}将通过从所有{a_{r,j}}的全局池中贪心地选择具有最高生存概率的草稿token来确定。

基于这一洞见，优化可以沿这个贪心接纳路径进行评估。我们首先将所有有效的前缀扩展按生存概率降序全局排序。为了动态确定最优的目标批大小B，我们从排序后的池中逐步接纳token，通过预分析的成本表以O(1)查找更新预期吞吐量Θ。

无损推测解码严格要求非预期属性：接纳决策不能依赖于未来的候选token（Chen et al., 2023; Leviathan et al., 2023）。因为我们的置信度头依赖于先前采样token的Markov特征，计算下一个生存概率a_{r,k+1}明确地需要已实例化的候选x_{r,k}。事后全局搜索因此会无意中将x_{r,k}泄露到第k步的接纳决策中，引入选择偏差（我们在附录A中提供了一个具体的反例来证明这种理论违反）。

为了强制严格因果性，调度器（算法1）采用了一个早停机制。通过在吞吐量下降时（Θ ≤ Θ_best）立即中断贪心搜索，截断决策仅依赖于处理到那一确切步骤的前缀。这将接纳事件与未来的token隔离开来，确保了精确的目标分布恢复。注意，当且仅当目标Θ是单峰时，这种逐步早停才能产生全局最大吞吐量，这隐含地假设了一个平滑衰减的硬件容量曲线。我们将在第5.2节中处理真实世界非平滑SPS特性和异步系统管道所需的工程适配。

### 3.3. 训练

在训练期间，我们从每个目标序列中随机采样多个锚点位置，形成γ-token块作为训练数据。目标模型在整个训练过程中保持冻结；草稿模型共享其嵌入层和语言模型头并保持其冻结，仅更新骨干草稿模型、序列块和置信度头。

训练目标包含三项：交叉熵损失L_ce、分布匹配损失L_tv和置信度损失L_conf。所有三项都按位置加权，权重为w_k = exp(-(k-1)/γ)（Chen et al., 2026），这强调了在前缀验证下对预期接受长度贡献更大的早期块位置。交叉熵损失L_ce训练草稿模型预测正确的下一个token：

L_ce = - Σ_{k=1}^γ w_k log p^d_k(x*_k)    (9)

其中x*_k是真实token，p^d_k是草稿分布。分布匹配损失L_tv惩罚草稿与目标分布之间的总变差距离：

L_tv = Σ_{k=1}^γ w_k ‖p^d_k - p^t_k‖_1    (10)

由于总变差距离是接受率的直接代理：每步接受概率等于1 - (1/2)‖p^d - p^t‖_1（Leviathan et al., 2023），最小化L_tv直接最大化预期接受率。置信度损失L_conf是一个二元交叉熵损失，训练置信度头预测来自公式8的软接受标签c*_k：

L_conf = - Σ_{k=1}^γ w_k [c*_k log c_k + (1 - c*_k) log(1 - c_k)]    (11)

总体目标是三项的加权组合（默认权重α_ce = 0.1, α_tv = 0.9, α_conf = 1.0）：

L = α_ce L_ce + α_tv L_tv + α_conf L_conf    (12)

## 4. 实验

在本节中，我们使用离线基准验证DSpark的草稿质量，并在第5节中报告置信度调度器在在线生产流量下的有效性。实验设置在第4.1节中描述，主要结果在第4.2节中，额外分析包含在第4.3节中。

### 4.1. 实验设置

**目标和草稿模型。** 我们在跨越不同规模和模型系列的目标模型上评估DSpark：Qwen3-{4B, 8B, 14B}（Yang et al., 2025）和Gemma4-12B（Google DeepMind, 2026）。对于草稿模型，我们将DSpark与两个代表性的草稿模型进行比较：DFlash（Chen et al., 2026），一个最先进的并行草稿模型；以及Eagle3（Li et al., 2026b），一个基于训练时测试（TTT）的自回归草稿模型。为了公平比较，我们在相同的训练框架和相同的数据上重新训练所有草稿模型。我们将Eagle3的TTT视野（7）与DFlash和DSpark使用的块大小（7）对齐，并且对所有草稿模型使用相同的目标模型特征层。对于草稿模型层数，Eagle3设置为1，DSpark和DFlash设置为5（Chen et al., 2026）。除非另有说明，DSpark表示Markov头变体；我们在第4.3.2节中研究RNN头变体。

**训练数据。** 我们使用Open-PerfectBlend 2，一个PerfectBlend（Xu et al., 2024）的开源版本，包含130万样本。它是一个通用指令数据集，包含对话（17.6%）、数学（39.4%）、代码（38.9%）和指令跟随数据（4.1%）。我们只使用Open-PerfectBlend中的提示词；响应由每个目标模型使用推荐的采样参数重新生成。每个草稿模型训练10个epoch以确保完全收敛。对于数据生成和评估，我们采用非思考模式。

**评估协议。** 我们在三个领域评估不同算法的性能：

1. 数学推理，包括GSM8K（Cobbe et al., 2021）、MATH500（Lightman et al., 2024）和AIME25（Zhang and Math-AI, 2025）。
2. 代码生成，包括MBPP（Austin et al., 2021b）、HumanEval（Chen et al., 2021）和Live-CodeBench（Jain et al., 2025）。
3. 日常对话，包括MT-Bench（Zheng et al., 2023）、Alpaca（Taori et al., 2023）和Arena-Hard（Li et al., 2024a, 2025b）。

对于所有基准测试，我们使用标准推测解码（Chen et al., 2023; Leviathan et al., 2023），采样温度设置为1.0。我们报告每解码轮的接受长度（τ）3。对于所有草稿模型，我们使用基于链的草稿。

### 4.2. 实验结果

为了隔离草稿质量与系统级调度策略，我们的离线评估禁用了置信度调度器，迫使所有草稿模型提出固定数量的token块。主要结果以每轮平均接受长度（τ）衡量，报告在表1中。

DSpark在所有评估的目标模型和基准领域上持续优于自回归基线（Eagle3）和并行基线（DFlash）。具体来说，在Qwen3-4B、8B和14B模型上，DSpark相对于Eagle3将宏平均接受长度分别提升了30.9%、26.7%和30.0%。类似地，与DFlash相比，DSpark在三个规模上分别产生了16.3%、18.4%和18.3%的相对改进。关键的是，这一优势跨模型系列泛化，Gemma4-12B目标上的一致性能增益证明了这一点。

除了平均改进之外，表1还揭示了一个强烈的领域效应：结构化任务（例如，Qwen3-4B上数学为5.57，代码为5.12）上的接受长度自然高于开放式对话（3.49）。数据可预测性中的这种固有方差意味着固定验证长度经常将计算浪费在极有可能被拒绝的尾部token上。这直接激发了我们的置信度调度验证，它基于预期接受动态修剪草稿块。

### 4.3. 实验分析

#### 4.3.1. 为什么并行生成能胜过自回归？

表1呈现了一个反直觉的观察：并行草稿模型（DFlash）和半自回归草稿模型（DSpark）通常产生比完全自回归草稿模型（Eagle3）更长的接受长度。这一发现与逐步自回归比并行模型产生更高质量序列的标准预期相矛盾（Israel et al., 2026; Ren et al., 2020; Zheng et al., 2025）。

为了分析这种行为，我们检查了宏接受长度之外的性能。使用Qwen3-4B目标模型和第4.1节中描述的基准集，我们引入了在实际推测解码过程中跟踪的逐位置条件接受率。具体来说，对于给定的草稿位置k，评估分母只计算目标模型成功验证并接受了从1到k-1的所有前面草稿token的实例。然后该指标计算在这些有效实例中位置k的token也被接受的比例。这种方法确保了对位置k的评估不会因之前的前缀错误而受罚，揭示了每个特定步骤的基础预测质量。图2详述了这些测量，展示了跨架构的明显行为差异。

**位置1的容量优势。** 在第一个草稿位置，两种架构都仅基于目标上下文预测下一个token。这里的性能差异严格源于架构容量：像Eagle3这样的自回归模型由于其O(γ)延迟而受限于浅层网络，而O(1)并行草稿模型可以承担更深得多的网络。这种结构差距在位置1产生了显著的准确率优势，DFlash明显高于Eagle3（例如，数学上0.88对0.81，对话上0.72对0.53）。由于推测解码作为一个严格的前缀匹配生存过程运行，第一个token具有最高的杠杆作用——在这里拒绝会立即使整个块失效。因此，这种初始容量优势不成比例地提升了最终接受长度，解释了为什么并行草稿模型尽管在后期位置有快速的接受率衰减，却在全局上优于自回归模型。

**独立性在后期位置的局限性。** 检查曲线尾部（位置2到7）揭示了独立并行生成的固有限制。随着较早的token锁定一个特定的语义路径，后续token自然变得更可预测。像Eagle3这样的自回归模型有效利用这种条件确定性，在块中更深的位置维持甚至增加条件接受率（例如，在对话上从0.53到0.74）。相比之下，DFlash遭受快速接受率衰减，在代码上从0.87下降到0.78，在对话上从0.72下降到0.63。因为每个并行位置对所有可能的先前token进行边际化而不是以精确采样的前缀为条件，该模型经常提出不一致的后缀组合——这种模式被称为多模态冲突（Gu et al., 2018; Stern et al., 2018）。

**通过半自回归缓解后缀衰减。** 前面的分析突出了一个明确的架构目标：将并行骨干网络对初始token的高容量与自回归模型对后续token的依赖建模相结合。这直接激发了DSpark的半自回归设计。如图2所示，DSpark继承了深层并行草稿模型的高初始接受率（例如，在数学上从0.93开始）。同时，其轻量级序列头减轻了并行生成典型的快速接受率衰减。通过解决这种权衡，DSpark在整个草稿块中维持了高且稳定的条件接受率。

#### 4.3.2. 少量自回归就能走得很远

基于第4.3.1节的洞见，我们沿两个维度探索DSpark的架构设计空间：草稿深度（Transformer层数）和提案长度（块大小γ）。除非另有说明，本节中的所有实验使用Qwen3-4B作为目标模型，并遵循第4.1节详述的评估协议。

**草稿深度。** 增加Transformer层数自然扩展了草稿模型的预测能力。为了隔离这种效应，我们将块大小固定为7，并将DSpark的层数从1变化到5，与5层的DFlash基线进行比较。图3汇总了跨数学、代码和对话领域的接受长度。如预期，DSpark的性能随深度单调改善，最大边际增益出现在从一层到两层时。值得注意的是，2层的DSpark在所有领域上都优于5层的DFlash基线。这表明通过轻量级序列头注入局部自回归提供了非常有利的准确率-参数权衡，实现了比简单堆叠更深并行层更好的序列连贯性。

**提案长度。** 接下来，我们将草稿深度固定为5层，并将草稿长度（提案长度γ加一个锚点token）在{4, 8, 12, 16}上缩放，以评估更长草稿块上的性能。对于DSpark，我们评估了默认的Markov头和RNN头。图4的前三个面板显示，DSpark在每个提案长度上都持续优于DFlash。更重要的是，随着γ增加，性能差距稳步扩大。由于纯并行生成（DFlash）遭受快速接受率衰减（图2），其边际效用对于长块来说逐渐减少。DSpark缓解了这种衰减，导致其相对于DFlash的相对增益增长。例如，在γ=7时，DSpark在数学上提升接受长度16%，在代码上提升15%，在对话上提升18%；在γ=15时，这些增益分别扩大到30%、26%和22%。此外，RNN头相对于Markov头只提供了额外的边际收益，主要体现在更长的提案长度上。鉴于其更高的实现复杂性和不太有利的部署特性，我们使用Markov头作为默认选择。

**延迟开销。** 我们量化了DSpark中序列生成循环的开销。图4的最右面板报告了每轮的引擎延迟——包括一次目标验证前向传播、并行草稿块前向传播和串行采样循环——在批大小为128时测量。为了防止序列长度偏差，报告的延迟是不同上下文长度（{512, 1024, 2048, 4096} token）上的算术平均值。由于在此批大小下目标模型主导验证计算时间，序列块的延迟开销可以忽略不计。因此，将草稿长度从4扩展到16仅比DFlash基线增加了0.2%到1.3%的全轮延迟，尽管交付了高达30%的接受长度改进。

#### 4.3.3. 更智能地验证，而不是更久：置信度头的作用

虽然DSpark在长草稿块上维持了高接受率，但验证整个提案仍然效率低下（Hu et al., 2026; Huang et al., 2024）。由于第4.2节中注意到的固有领域差异，开放式对话中的尾部token仍然面临高拒绝风险，使得盲目验证成为对目标计算的浪费。为了评估置信度头能否有效修剪这些没有前途的后缀，我们使用Qwen3-4B进行了离线阈值扫描。我们在此单独验证估计器，将硬件感知前缀调度器（第3.2.2节）留待第5节的生产环境评估。

**诊断：静态阈值扫描。** 图5绘制了不同置信度阈值下的平均每步token数（柱状图）和总体接受率（折线图）。随着阈值增加，接受率稳定上升，因为估计器过滤掉了最终会被拒绝的token（阴影柱状图）。这表明置信度头可以识别低价值后缀token，并且这种修剪在对话工作负载上最为明显，其中高熵token分布限制了固定长度验证的效率。在对话子图中，提高阈值显著减少了被拒绝的token，使接受率从45.7%提高到95.7%。相比之下，结构化任务（数学和代码）经历较温和的修剪并保留了更多草稿token，接受率分别从76.9%提高到92.5%和从67.6%提高到92.0%。

**从静态阈值到校准调度。** 虽然对诊断有用，但静态阈值在动态服务环境中是次优的，因为它忽略了系统负载：验证低置信度token在低并发下产生最小的机会成本，但在高并发下浪费关键的批次容量。这种负载依赖性激发了硬件感知前缀调度器。如第3.2节所述，最大化系统级吞吐量要求置信度模型既表现出强大的预测判别能力，又表现出精确的校准以准确估计累积生存概率。可靠性图（图6）表明，虽然原始模型实现了强大的判别能力（ROC-AUC (Hanley and McNeil, 1982) 从0.81到0.90），但它过于自信（ECE 3%-8%）。应用事后STS（第3.2.1节）缓解了这种过度自信，将平均ECE降低到约1%，并产生了可靠的生存估计。

## 5. DSpark的真实世界部署

虽然第4节确立了DSpark在离线基准测试中的算法增益，但将其与DeepSeek-V4（DeepSeek-AI, 2026）等大规模模型一起部署引入了额外的系统级挑战，涉及训练和推理。在本节中，我们介绍DSpark的端到端生产管道。我们详述了可扩展的训练机制、部署硬件感知前缀调度器（第3.2.2节）所需的系统级优化，以及该框架在真实用户流量下的端到端性能。

### 5.1. 可扩展且灵活的训练

DSpark草稿模型与DeepSeek-V4-Flash和DeepSeek-V4-Pro（DeepSeek-AI, 2026）的预览版本共同部署。并行骨干网络包含三个MoE层（Dai et al., 2024），使用mHC（Xie et al., 2026）和128的滑动窗口注意力。我们将最大块大小配置为γ=5，并使用Markov头进行序列建模。此外，置信度头与草稿模型一起端到端训练，然后通过STS进行校准，以提供可靠的调度信号。

训练草稿模型需要目标模型的输出分布作为监督。在两个模型上评估完整的文档上下文会产生显著的内存占用和工人间通信开销。为了解决这些瓶颈，我们在内部训练框架（HAI-LLM）4中实现了两个系统级优化：

*   **隐藏状态通信。** 在并行工人之间传输目标模型的完整词汇表logits（V≈10^5）造成了显著的带宽瓶颈。取而代之，我们临时缓存目标模型前向传播的激活，并仅传递紧邻语言模型头之前的隐藏状态。然后语言模型头投影在草稿模型的工人上本地执行，仅针对采样的目标位置。这将每token通信复杂度降低到O(d)，其中d是隐藏维度。
*   **锚点边界序列打包。** 为了将草稿模型的计算成本从目标模型的上下文长度解耦，我们从训练序列中采样固定数量的草稿锚点，并将这些孤立的预测块打包成密集的训练批次。我们通过token级注意力索引而非标准的2D掩码来管理这种打包。这保持了跨多个独立序列和锚点的精确因果掩码，避免了与标准填充相关的计算和内存开销。

### 5.2. 实践中的硬件感知前缀调度器

在第3.2.2节中，算法1提供了一个理论上合理且无损的调度机制。然而，直接将该算法部署到生产环境暴露了两个与现实世界基础设施的根本冲突。首先，该算法假设一个平滑的单峰容量曲线，而真实的硬件容量SPS(B)本质上是离散的，表现出锯齿状、阶梯式的退化（Yan et al., 2020）。其次，该算法要求每步调度动态草稿token，这与连续的CUDA图回放（Fireworks AI, 2023）和零开销调度（ZOS）（Zheng et al., 2024; Zhu et al., 2025）相冲突。

为了在系统兼容性、吞吐量和算法正确性之间进行权衡，我们使调度器异步运行。因为ZOS要求在當前步骤完成之前就知道下一步的批次大小，同步调度将不可避免地使GPU管道停滞。相反，我们使用两步之前的置信度头输出来近似即将到来的验证容量。机制上，当前步骤中的候选token仍然严格按其实时更新的累积置信度分数排序；两步前的历史预测仅用于确定动态截断长度（即批次容量限制K）。这有效地将接纳过程转化为动态的top-K选择。虽然近似容量K引入了一个轻微的时间偏移，但选择机制从根本上保持了排名：最有信心的草稿token总是优先被验证。这种适配完全隐藏了调度延迟，并确保了无缝的ZOS集成。

在此异步管道的基础上，我们解决了硬件利用瓶颈。为了防止调度器被锯齿状SPS悬崖困在局部最小值，我们移除了早停中断，启用不受约束的全局搜索。通常情况下，这种事后搜索会泄露未来token信息并违反无损保证（附录A）。然而，我们的ZOS驱动适配自然防止了这种情况。因为不受约束的搜索仅评估两步前的历史预测，接纳决策与当前token x_{r,k}的实现隔离开来。截断长度本质上仅依赖于两步前可用的信息。因此，异步设计形成了一个因果屏障，在硬件悬崖上最大化物理吞吐量，同时保持精确的目标分布。

### 5.3. 高吞吐和低延迟推理

在解码过程中，生产服务系统必须同时优化两个竞争目标：每请求延迟和总吞吐量（Kwon et al., 2023; Zhao et al., 2025a; Zhong et al., 2024）。前者控制个体用户的服务质量——这一因素在基于Agent的工作负载中日益关键（Tiwari et al., 2026）——而后者决定同时服务的用户总数。由于推测解码不可避免会产生验证计算浪费，它本质上游走于这种权衡之间，用额外的系统计算换取更快的每请求生成。

然而，在我们的部署环境中，每步处理的请求数量经常受到资源限制（例如，每个请求固定的KV缓存容量）和可用用户流量池（例如，RL长尾负载）的约束。因此，有效批次大小持续远低于GPU计算饱和的阈值。在这种机制下，传统的权衡简化了：给定固定的并发限制，最大化每GPU总token吞吐量和最大化每个用户的生成速度（tok/s/user）成为高度相关的目标而非竞争目标。

为了实现这种最大吞吐量，异步调度器（第5.2节）积极地将空闲计算引导至最有希望的草稿token。然而，执行这种动态路由在物理执行层引入了一个严峻的挑战：推理框架必须高效地支持单个批次内的可变长度查询。标准的解码核针对固定查询长度进行了高度优化；天真地处理可变长度的已验证前缀由于填充和不均匀的工作负载分布导致严重的GPU利用率不足。我们通过将物理执行与逻辑序列跟踪解耦来解决这个问题。在我们的计算核中，跨不同请求的所有token被展平并作为独立元素相同处理。复杂的序列内依赖关系则通过集成到我们稀疏注意力实现中的一个标记张量来严格传达。具体在DeepSeek-V4架构上，只需要修改索引注意力和压缩核以支持这种可变长度路由，使动态调度器能够无缝运行而不引入低级执行开销。

### 5.4. 真实用户流量下的性能

我们评估了DSpark-5（配置最大草稿长度γ=5）与MTP-1（DeepSeek-AI, 2024）基线在DeepSeek-V4-Flash（预览版）和DeepSeek-V4-Pro（预览版）的生产服务引擎中的对比。MTP-1代表了以前的生产设置，在DeepSeek-V4-preview发布两周后被DSpark取代。这种单token设置历史上一直在生产中维护，因为部署静态多token草稿模型（例如MTP-3/5）在高并发下由于过度的验证开销严格降低总吞吐量。因此，将DSpark与此既定基线直接比较，证明了其在动态服务环境中安全解锁更大草稿块性能潜力的能力。在所有图中，散点代表直接从真实用户流量中采样的原始遥测数据，捕获了复杂的真实世界请求分布，而实线代表拟合的性能前沿。

**服务Pareto前沿。** 图7说明了系统总吞吐量与每用户生成速度（交互性）之间的权衡。为了量化DSpark在实际部署约束下的行为，我们在几个交互性SLA锚点评估了系统。这里，SLA（服务等级协议）指定了系统必须保证的最小每用户生成速度（以每秒token数计）。

对于V4-Flash引擎，我们在80和120 tok/s/user的SLA锚点评估系统。在适度的80 tok/s/user SLA下，DSpark相对于MTP-1基线将总吞吐量提高了51%。更严格的120 tok/s/user SLA代表了一个质上不同的机制：在此约束下，单token的MTP-1基线接近其操作边界，只能维持非常小的并发批次。因此，此点的相对吞吐量比率数值上很大，DSpark实现了标称的661%更高的总吞吐量。因此，我们将此高SLA点主要解释为DSpark扩展了可行的交互性前沿的证据，而不是作为对充分利用基线的代表性倍数加速。在匹配的实际吞吐水平下——这提供了更稳定的比较——DSpark将每用户生成速度加速了60%到85%。

V4-Pro部署显示了相同的模式。在适度的35 tok/s/user SLA下，DSpark将总吞吐量提高了52%。在更严格的50 tok/s/user SLA下，MTP-1再次进入低并发机制，DSpark产生标称的406%相对吞吐量优势。与V4-Flash一样，我们将此点视为DSpark在基线无法有效支持的交互性目标下维持有用吞吐量的指示。在匹配的系统容量下，DSpark提供了57%到78%更快的每用户生成。总体而言，这些结果表明DSpark将观察到的吞吐量-交互性前沿向外移动：它在中等SLA机制下提高了吞吐量，更重要的是，在严格的交互性约束下保持了非退化的服务容量。

**负载下的吞吐量动态。** 图8通过绘制总吞吐量（上行）和动态验证预算（下行）与系统并发度的关系，分析了驱动这些增益的底层机制。

*   在生产部署典型的中等并发机制下（对于V4-Flash少于200个并发请求，对于V4-Pro为150个），硬件感知调度器通过分配更长的验证预算来利用可用的目标计算容量，从MTP-1的静态2个token扩展到每个请求大约4-6个token。这种扩展的验证在每个前向传播中产生了更多被接受的token，直接贡献了在Pareto前沿上观察到的吞吐量增益。
*   随着系统并发度扩大且目标容量饱和，调度器动态地限制这一预算。平均验证长度随负载平滑降低，确保低置信度草稿token在消耗关键批次容量之前被修剪。这种负载感知行为稳定了生产部署：DSpark在轻流量下最大化空闲计算的效用，同时在重流量下有效地保持关键批次容量。

**局限性。** 尽管前缀调度器最大程度减少了目标模型验证的浪费，DSpark仍然承担固定的草稿端成本，通过并行骨干网络生成初始的γ-token块。对于具有固有低接受率的复杂查询，这种前期草稿计算是不可恢复的。未来的优化可以在草稿模型中引入难度感知的提前退出，使这类请求能够绕过完整块生成。

## 6. 相关工作

**推测解码算法。** 推测解码通过将token提案与验证解耦来加速自回归生成。建立在早期的块级方法（Ge et al., 2022; Stern et al., 2018; Sun et al., 2021; Xia et al., 2023）之上，现代方法采用拒绝采样来精确保持目标模型的分布（Chen et al., 2023; Leviathan et al., 2023）。由于推理加速直接依赖于草稿模型的效率和准确性，广泛的研究集中在优化其架构上。除了使用独立的较小语言模型（Chen et al., 2023; Leviathan et al., 2023），后续工作直接将多token头或特征外推器集成到目标模型中（Ankner et al., 2024; Cai et al., 2024, 2025; DeepSeek-AI, 2024; Gloeckle et al., 2024; Li et al., 2024b,c, 2026b; Zhang et al., 2025）。其他策略包括通过提前退出来实现自推测（Elhoushi et al., 2024; Liu et al., 2024a; Xia et al., 2025; Zhang et al., 2024）、动态词汇压缩（Williams et al., 2026; Zhao et al., 2025b）、提示查找（Saxena, 2023; Somasundaram et al., 2025）、后缀自动机（Hu et al., 2025）和检索（He et al., 2023; Shen et al., 2026）。为了消除草稿本身的顺序瓶颈，最近的方法提出了并行或块级生成。P-EAGLE并行化了EAGLE风格的草稿（Hui et al., 2026），而PARD、DART和DFlash使用类扩散预测在单次前向传播中生成整个块（An et al., 2026; Chen et al., 2026; Liu et al., 2026a），DDTree随后将其扩展到可验证的草稿树（Ringel and Romano, 2026）。并行工作也在改进DFlash：Domino（Huang et al., 2026a）引入了一个CausalEncoder，概念上类似于我们的RNN头，而DFlare（Zhang et al., 2026a）通过逐层融合解决了条件瓶颈。

**系统感知的推测解码调度。** 除了草稿模型架构之外，另一条工作线专注于确定在每个轮次中生成或验证的最优推测token数量。为此，各种方法使用置信度启发式（Du et al., 2024; Li et al., 2024b; Liu et al., 2026c; Mamou et al., 2024; Wen and Feng, 2026）、学习得到的接受预测器（Huang et al., 2024; Zacks917, 2026）或bandit策略（Liu et al., 2026b）在线调整草稿长度。此外，认识到推测解码本质上是一个系统级调度问题，最近的工作通过根据实时系统负载和请求优先级调整推测预算来优化总体吞吐和延迟（AngelSlim Team, 2026; Hu et al., 2026; Huang et al., 2026b; Li et al., 2026a; Liu et al., 2024c; Miao et al., 2024; Sadhukhan et al., 2025; Wu et al., 2025）。

**并行生成。** 并行生成token的模型提供了几乎与输出长度无关的解码延迟，使其成为自回归解码的一个有吸引力的替代。非自回归Transformer（NAT, Gu et al., 2018）通过在一次前向传播中独立预测所有位置开创了这一方向。然而，这迫使模型对所有合理模式进行平均，通常产生混合了来自不同有效序列的片段的输出。两条主要的工作线已经出现以解决这一局限性。一个方向保留单次前向传播架构，但改变模型所见或训练方式：引入潜变量作为条件输入以引导所有位置朝向一致的输出（Gu et al., 2018; Kaiser et al., 2018; Ma et al., 2019），或放宽训练目标使模型专注于产生单个连贯输出而不是对所有有效替代方案建模完整分布（Du et al., 2021; Qian et al., 2021; Shao et al., 2021, 2023）。另一方向通过迭代重预测（Austin et al., 2021a; Ghazvininejad et al., 2019; Li et al., 2022）、块级自回归（Arriola et al., 2025; Wang et al., 2018）或结构化输出层（如CRF（Sun et al., 2019）、CTC（Libovický and Helcl, 2018; Saharia et al., 2020）、HMM（Huang et al., 2022b）和PCFG（Gui et al., 2023））重新引入有限的序列依赖性。

推测解码进一步要求草稿模型必须为拒绝采样规则提供精确的每token概率。上述大多数技术由于迭代细化、潜变量边际化或全局归一化而难以提供这样的概率。例如，在与我们设计密切相关的CRF-NAT（Sun et al., 2019）中，也在并行隐藏状态上放置了一个序列模块，但其全局归一化的配分函数阻止了精确的每token概率计算。类似地，在将CTC输出层适应于并行推测解码时，CTC-drafter（Wen et al., 2024）由于对齐路径的潜变量边际化而限制为贪心验证。DSpark通过保持序列校正的局部性来规避这些限制，使得每token概率仍然是精确的softmax评估。

## 6. 相关工作

### 推测解码算法

推测解码通过将 token 提议与验证分离来加速自回归生成。在早期块级方法的基础上，现代方法采用拒绝采样精确保留目标模型的分布。由于推理加速直接取决于草案模型的效率和准确性，大量研究聚焦于优化其架构。除了使用独立小语言模型外，后续工作将多 token 头或特征外推器直接集成到目标模型中。其他策略包括通过早期退出的自推测、动态词汇压缩、提示查找、后缀自动机和检索。

为消除草稿本身的顺序瓶颈，近期方法提出并行或块级生成。P-EAGLE 并行化了 EAGLE 风格的草稿，而 PARD、DART 和 DFlash 使用扩散启发的预测在单次前向传播中生成整个块，DDTree 进一步将其扩展为可验证的草稿树。并行工作也在改进 DFlash：Domino 引入了概念上类似我们 RNN 头的 CausalEncoder，而 DFlare 通过逐层融合解决条件瓶颈。

### 推测解码的系统感知调度

超越草案模型架构，另一条工作线聚焦于确定每轮生成或验证的最佳推测 token 数量。为此，各种方法使用置信度启发式、学习接受预测器或 bandit 策略在线调整草稿长度。此外，认识到推测解码本质上是一个系统级调度问题，近期工作通过根据实时系统负载和请求优先级调整推测预算来优化总体 goodput 和延迟。

### 并行生成

并行生成 token 的模型提供几乎与输出长度无关的解码延迟，使其成为自回归解码的有吸引力的替代方案。非自回归 Transformer 开创了这一方向，在单次前向传播中独立预测所有位置。然而，这迫使模型平均所有可能的模式，通常产生混合了不同有效序列片段的输出。

两条主要研究路线解决这一限制。一条路线保留单次前向传播架构但改变模型看到的内容或训练方式：引入潜变量作为条件输入引导所有位置朝向一致输出，或放宽训练目标使模型专注于产生单一连贯输出而非建模所有有效替代的完整分布。另一条路线通过迭代重预测、块级自回归或结构化输出层（如 CRF、CTC、HMM 和 PCFG）重新引入有限顺序依赖。

推测解码进一步要求草案器必须为拒绝采样规则提供精确的每 token 概率。由于迭代细化、潜变量边缘化或全局归一化，上述大多数技术不能直接提供这样的概率。例如，在与我们设计密切相关的 CRF-NAT 中，也在并行隐藏状态上放置了顺序模块，但其全局归一化的配分函数阻止了精确的每 token 概率计算。类似地，当将 CTC 输出层适配到并行推测解码时，CTC-drafter 由于对齐路径的潜变量边缘化而受限为贪心验证。DSpark 通过保持顺序纠错局部化来规避这些限制，因此每 token 概率仍然是精确的 softmax 评估。

## 7. 结论

在本文中，我们提出了DSpark，一个旨在克服大语言模型在高并发生产环境中推理的结构性和系统级瓶颈的推测解码框架。在算法层面，DSpark引入了一种半自回归生成范式——将计算密集的并行骨干网络与轻量级序列头相结合——以缓解独立并行草稿模型的快速后缀衰减。在系统层面，我们将验证长度选择形式化为一个全局吞吐量最大化问题，采用一个硬件感知前缀调度器，该调度器基于校准的生存概率和实时引擎负载动态调整目标模型的验证预算。广泛的离线评估表明，DSpark在多个领域显著优于最先进的自回归和并行基线。此外，其在DeepSeek-V4中的真实世界部署验证了其在生产服务中的实用价值：通过智能管理验证开销，DSpark在重负载下维持了稳健的并发性，持续加速了每用户生成速度，并有效地将LLM服务的Pareto前沿向外移动。

## 参考文献

T. Abramovich, M. Ashkenazi, I. Putterman, B. Chislett, T. Mitra, B. D. Rouhani, R. Zilberstein, and Y. Geifman. Speed-bench: A unified and diverse benchmark for speculative decoding. arXiv preprint arXiv:2604.09557, 2026.

Z. An, H. Bai, Z. Liu, D. Li, and E. Barsoum. PARD: Accelerating LLM inference with low-cost PARallel draft model adaptation. In The Fourteenth International Conference on Learning Representations, 2026.

AngelSlim Team. D-Cut: Adaptive verification depth pruning for speculative decoding, 2026.

Z. Ankner, R. Parthasarathy, A. Nrusimha, C. Rinard, J. Ragan-Kelley, and W. Brandon. Hydra: Sequentially-dependent draft heads for medusa decoding. In First Conference on Language Modeling, 2024.

M. Arriola, S. S. Sahoo, A. Gokaslan, Z. Yang, Z. Qi, J. Han, J. T. Chiu, and V. Kuleshov. Block diffusion: Interpolating between autoregressive and diffusion language models. In The Thirteenth International Conference on Learning Representations, 2025.

J. Austin, D. D. Johnson, J. Ho, D. Tarlow, and R. van den Berg. Structured denoising diffusion models in discrete state-spaces. In Advances in Neural Information Processing Systems, 2021a.

J. Austin, A. Odena, M. Nye, M. Bosma, H. Michalewski, D. Dohan, E. Jiang, C. Cai, M. Terry, Q. Le, et al. Program synthesis with large language models. arXiv preprint arXiv:2108.07732, 2021b.

T. Cai, Y. Li, Z. Geng, H. Peng, J. D. Lee, D. Chen, and T. Dao. Medusa: Simple LLM inference acceleration framework with multiple decoding heads. In Proceedings of the 41st International Conference on Machine Learning, volume 235, pages 5209–5235, 2024.

Y. Cai, X. Liang, X. Wang, J. Ma, H. Liang, J. Luo, X. Zuo, L. Duan, Y. Yin, and X. Chen. Fastmtp: Accelerating llm inference with enhanced multi-token prediction, 2025.

C. Chen, S. Borgeaud, G. Irving, J.-B. Lespiau, L. Sifre, and J. Jumper. Accelerating large language model decoding with speculative sampling. arXiv preprint arXiv:2302.01318, 2023.

J. Chen, Y. Liang, and Z. Liu. Dflash: Block diffusion for flash speculative decoding. arXiv preprint arXiv:2602.06036, 2026.

M. Chen, J. Tworek, H. Jun, Q. Yuan, H. P. de Oliveira Pinto, J. Kaplan, H. Edwards, Y. Burda, N. Joseph, G. Brockman, A. Ray, R. Puri, G. Krueger, M. Petrov, H. Khlaaf, G. Sastry, P. Mishkin, B. Chan, S. Gray, N. Ryder, M. Pavlov, A. Power, L. Kaiser, M. Bavarian, C. Winter, P. Tillet, F. P. Such, D. Cummings, M. Plappert, F. Chantzis, E. Barnes, A. Herbert-Voss, W. H. Guss, A. Nichol, A. Paino, N. Tezak, J. Tang, I. Babuschkin, S. Balaji, S. Jain, W. Saunders, C. Hesse, A. N. Carr, J. Leike, J. Achiam, V. Misra, E. Morikawa, A. Radford, M. Knight, M. Brundage, M. Murati, K. Mayer, P. Welinder, B. McGrew, D. Amodei, S. McCandlish, I. Sutskever, and W. Zaremba. Evaluating large language models trained on code, 2021.

Y. Cheng, A. Zhang, X. Zhang, C. Wang, and Y. Wang. Recurrent drafter for fast speculative decoding in large language models, 2024.

K. Cobbe, V. Kosaraju, M. Bavarian, M. Chen, H. Jun, L. Kaiser, M. Plappert, J. Tworek, J. Hilton, R. Nakano, C. Hesse, and J. Schulman. Training verifiers to solve math word problems. arXiv preprint arXiv:2110.14168, 2021.

D. Dai, C. Deng, C. Zhao, R. Xu, H. Gao, D. Chen, J. Li, W. Zeng, X. Yu, Y. Wu, et al. Deepseekmoe: Towards ultimate expert specialization in mixture-of-experts language models. In Proceedings of the 62nd Annual Meeting of the ACL, pages 1280–1297, 2024.

DeepSeek-AI. Deepseek-v3 technical report. arXiv preprint arXiv:2412.19437, 2024.

DeepSeek-AI. Deepseek-v4: Towards highly efficient million-token context intelligence, 2026.

C. Du, Z. Tu, and J. Jiang. Order-agnostic cross entropy for non-autoregressive machine translation. In Proceedings of the 38th International Conference on Machine Learning, volume 139, pages 2849–2859, 2021.

C. Du, J. Jiang, X. Yuanchen, J. Wu, S. Yu, Y. Li, S. Li, K. Xu, L. Nie, Z. Tu, and Y. You. GliDe with a CaPE: A low-hassle method to accelerate speculative decoding. In Proceedings of the 41st International Conference on Machine Learning, volume 235, pages 11704–11720, 2024.

M. Elhoushi, A. Shrivastava, D. Liskovich, B. Hosmer, B. Wasti, L. Lai, A. Mahmoud, B. Acun, S. Agarwal, A. Roman, A. Aly, B. Chen, and C.-J. Wu. Layerskip: Enabling early exit inference and self-speculative decoding. In Proceedings of the 62nd Annual Meeting of the ACL, page 12622–12642, 2024.

Fireworks AI. Speed, Python: Pick Two. How CUDA Graphs Enable Fast Python Code for Deep Learning, Aug. 2023.

T. Ge, H. Xia, X. Sun, S.-Q. Chen, and F. Wei. Lossless acceleration for seq2seq generation with aggressive decoding. arXiv preprint arXiv:2205.10350, 2022.

M. Ghazvininejad, O. Levy, Y. Liu, and L. Zettlemoyer. Mask-predict: Parallel decoding of conditional masked language models. In Proceedings of EMNLP-IJCNLP, pages 6112–6121, 2019.

F. Gloeckle, B. Youbi Idrissi, B. Roziere, D. Lopez-Paz, and G. Synnaeve. Better & faster large language models via multi-token prediction. In Proceedings of the 41st International Conference on Machine Learning, volume 235, pages 15706–15734, 2024.

Google DeepMind. Gemma 4 model card, 2026.

J. Gu, J. Bradbury, C. Xiong, V. O. Li, and R. Socher. Non-autoregressive neural machine translation. In International Conference on Learning Representations, 2018.

S. Gui, C. Shao, Z. Ma, X. Zhang, Y. Chen, and Y. Feng. Non-autoregressive machine translation with probabilistic context-free grammar. In Thirty-seventh Conference on Neural Information Processing Systems, 2023.

C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger. On calibration of modern neural networks. In International conference on machine learning, pages 1321–1330, 2017.

J. A. Hanley and B. J. McNeil. The meaning and use of the area under a receiver operating characteristic (roc) curve. Radiology, 143(1):29–36, 1982.

Z. He, Z. Zhong, T. Cai, J. D. Lee, and D. He. Rest: Retrieval-based speculative decoding, 2023.

X. Hu, Y. Shen, B. Zhang, H. Zhang, J. Dai, S. Ge, L. Chen, Y. Li, and M. Wan. Echo: Elastic speculative decoding with sparse gating for high-concurrency scenarios. arXiv preprint arXiv:2604.09603, 2026.

Y. Hu, K. Wang, X. Zhang, F. Zhang, C. Li, H. Chen, and J. Zhang. SAM decoding: Speculative decoding via suffix automaton. In Proceedings of the 63rd Annual Meeting of the ACL, pages 12187–12204, 2025.

F. Huang, T. Tao, H. Zhou, L. Li, and M. Huang. On the learning of non-autoregressive transformers. In Proceedings of the 39th International Conference on Machine Learning, volume 162, pages 9356–9376, 2022a.

F. Huang, H. Zhou, Y. Liu, H. Li, and M. Huang. Directed acyclic transformer for non-autoregressive machine translation. In Proceedings of the 39th International Conference on Machine Learning, volume 162, pages 9410–9428, 2022b.

J. Huang, Y. Zhang, Q. Zhang, H. Lin, H. Xu, and L. Zhang. Domino: Decoupling causal modeling from autoregressive drafting in speculative decoding, 2026a.

K. Huang, X. Guo, and M. Wang. Specdec++: Boosting speculative decoding via adaptive candidate lengths. arXiv preprint arXiv:2405.19715, 2024.

K. Huang, H. Wu, Z. Shi, H. Zou, M. Yu, and Q. Shi. Adaspec: Adaptive speculative decoding for fast, slo-aware large language model serving. In Proceedings of SoCC '25, pages 361–374, 2026b.

M. Hui, X. Huang, J. C. Salas, Y. Sun, N. Pemberton, X. Song, A. Khetan, and G. Karypis. P-eagle: Parallel-drafting eagle with scalable training, 2026.

D. Israel, G. Van den Broeck, and A. Grover. Accelerating diffusion llms via adaptive parallel decoding. Advances in neural information processing systems, 38:52870–52888, 2026.

N. Jain, A. Gu, W.-D. Li, F. Yan, T. Zhang, S. Wang, A. Solar-Lezama, K. Sen, and I. Stoica. Livecodebench: Holistic and contamination free evaluation of large language models for code. In ICLR, volume 2025, pages 58791–58831, 2025.

L. Kaiser, S. Bengio, A. Roy, A. Vaswani, N. Parmar, J. Uszkoreit, and N. Shazeer. Fast decoding in sequence models using discrete latent variables. In Proceedings of the 35th International Conference on Machine Learning, volume 80, pages 2390–2399, 2018.

W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. Gonzalez, H. Zhang, and I. Stoica. Efficient memory management for large language model serving with pagedattention. In Proceedings of the 29th SOSP, pages 611–626, 2023.

Y. Leviathan, M. Kalman, and Y. Matias. Fast inference from transformers via speculative decoding. In Proceedings of the 40th International Conference on Machine Learning, volume 202, pages 19274–19286, 2023.

G. Li, Z. Fu, M. Fang, Q. Zhao, M. Tang, C. Yuan, and J. Wang. Diffuspec: Unlocking diffusion language models for speculative decoding, 2025a.

R. Li, Z. Zhang, L. Zhang, H. Wang, X. Fu, and Z. Lai. Nightjar: Dynamic adaptive speculative decoding for large language models serving, 2026a.

T. Li, W.-L. Chiang, E. Frick, L. Dunlap, B. Zhu, J. E. Gonzalez, and I. Stoica. From live data to high-quality benchmarks: The arena-hard pipeline, April 2024a.

T. Li, W.-L. Chiang, E. Frick, L. Dunlap, T. Wu, B. Zhu, J. E. Gonzalez, and I. Stoica. From crowdsourced data to high-quality benchmarks: Arena-hard and benchbuilder pipeline. In Proceedings of the 42nd International Conference on Machine Learning, volume 267, pages 34209–34231, 2025b.

X. L. Li, J. Thickstun, I. Gulrajani, P. Liang, and T. Hashimoto. Diffusion-LM improves controllable text generation. In Advances in Neural Information Processing Systems, 2022.

Y. Li, F. Wei, C. Zhang, and H. Zhang. EAGLE-2: Faster inference of language models with dynamic draft trees. In Proceedings of EMNLP, pages 7421–7432, 2024b.

Y. Li, F. Wei, C. Zhang, and H. Zhang. EAGLE: Speculative sampling requires rethinking feature uncertainty. In Proceedings of the 41st International Conference on Machine Learning, volume 235, pages 28935–28948, 2024c.

Y. Li, F. Wei, C. Zhang, and H. Zhang. EAGLE-3: Scaling up inference acceleration of large language models via training-time test. In The Thirty-ninth Annual Conference on Neural Information Processing Systems, 2026b.

J. Libovický and J. Helcl. End-to-end non-autoregressive neural machine translation with connectionist temporal classification. In Proceedings of EMNLP, pages 3016–3021, 2018.

H. Lightman, V. Kosaraju, Y. Burda, H. Edwards, B. Baker, T. Lee, J. Leike, J. Schulman, I. Sutskever, and K. Cobbe. Let's verify step by step. In The Twelfth International Conference on Learning Representations, 2024.

F. Liu, Y. Tang, Z. Liu, Y. Ni, D. Tang, K. Han, and Y. Wang. Kangaroo: Lossless self-speculative decoding for accelerating llms via double early exiting. In Advances in Neural Information Processing Systems, volume 37, pages 11946–11965, 2024a.

F. Liu, X. Li, K. Zhao, Y. Gao, Z. Zhou, Z. Zhang, Z. Wang, W. Dou, S. Zhong, and C. Tian. Dart: Diffusion-inspired speculative decoding for fast llm inference, 2026a.

H. Liu, J. Huang, Z. Jia, Y. Park, and Y.-X. Wang. Not-a-bandit: Provably no-regret drafter selection in speculative decoding for llms, 2026b.

T. Liu, Q. Lv, Y. Shen, X. Sun, and X. Sun. Talon: Confidence-aware speculative decoding with adaptive token trees. arXiv preprint arXiv:2601.07353, 2026c.

X. Liu, C. Daniel, L. Hu, W. Kwon, Z. Li, X. Mo, A. Cheung, Z. Deng, I. Stoica, and H. Zhang. Optimizing speculative decoding for serving large language models using goodput. arXiv e-prints, pages arXiv–2406, 2024b.

X. Liu, J. Park, L. Hu, W. Kwon, Z. Li, C. Zhang, K. Du, X. Mo, K. You, A. Cheung, et al. Turbospec: Closed-loop speculation control system for optimizing llm serving goodput. arXiv preprint arXiv:2406.14066, 2024c.

X. Ma, C. Zhou, X. Li, G. Neubig, and E. Hovy. FlowSeq: Non-autoregressive conditional sequence generation with generative flow. In Proceedings of EMNLP-IJCNLP, pages 4282–4292, 2019.

J. Mamou, O. Pereg, D. Korat, M. Berchansky, N. Timor, M. Wasserblat, and R. Schwartz. Dynamic speculation lookahead accelerates speculative decoding of large language models. In Proceedings of The 4th NeurIPS ENLSP, volume 262, pages 456–467, 2024.

X. Miao, G. Oliaro, Z. Zhang, X. Cheng, Z. Wang, Z. Zhang, R. Y. Y. Wong, A. Zhu, L. Yang, X. Shi, et al. Specinfer: Accelerating large language model serving with tree-based speculative inference and verification. In Proceedings of the 29th ACM ASPLOS, Volume 3, pages 932–949, 2024.

M. P. Naeini, G. Cooper, and M. Hauskrecht. Obtaining well calibrated probabilities using bayesian binning. In Proceedings of the AAAI conference on artificial intelligence, volume 29, 2015.

Y. Ovadia, E. Fertig, J. Ren, Z. Nado, D. Sculley, S. Nowozin, J. Dillon, B. Lakshminarayanan, and J. Snoek. Can you trust your model's uncertainty? evaluating predictive uncertainty under dataset shift. Advances in neural information processing systems, 32, 2019.

L. Qian, H. Zhou, Y. Bao, M. Wang, L. Qiu, W. Zhang, Y. Yu, and L. Li. Glancing transformer for non-autoregressive neural machine translation. In Proceedings of ACL, pages 1993–2003, 2021.

Y. Ren, J. Liu, X. Tan, Z. Zhao, S. Zhao, and T.-Y. Liu. A study of non-autoregressive model for sequence generation. In Proceedings of ACL, pages 149–159, 2020.

L. Ringel and Y. Romano. Accelerating speculative decoding with block diffusion draft trees. arXiv preprint arXiv:2604.12989, 2026.

R. Sadhukhan, J. Chen, Z. Chen, V. Tiwari, R. Lai, J. Shi, I. E.-H. Yen, A. May, T. Chen, and B. Chen. Magicdec: Breaking the latency-throughput tradeoff for long context generation with speculative decoding. In The Thirteenth International Conference on Learning Representations, 2025.

C. Saharia, W. Chan, S. Saxena, and M. Norouzi. Non-autoregressive machine translation with latent alignments. In Proceedings of EMNLP, pages 1098–1108, 2020.

J. Sandler, J. Christopher, T. Hartvigsen, and F. Fioretto. Specdiff-2: Scaling diffusion drafter alignment for faster speculative decoding. In Ninth Conference on Machine Learning and Systems, 2026.

A. Saxena. Prompt lookup decoding, November 2023.

C. Shao, Y. Feng, J. Zhang, F. Meng, and J. Zhou. Sequence-level training for non-autoregressive neural machine translation. Computational Linguistics, 47(4):891–925, 2021.

C. Shao, Z. Ma, M. Zhang, and Y. Feng. Beyond MLE: Convex learning for text generation. In Thirty-seventh Conference on Neural Information Processing Systems, 2023.

Y. Shen, T. Liu, X. Hu, Q. Kong, B. Zhang, J. Dai, J. Zhang, S. Ge, L. Chen, Y. Li, M. Wan, and C. Wang. Draft less, retrieve more: Hybrid tree construction for speculative decoding, 2026.

S. Somasundaram, A. Phukan, and A. Saxena. PLD+: Accelerating LLM inference by leveraging language model artifacts. In Findings of NAACL, pages 6090–6104, 2025.

M. Stern, N. Shazeer, and J. Uszkoreit. Blockwise parallel decoding for deep autoregressive models. In Advances in Neural Information Processing Systems, volume 31, 2018.

X. Sun, T. Ge, F. Wei, and H. Wang. Instantaneous grammatical error correction with shallow aggressive decoding. In Proceedings of ACL, pages 5937–5947, 2021.

Z. Sun, Z. Li, H. Wang, D. He, Z. Lin, and Z. Deng. Fast structured decoding for sequence models. In Advances in Neural Information Processing Systems, volume 32, 2019.

R. Taori, I. Gulrajani, T. Zhang, Y. Dubois, X. Li, C. Guestrin, P. Liang, and T. B. Hashimoto. Stanford alpaca: An instruction-following llama model, 2023.

S. Tiwari, T. Chugh, N. Rickert, S. Peter, R. Mahajan, and H. Shen. Cachewise: Understanding workloads and optimizing kvcache management for efficiently serving llm coding agents. arXiv preprint arXiv:2606.16824, 2026.

C. Wang, J. Zhang, and H. Chen. Semi-autoregressive neural machine translation. In Proceedings of EMNLP, pages 479–488, 2018.

Z. Wang, D. Ma, X. Huang, D. Cai, T. Lan, J. Xu, H. Mi, X. Tang, and Y. Wang. THE END OF MANUAL DECODING: TOWARDS TRULY END-TO-END LANGUAGE MODELS. In The Fourteenth International Conference on Learning Representations, 2026.

Z. Wen and Y. Feng. Specbound: Adaptive bounded self-speculation with layer-wise confidence calibration, 2026.

Z. Wen, S. Gui, and Y. Feng. Speculative decoding with ctc-based draft model for llm inference acceleration. In Advances in Neural Information Processing Systems, volume 37, pages 92082–92100, 2024.

M. Williams, Y. D. Kwon, R. Li, A. Kouris, and S. I. Venieris. Speculative decoding with a speculative vocabulary. arXiv preprint arXiv:2602.13836, 2026.

Z. Wu, Z. Zhou, A. Verma, A. Prakash, D. Rus, and B. K. H. Low. TETRIS: Optimal draft token selection for batch speculative decoding. In Proceedings of the 63rd Annual Meeting of the ACL, pages 33329–33345, 2025.

H. Xia, T. Ge, P. Wang, S.-Q. Chen, F. Wei, and Z. Sui. Speculative decoding: Exploiting speculative execution for accelerating seq2seq generation. In Findings of EMNLP, pages 3909–3925, 2023.

H. Xia, Z. Yang, Q. Dong, P. Wang, Y. Li, T. Ge, T. Liu, W. Li, and Z. Sui. Unlocking efficiency in large language model inference: A comprehensive survey of speculative decoding. In Findings of ACL, pages 7655–7671, 2024.

H. Xia, Y. Li, J. Zhang, C. Du, and W. Li. SWIFT: On-the-fly self-speculative decoding for LLM inference acceleration. In The Thirteenth International Conference on Learning Representations, 2025.

Z. Xie, Y. Wei, H. Cao, C. Zhao, C. Deng, J. Li, D. Dai, H. Gao, M. Xu, K. Yu, L. Zhao, S. Zhou, Z. Xu, Z. Zhang, W. Zeng, S. Hu, Y. Wang, J. Yuan, L. Wang, and W. Liang. mHC: Manifold-constrained hyper-connections. In Forty-third International Conference on Machine Learning, 2026.

T. Xu, E. Helenowski, K. A. Sankararaman, D. Jin, K. Peng, E. Han, S. Nie, C. Zhu, H. Zhang, W. Zhou, et al. The perfect blend: Redefining rlhf with mixture of judges. arXiv preprint arXiv:2409.20370, 2024.

D. Yan, W. Wang, and X. Chu. Demystifying tensor cores to optimize half-precision matrix multiply. 2020 IEEE IPDPS, pages 634–643, 2020.

A. Yang, A. Li, B. Yang, B. Zhang, B. Hui, B. Zheng, B. Yu, C. Gao, C. Huang, C. Lv, et al. Qwen3 technical report. arXiv preprint arXiv:2505.09388, 2025.

Zacks917. AutoMTP_vLLM: Adapt vllm to automtp (early stop for multi-token prediction), 2026.

J. Zhang, J. Wang, H. Li, L. Shou, K. Chen, G. Chen, and S. Mehrotra. Draft & verify: Lossless large language model acceleration via self-speculative decoding. In Proceedings of the 62nd Annual Meeting of the ACL, page 11263–11282, 2024.

J. Zhang, Z. Yu, S. Liu, E. J. Yu, Z. Li, D. Zhu, J. Duo, W. Xiong, Y. Song, G. Yu, J. Zhu, and S. Li. Dflare: Scaling up draft capacity for block diffusion speculative decoding, 2026a.

L. Zhang, X. Wang, Y. Huang, and R. Xu. Learning harmonized representations for speculative sampling, 2025.

S. Zhang, Y. Zhang, Z. Zhu, H. Wang, D. Ma, D. Zhang, L. Chen, and K. Yu. Pacer: Blockwise pre-verification for speculative decoding with adaptive length. arXiv preprint arXiv:2602.01274, 2026b.

Y. Zhang and T. Math-AI. American invitational mathematics examination (aime) 2025, 2025.

C. Zhao, C. Deng, C. Ruan, D. Dai, H. Gao, J. Li, L. Zhang, P. Huang, S. Zhou, S. Ma, et al. Insights into deepseek-v3: Scaling challenges and reflections on hardware for ai architectures. In Proceedings of ISCA, pages 1731–1745, 2025a.

W. Zhao, T. Pan, X. Han, Y. Zhang, S. Ao, Y. Huang, K. Zhang, W. Zhao, Y. Li, J. Zhou, et al. Fr-spec: Accelerating large-vocabulary language models via frequency-ranked speculative sampling. In Proceedings of ACL, pages 3909–3921, 2025b.

K. Zheng, Y. Chen, H. Mao, M.-Y. Liu, J. Zhu, and Q. Zhang. Masked diffusion models are secretly time-agnostic masked models and exploit inaccurate categorical sampling. In The Thirteenth International Conference on Learning Representations, 2025.

L. Zheng, W.-L. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Lin, Z. Li, D. Li, E. Xing, et al. Judging llm-as-a-judge with mt-bench and chatbot arena. Advances in neural information processing systems, 36:46595–46623, 2023.

L. Zheng, L. Yin, Z. Xie, C. Sun, J. Huang, C. H. Yu, S. Cao, C. Kozyrakis, I. Stoica, J. E. Gonzalez, C. Barrett, and Y. Sheng. Sglang: Efficient execution of structured language model programs. In Advances in Neural Information Processing Systems, volume 37, pages 62557–62583, 2024.

Y. Zhong, S. Liu, J. Chen, J. Hu, Y. Zhu, X. Liu, X. Jin, and H. Zhang. DistServe: Disaggregating prefill and decoding for goodput-optimized large language model serving. In 18th USENIX OSDI, pages 193–210, 2024.

K. Zhu, Y. Gao, Y. Zhao, L. Zhao, G. Zuo, Y. Gu, D. Xie, T. Tang, Q. Xu, Z. Ye, K. Kamahori, C.-Y. Lin, Z. Wang, S. Wang, A. Krishnamurthy, and B. Kasikci. Nanoflow: towards optimal large language model serving throughput. In Proceedings of OSDI '25, USA, 2025.

## 附录A

### 反例：无早停时的选择偏差

我们提供一个简单的反例来说明在线全局搜索（即在算法1中没有中断条件的情况）如何违反无损推测解码所需的非预期属性。形式上，第k个草稿token的接纳事件ℓ_r ≥ k必须由调度器在token x_{r,k}被采样之前可用的信息决定。它不能依赖于x_{r,k}本身的实现。考虑一个单一请求（R=1）和最大草稿长度（γ=2）的场景。假设第一个位置的预token置信度为a_1 = 0.8，分析得到的容量曲线为：

SPS(1) = 1.0,
SPS(2) = 0.5,
SPS(3) = 0.45.

验证0个和1个草稿token的预期吞吐量为：

Θ_0 = 1 · SPS(1) = 1.0,
Θ_1 = (1 + 0.8) · SPS(2) = 0.9.

没有早停时，调度器在提交任何接纳决策之前继续评估Θ_2。由于Markov置信度头使用先前采样的token，下一个置信度分数c_2明确依赖于x_1的实现。因此，第二个前缀的生存概率

a_2 = a_1 c_2

同样依赖于x_1。考虑x_1的两种可能实现：

*   情况1（x_1产生高c_2）：假设x_1导致c_2 = 0.9。那么

    a_2 = 0.8 × 0.9 = 0.72。

    长度为2的预期吞吐量为

    Θ_2 = (1 + 0.8 + 0.72) × 0.45 = 1.134。

    由于Θ_2是{1.0, 0.9, 1.134}中的全局最大值，调度器返回ℓ = 2。第一个token x_1被接纳进入验证前缀。

*   情况2（x_1产生低c_2）：假设x_1导致c_2 = 0。那么

    a_2 = 0。

    长度为2的预期吞吐量为

    Θ_2 = (1 + 0.8 + 0) × 0.45 = 0.81。

    这里，全局最大值仍然是Θ_0 = 1.0，所以调度器返回ℓ = 0。第一个token x_1不被接纳进入验证前缀。

因此，第一个草稿token的接纳动态地依赖于第一个草稿token本身的值。这种事后依赖引入了选择偏差：调度器偏向那些导致高置信度续写的token，即使x_1的接纳决策本应在观察到x_1之前做出。我们现在明确分布偏差。令词汇表为{A, B}，并考虑第一个位置的目标和草稿分布：

p_t(A) = 0.7, p_t(B) = 0.3,
p_d(A) = 0.5, p_d(B) = 0.5.

第一个位置的标准推测接受概率为：

Σ_{x∈{A,B}} min(p_t(x), p_d(x)) = min(0.7, 0.5) + min(0.3, 0.5) = 0.8,

与假设值（a_1 = 0.8）匹配。假设事后调度器如上所述运行：x_1 = A产生高续写置信度，因此ℓ=2；而x_1 = B产生低续写置信度，因此ℓ=0。那么第一个输出token的分布如下。如果x_1 = A，草稿token被接纳并以概率

min(1, p_t(A)/p_d(A)) = min(1, 0.7/0.5) = 1

被接受，所以输出token是A。如果x_1 = B，草稿token不被接纳；目标模型转而从p_t生成一个新的token。因此，

Pr(Y = A) = Pr(x_1 = A) · 1 + Pr(x_1 = B) · p_t(A) = 0.5 + 0.5 × 0.7 = 0.85,

因此

Pr(Y = B) = 0.15。

这个输出分布（(0.85, 0.15)）与目标分布（(0.7, 0.3)）不同，证明事后调度器不是无损的。早停机制防止了因果贪心调度器中的这个问题。由于Θ_1 < Θ_0，调度器在评估任何依赖于续写的量（如c_2）之前立即停止并返回ℓ=0。因此，第一个位置的接纳决策只依赖于预token信息，并且不能被x_1的实现所偏置。这恢复了标准无损论证所需的非预期属性。
