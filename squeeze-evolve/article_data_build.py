#!/usr/bin/env python3
"""
article_data_build.py — Squeeze Evolve: Unified Multi-Model Orchestration for Verifier-Free Evolution
==================================================================================================
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "Squeeze Evolve：无验证器进化中多模型编排的统一框架",
    "summary": [
        {"key": "核心问题", "body": "无外部验证器时，简单进化加速向狭窄模式坍缩；统一使用高成本模型浪费计算，很快被昂贵模型的控制开销吞噬"},
        {"key": "Squeeze Evolve", "body": "将遗传算子路由到最适合的模型：初始化用最强最贵模型，重组/聚合用经济模型；Group Confidence 做零额外推理成本的适应度信号"},
        {"key": "实验结果", "body": "在 AIME/GPQA/LiveCodeBench/MMMU-Pro/ARC-AGI-V2 上相比 RSA 降低 47-69% 成本，或同等成本下 3-12 分提升"},
    ],
    "lead": [
        "测试时计算扩展已是从单次推理走向搜索和精炼的有效手段。但现有方法要么依赖外部验证器（增加系统复杂度），要么滥用昂贵模型（快速消耗预算）。**我们发现无验证器进化存在一个根本瓶颈：多样性崩塌。** 没有外部验证器，循环只能放大当前模型已经「知道如何识别」的轨迹——但过于狭窄的搜索坍缩从根本上限制了可达到的最好结果。Squeeze Evolve 的解决方案是将每种进化算子路由到最适合的模型，实现成本-能力前沿的系统性左移。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "统一进化框架：将测试时方法纳入一个公式",
            "paras": [
                "许多看似不同的测试时方法可以统一到一个演化框架中。对于一个查询 Q，初始化一个种群 P(0)，使用祖先函数对候选解采样。每轮选择器 select 根据适应度信号 f 挑选出 K 个群组，重组器 recomb 对每组中的候选执行交叉/变异，产生新种群。**最终种群 P(T) 由一系列算子组合推导而来：P(T) = (Φ_fT ∘ Φ_f(T-1) ∘ ... ∘ Φ_f1)(P(0))。**",
                "在这个框架下，majority voting 是退化的单步过程、self-refinement 是每步混洗-选择-变异循环、RSA 是 10 步的噪声鲁棒聚合迭代。这个统一视角揭示了不同方法的共同设计空间和共同瓶颈。",
            ],
        },
        {
            "type": "h2",
            "title": "关键发现：无验证器进化的固有瓶颈",
            "paras": [
                "论文通过实证分析揭示了三个关键洞察。**第一，多样性崩塌。** 在同一模型上反复运行开放循环进化，候选解的多样性在几轮内急剧下降，pass@K 上限也随之坍缩。而多模型路由机制可以维持多样性。",
                "**第二，Pass@K 的天花板。** 无验证器时，循环只能放大模型已知的轨迹方向——这与验证器驱动的演化的关键区别在于后者可以使用外部评分来逃逸局部最优。",
                "**第三，祖先函数主导最终精度。** 实验结果清晰表明：使用 GPT-OSS-120B 作为祖先函数 + GPT-OSS-20B 重组，准确率 89%；但颠倒角色则降至 66%——初始种群的质量是最终精度的最强预测因子。同样，聚合阶段的最佳模型并非决定性的——4 条正确轨迹+1 条错误轨迹的混合，最好模型也仅 83%；但 4 条来自较弱模型的正确轨迹却能达到 95%。",
            ],
        },
        {
            "type": "h2",
            "title": "Squeeze Evolve 算法",
            "paras": [
                "算法在三个核心算子间执行模型路由：**初始化**所有 N 个候选从最强（通常也最贵）模型 M2 采样——因为初始质量主导最终结果。**适应度信号**从模型自身的输出派生，无需外部评分：Group Confidence (GC) 基于 top-K 个 token 对数概率，Self-Consistency (SC) 基于种群内答案一致性频率。**三档重组**：对最高适应度的群组使用最强模型 M2 深层次精炼，中等适应度群组使用经济模型 M1 做标准交叉，最低适应度群组使用 M1 仅做变异。这种路由策略确保昂贵模型的计算聚焦于最有潜力的候选。",
                "论文还验证了 GC 与各种基准测试得分的强斯皮尔曼秩相关——正确轨迹的置信度一致高于错误轨迹，这为无验证器路由提供了可行性基础。",
            ],
        },
        {
            "type": "h2",
            "title": "系统实现：延迟匹配服务 + 高效评分引擎",
            "paras": [
                "路由本身不足以获得实际收益。Squeeze Evolve 将 M1 和 M2 部署在独立的 GPU 池中，大小调整使它们在每次循环中大约同时完成工作。**Self-confidence 几乎免费**——模型在生成时已产生所需的对数概率，无需额外推理。Cross-confidence 使用小型评分模型，仅需 0.5-0.8× 的单次前向传播成本。**评分引擎**将前向传播与 batch scoring 融合，相比逐次推理实现 9-15× 加速。总体路由开销仅占端到端延迟的 1.9-6.8%。",
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "在 AIME 2025 上，Qwen3-30B Instruct → Thinking 路由将成本降低 47-69%，精度基本持平。在 GPQA-Diamond 上，Mixed (GPT-OSS-120B + Gemini 3.1 Pro) 路由在 76.3% 精度下成本降至 $0.4/problem，同等精度下比 RSA 低 60%。在 LiveCodeBench V6 上，在 $0.2/problem 的低预算下，路由比 RSA 高 12 分。",
                "**MMMU-Pro：** 异构路由（Claude Opus 4.6 Gemini 3.1 Pro → GPT 5.4）在 126.3 小时到达 78.9% 精度，而 RSA 仅 67.1%。",
                "**ARC-AGI-V2：** Squeeze Evolve 在 Gemini 3.1 Pro + GPT 5.4 上达到 80.8% 正确率，超过单个 GPT 5.4 的 72% 和 Gemini 3.1 Pro 的 72%。**Circle Packing（科学发现）：** GPT-OSS-120B + Gemini 3.1 Pro 获得 3.9586（满分 4.0），超过所有已知基线——这是首次无验证器方法在科学发现任务上达到可验证方法的水平。",
            ],
        },
    ],
    "conclusion": [
        "这篇论文的核心贡献在于将「哪个模型做哪件事」从直觉提升为系统的框架。**统一公式→识别瓶颈→路由方案→系统实现→跨任务验证，链条完整。** 最具洞察力的发现是「祖先函数主导最终精度」——这意味着在进化推理中，花大钱生成高质量的初始种群，然后用便宜模型做后续迭代，比均匀分配预算更划算。",
        "**从工程视角看，Squeeze Evolve 和同一时期的 MAPD（多 Agent 协议蒸馏）有互补性：** MAPD 在训练时用多 Agent 合成结构化协议来蒸馏知识；Squeeze Evolve 在推理时用多模型编排来降低验证成本。两者都认识到「不同模型适合不同角色」这个基本事实。",
        "**独立观点：** 论文中 Group Confidence 与任务得分的相关性（斯皮尔曼相关系数）可能是最被低估的结果——它本质上是说模型在「知道答案」和「不知道答案」时，内部状态有可分辨的信号。这意味着不需要外部奖励模型就能做推理时路由。**这个发现对 Agentic 系统的自校准和自纠错有更深远的含义，超出了本文的范围。**",
    ],
    "reference_url": "https://arxiv.org/abs/2604.07725",
    "figs": [
        {"src": "x1.png", "caption": "Figure 1: Squeeze Evolve 将成本-能力前沿向左移动——结合无验证器进化与多模型编排。"},
        {"src": "x3.png", "caption": "Figure 2: 单一模型开放循环进化使多样性崩塌并收缩 pass@K 上限，多模型路由保持两者。"},
        {"src": "x6.png", "caption": "Figure 4: Squeeze Evolve 概览——昂贵模型生成初始种群，物美价廉的模型做重组和聚合。"},
        {"src": "x12.png", "caption": "MMMU-Pro 上的精度-成本曲线：异构路由在远低于 RSA 的成本下达到更高精度。"},
        {"src": "x17.png", "caption": "Figure 4 (右下): 路由开销最小——仅占端到端延迟的 1.9-6.8%。"},
    ],
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入: {len(DATA['sections'])} sections, {sum(len(s.get('paras',[])) for s in DATA['sections'])} paras")