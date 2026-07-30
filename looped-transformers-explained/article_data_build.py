#!/usr/bin/env python3
"""
article_data_build.py — Looped Transformers Explained Clearly
============================================================
X/Twitter article by @neural_avb (AVB) — What are Looped Transformers? Explained clearly
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "循环 Transformer 详解：用更少的参数，做更深的推理",
    "summary": [
        {"key": "核心思想", "body": "Looped Transformer 重复使用同一组权重多次处理输入，用计算换参数，同一段文字视为反复精读几次"},
        {"key": "三段式架构", "body": "Prelude 编码→Core 循环块反复精炼→Coda 解码输出，训练时随机采样循环次数 r，推理时可调"},
        {"key": "实用方向", "body": "ARC-AGI 抽象推理、上下文学习表现不错，新一代 (Loopie) 在等计算量下首次击败普通 Transformer"},
    ],
    "sections": [
        {
            "type": "h2",
            "title": "为什么需要循环 Transformer",
            "paras": [
                "让 LLM 变聪明通常有两条路：一是给更多参数（更大的大脑），二是给更多计算/数据来训练（更长的教育）。两条路都有效，但都很昂贵。**一切研究的终极动机是在资源约束下最大化目标。** 从这个角度看，我们更该追逐第三种选择：重复使用已有的参数，而不是买新的。这个想法催生了 Looped Transformer。",
                "Looped Transformer 截取模型的一段，用循环多次处理同一输入，让它每次多「思考」一点——就像反复读一段话来加深理解。**如果这个思路成立，你可以在只存储小模型权重的同时，获得大得多的模型的智能收益。** 不是训练 100 层 Transformer，而是训练 25 层并循环 4 次。前向延迟和 FLOPs 数基本保持不变，但权重数减少 4 倍。实际上，你训练出的权重是多态的——同一组权重能够反射和迭代自身的过去输出。",
            ],
        },
        {
            "type": "h2",
            "title": "最早的原型：Universal Transformer (2018)",
            "paras": [
                "最常被引用的 Looped Transformer 论文是 2018 ICLR 的 Universal Transformer。它不是堆叠 N 个不同的层，而是用一个共享的过渡函数在时间步上循环应用。**不再是「层 1 → 层 2 → ... → 层 N」，而是迭代式地并行精化每个位置的表示，每次循环都用同一组权重。**",
                "UT 后来被称为所有现代循环/递归深度语言模型的直接架构祖先。但它当时为什么没有成为更大的事件？有五个原因：",
                "**1. 计算 vs 参数权衡当时不被理解。** 给定 N 倍计算增长，简单地把模型做大 N 倍通常比循环 N 次更好。2018 年缩放定律还没发表，领域缺乏框架来问「每 FLOP 是循环计算更有价值还是参数计算更有价值？」UT 在匹配参数数量而非匹配训练计算下评估，这美化了循环（循环步骤好像是「免费」的参数），隐藏了真实计算成本。",
                "**2. 时机不对。** UT 恰好在领域进入「规模就是一切」时代时发表。BERT、GPT-2、GPT-3 演示了原始可并行化 Transformer 的暴力参数和数据缩放能带来巨大、可预测的收益。而循环深度本质上是顺序的——步骤 t+1 必须等步骤 t 完成。",
                "**3. 基础设施没准备好。**",
                "**4. 增益不够戏剧性。** UT 更像研究论文而非百万美元级的模型。在小规模上结果不够大到改变范式。且 UT 只测试了密集架构，现代 LT 利用了 7 年更多研究的积累（MoE、稀疏注意力、DSA、CSA）。UT 还是 encoder-decoder，现在所有 LM 都是 decoder-only。",
                "**5. 计算资源和资金不同。** 2026 年的 GPU 远超 2019 年，投资者也更愿意投资前沿 AI 研究。",
            ],
        },
        {
            "type": "h2",
            "title": "现代 Looped Transformer：隐式思考",
            "paras": [
                "Universal Transformer 的核心思想是：重复应用同一个 self-attention + transition 块，并行精化每个 token 的表示，用 per-token halting 决定何时结束。现代 Looped Transformer 保留了权重共享的核心，但围绕 decoder-only、十亿到万亿参数因果语言模型的需求重构了几乎所有其他方面。",
                "**不再是整个网络循环**，现代实现将网络分为三个功能组：**Prelude**（少量普通非循环层，将原始 token 嵌入潜空间）、**Core 循环块**（实际「循环」部分，重复应用，接收上一轮潜状态+嵌入输入→新潜状态）、**Coda**（少量普通层+LM 头，将最终潜状态解嵌回 token 概率）。",
                "因为通过数十次循环迭代反向传播很昂贵（每一步都要存激活值），现代实现通常使用截断反向传播——梯度只传播通过最近的随机子集迭代，而非完整展开链。",
            ],
        },
        {
            "type": "h2",
            "title": "循环多少次：采样 vs 停机",
            "paras": [
                "这是与 UT 最重要的区别。Universal Transformer 使用 ACT（自适应计算时间）——学到每个 token 的停机概率，逐个符号决定何时停止精化。**现代循环 LLM 基本放弃了这个想法，改用更简单、更可扩展的方式：训练时随机采样循环次数 r（而非学习）。** 这训练模型对任何推理时的展开深度都鲁棒，所以测试时可以简单地把 r 当作一个旋钮来权衡计算与质量。更多迭代通常意味着更好的推理，但边际收益递减。",
            ],
        },
        {
            "type": "h2",
            "title": "相关工作和后续方向",
            "paras": [
                "如果你把模型循环 N 次，训练计算近似乘以 N 倍。循环不是免费的。在固定预算下，之前的工作表明普通 Transformer 做大 N 倍通常比循环小模型 N 次更好。**这个领域的挑战就是克服这个约束。**",
                "\n**MoEUT**（2024）：循环细粒度专家组而不是单个密集块，融合权重共享与 MoE 容量。",
                "\n**Relaxed Recursive Transformers**（2024）：保持共享重复块，但附加上每步 LoRA 适配器，弥补严格权重共享损失的表达力。",
                "\n**Mixture-of-Recursions (MoR, 2025)**：每个 token 路由到动态学习的递归步数——简单 token 少循环，困难 token 多循环。",
                "\n**DeepLoop**（2026）：修复训练稳定性 bug——标准 DeepNorm 缩放假设独立层，但循环模型跨访问共享同一权重，DeepLoop 引入更强的循环感知缩放指数。",
                "\n**Loopie**（2026）：解决计算问题——用正确配方（层循环+半存储深度+重投计算到 MoE 骨干），循环模型首次在等计算量下击败普通 Transformer。Loopie 还改变了循环位置：不是循环整个多层栈，而是逐层循环（每个层循环多次才进入下一层），即「A A A B B B C C C」而非「A B C A B C A B C」。",
            ],
        },
    ],
    "conclusion": [
        "这篇 X 文章清晰梳理了 Looped Transformer 从 Universal Transformer (2018) 到 Loopie (2026) 的演进。**核心矛盾一直没变：循环深度本质上是顺序的，训练计算随循环次数线性增长。** 在这个约束下，过去多年大家默认做 大 模型比做 深 模型更划算。",
        "**转折点出现在 2025-2026 年。** Loopie 首次在等计算量下证明循环模型可以击败普通 Transformer，关键在于层循环+半存储深度+MoE 三个技巧的组合。这说明之前的失败不是循环本身的问题，而是配方不对。DeepLoop 则解决了另一个长期被忽视的问题：权重共享下的训练稳定性。",
        "**独立观点：** 这台「用参数深度换计算深度」的故事和 latent reasoning 是同一枚硬币的两面——LOTUS 证明了循环架构可以弥合隐式与显式推理的差距，而 Looped Transformer 提供了这个循环骨架本身。推理时计算扩展（inference-time scaling）的下一个方向，很可能就是这种「可调循环深度」的架构。",
    ],
    "reference_url": "https://x.com/neural_avb/status/2081741935883223196",
    "figs": [
        {"src": "fig01.jpg", "caption": "Looped Transformer 示意图：同一组权重循环处理多次输入。"},
        {"src": "fig02.jpg", "caption": "Universal Transformer 架构：共享过渡函数在时间步上循环应用。"},
        {"src": "fig04.jpg", "caption": "现代 Looped Transformer 的三段式架构：Prelude → Core 循环块 → Coda。"},
    ],
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path}: {len(DATA['sections'])} sections, {sum(len(s.get('paras',[])) for s in DATA['sections'])} paras")