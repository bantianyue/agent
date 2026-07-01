# vLLM Semantic Router: Signal Driven Decision Routing for Mixture-of-Modality Models

**论文标题：** vLLM Semantic Router: Signal Driven Decision Routing for Mixture-of-Modality Models
**作者：** Xunzhuo Liu, Huamin Chen 等 30+ 位作者
**时间：** June 2026
**论文链接：** https://arxiv.org/abs/2603.04444

## Abstract

随着 LLM 在模态、能力和成本方面的多样化，智能请求路由——在推理时为每个查询选择正确的模型——已成为关键的工程挑战。本文提出 vLLM Semantic Router（VSR），一个信号驱动的决策路由框架，用于 Mixture-of-Modality（MoM）模型部署。架构遵循两个互补的 Shannon 视角：信息论视角中，信号提取通过从原始查询中蒸馏路由相关信息来减少"选哪个模型？"的熵；布尔代数视角中，决策引擎从信号条件中组合功能完备的路由策略。核心创新是「可组合的信号编排」（composable signal orchestration）：13 种异质信号类型（涵盖亚毫秒启发式方法和语义、安全、模态的神经分类器）通过可配置的布尔决策规则组合成部署特定的路由策略。匹配的决策通过 13 种选择算法驱动语义模型路由，同时 per-decision 插件链执行安全约束（包括三阶段 HaluGate 幻觉检测流水线和轻量级情景记忆系统 ReflectionGate）。

## 1. Introduction

LLM 的格局沿着多个维度碎片化：模态（文本、代码、视觉、扩散）、规模（1B 到 1T+ 参数）、成本（per-token 价格相差 10 倍以上）、专业化（通用 vs 领域微调）。企业越来越运行异构模型集群——本地 vLLM 实例与 OpenAI、Anthropic、Azure、Bedrock、Gemini 和 Vertex AI 的云端点混合——各有不同的能力、价格和合规特征。

这创造了一个根本性的推理时优化问题：给定一个用户查询、一个多样化的模型集群和部署特定的约束条件，哪个模型应该服务它，该应用什么安全和隐私策略？

**关键贡献：**
1. **可组合的信号-决策-插件架构**：13 种信号类型通过布尔决策规则组合成部署特定的路由策略，每个决策有独立的插件链
2. **语义模型路由与成本感知选择**：集成 13 种模型选择算法
3. **HaluGate：门控幻觉检测**：三阶段流水线——哨兵门控、token 级检测、NLI 解释
4. **多 Provider 和多端点路由**：原生支持跨异质后端（vLLM, OpenAI, Anthropic 等）
5. **LoRA 多任务分类**：从单一基座模型服务 n 个分类任务
6. **情景对话记忆与 ReflectionGate**：轻量级记忆系统，无需推理时 LLM 调用
7. **可编程神经符号配置语言**：带形式语法的 DSL

## 2. System Architecture

三层架构：
- **输入层（信号提取）**：将请求映射为结构化信号结果，涵盖 13 种信号类型。启发式信号（keyword, language, context length, authz）在亚毫秒内完成；ML 信号（embedding, domain, fact-check, modality 等）需要 10-120ms 神经推理。
- **隐藏层（决策块）**：评估一组决策，每个定义为信号条件上的布尔公式，选择最佳匹配决策
- **投影层（插件链）**：每个决策携带 per-decision 插件配置（pre-routing: 安全执行、语义缓存、RAG 注入；semantic model selection; post-routing: 幻觉检测、缓存更新）

四个设计原则：可组合性、正交性、闭环适应性、per-decision 作用域、Provider 抽象。

## 3. Signal Extraction Layer

13 种信号类型：
**启发式信号**: Keyword、Context Length（token 计数区间）、Language（100+ 语言检测）、Authorization（RBAC）
**学习信号**: Embedding Similarity（余弦相似度）、Domain Classification（MMLU 分类）、Factual Grounding（HaluGate Sentinel）、User Feedback、Modality（autoregressive/diffusion/both）、Complexity（对比度嵌入）、Jailbreak Detection（BERT + 对比度嵌入）、PII Detection（token 级 NER）、Preference

关键优化：按需驱动评估——只计算被至少一个决策引用的信号类型，相比穷举评估减少 50-70% 延迟。

## 4. Decision Engine

决策 = {名称, 布尔公式 φ, 候选模型集, 插件配置, 优先级}

布尔公式递归定义：叶节点引用信号，复合节点通过 AND, OR, NOT 组合。功能完备性：任意 {0,1}^N → {0,1} 的布尔函数可通过 AND/OR/NOT 表示。

两种选择策略：优先级策略（确定性、管理员可控）和置信度策略（数据驱动）。

对应数字逻辑电路：深度 1 的决策公式 ↔ PLA；递归规则节点树 ↔ 通用组合逻辑电路；优先级多决策集 ↔ 带优先编码器的电路阵列。

支持模糊评估延伸，用 (min, max, 1−x) 三元素在连续置信度上处理。

## 5. Plugin Framework

插件模型：π: (Request, Context, Config) → (Request', Response') ∪ {⊥}

请求路径顺序：fast response → cache → RAG → modality → memory → system prompt → header mutation
响应路径顺序：hallucination detection → cache write

核心插件：语义缓存（4 种后端：HNSW/Redis/Milvus/混合）、系统提示注入（Replace/Insert）、Header Mutation、Fast Response（安全短路）

## 6. Programmable Neural-Symbolic Configuration Language

DSL 定义 5 种顶级块类型：SIGNAL, ROUTE, PLUGIN, BACKEND, GLOBAL。

编译流水线：Lexing → Parsing → Compilation → Emission（flat YAML / Kubernetes CRD / Helm values）

三级别验证：Syntax error（Level 1）+ Reference resolution（Level 2, 含模糊 QuickFix）+ Constraint check（Level 3）

DSL 被理解为神经符号推理引擎的指令集。功能完备性保证任何路由策略都是可表达的，这使路由器配置变成程序合成问题——LLM 代码生成 Agent 可从自然语言规范合成 DSL 配置。

## 7. Request-Time Safety

安全检测作为 first-class signals 运行在信号提取层，而非串行插件。三种优势：零额外延迟、可与域信号组合、统一可观测性。

Jailbreak 检测支持 BERT 分类器和对比度嵌入两种方法。对比度方法专为多轮"温水煮青蛙"攻击设计，通过对所有用户消息求 max 聚合检测逐步升级。

PII 检测：token 级 NER 分类器（person, email, phone, SSN, credit_card 等），per-rule 允许列表支持差异化执行。

## 8. HaluGate: Gated Hallucination Detection

三阶段门控流水线：
1. Sentinel（门控）：轻量级二分类器判断查询是否需事实核查。40-60% 的非事实查询跳过后续阶段
2. Detector（span 识别）：token 级分类器识别模型响应中的幻觉 span
3. Explainer（NLI 分类）：对每个标记 span，NLI 模型区分 entailment/contradiction/neutral

门控减少预期检测成本约 50%。

## 9. LoRA-Based MoM Model Family

n 个独立模型需要 n·|θ_base| 内存。LoRA 方案只需要 |θ_base| + n·2rd（rank=32 时每个 adapter 仅 ~49K 参数）。

对 n=6，LoRA 架构比独立模型节省约 6× 内存。

MoM 模型族：mom-domain, mom-pii, mom-jailbreak, mom-sentinel, mom-detector, mom-explainer, mom-feedback, mom-modality, mom-embedding, mom-toolcall, mom-intent。

## 10. Semantic Model Selection

13 种选择算法：
- Rating-Based: Static, Elo Rating (RouteLLM)
- Embedding-Based: RouterDC, Hybrid
- Cascading: AutoMix (POMDP 公式)
- Classical ML: KNN, KMeans, SVM, MLP
- Reinforcement Learning: Thompson Sampling, GMTRouter
- Latency-Aware: 基于 TPOT/TTFT 百分位
- Multi-Round Reasoning: ReMoM（广度调度并行 + 合成）

统一接口 Select: (𝐞_q, z, ℳ, Θ) → (m*, c)

## 11. Multi-Runtime ML Inference

四运行时架构：Candle（GPU 分类）、Linfa（CPU ML）、ONNX Runtime（Embeddings）、NLP Binding（BM25/N-gram）

所有运行时编译为 Rust 共享库，通过 CGo/C FFI 链接到 Go 路由进程，消除 Python 运行时开销。

ModernBERT-base-32k：YaRN RoPE 扩展上下文窗口到 32K tokens。

## 12. Request Processing Pipeline

Envoy External Processor (ExtProc) 实现，透明拦截 LLM API 流量。

多端点路由：端点拓扑 ℰ = {(e_i, w_i, p_i, α_i)}，加权随机选择 + 粘滞会话亲和性 + 故障转移。

Provider 协议翻译：OpenAI/Azure → Anthropic → Bedrock/Vertex AI → Gemini → vLLM/local，透明的格式转换。

Responses API 支持、可插拔授权工厂（API Key, OAuth2/OIDC, Cloud IAM, Passthrough, Custom）。

## 13. Memory and RAG

持久记忆：每个对话轮次直接存储为情景块（无需外部 LLM），熵门控过滤低信号轮次。阅读路径通过 ReflectionGate（安全/recency/去重/预算限制）后注入。

RAG 插件：三信号混合检索（Vector + BM25 + N-gram），加权融合或 Reciprocal Rank Fusion。6 种后端：In-Memory, Milvus, Llama Stack, External API, MCP, OpenAI file search。

## 16. Evaluation

信号提取延迟：启发式 <0.5ms p99；ML 信号 15-120ms，并行评估下墙钟时间由最慢信号主导（~120ms）。

Flash Attention 替代 SDPA：4K 时 3.3x 加速，8K 及以上 SDPA 因 GPU OOM 不可用；Flash Attention 在 32K/20 并发下仍能工作。

LoRA 内存效率：n=6 时省 ~6×（575MB vs 3,438MB）。

决策引擎开销：<0.1ms（10 决策/3 条件）、<0.5ms（100 决策/5 条件）。

语义缓存：精确匹配 100% hit rate（<5ms）； paraphrased query 60-80% hit rate。

生产验证：600+ merged contributions from 50+ engineers。

## 18. Conclusion

可组合信号编排使单一框架通过配置即可服务多样化部署场景。Lora 多任务分类节省 ~n× 内存；HaluGate 门控减少 ~50% 检测成本；Rust-native ML 绑定实现亚 10ms 信号提取延迟。

未来方向：可学习决策策略、可微分熵折叠策略、自适应成本优化、对比偏好路由、跨 provider 一致性、多轮安全、联邦信号编排、Agent 路由策略合成。
