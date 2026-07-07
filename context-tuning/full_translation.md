Context Tuning for In-Context Optimization（面向上下文优化的上下文调优）

作者：Jack Lu, Ryan Teehan, Zhenbang Yang, Mengye Ren
机构：New York University（纽约大学）
会议：The 43rd International Conference on Machine Learning (ICML 2026)（第43届国际机器学习大会）
资源：arXiv, PDF, Code

TL;DR：Context Tuning（上下文调优）直接优化大语言模型的记忆表征，实现高效适配，且无需更新模型权重。

摘要：

我们提出 Context Tuning，一种简单而有效的方法，能在不更新权重的前提下显著增强大语言模型（LLM）的少样本适配能力。In-Context Learning（ICL，上下文学习）在单次前向传播中形成对演示样本的"记忆表征"，但当演示不足时无法对其进行精炼。基于提示的方法通过优化一个可训练的提示（prompt）或前缀（prefix）提供轻量级适配，但它与演示样本是独立初始化的。相比之下，Context Tuning 利用模型固有的 ICL 能力，从演示样本中初始化一个可训练的"记忆表征"，然后通过基于梯度的优化对其进行精炼。在 CrossFit、UnifiedQA、MMLU、BIG-Bench Hard、ARC 等基准上的大量评测表明，Context Tuning 在性能上同时超越了 ICL 和传统的基于提示的适配方法，同时达到了与 Test-Time Training（TTT，测试时训练）相竞争的准确率，且训练效率显著更高。

正文内容：

概述（Overview）

CT-KV 是 Context Tuning 最强的变体：

与上下文学习（ICL）相比，CT-KV 对模型为给定输入-输出示例形成的初始记忆表征进行精炼，而不是直接用它来做预测，从而大幅提高了准确率。

与测试时训练（TTT）相比，CT-KV 在不更新模型权重的情况下达到了有竞争力的准确率，且训练时间仅需一半或更少。

与 TTT 结合使用时，CT-KV 达到了最高的准确率，这表明 KV cache 调优与模型权重更新是互补的。

横轴为训练时间、纵轴为准确率，在 26 个 NLP 任务上取平均。

Context Tuning for In-Context Optimization（面向上下文优化的上下文调优）

CT-KV 保持 LLM 冻结，将所提供的示例形成的键值（KV）缓存转化为一个可训练的"记忆表征"。在优化过程中，Leave-One-Out Masking（留一掩码）要求模型基于其他示例来预测每个输出，而 Token Dropout（词元丢弃）则改善泛化能力。在推理时，模型以完整的优化后缓存为条件。我们的论文还提出了 CT-Prompt，一种基于提示嵌入的变体。

CT-KV 从提供的示例中初始化一个键值前缀，并用留一掩码（左图）对其进行优化。在生成时，模型以完整的优化后前缀为条件来回答新的查询（右图）。

实验（Experiments）

我们在 NLP-LR、MMLU、BBH 和 ARC 上评测 Context Tuning。实验涵盖 1B 到 32B 参数的预训练 LLM。

来自 BBH、NLP-LR、MMLU 的典型测试示例，后跟三个输入-输出示例和来自 ARC 的一个测试示例。

将 Context Tuning 与基线方法对比（Comparing Context Tuning to Baselines）

CT-KV 在全部四个基准上均超越了上下文学习（ICL）、Prompt Tuning、Prefix Tuning、LoRA、rank-stabilized LoRA 和 DoRA。它在不更新模型权重、且训练时间仅需一半或更少的情况下，达到了与 TTT 相竞争的准确率；而 TTT+CT-KV 在每个基准上都取得了最佳准确率。在 NLP-LR 上，CT-KV 的单任务适配在样本量匹配的条件下超越了 MetaICL 的多任务元训练（44.2% vs. 43.3%）。

每个任务以秒为单位的准确率和训练时间。均值和标准差在五组示例上计算，ARC 除外（它使用固定的一组示例）。加粗和下划线的值分别标记每个基准上最佳和第二佳的准确率。

对示例数量和质量的鲁棒性（Robustness to Example Count and Quality）

(a) 随着提供更多示例，CT-KV 始终领先于 ICL 和 Prefix Tuning。
(b) 即使在多达 75% 的示例标签被损坏的情况下，CT-KV 在两个基准上都表现最好。

NLP-LR 和 MMLU 的准确率随 (a) 示例数量和 (b) 标签损坏概率的变化。

扩展预训练模型（Scaling Up the Pretrained Models）

在从 12B 到 32B 参数、跨越多种架构的五个预训练模型上，CT-KV 均超越了 ICL 和 Prefix Tuning。

BBH 准确率随预训练模型规模增大而变化。

消融我们的设计选择（Ablating Our Design Choices）

留一掩码和词元丢弃在四个基准中的三个上均提升了 CT-KV。

在四个基准上对留一掩码和词元丢弃的消融。均值和标准差在五组示例上计算，ARC 除外（它使用固定的一组示例）。

定性结果（Qualitative Results）

我们展示了 CT-KV 预测在两个 ARC 任务优化过程中的演变。迭代 0 等同于 ICL。绿色标签表示正确预测，红色标签表示错误预测。

颜色映射（Color Mapping）

在迭代 0，模型用黄色填充每个带边界方块的内部。在优化过程中，它逐渐发现每个方块的正确填充颜色。

带有四个输入-输出示例、测试输入，以及 CT-KV 训练迭代中预测的 ARC 颜色映射任务。

交叉补全（Cross Completion）

在迭代 0，模型已经识别出应该用红色来完成十字形状，但不理解应该避免覆盖黑色方块。到迭代 200 时，预测变得更符合提供的示例，并解决了该任务。

带有四个输入-输出示例、测试输入，以及 CT-KV 训练迭代中预测的 ARC 交叉补全任务。

BibTeX（参考文献格式略）
