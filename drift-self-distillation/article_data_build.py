#!/usr/bin/env python3
"""
article_data_build.py — DRIFT: Difficulty Routing Self-DIstillation
arXiv 2606.30345 — 精简编译，论文类 60% 阈值。遵守图文原则、简洁原则、结论首句原则。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "DRIFT：用难度路由和节律门控探索实现 LLM 稳定自我进化，数学推理 +15.6%",

    "summary": [
        {"key": "核心问题", "body": "现有自蒸馏和 RL 方法缺乏问题级学习进度跟踪，容易题过度优化，难题监督弱，边界案例探索不足"},
        {"key": "核心方法", "body": "DRIFT：课程教师 + 难度路由 + 节律门控探索 + 成功缓冲池，四组件协同实现问题级自适应优化"},
        {"key": "实验结果", "body": "在数学推理和工具调用基准上全面超越 GRPO 和 SDPO 基线，AIME 提升 15.6%，MATH 提升 5.5%"},
    ],

    "lead": [
        "LLM 的自我进化——模型自己生成训练数据、自己从中学习——是减少对人类标注依赖的关键路径。但当前的自蒸馏和 RL 方法存在一个共同盲点：它们对所有问题用相同的优化策略，不考虑模型在不同问题上的掌握程度。",
        "DRIFT 提出了一种问题级自适应优化框架，通过四个组件的协同工作：课程教师（Curriculum Teacher）提供分阶段训练信号，难度路由（Difficulty Routing）按问题掌握度分配优化强度，节律门控探索（Rhythm-Gated Exploration）在 token 级别结构化探索，成功缓冲池（Success Buffer）存储利用成功轨迹。在数学推理和工具调用基准上，DRIFT 全面超越 GRPO 和 SDPO 基线。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "DRIFT 框架概览",
            "paras": [
                "DRIFT 是一个在线自我进化策略优化框架，围绕四个核心组件构建。下图展示了 DRIFT 的整体流程：",
            ],
            "figs": [
                {"src": "drift_pipeline_new.png", "caption": "DRIFT 框架整体流程。课程教师、难度路由、节律门控探索、成功缓冲池四组件协同工作。"},
            ],
        },
        {
            "type": "h2",
            "title": "课程教师：两阶段自适应训练",
            "paras": [
                "课程教师是 DRIFT 的训练策略管理器，分为两个阶段：",
                "**阶段一：自蒸馏快速热身**。使用自蒸馏进行快速初始化，积累经验轨迹。这一阶段让模型快速达到一个基本水平，为后续的精细优化做准备。",
                "**阶段二：稳定优化**。切换到自蒸馏与 RL 的混合优化，利用 RL 的探索能力和自蒸馏的稳定监督信号。阶段二的切换时机由模型在验证集上的表现动态决定。",
            ],
        },
        {
            "type": "h2",
            "title": "难度路由：问题级自适应优化",
            "paras": [
                "难度路由是 DRIFT 的核心创新。它在两个层面动态分配优化信号：",
                "**问题层面**：根据模型对每个问题的掌握程度，动态调整 RL 更新的强度。对于模型已掌握的问题，降低更新强度避免过度优化；对于模型尚未掌握的问题，增加更新强度。",
                "**Token 层面**：在细粒度上控制每个 token 的优化信号，确保模型在关键推理步骤上获得足够的监督。",
                "下图展示了难度路由在不同问题上的动态调整效果：",
            ],
            "figs": [
                {"src": "drift_routing_dynamics.png", "caption": "难度路由动态调整效果。不同难度的问题获得不同的优化强度。"},
            ],
        },
        {
            "type": "h2",
            "title": "节律门控探索",
            "paras": [
                "节律门控探索是 DRIFT 的探索策略组件。它通过一个节律门控机制在 token 级别进行结构化探索，在模型的推理路径中引入受控的随机性，避免陷入局部最优。",
                "与传统的无结构探索不同，节律门控探索根据当前 token 的预测不确定性动态调整探索强度——在不确定性高的 token 上增加探索，在确定性高的 token 上减少探索。",
            ],
        },
        {
            "type": "h2",
            "title": "成功缓冲池",
            "paras": [
                "成功缓冲池存储历史成功轨迹，用于重放训练。每当模型成功解决一个问题，完整的推理轨迹被存入缓冲池。在后续训练中，缓冲池中的成功轨迹被采样用于额外的训练信号。",
                "这种机制类似于 RL 中的经验回放，但专门针对推理任务设计——成功轨迹不仅提供正样本，还作为课程学习的参考标准，帮助模型在类似问题上更快地找到正确推理路径。",
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "在数学推理和工具调用两个领域的实验结果显示：",
                "**数学推理**：在 AIME 基准上，DRIFT 相比 GRPO 提升 15.6%，相比 SDPO 提升 9.8%。在 MATH 基准上分别提升 5.5% 和 3.2%。下图左展示了不同方法在 AIME 和 MATH 上的性能对比。",
                "**工具调用**：在 SciKnowEval 和工具使用基准上，DRIFT 同样全面超越 GRPO 和 SDPO，展示了框架在非数学推理任务上的泛化能力。",
                "**训练动态**：下图右展示了 DRIFT 训练过程中的难度路由动态变化，可以看到模型在不同问题上的掌握度随训练推进而逐步提升。",
            ],
            "figs": [
                {"src": "drift_performance.png", "caption": "AIME 和 MATH 上的性能对比。DRIFT 全面超越 GRPO 和 SDPO。"},
                {"src": "drift_training_dynamics.png", "caption": "训练过程中难度路由的动态变化。模型在不同问题上的掌握度逐步提升。"},
            ],
        },
        {
            "type": "h2",
            "title": "收敛性与消融分析",
            "paras": [
                "DRIFT 的收敛性分析显示，相比 GRPO 和 SDPO，DRIFT 的训练曲线更平滑，收敛更快。下图 1 展示了不同方法的收敛曲线对比。",
                "消融实验（下图 2）验证了每个组件的贡献：难度路由贡献最大，其次是节律门控探索，成功缓冲池和课程教师也各有显著贡献。去掉任何一个组件都会导致性能下降。",
            ],
            "figs": [
                {"src": "drift_convergence.png", "caption": "训练收敛曲线对比。DRIFT 收敛更快、更稳定。"},
                {"src": "drift_tooluse_ablation.png", "caption": "消融实验结果。每个组件都有显著贡献，难度路由贡献最大。"},
            ],
        },
    ],

    "conclusion": [
        "核心贡献是：提出了一种问题级自适应优化框架，通过难度路由解决了自蒸馏和 RL 方法在 LLM 自我进化中的共同盲点——对所有问题用相同策略。",
        "DRIFT 的四个组件（课程教师、难度路由、节律门控探索、成功缓冲池）协同工作，在数学推理和工具调用基准上全面超越 GRPO 和 SDPO。",
        "对于需要 LLM 持续自我进化的团队来说，DRIFT 提供了一个可插拔的框架——可以叠加在现有 GRPO/SDPO 训练流程之上，无需改变基础设施。",
    ],
    "reference_url": "https://arxiv.org/abs/2606.30345",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")