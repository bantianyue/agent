#!/usr/bin/env python3
"""
article_data_build.py — MLPs are Hebbians: Constructing Efficient Fact-Storing MLPs for Transformers
精简编译模式（compact），全部使用 arXiv 2607.10034 论文正式图。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "MLP 是 Hebbian 记忆：无需训练就能存储事实的 Transformer 构造方法",

    "summary": [
        {"key": "核心发现", "body": "Transformer MLP 天然是一种 Hebbian 记忆，可通过闭式公式直接构造，无需梯度下降，实现信息论最优速率的事实存储与召回"},
        {"key": "闭式构造", "body": "给定键值对嵌入，从高斯分布采样随机矩阵，构造门控 MLP 即可精确存储事实集，参数数量接近 Θ(F log F) 的最优速率"},
        {"key": "性能对比", "body": "相比 NTK 等先前构造方法提升 10-104×，最接近梯度下降训练 MLP 的 3-10× 以内，且在 Transformer 块内仍保持最优速率"},
    ],

    "lead": [
        "Transformer 中的 MLP 层一直被认为是「黑盒」——它们存储了海量知识，但没人真正知道存储机制是什么。**斯坦福 Hazy Research 团队的最新论文发现了一个惊人的事实：MLP 本质上是一种 Hebbian 记忆，可以用一个简单的闭式公式直接构造，完全不依赖梯度下降训练。**",
        "这意味着我们可以**瞬间将知识注入 Transformer 块**——给定一组键值对（如「法国的首都是巴黎」），通过一个随机矩阵加门控机制，就能构建一个精确存储这些事实的 MLP，而且参数数量接近信息论的理论下限。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "核心直觉：MLP 即 Hebbian 记忆",
            "paras": [
                "Hebbian 学习规则的核心是「一起放电的神经元，连接会增强」。论文发现，**MLP 的激活模式天然符合 Hebbian 机制**——输入通过随机投影映射到高维空间，与键嵌入的匹配程度决定哪些神经元被激活，从而实现事实的存储与检索。",
                "这一发现的关键意义在于：**MLP 不需要梯度下降就能「记住」事实。** 只要给定键嵌入（key embedding）和值嵌入（value embedding），通过一个简单的数学构造就能精确存储这些事实，参数效率接近信息论极限。",
                "具体来说，一个事实集定义为从键到值的映射：键嵌入 K = {k₁, ..., k_F}，值嵌入 V = {v₁, ..., v_F}，以及映射 f: [F] → [F]。例如，在「首都」事实集中，键嵌入「France」映射到值嵌入「Paris」。MLP 存储该事实集意味着：当查询键 k_i 时，输出与正确值 v_f(i) 的点积最大。",
            ],
            "figs": [
                {"src": "paper_banner.png", "caption": "论文 Figure 1：Hazy Research 构建事实存储 MLP 的概念图。论文提出了首个闭式的事实存储 MLP 构造方法。"},
            ],
        },
        {
            "type": "h2",
            "title": "闭式构造：一个极其简单的配方",
            "paras": [
                "构造方法出人意料地简单。给定键 k_i 和值 v_f(i)，从高斯分布中采样两个随机矩阵 A, G ∈ R^(m×d)，构建门控 MLP（Gated MLP）：",
                "**MLP(x) = A^T · (Gx > 0 的激活) · V**",
                "是的，整个构造就这么简单——**没有梯度下降，没有反向传播，没有迭代优化**。第一个矩阵 G 将输入随机投影到高维空间，门控激活函数选择与输入匹配的神经元，第二个矩阵 A 收集这些激活来产生正确的值输出。",
                "作者在论文中给出了完整的数学证明：当键嵌入各向同性时（如均匀球面分布），该构造能以信息论最优速率 Θ(F log F) 参数精确存储 F 个事实。对于非各向同性嵌入（如 LLM 的实际嵌入），容量按相同速率缩放，但需乘以嵌入几何结构决定的惩罚因子。",
            ],
            "figs": [
                {"src": "paper_fig2.png", "caption": "论文 Figure 2：MLP 存储容量的理论分析。左图展示边际分布随事实数量增长的缩放规律，中图展示构造的 MLP 容量与信息论最优边界的关系，右图展示 β 参数对存储容量的影响。"},
            ],
        },
        {
            "type": "h2",
            "title": "MLP 存储容量：信息论最优",
            "paras": [
                "论文的核心理论贡献是证明了所构造的 MLP 的存储容量。**在键和值嵌入各向同性的条件下，MLP 用 W 个参数可以精确存储 F 个事实，达到信息论最优速率 W = Θ(F log F)。**",
                "这意味着参数数量仅随事实数量线性增长（乘以对数因子），与理论极限一致。相比之下，先前基于神经正切核（NTK）的构造方法在同一任务上需要多 10-104 倍的参数。而梯度下降训练的 MLP 虽然表现更好，但本文构造方法已将其差距缩小到 3-10 倍以内。",
                "论文还提供了两种增强变体：**白化变体**（whitened variant）使用协方差白化核来适应嵌入分布；**数据依赖变体**（data-dependent variant）通过求解最小二乘问题来优化存储。数据依赖变体在 Transformer 场景中表现尤为出色。",
            ],
            "figs": [
                {"src": "arxiv_fig_mlp_anisotropic.png", "caption": "论文扩展数据：非各向同性嵌入下的 MLP 容量缩放。在 β=1.5 的非各向同性设置下，构造的 Hebbian MLP 仍然保持接近 Θ(F log F) 的容量缩放趋势。"},
            ],
        },
        {
            "type": "h2",
            "title": "Transformer 块内的事实召回",
            "paras": [
                "在独立 MLP 中存储事实是一回事，在 Transformer 块内使用是另一回事。**当 MLP 位于 Transformer 块中时，注意力层传递给它的不是精确的键嵌入 k_i，而是带有噪声的版本 q = k_i + ε。**",
                "论文证明，**只要注意力噪声（即查询向量与精确键嵌入的 L2 误差）低于 √(d/(F log F))，Transformer 块就能正确召回事实。** 在此条件下，整个块继承了 MLP 的信息论最优缩放特性。",
                "实验验证显示，数据依赖变体在 Transformer 场景中表现最佳：**在固定模型维度下随事实数量增长，该构造保持在梯度下降训练 MLP 的 3× 以内，比先前构造方法好 63×。** 这是首个证明 Transformer 块能以信息论最优速率存储事实的 MLP 构造方法。",
            ],
            "figs": [
                {"src": "paper_fig3.png", "caption": "论文 Figure 3：Transformer 块内的事实召回。左图展示带噪声查询的 Transformer 块结构，中图展示构造 MLP 在 Transformer 块中的容量缩放，右图展示与梯度下降训练模型的对比。"},
                {"src": "arxiv_fig_transformer_scaling.png", "caption": "论文扩展数据：Transformer 容量缩放曲线。在训练准确率 99% 的阈值下，构造的 Transformer 块在不同模型维度（d=512, 1024）上均实现接近最优的容量缩放。"},
            ],
        },
        {
            "type": "h2",
            "title": "真实 LLM 嵌入下的验证",
            "paras": [
                "论文不仅给出了理论分析，还使用 **Qwen3-0.6B** 的真实 LLM 嵌入进行了实验验证。结果表明，即使使用真实 LLM 的非各向同性嵌入，构造的 MLP 仍然能高效存储事实。",
                "**MLP 容量实验**：使用 Qwen3-0.6B 第 14 层的嵌入，构造的 MLP 在事实存储任务上接近梯度下降训练的性能，白化变体进一步提升了容量。",
                "**Transformer 块实验**：将构造的 MLP 嵌入到 Transformer 块中，在真实 LLM 嵌入上测试事实召回能力，构造方法仍然保持竞争力。",
                "**边际分析**：论文通过边际分布分析揭示了构造方法的成功原因——Hebbian 核函数在正确的键上产生较大的核值，在不匹配的键上产生较小的核值，从而实现了精确的键值检索。",
            ],
            "figs": [
                {"src": "arxiv_fig_mlp_llm.png", "caption": "Qwen3-0.6B 第 14 层嵌入下的 MLP 容量实验。构造的 MLP（含白化变体）在真实 LLM 嵌入上接近梯度下降训练的性能。"},
                {"src": "arxiv_fig_margin_violin.png", "caption": "边际分布小提琴图：正确键（蓝色）与错误键（橙色）的核值分布差异，揭示了 Hebbian 检索机制的工作边界。"},
                {"src": "arxiv_fig_transformer_llm.png", "caption": "Qwen3-0.6B 第 14 层嵌入下的 Transformer 容量实验。构造的 Transformer 块在真实 LLM 嵌入上仍保持接近最优的容量。"},
            ],
        },
        {
            "type": "h2",
            "title": "未来方向",
            "paras": [
                "论文打开了多个有意义的研究方向：",
                "**理解预训练 LLM 的事实存储机制**：能否用本文的理论框架理解预训练语言模型中的 MLP？能否直接提取或编辑存储在这些 MLP 中的知识？",
                "**序列混合器与多层 Transformer 的记忆**：能否将理论扩展到注意力 KV 缓存等序列混合器的参数化事实存储？注意力和 MLP 层如何协作在多层的模型中存储知识？",
                "这些问题的答案可能不仅会改变我们对 Transformer 的理解，还可能催生新一代的**高效模型编辑和知识注入技术**。",
            ],
        },
    ],

    "conclusion": [
        "这篇论文的核心贡献用一个简洁的理论框架统一了 MLP 的事实存储行为：**MLP 是 Hebbian 记忆，可以用闭式公式直接构造，无需梯度下降，以信息论最优速率存储事实，且在 Transformer 块内仍然有效。**",
        "这一发现的意义不仅在于它让我们理解了 MLP 的内部工作机制，更在于它开辟了一条**无需训练就能注入知识**的路径。想象一下，未来的 LLM 可能不再需要昂贵的微调来更新知识——只需通过一个简单的构造公式，就能将新的事实瞬间插入模型。",
    ],

    "reference_url": "https://arxiv.org/abs/2607.10034",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")