# Mixture-of-Agents Enhances Large Language Model Capabilities — 完整翻译

## Abstract
大型语言模型（LLM）的最新进展在自然语言理解和生成任务上展现了强大能力。随着 LLM 数量不断增长，如何利用多个 LLM 的集体专业知识是一个令人兴奋的开放方向。本文提出 Mixture-of-Agents（MoA）方法，构建分层 MoA 架构，每层包含多个 LLM Agent。每个 Agent 以上一层所有 Agent 的输出作为辅助信息来生成响应。MoA 在 AlpacaEval 2.0、MT-Bench 和 FLASK 上达到 SOTA，超越 GPT-4 Omni。仅使用开源 LLM 的 MoA 以 65.1% 的得分领先 AlpacaEval 2.0，而 GPT-4 Omni 为 57.5%。

## 1 Introduction
LLM 在自然语言理解和生成方面取得了重大进展。但尽管 LLM 数量众多且成果显著，它们仍然面临模型规模和训练数据的内在约束。进一步扩展模型极其昂贵，需要在数万亿 token 上重新训练。

同时，不同 LLM 拥有独特的优势，擅长不同的任务方面。有的擅长复杂指令跟随，有的更适合代码生成。这引出一个有趣的问题：能否利用多个 LLM 的集体专业知识，创建一个更强大更鲁棒的模型？

答案是肯定的。本文发现了一个内在现象——LLM 的「协作性」（collaborativeness）：当一个 LLM 看到其他模型的输出时，即使这些模型本身能力较弱，它也能生成更好的响应。

基于此发现，本文提出了 MoA 方法论。初始层中的 LLM（称为 Agent A1,1...A1,n）独立生成响应；这些响应被交给下一层的 Agent（A2,1...A2,n）进行进一步优化。这个迭代优化过程持续多个周期，直到得到更鲁棒和全面的响应。

为了确保模型间有效协作，需要仔细选择每个 MoA 层的 LLM，基于两个标准：
- (a) 性能指标：模型在层 i 的平均胜率决定是否适合纳入层 i+1
- (b) 多样性：异构模型生成的响应比相同模型生成的响应贡献更大

贡献总结：
1. 提出 MoA 框架
2. 发现 LLM 的协作性
3. MoA 在 AlpacaEval 2.0、MT-Bench、FLASK 上达到 SOTA

## 2 Mixture-of-Agents Methodology

### 2.1 Collaborativeness of LLMs
LLM 在参考其他模型输出时能生成更高质量的响应。可以将 LLM 分为两个角色：

- **Proposers（提议者）：** 擅长生成有用的参考响应供其他模型使用。好的 proposer 不一定自己得分高，但应提供更多上下文和不同视角。
- **Aggregators（聚合者）：** 擅长将其他模型的响应合成为单一高质量输出。好的 aggregator 即使在输入质量低于自身输出时也能保持或提升质量。

GPT-4o、Qwen1.5、LLaMA-3 在两种角色上都表现出色。WizardLM 作为 proposer 表现出色，但 aggregating 能力较弱。

### 2.2 Mixture-of-Agents
MoA 结构：有 l 层，每层 i 包含 n 个 LLM（Ai,1, Ai,2, ..., Ai,n）。LLM 可以在同层或跨层复用。

MoA 不需要任何微调。给定输入 prompt x1，第 i 层输出 yi 的表达：
yi = ⊕j=1n[Ai,j(xi)] + x1, 其中 xi+1 = yi
"+" 表示文本拼接，"⊕" 表示使用 "Aggregate-and-Synthesize" prompt 处理。

Aggregate-and-Synthesize prompt："你收到了来自多个开源模型对最新用户查询的一组响应。你的任务是将这些响应合成为一个高质量响应。关键是要批判性地评估这些信息，认识到其中可能包含偏见或错误。你的响应不应简单复制给定答案，而应提供精炼、准确、全面的回复。"

实际上，最后一层只需要一个 LLM 的输出作为最终结果。

### 2.3 Analogy to MoE
MoA 将 MoE 概念扩展到模型级别——在模型层面而非激活层面运作。MoA 完全通过 prompt 接口运作，不需要修改内部激活或权重。优势：(1) 消除微调的计算开销；(2) 灵活可扩展，可应用于任何最新 LLM。

## 3 Evaluation

### 3.1 Setup
**基准测试：** AlpacaEval 2.0（805 条指令，LC win rate）、MT-Bench、FLASK（12 个技能维度评分）
**模型：** Qwen1.5-110B-Chat、Qwen1.5-72B-Chat、WizardLM-8x22B、LLaMA-3-70B-Instruct、Mixtral-8x22B-v0.1、dbrx-instruct。3 个 MoA 层，Qwen1.5-110B-Chat 作为最后一层的 aggregator。MoA w/ GPT-4o 变体用 GPT-4o 做最终 aggregator。MoA-Lite 用 2 层 + Qwen1.5-72B-Chat 做 aggregator。

### 3.2 Benchmark Results
**AlpacaEval 2.0：** MoA w/ GPT-4o LC win rate 65.7%，MoA 65.1%，MoA-Lite 59.3%，GPT-4 Omni 57.5%，GPT-4 Turbo 55.0%。MoA 比 GPT-4o 提升 7.6 个百分点。

**MT-Bench：** MoA w/ GPT-4o 9.40，MoA 9.25，GPT-4 Turbo 9.31。

**FLASK：** MoA 在 robustness、correctness、efficiency、factuality、commonsense、insightfulness、completeness 上显著提升。MoA 在 conciseness 上表现不佳——输出略冗长。

### 3.3 What Makes MoA Work Well
1. **MoA 显著优于 LLM ranker：** aggregator 不仅仅是选择最佳回答，而是进行复杂的聚合
2. **MoA 倾向于纳入最佳答案：** BLEU 相似度与胜率呈正相关
3. **多样性和 proposer 数量：** 增加 proposer 数量和模型多样性均提升性能
4. **模型角色专业化：** GPT-4o、Qwen、LLaMA-3 在两种角色上都出色。WizardLM 擅长 proposer 但不擅长 aggregator。dbrx-instruct 作为 aggregator 较弱（41.5%），作为 proposer 不错（55.1%）

### 3.4 Budget and Token Analysis
MoA 在性价比 Pareto 前沿上。MoA-Lite 可以在匹配 GPT-4o 成本的同时达到更高质量。MoA 的效果优于 GPT-4 Turbo 约 4%，同时成本效益是后者的两倍以上。

## 4 Related Work
LLM Reasoning: CoT、ToT、GoT、Self-Consistency 等推理增强方法。
Model Ensemble: PairRanker、路由方法、FrugalGPT、多 Agent 协作（对称/非对称讨论、ReConcile 加权投票等）。

## 5 Conclusion
MoA 通过多阶段迭代协作利用多个 LLM 的能力。在 AlpacaEval 2.0、MT-Bench、FLASK 上显著提升。LC win rate 达到 65%。

**Limitations：** 需要迭代聚合响应，首 token 时间（TTFT）高。未来可探索分块聚合降低 TTFT。

**Broader Impact：** 增强 LLM 驱动助手的效果，提高模型可解释性。
