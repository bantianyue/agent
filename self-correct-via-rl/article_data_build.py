#!/usr/bin/env python3
"""
article_data_build.py — Training Language Models to Self-Correct via Reinforcement Learning
arXiv 2409.12917 — 精简编译，论文类 60% 阈值。遵守图文原则、简洁原则、结论首句原则。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "SCoRe：用多轮在线 RL 训练 LLM 自我纠错，仅用自生成数据，MATH 提升 15.6%",

    "summary": [
        {"key": "核心问题", "body": "LLM 自我纠错能力严重不足，SFT 训练纠错行为面临分布偏移和行为坍缩两大困境"},
        {"key": "核心方法", "body": "SCoRe：两阶段多轮在线 RL——阶段 I 防止行为坍缩，阶段 II 用奖励塑形放大纠错行为"},
        {"key": "实验结果", "body": "Gemini 1.0 Pro 和 1.5 Flash 上 MATH 提升 15.6%、HumanEval 提升 9.1%，所有训练数据完全自生成"},
    ],

    "lead": [
        "自我纠错（Self-Correction）是大语言模型的一个重要能力——模型应该能发现自己在推理中的错误并修正。但现代 LLM 的自我纠错能力严重不足，甚至在被明确要求检查时也不会改进答案。",
        "SCoRe（Self-Correction via RL）提出了一种多轮在线强化学习方案，完全使用模型自生成数据训练。核心洞察是：SFT 在纠错数据上训练会面临分布偏移（训练用的纠错轨迹来自不同策略）和行为坍缩（模型学会不做修改以最大化似然）。SCoRe 通过两阶段多轮 RL 解决了这些问题，在 MATH 和 HumanEval 上取得了目前最优的自我纠错性能。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "SFT 训练自我纠错的困境",
            "paras": [
                "SFT 在模型生成的纠错轨迹上训练时面临两个根本问题：",
                "**分布偏移**：训练数据由某个策略收集，但模型自己的错误模式和该策略不同——模型在训练时看到的是「别人的错误」，而不是「自己的错误」。",
                "**行为坍缩**：最大化似然训练倾向于让模型学会「不做修改」——因为修改会增加 token 生成概率的乘积，而不修改（保留原答案）的似然更高。SFT 模型在测试时几乎不做任何编辑，即使被要求检查错误也不会改进。",
            ],
            "figs": [
                {"src": "sft_edit_distances.png", "caption": "SFT 训练后的编辑距离分布。模型倾向于不做修改（编辑距离为 0）或仅做细微改动。"},
                {"src": "sft_validation.png", "caption": "SFT 验证集上的表现。SFT 虽然提升了首次尝试准确率，但未能教会模型真正纠错。"},
            ],
        },
        {
            "type": "h2",
            "title": "SCoRe 方法概览",
            "paras": [
                "SCoRe 是一个两阶段多轮 RL 方法，完全使用模型自生成数据训练。整个流程如下图所示：",
            ],
            "figs": [
                {"src": "SCoRe_main_figure.png", "caption": "SCoRe 整体流程。两阶段多轮 RL：阶段 I 初始化策略，阶段 II 用奖励塑形放大纠错行为。"},
            ],
        },
        {
            "type": "h2",
            "title": "阶段 I：多轮 RL 初始化",
            "paras": [
                "标准多轮 RL 训练会导致两次尝试的响应高度耦合，后续迭代的覆盖范围很差。阶段 I 专门设计了一个初始化策略来缓解这个问题：通过多轮 RL 在基础模型上首次训练，生成一个不容易坍缩的策略初始化。",
                "下图展示了阶段 I 训练的效果对比——有了阶段 I 的初始化，策略的 (t1,t2) 覆盖率更高，探索行为更好，最终性能也更好。",
            ],
            "figs": [
                {"src": "multiturn_train_stage1_only.png", "caption": "阶段 I 训练效果。阶段 I 的初始化策略比标准多轮 RL 获得更高的覆盖率，后续探索更好。"},
                {"src": "diff_answer_freq.png", "caption": "答案差异频率。没有阶段 I 初始化，策略很快学会不改变答案，导致探索不足。"},
            ],
        },
        {
            "type": "h2",
            "title": "阶段 II：奖励塑形放大纠错",
            "paras": [
                "阶段 II 在阶段 I 的初始化基础上，使用奖励塑形（Reward Shaping）来放大纠错行为。核心思想是：对第二次尝试正确但第一次尝试错误的样本给予额外奖励，鼓励模型学会真正的纠错而非保持不变。",
                "奖励函数设计为：R = R(t2) + α·[R(t2) > R(t1)]，其中第二项是纠错奖励——只有当第二次尝试比第一次更好时才给予。这利用了多轮交互的特性：第一次尝试提供了自然的基线，使奖励塑形可以针对性地奖励纠错行为。",
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "在 MATH 和代码生成（MBPP、HumanEval）上的实验结果显示：",
                "**MATH**：SCoRe 在 Gemini 1.0 Pro 上提升 15.6%，在 1.5 Flash 上提升 9.1%。多个尝试次数下性能持续提升，10 次尝试时准确率接近 60%。",
                "**HumanEval**：SCoRe 在 Gemini 1.0 Pro 上提升 9.1%。",
                "**与 SFT 基线对比**：SCoRe 在所有指标上显著优于 SFT 基线，包括 STaR 和 NReference 等变体。SFT 模型虽然首次尝试准确率提高，但纠错能力几乎没有改善。",
                "**推理时计算扩展**：SCoRe 的自我纠错能力随推理计算量增加而持续提升，说明模型真正学会了利用额外计算来提高准确率，而非简单地重复生成。",
            ],
            "figs": [
                {"src": "main_math_bar.png", "caption": "MATH 上的主要结果对比。SCoRe 在所有指标上显著优于 SFT 和基线。"},
                {"src": "math_10attempts_all.png", "caption": "MATH 上 10 次尝试的准确率曲线。SCoRe 随尝试次数增加持续提升。"},
                {"src": "inference_compute_scaling.png", "caption": "推理计算扩展曲线。SCoRe 的自我纠错能力随推理计算量增加而持续提升。"},
            ],
        },
        {
            "type": "h2",
            "title": "分析：SCoRe 学到了什么",
            "paras": [
                "对 SCoRe 训练后的行为分析揭示了几种有效的纠错策略：",
                "**答案更改**：模型在第二次尝试中更频繁地更改答案，且更改后正确的比例显著提高。",
                "**编辑距离**：SCoRe 的编辑距离分布显示模型做了有意义的编辑（不仅是微小改动），而 SFT 模型几乎不做编辑。",
                "**折现回报**：SCoRe 训练过程中，第二次尝试的折现回报持续上升，说明模型确实在从纠错中获益。",
            ],
            "figs": [
                {"src": "edit_histogram_subplots.png", "caption": "编辑距离分布对比。SCoRe 的编辑距离分布更广泛，说明模型做了有意义的修改。"},
                {"src": "discounted_return.png", "caption": "训练过程中折现回报变化。第二次尝试的回报持续上升，验证了纠错行为的习得。"},
            ],
        },
    ],

    "conclusion": [
        "核心贡献是：提出了一种完全基于模型自生成数据、无需外部反馈的多轮在线 RL 方法，让 LLM 学会真正的自我纠错。",
        "SCoRe 的关键洞察是：SFT 在纠错数据上训练面临分布偏移和行为坍缩，而多轮 RL 加上阶段 I 的初始化策略和阶段 II 的奖励塑形可以同时解决这两个问题。",
        "SCoRe 在 MATH 和 HumanEval 上的显著提升表明，自我纠错能力可以通过适当的 RL 训练从模型自身获得，而不需要更强模型或外部监督。",
    ],
    "reference_url": "https://arxiv.org/abs/2409.12917",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")